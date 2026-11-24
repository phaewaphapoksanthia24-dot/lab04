"""Lab 3 analytical DC bias calculations (kept separate from SPICE results).

If your Lab 3 project already has a working dc_bias.py, KEEP IT and adapt
app.py's import/call signatures instead of overwriting this file.
"""
from __future__ import annotations

from typing import Any, Dict


def _region(vce: float) -> str:
    if vce < 0.2:
        return "saturation"
    if vce < 1.0:
        return "near saturation"
    return "active"


def fixed_bias(p: Dict[str, float]) -> Dict[str, Any]:
    """RB from VCC to base, emitter at ground."""
    ib = (p["vcc"] - p["vbe"]) / p["rb"]
    ic = p["beta"] * ib
    vb = p["vbe"]
    ve = 0.0
    vc = p["vcc"] - ic * p["rc"]
    vce = vc - ve
    return {"ib_uA": ib * 1e6, "ic_mA": ic * 1e3, "vb": vb,
            "ve": ve, "vc": vc, "vce": vce, "region": _region(vce)}


def emitter_bias(p: Dict[str, float]) -> Dict[str, Any]:
    """RB from VCC to base plus emitter resistor RE."""
    ib = (p["vcc"] - p["vbe"]) / (p["rb"] + (p["beta"] + 1) * p["re"])
    ic = p["beta"] * ib
    ve = (p["beta"] + 1) * ib * p["re"]
    vb = ve + p["vbe"]
    vc = p["vcc"] - ic * p["rc"]
    vce = vc - ve
    return {"ib_uA": ib * 1e6, "ic_mA": ic * 1e3, "vb": vb,
            "ve": ve, "vc": vc, "vce": vce, "region": _region(vce)}


def divider_bias(p: Dict[str, float]) -> Dict[str, Any]:
    """Voltage divider R1/R2 with emitter resistor RE (Thevenin form)."""
    vth = p["vcc"] * p["r2"] / (p["r1"] + p["r2"])
    rth = p["r1"] * p["r2"] / (p["r1"] + p["r2"])
    if vth <= p["vbe"]:
        return {"ib_uA": 0.0, "ic_mA": 0.0, "vb": 0.0, "ve": 0.0,
                "vc": p["vcc"], "vce": p["vcc"], "region": "cutoff",
                "vth": vth, "rth_kohm": rth / 1e3}
    ib = (vth - p["vbe"]) / (rth + (p["beta"] + 1) * p["re"])
    ic = p["beta"] * ib
    ve = (p["beta"] + 1) * ib * p["re"]
    vb = ve + p["vbe"]
    vc = p["vcc"] - ic * p["rc"]
    vce = vc - ve
    result = {"ib_uA": ib * 1e6, "ic_mA": ic * 1e3, "vb": vb,
              "ve": ve, "vc": vc, "vce": vce, "region": _region(vce)}
    result.update({"vth": vth, "rth_kohm": rth / 1e3})
    return result


def calculate(mode: str, p: Dict[str, float]) -> Dict[str, Any]:
    modes = {
        "fixed": fixed_bias,
        "emitter": emitter_bias,
        "divider": divider_bias,
    }
    if mode not in modes:
        raise ValueError(f"Unknown analytical bias mode: {mode}")
    return modes[mode](p)
