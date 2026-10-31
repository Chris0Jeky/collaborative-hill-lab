"""Independent copying-choice history oracle; deliberately imports no model code."""

from fractions import Fraction
from itertools import product
from math import prod


def histories(adjacency, fixed_defectors, denominator, rounds):
    """Enumerate uniform source-vertex choices and keep entire labeled histories."""
    agents = tuple(sorted(adjacency))
    dynamic = tuple(a for a in agents if a not in fixed_defectors)
    seats = {a: i for i, a in enumerate(agents)}
    choices = [tuple(adjacency[a]) + ((a,) if denominator == "include_self" else ())
               for a in dynamic]
    weight = Fraction(1, prod(map(len, choices)))
    initial = tuple(int(a in dynamic) for a in agents)
    paths = {(initial,): Fraction(1)}
    for _ in range(rounds - 1):
        following_paths = {}
        for history, probability in paths.items():
            for sources in product(*choices):
                votes = dict.fromkeys(agents, 0)
                for actor, source in zip(dynamic, sources, strict=True):
                    votes[actor] = history[-1][seats[source]]
                following = tuple(votes[a] for a in agents)
                key = (*history, following)
                following_paths[key] = following_paths.get(key, Fraction()) + probability * weight
        paths = following_paths
    assert sum(paths.values()) == 1
    return paths
