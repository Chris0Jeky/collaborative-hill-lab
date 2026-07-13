# Cost worksheet — Study 001 (no fabricated prices)

This worksheet contains MEASURED quantities and FORMULAS only. Per-token prices change and
must be read from the provider's pricing page on the day of the decision; the founding agent
recorded none, deliberately (locked principle: never fabricate cost data).

## Measured quantities (scripted fixture, official-briefing skin, 2026-07-13)

From a full 12-round, 3-agent episode (attr-ledger condition), rendering every observation
through `agents/llm/rendering.py`:

- prompts per episode: **36** (3 agents × 12 rounds)
- prompt size: min 2,099 / mean 2,524 / max 3,094 characters
- total prompt characters per episode: **90,865**

Rule-of-thumb conversion (≈4 chars/token for English; VERIFY with the provider's tokenizer):
- input tokens per episode ≈ **23,000** (plus system prompt overhead × 36 calls)
- output tokens per episode: bounded by the JSON action format; budget ≈ 100–200 tokens/call
  → ≈ **3,600–7,200** per episode
- retries multiply both: with max_retries=1, worst case ×2.

## Formula

For E episodes per cell, 4 cells (+1 exploratory arm), R retry factor (1.0–2.0):

    input_tokens_total  ≈ 5 cells × E × 23,000 × R  (+ system prompt × 36 × 5E calls)
    output_tokens_total ≈ 5 cells × E × 5,400 × R

    cost = input_tokens_total × price_in + output_tokens_total × price_out

Fill `price_in`/`price_out` from the provider pricing page (record page URL, price, and
access date in this file when doing so). Then check against the HUMAN cost ceiling
(PREREGISTRATION §11) before freezing.

## Worked example structure (prices intentionally blank)

| item | value |
|---|---|
| episodes per cell (E) | HUMAN (post-pilot) |
| retry factor (R) | from pilot |
| price_in ($/Mtok) | ____ (source URL + date: ____) |
| price_out ($/Mtok) | ____ (source URL + date: ____) |
| estimated total | computed, not guessed |

Pilot (5 episodes/cell) uses the same formula with E=5 and must be re-measured: pilot
manifests record real token counts when the provider returns them; those replace the
character-based estimates above for the full-run decision.
