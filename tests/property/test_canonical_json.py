"""Canonical JSON + fraction serialization (engine/hashing.py).

Byte-stability rules: sorted keys, compact separators, ASCII-only escapes, and
a closed value grammar (None|bool|int|str|list|dict[str,...]). Floats and
Fractions are rejected anywhere in the tree; non-string keys are rejected.
frac_str/parse_frac round-trip exactly.
"""

import json
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from collaborative_hill.engine.hashing import (
    NonCanonicalValueError,
    canonical_json,
    content_hash,
    frac_str,
    parse_frac,
)


def test_keys_are_sorted_and_separators_compact():
    s = canonical_json({"b": 1, "a": 2, "c": {"z": 1, "y": 2}})
    assert s == '{"a":2,"b":1,"c":{"y":2,"z":1}}'


def test_non_ascii_is_escaped():
    s = canonical_json({"k": "café — π"})
    assert "\\u" in s
    assert all(ord(ch) < 128 for ch in s)
    # round-trips back to the original string
    assert json.loads(s)["k"] == "café — π"


def test_float_rejected_top_level():
    with pytest.raises(NonCanonicalValueError, match="float"):
        canonical_json(3.14)


def test_float_rejected_when_nested():
    with pytest.raises(NonCanonicalValueError, match=r"\$\.a\[1\]\.b"):
        canonical_json({"a": [1, {"b": 2.0}]})


def test_fraction_rejected_with_guidance():
    with pytest.raises(NonCanonicalValueError, match="frac_str"):
        canonical_json({"score": Fraction(3, 2)})


def test_non_string_key_rejected():
    with pytest.raises(NonCanonicalValueError, match="non-string key"):
        canonical_json({1: "a"})


def test_unsupported_type_rejected():
    with pytest.raises(NonCanonicalValueError, match="unsupported type"):
        canonical_json({"x": {1, 2, 3}})  # a set


def test_tuple_serializes_like_list():
    assert canonical_json({"x": (1, 2, 3)}) == canonical_json({"x": [1, 2, 3]})


def test_frac_str_known_values():
    assert frac_str(Fraction(3, 2)) == "3/2"
    assert frac_str(Fraction(39)) == "39"
    assert frac_str(Fraction(-1, 3)) == "-1/3"
    assert frac_str(0) == "0"
    assert frac_str(Fraction(4, 2)) == "2"  # normalized


@given(st.integers(min_value=-(10**6), max_value=10**6),
       st.integers(min_value=1, max_value=10**6))
def test_frac_str_parse_frac_round_trip(num, den):
    f = Fraction(num, den)
    assert parse_frac(frac_str(f)) == f


@given(st.integers(min_value=-(10**9), max_value=10**9))
def test_frac_str_integer_round_trip(n):
    assert parse_frac(frac_str(Fraction(n))) == Fraction(n)
    assert "/" not in frac_str(Fraction(n))


# Canonical JSON is a closed grammar over these value types.
_json_value = st.recursive(
    st.none() | st.booleans() | st.integers(min_value=-(10**9), max_value=10**9)
    | st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=0x2FFF)),
    lambda children: st.lists(children, max_size=4)
    | st.dictionaries(st.text(min_size=0, max_size=6), children, max_size=4),
    max_leaves=25,
)


@given(_json_value)
def test_canonical_json_is_deterministic_and_reparses(value):
    a = canonical_json(value)
    b = canonical_json(value)
    assert a == b
    # keys sorted at every level -> re-serializing the parsed form is a fixpoint
    reparsed = json.loads(a)
    assert canonical_json(reparsed) == a
    assert content_hash(value) == content_hash(reparsed)


@given(_json_value)
def test_canonical_json_keys_sorted_everywhere(value):
    s = canonical_json(value)

    def check(obj):
        if isinstance(obj, dict):
            keys = list(obj.keys())
            assert keys == sorted(keys)
            for v in obj.values():
                check(v)
        elif isinstance(obj, list):
            for v in obj:
                check(v)

    check(json.loads(s))
