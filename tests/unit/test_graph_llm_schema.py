"""Graph N-IPD must request the existing typed vote schema, not EC actions."""

import pytest

from collaborative_hill.agents.llm.rendering import action_schema_for


@pytest.mark.parametrize("mode,required", [("pairwise", "pairwise_vote"),
                                         ("neighbourhood", '"type": "cooperate"')])
def test_graph_nipd_has_the_correct_action_schema(mode, required):
    schema = action_schema_for({"mechanism": "nipd_graph", "mode": mode})
    assert required in schema
    assert "inspect_evidence" not in schema
    assert schema == action_schema_for({"mechanism": "nipd", "mode": mode})
