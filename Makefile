# Each target delegates to its owner's entry point; a missing entry point fails loudly (see CLAUDE.md).
DATA ?= data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx
PY   ?= python3
need = @test -e $(1) || { echo "make $@: NOT IMPLEMENTED - $(1) does not exist yet (owner: $(2) agent)" >&2; exit 1; }

.PHONY: setup data themes run test verify submit crosscheck fixtures

setup:
	$(PY) -m pip install -r requirements.txt
	-chmod +x scripts/hooks/* scripts/*.sh 2>/dev/null
	@git rev-parse --git-dir >/dev/null 2>&1 && git config core.hooksPath scripts/hooks || echo "setup: not a git checkout; commit hook skipped"

data:
	$(call need,agents/data/pipeline.py,data)
	$(PY) agents/data/pipeline.py --data "$(DATA)"

themes: data
	$(call need,agents/text/themes.py,text)
	$(PY) agents/text/themes.py

run: themes
	$(call need,agents/tool/build.py,tool)
	$(PY) agents/tool/build.py

test:
	$(PY) -m pytest -q --import-mode=importlib tests agents

verify:
	bash scripts/check_repo.sh
	$(call need,scripts/verify.py,narrative)
	$(PY) scripts/verify.py

submit:
	$(call need,scripts/submit.py,narrative)
	$(PY) scripts/submit.py

# Independent recompute of headline numbers from the raw xlsx; opens to:data issues on mismatch (ARGS=--no-issues to skip)
crosscheck:
	$(PY) agents/narrative/crosscheck/crosscheck.py --data "$(DATA)" $(ARGS)

# Synthetic raw-format workbooks (base + drift variants) -> tests/fixtures/ (gitignored)
fixtures:
	$(PY) agents/narrative/fixtures/make_fixtures.py --out tests/fixtures
