# Graph topology — deterministic offline controls

**Status: executed exploratory controls, unfrozen; scripted agents only.**
The analytical predictions below were committed before execution. They are not an
externally timestamped preregistration. The mechanism contract is
[ADR-0011](../../docs/adr/0011-versioned-graph-nipd.md).

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
a study. Local source identity and execution evidence are recorded separately
from these analytical predictions.

## Recorded execution

The original run completed all 18 episodes (144 rounds and 3,114 ledger events).
All 18 measured cooperation curves match the pre-execution predictions, and all
18 sealed runs replay successfully. The [exact readout](RESULTS.md) and
[machine-readable results](RESULTS.json) retain every curve and terminal score.

Targeted TFT's mean eligible-vote cooperation is `5/8` on both complete and ring
graphs. Linked TFT has mean `1/10` on the complete graph and `3/20` on the ring:
the ring delays the spread of defection by one round in this fixed design. On the
star, targeted and linked TFT both have mean `1/16` with AllD at the hub; with AllD
at a leaf their means are `49/64` and `5/32`. Quorum TFT remains at `4/5` except
with AllD at the star hub, where its eight-round mean is `1/10`. These fractions
use the action-mode-specific vote units described above; moving AllD also changes
policy placement and, for pairwise votes, its degree weight.

The original execution and report used clean local source
`873666aa9dfe1de7cc76d31275b4828fa44e065d`, Python 3.12.14 and all 38 applicable
dependency-lock pins, including setuptools 84.1.0. The
[raw execution source record](EXECUTION_SOURCE.json) commits to 71 named
source/input files, all checked against that commit's Git blobs. The native
[published source checkpoint](https://github.com/Chris0Jeky/collaborative-hill-lab/commit/78caa2a98c62c1818227e90886525d6f2aa19eb0)
was created before this execution and has the identical full Git tree
`875823c171036dcf40a0b9f2834074bce7ad05f9`. Its different commit identifier reflects
the different parent history. [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json)
records that mapping and the original file checksums separately.

`RESULTS.json`, `RESULTS.md` and `EXECUTION_SOURCE.json` are unchanged copies of
the original generated bytes. The JSON SHA-256 is
`69349116386452e913e1eabc546082a9d052d8993fc3a2dbb5f134658fe6a099`.
The original readout was regenerated byte-for-byte from the original sealed
artifacts, with all 18 runs replayed again. Raw ledgers and checkpoints remain
generated artifacts outside Git; independent replay needs those artifacts.
The execution source record preserves the pre-execution README hash, so this
later status/readout update does not replace the original design commitment.

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
