"""Exercise comparison filters in Chrome using the lab gate's real sealed fixtures."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from check_lab_browser import CAPTURE_ERRORS, snapshot

from collaborative_hill.reporting.comparison_view import write_comparison

CHECK_JS = r"""<script>
(() => {
  const result = document.createElement('p');
  result.id = 'browser-check-result'; result.dataset.status = 'failed';
  document.body.append(result);
  let assertions = 0;
  const check = (ok, message) => { if (!ok) throw new Error(message); assertions++; };
  const el = id => document.getElementById(id);
  const change = (node, value) => {
    node.value = String(value); node.dispatchEvent(new Event('change', {bubbles: true}));
  };
  try {
    const summary = JSON.parse(el('comparison-json').textContent);
    const round = el('compare-round'), agent = el('compare-agent');
    const rounds = [...document.querySelectorAll('.comparison-round')];
    const visibleRounds = () => rounds.filter(node => !node.hidden);
    check(rounds.length === 51, 'missing recorded rounds');
    check(round.options.length === 52 && agent.options.length === 4, 'missing filter options');
    check(summary.common_prefix_events === 131, 'unexpected branch prefix fixture');
    check(summary.first_action_difference.round === 10, 'unexpected first action difference');
    check(el('source-left').textContent.includes('pw-2tft-alld-r000'), 'left source missing');
    check(el('source-right').textContent.includes('browser-branch'), 'right source missing');
    check(el('validation').textContent.includes('replay verified for both runs'), 'replay missing');
    check(el('meta-policy_ids').textContent.includes('Differ'), 'changed policies not flagged');
    check(el('ancestry-right').textContent.includes('logical round 10'), 'fork boundary missing');
    check(visibleRounds().length === 1, 'initial round filter did not initialize');
    rounds.forEach(frame => {
      change(round, frame.dataset.round);
      check(visibleRounds().length === 1 && visibleRounds()[0] === frame, 'wrong round visible');
      ['a1', 'a2', 'a3'].forEach((id, index) => {
        change(agent, index);
        const visible = [...frame.querySelectorAll('.agent')].filter(node => !node.hidden);
        check(visible.length === 1 && visible[0].querySelector('h3').textContent === id,
          'wrong agent perspective visible');
        check(el('selection-status').textContent.includes(id), 'selection status not updated');
      });
    });
    change(round, 'all'); change(agent, 'all');
    check(visibleRounds().length === 51, 'all-rounds option hides frames');
    check(rounds.every(frame => [...frame.querySelectorAll('.agent')].every(node => !node.hidden)),
      'all-agents option hides a perspective');
    change(round, 9); change(agent, 2);
    check(el('round-9-agent-2-right-observations').textContent.includes('inherited prefix'),
      'inherited branch observation is unlabeled');
    check(!el('round-9-agent-2-left-observations').textContent.includes('inherited prefix'),
      'ordinary root observation was labeled inherited');
    check(el('round-9-agent-2-left-observations').textContent.includes('shared leading event hash'),
      'shared history missing from parent panel');
    change(round, 10);
    const left = el('round-10-agent-2-left-actions');
    const right = el('round-10-agent-2-right-actions');
    const leftAction = JSON.parse(left.querySelector('pre').textContent).proposal.action;
    const rightAction = JSON.parse(right.querySelector('pre').textContent).proposal.action;
    check(leftAction.type === 'pairwise_vote' &&
      Object.values(leftAction.moves).every(x => x === 'D'),
      'parent action is not the literal AllD control');
    check(rightAction.type === 'pairwise_vote' &&
      Object.values(rightAction.moves).every(x => x === 'C'),
      'child action is not the literal AllC continuation');
    check(!right.textContent.includes('inherited prefix'), 'new child action labeled inherited');
    change(round, 50);
    check(el('round-50-agent-2-left-observations').textContent.includes('No observation recorded'),
      'terminal frame carries an earlier observation');
    check(el('round-50-right-outcomes').textContent.includes('RunCompleted'), 'child seal missing');
    change(round, 10);
    check(document.documentElement.scrollWidth <= innerWidth + 1, 'comparison overflows viewport');
    check(window.browserCheckErrors.length === 0, window.browserCheckErrors.join('; '));
    result.dataset.status = 'passed'; result.dataset.assertions = String(assertions);
    result.textContent = `${assertions} comparison assertions passed at ${innerWidth}px`;
  } catch (error) { result.textContent = String(error.stack || error); }
})();
</script>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=REPO / "artifacts/browser-smoke/runs")
    parser.add_argument("--out", type=Path, default=REPO / "artifacts/comparison-browser")
    parser.add_argument("--browser", default=os.environ.get("CHROME_BIN")
                        or shutil.which("google-chrome") or shutil.which("chromium"))
    args = parser.parse_args()
    if not args.browser:
        parser.error("Chrome is required; provide --browser or set CHROME_BIN")
    parent = next((path.parent for path in args.fixtures.rglob("events.jsonl")
                   if path.parent.parent.name == "pw-2tft-alld"), None)
    if parent is None:
        parser.error("run the lab browser gate first to generate its sealed fixtures")
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    console = output / "comparison.html"
    write_comparison(parent, args.fixtures / "branch-demo", console, verify_replay=True)
    page = output / "browser-check.html"
    html = console.read_text(encoding="utf-8").replace("<head>", "<head>" + CAPTURE_ERRORS, 1)
    page.write_text(html.replace("</body>", CHECK_JS + "</body>", 1),
                    encoding="utf-8", newline="\n")
    views = [snapshot(args.browser, page, output, *view) for view in (
        ("desktop-comparison", 1440, 3200, "comparison"),
        ("mobile-comparison", 420, 4200, "comparison"),
    )]
    report = {"schema_version": 1, "snapshots": views}
    (output / "RESULTS.json").write_text(json.dumps(report, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
