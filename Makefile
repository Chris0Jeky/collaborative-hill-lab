# Collaborative Hill Lab — stable entry points.
# Windows note: run from Git Bash (GNU make 3.81 works). Every target has a
# direct-command equivalent documented in README.md.

PY := .venv/Scripts/python.exe
CHL := $(PY) -m collaborative_hill.cli

.PHONY: doctor setup check test validate study-000 study-001-smoke replay-smoke report clean-generated

doctor:
	$(CHL) doctor

setup:
	python -m venv .venv
	$(PY) -m pip install --disable-pip-version-check -e ".[dev,analysis]"
	$(PY) -m pip freeze --exclude-editable > requirements-lock.txt

check:
	$(PY) -m ruff check src tests studies
	$(PY) -m pytest tests/unit tests/property -q

test:
	$(PY) -m pytest tests/ -q

validate:
	$(CHL) study validate "studies/000-legacy-reproduction"
	$(CHL) study validate "studies/001-evidence-commons"

study-000:
	$(CHL) run "studies/000-legacy-reproduction" --artifacts artifacts
	$(PY) "studies/000-legacy-reproduction/generate_report.py"

study-001-smoke:
	$(CHL) run "studies/001-evidence-commons" --artifacts artifacts --replicates 1
	cd "studies/001-evidence-commons" && "../../$(PY)" certificate.py

# replays the first sealed run found under artifacts/ (both studies qualify)
replay-smoke:
	$(PY) scripts/replay_smoke.py

report:
	$(PY) scripts/report_all.py

clean-generated:
	$(PY) scripts/clean_generated.py
