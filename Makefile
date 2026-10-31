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
STUDY002_ARTIFACTS ?= artifacts/study-002

<<<<<<< HEAD
.PHONY: doctor setup check check-atlas check-study002 check-responsive check-graph check-sparse-ptft test validate acceptance study-000 study-001-smoke study-002-plan study-002 replay-smoke report clean-generated
=======
.PHONY: doctor setup quick lab mutants check check-atlas check-study002 check-responsive check-graph test validate acceptance study-000 study-001-smoke study-002-plan study-002 replay-smoke report clean-generated
>>>>>>> origin/main

doctor:
	$(CHL) doctor

setup:
	"$(PYTHON)" -m venv .venv
	"$(PY)" -m pip install --disable-pip-version-check -r requirements-lock.txt
	"$(PY)" -m pip install --disable-pip-version-check --no-build-isolation -c requirements-lock.txt -e ".[dev,analysis]"
	"$(PY)" -m pip check

# Fast feedback only: CI still runs the complete gate on the exact commit.
quick:
	"$(PY)" scripts/quick.py

lab:
	"$(PY)" scripts/lab.py

# Slow development probe: a survivor is a test gap or an equivalent change.
mutants:
	"$(PY)" scripts/mutants.py

check:
	"$(PY)" -m ruff check src tests studies scripts
	"$(PY)" -m mypy
	"$(PY)" -m pytest tests/unit tests/property -q

# The standalone experiment is outside the installed package's mypy scope.
check-atlas:
	"$(PY)" -m ruff check experiments/incentive-atlas
	"$(PY)" -m mypy --strict --follow-imports=silent experiments/incentive-atlas/atlas.py scripts/check_atlas.py
	"$(PY)" scripts/check_atlas.py

check-study002:
	"$(PY)" -m mypy --strict --follow-imports=silent studies/002-nipd-sensitivity/*.py
	"$(PY)" studies/002-nipd-sensitivity/generate_study.py --check
	"$(PY)" studies/002-nipd-sensitivity/generate_exact_benchmark.py --check

check-responsive:
	"$(PY)" -m ruff check experiments/responsive-commons
	"$(PY)" -m mypy --strict --follow-imports=silent experiments/responsive-commons/responsive_commons.py
	"$(PY)" experiments/responsive-commons/responsive_commons.py --check

check-graph:
	"$(PY)" -m ruff check experiments/graph-topology
	"$(PY)" -m mypy --strict --follow-imports=silent experiments/graph-topology/graph_experiment.py scripts/check_graph.py
	"$(PY)" experiments/graph-topology/graph_experiment.py --check
	$(CHL) study validate experiments/graph-topology
	"$(PY)" scripts/check_graph.py

check-sparse-ptft:
	"$(PY)" -m ruff check experiments/sparse-ptft
	"$(PY)" -m mypy --strict --follow-imports=silent experiments/sparse-ptft/*.py
	"$(PY)" -m pytest tests/unit/test_sparse_ptft.py -q
	"$(PY)" experiments/sparse-ptft/generate.py --check

test:
	"$(PY)" -m pytest tests/ -q

validate:
	$(CHL) study validate "studies/000-legacy-reproduction"
	$(CHL) study validate "studies/001-evidence-commons"
	$(CHL) study validate "studies/002-nipd-sensitivity"
	$(CHL) study validate "studies/002-nipd-sensitivity/stochastic"

acceptance:
	"$(PY)" scripts/acceptance.py

study-000:
	$(CHL) run "studies/000-legacy-reproduction" --artifacts artifacts
	"$(PY)" "studies/000-legacy-reproduction/generate_report.py"

study-001-smoke:
	$(CHL) run "studies/001-evidence-commons" --artifacts artifacts --replicates 1
	"$(PY)" "studies/001-evidence-commons/certificate.py"

study-002-plan:
	"$(PY)" studies/002-nipd-sensitivity/run_study.py --artifacts "$(STUDY002_ARTIFACTS)" --plan

study-002:
	"$(PY)" studies/002-nipd-sensitivity/run_study.py --artifacts "$(STUDY002_ARTIFACTS)"
	"$(PY)" studies/002-nipd-sensitivity/generate_report.py --artifacts "$(STUDY002_ARTIFACTS)" --output "$(STUDY002_ARTIFACTS)/report"

# Replays the first sealed run found under artifacts/.
replay-smoke:
	"$(PY)" scripts/replay_smoke.py

report:
	"$(PY)" scripts/report_all.py

clean-generated:
	"$(PY)" scripts/clean_generated.py
