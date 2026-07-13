# Architecture & Data-Modelling Stress Test — Option C Research Kernel

Role: adversarial architecture / data-modelling reviewer.
Scope: the lead's Option-C sketch (own deterministic kernel + optional legacy/Concordia adapters).
Date: 2026-07-13. Confidence tags: **[H]** high, **[M]** medium, **[L]** low / from-knowledge-not-verified.

Verdict up front: **Option C is correct and the only option that can deliver hash-verified deterministic
replay.** The sketch is sound but has **five latent correctness bugs** that will silently break
determinism or the "prefix byte-identical" branch guarantee if implemented as written. They are all
fixable now and cheap; fixing them after Study 000 has recorded ledgers is not. Details below, most
load-bearing first.

---

## 0. Evidence gathered (what is verified vs asserted)

Legacy engine inspected read-only at `.../scratchpad/legacy-npd`:

- **Global mutable RNG, seeded per run.** `npdl/simulation/runner.py:512-513` and `main.py:334-335`:
  `random.seed(run_number); np.random.seed(run_number)`. There is **no** per-component or per-agent
  stream isolation anywhere — a single process-global MT19937 is shared by network construction,
  agent exploration, rewiring, and tie-breaks. **[H]**
- **Dual RNG code paths.** `npdl/core/true_pairwise.py:20-40` defines a fake `np` shim when numpy is
  missing, so `np.random.*` resolves to *either* numpy's Mersenne Twister *or* the stdlib `random`
  module depending on the install. Same seed → different streams across environments. **[H]**
- **No typed schema layer.** `requirements.txt` has numpy/pandas/networkx/matplotlib/dash/pygame —
  **no pydantic, no jsonschema, no hashing, no event ledger.** Payoffs are Python floats
  (`get_pairwise_payoffs`, `true_pairwise.py:43-54`; `calculate_payoffs`, `environment.py:179-227`)
  and are averaged for learning (`round_avg_payoffs_for_learning`, `runner.py`/`environment.py`). **[H]**
- Network built with unseeded-relative-to-global `nx.random_regular_graph`, `random.choice`
  (`environment.py:80-156, 505-536`) — order-and-global-state dependent. **[H]**
- Clean, reusable pure function worth keeping as an **oracle**: `get_pairwise_payoffs(move1, move2,
  R,S,T,P)` (`true_pairwise.py:43-54`) and `calculate_payoffs` (`environment.py:179-227`).

Concordia (v2.0, the "Generative AI as a Game Engine" line, arXiv 2507.08892; repo
`google-deepmind/concordia`): Entity-Component; **GameMaster is itself an entity**; `Engine` is
`Sequential` or `Simultaneous`; action flow is typed via `ActionSpec.output_type ∈ {MAKE_OBSERVATION,
NEXT_ACTION_SPEC, RESOLVE, NEXT_GAME_MASTER}`; **resolution happens inside a GM component's
`pre_act()` that parses free-text LLM output**; checkpoint via component `get_state()/set_state()`.
This is verified from the repo CHEATSHEET/README and the v2.0 writeup. **[H for API shape; M for exact
current method signatures — pin to a commit before coding.]**

Python 3.14 / pydantic: pydantic **2.12+** with **pydantic-core 2.47+** ships CPython 3.14 wheels
(incl. 3.14t free-threaded). Pin `pydantic>=2.12`. **[H]**

---

## 1. Determinism hazards in Python (with prescriptions)

The determinism claim has a **scope trap** that must be stated in the design doc first, because it is
the difference between a true and a false claim:

> **Kernel replay is deterministic *given recorded agent actions*. Agent *cognition* (LLM sampling)
> is NOT reproducible and is out of the hash chain.** Replay replays the recorded typed action; it
> does not re-query the model.

If this line is not written down, the whole "identical hash chains" promise is false the moment an LLM
agent is in the loop. Everything below assumes it. **[H]**

### 1.1 Floats — do not hash them. Use integers / fixed-point.
- Legacy already shows the smell: float payoffs + averaging. Float arithmetic is deterministic on a
  single platform under IEEE-754 for `+ - * /` and `sqrt`, but **`sum()` order, `math.fsum`, numpy
  reductions, and any transcendental (`exp`, `log`, `**` non-integer) are platform/lib-version
  sensitive**, and float→text is a canonicalization minefield (see 1.4). **[H]**
- **Prescription:** all *scored* quantities (payoffs, budgets, reputation, evidence weights) are
  **integers in fixed-point** (e.g., store "milli-utils": 3.0 → `3000`). Do arithmetic in `int`.
  Convert to float only at the analysis/reporting boundary (DuckDB), never inside a hashed payload.
  If a mechanism genuinely needs a ratio (a threshold like "≥60%"), express it as an integer
  comparison `100*coop >= 60*total`, never `coop/total >= 0.6`. **[H]**
- Probabilistic *draws* (e.g., "cooperate w.p. p") are fine because the **outcome** (the chosen
  action) is recorded as an integer/enum, not the float. Keep `p` in the mechanism spec as a rational
  `{"num":6,"den":10}` or a fixed-point int, and compare against a uniform integer draw
  `rng_uint < num * (2^k // den)` — never against `rng.random() < 0.6`. **[H]**

### 1.2 Dict ordering / set iteration.
- Python dicts are insertion-ordered (stable) **[H]**, but **`set` iteration order is
  hash-randomized** for `str`/`bytes` unless `PYTHONHASHSEED` is fixed, and is arbitrary for other
  types. Legacy leans on `random.choice(list(set(...)))` patterns (`environment.py`), which is doubly
  order-dependent. **[H]**
- **Prescription:** ban `set` iteration in any ordered/scored path. Anywhere you iterate agents,
  claims, or actions, iterate a **`sorted()` list keyed on a stable integer ID**, never on a name or
  object identity. Add a lint/CI grep that fails on `for .* in .*set(` and on iterating a raw dict
  whose keys are strings in a resolution path. Do **not** rely on `PYTHONHASHSEED=0` as the fix — it
  is invisible and a single missed env var reintroduces nondeterminism. **[H]**

### 1.3 PRNG choice — reject MT19937; use a counter-based, splittable generator.
This is the single highest-leverage decision and it interacts with branching (§2).
- `random` (stdlib MT19937): algorithm is stable across CPython versions, **but the *methods* are
  not** — `random.shuffle`, `randbelow`, `choices` implementations have changed between minor
  versions (e.g., the 3.11 `randbelow` path). MT state is 2.5 KB and **cannot be fast-forwarded**;
  you must snapshot the whole state to checkpoint, and you cannot cheaply resume a stream at
  event N without replay. **[M]**
- numpy legacy `np.random.seed`/`RandomState`: also MT19937, global, deprecated for new code. **[H]**
- **Prescription:** use **`numpy.random.Generator(Philox(key=...))`** (or `PCG64`, but Philox is the
  right call). Philox is **counter-based**: its state is `(key, counter)`, so a stream can be
  positioned to any offset in O(1), snapshotted in ~40 bytes, and resumed after a branch without
  replay. numpy guarantees bit-stream stability for a pinned `Generator`+bit-generator across numpy
  versions (documented stream-compatibility policy). Pin numpy and record its version in run
  metadata. **[M — verify numpy's current stream-stability guarantee for Philox against the pinned
  version in a metamorphic test.]**
- Only draw **raw uint64s** from the generator (`rng.integers(0, 2**64, dtype=uint64)`), and build
  every higher-level primitive (uniform, choice, shuffle) yourself from those uints with an
  integer-only algorithm you own. This decouples you from numpy's *method* implementations (which may
  change) while keeping its *bit generator* (which is versioned). **[H]**

### 1.4 JSON canonicalization — the recipe (and its traps).
Python's `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)` is *close* to
canonical **within one pinned interpreter** but has four traps:
1. **NaN / ±Infinity:** `json` emits bare `NaN`/`Infinity` (invalid JSON) by default. **Set
   `allow_nan=False`** so it raises. Combined with §1.1 (no floats in payloads) this can't fire, but
   set it as a belt. **[H]**
2. **`-0.0`:** serializes as `"-0.0"` and hashes differently from `"0.0"`. Another reason floats
   never enter payloads. If one ever must, normalize `x + 0.0` and reject non-finite. **[H]**
3. **Unicode / key sort order:** `sort_keys` sorts by Unicode **code point**; RFC 8785 (JCS) sorts by
   UTF-16 code unit — these differ for astral-plane (>U+FFFF) characters. Also, unnormalized Unicode
   (NFC vs NFD) hashes differently. **Prescription:** **NFC-normalize all strings on ingest**,
   restrict payload *keys* to ASCII identifiers (enforce in pydantic with a key pattern), and you
   avoid the JCS/codepoint divergence entirely. If you ever need cross-language canonicalization, use
   a real **RFC 8785 JCS** library rather than `json.dumps`. **[H]**
4. **Integer bounds & bytes:** JSON has no native int64 guarantee across parsers and no bytes type.
   Keep integers within int64, and encode any binary (hashes) as lowercase hex strings. **[H]**
- **Recommended canonical form:** define ONE function `canon(obj) -> bytes`:
  `json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=True, allow_nan=False)
  .encode("ascii")`. Use `ensure_ascii=True` (not False) so the *byte* output is independent of the
  reader's encoding and astral chars become `\uXXXX` escapes — this sidesteps the UTF-16 sort issue
  for *values* too. Forbid floats/NaN by schema. Freeze this function; never "improve" it (any change
  is a hard fork of every ledger). Add a golden-vector test with tricky inputs (emoji, `-0`, nested,
  key-order permutations). **[H]**

### 1.5 Hash-chain design flaws (see also §2).
- **Domain separation.** sha256 is used for the event hash, the seed derivation, checkpoint hashes,
  spec/mechanism/skin hashes — all in one codebase. Without a per-use domain tag, a payload could in
  principle be crafted to equal a seed-derivation preimage, and more practically, refactors can
  cross-wire the uses. **Prescription:** every hash input is prefixed with a versioned ASCII tag +
  `\0`: `b"chl.event.v1\0"`, `b"chl.seed.v1\0"`, `b"chl.ckpt.v1\0"`, `b"chl.mech.v1\0"`,
  `b"chl.skin.v1\0"`. **[H]**
- **Exactly what `event_hash` covers.** `event_hash = sha256(b"chl.event.v1\0" ||
  canon({schema_version, study_id?, run_id?, seq, logical_time, actor, event_type, payload,
  parent_event_hash}))`. It covers `parent_event_hash` (that's what makes it a chain) and **excludes
  itself and all unhashed metadata**. Genesis: `parent_event_hash = sha256(b"chl.genesis.v1\0" ||
  mechanism_hash)` so the chain is bound to the compiled mechanism. **[H]**
- **length-extension / second-preimage:** not a threat here (this is research integrity, not an
  adversary) — plain sha256 over canonical JSON of a fixed struct is fine. Do **not** hash by
  string-concatenating fields without a canonical encoder (that's the §2.2 bug). **[H]**

---

## 2. Event-sourcing design

### 2.1 Payload (hashed) vs metadata (unhashed) — the causal test.
Rule: **a field is hashed iff replay's output depends on it.** Concretely:

- **Hashed payload:** the actor's chosen typed action; resolved outcomes; scored deltas (integers);
  seed-stream identity used; institution decisions; config/mechanism hash the event was produced
  under; logical_time; seq; actor id.
- **Unhashed metadata (side channel):** wall-clock timestamps, latency, host, process id, log level,
  cost, token counts, **and for LLM agents: the raw prompt and raw completion text, model id,
  temperature, provider**. These are audit-critical but **causally irrelevant to kernel replay**
  because replay consumes the *recorded action*, not the model. Storing model id here (not in the
  hash) is deliberate: it lets you audit "which model produced this" without making the mechanism
  hash depend on a model version. **[H]**
- **Trap:** it is tempting to hash the LLM prompt/response "for integrity." Do **not** — it makes the
  chain unreproducible (LLM nondeterminism) and couples mechanism identity to prompt wording (a §3
  narrative leak). Keep a *separate* transcript store, content-addressed, referenced by hash from the
  metadata, so audit is possible without polluting the mechanism chain. **[H]**

### 2.2 **BUG: the seed-derivation concatenation is ambiguous (canonicalization defect).**
`sha256(study_seed || condition || replicate || scenario || agent || component)` with plain
concatenation is a classic collision bug: `("ab","c")` and `("a","bc")` hash identically. Two distinct
(agent, component) pairs can collide → **shared PRNG streams → silent correlation between agents that
should be independent.** Severity: high; it corrupts the science, not just an ID. **[H]**
- **Prescription (labeled HKDF-style derivation, length-unambiguous):**
  ```
  root = sha256(b"chl.seed.v1\0" || canon({"study_seed": study_seed}))
  def derive(parent32, label, index):   # label ∈ {"condition","replicate","scenario","agent","component"}
      return sha256(b"chl.seed.v1\0" || parent32 || u8(len(label)) || label.encode()
                    || u32be(index))
  key = derive(derive(derive(root,"condition",c),"replicate",r), ...)   # chain per plane
  ```
  Then `Philox(key=int.from_bytes(key32,"big") & MASK128)` (or feed the full 256 bits as the Philox
  key + counter=0). Because each level is fixed-width/length-prefixed, no two identity tuples collide.
  Derivation is **by identity, not by draw order** — adding a 4th agent does not perturb agents 0–2's
  streams. That is the property legacy's global RNG fundamentally cannot provide. **[H]**

### 2.3 Cheap replay verification.
- The chain head hash is already a Merkle-chain accumulator. **To verify a whole run: recompute the
  chain and compare only the final head hash (32-byte compare).** O(n) compute, O(1) trust decision.
  Record `{head_hash, event_count, mechanism_hash}` in the sealed manifest; verification = replay →
  compare head. **[H]**
- For **segment/branch** verification without full replay, write a **checkpoint every K events** that
  records the head hash at that seq. Then any segment `[i, j]` is verifiable from checkpoint `i`'s
  head. A full Merkle *tree* (O(log n) inclusion proofs) is overkill at research scale — a chain +
  periodic checkpoints is enough. **[M]**

### 2.4 Checkpoint format — must capture ALL mutable state.
`checkpoint = { seq, head_event_hash, logical_time, world_state, institution_state,
per_agent_internal_state, per_stream_rng_positions:[{stream_id,(key,counter)}], metric_accumulators }`,
content-hashed with `b"chl.ckpt.v1\0"`, and a `checkpoint` **event** is appended to the ledger
carrying only the checkpoint hash (keeps the chain the single source of truth). **[H]**
- **The checkpoint is only correct if there is zero mutable state outside it.** Legacy fails this
  (module-global RNG, `agent.score` mutated in place). **Prescription:** the kernel forbids
  module-level mutable state; all state is reachable from the checkpoint object. Enforce with a
  smoke test: `checkpoint → drop process → resume → run M more events → head hash equals
  no-checkpoint run's head hash`. If that test passes, the checkpoint is complete; if it can't be
  made to pass, there is hidden global state. **[H]**
- Counter-based RNG (§1.3) makes RNG checkpointing ~40 bytes/stream and makes resume exact; MT19937
  would force a 2.5 KB/stream blob and still couples to method-version stability. Concrete reason to
  pick Philox. **[H]**

### 2.5 **BUG: branching vs "prefix byte-identical" conflicts with run_id in the envelope.**
The envelope includes `run_id`. If a branch is a *new* run with a new `run_id`, then every event's
canonical bytes differ from the parent's even where the events are logically identical → the promised
"prefix byte-identical" is **impossible** as specified. **[H]**
- **Prescription — structural sharing + derived run identity:**
  1. Storage: a branch does **not** copy the prefix; it stores a pointer `{forked_from: run_R, at_seq:
     N}` plus only its post-N events. The prefix *bytes* are literally the parent's bytes (COW), so
     "prefix byte-identical" is true by construction. **[H]**
  2. Identity: make `run_id` a **derived** value, not a random UUID — `run_id = sha256(b"chl.run.v1\0"
     || mechanism_hash || seed_root || branch_lineage)`. Two runs with identical mechanism+seed get
     the same run_id, so replay reproduces it; a branch's lineage differs only *after* N. If you want
     the hashed envelope to be branch-agnostic before N, **move `run_id` and `study_id` OUT of the
     hashed envelope into metadata** and bind the run identity via the genesis parent hash instead
     (§1.5). Then identical prefixes hash identically regardless of run_id. Pick one of these two;
     both make the guarantee real. Recommend (1)+(genesis-binding). **[H]**

### 2.6 Branch + seed re-derivation.
Because seeds are derived **by identity** (§2.2), a branch that overrides config at event N:
- Streams whose identity inputs are unchanged by the override keep the **same (key, counter)** and
  therefore replay identical draws up to and beyond N (divergence comes only from the changed
  mechanism consuming them differently). **[H]**
- The branch resumes each stream from the **checkpoint's recorded (key, counter)** at seq N — no
  replay-from-genesis needed. Streams introduced by the override (e.g., a new institution's RNG) are
  freshly derived from their identity. **This is clean only with counter-based RNG.** With MT19937 you
  would have to snapshot/restore full state per stream and could not reason about "same draws." **[H]**
- **Do not re-seed globally on branch** (legacy's `random.seed(run_number)` model). Re-derive per
  stream by identity. **[H]**

---

## 3. Mechanism-hash vs narrative-hash — exact field assignment

Compile-time split. `mechanism_hash = sha256(b"chl.mech.v1\0" || canon(MechanismSpec))`,
`skin_hash = sha256(b"chl.skin.v1\0" || canon(NarrativeSkin))`. **Invariant to test: permuting/
replacing the entire NarrativeSkin must not change `mechanism_hash` and must not change any
event/head hash of a fixed-action replay.** Make that a property test. **[H]**

**Into `mechanism_hash` (the numbers):**
- world dynamics params & update rule id; payoff/scoring function + integer coefficients (R,S,T,P as
  ints); interaction topology + partner-selection rule; information/observation *policy* (what fields
  are revealed to whom, as field-ids); institution rules (constrain + react logic ids + integer
  thresholds); action-space definition (the discriminated-union tags + typed field schema);
  seed-derivation labels & study_seed; episode length; agent **policy types / hyperparameters** (e.g.
  "TFT", epsilon as fixed-point) — but **not** prompt wording.

**Into `skin_hash` only (never mechanism):**
- entity display names; flavor/premise/story text; prompt phrasings and system-prompt wording;
  observation *surface strings* (the English rendering of an observation whose *structure* is in the
  mechanism); UI labels; ordering-irrelevant cosmetic metadata.

**Where narrative leaks into mechanics (the usual six):**
1. **Display name as a dict key or sort key** → ordering/tie-breaks depend on skin. *Fix:* mechanism
   operates only on stable integer IDs; names are a render-time lookup. **[H]**
2. **Parsing free-text agent output to decide the action** (Concordia's whole model). The *words* are
   skin; the *canonical action* is mechanism. *Fix:* an explicit, mechanism-owned `parse(text) ->
   ActionUnion | Invalid` mapping; the parser and its enum are mechanism, the surface phrases are
   skin. Record the canonical action in the payload, the raw text in metadata. **[H]**
3. **Prompts that embed authoritative numbers** ("you need 3 points to pass"). If the `3` is also the
   mechanism threshold, you now have two sources of truth. *Fix:* single source — the skin *renders*
   the number from the mechanism spec; the number is never read back from the prompt. **[H]**
4. **RNG seeded from a name/string hash** → changing a display name changes draws. *Fix:* seeds
   derive only from integer identities (§2.2), never from skin strings. **[H]**
5. **Observation policy branching on narrative framing** (revealing different info depending on the
   story). *Fix:* observation policy is mechanism, keyed on field-ids; skin only styles the reveal.
   **[H]**
6. **String tie-breaks** ("sort agents alphabetically"). *Fix:* tie-break on integer id. **[H]**

Design stance: **the skin is a pure function `render(mechanism_state) -> text` that is never read
back into the mechanism.** If a value flows skin→mechanism, it is a bug by definition. Add an
import/dataflow lint so the mechanism package cannot import the skin package. **[H]**

---

## 4. Five-plane model — where composition creaks, and the interface fix

The five planes (world / information / interaction / institution / cognition) are **not a clean
layered stack** — institution both reads world ground truth and gates/reacts to actions, and
observation needs both world and institution state. Naive composition produces circular reads and
order-dependent mutation. Prescribe **read-models + two-phase institution + a hard observation
firewall.** **[H]**

- **World internals needed by institution.** An institution rule like "sanction a false report" must
  know whether a claim was actually false → institution needs **ground truth**. *Boundary:* expose a
  read-only `WorldView` (and `EvidenceView`) to institutions; **only the world-update step writes
  world state.** Institutions never mutate world; they emit institutional events that the world-update
  consumes next tick or same tick in a defined order. **[H]**
- **Observation needs institution state.** Reputation/sanctions are institution-owned but often
  observable. *Boundary:* `observe(agent, WorldView, InstitutionView, InformationPolicy) ->
  Observation` is a **pure function** reading both read-models; the InformationPolicy (mechanism)
  decides which fields cross. **[H]**
- **Cognition firewall (the core scientific guarantee).** Cognition/agents see **only `Observation`
  objects**, never `WorldView`/`InstitutionView`/scored internals. This single boundary is what keeps
  "scored world variables out of generative hands" (§5). Enforce by construction: the agent interface
  is `act(Observation) -> ActionProposal`; it has no other arguments and no access to kernel objects.
  **[H]**
- **Interaction plane owns ordering.** Who-acts-with-whom and turn order must be **deterministic and
  integer-keyed** (sorted ids), not dict/set order (§1.2). **[H]**
- **Two-phase institution (resolves the read/react circularity).** Split institution into:
  `constrain(proposals, views) -> admissible_proposals` (pre-resolution: legality, budgets, gating)
  and `react(resolved_outcomes, views) -> sanctions/events` (post-resolution). This breaks the
  "institution needs both pre- and post- state" knot and makes the episode loop a straight line. **[H]**
- **Simultaneous resolution against a frozen snapshot.** If actions resolve simultaneously, resolve
  every action against a **frozen pre-action `WorldView`**, then apply all deltas, to kill
  intra-tick order dependence. Make sequential-vs-simultaneous an explicit mechanism field. **[H]**

**Refined episode loop (drop-in for the sketch):**
`freeze views → observe (info policy) → agents propose typed actions → validate (schema + legality) →
institution.constrain → resolve deterministically vs frozen snapshot → world/evidence update →
institution.react → append events → online metrics → maybe checkpoint → (loop) → seal`. The sketch's
loop is right; the additions are the frozen snapshot, the constrain/react split, and validate-before-
constrain. **[H]**

---

## 5. Concordia adapter seam

Concordia's architecture (verified §0): Entity-Component; **GameMaster is an entity that resolves the
world by having an LLM read free text in `pre_act()`**; engines `Sequential`/`Simultaneous`;
`ActionSpec.output_type` routes MAKE_OBSERVATION / NEXT_ACTION_SPEC / RESOLVE / NEXT_GAME_MASTER;
checkpoint via component `get_state()/set_state()`. **[H API shape; M exact signatures — pin a commit.]**

**The fundamental mismatch:** Concordia's **scored/world truth lives in natural language and is
adjudicated by an LLM**. That is nondeterministic, unhashable, and puts scored variables directly in
generative hands — the exact opposite of this kernel. Therefore **never** let Concordia's GameMaster
resolve, score, or own world state. **[H]**

**Narrowest sane adapter boundary:** use Concordia **only as a cognition provider behind the §4
observation firewall.**
- Adapter = `ConcordiaCognitionAdapter(Observation) -> ActionProposal`. It wraps a Concordia
  `Entity`/`EntityAgentWithLogging`: our `Observation` is rendered (via the NarrativeSkin) into the
  text Concordia expects; Concordia's `entity.act(action_spec)` returns free text; our
  **mechanism-owned `parse()`** (§3 leak #2) maps that text to a typed `ActionUnion`. Only the typed
  action crosses back into the kernel. **[H]**
- **Do not use Concordia's GameMaster/engine at all** in the deterministic path. If you want its GM
  for *flavor*, use it strictly as a **skin renderer** (observation text generation) fed *from our
  authoritative state*, hash-excluded, never read back. **[H]**
- Concordia's LLM prompt/response goes to the **unhashed transcript store** (§2.1). The kernel's
  determinism holds because it replays the recorded typed action, not Concordia. **[H]**
- Keep the adapter in `chl/adapters/concordia/` with a dependency on the kernel's public
  `Observation`/`ActionProposal` types only, and **no kernel dependency on Concordia** (import
  direction inward). Pin Concordia to a commit; its v2.0 API is young and moving. **[H]**

Net: Concordia is a **cognition/skin plug-in**, not a substrate. This preserves the whole value of
Option C while letting you borrow generative agents when a study wants them.

---

## 6. Python 3.14 specifics

- **pydantic:** use **`pydantic>=2.12`** (pydantic-core ≥2.47 ships 3.14 wheels, incl. 3.14t). Do not
  use `pydantic.v1` (unsupported on 3.14). **[H]**
- **PEP 649/749 deferred annotations are the default in 3.14** — annotations are lazily evaluated.
  pydantic 2.12 is built for this, but **third-party models and `from __future__ import annotations`
  interactions can surprise**; add a CI job that imports every model and calls
  `model_rebuild()` / `TypeAdapter` on startup to force resolution and fail fast. **[M]**
- **Pydantic serialization stability is NOT a hashing guarantee.** `model_dump(mode="json")` field
  order, enum/`Decimal`/`datetime` rendering, and `None`-omission can shift across minor pydantic
  versions. **Do not hash `model_dump` output.** Validate with pydantic, then hand a plain
  `dict`/list to your frozen `canon()` (§1.4) and hash that. Pin pydantic and add a golden-hash test
  so a pydantic bump that would change bytes fails CI. **[H]**
- **`hashlib`:** sha256 stable; pass `usedforsecurity=False` (available since 3.9) on the research
  hashes if you want to signal intent (does not change digest). **[H]**
- **`random`:** stdlib method implementations are not version-locked (§1.3) — another reason to own
  your primitives over a pinned bit generator. **[H]**
- **`dataclasses`:** no relevant behavioral change in 3.14; fine for internal non-validated structs.
  Prefer pydantic for anything that is hashed/serialized (schema enforcement). **[L]**
- **Free-threading (3.14t):** **irrelevant and mildly hazardous here.** The kernel is single-threaded
  and deterministic; use the **standard GIL build**, not `python3.14t`. C-extension wheels (numpy,
  duckdb, pydantic-core) exist for 3.14t but the ecosystem is less battle-tested; determinism is
  unaffected by the choice, so pick the boring build. If you later parallelize *replicates*, do it
  with **processes** (each its own seed lineage), not free threads. **[H]**
- **DuckDB/Parquet:** analysis-only, downstream of the ledger; float rounding there is fine because it
  never re-enters a hash. Keep the ledger (Parquet/JSONL) the source of truth; DuckDB is a view. **[H]**

---

## 7. Verdict: A vs B vs C

**Option A — build on legacy `npdl`: NO (as kernel).** Disqualifiers, all verified: process-global
mutable RNG seeded per-run (`runner.py:512-513`, `main.py:334-335`) — cannot provide per-component
stream isolation, cannot support identity-keyed seeds or cheap branch resume; dual numpy/stdlib RNG
paths (`true_pairwise.py:20-40`) — same seed → different streams across installs; no typed schemas, no
ledger, no hashing, float payoffs. Retrofitting determinism into this is a rewrite, not an adoption.
**Keep legacy in exactly two roles:** (a) a **reference payoff/dynamics oracle** — `get_pairwise_
payoffs` and `calculate_payoffs` are clean pure functions, wrap them behind `chl/adapters/legacy/` and
call them as an external oracle in **Study 000 metamorphic tests** (kernel result == legacy result on
matched inputs); (b) behavioral fixtures. Never import legacy RNG-coupled code into the kernel. **[H]**

**Option B — build on Concordia: NO (as kernel/scoring substrate).** Concordia resolves and scores the
world via LLM free-text adjudication (`GameMaster.pre_act`) — nondeterministic, unhashable, scored
variables in generative hands. Adopting it as substrate makes hash-verified replay impossible. **Use
it as a cognition/skin adapter behind the observation firewall (§5), pinned to a commit.** **[H]**

**Option C — own deterministic kernel + adapters: YES. Recommended.** It is the only option that
delivers integer-scored, seed-isolated, hash-verified deterministic replay with branch-prefix
identity, while still letting you (a) cross-check against legacy as an oracle and (b) drop in Concordia
generative agents when a study calls for them. The adapters are what make C strictly dominate A and B
rather than throwing their value away. **[H]**

### Repo-layout adjustments (only the ones that concretely help)

The lead's task breakdown (kernel / domain / engine / agents / metrics / CLI) is already the right
spine. Two concrete additions:

1. **Adapters live outside the deterministic core with inward-only deps:**
   `chl/kernel/` (seeds, `canon`, hashing, ledger, stores, checkpoint — the trust root, imports
   nothing domain-specific) → `chl/domain/` (five-plane ScenarioSpec, MechanismSpec, NarrativeSkin,
   ActionUnion, evidence/claims) → `chl/engine/` (runner, replay, branch, observe, validate, resolve)
   → `chl/agents/` (scripted policies, LLM adapter, fake provider) → `chl/adapters/{legacy,concordia}/`
   (oracle + cognition). `chl/analysis/` (DuckDB/Parquet) hangs off the ledger only.
2. **Enforce the import direction and the mechanism/skin firewall with `import-linter` in CI:** rules
   = `kernel` may not import `domain|engine|agents|adapters`; `mechanism`/domain-mechanism may not
   import `skin`; `agents`/`adapters` may not import `kernel` internals (only public types).
   This turns the §3/§4 firewalls from prose into a failing build. Cheapest layer that actually
   enforces the invariant (per the CLAUDE.md enforcement-ladder rule). **[H]**

Plus the frozen, tested singletons the whole design rests on: **`canon()`** (golden-vector test),
**`derive_seed()`** (collision/length-prefix test), the **checkpoint-completeness** smoke test, and
the **skin-invariance** property test. Write those four tests before Study 000 records any ledger.

---

## Residual risk / NOT verified

- Exact current Concordia method signatures (`act`/`pre_act`/`ActionSpec` fields) — read from
  CHEATSHEET/README, **not** run against a pinned checkout. Pin a commit and confirm before coding the
  adapter. **[M]**
- numpy's Philox bit-stream stability across the specific pinned numpy version — asserted from numpy's
  documented policy, **not** empirically re-tested here. Add a metamorphic golden-stream test. **[M]**
- pydantic 2.12 + PEP 649 edge cases with forward refs in the five-plane recursive specs — assert
  early `model_rebuild()` in CI. **[M]**
- Legacy behavioral equivalence (whether the oracle reproduces the *paper's* numbers) is a different
  discovery agent's charge (payoff/math verification); this review only certifies the legacy code is
  unfit as a *kernel*, and that its pure payoff functions are safe to reuse *as an oracle*. **[H]**
