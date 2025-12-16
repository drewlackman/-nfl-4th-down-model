import argparse
import csv
import json
from pathlib import Path
from typing import List, Optional, Tuple, TypedDict

from .model import evaluate, load_lookups


def yard_line_type(value: str) -> int:
    try:
        yard_line = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("yard line must be an integer") from exc
    if not 1 <= yard_line <= 99:
        raise argparse.ArgumentTypeError("yard line must be between 1 and 99")
    return yard_line


def yards_to_go_type(value: str) -> float:
    try:
        yards = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("yards to go must be numeric") from exc
    if yards <= 0:
        raise argparse.ArgumentTypeError("yards to go must be positive")
    return yards

def parse_optional_prob(value: Optional[object], label: str) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        val = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not 0 <= val <= 1:
        raise ValueError(f"{label} must be between 0 and 1")
    return val


def parse_optional_punt(value: Optional[object]) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        val = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("punt_net must be numeric") from exc
    if val <= 0:
        raise ValueError("punt_net must be positive")
    return val


class BatchCase(TypedDict):
    yard_line: int
    yards_to_go: float
    p_convert: Optional[float]
    p_fg: Optional[float]
    punt_net: Optional[float]


def choose_override(row_value: Optional[float], global_value: Optional[float]) -> Optional[float]:
    return row_value if row_value is not None else global_value


def load_batch_cases(path: Path, fmt: str) -> List[BatchCase]:
    if fmt == "csv":
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            missing = {"yard_line", "yards_to_go"} - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"CSV missing columns: {', '.join(sorted(missing))}")
            rows: List[BatchCase] = []
            for row in reader:
                yard_line = yard_line_type(row["yard_line"])
                yards = yards_to_go_type(row["yards_to_go"])
                rows.append(
                    BatchCase(
                        yard_line=yard_line,
                        yards_to_go=yards,
                        p_convert=parse_optional_prob(row.get("p_convert"), "p_convert"),
                        p_fg=parse_optional_prob(row.get("p_fg"), "p_fg"),
                        punt_net=parse_optional_punt(row.get("punt_net")),
                    )
                )
            return rows
    with path.open() as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("JSON input must be a list of {yard_line, yards_to_go}")
    rows: List[BatchCase] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"JSON entry {idx} is not an object")
        if "yard_line" not in item or "yards_to_go" not in item:
            raise ValueError(f"JSON entry {idx} missing required keys")
        rows.append(
            BatchCase(
                yard_line=yard_line_type(str(item["yard_line"])),
                yards_to_go=yards_to_go_type(str(item["yards_to_go"])),
                p_convert=parse_optional_prob(item.get("p_convert"), "p_convert"),
                p_fg=parse_optional_prob(item.get("p_fg"), "p_fg"),
                punt_net=parse_optional_punt(item.get("punt_net")),
            )
        )
    return rows


def print_single_result(
    out: dict,
    show_wp: bool = False,
    override_p: float = None,
    override_fg: float = None,
) -> None:
    print("\n4th Down Decision (EV-based)")
    print("----------------------------")
    print(f"Yard line: {out['yard_line']}")
    print(f"Yards to go: {out['yards_to_go']}")
    print("")
    print(f"P(convert): {out['prob_convert']:.3f}")
    if override_p is not None:
        print(f"  (overridden from model to {override_p:.3f})")
    print(f"FG distance: {out['fg_distance']} | P(make): {out['prob_fg_make']:.3f}")
    if override_fg is not None:
        print(f"  (overridden from model to {override_fg:.3f})")
    print("")
    print("Expected Value (EP units):")
    for k, v in out["ev"].items():
        print(f"  {k:>4}: {v:+.3f}")
    be = out.get("break_even_p_convert")
    be_text = f"{be:.3f}" if be is not None else "N/A"
    print(f"\nBreak-even p(convert) vs best non-go: {be_text}")
    print("")
    print("Delta vs best (EV):")
    for k, v in out["delta_ev"].items():
        print(f"  {k:>4}: {v:+.3f}")
    if show_wp:
        print("")
        print("Win Probability (approx.):")
        for k, v in out["wp"].items():
            print(f"  {k:>4}: {v:>.3f}")
        print("")
        print("Delta vs best (WP):")
        for k, v in out["delta_wp"].items():
            print(f"  {k:>4}: {v:+.3f}")
    print("")
    print(f"Recommendation: {out['recommendation'].upper()}\n")


def batch_header(include_wp: bool = False) -> List[str]:
    header_parts = [
        "yard_line",
        "yards_to_go",
        "recommendation",
        "go_ev",
        "fg_ev",
        "punt_ev",
        "go_delta_ev",
        "fg_delta_ev",
        "punt_delta_ev",
        "break_even_p_convert",
    ]
    if include_wp:
        header_parts += [
            "go_wp",
            "fg_wp",
            "punt_wp",
            "go_delta_wp",
            "fg_delta_wp",
            "punt_delta_wp",
        ]
    return header_parts


def format_batch_row(res: dict, include_wp: bool = False) -> List[str]:
    row = [
        str(res["yard_line"]),
        str(res["yards_to_go"]),
        res["recommendation"],
        f"{res['ev']['go']:.3f}",
        f"{res['ev']['fg']:.3f}",
        f"{res['ev']['punt']:.3f}",
        f"{res['delta_ev']['go']:.3f}",
        f"{res['delta_ev']['fg']:.3f}",
        f"{res['delta_ev']['punt']:.3f}",
        f"{res['break_even_p_convert']:.3f}" if res["break_even_p_convert"] is not None else "",
    ]
    if include_wp:
        row += [
            f"{res['wp']['go']:.3f}",
            f"{res['wp']['fg']:.3f}",
            f"{res['wp']['punt']:.3f}",
            f"{res['delta_wp']['go']:.3f}",
            f"{res['delta_wp']['fg']:.3f}",
            f"{res['delta_wp']['punt']:.3f}",
        ]
    return row


def format_batch_table(results: List[dict], include_wp: bool = False, delimiter: str = ",") -> str:
    rows = [delimiter.join(batch_header(include_wp))]
    for res in results:
        row = format_batch_row(res, include_wp=include_wp)
        rows.append(delimiter.join(row))
    return "\n".join(rows)


def print_batch_table(results: List[dict], include_wp: bool = False) -> None:
    print(format_batch_table(results, include_wp=include_wp))


def main():
    parser = argparse.ArgumentParser(description="NFL 4th Down Decision Model")
    parser.add_argument(
        "--yard_line",
        type=yard_line_type,
        help="1 = own goal line, 99 = opponent goal line",
    )
    parser.add_argument(
        "--yards_to_go",
        type=yards_to_go_type,
        help="Yards needed for first down",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to CSV or JSON file for batch evaluation",
    )
    parser.add_argument(
        "--input-format",
        choices=("csv", "json"),
        default="csv",
        help="Format of --input file (default: csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="When using --input, write results to this path instead of stdout",
    )
    parser.add_argument(
        "--output-format",
        choices=("csv", "json", "tsv"),
        default="csv",
        help="Format for --output (default csv; use tsv for tab-separated tables). Ignored without --output.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting existing --output file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of formatted text",
    )
    parser.add_argument(
        "--lookups",
        type=Path,
        help="Path to alternate lookups.json (defaults to built-in tables)",
    )
    parser.add_argument(
        "--show-wp",
        action="store_true",
        help="Display approximate win probabilities derived from EV values",
    )
    parser.add_argument(
        "--p-convert",
        type=float,
        help="Override modeled p(convert) to see EV/WP at a custom success probability (0-1)",
    )
    parser.add_argument(
        "--p-fg",
        type=float,
        help="Override modeled field-goal make probability (0-1)",
    )
    parser.add_argument(
        "--punt-net",
        type=float,
        help="Override expected punt net yards (results capped to field limits)",
    )
    args = parser.parse_args()

    if args.lookups:
        load_lookups(args.lookups)
    if args.p_convert is not None and not (0 <= args.p_convert <= 1):
        parser.error("--p-convert must be between 0 and 1")
    if args.p_fg is not None and not (0 <= args.p_fg <= 1):
        parser.error("--p-fg must be between 0 and 1")
    if args.punt_net is not None and args.punt_net <= 0:
        parser.error("--punt-net must be positive")

    if args.input:
        if args.yard_line is not None or args.yards_to_go is not None:
            parser.error("Provide either --yard_line/--yards_to_go or --input, not both.")
        cases = load_batch_cases(args.input, args.input_format)
        results = [
            evaluate(
                case["yard_line"],
                case["yards_to_go"],
                override_p_convert=choose_override(case["p_convert"], args.p_convert),
                override_p_fg=choose_override(case["p_fg"], args.p_fg),
                override_punt_net=choose_override(case["punt_net"], args.punt_net),
            )
            for case in cases
        ]
        if args.output:
            if args.output.exists() and not args.force:
                parser.error(f"{args.output} already exists. Use --force to overwrite.")
            if args.output_format == "json":
                args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
            else:
                delimiter = "\t" if args.output_format == "tsv" else ","
                args.output.write_text(
                    format_batch_table(results, include_wp=args.show_wp, delimiter=delimiter),
                    encoding="utf-8",
                )
            print(f"Wrote {len(results)} rows to {args.output}")
        elif args.json:
            print(json.dumps(results, indent=2))
        else:
            print_batch_table(results, include_wp=args.show_wp)
        return

    if args.yard_line is None or args.yards_to_go is None:
        parser.error("You must specify --yard_line and --yards_to_go for single evaluation.")

    out = evaluate(
        args.yard_line,
        args.yards_to_go,
        override_p_convert=args.p_convert,
        override_p_fg=args.p_fg,
        override_punt_net=args.punt_net,
    )

    if args.json:
        print(json.dumps(out, indent=2))
        return

    print_single_result(
        out,
        show_wp=args.show_wp,
        override_p=args.p_convert,
        override_fg=args.p_fg,
    )

if __name__ == "__main__":
    main()
