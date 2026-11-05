"""Offline, read-only inspection of event payloads from an already validated run.

Observations are agent-specific snapshots, not reconstructed world state. Only
the caller's verified events are used: never checkpoints, private scenario truth,
provider transcripts, or unhashed event metadata.
"""

import json
from typing import Any

from collaborative_hill.engine.events import Event, EventType


def round_frames(events: list[Event], fork_seq: int | None = None) -> list[dict[str, Any]]:
    """Keep event order and exact logical times, including unresolved and seal-only times."""
    frames: dict[int, dict[str, Any]] = {}
    for event in events:
        if event.event_type == EventType.RUN_STARTED:
            continue
        frame = frames.setdefault(event.logical_time, {
            "round": event.logical_time, "observations": [], "actions": [],
            "audits": [], "outcomes": [], "checkpoints": [], "terminal": [],
        })
        record = {"seq": event.seq, "event_type": event.event_type.value,
                  "actor": event.actor, "run_id": event.run_id, "payload": event.payload,
                  "event_hash": event.event_hash,
                  "inherited": fork_seq is not None and event.seq <= fork_seq}
        if event.event_type == EventType.OBSERVATION_ISSUED:
            bucket = "observations"
        elif event.event_type in (EventType.ACTION_PROPOSED, EventType.ACTION_ACCEPTED,
                                 EventType.ACTION_REJECTED):
            bucket = "actions"
        elif event.event_type == EventType.AUDIT_PUBLISHED:
            bucket = "audits"
        elif event.event_type == EventType.CHECKPOINT_CREATED:
            bucket = "checkpoints"
        elif event.event_type in (EventType.RUN_COMPLETED, EventType.RUN_FAILED):
            bucket = "terminal"
        else:
            bucket = "outcomes"
        frame[bucket].append(record)
    return [frames[t] for t in sorted(frames)]


def render_inspector(traces: list[dict[str, Any]]) -> str:
    """Embed inert JSON and a dependency-free UI; broken traces never enter the selector."""
    runs = [{key: trace.get(key) for key in (
        "study_id", "condition_id", "run_id", "replicate", "kind", "status",
        "failure_reason", "policies", "parent_run", "fork_round", "fork_seq",
        "final_event_hash", "replay_identical", "frames",
    )} for trace in traces if "broken" not in trace and trace.get("frames")]
    if not runs:
        return ""
    # HTML parsers recognize </script> even for application/json. Escape HTML
    # delimiters here; all parsed strings later enter the DOM via textContent.
    data = json.dumps(runs, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    data = data.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    return (f"<style>{INSPECTOR_CSS}</style>{INSPECTOR_HTML}"
            f'<script type="application/json" id="inspection-data">{data}</script>'
            f"<script>{INSPECTOR_JS}</script>")


INSPECTOR_CSS = """
.inspector{margin:22px 0;padding:18px;border:1px solid var(--line);border-radius:10px;
background:var(--panel)}.inspector h2{margin:0 0 6px;font-size:20px}
.inspector h3{margin:0 0 10px;font-size:16px}.inspector h4{margin:10px 0 4px;font-size:14px}
.inspector label{display:block;font-size:12px;color:var(--dim);font-weight:600}
.inspect-controls{display:grid;grid-template-columns:minmax(0,2fr) minmax(130px,1fr);
gap:12px;margin:14px 0}.inspect-controls select{width:100%;margin-top:4px}
.inspector select,.inspector button{font:inherit;color:var(--ink);background:var(--bg);
border:1px solid var(--line);border-radius:5px;padding:7px;max-width:100%}
.inspector button{cursor:pointer}.inspector button:disabled{opacity:.4;cursor:default}
.inspector :focus-visible{outline:3px solid var(--ec);outline-offset:2px}
.inspect-round{display:flex;align-items:center;gap:12px;margin:14px 0;flex-wrap:wrap}
.inspect-round input{flex:1;min-width:130px;accent-color:var(--ec)}
.inspect-round label{min-width:160px}.inspect-grid{display:grid;
grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.inspect-panel{padding:14px;border:1px solid var(--line);border-radius:7px;min-width:0}
.inspect-panel.wide{grid-column:1/-1}.inspector p{margin:6px 0 10px}
.inspector pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:320px;overflow:auto;
background:var(--bg);padding:10px;font:12px/1.45 ui-monospace,Consolas,monospace}
.inspector table{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0}
.inspector td,.inspector th{padding:6px;text-align:left;border-bottom:1px solid var(--line);
overflow-wrap:anywhere}.inspector th{color:var(--dim);font-weight:600}
.inspect-event{padding:8px 10px;margin:7px 0;background:var(--bg);border-radius:5px;
overflow-wrap:anywhere}.inspect-event.rejected{border-left:3px solid var(--bad)}
.inspect-event.accepted{border-left:3px solid var(--c)}
.inspect-event.audit{border-left:3px solid var(--ec)}
.inspect-meta{font-size:12px;color:var(--dim);overflow-wrap:anywhere}
.inspect-summary{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 12px}
.inspect-summary span{border:1px solid var(--line);padding:5px 8px;border-radius:4px;
font-size:12px}.inspect-network{width:100%;max-height:260px;display:block}
.inspect-network text{fill:var(--ink);font:12px system-ui,sans-serif}
.inspect-network circle{fill:var(--panel);stroke:var(--line);stroke-width:2}
.inspect-network line{stroke-width:4}.inspect-network .both-c{stroke:var(--c)}
.inspect-network .both-d{stroke:var(--d)}.inspect-network .mixed{stroke:var(--mix)}
#inspect-run-status{border-bottom:1px solid var(--line);padding-bottom:12px}
@media(max-width:680px){.inspect-grid,.inspect-controls{grid-template-columns:1fr}
.inspector{padding:12px}.inspect-panel{padding:10px}.inspect-round{gap:8px}}
"""

INSPECTOR_HTML = """
<section class="inspector" id="run-inspector" hidden aria-labelledby="inspector-title">
<h2 id="inspector-title">Inspect a run</h2>
<p class="dim">Choose any verified run and logical round. Observations are what one agent
received before acting. Outcomes are recorded later; they are not added to that observation.</p>
<div class="inspect-controls">
<label>Run <select id="inspect-run"></select></label>
<label>Agent perspective <select id="inspect-agent"></select></label></div>
<div id="inspect-run-status"></div>
<div class="inspect-round">
<button id="inspect-prev" type="button" aria-label="Previous recorded round">Previous</button>
<label id="inspect-round-label" for="inspect-round">Logical round</label>
<input id="inspect-round" type="range" min="0" value="0" step="1">
<button id="inspect-next" type="button" aria-label="Next recorded round">Next</button></div>
<div id="inspect-round-status" class="inspect-meta" role="status" aria-live="polite"></div>
<div class="inspect-grid">
<section class="inspect-panel"><h3>Before actions · agent observation</h3>
<div id="inspect-observation"></div></section>
<section class="inspect-panel"><h3>Actions in this round</h3>
<div id="inspect-actions"></div></section>
<section class="inspect-panel"><h3>Public audit publications</h3>
<div id="inspect-audits"></div></section>
<section class="inspect-panel"><h3>Round outcomes · researcher view</h3>
<div id="inspect-outcomes"></div></section>
<section class="inspect-panel wide"><h3>Recorded state references and seal</h3>
<div id="inspect-seals"></div></section></div></section>
<noscript><p class="dim">Enable JavaScript for the offline round inspector.
The verified run summaries below remain available.</p></noscript>
"""

INSPECTOR_JS = r"""
(() => {
  'use strict';
  const runs = JSON.parse(document.getElementById('inspection-data').textContent);
  const el = id => document.getElementById(id);
  const runSelect = el('inspect-run'), agentSelect = el('inspect-agent');
  const slider = el('inspect-round');
  const add = (parent, tag, text, cls = '') => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    if (cls) node.className = cls;
    parent.appendChild(node);
    return node;
  };
  const json = (parent, value, label = 'Exact recorded JSON') => {
    const detail = add(parent, 'details');
    add(detail, 'summary', label);
    add(detail, 'pre', JSON.stringify(value, null, 2));
  };
  const text = value => value === null || value === undefined ? 'not recorded' : String(value);
  const table = (parent, headers, rows) => {
    const node = add(parent, 'table'), head = add(node, 'thead');
    const tr = add(head, 'tr');
    headers.forEach(h => add(tr, 'th', h));
    const body = add(node, 'tbody');
    rows.forEach(row => {
      const line = add(body, 'tr');
      row.forEach(cell => add(line, 'td', text(cell)));
    });
  };
  const chips = (parent, values) => {
    const row = add(parent, 'div', undefined, 'inspect-summary');
    values.forEach(value => add(row, 'span', value));
  };
  const ref = (parent, event) => {
    add(parent, 'div', `Event ${event.seq} · ${event.run_id}` +
      (event.inherited ? ' · inherited prefix' : ''), 'inspect-meta');
  };
  const eventCard = (parent, event, heading, cls = '') => {
    const card = add(parent, 'div', undefined, `inspect-event ${cls}`);
    add(card, 'strong', heading);
    ref(card, event);
    json(card, event.payload);
    return card;
  };
  const auditCard = (parent, report) => {
    const card = add(parent, 'div', undefined, 'inspect-event audit');
    add(card, 'strong', `${text(report.slot_id)} · ${text(report.proposition_id)}`);
    add(card, 'div', `Published round ${text(report.publish_round)} · ${text(report.verdict)}`);
    return card;
  };
  function observation(parent, event) {
    const obs = event.payload.observation;
    ref(parent, event);
    add(parent, 'p', 'This snapshot may include evidence available only to the selected agent.',
      'dim');
    if (obs.mechanism === 'evidence_commons') {
      chips(parent, [`${(obs.evidence || []).length} visible evidence items`,
        `${(obs.evidence || []).filter(item => item.facts !== undefined).length} inspected`,
        `${(obs.claims || []).length} visible claims`, `Effort ${text(obs.my_effort_spent)}`]);
      table(parent, ['Own budget', 'Remaining'], Object.entries(obs.my_budgets || {}));
      add(parent, 'h4', 'Claims visible before actions');
      if (!(obs.claims || []).length) add(parent, 'p', 'No claims in this observation.', 'dim');
      (obs.claims || []).forEach(claim => {
        const card = add(parent, 'div', undefined, 'inspect-event');
        add(card, 'strong', `${claim.claim_id} · ${claim.slot_id}: ${claim.proposition_id}`);
        add(card, 'div', `Support ${text(claim.net_support)} · ` +
          `${text(claim.n_verifications)} verifications · ${text(claim.n_challenges)} challenges`);
        json(card, claim);
      });
      add(parent, 'h4', 'Audit channel in this observation');
      if (!Object.hasOwn(obs, 'audit')) {
        add(parent, 'p', 'No audit channel recorded in this observation.', 'dim');
      } else if (!obs.audit.reports.length) {
        add(parent, 'p', 'Audit channel present; no reports published yet.', 'dim');
      } else {
        obs.audit.reports.forEach(report => auditCard(parent, report));
      }
    } else {
      chips(parent, [text(obs.mechanism), text(obs.mode), `${text(obs.n_agents)} agents`]);
      if (obs.mode === 'pairwise') {
        add(parent, 'h4', 'Previous round as observed');
        if (obs.moves_against_me === null) {
          add(parent, 'p', 'No previous-round moves observed.', 'dim');
        } else {
          table(parent, ['Opponent', 'Their move toward me', 'My move toward them'],
            (obs.opponents || []).map(id => [id, (obs.moves_against_me || {})[id],
              (obs.my_last_moves || {})[id]]));
        }
      } else {
        table(parent, ['Previous-round observation', 'Value'], [
          ['Other cooperators', obs.others_cooperated_last_round],
          ['My move', obs.my_last_move]]);
      }
    }
    json(parent, obs, 'Full agent observation');
  }
  function network(parent, pairs, agents) {
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 400 260');
    svg.setAttribute('class', 'inspect-network');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Recorded pairwise interactions; exact directions in table');
    const points = new Map(agents.map((agent, i) => {
      const angle = -Math.PI / 2 + 2 * Math.PI * i / agents.length;
      return [agent, [200 + 100 * Math.cos(angle), 130 + 90 * Math.sin(angle)]];
    }));
    pairs.forEach(pair => {
      const a = points.get(pair.a), b = points.get(pair.b);
      if (!a || !b) return;
      const line = document.createElementNS(ns, 'line');
      ['x1', 'y1', 'x2', 'y2'].forEach((name, i) =>
        line.setAttribute(name, [a[0], a[1], b[0], b[1]][i]));
      line.setAttribute('class', pair.move_ab === pair.move_ba ?
        (pair.move_ab === 'C' ? 'both-c' : 'both-d') : 'mixed');
      const title = document.createElementNS(ns, 'title');
      title.textContent = `${pair.a} → ${pair.b}: ${pair.move_ab}; ` +
        `${pair.b} → ${pair.a}: ${pair.move_ba}`;
      line.appendChild(title); svg.appendChild(line);
    });
    points.forEach(([x, y], agent) => {
      const circle = document.createElementNS(ns, 'circle');
      circle.setAttribute('cx', x); circle.setAttribute('cy', y); circle.setAttribute('r', 18);
      svg.appendChild(circle);
      const label = document.createElementNS(ns, 'text');
      label.setAttribute('x', x); label.setAttribute('y', y + 4);
      label.setAttribute('text-anchor', 'middle'); label.textContent = agent;
      svg.appendChild(label);
    });
    parent.appendChild(svg);
    add(parent, 'p', 'Teal: both cooperate · red: both defect · amber: different moves. ' +
      'Edges are recorded interactions; isolated roster members stay visible.', 'inspect-meta');
    table(parent, ['From', 'To', 'Forward move', 'Reverse move'],
      pairs.map(pair => [pair.a, pair.b, pair.move_ab, pair.move_ba]));
  }
  function draw() {
    const run = runs[Number(runSelect.value)], frame = run.frames[Number(slider.value)];
    el('inspect-round-label').textContent = `Logical round ${frame.round} (zero-based)`;
    el('inspect-prev').disabled = Number(slider.value) === 0;
    el('inspect-next').disabled = Number(slider.value) === run.frames.length - 1;
    const events = Object.values(frame).filter(Array.isArray).flat();
    const inherited = events.filter(event => event.inherited).length;
    el('inspect-round-status').textContent = `${events.length} recorded events · ` +
      `${frame.observations.length} observations · ${frame.actions.length} action events` +
      (inherited ? ` · ${inherited} inherited events` : '') +
      (frame.terminal.length && !frame.observations.length ? ' · seal-only logical time' : '');
    const obsPanel = el('inspect-observation'); obsPanel.replaceChildren();
    const obs = frame.observations.find(event => event.payload.agent_id === agentSelect.value);
    if (obs) observation(obsPanel, obs);
    else add(obsPanel, 'p', 'No observation recorded for this agent at this logical time. ' +
      'Do not infer an empty world or carry earlier knowledge forward.', 'dim');
    const actions = el('inspect-actions'); actions.replaceChildren();
    if (!frame.actions.length) {
      add(actions, 'p', 'No actions recorded at this logical time.', 'dim');
    }
    frame.actions.forEach(event => {
      const p = event.payload, action = p.action || (p.proposal || {}).action || {};
      const verdict = event.event_type.replace('Action', '');
      const card = eventCard(actions, event,
        `${p.agent_id}: ${text(action.type)} · ${verdict}` + (p.fallback ? ' (fallback)' : ''),
        verdict.toLowerCase());
      if (p.reason) add(card, 'p', p.reason, 'broken');
    });
    const audits = el('inspect-audits'); audits.replaceChildren();
    if (!frame.audits.length) add(audits, 'p', 'No audit publication at this logical time. ' +
      'This does not say whether a channel exists or a later report is scheduled.', 'dim');
    frame.audits.forEach(event => {
      const card = auditCard(audits, event.payload.report);
      ref(card, event); json(card, event.payload);
    });
    const outcomes = el('inspect-outcomes'); outcomes.replaceChildren();
    add(outcomes, 'p', 'These events describe resolution and effects. They may not have been ' +
      'visible to every agent.', 'dim');
    const transition = frame.outcomes.find(event => event.event_type === 'WorldTransitioned');
    if (!transition) add(outcomes, 'p', 'No resolved world transition recorded here.', 'dim');
    if (transition && transition.payload.cooperative_votes !== undefined) {
      const p = transition.payload;
      chips(outcomes, [`${p.cooperative_votes}/${p.total_votes} cooperative votes`]);
      if (p.pair_results) network(outcomes, p.pair_results, Object.keys(run.policies));
      else if (p.moves) table(outcomes, ['Agent', 'Resolved move'], Object.entries(p.moves));
    }
    frame.outcomes.forEach(event => eventCard(outcomes, event, event.event_type));
    const seals = el('inspect-seals'); seals.replaceChildren();
    add(seals, 'p', 'State hashes identify recorded checkpoints; private checkpoint contents ' +
      'are not loaded into this page. Terminal metrics are post-run outcomes.', 'dim');
    if (!frame.checkpoints.length && !frame.terminal.length) {
      add(seals, 'p', 'No checkpoint or terminal seal at this logical time.', 'dim');
    }
    [...frame.checkpoints, ...frame.terminal].forEach(event => {
      const card = eventCard(seals, event, event.event_type);
      add(card, 'div', `Event hash: ${event.event_hash}`, 'inspect-meta');
      const hash = event.payload.state_hash || event.payload.final_state_hash;
      if (hash) add(card, 'div', `State hash: ${hash}`, 'inspect-meta');
      if (event.payload.reason) add(card, 'p', event.payload.reason, 'broken');
    });
  }
  function chooseRun() {
    const run = runs[Number(runSelect.value)];
    const previousAgent = agentSelect.value; agentSelect.replaceChildren();
    Object.keys(run.policies).forEach(agent => {
      const option = add(agentSelect, 'option', agent); option.value = agent;
    });
    if (Object.hasOwn(run.policies, previousAgent)) agentSelect.value = previousAgent;
    slider.max = String(run.frames.length - 1); slider.value = '0';
    const status = el('inspect-run-status'); status.replaceChildren();
    const replay = run.replay_identical === null ? 'Replay not requested' :
      run.replay_identical ? 'Replay identical' : 'Replay mismatch';
    chips(status, [`Verified sealed run · ${run.status}`, replay]);
    if (run.failure_reason) add(status, 'p', run.failure_reason, 'broken');
    if (run.parent_run) add(status, 'p', `Branch of ${run.parent_run}; continuation begins ` +
      `at round ${run.fork_round}. Policies below describe the continuation. ` +
      'Earlier events retain their original run IDs and inherited labels.', 'dim');
    add(status, 'div', `Terminal event hash: ${run.final_event_hash}`, 'inspect-meta');
    json(status, run.policies, run.parent_run ? 'Continuation policies' : 'Recorded policies');
    draw();
  }
  runs.forEach((run, i) => {
    const option = add(runSelect, 'option', `${i + 1}. ${run.study_id} / ${run.condition_id}` +
      ` · ${run.run_id} · replicate ${run.replicate} · ${run.final_event_hash.slice(0, 12)}`);
    option.value = String(i);
  });
  runSelect.addEventListener('change', chooseRun);
  agentSelect.addEventListener('change', draw); slider.addEventListener('input', draw);
  el('inspect-prev').addEventListener('click', () => { slider.stepDown(); draw(); });
  el('inspect-next').addEventListener('click', () => { slider.stepUp(); draw(); });
  el('run-inspector').hidden = false;
  chooseRun();
})();
"""
