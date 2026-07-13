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
