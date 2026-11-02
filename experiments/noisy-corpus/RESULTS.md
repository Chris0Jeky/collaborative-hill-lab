# Noisy corpus — exact synthetic expectations

This is an unfrozen offline scripted-policy experiment. Its complete local
[design](DESIGN.md) and [ADR-0017](../../docs/adr/0017-noisy-corpus-and-audit-contract.md)
precede execution. The source commit and file digests are in
[SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json); every finite outcome, schedule,
terminal hash and exact weighting is retained in [RESULTS.json](RESULTS.json).

**64 behavioral episodes, 64 action-fixed accounting controls, 128 full ledger replays; 8 rounds per episode.**
The six error rates and two error-dependence models reweight those same outcomes.
These are declared models, not estimates, extra replicates or empirical prevalence.
The truth mixture assigns p and q probability 1/2 each by construction.

Declared predictions held: P1, P2, P3, P4, P5, P6, P7, P8. Not held: none.

## Exact outcomes by rate

C and W are probabilities of a correct or wrong accepted slot. Abstention is the
probability of no accepted slot. Selective accuracy conditions on acceptance; an
em dash means undefined because acceptance has probability zero. All values are exact.
Effort, contribution and total utility are expectations at the declared placeholders.
Behavioral expectations use aggregate accountability; attributable runs replay the same
actions.

| Error model | Labels | e | Rule | C | W | Abstention | Selective accuracy | Quality | Effort | Contribution | Total utility |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| independent | distinct | 0 | conditional | 1 | 0 | 0 | 1 | 12 | 24 | 3/4 | -5 |
| independent | collapsed | 0 | conditional | 1 | 0 | 0 | 1 | 12 | 24 | 3/4 | -5 |
| independent | distinct | 0 | skeptical | 1 | 0 | 0 | 1 | 12 | 24 | 3/4 | -5 |
| independent | collapsed | 0 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| independent | distinct | 1/10 | conditional | 9/10 | 1/10 | 0 | 9/10 | 48/5 | 24 | 3/4 | -44/5 |
| independent | collapsed | 1/10 | conditional | 9/10 | 1/10 | 0 | 9/10 | 48/5 | 24 | 3/4 | -44/5 |
| independent | distinct | 1/10 | skeptical | 729/1000 | 1/1000 | 27/100 | 729/730 | 1092/125 | 399/20 | 519/800 | -3059/500 |
| independent | collapsed | 1/10 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| independent | distinct | 1/4 | conditional | 3/4 | 1/4 | 0 | 3/4 | 6 | 24 | 3/4 | -29/2 |
| independent | collapsed | 1/4 | conditional | 3/4 | 1/4 | 0 | 3/4 | 6 | 24 | 3/4 | -29/2 |
| independent | distinct | 1/4 | skeptical | 27/64 | 1/64 | 9/16 | 27/28 | 39/8 | 249/16 | 69/128 | -251/32 |
| independent | collapsed | 1/4 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| independent | distinct | 1/2 | conditional | 1/2 | 1/2 | 0 | 1/2 | 0 | 24 | 3/4 | -24 |
| independent | collapsed | 1/2 | conditional | 1/2 | 1/2 | 0 | 1/2 | 0 | 24 | 3/4 | -24 |
| independent | distinct | 1/2 | skeptical | 1/8 | 1/8 | 3/4 | 1/2 | 0 | 51/4 | 15/32 | -51/4 |
| independent | collapsed | 1/2 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| independent | distinct | 3/4 | conditional | 1/4 | 3/4 | 0 | 1/4 | -6 | 24 | 3/4 | -67/2 |
| independent | collapsed | 3/4 | conditional | 1/4 | 3/4 | 0 | 1/4 | -6 | 24 | 3/4 | -67/2 |
| independent | distinct | 3/4 | skeptical | 1/64 | 27/64 | 9/16 | 1/28 | -39/8 | 249/16 | 69/128 | -745/32 |
| independent | collapsed | 3/4 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| independent | distinct | 1 | conditional | 0 | 1 | 0 | 0 | -12 | 24 | 3/4 | -43 |
| independent | collapsed | 1 | conditional | 0 | 1 | 0 | 0 | -12 | 24 | 3/4 | -43 |
| independent | distinct | 1 | skeptical | 0 | 1 | 0 | 0 | -12 | 24 | 3/4 | -43 |
| independent | collapsed | 1 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| correlated | distinct | 0 | conditional | 1 | 0 | 0 | 1 | 12 | 24 | 3/4 | -5 |
| correlated | collapsed | 0 | conditional | 1 | 0 | 0 | 1 | 12 | 24 | 3/4 | -5 |
| correlated | distinct | 0 | skeptical | 1 | 0 | 0 | 1 | 12 | 24 | 3/4 | -5 |
| correlated | collapsed | 0 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| correlated | distinct | 1/10 | conditional | 9/10 | 1/10 | 0 | 9/10 | 48/5 | 24 | 3/4 | -44/5 |
| correlated | collapsed | 1/10 | conditional | 9/10 | 1/10 | 0 | 9/10 | 48/5 | 24 | 3/4 | -44/5 |
| correlated | distinct | 1/10 | skeptical | 9/10 | 1/10 | 0 | 9/10 | 48/5 | 24 | 3/4 | -44/5 |
| correlated | collapsed | 1/10 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| correlated | distinct | 1/4 | conditional | 3/4 | 1/4 | 0 | 3/4 | 6 | 24 | 3/4 | -29/2 |
| correlated | collapsed | 1/4 | conditional | 3/4 | 1/4 | 0 | 3/4 | 6 | 24 | 3/4 | -29/2 |
| correlated | distinct | 1/4 | skeptical | 3/4 | 1/4 | 0 | 3/4 | 6 | 24 | 3/4 | -29/2 |
| correlated | collapsed | 1/4 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| correlated | distinct | 1/2 | conditional | 1/2 | 1/2 | 0 | 1/2 | 0 | 24 | 3/4 | -24 |
| correlated | collapsed | 1/2 | conditional | 1/2 | 1/2 | 0 | 1/2 | 0 | 24 | 3/4 | -24 |
| correlated | distinct | 1/2 | skeptical | 1/2 | 1/2 | 0 | 1/2 | 0 | 24 | 3/4 | -24 |
| correlated | collapsed | 1/2 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| correlated | distinct | 3/4 | conditional | 1/4 | 3/4 | 0 | 1/4 | -6 | 24 | 3/4 | -67/2 |
| correlated | collapsed | 3/4 | conditional | 1/4 | 3/4 | 0 | 1/4 | -6 | 24 | 3/4 | -67/2 |
| correlated | distinct | 3/4 | skeptical | 1/4 | 3/4 | 0 | 1/4 | -6 | 24 | 3/4 | -67/2 |
| correlated | collapsed | 3/4 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |
| correlated | distinct | 1 | conditional | 0 | 1 | 0 | 0 | -12 | 24 | 3/4 | -43 |
| correlated | collapsed | 1 | conditional | 0 | 1 | 0 | 0 | -12 | 24 | 3/4 | -43 |
| correlated | distinct | 1 | skeptical | 0 | 1 | 0 | 0 | -12 | 24 | 3/4 | -43 |
| correlated | collapsed | 1 | skeptical | 0 | 0 | 1 | — | 0 | 9 | 3/8 | -9 |

## Conditional expectations and negative controls

RESULTS.json also retains separate p-true and q-true expectation rows. Each is checked
against the closed-form oracle; their equality is a property of this symmetric synthetic
design. It does not estimate real truth prevalence.

All 32 matched truth-flip pairs are checked for identical
observations and typed actions, opposite signed quality and equal effort. Whole ledgers
are checked for hidden truth-field keys. Correctness in the final unobserved seal is
permitted; neither baseline policy receives truth during the episode.

The independent error model has C=(1-e)^3 and W=e^3 for the distinct-label skeptic.
The conditional control follows the first report: C=1-e and W=e. Thus the declared
skeptical-minus-conditional quality difference is -12 e(1-e)(1-2e). Screening lowers
signed quality at e=1/10 and e=1/4 despite improving selective accuracy; it discards
many correct claims along with wrong ones. At e=3/4 its positive contrast means
less negative quality. Effort savings and utility changes remain separate outcomes.

With fully correlated errors, three distinct labels always agree, even when wrong.
Both rules then have the same C=1-e and W=e. The marginal error rate alone does not
identify the value of corroboration. Collapsing labels always silences the skeptic,
including when the generator produces independent reports or perfect evidence.

## Audit observation contract foundation

The separately versioned `ec-audit-observation@1` contract has strict validated inputs,
a deterministic public projection, fixed target/publication timing, exact declared
accuracy and explicit unavailable reports. The checked fixture is in RESULTS.json.
**No audit-enabled engine, audit policy, truth-feedback episode or learned behavior is
implemented here.** The supplied fixture findings do not establish their accuracy.
Accuracy 1 would be a perfect synthetic trusted-oracle assumption, not deployed truth.
ADR-0017 lists the remaining compiler/version/hash, generator, engine/event, policy,
replay/branch/leak/C3, and pre-execution experimental-design gates.

## Scope

This one-slot, all-active, full-reading design identifies exact outcomes only under
its imposed corpus distributions and placeholders. It supplies no general benefit,
optimal institution, equilibrium, social-dilemma, human or LLM claim. No weights or
models were selected and no study was frozen. Existing study and experiment evidence
was left unchanged. Distinct source labels are not evidence of real independence.

## Reproduce

```bash
python experiments/noisy-corpus/noisy_corpus.py --out artifacts/noisy-corpus-new
python experiments/noisy-corpus/noisy_corpus.py --check
```

`--out` requires a clean committed worktree and a fresh directory. `--check`
recreates all 128 sealed runs, verifies every full replay, and byte-compares the JSON
and Markdown readouts in a temporary directory. Both remain offline.

Study hash: `5909c798f10bdc1f16ca5cc3bda4398a98c27146875ac27bacb8ff2ae9a87d5c`. The study remains unfrozen.
