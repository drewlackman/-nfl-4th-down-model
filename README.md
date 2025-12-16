# NFL 4th-Down Decision Model

A beginner-friendly Python project that recommends whether to go for it, punt, or kick a field goal on 4th down using a simple Expected Points model.

## Quick start
1. Create and activate a virtual environment (Python 3.10+):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install the package (add `".[dev]"` to get lint/test extras):

   ```bash
   pip install -e .
   ```

3. Run the CLI with any yard line / yards-to-go combo (1 = own goal line, 99 = opponent). `--show-wp` adds the win-probability view you see in the screenshot:

   ```bash
   nfl4th --yard_line 50 --yards_to_go 2.5 --show-wp
   ```

That’s enough to explore the model. When you’re ready, run `nfl4th --help` or jump to the advanced options below for overrides and batch mode.

## Batch mode (optional)
Use a CSV/JSON input file (see `examples/sample_plays.csv`) to evaluate multiple plays at once:

```bash
nfl4th --input examples/sample_plays.csv \
       --output examples/sample_output.csv \
       --output-format csv \
       --force
```

Omit `--output` to stream the table to stdout, or switch to JSON output via `--output-format json`.

## Advanced CLI options

| Flag | Type / Default | Description |
| --- | --- | --- |
| `--yard_line` | int (1‑99) | Yard line for single-play evaluation (1 = own goal line, 99 = opponent). Required unless `--input` is used. |
| `--yards_to_go` | float (>0) | Yards needed for the first down in single-play mode. Required unless `--input` is used. |
| `--input` | path | CSV or JSON file to run in batch mode (mutually exclusive with `--yard_line` / `--yards_to_go`). |
| `--input-format` | `csv` (default) or `json` | File format when supplying `--input`. Determines how the file is parsed. |
| `--output` | path | When set with `--input`, write results to this path instead of printing them. |
| `--output-format` | `csv` (default), `json`, `tsv` | Format for `--output`. Ignored when `--output` is omitted. |
| `--force` | flag (false) | Allow overwriting an existing `--output` file. |
| `--json` | flag (false) | Emit machine-readable JSON instead of the formatted text or table. |
| `--lookups` | path | Use a custom `lookups.json` file instead of the built-in tables. |
| `--show-wp` | flag (false) | Display approximate win probabilities alongside expected value outputs. |
| `--p-convert` | float [0,1] | Override the modeled conversion probability before computing EV/WP. |
| `--p-fg` | float [0,1] | Override the modeled field-goal make probability. |
| `--punt-net` | float (>0) | Override expected net punt yardage (capped to field limits internally). |
