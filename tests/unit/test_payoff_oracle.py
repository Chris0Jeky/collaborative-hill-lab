"""Oracle: every N=3 payoff profile against hand-derived literal tables.

Ground truth (paper prisoners.tex + independent re-derivation), NOT read from
the code under test. N=3, T=5, R=3, P=1, S=0.
"""

from fractions import Fraction

import pytest
from _fixtures import neighbourhood_actions, nipd, step

from collaborative_hill.domain.actions import PairwiseVoteAction
from collaborative_hill.domain.world.nipd import (
    NIPDParams,
    neighbourhood_payoff,
    pairwise_game,
)

PARAMS = NIPDParams()  # T=5, R=3, P=1, S=0

# -- pairwise: sum of two 2-player games; scores are exact ints -----------------

# Literal oracle: each agent's per-round total across its two games.
PAIRWISE_ORACLE = {
    "all_C": {"a1": "6", "a2": "6", "a3": "6"},
    "two_C_one_D": {"a1": "3", "a2": "3", "a3": "10"},   # C->R+S=3, D->T+T=10
    "one_C_two_D": {"a1": "0", "a2": "6", "a3": "6"},    # C->S+S=0, D->T+P=6
    "all_D": {"a1": "2", "a2": "2", "a3": "2"},          # P+P=2
}

NEIGHBOURHOOD_ORACLE = {
    "all_C": {"a1": "3", "a2": "3", "a3": "3"},          # U_C(2)=3
    "two_C_one_D": {"a1": "3/2", "a2": "3/2", "a3": "5"},  # U_C(1)=3/2, U_D(2)=5
    "one_C_two_D": {"a1": "0", "a2": "3", "a3": "3"},    # U_C(0)=0, U_D(1)=3
    "all_D": {"a1": "1", "a2": "1", "a3": "1"},          # U_D(0)=1
}

# move assignment per profile (a1 <= a2 <= a3 by id); C-count fixed per profile
PROFILES = {
    "all_C": {"a1": "C", "a2": "C", "a3": "C"},
    "two_C_one_D": {"a1": "C", "a2": "C", "a3": "D"},
    "one_C_two_D": {"a1": "C", "a2": "D", "a3": "D"},
    "all_D": {"a1": "D", "a2": "D", "a3": "D"},
}


def _pairwise_from_letters(letters):
    moves = {}
    for a in ("a1", "a2", "a3"):
        moves[a] = {o: letters[a] for o in ("a1", "a2", "a3") if o != a}
    return {a: PairwiseVoteAction(moves=m) for a, m in moves.items()}


@pytest.mark.parametrize("profile", list(PROFILES))
def test_pairwise_mechanism_resolve_matches_oracle(profile):
    mech = nipd("pairwise")
    state = mech.initial_state()
    actions = _pairwise_from_letters(PROFILES[profile])
    new_state, _events = step(mech, state, actions)
    assert new_state["scores"] == PAIRWISE_ORACLE[profile]


@pytest.mark.parametrize("profile", list(PROFILES))
def test_neighbourhood_mechanism_resolve_matches_oracle(profile):
    mech = nipd("neighbourhood")
    state = mech.initial_state()
    actions = neighbourhood_actions(PROFILES[profile])
    new_state, _events = step(mech, state, actions)
    assert new_state["scores"] == NEIGHBOURHOOD_ORACLE[profile]


def test_pairwise_game_pure_function_full_table():
    assert pairwise_game("C", "C", PARAMS) == (3, 3)
    assert pairwise_game("C", "D", PARAMS) == (0, 5)
    assert pairwise_game("D", "C", PARAMS) == (5, 0)
    assert pairwise_game("D", "D", PARAMS) == (1, 1)


def test_neighbourhood_payoff_pure_function_all_k():
    n = 3
    # cooperator: U_C(k) = 3k/2
    assert neighbourhood_payoff("C", 0, n, PARAMS) == Fraction(0)
    assert neighbourhood_payoff("C", 1, n, PARAMS) == Fraction(3, 2)
    assert neighbourhood_payoff("C", 2, n, PARAMS) == Fraction(3)
    # defector: U_D(k) = 1 + 2k
    assert neighbourhood_payoff("D", 0, n, PARAMS) == Fraction(1)
    assert neighbourhood_payoff("D", 1, n, PARAMS) == Fraction(3)
    assert neighbourhood_payoff("D", 2, n, PARAMS) == Fraction(5)


def test_neighbourhood_payoff_returns_exact_fraction_type():
    val = neighbourhood_payoff("C", 1, 3, PARAMS)
    assert isinstance(val, Fraction)
    assert val == Fraction(3, 2)


def test_defection_strictly_dominant_pairwise():
    # In every pairwise cell, D beats C against a fixed opponent move.
    assert pairwise_game("D", "C", PARAMS)[0] > pairwise_game("C", "C", PARAMS)[0]
    assert pairwise_game("D", "D", PARAMS)[0] > pairwise_game("C", "D", PARAMS)[0]


def test_defection_strictly_dominant_neighbourhood():
    # For each k of OTHER cooperators, U_D(k) > U_C(k).
    for k in range(3):
        assert neighbourhood_payoff("D", k, 3, PARAMS) > neighbourhood_payoff("C", k, 3, PARAMS)


def test_is_dilemma_defaults_and_axelrod_condition():
    assert NIPDParams().is_dilemma(3) is True
    # 2R > T + S: 6 > 5. Break it and is_dilemma must be False.
    assert NIPDParams(T=5, R=2, P=1, S=0).is_dilemma(3) is False  # 2R=4 !> 5
    assert NIPDParams(T=3, R=3, P=1, S=0).is_dilemma(3) is False  # T not > R
    # explicit 2R > T + S check on defaults
    p = NIPDParams()
    assert 2 * p.R > p.T + p.S
    assert p.T > p.R > p.P > p.S
