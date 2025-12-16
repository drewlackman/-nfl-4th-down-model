import json
from pathlib import Path

import pytest

from nfl4th import model
from nfl4th.cli import format_batch_table, load_batch_cases


def test_p_convert_bounds_and_monotonic():
    short = model.p_convert(1)
    long = model.p_convert(10)
    assert 0.05 <= short <= 0.95
    assert 0.05 <= long <= 0.95
    assert short > long  # fewer yards => higher success chance


def test_p_fg_make_reasonable_range():
    chip_shot = model.p_fg_make(model.fg_distance(80))
    long_try = model.p_fg_make(model.fg_distance(20))
    assert 0.02 <= chip_shot <= 0.98
    assert 0.02 <= long_try <= 0.98
    assert chip_shot > long_try


def test_expected_punt_spot_behavior():
    backed_up = model.expected_punt_spot(15)
    midfield = model.expected_punt_spot(50)
    coffin_corner = model.expected_punt_spot(85)
    assert backed_up < midfield  # longer net from deep in own territory
    assert coffin_corner == 20  # most punts here become touchbacks


def test_ep_by_yardline_monotonic():
    own = model.ep_by_yardline(10)
    midfield = model.ep_by_yardline(50)
    redzone = model.ep_by_yardline(90)
    assert own < midfield < redzone


def test_win_probability_curve_behaves():
    low = model.win_prob_from_ep(-2)
    neutral = model.win_prob_from_ep(0)
    high = model.win_prob_from_ep(4)
    assert 0 <= low < neutral < high <= 1


def test_load_custom_lookup(tmp_path: Path):
    custom = {
        "convert": [[0.5, 0.95], [10, 0.95]],
        "fg": [[20, 0.5], [65, 0.5]],
        "ep": [[1, -1.0], [99, 1.0]],
        "punt_net": [[10, 30], [90, 30]],
        "wp": [[-1.0, 0.3], [1.0, 0.7]],
    }
    lookup_path = tmp_path / "lookups.json"
    lookup_path.write_text(json.dumps(custom), encoding="utf-8")
    try:
        model.load_lookups(lookup_path)
        assert model.p_convert(5) == pytest.approx(0.95)
        assert model.p_fg_make(40) == pytest.approx(0.5)
        assert model.ep_by_yardline(50) == pytest.approx(0.0, abs=0.6)
    finally:
        model.load_lookups()  # reset back to default tables for other tests


@pytest.mark.parametrize(
    "yard_line,yards_to_go,expected",
    [
        (20, 1.0, "punt"),
        (90, 5.0, "fg"),
    ],
)
def test_evaluate_recommendations(yard_line, yards_to_go, expected):
    decision = model.evaluate(yard_line, yards_to_go)
    assert decision["recommendation"] == expected
    assert set(decision["ev"].keys()) == {"go", "fg", "punt"}
    assert set(decision["wp"].keys()) == {"go", "fg", "punt"}
    for val in decision["wp"].values():
        assert 0 <= val <= 1
    assert set(decision["delta_ev"].keys()) == {"go", "fg", "punt"}
    assert set(decision["delta_wp"].keys()) == {"go", "fg", "punt"}
    best = decision["recommendation"]
    assert pytest.approx(decision["delta_ev"][best], abs=1e-9) == 0
    assert pytest.approx(decision["delta_wp"][best], abs=1e-9) == 0
    assert "break_even_p_convert" in decision
    break_even = decision["break_even_p_convert"]
    if break_even is not None:
        assert 0 <= break_even <= 1


def test_evaluate_with_override_prob():
    base = model.evaluate(50, 2)
    overridden = model.evaluate(50, 2, override_p_convert=0.2)
    assert overridden["prob_convert"] == 0.2
    assert overridden["ev"]["go"] != base["ev"]["go"]


def test_evaluate_with_override_fg():
    base = model.evaluate(70, 4)
    overridden = model.evaluate(70, 4, override_p_fg=0.1)
    assert overridden["prob_fg_make"] == 0.1
    assert overridden["ev"]["fg"] != base["ev"]["fg"]


def test_evaluate_with_override_punt_net():
    base = model.evaluate(40, 4)
    overridden = model.evaluate(40, 4, override_punt_net=20)
    assert overridden["ev"]["punt"] != base["ev"]["punt"]


def test_format_batch_csv_contains_header():
    res = model.evaluate(40, 2)
    csv_data = format_batch_table([res], include_wp=True)
    lines = csv_data.splitlines()
    assert lines[0].startswith("yard_line,yards_to_go")
    assert "break_even_p_convert" in lines[0]
    assert len(lines) == 2


def test_format_batch_table_tsv():
    res = model.evaluate(35, 1)
    tsv = format_batch_table([res], include_wp=False, delimiter="\t")
    assert "\t" in tsv.splitlines()[0]


def test_load_batch_cases_with_overrides_csv(tmp_path: Path):
    csv_path = tmp_path / "plays.csv"
    csv_path.write_text(
        "yard_line,yards_to_go,p_convert,p_fg,punt_net\n"
        "40,2,0.55,0.7,44\n",
        encoding="utf-8",
    )
    rows = load_batch_cases(csv_path, "csv")
    assert rows[0]["p_convert"] == 0.55
    assert rows[0]["p_fg"] == 0.7
    assert rows[0]["punt_net"] == 44


def test_load_batch_cases_with_overrides_json(tmp_path: Path):
    json_path = tmp_path / "plays.json"
    json_path.write_text(
        json.dumps(
            [
                {
                    "yard_line": 30,
                    "yards_to_go": 3,
                    "p_convert": 0.5,
                    "p_fg": 0.8,
                    "punt_net": 42,
                }
            ]
        ),
        encoding="utf-8",
    )
    rows = load_batch_cases(json_path, "json")
    assert rows[0]["p_convert"] == 0.5
    assert rows[0]["p_fg"] == 0.8
    assert rows[0]["punt_net"] == 42
