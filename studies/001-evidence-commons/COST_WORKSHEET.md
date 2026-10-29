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
- The historical one-repair assumption (`max_retries=1`) allows at most two completion
  calls per decision when transport retries are disabled. Current provider configuration
  separately controls action-format repair completions (`max_retries`) and HTTP 429 request
  retries (`rate_limit_retries`); both default to zero for the real transport. Count both
  when estimating usage. A request-count bound is not an exact token/cost multiplier:
  repair prompts differ, and a failed request's usage or charges can remain unknown.

## Formula

For E episodes per cell, 4 cells (+1 exploratory arm), and a pilot-estimated retry factor R
under the declared settings (the historical 1.0–2.0 assumption is not a general bound):

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
