"""Metamorphic: a narrative skin is prose only — it cannot touch the game.

Two very different skins over one mechanism must agree on mechanism_hash and
evidence_corpus_hash while disagreeing on narrative_hash. Stronger: driving the
scripted scenario through run_episode under both compilations (same RunConfig,
no narrative-bearing start_meta) must produce byte-identical full event hash
chains — proof that the skin never leaks into the sealed ledger.
"""

import pytest

from collaborative_hill.experiments.scenario import compile_scenario

from ._helpers import default_ec_evidence, ec_spec, execute, plain_skin, rich_ec_skin

pytestmark = pytest.mark.metamorphic


def _compile_both():
    spec = ec_spec(default_ec_evidence(), scenario_id="skin-iso")
    plain = compile_scenario(spec, plain_skin())
    rich = compile_scenario(spec, rich_ec_skin())
    return plain, rich


def test_skin_swaps_narrative_hash_only():
    plain, rich = _compile_both()

    # The game is identical...
    assert plain.mechanism_hash == rich.mechanism_hash
    assert plain.evidence_corpus_hash == rich.evidence_corpus_hash
    # ...the prose is not...
    assert plain.narrative_hash != rich.narrative_hash
    # ...and the scenario hash folds the narrative in, so it differs too.
    assert plain.scenario_hash != rich.scenario_hash


def test_skin_does_not_leak_into_the_ledger(tmp_path):
    plain, rich = _compile_both()

    # Identical RunConfig; start_meta omitted so no narrative_hash enters the
    # hashed RunStarted payload. Scripted EC policy ids do not depend on the skin.
    common = dict(seed_root=("skin", 0), study_id="study", run_id="run")
    _, plain_events, _ = execute(plain, tmp_path / "plain", **common)
    _, rich_events, _ = execute(rich, tmp_path / "rich", **common)

    assert len(plain_events) == len(rich_events)
    assert len(plain_events) > 1
    plain_chain = [e.event_hash for e in plain_events]
    rich_chain = [e.event_hash for e in rich_events]
    assert plain_chain == rich_chain
    # The final sealed hash is the tamper-evident summary of the whole run.
    assert plain_events[-1].event_hash == rich_events[-1].event_hash


def test_skin_referencing_unknown_ids_is_rejected():
    from collaborative_hill.experiments.scenario import NarrativeSkin

    spec = ec_spec(default_ec_evidence(), scenario_id="skin-bad")

    with pytest.raises(ValueError, match="unknown agent"):
        compile_scenario(spec, NarrativeSkin(skin_id="x", agent_names={"ghost": "G"}))

    with pytest.raises(ValueError, match="unknown evidence"):
        compile_scenario(spec, NarrativeSkin(skin_id="x", evidence_content={"e404": "..."}))

    with pytest.raises(ValueError, match="unknown slot"):
        compile_scenario(spec, NarrativeSkin(skin_id="x", slot_titles={"s404": "..."}))

    with pytest.raises(ValueError, match="unknown proposition"):
        compile_scenario(spec, NarrativeSkin(skin_id="x", proposition_texts={"p404": "..."}))
