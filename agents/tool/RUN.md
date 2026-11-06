# How to run the EveryMind survey tool

One command turns a survey export (`.xlsx`) into every number and a dashboard you can open in any browser.

## What you need

- Python 3.10 or newer (`python3 --version`)
- `make` (built into macOS and Linux; on Windows use WSL, or run the three Python commands under "Without make")
- The survey export, e.g. `BuildFest_EveryMind_Survey_Data_FULL.xlsx`, with a sheet named `Survey Data`

## First time on a computer

Open a terminal in the project folder (the one that contains `Makefile`), then run:

```bash
make setup
```

`make setup` installs the Python packages in `requirements.txt` and, in a git checkout, turns on the repo's commit checks. If you unzipped the artifact (no git) and `make setup` stops at a `git config` error, install the packages directly instead:

```bash
python3 -m pip install -r requirements.txt
```

## Run it

1. Put the export in `data/raw/`. That folder is never committed, so survey rows never leave your computer.
2. Run:

```bash
make run DATA=data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx
```

3. Open the dashboard:

```bash
open outputs/dashboard.html
```

On Windows or Linux, double-click `outputs/dashboard.html` instead.

`make run` runs three steps in order and stops at the first error:

| Step | Command it runs | Writes |
|---|---|---|
| Clean and analyze | `agents/data/pipeline.py --data <file>` | `data/processed/` (local only), `outputs/findings.json`, `outputs/validation_report.json` |
| Code the comments | `agents/text/themes.py` | `outputs/themes.json` |
| Build the dashboard | `agents/tool/build.py` | `outputs/dashboard.html` |

### Without make

```bash
python3 agents/data/pipeline.py --data data/raw/your_export.xlsx
python3 agents/text/themes.py
python3 agents/tool/build.py --strict
```

`--strict` makes the dashboard step fail if the first two steps didn't produce their files, instead of falling back to example data.

## Refresh with next month's export

1. Save the new export to `data/raw/`, e.g. `data/raw/survey_2026_12.xlsx`. You can keep the old one; nothing is overwritten except `outputs/`.
2. Run `make run DATA=data/raw/survey_2026_12.xlsx`.
3. Open `outputs/dashboard.html`. Check the **Data:** line under the title: the response count and the input file fingerprint should match the new file.
4. Scroll to **How to read this, and its limits → Data checks**. New counties, roles or answer wordings that the cleaning step doesn't recognize are counted there. They are not silently dropped.
5. If anything new appears there (say, a new county spelling), ask whoever maintains `agents/data/mappings/` to add it, then run step 2 again.

What updates automatically: every chart, group list, month and table. A new county or a new month appears without code changes. Any group with fewer than 10 people is hidden and listed as "not shown", for privacy and because such numbers are unreliable.

## Sharing the dashboard

`outputs/dashboard.html` is a single file that works offline. You can email it or put it on a shared drive. It contains totals only: no individual answers, comment text, names or emails.

## Checking it works

```bash
make test
```

This runs the automated checks on synthetic data. They need no survey file.

## Troubleshooting

| You see | What it means | What to do |
|---|---|---|
| `make run: NOT IMPLEMENTED - agents/... does not exist yet` | A step hasn't been written yet (during development). | Pull the latest code: `git pull --rebase`. |
| `No module named pandas` (or openpyxl, jsonschema) | Packages aren't installed. | `make setup`, or `python3 -m pip install -r requirements.txt` |
| An error naming the sheet or a column | The export's layout changed (renamed sheet or missing column). | Re-export with the same columns, or report the error message to the data maintainer. |
| `build: ERROR findings ... does not match contracts/findings.schema.json` | The analysis output and the dashboard disagree on the file format. | Pull the latest code so both sides match, then rerun. |
| `build: ERROR ... duplicate IDs` | Two numbers share an ID. | Report it to the data maintainer; IDs must be unique. |
| A red **EXAMPLE DATA** banner on the dashboard | The dashboard was built without real outputs and used the synthetic examples. | Run the full `make run DATA=...` command. Never cite numbers from a page with this banner. |
| "⚠ comments were coded from a different export" under the title | `themes.json` and `findings.json` came from different files. | Run `make run DATA=...` again so both are rebuilt from the same export. |
| `build: WARNING ... n=… < 10 but value not suppressed; hidden in dashboard` | The analysis published a value for a group under 10 people. The dashboard hid it. | Nothing for viewers. Maintainers should fix the suppression in the data step. |
| A chart section says "could not be drawn" | A browser problem or an unexpected file shape. | Open the file in a current Chrome, Edge, Firefox or Safari. The numbers are still in **All numbers**. |
| `python3: command not found` (Windows) | Python isn't on the PATH. | Install Python 3.10+ from python.org and tick "Add to PATH", or use WSL. |
