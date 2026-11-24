/* Render Lab 04 charts from the REAL ngspice payload embedded by Flask. */
(function () {
  "use strict";
  const sim = window.LAB4_SIM;
  if (!sim || !sim.data) return;

  const NS = "http://www.w3.org/2000/svg";
  const element = (tag, attrs, text) => {
    const node = document.createElementNS(NS, tag);
    Object.keys(attrs).forEach(key => node.setAttribute(key, attrs[key]));
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const clear = svg => { while (svg.firstChild) svg.removeChild(svg.firstChild); };
  const fmt = value => {
    const a = Math.abs(value);
    if (a >= 1e9) return (value / 1e9).toFixed(1) + "G";
    if (a >= 1e6) return (value / 1e6).toFixed(1) + "M";
    if (a >= 1e3) return (value / 1e3).toFixed(1) + "k";
    if (a !== 0 && a < 0.01) return value.toExponential(1);
    return Number(value.toFixed(2)).toString();
  };

  function ticks(min, max, count) {
    const raw = (max - min) / count;
    const magnitude = Math.pow(10, Math.floor(Math.log10(raw || 1)));
    const norm = raw / magnitude;
    const step = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10) * magnitude;
    const out = [];
    for (let value = Math.ceil(min / step) * step; value <= max + step * 1e-6; value += step) {
      out.push(value);
    }
    return out;
  }

  function lineChart(svg, options) {
    clear(svg);
    const height = svg.viewBox.baseVal.height || 280;
    const width = 660, margin = { left: 62, right: 18, top: 18, bottom: 44 };
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const points = options.series.reduce((all, s) => all.concat(s.points), []);
    if (!points.length) return;

    let xmin = Math.min(...points.map(p => p.x));
    let xmax = Math.max(...points.map(p => p.x));
    let ymin = Math.min(...points.map(p => p.y));
    let ymax = Math.max(...points.map(p => p.y));
    if (options.zero) { ymin = Math.min(ymin, 0); ymax = Math.max(ymax, 0); }
    if (xmax === xmin) { xmin -= 1; xmax += 1; }
    if (ymax === ymin) { ymin -= 1; ymax += 1; }
    const padding = (ymax - ymin) * 0.08;
    ymin -= padding; ymax += padding;

    const lx = value => options.log ? Math.log10(Math.max(value, 1e-12)) : value;
    const sx = value => margin.left + (lx(value) - lx(xmin)) / (lx(xmax) - lx(xmin)) * plotW;
    const sy = value => margin.top + plotH - (value - ymin) / (ymax - ymin) * plotH;

    ticks(ymin, ymax, 5).forEach(value => {
      const y = sy(value);
      if (y < margin.top || y > margin.top + plotH) return;
      svg.appendChild(element("line", { x1: margin.left, y1: y, x2: margin.left + plotW, y2: y, stroke: "#e3edf3" }));
      svg.appendChild(element("text", { x: margin.left - 6, y: y + 3, "text-anchor": "end", fill: "#5d6f7c", "font-size": 10 }, fmt(value)));
    });

    let xticks;
    if (options.log) {
      xticks = [];
      for (let decade = Math.floor(lx(xmin)); decade <= Math.ceil(lx(xmax)); decade++) {
        [1, 2, 5].forEach(multiplier => {
          const value = multiplier * Math.pow(10, decade);
          if (lx(value) >= lx(xmin) && lx(value) <= lx(xmax)) {
            xticks.push({ value, label: fmt(value) });
          }
        });
      }
    } else {
      xticks = ticks(xmin, xmax, 6).map(value => ({ value, label: fmt(value) }));
    }
    xticks.forEach(tick => {
      const x = sx(tick.value);
      if (x < margin.left || x > margin.left + plotW) return;
      svg.appendChild(element("line", { x1: x, y1: margin.top, x2: x, y2: margin.top + plotH, stroke: "#eef4f8" }));
      svg.appendChild(element("text", { x, y: margin.top + plotH + 16, "text-anchor": "middle", fill: "#5d6f7c", "font-size": 10 }, tick.label));
    });

    svg.appendChild(element("line", { x1: margin.left, y1: margin.top, x2: margin.left, y2: margin.top + plotH, stroke: "#9fb3c0" }));
    svg.appendChild(element("line", { x1: margin.left, y1: margin.top + plotH, x2: margin.left + plotW, y2: margin.top + plotH, stroke: "#9fb3c0" }));
    svg.appendChild(element("text", { x: margin.left + plotW, y: height - 5, "text-anchor": "end", fill: "#5d6f7c", "font-size": 11 }, options.xLabel));
    svg.appendChild(element("text", { x: 10, y: margin.top + 4, fill: "#5d6f7c", "font-size": 11 }, options.yLabel));

    options.series.forEach(series => {
      const path = series.points.map((p, index) =>
        (index ? "L" : "M") + sx(p.x).toFixed(2) + " " + sy(p.y).toFixed(2)
      ).join(" ");
      svg.appendChild(element("path", { d: path, fill: "none", stroke: series.color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
    });
    options.series.forEach((series, index) => {
      svg.appendChild(element("rect", { x: margin.left + 8 + index * 160, y: margin.top + 4, width: 12, height: 3, fill: series.color }));
      svg.appendChild(element("text", { x: margin.left + 24 + index * 160, y: margin.top + 9, fill: "#5d6f7c", "font-size": 10 }, series.name));
    });
  }

  function barChart(svg, items) {
    clear(svg);
    const height = svg.viewBox.baseVal.height || 280;
    const width = 660, margin = { left: 72, right: 76, top: 14, bottom: 14 };
    const rowH = (height - margin.top - margin.bottom) / items.length;
    const max = Math.max(...items.map(item => Math.abs(item.value)), 1e-9) * 1.15;
    items.forEach((item, index) => {
      const y = margin.top + index * rowH + rowH * 0.2;
      const barH = rowH * 0.55;
      const barW = Math.abs(item.value) / max * (width - margin.left - margin.right);
      svg.appendChild(element("text", { x: margin.left - 8, y: y + barH * 0.78, "text-anchor": "end", fill: "#22313c", "font-size": 12, "font-weight": 700 }, item.name));
      svg.appendChild(element("rect", { x: margin.left, y, width: width - margin.left - margin.right, height: barH, rx: 3, fill: "#eef4f8" }));
      svg.appendChild(element("rect", { x: margin.left, y, width: Math.max(barW, 1), height: barH, rx: 3, fill: item.color }));
      svg.appendChild(element("text", { x: margin.left + barW + 7, y: y + barH * 0.78, fill: "#22313c", "font-size": 12, "font-weight": 700 }, item.label));
    });
  }

  const data = sim.data;
  const plotA = document.getElementById("plotA");
  const plotB = document.getElementById("plotB");
  if (!plotA || !plotB) return;
  const titleA = document.getElementById("titleA");
  const titleB = document.getElementById("titleB");

  if (sim.mode === "dc") {
    titleA.textContent = "DC node voltages from ngspice .op (V)";
    titleB.textContent = "Bias currents from ngspice .op";
    barChart(plotA, [
      { name: "VB", value: data.vb, label: data.vb.toFixed(3) + " V", color: "#167e93" },
      { name: "VE", value: data.ve, label: data.ve.toFixed(3) + " V", color: "#0c8e83" },
      { name: "VC", value: data.vc, label: data.vc.toFixed(3) + " V", color: "#a65a2c" },
      { name: "VCE", value: data.vce, label: data.vce.toFixed(3) + " V", color: "#4d7fa9" }
    ]);
    barChart(plotB, [
      { name: "IC", value: data.ic_ma, label: data.ic_ma.toFixed(3) + " mA", color: "#a65a2c" },
      { name: "IB", value: data.ib_ua, label: data.ib_ua.toFixed(2) + " µA", color: "#167e93" }
    ]);
  } else if (sim.mode === "ac") {
    titleA.textContent = "Bode magnitude · 20log10|Vout/Vbase| (dB)";
    titleB.textContent = "Bode phase · Vout/Vbase (degree)";
    const series = values => data.frequency_hz.map((f, i) => ({ x: f, y: values[i] }));
    lineChart(plotA, {
      log: true, zero: true, xLabel: "Frequency (Hz)", yLabel: "Gain (dB)",
      series: [{ name: "|Av| (dB)", color: "#0f6b7d", points: series(data.gain_db) }]
    });
    lineChart(plotB, {
      log: true, xLabel: "Frequency (Hz)", yLabel: "Phase (deg)",
      series: [{ name: "∠Av (deg)", color: "#0c8e83", points: series(data.phase_deg) }]
    });
  } else {
    titleA.textContent = "Transient Vin / Vout from ngspice .tran (mV)";
    titleB.textContent = "Vout vs Vin · phase locus";
    lineChart(plotA, {
      zero: true, xLabel: "Time (ms)", yLabel: "Voltage (mV)",
      series: [
        { name: "Vin @ base", color: "#0c8e83", points: data.time_ms.map((t, i) => ({ x: t, y: data.vin_mv[i] })) },
        { name: "Vout @ RL", color: "#c77a35", points: data.time_ms.map((t, i) => ({ x: t, y: data.vout_mv[i] })) }
      ]
    });
    lineChart(plotB, {
      xLabel: "Vin (mV)", yLabel: "Vout (mV)",
      series: [{
        name: "Vout / Vin", color: "#7a5232",
        points: data.vin_mv.map((v, i) => ({ x: v, y: data.vout_mv[i] }))
      }]
    });
  }
})();
