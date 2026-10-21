# Collaborative Hill Lab — stable entry points.
# Windows note: run from Git Bash (GNU make 3.81 works). Every target has a
# direct-command equivalent documented in README.md.

PYTHON ?= python
ifeq ($(OS),Windows_NT)
PY ?= .venv/Scripts/python.exe
else
PY ?= .venv/bin/python
endif
CHL := "$(PY)" -m collaborative_hill.cli

.PHONY: doctor setup check test validate study-000 study-001-smoke replay-smoke report clean-generated

doctor:
	$(CHL) doctor

setup:
	"$(PYTHON)" -m venv .venv
	"$(PY)" -m pip install --disable-pip-version-check -r requirements-lock.txt
	"$(PY)" -m pip install --disable-pip-version-check --no-build-isolation -c requirements-lock.txt -e ".[dev,analysis]"
	"$(PY)" -m pip check

check:
	"$(PY)" -m ruff check src tests studies scripts
	"$(PY)" -m mypy
	"$(PY)" -m pytest tests/unit tests/property -q

test:
	"$(PY)" -m pytest tests/ -q

validate:
	$(CHL) study validate "studies/000-legacy-reproduction"
	$(CHL) study validate "studies/001-evidence-commons"

study-000:
	$(CHL) run "studies/000-legacy-reproduction" --artifacts artifacts
	"$(PY)" "studies/000-legacy-reproduction/generate_report.py"

study-001-smoke:
	$(CHL) run "studies/001-evidence-commons" --artifacts artifacts --replicates 1
	"$(PY)" "studies/001-evidence-commons/certificate.py"

# replays the first sealed run found under artifacts/ (both studies qualify)
replay-smoke:
	"$(PY)" scripts/replay_smoke.py

report:
	"$(PY)" scripts/report_all.py

clean-generated:
	"$(PY)" scripts/clean_generated.py
