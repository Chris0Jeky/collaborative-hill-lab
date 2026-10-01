"""CLI ``branch --override`` validation: malformed params exit 2, rationals parse.

Covers three previously broken inputs:
- ``a0=ec_contributor:share_evidence`` (segment without ``k=v`` silently
  became an empty string, flipping ``share_evidence`` falsy);
- ``a0=ec_contributor:bogus=1`` (unknown key silently ignored);
- ``a0=ptft:epsilon=1/10`` (``float()`` crashed on the rational string).
"""

from types import SimpleNamespace

from typer.testing import CliRunner

import collaborative_hill.engine.branching as branching_mod
import collaborative_hill.engine.replay as replay_mod
from collaborative_hill.cli import app
from collaborative_hill.experiments.scenario import ECWorld, NIPDWorld

runner = CliRunner()


def _ec_resolved():
    world = ECWorld(slots={"s1": ("p1a", "p1b")}, true_propositions={"s1": "p1a"})
    return SimpleNamespace(spec=SimpleNamespace(world=world))


def _nipd_resolved(mode="neighbourhood"):
    return SimpleNamespace(spec=SimpleNamespace(world=NIPDWorld(mode=mode)))


def _patch_parent(monkeypatch, resolved):
    monkeypatch.setattr(
        replay_mod,
        "load_run",
        lambda run_dir: (None, resolved, {"run_id": "parent-r000"}),
    )


def _patch_branch(monkeypatch, captured):
    def fake_branch_run(*, parent_dir, fork_seq, child_dir, child_run_id,
                        policy_overrides):
        captured.update(policy_overrides)
        result = SimpleNamespace(
            run_id=child_run_id, status="completed", event_count=0
        )
        manifest = SimpleNamespace(model_dump_json=lambda indent=2: "{}")
        return result, manifest

    monkeypatch.setattr(branching_mod, "branch_run", fake_branch_run)


def _branch(tmp_path, override):
    return runner.invoke(
        app,
        ["branch", str(tmp_path), "--at-event", "1",
         "--override", override, "--out", str(tmp_path / "child")],
    )


def test_param_segment_without_equals_is_usage_error(tmp_path, monkeypatch):
    _patch_parent(monkeypatch, _ec_resolved())
    result = _branch(tmp_path, "a0=ec_contributor:share_evidence")
    assert result.exit_code == 2


def test_unknown_param_key_is_usage_error(tmp_path, monkeypatch):
    _patch_parent(monkeypatch, _ec_resolved())
    result = _branch(tmp_path, "a0=ec_contributor:bogus=1")
    assert result.exit_code == 2


def test_rational_epsilon_parses(tmp_path, monkeypatch):
    _patch_parent(monkeypatch, _nipd_resolved("neighbourhood"))
    captured: dict = {}
    _patch_branch(monkeypatch, captured)
    result = _branch(tmp_path, "a0=ptft:epsilon=1/10")
    assert result.exit_code == 0, result.output
    assert abs(captured["a0"].epsilon - 0.1) < 1e-9


def test_plain_policy_override_still_works(tmp_path, monkeypatch):
    _patch_parent(monkeypatch, _nipd_resolved("neighbourhood"))
    captured: dict = {}
    _patch_branch(monkeypatch, captured)
    result = _branch(tmp_path, "a3=allc")
    assert result.exit_code == 0, result.output
    assert captured["a3"].policy_id == "allc[neighbourhood]@1"
