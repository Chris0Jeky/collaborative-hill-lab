"""Exercise certificate verdicts through the generated report, not a duplicate predicate."""

import importlib.util
from fractions import Fraction
from pathlib import Path

import pytest

STUDY = Path(__file__).resolve().parents[2] / "studies" / "001-evidence-commons"


@pytest.fixture
def certificate(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(STUDY))
    spec = importlib.util.spec_from_file_location(
        "certificate_under_test", STUDY / "certificate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "STUDY_DIR", tmp_path)
    return module


@pytest.mark.parametrize(("benefit", "cost", "failed_institution", "c1", "c2"), [
    (Fraction(1, 2), 1, None, True, True),  # C1 gain=1/2; C2 total=3/2 > 0.
    (Fraction(0), 1, None, True, False),  # C1 true alone cannot certify.
    (Fraction(1), 3, None, True, False),  # Equal totals fail strict C2.
    (Fraction(1), 1, None, False, True),  # No strictly profitable deviation.
    (Fraction(0), 0, None, False, False),
    (Fraction(1, 2), 1, ("attributable", "shared_ledger"), True, False),
])
def test_social_dilemma_requires_both_conditions_everywhere(
    certificate, monkeypatch, tmp_path, capsys, benefit, cost, failed_institution, c1, c2,
):
    def run_profile(acc, topo, profile, workdir):
        # Synthetic public-good payoff: benefit per contributor minus own contribution cost.
        b = Fraction(0) if (acc, topo) == failed_institution else benefit
        count = profile.count("contributor")
        return {
            "utility": {a: b * count - cost * (s == "contributor")
                        for a, s in zip(certificate.AGENTS, profile, strict=True)},
            "briefing": (), "quality": 0, "credit": {},
        }

    monkeypatch.setattr(certificate, "run_profile", run_profile)
    certificate.main()
    report = (tmp_path / "MECHANISM_CERTIFICATE.md").read_text(encoding="utf-8")
    verdict = "CERTIFIED" if c1 and c2 else "NOT CERTIFIED"
    assert f"Social dilemma (within the enumerated strategy set): {verdict}**" in report
    stdout = capsys.readouterr().out
    assert f"C1 temptation everywhere: {c1}; C2 collective stakes everywhere: {c2}" in stdout
    if not c2:
        assert "C2 fails under:" in report
        assert "attributable x shared_ledger" in report.split("C2 fails under:")[1]
    assert "genuine dilemma" not in report
    if failed_institution:
        assert "Intervention integrity: VIOLATED**" in report
        assert "accountability redistributes credit without changing the task (C3)." not in report


def test_current_study_cannot_certify(certificate, tmp_path):
    certificate.main()
    report = (tmp_path / "MECHANISM_CERTIFICATE.md").read_text(encoding="utf-8")
    assert "Social dilemma (within the enumerated strategy set): NOT CERTIFIED**" in report
    for acc in ("aggregate", "attributable"):
        assert f"| {acc} x private | -20.00 | 0.00 | NO |" in report
        assert f"| {acc} x shared_ledger | -7.00 | 0.00 | NO |" in report
    assert "Intervention integrity: CERTIFIED**" in report
    assert "profiles checked: 16; violations: 0" in report
