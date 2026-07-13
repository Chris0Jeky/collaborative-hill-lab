# NEXT — sequenced backlog

Each item: what, dependencies, definition of done. Engineering (E), research (R),
publication (P) tracks. Human-owned decisions are marked ⛔ (see HANDOFF.md).

## Now (order matters)

1. **R1 ⛔ Human review of Study 001 preregistration.**
   Deps: none. Done when: every `HUMAN DECISION` field in
   `studies/001-evidence-commons/PREREGISTRATION.md` is filled (hypotheses wording,
   primary outcomes, minimum effect of interest, models/providers, utility weights,
   cost ceiling, stopping rule) and `chl study freeze "studies/001-evidence-commons" --yes`
   has been run by the human.

2. **E1 Real provider adapter** (one provider, pinned model id).
   Deps: R1 (choice of provider). Done when: `agents/llm/providers.py` gains a provider
   class that fills real token counts, is covered by a mocked unit test, records exact
   model id in manifests, and a single-episode live smoke (human-triggered, tiny budget)
   completes with tokens recorded and cost computed from a dated pricing entry in
   COST_WORKSHEET.md.

3. **R2 Study 001 pilot** (5 episodes/cell).
   Deps: E1, R1. Done when: pilot report with episode-level outcome variance,
   invalid-action rate, measured tokens/episode; sample-size table for 3+ candidate
   effect sizes; both skins piloted; abort thresholds validated.

4. **E2 Analysis notebook-free pipeline for the 2×2.**
   Deps: R2. Done when: `scripts/analyze_001.py` (or `chl analyze`) computes the SAP's
   paired contrasts + bootstrap CIs + Holm from sealed artifacts only, with golden-file
   test on scripted fixture data.

## Soon

5. **E3 Deception-capable verification** (agent-REPORTED verification outcomes + engine
   audit trail; makes lying measurable). Deps: none technically; R-design first.
   Done when: v1 mechanism version exists behind a scenario flag with certificate update +
   tests; v0 runs unchanged (hash-stable).
6. **E4 Reputation/sanction institution** (SanctSim lineage). Deps: E3 preferred.
   Done when: new InstitutionConfig field + rules + certificate C3-style invariance check.
7. **R3 Deconfound follow-up for the NPD lineage**: threshold sweep for quorum TFT
   (knife-edge at 1/2), pTFT denominator sensitivity, N=5. Done when: Study 002 draft
   with analytical predictions like Study 000's README.
8. **E5 Concordia cognition adapter** behind the observation firewall. Deps: none.
   Done when: a Concordia entity drives one EC agent through typed actions with the
   fake-LLM test pattern; pinned concordia version recorded.

## Later

9. **P1 ⛔ Publication decision on Study 000 findings** (defect + deconfound narrative is
   publishable methods work). Human decides venue/claims.
10. **E6 Ledger compression + DuckDB event views** once artifact volume hurts (not before).
11. **E7 MCP tool seam** design doc only (explicitly deferred in foundation).

## Dependencies snapshot

R1 → E1 → R2 → E2 → (M2 confirmatory run). E3→E4 independent of that chain. Nothing
blocks on E5–E7.
