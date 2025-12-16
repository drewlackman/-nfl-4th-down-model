#!/usr/bin/env python3
"""Generate lookup table JSON used by the model."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_csv",
        type=Path,
        help="CSV seed data with columns curve,x,y",
    )
    parser.add_argument(
        "output_json",
        type=Path,
        help="Destination for generated JSON lookup file",
    )
    return parser.parse_args()


def load_seed(path: Path) -> Dict[str, List[Tuple[float, float]]]:
    buckets: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"curve", "x", "y"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
        for row in reader:
            curve = row["curve"].strip()
            if not curve:
                continue
            x = float(row["x"])
            y = float(row["y"])
            buckets[curve].append((x, y))
    for curve in buckets:
        buckets[curve].sort(key=lambda pair: pair[0])
    return buckets


def main() -> None:
    args = parse_args()
    data = load_seed(args.input_csv)
    args.output_json.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
