"""Keep the Lab 2/3 style tests; run with: python -m pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dc_bias  # noqa: E402


P = {
    "vcc": 12.0, "beta": 100.0, "vbe": 0.7,
    "rb": 470e3, "rc": 2.2e3, "re": 1e3,
    "r1": 100e3, "r2": 22e3,
}


def test_fixed_bias_active():
    r = dc_bias.calculate("fixed", P)
    assert r["ib_uA"] > 0
    assert r["ic_mA"] > 0
    assert r["region"] == "active"


def test_divider_bias_matches_hand_calc():
    r = dc_bias.calculate("divider", P)
    assert abs(r["vth"] - 12 * 22 / 122) < 1e-9
    assert 0.5 < r["vb"] < 3.0
    assert 0.5 < r["ic_mA"] < 3.0


def test_all_modes_return_required_keys():
    for mode in ("fixed", "emitter", "divider"):
        r = dc_bias.calculate(mode, P)
        for key in ("ib_uA", "ic_mA", "vb", "ve", "vc", "vce", "region"):
            assert key in r
