"""ngspice adapter for the Lab 04 CE voltage-divider reference circuit.

This is the ONLY module that talks to the external solver.  It builds a
netlist from validated parameters, runs ngspice in batch mode with
``subprocess.run([...])``, parses the real output and never returns a
fabricated result.  Analytical Lab 03 results live in ``bias.py`` and stay
separate.
"""
from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List


class SpiceError(RuntimeError):
    """Raised when ngspice is missing, fails, times out or yields no data."""


def fmt(x: float) -> str:
    return f"{float(x):.8g}"


def find_ngspice() -> str:
    exe = os.environ.get("NGSPICE_EXE") or shutil.which("ngspice")
    if not exe:
        raise SpiceError(
            "ไม่พบ ngspice ใน PATH — ติดตั้ง ngspice แล้วตรวจด้วยคำสั่ง "
            "`ngspice --version` หรือตั้ง Environment variable NGSPICE_EXE"
        )
    return exe


def ngspice_version(exe: str) -> str:
    try:
        proc = subprocess.run(
            [exe, "--version"], capture_output=True, text=True,
            timeout=10, shell=False, check=False,
        )
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        match = re.search(r"ngspice[- ]?([0-9][^\s,]*)", text, re.I)
        return match.group(1) if match else "unknown (ตรวจด้วย ngspice --version)"
    except Exception:
        return "unknown"


SAFE_MODEL_NAME = re.compile(r"^[A-Za-z0-9_]+$")
SAFE_MODEL_PARAMS = re.compile(r"^[A-Za-z0-9_.=()+\- \t,]+$")


def model_text(p: Dict[str, float]) -> str:
    """Return the validated .model line body (without the .model directive)."""
    name = str(p.get("model_name", "QNPN")).strip()
    if not SAFE_MODEL_NAME.match(name):
        raise SpiceError("model_name ต้องเป็นชื่อ SPICE เช่น QNPN หรือ 2N2222 (A-Z, 0-9, _)")
    params = str(p.get("model_params", "")).strip()
    if not params:
        params = f"BF={fmt(p['bf'])} VAF={fmt(p['vaf'])} IS={fmt(p['isat'])}"
    if not SAFE_MODEL_PARAMS.match(params):
        raise SpiceError("model_params มีอักขระที่ไม่ปลอดภัยสำหรับ netlist")
    return f"{name} NPN({params})", name


def build_netlist(p: Dict[str, float], mode: str) -> str:
    """Build one netlist for one analysis mode."""
    model_line, model_name = model_text(p)
    lines = [
        "* ENG29 2121 Lab 04 - CE voltage-divider reference circuit",
        "* Results must come from a real ngspice batch run.",
        f"VCC VCC 0 DC {fmt(p['vcc'])}",
        f"VIN IN 0 AC 1 SIN(0 {fmt(p['amp'])} {fmt(p['freq'])})",
        f"R1 VCC BASE {fmt(p['r1'])}",
        f"R2 BASE 0 {fmt(p['r2'])}",
        f"RC VCC COLL {fmt(p['rc'])}",
        f"RE EMIT 0 {fmt(p['re'])}",
        f"RL OUT 0 {fmt(p['rl'])}",
        f"CIN IN BASE {fmt(p['cin'])}",
        f"COUT COLL OUT {fmt(p['cout'])}",
        f"Q1 COLL BASE EMIT {model_name}",
        f".model {model_line}",
    ]
    if mode == "dc":
        lines.append(".op")
    elif mode == "ac":
        lines.append(
            f".ac dec {int(p['ac_per_dec'])} {fmt(p['ac_fmin'])} {fmt(p['ac_fmax'])}"
        )
        # Gain/phase reference is v(base), i.e. after Cin on RL side.
        # ngspice 41 silently truncates a 4-expression .print line to the
        # first two expressions, so emit two separate tables and pair them.
        lines.append(".print ac vdb(out) vp(out)")
        lines.append(".print ac vdb(base) vp(base)")
    elif mode == "tran":
        step = float(p["tran_stop"]) / 1000.0
        lines.append(f".tran {fmt(step)} {fmt(p['tran_stop'])}")
        lines.append(".print tran v(base) v(out)")
    else:
        raise SpiceError(f"Unknown analysis mode: {mode}")
    lines.append(".end")
    return "\n".join(lines) + "\n"


def _log_text(log_path: str, proc: subprocess.CompletedProcess) -> str:
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    return (proc.stdout or "") + "\n" + (proc.stderr or "")


def _guard(log: str, proc: subprocess.CompletedProcess) -> None:
    if proc.returncode != 0:
        raise SpiceError(f"ngspice ออกด้วยสถานะ {proc.returncode}: " + log[-1200:])
    lowered = log.lower()
    for marker in ("fatal error", "error:", "unrecognized", "no such file", "syntax error"):
        if marker in lowered:
            raise SpiceError("ngspice รายงานข้อผิดพลาด: " + log[-1200:])


def _numeric_rows(log: str, ncols: int) -> List[List[float]]:
    """Parse SPICE .print tables whose first token is an integer index."""
    rows: List[List[float]] = []
    for line in log.splitlines():
        parts = line.split()
        if len(parts) < ncols + 1 or not re.fullmatch(r"\d+", parts[0]):
            continue
        values: List[float] = []
        try:
            for token in parts[1:ncols + 1]:
                values.append(float(token))
        except ValueError:
            continue
        if len(values) == ncols:
            rows.append(values)
    return rows


def parse_op(log: str, p: Dict[str, float]) -> Dict[str, Any]:
    nodes: Dict[str, float] = {}
    pattern = re.compile(
        r"^\s*v\(([A-Za-z0-9_]+)\)\s*=\s*([-+0-9.eE]+)", re.I | re.M
    )
    for match in pattern.finditer(log):
        try:
            nodes[match.group(1).lower()] = float(match.group(2))
        except ValueError:
            pass
    # Some ngspice builds print a plain two-column node table instead of
    # "v(node) = ..."; accept that format too before declaring failure.
    if any(node not in nodes for node in ("base", "emit", "coll")):
        for line in log.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            name = parts[0].lower()
            if name.startswith("v(") and name.endswith(")"):
                name = name[2:-1]
            if name not in ("base", "emit", "coll"):
                continue
            try:
                nodes[name] = float(parts[1])
            except ValueError:
                continue
    needed = ("base", "emit", "coll")
    if any(node not in nodes for node in needed):
        raise SpiceError("ไม่พบ node voltage จาก .op ใน ngspice log — ตรวจ netlist/engine")
    vb, ve, vc = nodes["base"], nodes["emit"], nodes["coll"]
    ic_ma = (p["vcc"] - vc) / p["rc"] * 1e3
    ib_ua = ((p["vcc"] - vb) / p["r1"] - vb / p["r2"]) * 1e6
    vce = vc - ve
    if vce < 0.2:
        region = "saturation"
    elif vce < 1.0:
        region = "near saturation"
    else:
        region = "active"
    return {
        "vb": vb, "ve": ve, "vc": vc, "vce": vce,
        "ic_ma": ic_ma, "ib_ua": ib_ua, "region": region,
        "vth": p["vcc"] * p["r2"] / (p["r1"] + p["r2"]),
        "rth_kohm": (p["r1"] * p["r2"] / (p["r1"] + p["r2"])) / 1e3,
    }


def _wrap_phase(deg: float) -> float:
    while deg > 180:
        deg -= 360
    while deg < -180:
        deg += 360
    return deg


def _ac_pair_tables(log: str) -> Dict[str, List[List[float]]]:
    """Read the two .print ac tables emitted by ngspice 41."""
    tables: Dict[str, List[List[float]]] = {"out": [], "base": []}
    current = None
    for line in log.splitlines():
        low = line.lower()
        if "vdb(out)" in low:
            current = "out"
            continue
        if "vdb(base)" in low:
            current = "base"
            continue
        if current is None:
            continue
        parts = line.split()
        if len(parts) < 4 or not re.fullmatch(r"\d+", parts[0]):
            continue
        try:
            tables[current].append([float(token) for token in parts[1:4]])
        except ValueError:
            continue
    return tables


def parse_ac(log: str) -> Dict[str, Any]:
    # Older ngspice builds accept all four expressions in one .print line.
    combined = _numeric_rows(log, 5)
    if len(combined) >= 3:
        freq = [row[0] for row in combined]
        out_db = [row[1] for row in combined]
        out_phase = [row[2] for row in combined]
        base_db = [row[3] for row in combined]
        base_phase = [row[4] for row in combined]
    else:
        tables = _ac_pair_tables(log)
        if len(tables["out"]) < 3:
            raise SpiceError("ngspice .ac ไม่มีตารางข้อมูล — ตรวจ .print ac ใน netlist")
        if tables["base"] and len(tables["base"]) != len(tables["out"]):
            raise SpiceError("ngspice .ac ตาราง v(out)/v(base) ไม่ตรงกัน — ตรวจ netlist")
        freq = [row[0] for row in tables["out"]]
        out_db = [row[1] for row in tables["out"]]
        out_phase = [row[2] for row in tables["out"]]
        base_db = (
            [row[1] for row in tables["base"]] if tables["base"]
            else [0.0] * len(freq)
        )
        base_phase = (
            [row[2] for row in tables["base"]] if tables["base"]
            else [0.0] * len(freq)
        )
    gain = [o - b for o, b in zip(out_db, base_db)]
    phase = [_wrap_phase(o - b) for o, b in zip(out_phase, base_phase)]
    peak = max(gain)
    threshold = peak - 20 * math.log10(math.sqrt(2))
    passing = [index for index, value in enumerate(gain) if value >= threshold]
    f_low = freq[passing[0]] if passing and passing[0] != 0 else None
    f_high = freq[passing[-1]] if passing and passing[-1] != len(freq) - 1 else None
    return {
        "frequency_hz": freq, "gain_db": gain, "phase_deg": phase,
        "midband_gain_db": peak, "f_low_hz": f_low, "f_high_hz": f_high,
        "points": len(freq),
    }


def _fundamental_phase(t_sec: List[float], v: List[float], f: float) -> float:
    cosine = sum(vi * math.cos(2 * math.pi * f * ti) for ti, vi in zip(t_sec, v))
    sine = sum(vi * math.sin(2 * math.pi * f * ti) for ti, vi in zip(t_sec, v))
    # v = A sin(wt + phi): cosine ~ A sin(phi), sine ~ A cos(phi)
    return math.degrees(math.atan2(cosine, sine))


def parse_tran(log: str, p: Dict[str, float]) -> Dict[str, Any]:
    rows = _numeric_rows(log, 3)
    if len(rows) < 10:
        raise SpiceError("ngspice .tran ไม่มีตารางข้อมูล — ตรวจ .print tran ใน netlist")
    t = [row[0] for row in rows]
    vin_raw = [row[1] for row in rows]
    vout_raw = [row[2] for row in rows]
    # v(base) sits at a ~1.9 V DC bias; v(out) is AC-coupled to 0 V DC.
    # Measure the AC component only, otherwise gain is measured against the
    # bias voltage instead of the 10 mV input signal.
    vin_dc = sum(vin_raw) / len(vin_raw)
    vout_dc = sum(vout_raw) / len(vout_raw)
    vin = [x - vin_dc for x in vin_raw]
    vout = [x - vout_dc for x in vout_raw]
    vin_pk = max(abs(x) for x in vin)
    vout_pk = max(abs(x) for x in vout)
    if vin_pk <= 0:
        raise SpiceError("Transient input เป็นศูนย์ — ตรวจ amplitude ของแหล่งสัญญาณ")
    phase = _wrap_phase(
        _fundamental_phase(t, vin, p["freq"]) -
        _fundamental_phase(t, vout, p["freq"])
    )
    return {
        "time_ms": [x * 1e3 for x in t],
        "vin_mv": [x * 1e3 for x in vin],
        "vout_mv": [x * 1e3 for x in vout],
        "vin_peak_mv": vin_pk * 1e3,
        "vout_peak_mv": vout_pk * 1e3,
        "gain_db": 20 * math.log10(max(vout_pk, 1e-15) / vin_pk),
        "phase_deg": phase,
        "relationship": "inverting (~180°)" if abs(phase) > 90 else "non-inverting",
        "points": len(t),
    }


def run_analysis(p: Dict[str, float], mode: str, timeout: int = 90) -> Dict[str, Any]:
    """Run one real ngspice analysis and return parsed, unit-tagged data."""
    exe = find_ngspice()
    version = ngspice_version(exe)
    netlist = build_netlist(p, mode)
    with tempfile.TemporaryDirectory(prefix="lab04_ngspice_") as workdir:
        cir = os.path.join(workdir, "circuit.cir")
        log_path = os.path.join(workdir, "run.log")
        with open(cir, "w", encoding="utf-8") as handle:
            handle.write(netlist)
        # Do NOT pass -r: raw-file mode makes ngspice 41 skip the textual
        # .print/.op tables that this adapter parses from the batch log.
        command = [exe, "-b", "-o", log_path, cir]
        try:
            proc = subprocess.run(
                command, cwd=workdir, capture_output=True, text=True,
                timeout=timeout, shell=False, check=False,
            )
        except subprocess.TimeoutExpired:
            raise SpiceError(
                f"ngspice timeout หลัง {timeout} วินาที — ปรับ .tran/.ac ให้สั้นลง"
            )
        except FileNotFoundError:
            raise SpiceError("ไม่พบ ngspice executable — ตรวจ PATH หรือ NGSPICE_EXE")
        log = _log_text(log_path, proc)
        _guard(log, proc)
        if mode == "dc":
            data = parse_op(log, p)
        elif mode == "ac":
            data = parse_ac(log)
        else:
            data = parse_tran(log, p)
    model_line, _ = model_text(p)
    return {
        "engine": "ngspice",
        "version": version,
        "status": "success",
        "mode": mode,
        "model": f".model {model_line}",
        "model_source": "instructor" if str(p.get("model_params", "")).strip() else "demo",
        "netlist": netlist,
        "log_excerpt": log[-5000:],
        "data": data,
        "reference": (
            "DC: v(base)/v(emit)/v(coll) from .op | "
            "AC: v(out)/v(base) after Cin | "
            "TRAN: v(out) vs v(base), SIN source"
        ),
        "provenance": "ngspice batch run (subprocess) — ไม่ใช่ค่าที่คำนวณใน Browser",
    }
