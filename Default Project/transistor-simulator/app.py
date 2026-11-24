"""ENG29 2121 Lab 04 — Flask app: Lab 3 analytical DC bias + real ngspice CE simulator."""
from __future__ import annotations

import os
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request

import dc_bias
import spice_engine

app = Flask(__name__)

DEFAULT_FORM: Dict[str, str] = {
    # CE reference circuit (Lab 4 SPICE)
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "rl": "10",
    "cin": "10", "cout": "10", "bf": "100", "vaf": "100", "isat": "1e-14",
    "amp_mv": "10", "freq_khz": "1",
    # Lab 3 analytical modes
    "b_vcc": "12", "b_beta": "100", "b_vbe": "0.7",
    "b_rb": "470", "b_rc": "2.2", "b_re": "1", "b_r1": "100", "b_r2": "22",
}


def _num(form, key: str, *, positive: bool = False, minimum=None, maximum=None) -> float:
    raw = (form.get(key, "") or "").strip()
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{key} ต้องเป็นตัวเลข (ได้ '{raw}')")
    if positive and value <= 0:
        raise ValueError(f"{key} ต้องมากกว่า 0")
    if minimum is not None and value < minimum:
        raise ValueError(f"{key} ต้อง >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{key} ต้อง <= {maximum}")
    return value


def parse_spice_params(form) -> Dict[str, float]:
    vcc = _num(form, "vcc", positive=True, maximum=100)
    r1 = _num(form, "r1", positive=True) * 1e3
    r2 = _num(form, "r2", positive=True) * 1e3
    rc = _num(form, "rc", positive=True) * 1e3
    re = _num(form, "re", positive=True) * 1e3
    rl = _num(form, "rl", positive=True) * 1e3
    cin = _num(form, "cin", positive=True) * 1e-6
    cout = _num(form, "cout", positive=True) * 1e-6
    bf = _num(form, "bf", positive=True)
    vaf = _num(form, "vaf", minimum=0)
    isat = _num(form, "isat", positive=True)
    amp = _num(form, "amp_mv", minimum=0) / 1e3
    freq = _num(form, "freq_khz", positive=True) * 1e3
    if amp == 0:
        raise ValueError("amp_mv ต้องมากกว่า 0 เพื่อให้เห็นสัญญาณ")
    return {
        "vcc": vcc, "r1": r1, "r2": r2, "rc": rc, "re": re, "rl": rl,
        "cin": cin, "cout": cout, "bf": bf, "vaf": vaf, "isat": isat,
        "amp": amp, "freq": freq,
        "ac_fmin": 0.1, "ac_fmax": 10e6, "ac_per_dec": 20,
        "tran_stop": 3.0 / freq,
    }


def parse_bias_params(form) -> Dict[str, float]:
    return {
        "vcc": _num(form, "b_vcc", positive=True, maximum=100),
        "beta": _num(form, "b_beta", positive=True),
        "vbe": _num(form, "b_vbe", minimum=0.2, maximum=1.5),
        "rb": _num(form, "b_rb", positive=True) * 1e3,
        "rc": _num(form, "b_rc", positive=True) * 1e3,
        "re": _num(form, "b_re", positive=True) * 1e3,
        "r1": _num(form, "b_r1", positive=True) * 1e3,
        "r2": _num(form, "b_r2", positive=True) * 1e3,
    }


def _form_from_request() -> Dict[str, str]:
    return {key: request.form.get(key, default) for key, default in DEFAULT_FORM.items()}


@app.route("/", methods=["GET", "POST"])
def index():
    form = _form_from_request()
    analytical = None
    analytical_mode = None
    spice = None
    error = None
    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action in ("fixed", "emitter", "divider"):
                analytical_mode = action
                analytical = dc_bias.calculate(action, parse_bias_params(form))
            elif action in ("dc", "ac", "tran"):
                spice = spice_engine.run_analysis(parse_spice_params(form), action)
            else:
                raise ValueError("ไม่พบการกระทำที่ระบุในฟอร์ม")
        except Exception as exc:  # engine/input failures must be visible, never silent
            error = str(exc)
    return render_template(
        "index.html", form=form, analytical=analytical,
        analytical_mode=analytical_mode, spice=spice, error=error,
    )


@app.route("/health")
def health():
    try:
        exe = spice_engine.find_ngspice()
        return jsonify({
            "ngspice": True,
            "version": spice_engine.ngspice_version(exe),
            "path": exe,
        })
    except Exception as exc:
        return jsonify({"ngspice": False, "error": str(exc)}), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
