/* Render charts from REAL ngspice data embedded by Flask (window.SIM). */
(function () {
  "use strict";
  const sim = window.SIM;
  if (!sim || !sim.data) return;
  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs, text) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (text !== undefined) n.textContent = text;
    return n;
  };
  const clear = svg => { while (svg.firstChild) svg.removeChild(svg.firstChild); };
  const fmt = v => {
    const a = Math.abs(v);
    if (a >= 1e6) return (v / 1e6).toFixed(1) + "M";
    if (a >= 1e3) return (v / 1e3).toFixed(1) + "k";
    if (a !== 0 && a < 0.01) return v.toExponential(1);
    return Number(v.toFixed(2)).toString();
  };
  const ticks = (min, max, n) => {
    const raw = (max - min) / n;
    const mag = Math.pow(10, Math.floor(Math.log10(raw || 1)));
    const step = (raw / mag <= 1 ? 1 : raw / mag <= 2 ? 2 : raw / mag <= 5 ? 5 : 10) * mag;
    const out = [];
    for (let v = Math.ceil(min / step) * step; v <= max + step * 1e-6; v += step) out.push(v);
    return out;
  };

  function line(svg, opts) {
    clear(svg);
    const H = svg.viewBox.baseVal.height || 280, W = 660;
    const m = { l: 60, r: 18, t: 16, b: 42 };
    const pw = W - m.l - m.r, ph = H - m.t - m.b;
    const all = opts.series.reduce((a, s) => a.concat(s.points), []);
    if (!all.length) return;
    let xmin = Math.min(...all.map(p => p.x)), xmax = Math.max(...all.map(p => p.x));
    let ymin = Math.min(...all.map(p => p.y)), ymax = Math.max(...all.map(p => p.y));
    if (opts.zero) { ymin = Math.min(ymin, 0); ymax = Math.max(ymax, 0); }
    if (xmax === xmin) { xmin -= 1; xmax += 1; }
    if (ymax === ymin) { ymin -= 1; ymax += 1; }
    const pad = (ymax - ymin) * 0.08; ymin -= pad; ymax += pad;
    const lx = x => opts.log ? Math.log10(Math.max(x, 1e-12)) : x;
    const sx = x => m.l + (lx(x) - lx(xmin)) / (lx(xmax) - lx(xmin)) * pw;
    const sy = y => m.t + ph - (y - ymin) / (ymax - ymin) * ph;

    ticks(ymin, ymax, 5).forEach(v => {
      const y = sy(v);
      if (y < m.t || y > m.t + ph) return;
      svg.appendChild(el("line", { x1: m.l, y1: y, x2: m.l + pw, y2: y, stroke: "#e3edf3" }));
      svg.appendChild(el("text", { x: m.l - 6, y: y + 3, "text-anchor": "end", fill: "#547084", "font-size": 10 }, fmt(v)));
    });
    let xt;
    if (opts.log) {
      xt = [];
      for (let dec = Math.floor(lx(xmin)); dec <= Math.ceil(lx(xmax)); dec++) {
        [1, 2, 5].forEach(k => {
          const val = k * Math.pow(10, dec), lv = Math.log10(val);
          if (lv >= lx(xmin) && lv <= lx(xmax)) xt.push({ v: val, label: fmt(val) });
        });
      }
    } else xt = ticks(xmin, xmax, 6).map(v => ({ v, label: fmt(v) }));
    xt.forEach(t => {
      const x = sx(t.v);
      if (x < m.l || x > m.l + pw) return;
      svg.appendChild(el("line", { x1: x, y1: m.t, x2: x, y2: m.t + ph, stroke: "#eef4f8" }));
      svg.appendChild(el("text", { x, y: m.t + ph + 16, "text-anchor": "middle", fill: "#547084", "font-size": 10 }, t.label));
    });
    svg.appendChild(el("line", { x1: m.l, y1: m.t, x2: m.l, y2: m.t + ph, stroke: "#9cb2c2" }));
    svg.appendChild(el("line", { x1: m.l, y1: m.t + ph, x2: m.l + pw, y2: m.t + ph, stroke: "#9cb2c2" }));
    svg.appendChild(el("text", { x: m.l + pw, y: H - 5, "text-anchor": "end", fill: "#486275", "font-size": 11 }, opts.xLabel));
    svg.appendChild(el("text", { x: 12, y: m.t + 4, fill: "#486275", "font-size": 11 }, opts.yLabel));

    opts.series.forEach(s => {
      const d = s.points.map((p, i) => (i ? "L" : "M") + sx(p.x).toFixed(2) + " " + sy(p.y).toFixed(2)).join(" ");
      svg.appendChild(el("path", { d, fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
    });
    opts.series.forEach((s, i) => {
      svg.appendChild(el("rect", { x: m.l + 8 + i * 150, y: m.t + 4, width: 12, height: 3, fill: s.color }));
      svg.appendChild(el("text", { x: m.l + 24 + i * 150, y: m.t + 9, fill: "#486275", "font-size": 10 }, s.name));
    });
  }

  function bars(svg, items) {
    clear(svg);
    const H = svg.viewBox.baseVal.height || 280, W = 660;
    const m = { l: 70, r: 70, t: 14, b: 16 };
    const rowH = (H - m.t - m.b) / items.length;
    const max = Math.max(...items.map(i => Math.abs(i.v)), 1e-9) * 1.15;
    items.forEach((it, i) => {
      const y = m.t + i * rowH + rowH * 0.2, bh = rowH * 0.55;
      const w = Math.abs(it.v) / max * (W - m.l - m.r);
      svg.appendChild(el("text", { x: m.l - 8, y: y + bh * 0.78, "text-anchor": "end", fill: "#254d67", "font-size": 12, "font-weight": 700 }, it.name));
      svg.appendChild(el("rect", { x: m.l, y, width: W - m.l - m.r, height: bh, rx: 3, fill: "#eef4f8" }));
      svg.appendChild(el("rect", { x: m.l, y, width: Math.max(w, 1), height: bh, rx: 3, fill: it.color }));
      svg.appendChild(el("text", { x: m.l + w + 7, y: y + bh * 0.78, fill: "#17344b", "font-size": 12, "font-weight": 700 }, it.label));
    });
  }

  const d = sim.data;
  const A = document.getElementById("plotA"), B = document.getElementById("plotB");
  if (!A || !B) return;

  if (sim.mode === "dc") {
    document.getElementById("titleA").textContent = "DC node voltages from ngspice .op (V)";
    document.getElementById("titleB").textContent = "Bias headroom · VCC vs VCE (V)";
    bars(A, [
      { name: "VB", v: d.vb, label: d.vb.toFixed(3) + " V", color: "#167e93" },
      { name: "VE", v: d.ve, label: d.ve.toFixed(3) + " V", color: "#0c8e83" },
      { name: "VC", v: d.vc, label: d.vc.toFixed(3) + " V", color: "#a65a2c" },
      { name: "VCE", v: d.vce, label: d.vce.toFixed(3) + " V", color: "#4d7fa9" }
    ]);
    bars(B, [
      { name: "IC", v: d.ic_ma, label: d.ic_ma.toFixed(3) + " mA", color: "#a65a2c" },
      { name: "IB", v: d.ib_ua, label: d.ib_ua.toFixed(2) + " µA", color: "#167e93" }
    ]);
  } else if (sim.mode === "ac") {
    document.getElementById("titleA").textContent = "Bode magnitude · 20 log10 |Vout/Vin| (dB)";
    document.getElementById("titleB").textContent = "Bode phase · Vout/Vin (degree)";
    const pts = (arr) => d.frequency_hz.map((f, i) => ({ x: f, y: arr[i] }));
    line(A, { log: true, zero: true, xLabel: "Frequency (Hz)", yLabel: "Gain (dB)",
      series: [{ name: "|Av| (dB)", color: "#167e93", points: pts(d.gain_db) }] });
    line(B, { log: true, xLabel: "Frequency (Hz)", yLabel: "Phase (deg)",
      series: [{ name: "∠Av (deg)", color: "#0c8e83", points: pts(d.phase_deg) }] });
  } else {
    document.getElementById("titleA").textContent = "Transient Vin / Vout from ngspice .tran (mV)";
    document.getElementById("titleB").textContent = "Vout vs Vin · phase locus";
    const t = d.time_ms;
    line(A, { zero: true, xLabel: "Time (ms)", yLabel: "Voltage (mV)",
      series: [
        { name: "Vin @ base", color: "#0c8e83", points: t.map((x, i) => ({ x, y: d.vin_mv[i] })) },
        { name: "Vout @ RL", color: "#c77a35", points: t.map((x, i) => ({ x, y: d.vout_mv[i] })) }
      ] });
    line(B, { xLabel: "Vin (mV)", yLabel: "Vout (mV)",
      series: [{ name: "Vout / Vin", color: "#7a5232",
        points: d.vin_mv.map((v, i) => ({ x: v, y: d.vout_mv[i] })) }] });
  }
})();
