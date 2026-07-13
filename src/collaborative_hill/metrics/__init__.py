"""Metric families, each versioned. Metrics read sealed ledgers only.

No metric may influence a live run (locked principle #2/#12): the runner never
imports this package. Floats are allowed HERE because metric outputs are
derived analysis artifacts, never part of any hash chain.

There is deliberately no single leaderboard score. Studies name one or two
primary outcomes; everything else is secondary/exploratory (METHODOLOGY.md).
"""

from collaborative_hill.metrics.cooperation import cooperation_metrics
from collaborative_hill.metrics.distribution import distribution_metrics
from collaborative_hill.metrics.epistemics import epistemic_metrics
from collaborative_hill.metrics.operations import operational_metrics

METRIC_VERSIONS = {
    "cooperation": "1",
    "epistemics": "1",
    "distribution": "1",
    "operations": "1",
}

__all__ = [
    "METRIC_VERSIONS",
    "cooperation_metrics",
    "epistemic_metrics",
    "distribution_metrics",
    "operational_metrics",
]
