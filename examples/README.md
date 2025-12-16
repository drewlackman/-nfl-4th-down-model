# Examples

These sample files make it easy to try the CLI without crafting inputs by hand.

## CSV Demo

```bash
nfl4th --input examples/sample_plays.csv --output examples/sample_output.csv --force
```

View results:

```bash
cat examples/sample_output.csv
```

## JSON Demo

```bash
nfl4th --input examples/sample_plays.csv --output examples/sample_output.json --output-format json --force
```

```bash
jq "." examples/sample_output.json
```
