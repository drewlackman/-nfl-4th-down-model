# NFL 4th Down Model

Data-driven command-line tool that estimates the expected value (EV) of going for it, kicking a field goal, or punting on 4th down. The goal is to provide a transparent, hackable model you can experiment with as you learn football analytics. Today’s version uses simple lookup tables and interpolated expected-points curves—perfect for explaining techniques, not for calling plays on Sundays.

![CLI screenshot](docs/cli-screenshot.png)

> **Why this matters:** 4th-down calls are some of the most scrutinized decisions in football. Showing you can model them—even with simplified assumptions—is a great portfolio piece for analytics roles, data engineering gigs, and software positions that value explainable models.

## Features

- EV calculation for go / FG / punt using conversion, kick, and punt curves.
- Optional win probability mapping and delta output so you can compare options quickly.
- Batch processing via CSV or JSON, including per-row overrides for conversion %, FG %, or punt nets.
- Flexible CLI overrides for experimenting with custom assumptions (`--p-convert`, `--p-fg`, `--punt-net`, `--lookups`, `--show-wp`, `--json`, etc.).
- Lookup table generator + documented seed data, so you can swap in your own curves.
- Pytest-based unit suite covering model helpers, CLI formatting, and batch parsing.

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Once dependencies are installed, run the CLI for a single play:

```bash
nfl4th --yard_line 50 --yards_to_go 2.5
```

You should see an EV breakdown for go/field goal/punt along with a recommendation:

```
4th Down Decision (EV-based)
----------------------------
Yard line: 50
Yards to go: 2.5

P(convert): 0.552
FG distance: 67 | P(make): 0.210

Expected Value (EP units):
    go: -0.321
    fg: -1.056
  punt: -0.708

Break-even p(convert) vs best non-go: 0.612

Delta vs best (EV):
    go: +0.387
    fg: -0.348
  punt:  0.000

Recommendation: PUNT
```

### Batch mode

Provide a CSV (default) or JSON list of scenarios:

```csv
yard_line,yards_to_go,p_convert,p_fg,punt_net
40,2,0.60,,45
65,4.5,,0.55,
18,1,,,
```

Run:

```bash
nfl4th --input plays.csv --json
```

This prints the evaluation for every row (CSV output if `--json` is omitted). Each row includes the raw EV values plus `*_delta_ev` columns showing how far each decision sits from the best option and a `break_even_p_convert` column indicating the conversion probability required for “go” to tie the best non-go choice. CSV/JSON inputs can optionally include `p_convert`, `p_fg`, or `punt_net` columns to override those assumptions per row. Add `--show-wp` if you also want the estimated win probabilities (and their deltas).

To capture results to a file, provide `--output plays.csv` (or `--output-format json` to write JSON, `tsv` for tab-separated). Existing files are preserved unless you pass `--force`.

Use `--p-convert 0.60` to override the modeled conversion probability (single play or batch) so you can see EV/WP under custom success assumptions. Similarly, `--p-fg 0.45` and `--punt-net 38` let you plug in your own field-goal make rate or expected punt net yards.

### Examples

Need a quick demo? Use the files in `examples/`:

nfl4th --input examples/sample_plays.csv --output examples/sample_output.csv --force
cat examples/sample_output.csv
```

nfl4th --input examples/sample_plays.csv --output examples/sample_output.json --output-format json --force
jq "." examples/sample_output.json
```

This repository already includes those sample inputs/outputs so you can show a working model immediately.

## Repository Layout

- `src/nfl4th/model.py` – core model logic (conversion probability, field-goal probability, punt outcomes, EV calculation).
- `src/nfl4th/cli.py` – command-line interface that accepts yard line & yards-to-go and prints results.
- `scripts/generate_lookup_tables.py` – helper that turns `data/curve_seed.csv` into the JSON consumed by the model.
- `tests/test_model.py` – pytest suite.
- `docs/` – optional screenshots/notes (create your own assets here).

## Modeling Assumptions

- **Conversion chances** come from a simple interpolation table built off league-average rates (≈72% on 4th-and-1, ≈26% on 4th-and-10, etc.).
- **Field-goal odds** use a distance-based curve that drops sharply beyond 55+ yards.
- **Punt model** varies net distance by field position and assumes touchbacks when the expected spot crosses the goal line.
- **Expected points** comes from an interpolated curve fit to historical drive results by yard line (so deep in your territory is negative EP, red-zone snaps approach +6).
- **Win probability** is a simple mapping from expected points to WP (e.g., negative EP ≈ <40% WP; +6 EP ≈ 95% WP). These WP values are shown when `--show-wp` is provided. WP mapping is intentionally simplistic—treat it as illustrative.

## Lookup Tables (data/curve_seed.csv)

The conversion/FG/punt/EP curves are stored in `data/curve_seed.csv`. When you tweak the seed data, regenerate the JSON the model loads:

```bash
python scripts/generate_lookup_tables.py data/curve_seed.csv src/nfl4th/lookups.json
```

Commit both the CSV change and the resulting `src/nfl4th/lookups.json` so the CLI stays in sync.

You can also point the CLI at an alternate lookup file (e.g., experimental fits) with `--lookups path/to/lookups.json`.

## Testing

```bash
source .venv/bin/activate
python -m pytest
```

## Roadmap / Ideas

1. Swap the hand-crafted lookup tables with curves derived from actual nflfastR data (two-minute situations, opponent adjustments, etc.).
2. Layer on situational adjustments (score, time, weather, team strength) to change conversion/FG odds dynamically.
3. Integrate win-probability impact alongside expected points using an actual WP model.
4. Build a notebook or small web UI that lets you upload CSVs and visualize the go/fg/punt EV curves.
5. Package as an installable CLI (via `pyproject.toml`) and add CI for automated tests.
