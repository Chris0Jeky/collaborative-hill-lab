"""Property tests for hierarchical deterministic seeding (engine/seeds.py).

Invariants under test:
- derive_seed is a pure function of the path (stable across calls).
- distinct last components (with distinct str()) give distinct seeds.
- the unit separator makes the path encoding injective: ("ab","c") and
  ("a","bc") never collide; more generally distinct string paths differ.
- str vs int is irrelevant precisely when str(x) is equal (documented aliasing).
- rng_for yields independent streams keyed by path (same path -> same draws).
- a component containing the reserved separator raises.
"""

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from collaborative_hill.engine.seeds import _SEP, derive_seed, rng_for

# Components avoiding the reserved unit separator (0x1f).
_safe_text = st.text(
    alphabet=st.characters(blacklist_characters="\x1f", min_codepoint=32, max_codepoint=200),
    min_size=0, max_size=8,
)
_component = st.one_of(_safe_text, st.integers(min_value=-(10**9), max_value=10**9))
_path = st.lists(_component, min_size=1, max_size=6).map(tuple)


@given(_path)
def test_derive_seed_is_stable(path):
    assert derive_seed(*path) == derive_seed(*path)
    assert 0 <= derive_seed(*path) < 2**64


@given(_path, _component, _component)
def test_different_last_component_differs(prefix, x, y):
    # Aliasing caveat: str/int equality collapses (derive_seed(1)==derive_seed("1")).
    assume(str(x) != str(y))
    assert derive_seed(*prefix, x) != derive_seed(*prefix, y)


_string_path = st.lists(_safe_text, min_size=1, max_size=6).map(tuple)


@given(_string_path, _string_path)
def test_distinct_string_paths_have_distinct_seeds(p1, p2):
    # The unit-separator encoding is injective over separator-free strings, so
    # distinct string paths never collide (the ("ab","c") vs ("a","bc") family).
    assume(p1 != p2)
    assert derive_seed(*p1) != derive_seed(*p2)


def test_explicit_separator_ambiguity_case():
    assert derive_seed("ab", "c") != derive_seed("a", "bc")


@given(_component)
def test_str_int_aliasing_only_when_str_equal(x):
    # Documented: components are stringified before hashing, so an int and its
    # decimal string alias to the same seed.
    assert derive_seed(x) == derive_seed(str(x))


def test_int_vs_split_string_do_not_alias():
    # 10 (one component) must differ from ("1","0") (two components).
    assert derive_seed(10) != derive_seed("1", "0")


@given(_path)
def test_rng_for_same_path_same_stream(path):
    a = rng_for(*path)
    b = rng_for(*path)
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]


@given(_path, _path)
def test_rng_for_different_path_independent_first_draw(p1, p2):
    assume(tuple(map(str, p1)) != tuple(map(str, p2)))
    # First draws differ with overwhelming probability (distinct 64-bit seeds).
    assert rng_for(*p1).random() != rng_for(*p2).random()


def test_empty_path_raises():
    with pytest.raises(ValueError):
        derive_seed()


def test_reserved_separator_component_raises():
    sep = _SEP.decode("latin-1")
    with pytest.raises(ValueError, match="reserved separator"):
        derive_seed("a" + sep + "b")


def test_bool_component_rejected():
    # bool is an int subclass but explicitly disallowed to avoid True/1 aliasing.
    with pytest.raises(TypeError):
        derive_seed(True)
