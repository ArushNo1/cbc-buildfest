# Each target delegates to its owner's entry point; a missing entry point fails loudly (see CLAUDE.md).
DATA ?= data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx
PY   ?= python3
need = @test -e $(1) || { echo "make $@: NOT IMPLEMENTED - $(1) does not exist yet (owner: $(2) agent)" >&2; exit 1; }

.PHONY: setup data themes run test verify submit

setup:
	chmod +x scripts/hooks/* scripts/*.sh
	git config core.hooksPath scripts/hooks
	$(PY) -m pip install -r requirements.txt

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
