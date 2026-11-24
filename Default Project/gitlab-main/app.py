import math

from flask import Flask, jsonify, render_template, request

import spice_engine
from bias import (
    MODE_DIVIDER,
    MODE_EMITTER,
    MODE_FIELDS,
    MODE_FIXED,
    MODES,
    W_CUTOFF,
    W_FORWARD_ACTIVE,
    W_SAT,
    BiasInputError,
    analyze_mode,
    parse_mode_inputs,
)

app = Flask(__name__)

MODE_LABELS = {
    MODE_DIVIDER: "Voltage Divider Bias",
    MODE_FIXED: "Fixed Bias",
    MODE_EMITTER: "Emitter Bias",
}

DEFAULT_VALUES = {
    MODE_DIVIDER: {
        "vcc": "12.0",
        "r1": "100",
        "r2": "22",
        "rc": "2.2",
        "re": "1.0",
        "beta": "100",
        "vbe": "0.70",
    },
    MODE_FIXED: {
        "vcc": "12.0",
        "rc": "2.2",
        "rb": "1000",
        "beta": "100",
        "vbe": "0.70",
    },
    MODE_EMITTER: {
        "vcc": "12.0",
        "rc": "2.2",
        "rb": "1000",
        "re": "1.0",
        "beta": "100",
        "vbe": "0.70",
    },
}

DEFAULT_UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "rb": "kΩ",
    "beta": "",
    "vbe": "V",
}

FIELD_DEFS = {
    "vcc": {"name": "vcc", "label": "VCC", "hint": "Supply Voltage", "units": ("V", "mV")},
    "r1": {"name": "r1", "label": "R1", "hint": "Upper Divider", "units": ("Ω", "kΩ", "MΩ")},
    "r2": {"name": "r2", "label": "R2", "hint": "Lower Divider", "units": ("Ω", "kΩ", "MΩ")},
    "rc": {"name": "rc", "label": "RC", "hint": "Collector Resistor", "units": ("Ω", "kΩ", "MΩ")},
    "re": {"name": "re", "label": "RE", "hint": "Emitter Resistor", "units": ("Ω", "kΩ", "MΩ")},
    "rb": {"name": "rb", "label": "RB", "hint": "Base Resistor", "units": ("Ω", "kΩ", "MΩ")},
    "beta": {"name": "beta", "label": "β", "hint": "Current Gain", "units": ()},
    "vbe": {"name": "vbe", "label": "VBE", "hint": "Base-Emitter Voltage", "units": ("V", "mV")},
}


# ---------------------------------------------------------------------------
# Lab 04 — CE voltage-divider SPICE simulator (additive; Lab 03 routes intact)
# ---------------------------------------------------------------------------

LAB4_MODE_DC = "dc"
LAB4_MODE_AC = "ac"
LAB4_MODE_TRAN = "tran"
LAB4_MODES = (LAB4_MODE_DC, LAB4_MODE_AC, LAB4_MODE_TRAN)
LAB4_MODE_LABELS = {
    LAB4_MODE_DC: "DC operating point (.op)",
    LAB4_MODE_AC: "AC frequency response (.ac)",
    LAB4_MODE_TRAN: "Transient waveform (.tran)",
}

LAB4_DEFAULTS = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "rl": "10",
    "cin": "10", "cout": "10", "bf": "100", "vaf": "100", "isat": "1e-14",
    "amp": "10", "freq": "1", "ac_fmin": "0.1", "ac_fmax": "10",
    "tran_cycles": "3", "model_name": "QNPN", "model_params": "",
}
LAB4_UNITS = {
    "vcc": "V", "r1": "kΩ", "r2": "kΩ", "rc": "kΩ", "re": "kΩ", "rl": "kΩ",
    "cin": "µF", "cout": "µF", "bf": "", "vaf": "V", "isat": "A",
    "amp": "mV", "freq": "kHz", "ac_fmin": "Hz", "ac_fmax": "MHz",
    "tran_cycles": "", "model_name": "", "model_params": "",
}
LAB4_FIELDS = (
    {"name": "vcc", "label": "VCC", "hint": "Supply", "units": ("V", "mV")},
    {"name": "r1", "label": "R1", "hint": "Upper divider", "units": ("Ω", "kΩ", "MΩ")},
    {"name": "r2", "label": "R2", "hint": "Lower divider", "units": ("Ω", "kΩ", "MΩ")},
    {"name": "rc", "label": "RC", "hint": "Collector", "units": ("Ω", "kΩ", "MΩ")},
    {"name": "re", "label": "RE", "hint": "Emitter", "units": ("Ω", "kΩ", "MΩ")},
    {"name": "rl", "label": "RL", "hint": "Load on OUT", "units": ("Ω", "kΩ", "MΩ")},
    {"name": "cin", "label": "Cin", "hint": "Input coupling", "units": ("pF", "nF", "µF")},
    {"name": "cout", "label": "Cout", "hint": "Output coupling", "units": ("pF", "nF", "µF")},
    {"name": "bf", "label": "BF (β)", "hint": "Simple BJT model", "units": ()},
    {"name": "vaf", "label": "VAF", "hint": "Early voltage", "units": ("V",) },
    {"name": "isat", "label": "IS", "hint": "Saturation current", "units": ("A", "µA", "nA")},
    {"name": "amp", "label": "Vin peak", "hint": "SIN amplitude", "units": ("mV", "V")},
    {"name": "freq", "label": "Freq", "hint": "Source frequency", "units": ("Hz", "kHz", "MHz")},
    {"name": "ac_fmin", "label": "AC fmin", "hint": "Sweep start", "units": ("Hz", "kHz")},
    {"name": "ac_fmax", "label": "AC fmax", "hint": "Sweep stop", "units": ("kHz", "MHz", "GHz")},
    {"name": "tran_cycles", "label": "Cycles", "hint": "Time window", "units": ()},
    {"name": "model_name", "label": "Model", "hint": "From starter kit", "units": ()},
    {"name": "model_params", "label": "Model params", "hint": "Inside NPN(...)", "units": ()},
)
LAB4_FIELD_NAMES = tuple(field["name"] for field in LAB4_FIELDS)

LAB4_UNIT_FACTORS = {
    "vcc": {"V": 1.0, "mV": 1e-3},
    "r1": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "r2": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "rc": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "re": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "rl": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "cin": {"pF": 1e-12, "nF": 1e-9, "µF": 1e-6, "uF": 1e-6},
    "cout": {"pF": 1e-12, "nF": 1e-9, "µF": 1e-6, "uF": 1e-6},
    "bf": {}, "vaf": {"V": 1.0},
    "isat": {"A": 1.0, "µA": 1e-6, "uA": 1e-6, "nA": 1e-9},
    "amp": {"mV": 1e-3, "V": 1.0},
    "freq": {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6},
    "ac_fmin": {"Hz": 1.0, "kHz": 1e3},
    "ac_fmax": {"kHz": 1e3, "MHz": 1e6, "GHz": 1e9},
    "tran_cycles": {},
    "model_name": {}, "model_params": {},
}


def fields_for_mode(mode):
    return tuple(FIELD_DEFS[field] for field in MODE_FIELDS[mode])

RESULT_ROWS = (
    ("VB", "vb"),
    ("VE", "ve"),
    ("VC", "vc"),
    ("VCE", "vce"),
    ("IB", "ib"),
    ("IC", "ic"),
    ("IE", "ie"),
)

COMPARISON_ROWS = (
    ("VB", "V", "vb", 1.0, "{:.2f}"),
    ("VE", "V", "ve", 1.0, "{:.2f}"),
    ("VC", "V", "vc", 1.0, "{:.2f}"),
    ("VCE", "V", "vce", 1.0, "{:.2f}"),
    ("IB", "µA", "ib", 1e6, "{:.1f}"),
    ("IC", "mA", "ic", 1e3, "{:.2f}"),
    ("IE", "mA", "ie", 1e3, "{:.2f}"),
)


def format_value(attribute, value):
    if attribute in ("vb", "ve", "vc", "vce"):
        return f"{value:.2f} V"
    if attribute == "ib":
        return f"{value * 1e6:.1f} µA"
    return f"{value * 1e3:.2f} mA"


def build_result_rows(result):
    return [
        {"label": label, "value": format_value(attribute, getattr(result.primary, attribute))}
        for label, attribute in RESULT_ROWS
    ]


def build_comparison_rows(result):
    rows = []
    for label, unit, attribute, scale, number_format in COMPARISON_ROWS:
        primary = getattr(result.primary, attribute) * scale
        nodal = getattr(result.independent, attribute) * scale
        if math.isclose(primary, nodal, rel_tol=1e-9, abs_tol=1e-9):
            delta = "0"
        else:
            delta = f"{abs(primary - nodal):.2g}"
        rows.append(
            {
                "label": label,
                "unit": unit,
                "thevenin": number_format.format(primary),
                "nodal": number_format.format(nodal),
                "delta": delta,
            }
        )
    return rows


def region_info(result):
    vce = result.primary.vce
    if W_FORWARD_ACTIVE in result.warnings:
        return {
            "kind": "warn",
            "title": "Forward Active model may not apply",
            "detail": (
                f"IB = {result.primary.ib * 1e6:.1f} µA and VCE = {vce:.2f} V; "
                "the values come from the active-region equations and are only approximate."
            ),
        }
    if result.region == "active":
        return {
            "kind": "ok",
            "title": "Active region approximation OK",
            "detail": f"VCE = {vce:.2f} V > 0.2 V (transistor in active region)",
        }
    if result.region == "saturation":
        return {
            "kind": "warn",
            "title": "Saturation region",
            "detail": f"VCE = {vce:.2f} V ≤ 0.2 V — active-region values are approximate",
        }
    return {
        "kind": "off",
        "title": "Cutoff region",
        "detail": "VBB ≤ VBE — the transistor is off and no collector current flows",
    }


def schematic_labels(values, units):
    labels = {}
    for field in values:
        value = (values.get(field) or "").strip()
        unit = (units.get(field) or "").strip()
        labels[field] = f"{value} {unit}".strip() if value else "—"
    return labels


LAB4_ERROR_EMPTY = "This field is required."
LAB4_ERROR_NUMBER = "Enter a number."
LAB4_ERROR_FINITE = "Enter a finite number."
LAB4_ERROR_POSITIVE = "Must be greater than 0."


def parse_lab4_params(raw):
    """Validate every CE field before a netlist is built (never pass raw form data)."""
    errors = {}
    values = {}
    for field in LAB4_FIELD_NAMES:
        text = (raw.get(field) or "").strip()
        if not text:
            # Instructor model text is optional: an empty value means "use the
            # simple BF/VAF/IS model from the other form fields".
            if field == "model_params":
                values[field] = ""
                continue
            errors[field] = LAB4_ERROR_EMPTY
            continue
        if field == "model_name":
            if not spice_engine.SAFE_MODEL_NAME.match(text):
                errors[field] = "Use SPICE name characters A-Z, 0-9, _."
            else:
                values[field] = text
            continue
        if field == "model_params":
            if text and not spice_engine.SAFE_MODEL_PARAMS.match(text):
                errors[field] = "Contains characters not allowed in a netlist."
            else:
                values[field] = text
            continue
        try:
            number = float(text)
        except ValueError:
            errors[field] = LAB4_ERROR_NUMBER
            continue
        if not math.isfinite(number):
            errors[field] = LAB4_ERROR_FINITE
            continue
        values[field] = number * LAB4_UNIT_FACTORS[field].get(
            raw.get(f"{field}_unit", ""), 1.0
        )

    for field in ("vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout", "bf",
                  "isat", "amp", "freq", "ac_fmin", "ac_fmax"):
        if field in values and values[field] <= 0:
            errors[field] = LAB4_ERROR_POSITIVE
    if "vaf" in values and values["vaf"] < 0:
        errors["vaf"] = "Must be 0 or more."
    if "vcc" in values and values["vcc"] > 100:
        errors["vcc"] = "VCC must be <= 100 V."
    if "ac_fmax" in values and "ac_fmin" in values:
        if values["ac_fmax"] <= values["ac_fmin"]:
            errors["ac_fmax"] = "Must be greater than AC fmin."
        elif values["ac_fmax"] > 1e9:
            errors["ac_fmax"] = "AC fmax must be <= 1 GHz."
    if "tran_cycles" in values:
        if values["tran_cycles"] < 1 or values["tran_cycles"] > 20:
            errors["tran_cycles"] = "Use 1–20 cycles."

    if errors:
        raise BiasInputError(errors)

    return {
        "vcc": values["vcc"], "r1": values["r1"], "r2": values["r2"],
        "rc": values["rc"], "re": values["re"], "rl": values["rl"],
        "cin": values["cin"], "cout": values["cout"], "bf": values["bf"],
        "vaf": values["vaf"], "isat": values["isat"], "amp": values["amp"],
        "freq": values["freq"], "ac_fmin": values["ac_fmin"],
        "ac_fmax": values["ac_fmax"], "ac_per_dec": 20,
        "tran_stop": values["tran_cycles"] / values["freq"],
        "model_name": values["model_name"],
        "model_params": values["model_params"],
    }


def render_lab4(values, units, mode=LAB4_MODE_DC, sim=None, errors=None, engine_error=None):
    return render_template(
        "lab4.html",
        fields=LAB4_FIELDS,
        values=values,
        units=units,
        mode=mode,
        mode_labels=LAB4_MODE_LABELS,
        sim=sim,
        errors=errors or {},
        engine_error=engine_error,
        schematic=schematic_labels(values, units),
    )


def render_page(
    values,
    units,
    mode=MODE_DIVIDER,
    mode_error=None,
    errors=None,
    result=None,
    warnings=(),
):
    return render_template(
        "index.html",
        values=values,
        units=units,
        mode=mode,
        mode_label=MODE_LABELS[mode],
        mode_labels=MODE_LABELS,
        mode_error=mode_error,
        errors=errors or {},
        fields=fields_for_mode(mode),
        result=result,
        rows=build_result_rows(result) if result else [],
        comparison=build_comparison_rows(result) if result and result.independent else [],
        region=region_info(result) if result else None,
        warnings=list(warnings),
        schematic=schematic_labels(values, units),
    )


@app.get("/")
def index():
    mode = request.args.get("mode", MODE_DIVIDER)
    mode_error = None
    if mode not in MODES:
        mode_error = "Choose a valid bias mode."
        mode = MODE_DIVIDER
    return render_page(
        DEFAULT_VALUES[mode], DEFAULT_UNITS, mode=mode, mode_error=mode_error
    )


@app.post("/calculate")
def calculate():
    mode = request.form.get("mode", MODE_DIVIDER)
    if mode not in MODES:
        return render_page(
            DEFAULT_VALUES[MODE_DIVIDER],
            DEFAULT_UNITS,
            mode=MODE_DIVIDER,
            mode_error="Choose a valid bias mode.",
        )

    fields = MODE_FIELDS[mode]
    values = {field: request.form.get(field, "") for field in fields}
    units = {field: request.form.get(f"{field}_unit", "") for field in fields}
    raw = dict(values)
    raw.update({f"{field}_unit": units[field] for field in fields})

    try:
        data = parse_mode_inputs(raw, mode)
    except BiasInputError as error:
        return render_page(values, units, mode=mode, errors=error.errors)

    result = analyze_mode(data)
    extra_warnings = [
        w for w in result.warnings if w not in (W_CUTOFF, W_SAT, W_FORWARD_ACTIVE)
    ]
    return render_page(values, units, mode=mode, result=result, warnings=extra_warnings)


@app.get("/lab4")
def lab4_index():
    return render_lab4(LAB4_DEFAULTS, LAB4_UNITS)


@app.post("/lab4/run")
def lab4_run():
    mode = request.form.get("analysis", LAB4_MODE_DC)
    if mode not in LAB4_MODES:
        mode = LAB4_MODE_DC
    values = {field: request.form.get(field, "") for field in LAB4_FIELD_NAMES}
    units = {
        field: request.form.get(f"{field}_unit", "")
        for field in LAB4_FIELD_NAMES
    }
    raw = dict(values)
    raw.update({f"{field}_unit": units[field] for field in LAB4_FIELD_NAMES})
    try:
        params = parse_lab4_params(raw)
        sim = spice_engine.run_analysis(params, mode)
    except BiasInputError as error:
        return render_lab4(values, units, mode=mode, errors=error.errors)
    except spice_engine.SpiceError as error:
        return render_lab4(values, units, mode=mode, engine_error=str(error))
    except Exception as error:  # engine/input failures are visible, never silent
        return render_lab4(values, units, mode=mode, engine_error=str(error))
    return render_lab4(values, units, mode=mode, sim=sim)


@app.get("/health")
def health():
    try:
        exe = spice_engine.find_ngspice()
        return jsonify({
            "ngspice": True,
            "version": spice_engine.ngspice_version(exe),
            "path": exe,
        })
    except spice_engine.SpiceError as error:
        return jsonify({"ngspice": False, "error": str(error)}), 503


if __name__ == "__main__":
    app.run(debug=False, port=5000)
