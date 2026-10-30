"""Lab console: see what agents did, from sealed ledgers only.

``run_trace`` reduces one verified ledger to a per-round, per-agent film strip.
``render_text`` gives a compact terminal readout; ``render_html`` writes one
self-contained page. Both are pure functions of the traces, so identical ledgers
give identical bytes. A ledger that fails verification is shown as broken, never
skipped. Display rates are floats derived for reading, not evidence records.
"""

from html import escape
from itertools import groupby
from pathlib import Path
from typing import Any

from collaborative_hill.engine.events import ChainError, Event, EventType
from collaborative_hill.engine.replay import replay_run
from collaborative_hill.reporting.report import _load_sealed_run

EC_GLYPHS = {
    "inspect_evidence": "i", "share_evidence": "s", "propose_claim": "p",
    "challenge_claim": "x", "verify_claim": "v", "approve_claim": "a",
    "withhold": "w", "abstain": ".",
}
NO_ACTION = "·"
REJECTED = "!"
SPARK = " ▁▂▃▄▅▆▇█"


def find_runs(root: Path) -> list[Path]:
    if (root / "events.jsonl").exists():
        return [root]
    return sorted(path.parent for path in root.rglob("events.jsonl"))


def _nipd_strips(transitions: list[dict[str, Any]], agents: list[str]) -> dict[str, str]:
    """One glyph per round: C, D, or the share of cooperative pairwise moves as + (mixed)."""
    strips = dict.fromkeys(agents, "")
    for payload in transitions:
        votes: dict[str, list[str]] = {agent: [] for agent in agents}
        if payload["mode"] == "pairwise":
            for pair in payload["pair_results"]:
                votes[pair["a"]].append(pair["move_ab"])
                votes[pair["b"]].append(pair["move_ba"])
        else:
            for agent, move in payload["moves"].items():
                votes[agent].append(move)
        for agent, moves in votes.items():
            distinct = set(moves)
            glyph = NO_ACTION if not distinct else "+" if len(distinct) > 1 else moves[0]
            strips[agent] += glyph
    return strips


def _ec_strips(events: list[Event], agents: list[str], rounds: int) -> dict[str, str]:
    cells = {agent: [NO_ACTION] * rounds for agent in agents}
    for event in events:
        accepted = event.event_type == EventType.ACTION_ACCEPTED
        if (accepted or event.event_type == EventType.ACTION_REJECTED) \
                and event.logical_time < rounds:
            kind = event.payload.get("action", {}).get("type")
            glyph = EC_GLYPHS.get(kind, "?") if accepted else REJECTED
            cells[event.payload["agent_id"]][event.logical_time] = glyph
    return {agent: "".join(row) for agent, row in cells.items()}


def run_trace(run_dir: Path, *, verify_replay: bool = False) -> dict[str, Any]:
    """Verified film strip of one run; a broken ledger yields ``{"broken": reason}``."""
    run_dir = Path(run_dir)
    identity = {"run_id": run_dir.name, "condition_id": run_dir.parent.name,
                "study_id": run_dir.parent.parent.name}
    try:
        events, manifest = _load_sealed_run(run_dir)
        replay = replay_run(run_dir).chains_match if verify_replay else None
    except (ChainError, ValueError, KeyError, OSError) as exc:
        return {**identity, "broken": f"{type(exc).__name__}: {exc}"}

    agents = list(events[0].payload["agents"])
    transitions = [event.payload for event in events
                   if event.event_type == EventType.WORLD_TRANSITIONED]
    votes = [payload for payload in transitions if "cooperative_votes" in payload]
    terminal = events[-1]
    trace: dict[str, Any] = {
        "run_id": manifest["run_id"], "condition_id": manifest["condition_id"],
        "study_id": manifest["study_id"], "replicate": manifest["replicate"],
        "status": manifest["status"], "failure_reason": manifest.get("failure_reason"),
        "policies": {agent: manifest["policies"][agent] for agent in agents},
        "events": len(events), "final_event_hash": terminal.event_hash,
        "parent_run": manifest.get("parent_run"), "fork_seq": manifest.get("fork_seq"),
        "replay_identical": replay,
    }
    if votes:
        trace["kind"] = "nipd"
        trace["strips"] = _nipd_strips(votes, agents)
        trace["cooperation"] = [p["cooperative_votes"] / p["total_votes"] for p in votes]
    else:
        trace["kind"] = "ec"
        trace["strips"] = _ec_strips(events, agents, len(transitions))
        if terminal.event_type == EventType.RUN_COMPLETED:
            payload = terminal.payload
            trace["quality"] = payload["collective_quality"]
            trace["utility"] = payload["utility"]
            trace["effort"] = payload["effort"]
            trace["slots_filled"] = sum(slot["claim_id"] is not None
                                        for slot in payload["briefing"])
            trace["slots"] = len(payload["briefing"])
            trace["slots_correct"] = sum(slot.get("correct") is True
                                         for slot in payload["briefing"])
    return trace


def trace_runs(root: Path, *, verify_replay: bool = False) -> list[dict[str, Any]]:
    return [run_trace(run_dir, verify_replay=verify_replay) for run_dir in find_runs(root)]


def _mean_series(traces: list[dict[str, Any]]) -> list[float]:
    series = [trace["cooperation"] for trace in traces if "cooperation" in trace]
    if not series:
        return []
    length = min(len(row) for row in series)
    return [sum(row[i] for row in series) / len(series) for i in range(length)]


def _spark(values: list[float]) -> str:
    return "".join(SPARK[round(value * (len(SPARK) - 1))] for value in values)


def _group(traces: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    key = lambda trace: (trace["study_id"], trace["condition_id"])  # noqa: E731
    return [(study, condition, list(rows))
            for (study, condition), rows in groupby(sorted(traces, key=key), key=key)]


def _summary(rows: list[dict[str, Any]]) -> str:
    good = [trace for trace in rows if "broken" not in trace]
    parts = [f"{len(good)}/{len(rows)} sealed"]
    mean = _mean_series(good)
    if mean:
        tail = mean[-min(10, len(mean)):]
        parts.append(f"cooperation mean {sum(mean) / len(mean):.2f}"
                     f" final {sum(tail) / len(tail):.2f}")
    qualities = [trace["quality"] for trace in good if "quality" in trace]
    if qualities:
        parts.append(f"quality {min(qualities)}..{max(qualities)}")
    failed = sum(trace["status"] != "completed" for trace in good)
    if failed:
        parts.append(f"{failed} failed")
    replays = [trace["replay_identical"] for trace in good
               if trace["replay_identical"] is not None]
    if replays:
        parts.append(f"replay {sum(replays)}/{len(replays)} identical")
    return ", ".join(parts)


def _short_policy(policy: str) -> str:
    return policy.split("@", maxsplit=1)[0].split("[", maxsplit=1)[0]


def render_text(traces: list[dict[str, Any]]) -> str:
    """Terminal film strip: one line per condition, one sample replicate's agents."""
    lines = []
    for study, condition, rows in _group(traces):
        lines.append(f"{study} / {condition}: {_summary(rows)}")
        mean = _mean_series([trace for trace in rows if "broken" not in trace])
        if mean:
            lines.append(f"  mean |{_spark(mean)}|")
        for trace in rows:
            if "broken" in trace:
                lines.append(f"  BROKEN {trace['run_id']}: {trace['broken']}")
        sample = next((trace for trace in rows if "broken" not in trace), None)
        if sample is not None:
            for agent, strip in sample["strips"].items():
                policy = _short_policy(sample["policies"][agent])
                lines.append(f"  {agent:>4} {policy:<22} {strip}")
    return "\n".join(lines) + "\n"


CSS = """
:root{--bg:#f6f5f1;--panel:#fff;--ink:#1d1f24;--dim:#62666f;--line:#dcdad3;
--c:#1b8a7a;--d:#c2502e;--mix:#d6a02b;--none:#e6e4dd;--ec:#3f5fa8;--bad:#b3202c;--ok:#1b8a7a}
@media (prefers-color-scheme:dark){:root{--bg:#14161a;--panel:#1c1f25;--ink:#e8e8e6;--dim:#9ba0aa;
--line:#30343c;--c:#3cb8a5;--d:#e0714d;--mix:#e4b64a;--none:#2a2e36;--ec:#7f9be0;--bad:#f0606b;
--ok:#3cb8a5}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);padding:24px 16px;
font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1040px;margin:0 auto}
h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 10px}
.dim{color:var(--dim)}.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px}
.note{margin:0 0 18px;color:var(--dim);max-width:70ch}
.tiles{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 8px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 14px}
.tile b{display:block;font-size:20px}.tile.bad b{color:var(--bad)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 14px;
margin:0 0 10px}
.card h3{font-size:14px;margin:0;overflow-wrap:anywhere}.card p{margin:2px 0 8px;color:var(--dim)}
.card.bad{border-color:var(--bad)}.broken{color:var(--bad);overflow-wrap:anywhere}
.heat{display:grid;gap:1px;width:100%}.heat i{display:block;height:7px;
background:color-mix(in srgb,var(--c) var(--p),var(--d))}
.strip{display:grid;gap:1px;grid-template-columns:minmax(52px,150px) repeat(var(--n),minmax(0,1fr));
align-items:center;margin-top:6px}
.strip .who{font-size:12px;color:var(--dim);overflow:hidden;white-space:nowrap;
text-overflow:ellipsis;padding-right:6px}
.strip b{display:block;font:600 10px/16px ui-monospace,Consolas,monospace;text-align:center;
color:#fff;background:var(--none);overflow:hidden}
.g-C{background:var(--c)!important}.g-D{background:var(--d)!important}
.g-m{background:var(--mix)!important}.g-e{background:var(--ec)!important}
.g-r{background:var(--bad)!important}.g-n{color:var(--dim)!important}
svg.curve{display:block;width:100%;height:44px;margin:0 0 8px}
svg.curve polyline{fill:none;stroke:var(--c);stroke-width:2;vector-effect:non-scaling-stroke}
svg.curve line{stroke:var(--line);vector-effect:non-scaling-stroke}
details{margin-top:8px}summary{cursor:pointer;color:var(--dim);font-size:13px}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--dim);margin:6px 0 16px}
.legend span{display:inline-flex;gap:5px;align-items:center}
.legend b{width:14px;height:14px;display:inline-block;background:var(--none)}
"""

LEGEND = (
    '<div class="legend"><span><b class="g-C"></b>cooperate</span>'
    '<span><b class="g-D"></b>defect</span><span><b class="g-m"></b>mixed pairwise</span>'
    '<span><b class="g-e"></b>Evidence Commons action: i inspect, s share, p propose, '
    'v verify, x challenge, a approve, w withhold</span>'
    '<span><b class="g-r"></b>rejected</span><span><b></b>no action</span></div>'
)


def _glyph_class(glyph: str) -> str:
    if glyph in ("C", "D"):
        return f"g-{glyph}"
    if glyph == "+":
        return "g-m"
    if glyph == REJECTED:
        return "g-r"
    return "g-n" if glyph in (NO_ACTION, ".", "w") else "g-e"


def _strip_html(trace: dict[str, Any]) -> str:
    rounds = max(len(strip) for strip in trace["strips"].values())
    cells = []
    for agent, strip in trace["strips"].items():
        policy = escape(trace["policies"][agent])
        cells.append(f'<span class="who" title="{policy}">{escape(agent)} '
                     f'{escape(_short_policy(trace["policies"][agent]))}</span>')
        cells += [f'<b class="{_glyph_class(glyph)}">{escape(glyph)}</b>' for glyph in strip]
    return (f'<div class="mono dim">{escape(trace["run_id"])} · {trace["events"]} events · '
            f'{trace["final_event_hash"][:12]}</div>'
            f'<div class="strip" style="--n:{rounds}">{"".join(cells)}</div>')


def _heat_html(rows: list[dict[str, Any]]) -> str:
    series = [trace["cooperation"] for trace in rows if "cooperation" in trace]
    if not series:
        return ""
    columns = max(len(row) for row in series)
    cells = "".join(f'<i style="--p:{round(value * 100)}%"></i>'
                    for row in series for value in row)
    return (f'<div class="heat" style="grid-template-columns:repeat({columns},minmax(0,1fr))" '
            f'role="img" aria-label="cooperation rate by round for each replicate">{cells}</div>')


def _curve_html(mean: list[float]) -> str:
    if len(mean) < 2:
        return ""
    points = " ".join(f"{i * 100 / (len(mean) - 1):.2f},{40 - value * 36:.2f}"
                      for i, value in enumerate(mean))
    return (f'<svg class="curve" viewBox="0 0 100 44" preserveAspectRatio="none" role="img" '
            f'aria-label="mean cooperation by round"><line x1="0" x2="100" y1="4" y2="4"/>'
            f'<line x1="0" x2="100" y1="40" y2="40"/><polyline points="{points}"/></svg>')


def _card_html(condition: str, rows: list[dict[str, Any]], max_detail: int) -> str:
    good = [trace for trace in rows if "broken" not in trace]
    bad = [trace for trace in rows if "broken" in trace]
    failed = any(trace["status"] != "completed" for trace in good)
    body = [f'<div class="card{" bad" if bad or failed else ""}">',
            f'<h3>{escape(condition)}</h3><p>{escape(_summary(rows))}</p>',
            _curve_html(_mean_series(good)), _heat_html(good)]
    body += [f'<div class="broken">BROKEN {escape(trace["run_id"])}: {escape(trace["broken"])}'
             '</div>' for trace in bad]
    if good:
        body.append(_strip_html(good[0]))
    extra = good[1:max_detail]
    if extra:
        strips = "".join(_strip_html(trace) for trace in extra)
        body.append(f'<details><summary>{len(extra)} more of {len(good)} replicates</summary>'
                    f'{strips}</details>')
    body.append("</div>")
    return "".join(body)


def render_html(traces: list[dict[str, Any]], *, max_detail: int = 4) -> str:
    groups = _group(traces)
    broken = sum("broken" in trace for trace in traces)
    failed = sum(trace.get("status") == "failed" for trace in traces)
    tiles = [("runs", len(traces), False), ("conditions", len(groups), False),
             ("broken ledgers", broken, broken > 0), ("failed runs", failed, failed > 0)]
    replays = [trace["replay_identical"] for trace in traces
               if trace.get("replay_identical") is not None]
    if replays:
        tiles.append(("replay identical", f"{sum(replays)}/{len(replays)}",
                      not all(replays)))
    tile_html = "".join(f'<div class="tile{" bad" if bad else ""}"><b>{value}</b>'
                        f'<span class="dim">{name}</span></div>' for name, value, bad in tiles)
    sections = []
    for study, study_groups in groupby(groups, key=lambda group: group[0]):
        cards = "".join(_card_html(condition, rows, max_detail)
                        for _, condition, rows in study_groups)
        sections.append(f"<h2>{escape(study)}</h2>{cards}")
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Lab Console</title><style>{CSS}</style></head><body><main>"
        "<h1>Lab Console</h1>"
        '<p class="note">Derived only from hash-verified sealed ledgers. Runs here are '
        "deterministic simulations; nothing on this page is a prediction about people or LLMs."
        f'</p><div class="tiles">{tile_html}</div>{LEGEND}{"".join(sections)}'
        "</main></body></html>\n"
    )


def write_console(root: Path, out: Path | None, *, verify_replay: bool = False,
                  max_detail: int = 4) -> tuple[str, list[dict[str, Any]]]:
    traces = trace_runs(root, verify_replay=verify_replay)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_html(traces, max_detail=max_detail), encoding="utf-8")
    return render_text(traces), traces
