"""Visual comparisons preserve the existing descriptive contract and source bytes."""

import json
import os
from collections import defaultdict
from html.parser import HTMLParser

import pytest
from typer.testing import CliRunner

from collaborative_hill.cli import app
from collaborative_hill.engine.store import FileCheckpointStore, RunPaths
from collaborative_hill.experiments import study as study_module
from collaborative_hill.reporting import comparison_view

from ._helpers import (
    default_ec_evidence,
    ec_spec,
    find_run_dirs,
    nipd_spec,
    plain_skin,
    write_study,
)

pytestmark = pytest.mark.metamorphic


@pytest.mark.parametrize("fork", [10, "ten"])
def test_root_fork_metadata_is_rejected_before_html_output(tmp_path, parent, fork):
    right = run_fixture(tmp_path / "right")
    path = parent / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert not manifest.get("parent_run")
    manifest["fork_seq"] = fork
    path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    before = snapshot(parent)
    # Default JSON retains its historical contract; using this unused field to
    # render ancestry requires an additional presentation validation boundary.
    plain = compare(parent, right)
    assert plain.exit_code == 0
    assert json.loads(plain.stdout)["left"]["fork_seq"] == fork
    out = tmp_path / "view" / "comparison.html"
    rendered = compare(parent, right, "--out", out)
    assert rendered.exit_code == 2
    assert "fork_seq" in rendered.output
    assert not out.parent.exists()
    assert snapshot(parent) == before


class Page(HTMLParser):
    """Read rendered text by semantic element ID, with normal HTML entity decoding."""

    def __init__(self, text):
        super().__init__()
        self.stack = []
        self.texts = defaultdict(list)
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag not in {"meta", "input", "br", "hr", "link"}:
            self.stack.append(attrs.get("id"))

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        for element_id in self.stack:
            if element_id is not None:
                self.texts[element_id].append(data)

    def text(self, element_id):
        return "".join(self.texts[element_id])


def snapshot(directory):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


def compare(left, right, *options):
    return CliRunner().invoke(app, ["compare", str(left), str(right), *map(str, options)])


def run_fixture(root, *, spec=None, skin=None, seed=17):
    study = root / "study"
    spec = spec or nipd_spec((("a1", "allc"), ("a2", "allc"), ("a3", "allc")), rounds=6)
    write_study(study, study_id="literal-control", seed=seed, checkpoint_every=2,
                conditions=[("cell", spec, skin or plain_skin())])
    study_module.run_study(study, root / "runs")
    run, = find_run_dirs(root / "runs")
    return run


@pytest.fixture
def parent(tmp_path):
    return run_fixture(tmp_path / "parent")


def branch(parent, out, *, override=False):
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    args = ["branch", str(parent), "--at-event", str(fork), "--out", str(out)]
    args.extend(["--override", "a3=alld" if override else "a3=allc"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    return fork


def test_matched_control_keeps_json_and_distinguishes_sources_with_duplicate_ids(tmp_path, parent):
    right = run_fixture(tmp_path / "repeat")
    original = compare(parent, right, "--verify-replay")
    before = snapshot(parent), snapshot(right)
    out = tmp_path / "reports" / "matched.html"
    result = compare(parent, right, "--verify-replay", "--out", out)
    assert result.exit_code == 0, result.output
    assert result.stdout == original.stdout
    data = json.loads(result.stdout)
    assert data["left"]["run_id"] == data["right"]["run_id"]
    assert data["utility_delta"] == {"a1": "0", "a2": "0", "a3": "0"}
    assert data["left"]["utilities_exact"] == {"a1": "36", "a2": "36", "a3": "36"}
    assert data["same_kernel_streams"] is True
    page = Page(out.read_text(encoding="utf-8"))
    assert str(parent.resolve()) in page.text("source-left")
    assert str(right.resolve()) in page.text("source-right")
    assert data["left"]["final_event_hash"] in page.text("source-left")
    assert "match" in page.text("meta-policy_ids").lower()
    assert "do not prove independent" in page.text("interpretation")
    assert "not statistical evidence" in page.text("interpretation")
    assert "Recorded-action replay verified" in page.text("validation")
    assert (snapshot(parent), snapshot(right)) == before
    again = tmp_path / "reports" / "repeat.html"
    assert compare(parent, right, "--verify-replay", "--out", again).exit_code == 0
    assert again.read_bytes() == out.read_bytes()


def test_branch_exact_deltas_and_observations_stay_aligned(tmp_path, parent):
    child = tmp_path / "child"
    fork = branch(parent, child, override=True)
    before = snapshot(parent), snapshot(child)
    out = tmp_path / "branch.html"
    result = compare(parent, child, "--out", out, "--verify-replay")
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["common_prefix_events"] == fork + 1
    assert data["utility_delta"] == {"a1": "-12", "a2": "-12", "a3": "16"}
    assert data["right"]["utilities_exact"] == {"a1": "24", "a2": "24", "a3": "52"}
    page = Page(out.read_text(encoding="utf-8"))
    assert "continuation begins at logical round 2" in page.text("ancestry-right")
    assert "inherited prefix" in page.text("round-0-agent-2-right-observations")
    assert '"moves_against_me": null' in page.text("round-0-agent-2-right-observations")
    assert '"a1": "C"' in page.text("round-2-agent-2-left-actions")
    assert '"a1": "D"' in page.text("round-2-agent-2-right-actions")
    assert "inherited prefix" not in page.text("round-2-agent-2-right-actions")
    assert "No observation recorded" in page.text("round-6-agent-2-right-observations")
    assert "RunCompleted" in page.text("round-6-right-outcomes")
    assert "differ" in page.text("meta-policy_ids").lower()
    assert (snapshot(parent), snapshot(child)) == before


def test_sibling_branches_with_duplicate_default_ids_remain_two_sources(tmp_path, parent):
    left, right = tmp_path / "left-child", tmp_path / "right-child"
    fork = branch(parent, left)
    branch(parent, right, override=True)
    out = tmp_path / "siblings.html"
    result = compare(left, right, "--out", out)
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["left"]["run_id"] == data["right"]["run_id"]
    assert data["left"]["final_event_hash"] != data["right"]["final_event_hash"]
    assert data["common_prefix_events"] >= fork + 1
    page = Page(out.read_text(encoding="utf-8"))
    assert str(left.resolve()) in page.text("source-left")
    assert str(right.resolve()) in page.text("source-right")
    assert '"a1": "C"' in page.text("round-2-agent-2-left-actions")
    assert '"a1": "D"' in page.text("round-2-agent-2-right-actions")


def test_scenario_narrative_policy_and_seed_confounds_are_visible(tmp_path, parent):
    spec = nipd_spec((("a1", "allc"), ("a2", "allc"), ("a3", "alld")), rounds=6,
                     scenario_id="changed")
    right = run_fixture(tmp_path / "changed", spec=spec, skin=plain_skin("new-skin"), seed=31)
    out = tmp_path / "confounds.html"
    result = compare(parent, right, "--out", out)
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["utility_delta"] == {"a1": "-18", "a2": "-18", "a3": "24"}
    page = Page(out.read_text(encoding="utf-8"))
    for key in ("scenario_hash", "narrative_hash", "policy_ids", "seed_root"):
        assert "differ" in page.text(f"meta-{key}").lower()
    assert "match" in page.text("meta-mechanism_hash").lower()
    assert "match" in page.text("meta-evidence_corpus_hash").lower()
    assert "Confounds" in page.text("compatibility")
    assert "do not guarantee" in page.text("kernel-streams")


@pytest.mark.parametrize("kind", ["mechanism", "evidence"])
def test_incompatible_pairs_fail_without_creating_export(tmp_path, kind):
    if kind == "mechanism":
        left = run_fixture(tmp_path / "left")
        right = run_fixture(tmp_path / "right", spec=nipd_spec(
            (("a1", "allc"), ("a2", "allc"), ("a3", "allc")), rounds=3))
    else:
        evidence = default_ec_evidence()
        left = run_fixture(tmp_path / "left", spec=ec_spec(evidence, rounds=3))
        changed = (evidence[0].model_copy(update={"source_id": "changed-source"}), *evidence[1:])
        right = run_fixture(tmp_path / "right", spec=ec_spec(changed, rounds=3))
    out = tmp_path / "must-not-create" / "comparison.html"
    before = snapshot(tmp_path)
    result = compare(left, right, "--out", out)
    assert result.exit_code == 2
    assert "same mechanism hash" in result.stderr
    assert not out.parent.exists()
    assert snapshot(tmp_path) == before


def test_failed_run_has_missing_frames_and_no_fabricated_delta(tmp_path, parent, monkeypatch):
    original = study_module.build_policies

    def fail_first_policy(resolved, *, allow_provider_requests=False, overrides=None):
        policies = original(resolved, allow_provider_requests=allow_provider_requests,
                            overrides=overrides)

        def fail(*args):
            raise RuntimeError("fixture stopped before an action")

        policies["a1"].propose = fail
        return policies

    monkeypatch.setattr(study_module, "build_policies", fail_first_policy)
    right = run_fixture(tmp_path / "failed")
    out = tmp_path / "failed.html"
    result = compare(parent, right, "--out", out)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["utility_delta"] is None
    page = Page(out.read_text(encoding="utf-8"))
    assert "unavailable" in page.text("utilities").lower()
    assert "No action recorded" in page.text("round-0-agent-0-right-actions")
    assert "No frame recorded" in page.text("round-1-agent-0-right-observations")
    assert "No frame recorded" in page.text("round-1-right-outcomes")
    assert "RunFailed" in page.text("round-0-right-outcomes")


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("relative", ["events.jsonl", "manifest.json", "new.html",
                                      "nested/new.html"])
def test_export_rejects_both_source_directories(tmp_path, parent, side, relative):
    child = tmp_path / "child"
    branch(parent, child)
    source = parent if side == "left" else child
    before = snapshot(parent), snapshot(child)
    result = compare(parent, child, "--out", source / relative)
    assert result.exit_code == 2
    assert "outside both" in result.stderr
    assert (snapshot(parent), snapshot(child)) == before


def test_export_refuses_existing_file_and_both_symlink_aliases(tmp_path, parent):
    child = tmp_path / "child"
    branch(parent, child)
    out = tmp_path / "existing.html"
    out.write_text("preserve me", encoding="utf-8", newline="\n")
    result = compare(parent, child, "--out", out)
    assert result.exit_code == 2
    assert "already exists" in result.stderr
    assert out.read_text(encoding="utf-8") == "preserve me"
    before = snapshot(parent), snapshot(child)
    for label, source in (("left", parent), ("right", child)):
        alias = tmp_path / f"{label}-alias"
        try:
            alias.symlink_to(source, target_is_directory=True)
        except OSError:
            pytest.skip("directory symlinks unavailable")
        result = compare(parent, child, "--out", alias / "new.html")
        assert result.exit_code == 2
        assert "outside both" in result.stderr
    assert (snapshot(parent), snapshot(child)) == before


def test_hostile_identity_and_payload_strings_are_inert(tmp_path):
    hostile = '</script><script>window.injected=true</script><img src=x onerror="boom">&\u2028'
    parent = run_fixture(tmp_path / "parent", spec=nipd_spec(
        (("a1", "allc"), (hostile, "allc"), ("a3", "allc")), rounds=6))
    child = tmp_path / "child"
    fork = FileCheckpointStore(RunPaths(parent).checkpoints).list_seqs()[0]
    result = CliRunner().invoke(app, ["branch", str(parent), "--at-event", str(fork),
                                      "--out", str(child), "--run-id", hostile,
                                      "--override", "a3=allc"])
    assert result.exit_code == 0, result.output
    before = snapshot(parent), snapshot(child)
    out = tmp_path / "hostile.html"
    result = compare(parent, child, "--out", out)
    assert result.exit_code == 0, result.output
    page = Page(out.read_text(encoding="utf-8"))
    assert hostile in page.text("source-right")
    assert hostile in page.text("round-2-agent-0-right-observations")
    assert hostile in json.loads(page.text("comparison-json"))["left"]["policy_ids"]
    assert not any(tag == "img" for tag, _ in page.tags)
    assert len([tag for tag, _ in page.tags if tag == "script"]) == 1
    assert not any(name.startswith("on") for _, attrs in page.tags for name in attrs)
    assert (snapshot(parent), snapshot(child)) == before


def test_export_exclusively_creates_even_if_output_appears_at_open(tmp_path, parent, monkeypatch):
    out = tmp_path / "arriving.html"
    original = comparison_view.render_comparison

    def render_with_concurrent_writer(*args, **kwargs):
        page = original(*args, **kwargs)
        out.write_text("concurrent writer must survive", encoding="utf-8", newline="\n")
        return page

    monkeypatch.setattr(comparison_view, "render_comparison", render_with_concurrent_writer)
    before = snapshot(parent)
    result = compare(parent, parent, "--out", out)
    assert result.exit_code == 2
    assert not result.stdout
    assert out.read_text(encoding="utf-8") == "concurrent writer must survive"
    assert snapshot(parent) == before


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("ancestor", [False, True])
def test_export_parent_swap_keeps_report_outside_both_sources(
        tmp_path, parent, monkeypatch, side, ancestor):
    child = tmp_path / "child"
    branch(parent, child)
    source = parent if side == "left" else child
    before = snapshot(parent), snapshot(child)
    reports = tmp_path / "reports"
    (reports / "nested").mkdir(parents=True)
    out = reports / "nested" / "comparison.html"
    swapping = reports if ancestor else out.parent
    displaced = tmp_path / "displaced"
    original = comparison_view.render_comparison
    attempted = []

    def render_with_parent_swap(*args, **kwargs):
        page = original(*args, **kwargs)
        attempted.append(True)
        if os.name == "nt":
            with pytest.raises(PermissionError):
                swapping.rename(displaced)
        else:
            swapping.rename(displaced)
            swapping.symlink_to(source, target_is_directory=True)
        return page

    monkeypatch.setattr(comparison_view, "render_comparison", render_with_parent_swap)
    result = compare(parent, child, "--out", out)
    assert result.exit_code == 0, result.output
    assert attempted == [True]
    assert (snapshot(parent), snapshot(child)) == before
    actual = out if os.name == "nt" else displaced / (
        "nested/comparison.html" if ancestor else "comparison.html")
    assert "<!doctype html>" in actual.read_text(encoding="utf-8")
