"""ngspice adapter for the Lab 04 CE voltage-divider reference circuit.

This module is the ONLY place that talks to the external solver.
It builds a netlist, runs ngspice in batch mode with subprocess.run(list),
parses the real output, and never returns a fabricated result.
"""
from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional


class SpiceError(RuntimeError):
    """Raised when ngspice is missing, fails, times out, or yields no data."""


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
        m = re.search(r"ngspice\s+([0-9][^\s,]*)", text, re.I)
        return m.group(1) if m else "unknown (ตรวจด้วย ngspice --version)"
    except Exception:
        return "unknown"


def build_netlist(p: Dict[str, float], mode: str) -> str:
    """Build one netlist for one analysis mode."""
    lines = [
        "* ENG29 2121 Lab 04 — CE voltage-divider reference circuit",
        "* ผลทั้งหมดมาจาก ngspice จริง — ห้ามแทนที่ด้วยค่าคงที่",
        f"VCC VCC 0 DC {fmt(p['vcc'])}",
        f"VIN IN 0 AC 1 SIN(0 {fmt(p['amp'])} {fmt(p['freq'])})",
        f"R1 VCC BASE {fmt(p['r1'])}",
        f"R2 BASE 0 {fmt(p['r2'])}",
        f"RC VCC COLL {fmt(p['rc'])}",
        f"RE EMIT 0 {fmt(p['re'])}",
        f"RL OUT 0 {fmt(p['rl'])}",
        f"CIN IN BASE {fmt(p['cin'])}",
        f"COUT COLL OUT {fmt(p['cout'])}",
        "Q1 COLL BASE EMIT QNPN",
        f".model QNPN NPN(BF={fmt(p['bf'])} VAF={fmt(p['vaf'])} IS={fmt(p['isat'])})",
    ]
    if mode == "dc":
        lines.append(".op")
    elif mode == "ac":
        lines.append(f".ac dec {int(p['ac_per_dec'])} {fmt(p['ac_fmin'])} {fmt(p['ac_fmax'])}")
        # Gain/phase are measured from BASE (after Cin) to OUT (on RL).
        lines.append(".print ac vdb(out) vp(out) vdb(base) vp(base)")
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
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    return (proc.stdout or "") + "\n" + (proc.stderr or "")


def _guard(log: str, proc: subprocess.CompletedProcess) -> None:
    if proc.returncode != 0:
        raise SpiceError(
            f"ngspice ออกด้วยสถานะ {proc.returncode}: "
            + log[-1200:]
        )
    lowered = log.lower()
    for marker in ("fatal error", "error:", "unrecognized", "no such file", "syntax error"):
        if marker in lowered:
            raise SpiceError("ngspice รายงานข้อผิดพลาด: " + log[-1200:])


def _numeric_rows(log: str, ncols: int) -> List[List[float]]:
    """Parse SPICE .print tables: first token is an integer index."""
    rows: List[List[float]] = []
    for line in log.splitlines():
        parts = line.split()
        if len(parts) < ncols + 1 or not re.fullmatch(r"\d+", parts[0]):
            continue
        vals: List[float] = []
        try:
            for token in parts[1:ncols + 1]:
                vals.append(float(token))
        except ValueError:
            continue
        if len(vals) == ncols:
            rows.append(vals)
    return rows


def parse_op(log: str, p: Dict[str, float]) -> Dict[str, Any]:
    nodes: Dict[str, float] = {}
    pattern = re.compile(r"^\s*v\(([A-Za-z0-9_]+)\)\s*=\s*([-+0-9.eE]+)", re.I | re.M)
    for m in pattern.finditer(log):
        try:
            nodes[m.group(1).lower()] = float(m.group(2))
        except ValueError:
            pass
    needed = ("base", "emit", "coll")
    if any(n not in nodes for n in needed):
        raise SpiceError("ไม่พบ node voltage จาก .op ใน ngspice log — ตรวจ netlist/engine")
    vb, ve, vc = nodes["base"], nodes["emit"], nodes["coll"]
    ic_ma = (p["vcc"] - vc) / p["rc"] * 1e3
    ib_ua = ((p["vcc"] - vb) / p["r1"] - vb / p["r2"]) * 1e6
    vce = vc - ve
    region = "active" if vce > 1.0 else ("near saturation" if vce > 0.2 else "saturation")
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


def parse_ac(log: str) -> Dict[str, Any]:
    rows = _numeric_rows(log, 5)  # index, freq, vdb(out), vp(out), vdb(base), vp(base)
    if len(rows) < 3:
        raise SpiceError("ngspice .ac ไม่มีตารางข้อมูล — ตรวจ .print ac ใน netlist")
    freq = [r[0] for r in rows]
    gain = [r[1] - r[3] for r in rows]          # Vout/Vin at base
    phase = [_wrap_phase(r[2] - r[4]) for r in rows]
    peak = max(gain)
    threshold = peak - 20 * math.log10(math.sqrt(2))
    passing = [f for f, g in zip(freq, gain) if g >= threshold]
    f_low = passing[0] if passing and freq.index(passing[0]) != 0 else None
    f_high = passing[-1] if passing and freq.index(passing[-1]) != len(freq) - 1 else None
    return {
        "frequency_hz": freq, "gain_db": gain, "phase_deg": phase,
        "midband_gain_db": peak, "f_low_hz": f_low, "f_high_hz": f_high,
        "points": len(freq),
    }


def _fundamental_phase(t_sec: List[float], v: List[float], f: float) -> float:
    c = sum(vi * math.cos(2 * math.pi * f * ti) for ti, vi in zip(t_sec, v))
    s = sum(vi * math.sin(2 * math.pi * f * ti) for ti, vi in zip(t_sec, v))
    # v(t) = A sin(wt + phi) -> c ~ A sin(phi), s ~ A cos(phi)
    return math.degrees(math.atan2(c, s))


def parse_tran(log: str, p: Dict[str, float]) -> Dict[str, Any]:
    rows = _numeric_rows(log, 3)  # index, time, v(base), v(out)
    if len(rows) < 10:
        raise SpiceError("ngspice .tran ไม่มีตารางข้อมูล — ตรวจ .print tran ใน netlist")
    t = [r[0] for r in rows]
    vin = [r[1] for r in rows]
    vout = [r[2] for r in rows]
    vin_pk = max(abs(x) for x in vin)
    vout_pk = max(abs(x) for x in vout)
    phase = _wrap_phase(_fundamental_phase(t, vin, p["freq"]) -
                        _fundamental_phase(t, vout, p["freq"]))
    if vin_pk <= 0:
        raise SpiceError("Transient input เป็นศูนย์ — ตรวจ amplitude ของแหล่งสัญญาณ")
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
    with tempfile.TemporaryDirectory(prefix="lab04_ngspice_") as wd:
        cir = os.path.join(wd, "circuit.cir")
        log_path = os.path.join(wd, "run.log")
        raw_path = os.path.join(wd, "run.raw")
        with open(cir, "w", encoding="utf-8") as fh:
            fh.write(netlist)
        cmd = [exe, "-b", "-o", log_path, "-r", raw_path, cir]
        try:
            proc = subprocess.run(
                cmd, cwd=wd, capture_output=True, text=True,
                timeout=timeout, shell=False, check=False,
            )
        except subprocess.TimeoutExpired:
            raise SpiceError(f"ngspice timeout หลัง {timeout} วินาที — ปรับ .tran/.ac ให้สั้นลง")
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
    return {
        "engine": "ngspice",
        "version": version,
        "status": "success",
        "mode": mode,
        "model": f"QNPN NPN(BF={fmt(p['bf'])}, VAF={fmt(p['vaf'])}, IS={fmt(p['isat'])})",
        "netlist": netlist,
        "log_excerpt": log[-5000:],
        "data": data,
        "provenance": "ngspice batch run (subprocess) — ไม่ใช่ค่าที่คำนวณใน Browser",
    }
