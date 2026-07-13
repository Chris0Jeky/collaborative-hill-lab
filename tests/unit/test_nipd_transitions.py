"""NIPD state transitions: round counter, cumulative fraction scores, last_moves
shape per mode, terminal boundary."""

from _fixtures import AGENTS, neighbourhood_actions, nipd, step, uniform_pairwise

from collaborative_hill.domain.actions import PairwiseVoteAction


def test_round_increments_each_resolve():
    mech = nipd("neighbourhood", rounds=5)
    state = mech.initial_state()
    assert state["round"] == 0
    for expected_next in (1, 2, 3):
        state, _ = step(mech, state, neighbourhood_actions(dict.fromkeys(AGENTS, "C")))
        assert state["round"] == expected_next


def test_cumulative_scores_accumulate_exactly_neighbourhood_all_c():
    mech = nipd("neighbourhood", rounds=5)
    state = mech.initial_state()
    assert state["scores"] == {"a1": "0", "a2": "0", "a3": "0"}
    running = ["3", "6", "9"]  # +3 each round (U_C(2)=3)
    for expected in running:
        state, _ = step(mech, state, neighbourhood_actions(dict.fromkeys(AGENTS, "C")))
        assert state["scores"] == dict.fromkeys(AGENTS, expected)


def test_cumulative_scores_exact_fractions_two_c_one_d():
    mech = nipd("neighbourhood", rounds=5)
    state = mech.initial_state()
    letters = {"a1": "C", "a2": "C", "a3": "D"}
    # cooperators +3/2 per round, defector +5 per round
    coop_running = ["3/2", "3", "9/2"]
    def_running = ["5", "10", "15"]
    for i in range(3):
        state, _ = step(mech, state, neighbourhood_actions(letters))
        assert state["scores"]["a1"] == coop_running[i]
        assert state["scores"]["a2"] == coop_running[i]
        assert state["scores"]["a3"] == def_running[i]


def test_cumulative_scores_accumulate_pairwise_all_c():
    mech = nipd("pairwise", rounds=5)
    state = mech.initial_state()
    for expected in ("6", "12", "18"):
        state, _ = step(mech, state, uniform_pairwise("C"))
        assert state["scores"] == dict.fromkeys(AGENTS, expected)


def test_last_moves_shape_neighbourhood():
    mech = nipd("neighbourhood", rounds=5)
    state = mech.initial_state()
    assert state["last_moves"] is None
    letters = {"a1": "C", "a2": "D", "a3": "C"}
    state, _ = step(mech, state, neighbourhood_actions(letters))
    # neighbourhood: flat map agent -> single move
    assert state["last_moves"] == {"a1": "C", "a2": "D", "a3": "C"}


def test_last_moves_shape_pairwise():
    mech = nipd("pairwise", rounds=5)
    state = mech.initial_state()
    assert state["last_moves"] is None
    actions = {
        "a1": _pv({"a2": "C", "a3": "D"}),
        "a2": _pv({"a1": "D", "a3": "C"}),
        "a3": _pv({"a1": "C", "a2": "C"}),
    }
    state, _ = step(mech, state, actions)
    # pairwise: nested agent -> opponent -> move (directed)
    assert state["last_moves"] == {
        "a1": {"a2": "C", "a3": "D"},
        "a2": {"a1": "D", "a3": "C"},
        "a3": {"a1": "C", "a2": "C"},
    }


def _pv(moves):
    return PairwiseVoteAction(moves=moves)


def test_is_terminal_at_round_boundary():
    mech = nipd("neighbourhood", rounds=5)
    state = mech.initial_state()
    for r in range(5):
        assert mech.is_terminal({**state, "round": r}) is False
    assert mech.is_terminal({**state, "round": 5}) is True
    assert mech.is_terminal({**state, "round": 6}) is True


def test_full_episode_reaches_terminal_after_rounds_resolves():
    mech = nipd("neighbourhood", rounds=3)
    state = mech.initial_state()
    n = 0
    while not mech.is_terminal(state):
        state, _ = step(mech, state, neighbourhood_actions(dict.fromkeys(AGENTS, "C")))
        n += 1
    assert n == 3
    assert state["round"] == 3
