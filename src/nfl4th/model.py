import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def _interp(value: float, samples: Iterable[Tuple[float, float]]) -> float:
    ordered = sorted(samples, key=lambda item: item[0])
    if value <= ordered[0][0]:
        return ordered[0][1]
    if value >= ordered[-1][0]:
        return ordered[-1][1]
    for idx in range(1, len(ordered)):
        x0, y0 = ordered[idx - 1]
        x1, y1 = ordered[idx]
        if value <= x1:
            span = x1 - x0
            weight = (value - x0) / span if span else 0.0
            return y0 + weight * (y1 - y0)
    return ordered[-1][1]


LOOKUPS_PATH = Path(__file__).resolve().with_name("lookups.json")

CONVERT_PROB_POINTS: List[Tuple[float, float]] = []
FG_PROB_POINTS: List[Tuple[float, float]] = []
EP_POINTS: List[Tuple[float, float]] = []
PUNT_NET_POINTS: List[Tuple[float, float]] = []
WP_POINTS: List[Tuple[float, float]] = []


def load_lookups(path: Optional[Path] = None) -> None:
    target = Path(path) if path else LOOKUPS_PATH
    with target.open() as fh:
        data: Dict[str, List[List[float]]] = json.load(fh)
    global CONVERT_PROB_POINTS, FG_PROB_POINTS, EP_POINTS, PUNT_NET_POINTS, WP_POINTS
    CONVERT_PROB_POINTS = [tuple(pair) for pair in data["convert"]]
    FG_PROB_POINTS = [tuple(pair) for pair in data["fg"]]
    EP_POINTS = [tuple(pair) for pair in data["ep"]]
    PUNT_NET_POINTS = [tuple(pair) for pair in data["punt_net"]]
    WP_POINTS = [tuple(pair) for pair in data["wp"]]


load_lookups()


def p_convert(yards_to_go: float) -> float:
    p = _interp(yards_to_go, CONVERT_PROB_POINTS)
    return max(0.05, min(0.95, p))


def fg_distance(yard_line: int) -> int:
    return int(round((100 - yard_line) + 17))


def p_fg_make(distance: int) -> float:
    p = _interp(distance, FG_PROB_POINTS)
    return max(0.02, min(0.98, p))


def ep_by_yardline(yard_line: int) -> float:
    yard = max(1, min(99, yard_line))
    return _interp(yard, EP_POINTS)

def flip_field(yard_line: int) -> int:
    return 100 - yard_line

def expected_punt_spot(yard_line: int) -> int:
    net = _interp(yard_line, PUNT_NET_POINTS)
    new_spot = yard_line + net
    if new_spot >= 100:
        return 20
    limited = max(20, min(99, new_spot))
    return int(round(limited))


def win_prob_from_ep(ep: float) -> float:
    return _interp(ep, WP_POINTS)

def evaluate(
    yard_line: int,
    yards_to_go: float,
    override_p_convert: float = None,
    override_p_fg: float = None,
    override_punt_net: float = None,
) -> dict:
    # GO
    pc = override_p_convert if override_p_convert is not None else p_convert(yards_to_go)
    conv_spot = min(99, int(round(yard_line + yards_to_go)))
    ep_after_convert = ep_by_yardline(conv_spot)

    fail_spot = flip_field(yard_line)
    ep_after_fail = -ep_by_yardline(fail_spot)

    ev_go = pc * ep_after_convert + (1 - pc) * ep_after_fail

    # FIELD GOAL
    dist = fg_distance(yard_line)
    pm = override_p_fg if override_p_fg is not None else p_fg_make(dist)

    ep_after_make = 3 - ep_by_yardline(25)
    miss_spot = flip_field(yard_line)
    ep_after_miss = -ep_by_yardline(miss_spot)

    ev_fg = pm * ep_after_make + (1 - pm) * ep_after_miss

    # PUNT
    if override_punt_net is not None:
        punt_spot = int(round(max(20, min(99, yard_line + override_punt_net))))
    else:
        punt_spot = expected_punt_spot(yard_line)
    opp_spot = flip_field(punt_spot)
    ev_punt = -ep_by_yardline(opp_spot)

    options = {"go": ev_go, "fg": ev_fg, "punt": ev_punt}
    wp_options = {k: win_prob_from_ep(v) for k, v in options.items()}
    best = max(options, key=options.get)
    best_ev = options[best]
    best_wp = wp_options[best]
    ev_delta = {k: v - best_ev for k, v in options.items()}
    wp_delta = {k: v - best_wp for k, v in wp_options.items()}

    non_go = {k: v for k, v in options.items() if k != "go"}
    best_alt_ev = max(non_go.values()) if non_go else None
    break_even = None
    denom = ep_after_convert - ep_after_fail
    if best_alt_ev is not None and abs(denom) > 1e-6:
        candidate = (best_alt_ev - ep_after_fail) / denom
        break_even = max(0.0, min(1.0, candidate))

    return {
        "yard_line": yard_line,
        "yards_to_go": yards_to_go,
        "prob_convert": pc,
        "fg_distance": dist,
        "prob_fg_make": pm,
        "ev": options,
        "wp": wp_options,
        "delta_ev": ev_delta,
        "delta_wp": wp_delta,
        "break_even_p_convert": break_even,
        "recommendation": best,
    }
