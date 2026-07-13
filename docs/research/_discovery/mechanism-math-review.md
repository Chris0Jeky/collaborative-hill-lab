# Mechanism & Mathematics Review — Legacy N-IPD (Pairwise vs Neighbourhood)

Reviewer role: Game-theoretic mechanism and mathematics reviewer.
Date: 2026-07-13. Confidence levels are stated per claim. All payoff claims below were
re-derived by hand **and** confirmed by a fresh numeric enumeration (script output embedded).

Legacy clone (READ-ONLY) root:
`.../scratchpad/legacy-npd` (abbreviated `LEGACY/` below).

> **Headline for the lead engineer:** The legacy repo contains **three independent, mutually
> inconsistent implementations** of the same game. The paper is a *literature review with no
> formulas or parameters* — it is NOT the source of ground truth. Ground truth for the model is
> the code, and the code disagrees with itself in two material ways (TFT semantics in pairwise
> mode; the cooperation-ratio denominator used by pTFT). Both must be resolved by an explicit
> spec + analytical oracle in the new implementation. The core scientific claim (pairwise
> sustains, neighbourhood collapses) is **mathematically sound and reproduces cleanly** — the
> risk is entirely in implementation drift, not in the theory.

---

## 1. The paper: what it actually is, and what it defines

**File:** `LEGACY/Paper Resources/Cooperation in N-Person Iterated Prisoner's Dilemma_ Pairwise
vs Group Interaction Structures – A Li.pdf` (7 pages, extracted via PyMuPDF).

**Critical finding (confidence: high):** This document is a **literature review** ("– A
Literature Review", p.1 title), organized into 4 themes. **It contains no game-theoretic
formulas, no payoff parameter values, no experiment specification, no algorithm, and no
results.** Any downstream doc that cites "the paper's payoff formula" or "the paper's
parameters" is over-claiming; those live only in code. Treat the PDF as *motivation and
terminology*, not as a spec.

### 1.1 Definitions the paper does give (conceptual, verbatim anchors)

- **N-person social dilemma / N-IPD** (p.1): "all individuals would benefit if everyone
  cooperates, but each has an incentive to defect for personal gain." Multi-player extension of
  PD; underlies tragedy of the commons (Hardin 1968).
- **"Neighbourhood model"** (p.4, "What is novel"): "*group payoff based on a single joint
  decision*" — the paper explicitly equates this to "an N-person Prisoner's Dilemma or a Public
  Goods Game (with linear payoff, each cooperation contributes to a common pool)" and to
  "well-mixed group reciprocity." So neighbourhood = aggregate/linear-PGG payoff off one action
  per agent.
- **"Pairwise model"** (p.4): "*a form of networked reciprocity where every pair of individuals
  has an independent game (effectively a complete graph of bilateral interactions if everyone
  interacts with everyone)*." So pairwise = decompose the N-set into a web of independent
  2-player IPDs.
- **TFT** (p.2): classic bilateral reciprocity, "if you defect on me, I defect on you next
  time"; relies on "clear bilateral feedback."
- **Group-average / probabilistic TFT** (p.2–3): the paper names "cooperating with probability
  equal to the last round's cooperation rate" as the natural group generalization and asserts it
  **fails**: "too lenient when defection is moderate and too harsh when one defection occurs
  (since one defector can spoil the average)." This is exactly the legacy `pTFT` / neighbourhood
  TFT. **The paper predicts its collapse a priori** (confidence: high this is the intended
  mechanism).
- **"Three is a crowd"** (p.2): Grujić et al. (2012) — dyadic >80% cooperation, adding one player
  makes cooperation falter. This is the empirical anchor for the 3-person focus.
- **Tragedy Valley vs Collaborative Hill** (p.5): the paper flags these as "the authors'
  metaphors to describe the regions of parameter space with low vs high cooperation."

### 1.2 Strategy designs the paper surveys (Theme 3) — not implemented as the primary variant
AoN / All-or-None (reduces to Win-Stay-Lose-Shift/Pavlov in 2-player); quorum/threshold
("cooperate if ≥ M of N"); GTFT (generous), Contrite TFT, Tit-for-two-tats. **Design note:** the
legacy `pTFT-Threshold` (cooperate iff coop-proportion ≥ 0.5) is the code's realization of the
Theme-3 "quorum/threshold" idea, and the paper's AoN (unanimity rule) is *not* implemented in the
primary static experiments — a gap if the new lab wants paper-faithful strategy coverage.

### 1.3 There is no "ecosystem-aware TFT" in the paper
The term **"ecosystem-aware TFT" is a legacy-code coinage, not from the paper** (confidence:
high). See §4.3. The paper's vocabulary is "group-average / probabilistic TFT" and
"threshold/quorum" strategies.

---

## 2. Analytical oracle: all 8 profiles for N=3, both modes

**Parameters (ground truth from code, identical across every implementation checked):**
`R=3, S=0, T=5, P=1` — i.e. `(T,R,P,S) = (5,3,1,0)`.
Sources: `LEGACY/npdl/core/utils.py:6-37,194-197`; `LEGACY/.../npd_simulator/core/models/
payoff_matrix.py:21-25`; `LEGACY/code_for_website/static_figure_generator/
static_figure_generator.py:15-19`.

Action encoding across code: **C=0, D=1** (note: 0 is Cooperate — a foot-gun for the new impl).

### 2.1 Pairwise payoff (sum of two 2-player PD games)

Each agent plays an independent 2-player PD against each of the other two, and receives the
**sum** (`static_figure_generator.py:126-128` sums `round_payoffs`; `npdl` sums into `score`,
`environment.py:345`). 2-player matrix (payoff to row player):

```
             opp C   opp D
   me C        R=3     S=0
   me D        T=5     P=1
```

Agent i's pairwise per-round payoff: `u_i^pw = Σ_{j≠i} PD(a_i, a_j)`.

### 2.2 Neighbourhood payoff (linear / public-goods)

One action per agent; payoff depends on number of *other* cooperators `k ∈ {0,…,N-1}`
(`static_figure_generator.py:22-28`, `npdl/core/utils.py:20,37`, `payoff_matrix.py:46-72`):

```
  U_C(k) = S + (R−S)·k/(N−1) = 0 + 3·k/2          (cooperator)
  U_D(k) = P + (T−P)·k/(N−1) = 1 + 4·k/2 = 1+2k   (defector)
```
For N=3: k/(N−1)=k/2.

### 2.3 The full oracle table (hand-derived; numerically confirmed)

Numeric enumeration (my script, seed-free, exact) reproduced the hand algebra exactly:

```
profile |  PAIRWISE (sum of 2 games)         | NEIGHBOURHOOD (linear)
A0A1A2  |  u0    u1    u2    sum             | u0   u1   u2   sum
CCC     |  6     6     6     18             | 3.0  3.0  3.0  9.0
CCD     |  3     3     10    16             | 1.5  1.5  5.0  8.0
CDC     |  3     10    3     16             | 1.5  5.0  1.5  8.0
CDD     |  0     6     6     12             | 0.0  3.0  3.0  6.0
DCC     |  10    3     3     16             | 5.0  1.5  1.5  8.0
DCD     |  6     0     6     12             | 3.0  0.0  3.0  6.0
DDC     |  6     6     0     12             | 3.0  3.0  0.0  6.0
DDD     |  2     2     2     6              | 1.0  1.0  1.0  3.0
```

Worked examples (algebra):
- **Pairwise, profile DCC** (agent0=D, others C): u0 = PD(D,C)+PD(D,C) = 5+5 = **10**; u1 =
  PD(C,D)+PD(C,C) = 0+3 = **3**; u2 = 3. Single defector among cooperators earns 10 (double
  temptation), suckers earn 3 (one R from each other, S from the defector). ✔
- **Neighbourhood, profile DCC**: agent0 defects with k=2 others cooperating → U_D(2)=1+2·2=**5.0**;
  each cooperator has k=1 (one other C) → U_C(1)=1.5. ✔
- **Consistency at the corners:** both modes agree that a lone defector beats a lone cooperator
  by the *shape* of PD, but the pairwise numbers are exactly `(N-1)=2×` a single 2-player game
  because payoffs are summed, whereas neighbourhood is *normalized* to a single game's scale.
  **This scale difference (factor N−1) is real and matters** — see §4.1.

---

## 3. Core theoretical claim: why pairwise sustains and neighbourhood collapses

Claim under test (Chris's thesis): *targeted pairwise reciprocity sustains cooperation; diffuse
aggregate reciprocity collapses to a "tragic valley."* Canonical stress test: **2 TFT + 1 AllD,
N=3.** I derive the mechanism formally, then confirm by simulation.

### 3.1 The strategies as implemented (this is where the two mechanisms diverge)

- **Pairwise TFT** (`static_figure_generator.py:43-47`, `npd_simulator/.../final_agents.py:
  40-45`): keeps a **per-opponent** memory `opponent_last_moves[opponent_id]` and copies *that
  specific opponent's* last move. Retaliation is **targeted**: defect only against the partner
  who defected on you.
- **Neighbourhood TFT = probabilistic pTFT** (`static_figure_generator.py:58-66`,
  `final_agents.py:54-66`): cooperates in round r with **probability equal to the previous-round
  group cooperation ratio**. Retaliation is **diffuse**: a defection anywhere lowers the single
  scalar signal that governs your action toward *everyone*, and you cannot tell who defected.

### 3.2 Pairwise mechanism — cooperation is preserved on reciprocating links

Decompose into the three edges {0-1, 0-2, 1-2}, agents 0,1 = TFT, agent 2 = AllD.
- **Edge 0-1 (TFT–TFT):** both start C; each copies the other's last move; (C,C) is an
  **absorbing state** — mutual cooperation persists forever, each earning R=3/round on this edge.
- **Edges 0-2, 1-2 (TFT–AllD):** AllD defects always; TFT cooperates round 1 (eats S=0), then
  copies D forever → locks to (D,D)=P=1/round. TFT loses exactly one sucker payoff, once.

Steady state per round: each TFT earns 3 (from the other TFT) + 1 (from AllD) = **4**; AllD earns
1+1 = **2**. **The defector is quarantined to its own edges; it cannot touch the 0-1 cooperative
relationship.** This is the "targeted punishment" — retaliation is local to the defecting
relationship, so cooperation between the two reciprocators is a stable equilibrium.

Note also **T + S < 2R** (5+0 < 6): mutual cooperation Pareto-dominates alternating exploitation
on a link, so TFT-TFT has no incentive to break the (C,C) absorbing state. ✔

### 3.3 Neighbourhood mechanism — cooperation decays geometrically to zero (the valley)

The two pTFT agents' cooperation probability in round r equals the previous-round group
cooperation ratio `q_{r-1}` (denominator = N; see §4.2). The single AllD contributes 0. Take
expectations over the pTFT coin flips:

```
E[# cooperators in round r] = 2·q_{r-1} + 0   ⇒   q_r = (2·q_{r-1})/3.
```

This is a **linear contraction with ratio 2/3 < 1**, so `q_r = (2/3)^r · q_0 → 0`. The unique
fixed point is **q* = 0 (universal defection)**. With q_0 = 2/3 after round 1 (both TFT
cooperate, AllD defects), cooperation extinguishes as `(2/3)^{r+1}`. **The lone defector poisons
the shared signal that both reciprocators depend on; because pTFT cannot target, it punishes the
*other cooperator* just as hard as the defector.** That is the "diffuse punishment → Tragic
Valley" mechanism, and it is exactly the failure the paper predicts on p.2–3.

General form (m reciprocators + 1 AllD, group size N=m+1): contraction ratio = m/(m+1) < 1 →
always collapses. The valley is generic, not a knife-edge.

### 3.4 Simulation confirmation (200 rounds; neighbourhood = 2000-trial Monte Carlo)

My fresh simulation (embedded script) reproduces the divergence decisively:

```
PAIRWISE      2TFT+1AllD: per-agent coop rate = [0.502, 0.502, 0.0]  scores = [799, 799, 408]
NEIGHBOURHOOD 2pTFT+1AllD: per-agent coop rate = [0.015, 0.015, 0.0]
```

- Pairwise TFT coop rate 0.502 = (100% on the TFT-TFT edge + 0% on the TFT-AllD edge)/2. The
  cooperative relationship is fully intact; the 0.5 is an averaging artifact over two partners.
  Scores 799 ≈ 4/round confirm §3.2.
- Neighbourhood coop collapses to ~1.5% (residual = round-1 cooperation amortized over 200
  rounds), confirming §3.3.

**Verdict (confidence: high):** The central claim is correct and the mechanism is precisely
"targeted vs diffuse retaliation," rooted in whether the strategy conditions on a *per-partner*
signal or a *pooled scalar* signal. This is the load-bearing result the whole lab is built on,
and it survives first-principles derivation and independent re-simulation.

---

## 4. Paper vs code, and code vs code — discrepancies (the important section)

### 4.1 Payoff scale differs by a factor of (N−1) between modes — by design, but unnormalized
Pairwise sums N−1 games (all-C ⇒ 2×R=6 at N=3; the test
`tests/test_neighborhood_vs_pairwise.py:315-316` asserts **27.0** at N=10), while neighbourhood
normalizes to one game's scale (all-C ⇒ 3.0; test asserts **3.0**, line 311). **Cross-mode payoff
comparisons are therefore not apples-to-apples** unless you divide pairwise totals by (N−1).
Confusingly, the `npdl` pairwise path **learns from the *average*** payoff (`environment.py:340,
359`; test line 319 asserts the RL reward is 3.0, not 27.0) but **scores the *total*** (line
345). So within one file the reward signal and the fitness signal are on different scales. Flag
for the new impl: **define one canonical normalization and apply it consistently to score,
reward, and reporting.** (confidence: high — directly asserted by the legacy tests.)

### 4.2 The cooperation-ratio denominator is inconsistent across implementations
The scalar that drives pTFT / neighbourhood-TFT is computed **three different ways**:
- `static_figure_generator.py:180`: `current_coop_ratio = num_cooperators / num_total_agents`
  — **denominator N, includes the agent itself.**
- `npd_simulator` neighbourhood path passes a `coop_ratio` that (per `npd_game.py:89`,
  `cooperation_rate = num_cooperators / self.num_agents`) is also **over N including self**.
- `npdl/core/environment.py:348`: `opp_coop_prop = opponent_coop_counts / opponent_total_counts`
  — **excludes self (proportion of *others*).** And the neighbourhood `TitForTatStrategy`
  (`agents.py:111-112`) computes `cooperation_count/len(neighbor_moves)` over neighbours only —
  **also excludes self.**

For N=3 with 2 TFT + 1 AllD this changes the signal a TFT sees from `2/3` (include self) vs
`1/2` (exclude self, counting only the other TFT and the AllD). **Different denominators →
materially different collapse dynamics and different fixed points.** The §3.3 contraction ratio
2/3 assumes the include-self convention (static generator). This is the single most important
under-specified quantity in the legacy code. (confidence: high.)

### 4.3 TFT means two different things in "pairwise" mode across the two engines — CRITICAL
- `static_figure_generator` / `npd_simulator` pairwise TFT: **true per-opponent** — plays a
  *different* move against each opponent based on that opponent's history
  (`static_figure_generator.py:43-47`).
- `npdl` pairwise TFT (`agents.py:88-96`): each agent emits **ONE move per round applied to all
  opponents**, and the rule is "**defect against everyone if ANY single opponent defected last
  round**" (line 94: `if any(move == "defect" ...): return "defect"`). This is *not* targeted
  reciprocity — it is a **grim-ish trigger that collectively punishes cooperators too**. Under 2
  TFT + 1 AllD in `npdl` pairwise, the AllD's defection makes **both TFTs defect against each
  other as well**, which would *break* the very cooperation §3.2 relies on. So the `npdl`
  "pairwise" mode does **not** implement the paper's pairwise mechanism; it is a hybrid that
  partially re-introduces diffuse punishment.

  **This is a genuine scientific bug, not just a style difference:** the headline "pairwise
  sustains cooperation" result depends on which engine you run. The static-figure engine
  (per-opponent) is the one that produces the published Collaborative-Hill result; `npdl`
  pairwise would blunt it. (confidence: high — verified by reading both `choose` paths.)

### 4.4 "Ecosystem-aware TFT" — naming and semantics
`README.md:22,342-343` and `COMPREHENSIVE_NPD_DOCUMENTATION.md:171-173` describe TFT as
"redesigned to be ecosystem-aware." In `npdl` this is the **threshold** variant
(`TitForTatStrategy`, cooperate iff coop-proportion ≥ 0.5, `agents.py:101-102,114-115`) — i.e.
the paper's *quorum/threshold* strategy, **relabeled**. Meanwhile `ProportionalTitForTatStrategy`
(`agents.py:120-159`) is the *probabilistic* pTFT. So "TFT" is overloaded: (a) per-opponent
retaliator, (b) probabilistic group-average, (c) 0.5-threshold quorum. **The new lab must give
these three distinct names and never call all of them "TFT."** (confidence: high.)

### 4.5 Duplicate / shadowed function in `utils.py`
`npdl/core/utils.py` defines `get_pairwise_payoffs` **twice** (lines 138 and 152); the second
silently shadows the first. Behaviour is identical, so no bug today, but it is dead code and a
maintenance hazard. (confidence: high, low severity.)

### 4.6 Exponential / threshold payoff variants exist in code but not in the paper
`utils.py:40-135` implements `exponential_payoff_*` (default exponent 2) and `threshold_payoff_*`
(0.3/0.7 split at threshold 0.5). These are **code-only extensions** with no paper grounding and
some arbitrary magic constants (0.3, 0.7). If the new lab reuses them, they need their own
justification; they are not "the paper's payoff function." (confidence: high.)

### 4.7 First-round / empty-memory conventions
All engines cooperate on round 1 (optimistic TFT). Suspicious-TFT starts D
(`tests/test_neighborhood_vs_pairwise.py:207-208`). The pTFT "first round" branch keys off
`coop_ratio is None` (`static_figure_generator.py:63-64`). These conventions are consistent but
**implicit**; the oracle should pin them.

---

## 5. Is it actually a social dilemma at these parameters? Proof.

A one-shot game is a social dilemma iff (i) defection strictly dominates for each player, yet
(ii) universal cooperation Pareto-dominates universal defection.

### 5.1 2-player PD kernel (pairwise)
Ordering **T > R > P > S**: 5 > 3 > 1 > 0 ✔ (enforced at `payoff_matrix.py:41-42`). Defection
dominant: T=5>R=3 (vs C) and P=1>S=0 (vs D) ✔. Mutual-C Pareto-superior to mutual-D: R=3>P=1 ✔.
Efficiency of cooperation over alternating exploitation **2R > T + S**: 6 > 5 ✔
(`payoff_matrix.py:43-44`). ⇒ genuine PD. (confidence: high.)

### 5.2 Neighbourhood (linear N-person), proven for general k
Defection dominance: for every fixed number of other cooperators k,
```
U_D(k) − U_C(k) = (P−S) + [(T−P)−(R−S)]·k/(N−1)
               = (1−0) + [4−3]·k/2 = 1 + k/2  > 0  for all k ≥ 0.
```
So D strictly dominates C **regardless of what others do** (a dominant strategy, hence the unique
Nash equilibrium is all-D). Numerically confirmed: gap = 1.0, 1.5, 2.0 for k=0,1,2.

Pareto-superiority of cooperation: all-C gives each U_C(N−1)=3.0; all-D gives each U_D(0)=1.0;
3.0 > 1.0 ✔. And per-round social welfare is monotone increasing in the number of cooperators
(sum column in §2.3: 9 > 8 > 6 > 3), so full cooperation is the utilitarian optimum. ⇒ genuine
N-person social dilemma. (confidence: high.)

**General conditions the parameters satisfy (worth encoding, not hard-coding 3/0/5/1):** the
linear N-IPD is a social dilemma iff `T > R > P > S` **and** the per-capita gain from a
cooperator to others exceeds the private loss — here guaranteed because U_D(k) and U_C(k) are
both increasing in k (positive externality of cooperation) while D−C gap stays positive.

---

## 6. What the analytical payoff oracle module must verify (spec for new impl)

The new lab needs a `payoff_oracle` that is the *single source of truth* and a property/oracle
test-suite asserting the following identities and inequalities. Grouped by concern.

### 6.1 Parameter well-formedness (assert on construction)
1. `T > R > P > S` (strict).
2. `2R > T + S` (cooperation beats alternating exploitation).
3. Linear-mode positivity of cooperation externality: `R > S` and `T > P` (so both `U_C`,`U_D`
   increase in k).
4. Dominance gap positive for all k: `U_D(k) − U_C(k) = (P−S) + ((T−P)−(R−S))·k/(N−1) > 0`
   for k∈{0,…,N−1}. Fails ⇒ not a dilemma; oracle must reject or flag.

### 6.2 Pairwise identities (exact)
5. 2-player matrix exactly `{CC:R, CD:S, DC:T, DD:P}` for the row player.
6. `u_i^pw(profile) = Σ_{j≠i} PD(a_i,a_j)`; enumerate all 2^N profiles at N∈{2,3} and match a
   frozen golden table (the §2.3 pairwise column for N=3).
7. All-C total = `(N−1)·R`; all-D total = `(N−1)·P`; single defector's total = `(N−1)·T`; the
   lone cooperator among defectors = `(N−1)·S`. (N=3: 6, 2, 10, 0.)
8. Symmetry: permuting agents permutes payoffs identically (no agent-index dependence).

### 6.3 Neighbourhood / linear identities (exact)
9. `U_C(k) = S + (R−S)·k/(N−1)`, `U_D(k) = P + (T−P)·k/(N−1)`, for k = number of **other**
   cooperators.
10. Boundary reduction to 2-player PD at N=2: `U_C(0)=S, U_C(1)=R, U_D(0)=P, U_D(1)=T`.
11. Corner equals mean-of-pairwise: `U_C(N−1) = R = pairwise_total/(N−1)` when all cooperate;
    `U_D(0)=P` likewise. (Normalization contract: **neighbourhood payoff ≡ pairwise total /
    (N−1)** in the all-same-action corners — encode this as the canonical cross-mode bridge.)
12. Golden table match for the §2.3 neighbourhood column at N=3.
13. Social-welfare monotonicity: Σ payoffs strictly increases with the number of cooperators.

### 6.4 Convention pins (these are the discrepancies from §4 — the oracle must FORCE a choice)
14. **Action encoding** is fixed and documented (legacy uses C=0/D=1; choose deliberately).
15. **Cooperation-ratio denominator** for any group-average strategy is a single documented
    convention (include-self /N **or** exclude-self /(N−1)) — assert it and test the 2TFT+1AllD
    signal equals the intended 2/3 or 1/2. (See §4.2 — currently inconsistent.)
16. **Pairwise TFT is per-opponent**, not "defect-against-all-if-any-defected." Metamorphic test:
    2 TFT + 1 AllD must keep the TFT–TFT edge at (C,C) forever; assert TFT-vs-TFT cooperation
    rate = 1.0 while TFT-vs-AllD = 0 after round 1. (Guards against the §4.3 `npdl` regression.)
17. **Score vs learning-reward normalization** is one documented convention applied to both.

### 6.5 Dynamical / mechanism oracles (small, deterministic where possible)
18. Pairwise, 2 TFT + 1 AllD: TFT steady-state per-round payoff = `R + P` (=4 at N=3); AllD =
    `2P` (=2). Assert to closed form.
19. Neighbourhood, m pTFT + 1 AllD (include-self convention): expected coop ratio obeys
    `q_r = (m/(m+1))·q_{r-1}` and `→ 0`; assert geometric decay ratio and q*→0 fixed point.
20. Nash / dominance oracle: in linear mode all-D is the unique NE (D dominant); in pairwise the
    stage game's unique NE is all-D but the *repeated* game admits the cooperative TFT-TFT
    equilibrium — assert both.
21. Pareto oracle: all-C Pareto-dominates all-D in both modes.
22. Determinism/replay: with fixed seed, identical profiles ⇒ identical payoffs bit-for-bit
    (needed because pTFT is stochastic).

---

## Appendix A — Primary source map (file:line)

| Concern | Authoritative location |
|---|---|
| Paper (lit review, no formulas) | `LEGACY/Paper Resources/Cooperation…– A Li.pdf` p.1–7 |
| Canonical params R,S,T,P | `utils.py:194-197`; `payoff_matrix.py:21-25`; `static_figure_generator.py:15-19` |
| PD constraint checks | `payoff_matrix.py:41-44` |
| Linear neighbourhood payoff | `utils.py:20,37`; `payoff_matrix.py:46-72`; `npd_game.py:38-59`; `static_figure_generator.py:22-28` |
| Pairwise 2-player payoff | `utils.py:152-177`; `payoff_matrix.py:74-88`; `static_figure_generator.py:15-17` |
| Pairwise round (sum) | `npdl/core/environment.py:287-386`; `static_figure_generator.py:96-157` |
| Neighbourhood round | `environment.py:245-285`; `static_figure_generator.py:165-207` |
| Pairwise TFT per-opponent | `static_figure_generator.py:43-47`; `npd_simulator/.../final_agents.py:40-45` |
| npdl pairwise TFT (defect-if-any) | `npdl/core/agents.py:88-96` |
| Neighbourhood pTFT (probabilistic) | `static_figure_generator.py:58-66`; `final_agents.py:54-66`; `agents.py:120-159` |
| "Ecosystem-aware" 0.5-threshold TFT | `agents.py:99-115`; `tft.py:87-117` (pTFT-Threshold) |
| coop-ratio denominator = N (incl self) | `static_figure_generator.py:180`; `npd_game.py:89` |
| coop-ratio denominator excl self | `environment.py:348`; `agents.py:111-112` |
| Payoff-scale test (27 vs 3) | `tests/test_neighborhood_vs_pairwise.py:305-320` |
| Canonical run config | `code_for_website/main_runs/config.py` (num_rounds 20000, num_runs 200; QL lr .1/df .95/eps .1); TFT-E exploration 0.1 |

## Appendix B — Verification method / what was NOT verified
- **Verified first-hand:** paper text (full extraction), all payoff formulas by hand + numeric
  enumeration of all 8 N=3 profiles both modes (script output embedded), social-dilemma
  inequalities (symbolic + numeric), the 2TFT+1AllD divergence (independent 200-round /
  2000-trial re-simulation), and each cited `file:line` was opened and read.
- **NOT verified:** I did not execute the legacy repo's own scripts end-to-end (no venv build);
  I relied on reading their source + my independent reimplementation. Q-learning agents' dynamics
  were not analyzed (out of scope: mechanism/math of the static strategies). Large-N behaviour
  and network-topology (small-world/scale-free) effects were read but not re-simulated. The
  exponential/threshold payoff variants were read, not numerically stress-tested.
- **Residual risk:** the biggest is §4.3 — if the new lab ports `npdl`'s pairwise TFT verbatim,
  the headline result weakens. Pin the per-opponent semantics in the oracle (§6.4 item 16).
