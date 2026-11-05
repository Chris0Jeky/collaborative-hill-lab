# Discover, run and inspect an experiment

This walkthrough runs the existing graph-topology controls, checks the resulting
artifacts, and opens a visual replay. It is fully offline after installation.
The experiment is small: 18 declared conditions, one eight-round episode each.

The question is concrete: **how do network topology, defector placement and the
reciprocity rule change cooperation?** The design holds its other settings fixed.
It includes complete, ring and star networks with targeted, linked and quorum
policies. It does not establish that one topology is best in general.

## 1. Install once and discover the available work

From the repository checkout, follow the [setup instructions](../README.md#install-and-verify)
and activate the virtual environment. Then run:

```bash
chl catalog
chl catalog --json
```

The catalog connects the shipped studies, standalone experiment packs and
historical reference. Each entry explains its question, evidence status,
source/readout and available operations. Some entries are analytical checks or
historical references, so they deliberately have no simulation run command.

Without activation, replace `chl` with `.venv/bin/python -m collaborative_hill.cli`
on POSIX or `.venv/Scripts/python.exe -m collaborative_hill.cli` on Windows.

## 2. Inspect the plan before running

Choose a directory that does not already exist:

```bash
chl experiment plan graph-topology --out artifacts/graph-first
chl experiment plan graph-topology --out artifacts/graph-first --json
```

Planning shows the actual commands without running them or creating the output.
JSON exposes the plan for agents. Inspect the requested operation and destination;
the catalog is a consistent front door to the existing experiment scripts, and
each script retains its own provenance and output protections.

## 3. Execute the existing design

```bash
chl experiment run graph-topology --out artifacts/graph-first
```

The graph runner retains its inputs, execution-source record, 18 sealed ledgers
and exact readout. It independently replays the runs. A destination that already
exists is refused; use another name for another execution. Do not delete an old
result merely to make this command succeed.

This execution helps you explore or verify the declared design. A repeat of its
deterministic controls is not another independent sample or a new preregistered
study. The checked-in original results and their source records remain separate.

## 4. Check artifact health

```bash
chl monitor artifacts/graph-first
chl monitor artifacts/graph-first --json
```

After a successful run, the snapshot should show **18 completed, 0 failed,
0 unsealed and 0 broken**. A partial run may show unsealed artifacts, but that
does not tell you whether its process is still alive. A valid recorded failure
and a broken artifact have different labels. The command never changes a run.
See [monitoring states and JSON](MONITORING.md) for exit codes and integrity scope.

## 5. Create and open the visual inspector

```bash
chl lab artifacts/graph-first --out artifacts/graph-first-console.html --verify-replay
```

Open `artifacts/graph-first-console.html` in a browser. It is self-contained and
works without a server or network connection. Keep the console outside the
individual evidence-run directories, and use a new filename when exporting it
again. Existing outputs are protected.

Start with the cooperation curve and agent film strips. Select a run and a
logical round to inspect the network interactions, recorded actions and agent
observations. Compare the same policy and placement across topologies before
changing another factor. In an Evidence Commons run, the same inspector exposes
claims and released audit events. Observations describe what an agent had before
its decision; resolved actions describe what happened afterward. Expand the exact
record when the summary needs more detail.

The console validates sealed inputs. `--verify-replay` additionally re-executes
the recorded actions and reports chain equality; it never calls an LLM provider.
Neither check authenticates an external source or turns a synthetic result into
a prediction about people.

## 6. Verify a pack or choose the next question

```bash
chl experiment plan graph-topology --check --json
chl experiment check graph-topology
```

Checks reproduce the existing verification contract, using temporary outputs
where the original gate does so. They do not replace the artifacts you just
created. Use the catalog to move next to Study 002's sensitivity controls,
responsive Evidence Commons, quality safeguards, component ablations, source
noise or audit feedback. Some full experiment packs require clean committed
source; the plan and runner report that requirement rather than weakening it.

When a new idea changes a mechanism, policy or scientific parameter, start from
the [current roadmap](../NEXT.md) and record its question, predicted contrasts
and controls before execution. Preserve negative and null findings. A new
experiment should explain a specific uncertainty in the existing evidence.

## Maintaining the visual workflow

The integration test runs the public command sequence on the real graph design,
checks all 18 completed ledgers, verifies replay and confirms that inspection and
a refused repeat leave source inputs and run artifacts unchanged.

On a machine with Chrome, `make check-lab-browser` additionally exercises the
actual run, agent and round controls, audit publication timing and graph rendering
at desktop and mobile widths. It writes screenshots, DOM snapshots and a JSON
result into a fresh `artifacts/browser-smoke` directory. For a repeat, call
`python scripts/check_lab_browser.py --out artifacts/browser-smoke-repeat`.
Use `--browser PATH` or `CHROME_BIN` when Chrome is not on the executable path.
The Ubuntu CI job runs this check and retains its review artifacts for 14 days.
Chrome is optional for running the lab itself.
