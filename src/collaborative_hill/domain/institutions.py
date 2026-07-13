"""Institution plane: accountability and evidence-topology rules.

Implemented now (the Study 001 2x2):

- accountability = "aggregate":   actions are anonymous in observations
  (counts only); individual credit earned during the episode is pooled and
  split equally at seal. Diffuse accountability — the Tragic Valley pole.
- accountability = "attributable": proposer/verifier/challenger identities are
  visible ("attributable peer review"), and individual credit accrues to the
  acting agent. Targeted accountability — the Collaborative Hill pole.

- evidence_topology = "private":       evidence starts visible only to its
  initial holders; ShareEvidenceAction (costly) makes an item public.
- evidence_topology = "shared_ledger": a shared provenance ledger lists every
  item's existence + source metadata publicly from round 0 (content still
  requires inspection budget), and all claim provenance is public.

The intervention changes WHO IS SEEN and WHO IS CREDITED, never the task,
payoff totals for identical behaviour, or legal actions — the mechanism
certificate (studies/001) checks this by enumeration.

Extension points deliberately NOT implemented (design-first, per the
second-occurrence rule; add when a study needs them, with an ADR):
reputation scores, commitments, sanctions (see SanctSim lineage), audits,
human approval gates, alternative credit-assignment schemes. Each would be a
new field on InstitutionConfig plus rules in the mechanism's observe/credit
paths; keep them out of world-truth resolution.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Accountability = Literal["aggregate", "attributable"]
EvidenceTopology = Literal["private", "shared_ledger"]


class InstitutionConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    accountability: Accountability = "aggregate"
    evidence_topology: EvidenceTopology = "private"
