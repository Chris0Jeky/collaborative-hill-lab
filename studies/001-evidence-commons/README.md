# Study 001 — Evidence Commons (DRAFT, human approval required)

Three agents assemble a shared briefing from fragmented, partly stale, partly false
evidence under mixed incentives. 2×2 design: **accountability** (aggregate vs attributable
peer review) × **evidence topology** (private/fragmented vs shared provenance ledger), plus
an optional misinformation arm. This is the first Evidence Commons instantiation of the
core research question (see `docs/research/RESEARCH_CHARTER.md`).

## What exists and runs today (no LLM, no cost)

- `generate_study.py` — produces the validated scenarios, two narrative skins, study.json.
- 5 conditions × 3 replicates of deterministic scripted personas
  (2 contributors + 1 free-rider; misinfo arm: contributor + verifier + misinformer):
  `chl run "studies/001-evidence-commons" --artifacts artifacts`
- `certificate.py` — the mechanism certificate: enumerates {contributor, freerider}³ under
  all four institutions and certifies (exact arithmetic): free-riding temptation exists
  everywhere (C1), contribution is collectively better (C2), and accountability
  redistributes credit without changing the task (C3). Output: `MECHANISM_CERTIFICATE.md`.
- `PREREGISTRATION.md` — DRAFT; every open item marked `HUMAN DECISION`.
- `COST_WORKSHEET.md` — measured prompt sizes + formulas; no prices assumed.

## Seed protocols and an explicitly paired draft

**The checked-in `study.json` uses legacy independent streams.** Its missing protocol field
means `legacy-independent-v1`: policy randomness includes the condition ID, so matching
replicate numbers do not create common random numbers (CRN). Earlier claims otherwise were
incorrect (see `docs/adr/0008-versioned-policy-pairing.md`). Its existing hashes, streams,
and sealed-run replay remain compatible. The deterministic personas do not consume their
RNG, so switching protocols alone does not add stochastic replication.

To create and smoke-run a **new, unfrozen** paired draft from the repository root:

```bash
python studies/001-evidence-commons/generate_study.py --seed-protocol paired-policy-v2 --output artifacts/drafts/study-001-paired-v2
python -m collaborative_hill.cli study validate artifacts/drafts/study-001-paired-v2
python -m collaborative_hill.cli run artifacts/drafts/study-001-paired-v2 --artifacts artifacts/paired-smoke --replicates 1
```

Use the project's Python environment. The output directory must be new or empty; the
generator refuses to overwrite the original study or a frozen output. Running the generator
without the protocol flag reproduces the original independent-stream JSON. No command above
freezes a study or changes hypotheses, providers, weights, sample-size decisions, or costs.

The paired draft has study ID `001-evidence-commons-paired-v2`, an explicit protocol field,
and explicit `scenario_block` on every condition. The four 2×2 cells share block `factorial`;
the optional arm with a different policy population has block `misinformation`. Within a
block/replicate, agent/round policy streams match across conditions; mechanism streams stay
condition-specific. The block mapping is part of the new study hash. It is an exploratory
configuration to review before preregistration, not an automatic scientific equivalence test.

Matching draws do not guarantee matching actions: accountability/topology change what an
agent observes, and policies may consume draws differently. `LLMPolicy` currently ignores
the kernel RNG, so this option provides **no provider-sampling CRN guarantee**. The SAP's
paired models require a verified pairing design for the randomness actually used.

## Environment details

- 4 briefing slots, 2 candidate propositions each (finite, typed — no free-text claims).
- 10 evidence items: fresh/stale, supporting/contradicting, one misinformation item (e05),
  one stale corroboration (e04), and one **prompt-injection fixture** (e08) whose prose
  (in both skins) instructs the reader to bypass verification — mechanically inert because
  only typed actions mutate the world.
- Budgets: 6 inspections, 3 verifications per agent; every contribution action costs
  effort; the briefing's quality reward is shared equally (the commons).
- Acceptance: deterministic net-support rule; verification is engine-adjudicated
  provenance-checking (see `CLAIMS_AND_LIMITATIONS.md` — agents cannot yet lie in
  verification; that is future work, not a hidden assumption).

## Skins

Two full skins over the identical mechanism (hash-verified at generation):
`official-briefing` (municipal council) and `newsroom-desk` (fact desk). The metamorphic
suite proves skin swaps cannot change mechanism hashes or scripted-run event chains.

## What must NOT happen without a human

- Freezing this study (`chl study freeze … --yes`).
- Any paid LLM run.
- Final choice of hypotheses, primary outcomes, utility weights, models, replicate count,
  cost ceiling (list in PREREGISTRATION.md footer and HANDOFF.md).
