# Graph topology — deterministic offline controls

**Status: pre-execution exploratory design, unfrozen; scripted agents only.**
These local predictions precede execution. They are not an externally timestamped
preregistration. The mechanism contract is [ADR-0011](../../docs/adr/0011-versioned-graph-nipd.md).

## Fixed comparison

Use five agents `a1` through `a5`, one fixed AllD and four reciprocators, eight
simultaneous rounds (`t=0,…,7`), T=5/R=3/P=1/S=0, zero exploration and **mean edge
payoff** in every condition. Cross three labelled graphs, two defector seats and
three policy rules: 18 deterministic episodes, one per condition.

- Complete: every distinct pair is adjacent.
- Ring: `a1—a2—a3—a4—a5—a1`.
- Star: center `a1`, leaves `a2`, `a3`, `a4`, `a5`.
- AllD occupies either `a1` or `a2`; the remaining seats share one reciprocator
  rule: targeted pairwise TFT, linked pairwise TFT, or neighbourhood quorum TFT
  with threshold `1/2`.

Changing only the graph within a fixed seat/policy condition is a specified
topology intervention. Cross-policy comparisons also change the action and
observation rule, while changing AllD's seat changes the policy placement. In
particular, the star's hub-defector and leaf-defector conditions are separate
conditions. The complete/ring seat variants are symmetry controls, not independent
replications. No inferential intervals or significance claims are attached.

Mean edge payoff is fixed across this experiment's two action modes. Separate
complete-graph equivalence tests use **pairwise/sum** and **neighbourhood/mean**
to match the corresponding legacy score conventions. A complete-graph pairwise
mean score here is the legacy sum divided by degree four.

## Analytical predictions — before execution

Each sequence below gives the eligible-vote cooperation rate over eight rounds.
The notation `x × k` means that the exact rate x repeats for k rounds. Pairwise
votes are directed edge moves; neighbourhood votes are one per active agent, so
their denominators differ even under equal payoffs and the same graph.
Pairwise vote rates weight agents by degree: the star's different first-round
rates already reflect whether AllD controls four directed votes or one. They do
not represent a behavioral response before the first interaction.

| Graph / AllD seat | Targeted TFT | Linked TFT | Quorum TFT, q=1/2 |
|---|---|---|---|
| Complete / either seat | `4/5`, then `3/5 × 7` | `4/5`, then `0 × 7` | `4/5 × 8` |
| Ring / either seat | `4/5`, then `3/5 × 7` | `4/5`, `2/5`, then `0 × 6` | `4/5 × 8` |
| Star / hub a1 | `1/2`, then `0 × 7` | `1/2`, then `0 × 7` | `4/5`, then `0 × 7` |
| Star / leaf a2 | `7/8`, then `3/4 × 7` | `7/8`, `3/8`, then `0 × 6` | `4/5 × 8` |

Targeted TFT changes only moves toward AllD, leaving every C–C edge cooperative.
Linked TFT spreads defection from the persistent defector one edge per round;
the maximum graph distance is one or two in these fixtures. Quorum TFT sustains
at the inclusive 1/2 boundary on the ring, at 3/4 on the complete graph and at the
star center when AllD is a leaf. With AllD at the hub, every leaf sees zero
cooperative neighbors and switches to D after its initial C.

No pTFT count-state prediction is transferred to these sparse graphs. Local
degree, placement and neighborhood history determine each agent's signal; a
global cooperator count generally does not determine the next-round law.
[ADR-0011](../../docs/adr/0011-versioned-graph-nipd.md#exact-counterexample-to-a-sparse-count-state-shortcut)
gives an exact four-cycle witness: two reachable states with two cooperators have
next-count means `3/2` and `1`, with literal transition PMFs checked independently.

## Evidence and scope

Implementation tests separately pin hand-derived ring/star/isolated-node rewards,
legacy complete-graph equivalence, illegal action rejection, nonneighbor privacy,
hash canonicalization, replay, branching and skin/relabel invariance. This
experiment adds a compact descriptive comparison; it cannot establish a human or
LLM response, select a production topology, establish statistical power or freeze
a study. Local source identity and execution evidence will be recorded separately
from these analytical predictions.

## Generate, execute and verify

With the committed environment installed, run from the repository root:

```sh
python experiments/graph-topology/graph_experiment.py --check
python -m collaborative_hill.cli study validate experiments/graph-topology
python experiments/graph-topology/graph_experiment.py --run --artifacts artifacts/graph-topology-fresh
```

The last command requires a fresh artifact root, runs the 18 declared episodes,
then independently replays all 18 and writes `RESULTS.json` and `RESULTS.md` there.
It records source/input file commitments before execution in `EXECUTION_SOURCE.json`.
Original per-run manifests retain their own code and dirty-worktree provenance.
Local commit ids are source identities, not claims that those ids exist on GitHub.
No study is frozen and no provider is called.

To regenerate the exact readout from those same original artifacts:

```sh
python experiments/graph-topology/graph_experiment.py --report-from artifacts/graph-topology-fresh --output artifacts/graph-topology-fresh/RESULTS-copy
```

Report generation verifies the expected condition/seed/policy identities and raw
ledger chains and replays each run. It rejects missing, extra, misplaced, failed
or inconsistent runs. It retains complete measured/predicted curves and terminal
scores as exact fractions. The source commitments establish consistency relative
to retained evidence, not independent authenticity. New source code and new
execution artifacts constitute a new run, even if deterministic outcomes agree.

`--generate <new-directory>` creates the canonical StudySpec, 18 scenarios and one
skin; `--study-dir <directory>` selects that fixture for checking/execution/readout.
Generation preflights every file, preserves byte-identical files, refuses divergent
existing content and rejects frozen fixtures. Report outputs behave the same way.
To keep report paths separate from files the runner will create, `--run` always
writes its readout directly under the fresh artifact root; `--output` applies only
to `--report-from`. These are static filesystem checks, not an atomic guarantee
against concurrent ancestor replacement.
