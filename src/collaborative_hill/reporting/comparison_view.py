"""Self-contained, read-only views of the existing descriptive run comparison.

No metrics or world state are recomputed here. The comparator supplies its exact
result and verified events; the inspector supplies the per-round projection.
"""

import json
from html import escape
from pathlib import Path
from typing import Any

from collaborative_hill.engine.events import Event
from collaborative_hill.reporting.comparison import compare_runs_with_events
from collaborative_hill.reporting.export import write_new_text
from collaborative_hill.reporting.inspector import round_frames
from collaborative_hill.reporting.provenance import display_fork_seq

SIDES = ("left", "right")
METADATA = (
    ("mechanism_hash", "Mechanism hash"),
    ("scenario_hash", "Scenario hash"),
    ("narrative_hash", "Narrative hash"),
    ("evidence_corpus_hash", "Evidence corpus hash"),
    ("policy_ids", "Effective policy labels"),
    ("seed_protocol", "Seed protocol"),
    ("seed_root", "Recorded mechanism seed root"),
    ("policy_seed_root", "Recorded policy seed root"),
    ("scenario_block", "Scenario block"),
)


def _value(value: Any) -> str:
    if value is None:
        return "Not separately recorded"
    if isinstance(value, str):
        return escape(value)
    return escape(json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2))


def _source(side: str, path: Path, summary: dict[str, Any], events: list[Event],
            fork: int | None) -> str:
    fields = [("Source directory", str(path.resolve())),
              *((key.replace("_", " ").title(), summary[key]) for key in (
                  "study_id", "condition_id", "run_id", "status", "final_event_hash"))]
    identity = "".join(f"<dt>{label}</dt><dd>{_value(value)}</dd>" for label, value in fields)
    if fork is None:
        ancestry = "No branch ancestry recorded in this artifact."
    else:
        ancestry = (
            f'Parent run label: {_value(summary["parent_run"])}<br>'
            f"Inherited through event {fork}; continuation begins at logical round "
            f"{events[fork + 1].logical_time}.<br>"
            f"Fork event hash: {_value(events[fork].event_hash)}"
        )
    return (f'<section class="source {side}" id="source-{side}"><h2>{side.title()}</h2>'
            f'<dl>{identity}</dl><p id="ancestry-{side}">{ancestry}</p></section>')


def _compatibility(summary: dict[str, Any]) -> str:
    rows, differences = [], []
    for key, label in METADATA:
        left, right = summary["left"][key], summary["right"][key]
        if left != right:
            verdict, style = "Differ", "difference"
            differences.append(label)
        elif left is None:
            verdict, style = "Not separately recorded", "muted"
        else:
            verdict, style = "Match", "match"
        rows.append(f'<tr id="meta-{key}"><th scope="row">{label}</th>'
                    f'<td class="{style}">{verdict}</td><td><pre>{_value(left)}</pre></td>'
                    f'<td><pre>{_value(right)}</pre></td></tr>')
    confounds = ("Confounds / differing recorded configuration: " + ", ".join(differences)
                 if differences else "Listed configuration metadata match.")
    streams = "Match" if summary["same_kernel_streams"] else "Differ"
    return ('<section id="compatibility"><h2>Compatibility and confounds</h2>'
            f'<p class="notice">{confounds} Interpret the comparison descriptively.</p>'
            '<details><summary>Inspect full configuration values</summary>'
            '<div class="table-scroll"><table><thead><tr><th>Metadata</th><th>Comparison</th>'
            '<th>Left</th><th>Right</th></tr></thead><tbody>' + "".join(rows)
            + '</tbody></table></div></details><p id="kernel-streams">'
            f'Effective kernel streams: <strong>{streams}</strong>. '
            'The existing comparator normalizes integer/string seed aliases and uses the '
            'mechanism root when no separate policy root is recorded. Equal kernel streams '
            'do not guarantee equal actions, provider sampling or variance.</p></section>')


def _utilities(summary: dict[str, Any]) -> str:
    if summary["utility_delta"] is None:
        body = '<p>Outcome comparison unavailable: at least one episode did not complete.</p>'
    else:
        rows = "".join(
            f'<tr><th scope="row">{escape(agent)}</th><td>{_value(left)}</td>'
            f'<td>{_value(summary["right"]["utilities_exact"][agent])}</td>'
            f'<td>{_value(summary["utility_delta"][agent])}</td></tr>'
            for agent, left in summary["left"]["utilities_exact"].items()
        )
        body = ('<table><thead><tr><th>Agent</th><th>Left</th><th>Right</th>'
                '<th>Right − Left</th></tr></thead><tbody>' + rows + '</tbody></table>')
    return ('<section id="utilities"><h2>Exact full-episode utilities</h2>'
            '<p>These are the existing comparison totals, including shared pre-fork history. '
            'Fractions are retained exactly; no averages or significance tests are added.</p>'
            f'{body}</section>')


def _records(frame: dict[str, Any] | None, buckets: tuple[str, ...],
             agent: str | None = None) -> list[dict[str, Any]]:
    if frame is None:
        return []
    return sorted((event for bucket in buckets for event in frame[bucket]
                   if agent is None or event["payload"].get("agent_id", event["actor"]) == agent),
                  key=lambda event: event["seq"])


def _events_panel(side: str, panel_id: str, frame: dict[str, Any] | None,
                  records: list[dict[str, Any]], missing: str, prefix: int) -> str:
    body = []
    for event in records:
        provenance = " · inherited prefix" if event["inherited"] else ""
        if event["seq"] < prefix:
            provenance += " · shared leading event hash"
        expanded = ' open' if event["event_type"] in {
            "ObservationIssued", "ActionProposed", "ActionAccepted", "ActionRejected",
        } else ""
        body.append(
            f'<article class="event"><p><strong>{escape(event["event_type"])}</strong> '
            f'· event {event["seq"]} · {escape(event["run_id"])}{provenance}</p>'
            f'<details{expanded}><summary>Exact recorded payload</summary><pre>'
            f'{_value(event["payload"])}</pre></details></article>'
        )
    if not body:
        message = "No frame recorded at this logical time." if frame is None else missing
        body.append(f'<p class="missing">{message}</p>')
    return (f'<section class="panel {side}" id="{panel_id}"><h4>{side.title()}</h4>'
            + "".join(body) + "</section>")


def _agent_comparison(round_index: int, index: int, agent: str,
                      frames: dict[str, dict[str, Any] | None], prefix: int) -> str:
    sections = []
    for bucket, label, missing in (
        ("observations", "Before actions · agent observation", "No observation recorded."),
        ("actions", "Recorded actions", "No action recorded for agent."),
    ):
        records = {side: _records(frames[side], (bucket,), agent) for side in SIDES}
        if not records["left"] or not records["right"]:
            verdict = "Missing recorded events on one or both sides."
        else:
            payloads = [[(event["event_type"], event["payload"]) for event in records[side]]
                        for side in SIDES]
            verdict = ("Recorded payloads match." if payloads[0] == payloads[1]
                       else "Recorded payloads differ.")
        panels = "".join(_events_panel(
            side, f"round-{round_index}-agent-{index}-{side}-{bucket}", frames[side], records[side],
            missing, prefix,
        ) for side in SIDES)
        sections.append(f'<h4>{label}</h4><p class="muted">{verdict}</p>'
                        f'<div class="pair">{panels}</div>')
    return (f'<section class="agent" data-agent="{index}"><h3>{escape(agent)}</h3>'
            + "".join(sections) + "</section>")


def _round(round_index: int, frames: dict[str, dict[str, Any] | None],
           agents: list[str], prefix: int) -> str:
    body = "".join(_agent_comparison(round_index, i, agent, frames, prefix)
                   for i, agent in enumerate(agents))
    outcomes = "".join(_events_panel(
        side, f"round-{round_index}-{side}-outcomes", frames[side],
        _records(frames[side], ("audits", "outcomes", "checkpoints", "terminal")),
        "No audit, outcome, checkpoint or seal recorded at this logical time.", prefix,
    ) for side in SIDES)
    return (f'<section class="comparison-round" id="round-{round_index}" '
            f'data-round="{round_index}"><h2>Logical round {round_index}</h2>{body}'
            '<details class="outcomes"><summary>Public audits and later outcomes · '
            'researcher view</summary><p>These events are not added to earlier agent '
            f'observations.</p><div class="pair">{outcomes}</div></details></section>')


def render_comparison(summary: dict[str, Any], sources: dict[str, Path],
                      events: dict[str, list[Event]]) -> str:
    """Render only comparator-verified inputs; escape every data-derived text node."""
    forks = {side: display_fork_seq(events[side], summary[side]) for side in SIDES}
    frames = {side: {frame["round"]: frame for frame in round_frames(
        events[side], forks[side])} for side in SIDES}
    rounds = sorted(frames["left"].keys() | frames["right"].keys())
    agents = sorted(summary["left"]["policy_ids"].keys() | summary["right"]["policy_ids"].keys())
    identities = "".join(_source(side, sources[side], summary[side], events[side], forks[side])
                         for side in SIDES)
    notes = "".join(f"<li>{escape(note)}</li>" for note in summary["notes"])
    replay = ("Recorded-action replay verified for both runs." if summary["replay_verified"]
              else "Recorded-action replay not requested.")
    round_options = "".join(f'<option value="{value}">{value}</option>' for value in rounds)
    agent_options = "".join(f'<option value="{i}">{escape(agent)}</option>'
                            for i, agent in enumerate(agents))
    body = "".join(_round(value, {side: frames[side].get(value) for side in SIDES}, agents,
                          summary["common_prefix_events"]) for value in rounds)
    first_difference = (_value(summary["first_action_difference"])
                        if summary["first_action_difference"] is not None
                        else "No proposed-action difference found.")
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        'style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; base-uri \'none\'">'
        f'<title>Run comparison · Collaborative Hill Lab</title><style>{CSS}</style></head>'
        '<body><main><header><p class="eyebrow">Collaborative Hill Lab · offline evidence view</p>'
        '<h1>Compare two runs</h1><p>Describe what changed in recorded artifacts.</p>'
        '<a href="#alignment-title">Inspect aligned rounds</a></header>'
        '<section class="notice" id="interpretation"><strong>Descriptive comparison only.</strong>'
        f'<details><summary>Interpretation limits</summary><ul>{notes}</ul></details>'
        '<p>Matching IDs, hashes or separate directories do not prove independent '
        'replicates. Shared history is not an additional replicate; no causal effect or provider '
        'sampling correspondence is inferred.</p></section>'
        f'<p id="validation">Both seals and recorded provenance validated. {replay} '
        'Replay uses recorded actions and does not call providers.</p>'
        f'<div class="pair">{identities}</div>{_compatibility(summary)}'
        '<section id="ancestry"><h2>Shared history and branch ancestry</h2>'
        f'<p>Shared leading event hashes: <strong>{summary["common_prefix_events"]}</strong>. '
        'This counts an identical leading ledger segment, not independent evidence. '
        'Parent IDs are recorded labels; no parent directory is read.</p>'
        '<details><summary>First proposed-action difference</summary><pre>'
        f'{first_difference}</pre></details></section>'
        f'{_utilities(summary)}<section aria-labelledby="alignment-title">'
        '<h2 id="alignment-title">Aligned observations and actions</h2>'
        '<p>Logical times are zero-based and aligned by their recorded number. Missing frames '
        'and events remain explicit. Payload equality excludes event envelope hashes and run IDs; '
        'it is not an outcome or causal estimate.</p>'
        '<div class="controls"><label>Logical round <select id="compare-round">'
        f'{round_options}<option value="all">All recorded rounds</option></select></label>'
        f'<label>Agent perspective <select id="compare-agent">{agent_options}'
        '<option value="all">All agents</option></select></label></div>'
        '<p class="muted" id="selection-status" role="status" aria-live="polite"></p>'
        '<noscript><p>All rounds and agents are shown. Enable JavaScript to use the offline '
        f'filters.</p></noscript>{body}</section>'
        '<details><summary>Original comparison JSON</summary>'
        f'<pre id="comparison-json">{_value(summary)}</pre></details></main>'
        f'<script>{JS}</script></body></html>\n'
    )


def _output_path(left: Path, right: Path, out: Path) -> Path:
    target = out.resolve()
    if any(target.is_relative_to(source.resolve()) for source in (left, right)):
        raise ValueError("comparison output must be outside both source evidence directories")
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"comparison output already exists: {out}")
    return target


def write_comparison(left: Path, right: Path, out: Path, *,
                     verify_replay: bool = False) -> dict[str, Any]:
    """Create a fresh HTML file outside both sources and return unchanged comparison JSON."""
    left, right, out = Path(left), Path(right), Path(out)
    _output_path(left, right, out)
    summary, events = compare_runs_with_events(left, right, verify_replay=verify_replay)
    # Invalid ancestry must fail before creating even an output parent. Rendering
    # then runs with destination ancestry pinned by the shared exclusive writer.
    for side in SIDES:
        display_fork_seq(events[side], summary[side])
    write_new_text(out, (left, right), lambda: render_comparison(
        summary, {"left": left, "right": right}, events))
    return summary


CSS = """
:root{color-scheme:light dark;--bg:#f6f5f1;--panel:#fff;--ink:#1d2731;--dim:#647182;
--line:#deddd6;--left:#1b8a7a;--right:#a66c1d;--bad:#b3202c}
@media(prefers-color-scheme:dark){:root{--bg:#14161a;--panel:#1c1f25;--ink:#e8e8e6;
--dim:#9ba0aa;--line:#30343c;--left:#3cb8a5;--right:#e4b64a;--bad:#f0606b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 system-ui,sans-serif}main{max-width:1250px;margin:auto;padding:28px}
h1{font-size:36px;margin:0}h2{font-size:22px;margin:24px 0 10px}h3{font-size:18px}
h4{font-size:15px;margin:12px 0 5px}p{margin:8px 0}.eyebrow,.muted{color:var(--dim)}
a{color:var(--left)}
.eyebrow{text-transform:uppercase;font-size:12px;letter-spacing:.08em}.pair{display:grid;
grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.source,.panel,.agent,.notice,.outcomes{
padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--panel);min-width:0}
.source,.panel{border-top:3px solid}.left{border-top-color:var(--left)}
.right{border-top-color:var(--right)}.source h2,.panel h4{margin-top:0}
.notice{margin:18px 0}.notice ul{padding-left:22px}dt{font-size:12px;color:var(--dim)}
dd{margin:0 0 10px;overflow-wrap:anywhere;font-family:ui-monospace,monospace;font-size:13px}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13px}th,td{padding:9px;
text-align:left;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}
th{color:var(--dim)}pre{margin:8px 0;white-space:pre-wrap;overflow-wrap:anywhere;
font:12px/1.5 ui-monospace,Consolas,monospace;max-height:340px;overflow:auto}
td pre{margin:0;max-width:330px;max-height:180px}.difference,.missing{color:var(--bad)}
.match{color:var(--left)}.controls{display:flex;gap:20px;flex-wrap:wrap;margin:18px 0}
label{display:block;font-size:13px;color:var(--dim)}select{display:block;margin-top:5px;
padding:10px;background:var(--panel);color:var(--ink);border:1px solid var(--line);
border-radius:5px;font:inherit;max-width:100%}:focus-visible{outline:3px solid var(--left);
outline-offset:3px}.agent{margin:16px 0}.agent>h3{margin:0}.event{border-top:1px solid var(--line);
padding:8px 0;overflow-wrap:anywhere}.event p{font-size:12px;color:var(--dim)}
details{margin:10px 0}summary{cursor:pointer;color:var(--ink)}.source p{overflow-wrap:anywhere;
font-size:13px}.table-scroll{overflow:auto}[hidden]{display:none!important}
@media(max-width:720px){main{padding:16px}.pair{grid-template-columns:1fr}h1{font-size:28px}
th,td{padding:6px}.source,.panel,.agent,.notice{padding:12px}}
"""

JS = """
(() => {
  'use strict';
  const round = document.getElementById('compare-round');
  const agent = document.getElementById('compare-agent');
  const refresh = () => {
    document.querySelectorAll('.comparison-round').forEach(node => {
      node.hidden = round.value !== 'all' && node.dataset.round !== round.value;
    });
    document.querySelectorAll('.agent').forEach(node => {
      node.hidden = agent.value !== 'all' && node.dataset.agent !== agent.value;
    });
    document.getElementById('selection-status').textContent =
      (round.value === 'all' ? 'All recorded rounds' : 'Logical round ' + round.value) +
      ' · ' + agent.options[agent.selectedIndex].textContent;
  };
  round.addEventListener('change', refresh);
  agent.addEventListener('change', refresh);
  refresh();
})();
"""
