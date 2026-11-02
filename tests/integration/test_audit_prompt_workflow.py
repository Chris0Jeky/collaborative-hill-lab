"""Sealed fake-only studies bind audit prompts, provenance and continuations."""

import hashlib
import json
import urllib.request
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from collaborative_hill.agents.llm import (
    FakeProvider,
    LLMPolicy,
    build_openai_compatible_policy,
)
from collaborative_hill.engine.branching import branch_run
from collaborative_hill.engine.events import EventType
from collaborative_hill.engine.replay import load_run, replay_run
from collaborative_hill.engine.store import FileCheckpointStore
from collaborative_hill.experiments.study import build_policies, run_study

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]
BASELINE = json.loads((ROOT / "tests/fixtures/llm_prompt_v1_baseline.json").read_text(
    encoding="utf-8"))
TEMPLATE_HASH = "ecca7bc5458a3b424cc3e130589b6be7cb60543b5b228a0c0ef8aabdbc688ed6"
LITERAL_REPORTS = [
    {"slot_id": "s1", "proposition_id": "p1a", "publish_round": 1, "verdict": "positive"},
    {"slot_id": "s1", "proposition_id": "p1b", "publish_round": 2, "verdict": "negative"},
]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(urllib.request.OpenerDirector, "open",
                        lambda *args, **kwargs: pytest.fail("network is forbidden in this suite"))


@pytest.fixture
def captured_prompts(monkeypatch):
    prompts = []
    original = FakeProvider.complete

    def capture(provider, prompt):
        prompts.append(prompt)
        return original(provider, prompt)

    monkeypatch.setattr(FakeProvider, "complete", capture)
    return prompts


def write_study(root, *, world="ec", renderer="ec-audit@1", audited=True):
    root.mkdir(parents=True)
    raw = deepcopy(next(case["scenario"] for case in BASELINE["chains"] if case["name"] == world))
    if world == "ec":
        raw["world"]["params"]["rounds"] = 3
    else:
        raw["world"]["rounds"] = 3
    for agent in raw["cognition"]["agents"]:
        params = agent["policy"]["params"]
        params["script"] = json.dumps([json.loads(params["script"])[0]] * 3)
        params["prompt_renderer"] = renderer
    if audited:
        raw["institution"]["audit"] = {
            "contract": {
                "contract_version": "ec-audit-observation@1", "audit_id": "prompt-workflow",
                "accuracy": "1", "accuracy_semantics": "symmetric-conditional-on-availability",
                "oracle_kind": "synthetic-trusted-oracle",
                "dependence": "independent-of-source-errors", "visibility": "public",
                "selection": "fixed-ex-ante-targets",
                "unavailable_semantics": "explicit-no-verdict",
                "schedule": [{key: value for key, value in row.items() if key != "verdict"}
                             for row in LITERAL_REPORTS],
            },
            "generation": {
                "generator_version": "ec-audit-generator@1", "unavailable_probability": "0",
                "draw_dependence": "independent-per-target",
                "unavailable_dependence": "independent-of-truth-source-errors-and-correctness",
            },
        }
    files = {
        "scenario.json": raw,
        "skin.json": {"skin_id": "plain"},
        "study.json": {
            "study_id": "audit-prompt-workflow", "seed": 108, "replicates": 1,
            "seed_protocol": "paired-policy-v2", "checkpoint_every": 1,
            "conditions": [{"condition_id": "cell", "scenario": "scenario.json",
                            "skin": "skin.json", "scenario_block": "prompt"}],
        },
    }
    for name, value in files.items():
        (root / name).write_text(json.dumps(value), encoding="utf-8", newline="\n")
    return root


def run_fixture(tmp_path, **kwargs):
    study_dir = write_study(tmp_path / "study", **kwargs)
    result, = run_study(study_dir, tmp_path / "runs")
    assert result.status == "completed"
    manifest, = (tmp_path / "runs").rglob("manifest.json")
    return manifest.parent


def rendered_data(prompt):
    section = prompt.split("## Public audit channel\n", 1)[1]
    return json.loads(section.partition("\n<<<AUDIT_DATA\n")[2].rpartition("\nAUDIT_DATA>>>")[0])


def transcript(run):
    return [json.loads(line) for line in (run / "llm_transcript.jsonl").read_text(
        encoding="utf-8").splitlines()]


def assert_provenance(manifest, prompts, rows, *, rounds, scope):
    assert manifest["prompt_template_hashes"] == dict.fromkeys(("a1", "a2", "a3"), TEMPLATE_HASH)
    assert all(",renderer=ec-audit@1," in item and item.endswith("]@2")
               for item in manifest["policies"].values())
    assert manifest["provider_metadata"] == manifest["sampling"] == {}
    assert manifest["input_tokens"] is manifest["output_tokens"] is manifest["cost_usd"] is None
    assert manifest["provider_usage_scope"] == scope
    assert {item["completion_calls"] for item in manifest["provider_usage"].values()} == {rounds}
    assert {item["request_attempts"] for item in manifest["provider_usage"].values()} == {rounds}
    assert Counter(row["prompt_sha256"] for row in rows) == Counter(
        hashlib.sha256(prompt.encode()).hexdigest() for prompt in prompts)
    assert all(row["input_tokens"] is None and row["output_tokens"] is None for row in rows)


def test_sealed_fake_study_displays_only_released_reports_and_replays_offline(
    tmp_path, captured_prompts, monkeypatch,
):
    run = run_fixture(tmp_path)
    events, _, manifest = load_run(run)
    observations = [event.payload["observation"] for event in events
                    if event.event_type == EventType.OBSERVATION_ISSUED]
    assert len(captured_prompts) == len(observations) == 9
    for prompt, obs in zip(captured_prompts, observations, strict=True):
        data = rendered_data(prompt)
        assert data["status"] == "present"
        assert data["envelope"]["audit_id"] == "prompt-workflow"
        assert data["envelope"]["reports"] == [
            row for row in LITERAL_REPORTS if row["publish_round"] <= obs["round"]]
        assert data["envelope"] == obs["audit"]
    assert_provenance(manifest, captured_prompts, transcript(run), rounds=3, scope="episode")
    before = {path.relative_to(run): path.read_bytes() for path in run.rglob("*") if path.is_file()}
    monkeypatch.setattr(FakeProvider, "complete",
                        lambda *args: pytest.fail("replay called provider"))
    assert replay_run(run).chains_match
    assert before == {path.relative_to(run): path.read_bytes()
                      for path in run.rglob("*") if path.is_file()}


def test_fresh_same_adapter_continuation_keeps_identity_prefix_and_offline_replay(
    tmp_path, captured_prompts, monkeypatch,
):
    parent = run_fixture(tmp_path)
    parent_events, resolved, parent_manifest = load_run(parent)
    checkpoints = FileCheckpointStore(parent / "checkpoints")
    fork = next(seq for seq in checkpoints.list_seqs()
                if checkpoints.load(seq)["logical_time"] == 1)
    assert checkpoints.load(fork)["state"]["audit_reports"] == []
    replacements = build_policies(resolved)
    captured_prompts.clear()
    child = tmp_path / "child"
    result, _ = branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
                           child_run_id="prompt-child", policy_overrides=replacements)
    assert result.status == "completed"
    events, _, manifest = load_run(child)
    assert len(captured_prompts) == 6
    assert manifest["prompt_template_hashes"] == parent_manifest["prompt_template_hashes"]
    assert (child / "events.jsonl").read_bytes().splitlines(keepends=True)[:fork + 1] == (
        (parent / "events.jsonl").read_bytes().splitlines(keepends=True)[:fork + 1])
    assert [event.payload["report"] for event in events
            if event.event_type == EventType.AUDIT_PUBLISHED] == LITERAL_REPORTS
    assert events[fork].event_hash == parent_events[fork].event_hash
    assert_provenance(manifest, captured_prompts, transcript(child), rounds=2, scope="continuation")
    parent.rename(tmp_path / "moved-parent")
    monkeypatch.setattr(FakeProvider, "complete",
                        lambda *args: pytest.fail("replay called provider"))
    assert replay_run(child).chains_match


@pytest.mark.parametrize("kind", ["fake", "compatible"])
def test_non_ec_audit_override_creates_no_branch_output(kind, tmp_path):
    parent = run_fixture(tmp_path, world="nipd", renderer="legacy@1", audited=False)
    _, resolved, _ = load_run(parent)
    checkpoints = FileCheckpointStore(parent / "checkpoints")
    fork = next(seq for seq in checkpoints.list_seqs()
                if checkpoints.load(seq)["logical_time"] == 1)
    if kind == "fake":
        override = LLMPolicy("a1", FakeProvider([]), resolved.skin, prompt_renderer="ec-audit@1")
    else:
        override = build_openai_compatible_policy("a1", resolved.skin, {
            "endpoint": "https://provider.invalid/chat", "model_id": "fixture-model",
            "max_tokens": 8, "prompt_renderer": "ec-audit@1",
        })
    child = tmp_path / "bad-child"
    with pytest.raises(ValueError, match="Evidence Commons"):
        branch_run(parent_dir=parent, fork_seq=fork, child_dir=child,
                   child_run_id="bad-child", policy_overrides={"a1": override},
                   allow_provider_requests=True)
    assert not child.exists()
    assert override.call_count == 0
    assert override.transcript == []


@pytest.mark.parametrize("renderer", [None, True, "future@1"])
def test_invalid_renderer_study_creates_no_output(renderer, tmp_path, captured_prompts):
    directory = write_study(tmp_path / "study", renderer=renderer)
    output = tmp_path / "runs"
    with pytest.raises(ValueError):
        run_study(directory, output)
    assert not output.exists()
    assert captured_prompts == []
