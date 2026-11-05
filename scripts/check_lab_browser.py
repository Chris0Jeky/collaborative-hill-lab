"""Exercise the offline inspector in real Chrome and retain reviewable screenshots.

Chrome is an optional developer/CI tool, not a lab runtime dependency. The check
uses its documented headless CLI on a local HTML file, with no browser server,
provider calls, sandbox bypasses or changes to original experiment evidence.
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from collaborative_hill.experiments.study import run_study
from collaborative_hill.reporting.lab import write_console

CAPTURE_ERRORS = """<script>
window.browserCheckErrors = [];
window.addEventListener('error', event => window.browserCheckErrors.push(event.message));
window.addEventListener('unhandledrejection', event =>
  window.browserCheckErrors.push(String(event.reason)));
</script>"""

CHECK_JS = r"""<script>
(() => {
  const result = document.createElement('p');
  result.id = 'browser-check-result';
  result.dataset.status = 'failed';
  document.body.append(result);
  let assertions = 0;
  const check = (ok, message) => {
    if (!ok) throw new Error(message);
    assertions++;
  };
  const el = id => document.getElementById(id);
  const change = (node, value, event = 'change') => {
    node.value = String(value);
    node.dispatchEvent(new Event(event, {bubbles: true}));
  };
  try {
    const runs = JSON.parse(el('inspection-data').textContent);
    const select = el('inspect-run'), agent = el('inspect-agent'), slider = el('inspect-round');
    check(!el('run-inspector').hidden, 'inspector did not initialize');
    check(runs.length === 5 && select.options.length === runs.length, 'missing run options');
    runs.forEach((run, index) => {
      change(select, index);
      check(agent.options.length === Object.keys(run.policies).length, 'missing agent options');
      check(el('inspect-run-status').textContent.includes(run.final_event_hash), 'wrong run seal');
      check(el('inspect-run-status').textContent.includes('Replay identical'), 'replay not shown');
      check(slider.value === '0' && el('inspect-prev').disabled, 'run change did not reset round');
      el('inspect-next').click();
      check(slider.value === '1', 'next button did not advance');
      el('inspect-prev').click();
      check(slider.value === '0', 'previous button did not return');
      run.frames.forEach((frame, frameIndex) => {
        change(slider, frameIndex, 'input');
        check(el('inspect-round-label').textContent.includes(`round ${frame.round} (`),
          'range input did not select its logical round');
        Object.keys(run.policies).forEach(id => {
          change(agent, id);
          const observation = frame.observations.find(event => event.payload.agent_id === id);
          if (observation) {
            check(el('inspect-observation').textContent.includes(
              `Event ${observation.seq} · ${observation.run_id}`),
              'agent selector displayed the wrong observation');
          } else {
            check(el('inspect-observation').textContent.includes('No observation recorded'),
              'missing observation was carried forward');
          }
        });
      });
      check(el('inspect-next').disabled, 'last frame allows next');
      check(el('inspect-seals').textContent.includes('RunCompleted'), 'terminal seal not shown');
    });
    const choose = condition => {
      const index = runs.findIndex(run => run.condition_id === condition);
      check(index >= 0, `fixture missing: ${condition}`);
      change(select, index);
      change(agent, 'a1');
      return runs[index];
    };
    ['positive', 'negative', 'unavailable'].forEach(verdict => {
      const run = choose(`behavior-tp-rq-${verdict}-3`);
      change(slider, run.frames.findIndex(frame => frame.round === 2), 'input');
      check(el('inspect-observation').textContent.includes('no reports published yet'),
        'future audit leaked into an earlier observation');
      check(el('inspect-audits').textContent.includes('No audit publication'),
        'future audit publication displayed early');
      change(slider, run.frames.findIndex(frame => frame.round === 3), 'input');
      check(el('inspect-audits').textContent.includes(`Published round 3 · ${verdict}`),
        'audit verdict or publication time is wrong');
      check(el('inspect-observation').textContent.includes(`Published round 3 · ${verdict}`),
        'published audit missing from the current observation');
      check(el('inspect-observation').textContent.includes('Own budget'), 'budget table missing');
      check(el('inspect-observation').textContent.includes('Claims visible before actions'),
        'claim view missing');
    });
    choose('ring-d-a1-targeted');
    change(slider, 1, 'input');
    const svg = el('inspect-outcomes').querySelector('svg');
    check(svg && svg.querySelectorAll('circle').length === 5, 'graph omitted agent nodes');
    check(svg.querySelectorAll('line').length === 5, 'ring graph has the wrong edge count');
    check(el('inspect-outcomes').textContent.includes('Forward move'),
      'graph has no exact move table');
    if (location.hash === '#audit') {
      choose('behavior-tp-rq-negative-3');
      change(slider, 3, 'input');
    }
    check(document.documentElement.scrollWidth <= innerWidth + 1, 'page overflows viewport');
    check(window.browserCheckErrors.length === 0, window.browserCheckErrors.join('; '));
    result.dataset.status = 'passed';
    result.dataset.assertions = String(assertions);
    result.textContent = `${assertions} browser assertions passed at ${innerWidth}px`;
    el('run-inspector').scrollIntoView();
  } catch (error) {
    result.textContent = String(error.stack || error);
    result.scrollIntoView();
  }
})();
</script>"""


class CheckResult(HTMLParser):
    """Read the actual result element, never a success string in script source."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "p" and values.get("id") == "browser-check-result":
            self.results.append(values)


def fixtures(root: Path) -> None:
    for directory, condition in (
        ("studies/000-legacy-reproduction", "pw-2tft-alld"),
        ("experiments/graph-topology", "ring-d-a1-targeted"),
    ):
        results = run_study(REPO / directory, root, only_condition=condition,
                            replicates_override=1)
        if len(results) != 1 or results[0].status != "completed":
            raise RuntimeError(f"browser fixture did not complete: {condition}")
    spec = importlib.util.spec_from_file_location("lab_demo", REPO / "scripts/lab.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audit demo fixtures")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    demo.audit_samples(root)


def snapshot(browser: str, page: Path, output: Path, name: str,
             width: int, height: int, scene: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="chl-browser-") as profile:
        completed = subprocess.run([
            browser, "--headless", "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", f"--user-data-dir={profile}",
            "--dump-dom", "--virtual-time-budget=1000", f"--window-size={width},{height}",
            f"--screenshot={output / (name + '.png')}", page.as_uri() + "#" + scene,
        ], capture_output=True, text=True, encoding="utf-8", timeout=60, check=False)
    (output / f"{name}.dom.html").write_text(completed.stdout, encoding="utf-8", newline="\n")
    (output / f"{name}.stderr.txt").write_text(completed.stderr, encoding="utf-8", newline="\n")
    parsed = CheckResult()
    parsed.feed(completed.stdout)
    if (completed.returncode or len(parsed.results) != 1
            or parsed.results[0].get("data-status") != "passed"):
        raise RuntimeError(f"{name} browser check failed; inspect {output / (name + '.dom.html')}")
    screenshot = output / f"{name}.png"
    if not screenshot.is_file() or screenshot.stat().st_size < 1000:
        raise RuntimeError(f"{name} browser did not capture a screenshot")
    return {"name": name, "viewport": [width, height], "scene": scene,
            "assertions": int(parsed.results[0].get("data-assertions") or 0)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", default=os.environ.get("CHROME_BIN")
                        or shutil.which("google-chrome") or shutil.which("chromium"))
    parser.add_argument("--out", type=Path, default=REPO / "artifacts/browser-smoke",
                        help="fresh output directory; existing files are never replaced")
    args = parser.parse_args()
    if not args.browser:
        parser.error("Chrome is required; provide --browser or set CHROME_BIN")
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixtures(output / "runs")
    console = output / "console.html"
    _, traces = write_console(output / "runs", console, verify_replay=True)
    if len(traces) != 5 or any(trace.get("replay_identical") is not True for trace in traces):
        raise RuntimeError("browser fixtures must all be sealed and replay identical")
    page = output / "browser-check.html"
    html = console.read_text(encoding="utf-8").replace("<head>", "<head>" + CAPTURE_ERRORS, 1)
    page.write_text(html.replace("</body>", CHECK_JS + "</body>", 1),
                    encoding="utf-8", newline="\n")
    version = subprocess.run([args.browser, "--version"], check=True, capture_output=True,
                             text=True, encoding="utf-8", timeout=15).stdout.strip()
    snapshots = [snapshot(args.browser, page, output, *view) for view in (
        ("desktop-graph", 1440, 1600, "graph"),
        ("mobile-audit", 420, 1800, "audit"),
    )]
    report = {"schema_version": 1, "browser": version, "runs": len(traces),
              "snapshots": snapshots}
    (output / "RESULTS.json").write_text(json.dumps(report, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
