"""Bounded labeled-state pTFT under ideal independent rational Bernoulli draws.

Neighborhood broadcast, zero exploration, fixed AllD actors. This module never
runs the simulator, samples an RNG, reads run artifacts, or computes payoffs.
"""

from fractions import Fraction
from itertools import product
from math import prod
from typing import Any, Literal

from collaborative_hill.domain.world.graph_nipd import UndirectedGraph
from collaborative_hill.engine.hashing import frac_str

Denominator = Literal["include_self", "exclude_self"]
State = tuple[int, ...]
Matrix = tuple[tuple[Fraction, ...], ...]
MAX_AGENTS = 6
MAX_STATES = 2 ** MAX_AGENTS
MAX_ROUNDS = 50


class GraphPTFT:
    """Exact full action vectors in sorted vertex order; fixed actors stay zero."""

    def __init__(self, adjacency: dict[str, tuple[str, ...]],
                 fixed_defectors: tuple[str, ...], denominator: Denominator) -> None:
        if not 2 <= len(adjacency) <= MAX_AGENTS:
            raise ValueError(f"graph must have 2 to at most {MAX_AGENTS} vertices")
        graph = UndirectedGraph(adjacency=adjacency)
        self.agents = tuple(graph.adjacency)
        if (not isinstance(fixed_defectors, tuple)
                or any(not isinstance(a, str) for a in fixed_defectors)
                or len(set(fixed_defectors)) != len(fixed_defectors)
                or not set(fixed_defectors) <= set(self.agents)):
            raise ValueError("fixed_defectors must be a tuple of distinct declared vertices")
        if denominator not in ("include_self", "exclude_self"):
            raise ValueError("denominator must be include_self or exclude_self")
        reached = {self.agents[0]}
        pending = [self.agents[0]]
        while pending:
            for neighbor in graph.adjacency[pending.pop()]:
                if neighbor not in reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
        if reached != set(self.agents):
            raise ValueError("only connected graphs are supported; no isolates")
        self.adjacency = dict(graph.adjacency)
        self.fixed_defectors = tuple(sorted(fixed_defectors))
        self.dynamic_agents = tuple(a for a in self.agents if a not in fixed_defectors)
        self.denominator = denominator
        self._neighbors = tuple(tuple(self.agents.index(b) for b in self.adjacency[a])
                                for a in self.agents)
        self.states = tuple(
            tuple(dict(zip(self.dynamic_agents, votes, strict=True)).get(a, 0)
                  for a in self.agents)
            for votes in product((0, 1), repeat=len(self.dynamic_agents))
        )

    def probabilities(self, state: State) -> tuple[Fraction, ...]:
        """P(next actor broadcasts C | labeled previous broadcasts).

        GraphNIPDMechanism.observe counts incident cooperating neighbors only.
        GraphProbabilisticTFTPolicy adds own previous C only for include-self.
        """
        if (len(state) != len(self.agents)
                or any(type(v) is not int or v not in (0, 1) for v in state)
                or any(state[i] for i, a in enumerate(self.agents) if a in self.fixed_defectors)):
            raise ValueError("state must be a full binary vector with fixed AllD seats zero")
        include = self.denominator == "include_self"
        return tuple(
            Fraction(sum(state[j] for j in neighbors) + (state[i] if include else 0),
                     len(neighbors) + int(include)) if a in self.dynamic_agents else Fraction()
            for i, (a, neighbors) in enumerate(zip(self.agents, self._neighbors, strict=True))
        )

    def transition_matrix(self) -> Matrix:
        """Conditional independence gives a product of actor Bernoulli factors."""
        rows = []
        for state in self.states:
            probabilities = self.probabilities(state)
            row = tuple(prod((p if vote else 1 - p
                              for p, vote in zip(probabilities, following, strict=True)),
                             start=Fraction(1)) for following in self.states)
            if sum(row) != 1 or any(p < 0 for p in row):
                raise ArithmeticError("invalid exact transition row")
            rows.append(row)
        return tuple(rows)

    def count_projection(self) -> Matrix:
        """Return the count law only after checking strong lumpability exactly."""
        projected: dict[int, tuple[Fraction, ...]] = {}
        for state, row in zip(self.states, self.transition_matrix(), strict=True):
            aggregate = tuple(sum((p for following, p in zip(self.states, row, strict=True)
                                   if sum(following) == k), Fraction())
                              for k in range(len(self.dynamic_agents) + 1))
            count = sum(state)
            if count in projected and projected[count] != aggregate:
                raise ValueError("global cooperator count is not lumpable; use labeled states")
            projected[count] = aggregate
        return tuple(projected[k] for k in range(len(self.dynamic_agents) + 1))

    def benchmark(self, rounds: int = 8) -> dict[str, Any]:
        """Finite-horizon moments, first-all-D CDF and restricted hitting time.

        t=0 is the initial all-pTFT-C round. Forward weighted path moments keep
        covariance: a[x]=E[S_t 1(X_t=x)], b[x]=E[S_t^2 1(X_t=x)], S_t=sum X_s.
        Absorption means first all-D, not entry into any recurrent class.
        """
        if type(rounds) is not int or not 1 <= rounds <= MAX_ROUNDS:
            raise ValueError(f"rounds must be an integer in [1, {MAX_ROUNDS}]")
        matrix = self.transition_matrix()
        counts = tuple(map(sum, self.states))
        size, m, n = len(self.states), len(self.dynamic_agents), len(self.agents)
        distribution = [Fraction()] * size
        distribution[-1] = Fraction(1)
        first_weighted = [p * m for p in distribution]
        second_weighted = [p * m * m for p in distribution]
        first, second, absorption = [], [], []
        for t in range(rounds):
            first.append(sum((p * k for p, k in zip(distribution, counts, strict=True)),
                             Fraction()))
            second.append(sum((p * k * k for p, k in zip(distribution, counts, strict=True)),
                              Fraction()))
            absorption.append(distribution[0])
            if t + 1 == rounds:
                break
            next_p, next_a, next_b = ([Fraction()] * size for _ in range(3))
            for i, row in enumerate(matrix):
                if not distribution[i]:
                    continue
                for j, chance in enumerate(row):
                    if not chance:
                        continue
                    k = counts[j]
                    next_p[j] += chance * distribution[i]
                    next_a[j] += chance * (first_weighted[i] + k * distribution[i])
                    next_b[j] += chance * (second_weighted[i] + 2 * k * first_weighted[i]
                                           + k * k * distribution[i])
            distribution, first_weighted, second_weighted = next_p, next_a, next_b
        total = sum(first_weighted, Fraction())
        variance = sum(second_weighted, Fraction()) - total * total
        marginal = sum((s - f * f for s, f in zip(second, first, strict=True)), Fraction())
        cross = (variance - marginal) / 2
        normalizer = (n * rounds) ** 2
        return {
            "schema_version": 1, "analysis_version": "sparse_ptft_exact@1",
            "model": "ideal_independent_rational_bernoulli", "epsilon": "0",
            "mode": "neighbourhood", "agents": list(self.agents),
            "adjacency": {a: list(self.adjacency[a]) for a in self.agents},
            "dynamic_agents": list(self.dynamic_agents),
            "fixed_defectors": list(self.fixed_defectors), "denominator": self.denominator,
            "state_count": size, "states": [list(s) for s in self.states],
            "initial_state": list(self.states[-1]), "first_round_index": 0, "rounds": rounds,
            "transition_probabilities": [[frac_str(p) for p in row] for row in matrix],
            "last_round_state_probabilities": [frac_str(p) for p in distribution],
            "expected_cooperators_by_round": [frac_str(f) for f in first],
            "expected_squared_cooperators_by_round": [frac_str(s) for s in second],
            "cooperation_by_round": [frac_str(f / n) for f in first],
            "expected_cumulative_cooperators": frac_str(total),
            "variance_cumulative_cooperators": frac_str(variance),
            "mean_cooperation": frac_str(total / (n * rounds)),
            "variance_mean_cooperation": frac_str(variance / normalizer),
            "variance_terms": {"sum_count_variances": frac_str(marginal),
                               "sum_cross_time_count_covariances": frac_str(cross),
                               "normalizer": frac_str(normalizer)},
            "absorption_state": list(self.states[0]),
            "absorption_by_round": [frac_str(p) for p in absorption],
            "first_all_d_by_round": [frac_str(absorption[0]), *(
                frac_str(absorption[t] - absorption[t - 1]) for t in range(1, rounds))],
            "absorption_probability_by_last_round": frac_str(absorption[-1]),
            "not_all_d_by_last_round": frac_str(1 - absorption[-1]),
            "hitting_time_censor_round": rounds - 1,
            "restricted_mean_first_all_d_round": frac_str(
                sum((1 - p for p in absorption[:-1]), Fraction())),
        }
