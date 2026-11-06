/* Dashboard renderer. Reads the aggregate view model embedded by build.py.
   Rule: this file only formats, sorts and selects numbers from findings.json /
   themes.json. It never computes a new statistic. Text goes in via textContent. */
(function () {
  "use strict";

  var VM = JSON.parse(document.getElementById("dash-data").textContent);
  var META = VM.meta;
  var T = META.small_n_threshold;
  var METRICS = VM.metrics;
  var BY = new Map(METRICS.map(function (m) { return [m.key, m]; }));
  var MEASURE_ORDER = ["post", "pre", "change", "quality", "recommend", "call_988", "themes", "missing"];
  // Theme buckets that are not a topic (filler, unmatched, questions in the "improve" box). Shown last, never called "top".
  var CATCH_ALL = { no_substantive: "catch-all", other_unclear: "catch-all", audience_question: "not a suggestion" };
  var SERIES = { after: { name: "After training", cls: "" }, before: { name: "Before (recalled after training)", cls: "s-before" } };

  // ------------------------------------------------------------------ DOM helpers
  function h(tag, attrs) {
    var e = document.createElement(tag);
    setAttrs(e, attrs);
    for (var i = 2; i < arguments.length; i++) add(e, arguments[i]);
    return e;
  }
  var SVGNS = "http://www.w3.org/2000/svg";
  function s(tag, attrs) {
    var e = document.createElementNS(SVGNS, tag);
    setAttrs(e, attrs);
    for (var i = 2; i < arguments.length; i++) add(e, arguments[i]);
    return e;
  }
  function setAttrs(e, attrs) {
    if (!attrs) return;
    Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v == null || v === false) return;
      if (k === "class") e.setAttribute("class", v);
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? "" : String(v));
    });
  }
  function add(e, kid) {
    if (kid == null || kid === false) return;
    if (Array.isArray(kid)) { kid.forEach(function (k) { add(e, k); }); return; }
    e.appendChild(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  function $(sel) { return document.querySelector(sel); }
  function slot(id) { return document.querySelector("#" + id + " .slot"); }

  // ------------------------------------------------------------------ formatting
  var NF = new Intl.NumberFormat("en-US");
  function fmtInt(n) { return n == null ? "—" : NF.format(n); }
  function signed(v, digits) {
    var a = Math.abs(v), body = digits == null ? String(a) : a.toFixed(digits);
    return (v > 0 ? "+" : v < 0 ? "−" : "") + body;
  }
  function fmt(v, unit) {
    if (v == null || typeof v !== "number" || isNaN(v)) return "—";
    switch (unit) {
      case "pct": return v.toFixed(1) + "%";
      case "count": return NF.format(v);
      case "points": return signed(v, 2);
      case "nps": return signed(v, Number.isInteger(v) ? null : 1);
      case "mean": case "median": return v.toFixed(2);
      default: return String(Math.round(v * 100) / 100);
    }
  }
  function fmtCI(r, unit) {
    if (!r || r.ci_low == null || r.ci_high == null) return "";
    return fmt(r.ci_low, unit) + " to " + fmt(r.ci_high, unit);
  }
  function tickFmt(v, unit) {
    if (unit === "pct") return v + "%";
    if (unit === "nps" || unit === "points") return v > 0 ? "+" + v : v < 0 ? "−" + Math.abs(v) : "0";
    return NF.format(v);
  }
  function scaleNote(m) {
    var sc = m.scale;
    if (m.unit === "mean" || m.unit === "median") {
      if (sc.lo === 1 && sc.hi === 5) return "on a 1–5 scale (5 = strongly agree)";
      if (sc.lo === 0 && sc.hi === 10) return "on a 0–10 scale";
    }
    if (m.unit === "nps") return "from −100 to +100";
    if (m.unit === "points") return "points on the 1–5 agreement scale";
    return "";
  }
  function metricName(m) {
    if (m.measure === "themes") return m.item_label;
    return m.item_label + " — " + m.stat_label;
  }
  function lc(s) { return s ? s.charAt(0).toLowerCase() + s.slice(1) : s; }

  // ------------------------------------------------------------------ lookups
  function overall(key) { var m = BY.get(key); return m && m.overall ? m.overall : null; }
  function metricsWhere(fn) {
    return METRICS.filter(fn).sort(function (a, b) { return order(a) - order(b) || (a.key < b.key ? -1 : 1); });
  }
  var ITEM_ORDER = ["identify_crisis", "describe_988", "know_when_to_use", "engaging", "knowledgeable", "organized", "score", "likelihood"];
  function order(m) {
    var mi = MEASURE_ORDER.indexOf(m.measure); if (mi < 0) mi = 50;
    var ii = ITEM_ORDER.indexOf(m.item); if (ii < 0) ii = 50;
    return mi * 100 + ii;
  }
  function shown(r) { return r && r.value != null; }

  // ------------------------------------------------------------------ tooltip
  var tip = $("#tip");
  function place(x, y) {
    var w = tip.offsetWidth, hh = tip.offsetHeight;
    var left = x + 14, top = y + 14;
    if (left + w > window.innerWidth - 8) left = x - w - 14;
    if (top + hh > window.innerHeight - 8) top = y - hh - 14;
    tip.style.left = Math.max(8, left) + "px";
    tip.style.top = Math.max(8, top) + "px";
  }
  function showTip(node, content, evt) {
    tip.replaceChildren(content);
    tip.hidden = false;
    if (evt && evt.clientX != null) place(evt.clientX, evt.clientY);
    else { var b = node.getBoundingClientRect(); place(b.left + Math.min(b.width, 260), b.top); }
  }
  function hideTip() { tip.hidden = true; }
  function bindTip(node, make) {
    node.addEventListener("pointerenter", function (e) { showTip(node, make(), e); });
    node.addEventListener("pointermove", function (e) { if (!tip.hidden) place(e.clientX, e.clientY); });
    node.addEventListener("pointerleave", hideTip);
    node.addEventListener("focus", function () { showTip(node, make()); });
    node.addEventListener("blur", hideTip);
  }
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") hideTip(); });
  window.addEventListener("scroll", hideTip, { passive: true });

  function tipRec(rec, unit, series) {
    var f = document.createDocumentFragment();
    if (!shown(rec)) {
      f.appendChild(h("div", { class: "tv" }, "Not shown"));
      f.appendChild(h("div", { class: "tm" }, rec ? "Fewer than " + T + " people (n = " + fmtInt(rec.n) + "). Hidden to protect privacy and because the number would be unreliable." : "No data."));
    } else {
      f.appendChild(h("div", null, series ? h("span", { class: "tk " + series.cls }) : null,
        h("span", { class: "tv" }, fmt(rec.value, unit)), series ? h("span", { class: "tm" }, "  " + series.name) : null));
      if (rec.ci_low != null) f.appendChild(h("div", { class: "tm" }, "95% range: " + fmtCI(rec, unit)));
      if (unit === "pct" && rec.numerator != null) f.appendChild(h("div", null, fmtInt(rec.numerator) + " of " + fmtInt(rec.n)));
    }
    if (rec) {
      f.appendChild(h("div", null, "n = " + fmtInt(rec.n) + ": " + rec.denominator));
      if (rec.n_missing) f.appendChild(h("div", { class: "tm" }, fmtInt(rec.n_missing) + " left it blank or gave an answer that could not be read"));
      if (rec.caveat) f.appendChild(h("div", { class: "tm" }, rec.caveat));
      f.appendChild(h("div", { class: "ti mono" }, "ID " + rec.id));
    }
    return f;
  }

  // ------------------------------------------------------------------ scales
  function niceStep(range, count) {
    var raw = range / count, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
    return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
  }
  function domainFor(scale, recs) {
    var vals = [];
    recs.forEach(function (r) {
      if (!r || r.value == null) return;
      vals.push(r.value);
      if (r.ci_low != null) vals.push(r.ci_low);
      if (r.ci_high != null) vals.push(r.ci_high);
    });
    var lo = scale.lo, hi = scale.hi;
    if (lo == null) lo = Math.min.apply(null, [0].concat(vals));
    if (hi == null) hi = Math.max.apply(null, [0].concat(vals));
    if (hi === lo) hi = lo + 1;
    if (!scale.fixed) {
      var st = niceStep(hi - lo, 4);
      lo = Math.floor(lo / st) * st; hi = Math.ceil(hi / st) * st;
      if (hi === lo) hi = lo + st;
    }
    return [lo, hi];
  }
  function ticksFor(lo, hi, count) {
    var st = niceStep(hi - lo, count), out = [];
    for (var v = Math.ceil(lo / st - 1e-9) * st; v <= hi + st * 1e-9; v += st) out.push(Math.round(v * 1e6) / 1e6);
    return out;
  }

  // ------------------------------------------------------------------ flags
  function flagFor(rec) {
    if (!rec) return null;
    if (rec.level === "other_pooled") return h("span", { class: "flag neutral", title: "Groups with fewer than " + T + " people, combined" }, "pooled");
    if (!shown(rec)) return h("span", { class: "flag", title: "Fewer than " + T + " people" }, "⚠ under " + T);
    if (rec.small_n) return h("span", { class: "flag", title: "Small group" }, "⚠ small group");
    return null;
  }

  // ------------------------------------------------------------------ row chart (horizontal bars or dots)
  function legend(items) {
    return h("div", { class: "legend", "aria-hidden": "true" }, items.map(function (it) {
      return h("span", null, h("span", { class: "sw " + it.cls, style: it.bg ? "background:" + it.bg : null }), it.name);
    }));
  }
  function rowChart(cfg) {
    var recs = [];
    cfg.rows.forEach(function (r) { r.lanes.forEach(function (l) { recs.push(l.rec); }); });
    if (cfg.ref && cfg.ref.value != null) recs.push({ value: cfg.ref.value });
    var d = domainFor(cfg.scale, recs), lo = d[0], hi = d[1];
    var pos = function (v) { return Math.max(0, Math.min(100, (v - lo) / (hi - lo) * 100)); };
    var ticks = ticksFor(lo, hi, 4);
    var isBar = cfg.scale.mark === "bar";
    var hasCI = recs.some(function (r) { return r && r.ci_low != null; });

    var root = h("div", { class: "rchart", role: "group", "aria-label": cfg.ariaLabel });
    if (cfg.labelWidth) root.style.setProperty("--label-w", cfg.labelWidth);
    var leg = [];
    if (cfg.series.length > 1) cfg.series.forEach(function (sr) { leg.push({ cls: sr.cls || "", name: sr.name, bg: sr.cls ? null : "var(--s-after)" }); });
    if (hasCI) leg.push({ cls: "ci", name: "95% range (likely spread of the true value)" });
    if (cfg.ref && cfg.ref.value != null) leg.push({ cls: "ref", name: cfg.ref.label });
    if (leg.length) root.appendChild(legend(leg));

    cfg.rows.forEach(function (row, ri) {
      var plot = h("div", { class: "rplot", "aria-hidden": "true" });
      var srBits = [];
      row.lanes.forEach(function (lane) {
        var L = h("div", { class: "lane" });
        ticks.forEach(function (t) { L.appendChild(h("div", { class: "grid-line" + (t === 0 ? " zero" : ""), style: "left:" + pos(t) + "%" })); });
        if (cfg.ref && cfg.ref.value != null) L.appendChild(h("div", { class: "ref-line", style: "left:" + pos(cfg.ref.value) + "%" }));
        var r = lane.rec, sc = lane.series.cls || "";
        if (!shown(r)) {
          L.appendChild(h("div", { class: "supp" }, r ? "Not shown: n = " + fmtInt(r.n) + " (under " + T + ")" : "No data"));
          srBits.push((lane.series.name ? lane.series.name + ": " : "") + "not shown, fewer than " + T + " people");
        } else {
          if (isBar) {
            var x0 = pos(Math.max(lo, 0)), x1 = pos(r.value);
            L.appendChild(h("div", { class: "bar " + sc, style: "left:" + Math.min(x0, x1) + "%;width:" + Math.abs(x1 - x0) + "%" }));
          }
          if (r.ci_low != null && r.ci_high != null)
            L.appendChild(h("div", { class: "ci", style: "left:" + pos(r.ci_low) + "%;width:" + (pos(r.ci_high) - pos(r.ci_low)) + "%" }));
          if (!isBar) L.appendChild(h("div", { class: "dot " + sc, style: "left:" + pos(r.value) + "%" }));
          var end = Math.max(pos(r.value), r.ci_high != null ? pos(r.ci_high) : 0);
          var named = cfg.laneNamesOnFirst && ri === 0 && row.lanes.length > 1;
          L.appendChild(h("span", { class: "vlab", style: "left:" + end + "%" },
            named ? h("span", { class: "lane-name" }, lane.series.short + " ") : null, fmt(r.value, cfg.unit)));
          srBits.push((lane.series.name ? lane.series.name + ": " : "") + fmt(r.value, cfg.unit) +
            (r.ci_low != null ? ", 95% range " + fmtCI(r, cfg.unit) : ""));
        }
        plot.appendChild(L);
      });
      var label = h("div", { class: "rlabel" }, row.label, row.flag ? [" ", row.flag] : null, h("span", { class: "n" }, row.sub));
      var rr = h("div", { class: "rrow", tabindex: "0" }, label, plot, h("span", { class: "sr" }, srBits.join("; ")));
      bindTip(rr, function () {
        var f = document.createDocumentFragment();
        f.appendChild(h("div", { class: "tm" }, row.label));
        row.lanes.forEach(function (lane, i) {
          if (i) f.appendChild(h("hr"));
          f.appendChild(tipRec(lane.rec, cfg.unit, row.lanes.length > 1 ? lane.series : null));
        });
        return f;
      });
      root.appendChild(rr);
    });
    root.appendChild(h("div", { class: "raxis", "aria-hidden": "true" }, h("div"),
      h("div", { class: "ticks" }, ticks.map(function (t, i) {
        return h("span", { class: i === 0 && pos(t) < 2 ? "first" : i === ticks.length - 1 && pos(t) > 98 ? "last" : null, style: "left:" + pos(t) + "%" }, tickFmt(t, cfg.unit));
      })),
      cfg.axisTitle ? h("div", { class: "axis-title" }, cfg.axisTitle) : null));
    return root;
  }

  // ------------------------------------------------------------------ SVG charts (time series, distributions)
  function measured(wrap, draw) {
    var last = -1;
    var run = function () {
      var w = Math.round(wrap.clientWidth);
      if (!w || w === last) return;
      last = w; draw(w);
    };
    if (typeof ResizeObserver !== "undefined") new ResizeObserver(run).observe(wrap);
    else window.addEventListener("resize", run);
    requestAnimationFrame(run);
  }
  function monthIndex(level) {
    var m = /^(\d{4})[_-](\d{1,2})(?:_to_\d{4}[_-]\d{1,2})?$/.exec(level);
    return m ? Number(m[1]) * 12 + Number(m[2]) - 1 : null;
  }

  function timeChart(cfg) {
    var outer = h("div");
    var leg = [];
    if (cfg.recs.some(function (r) { return r.ci_low != null; })) leg.push({ cls: "", name: "Shaded band: 95% range", bg: "color-mix(in srgb, var(--s-after) 25%, transparent)" });
    if (cfg.ref && cfg.ref.value != null) leg.push({ cls: "refh", name: cfg.ref.label });
    leg.push({ cls: "", name: "× = fewer than " + T + " people, not shown", bg: "transparent" });
    outer.appendChild(legend(leg));
    var wrap = h("div", { class: "svgchart", role: "img", "aria-label": cfg.ariaLabel });
    outer.appendChild(wrap);
    // Pooled / unknown periods have no place on a time axis; they stay in the table below.
    var timed = cfg.recs.filter(function (r) { return monthIndex(r.level) != null; });
    var recs = (timed.length >= 2 ? timed : cfg.recs).slice();
    var allMonths = recs.every(function (r) { return monthIndex(r.level) != null; });
    recs.sort(function (a, b) { return allMonths ? monthIndex(a.level) - monthIndex(b.level) : (a.level < b.level ? -1 : 1); });
    var xi = recs.map(function (r, i) { return allMonths ? monthIndex(r.level) : i; });
    measured(wrap, function (W) {
      var H = 280, m = { l: 52, r: 24, t: 16, b: 58 };
      var d = domainFor(cfg.scale, recs.concat(cfg.ref ? [{ value: cfg.ref.value }] : [])), lo = d[0], hi = d[1];
      var x0 = Math.min.apply(null, xi), x1 = Math.max.apply(null, xi);
      var pw = W - m.l - m.r, ph = H - m.t - m.b;
      var X = function (v) { return m.l + (x1 === x0 ? pw / 2 : (v - x0) / (x1 - x0) * pw); };
      var Y = function (v) { return m.t + (1 - (v - lo) / (hi - lo)) * ph; };
      var svg = s("svg", { viewBox: "0 0 " + W + " " + H, width: W, height: H, "aria-hidden": "true", focusable: "false" });
      ticksFor(lo, hi, 4).forEach(function (t) {
        svg.appendChild(s("line", { class: t === lo || t === 0 ? "bl" : "gl", x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t) }));
        svg.appendChild(s("text", { x: m.l - 8, y: Y(t) + 4, "text-anchor": "end" }, tickFmt(t, cfg.unit)));
      });
      if (cfg.ref && cfg.ref.value != null) {
        svg.appendChild(s("line", { class: "ref", x1: m.l, x2: W - m.r, y1: Y(cfg.ref.value), y2: Y(cfg.ref.value) }));
      }
      // Line and CI band, broken wherever a point is hidden.
      var seg = [];
      var flush = function () {
        if (!seg.length) return;
        if (seg.every(function (p) { return p.r.ci_low != null; }) && seg.length > 1) {
          var up = seg.map(function (p) { return X(p.x) + "," + Y(p.r.ci_high); });
          var dn = seg.slice().reverse().map(function (p) { return X(p.x) + "," + Y(p.r.ci_low); });
          svg.appendChild(s("polygon", { class: "band", points: up.concat(dn).join(" ") }));
        }
        if (seg.length > 1) svg.appendChild(s("path", { class: "line", d: "M" + seg.map(function (p) { return X(p.x) + "," + Y(p.r.value); }).join("L") }));
        seg = [];
      };
      recs.forEach(function (r, i) {
        if (!shown(r)) { flush(); return; }
        if (allMonths && seg.length && xi[i] - seg[seg.length - 1].x > 1) flush();
        seg.push({ x: xi[i], r: r });
      });
      flush();
      // Axis labels: greedy left-to-right, skip any that would collide (every value stays in the table and tooltip).
      var minGap = 64, lastLab = -Infinity;
      var span = recs.length > 1 ? (X(xi[recs.length - 1]) - X(xi[0])) / (recs.length - 1) : pw;
      var xh = s("line", { class: "xh", y1: m.t, y2: H - m.b, x1: -10, x2: -10, visibility: "hidden" });
      svg.appendChild(xh);
      recs.forEach(function (r, i) {
        var cx = X(xi[i]);
        if (shown(r)) {
          if (r.ci_low != null) svg.appendChild(s("line", { class: "xh", x1: cx, x2: cx, y1: Y(r.ci_low), y2: Y(r.ci_high) }));
          svg.appendChild(s("circle", { class: "pt", cx: cx, cy: Y(r.value), r: 5 }));
        } else {
          var by = Y(lo) - 8;
          svg.appendChild(s("path", { class: "supp-x", d: "M" + (cx - 4) + "," + (by - 4) + "L" + (cx + 4) + "," + (by + 4) + "M" + (cx + 4) + "," + (by - 4) + "L" + (cx - 4) + "," + (by + 4) }));
        }
        if (cx - lastLab >= minGap) {
          lastLab = cx;
          svg.appendChild(s("text", { x: cx, y: H - m.b + 18, "text-anchor": "middle" }, r.level_label));
          svg.appendChild(s("text", { x: cx, y: H - m.b + 34, "text-anchor": "middle" }, "n=" + fmtInt(r.n)));
        }
        var hw = Math.max(24, Math.min(80, span));
        var hit = s("rect", { class: "hit", x: cx - hw / 2, y: m.t, width: hw, height: ph, tabindex: "0", role: "img",
          "aria-label": r.level_label + ": " + (shown(r) ? fmt(r.value, cfg.unit) : "not shown") + ", n = " + fmtInt(r.n) });
        bindTip(hit, function () {
          var f = document.createDocumentFragment();
          f.appendChild(h("div", { class: "tm" }, r.level_label));
          f.appendChild(tipRec(r, cfg.unit, null));
          return f;
        });
        hit.addEventListener("pointerenter", function () { xh.setAttribute("x1", cx); xh.setAttribute("x2", cx); xh.setAttribute("visibility", "visible"); });
        hit.addEventListener("focus", function () { xh.setAttribute("x1", cx); xh.setAttribute("x2", cx); xh.setAttribute("visibility", "visible"); });
        hit.addEventListener("pointerleave", function () { xh.setAttribute("visibility", "hidden"); });
        hit.addEventListener("blur", function () { xh.setAttribute("visibility", "hidden"); });
        svg.appendChild(hit);
      });
      if (cfg.axisTitle) svg.appendChild(s("text", { x: m.l + pw / 2, y: H - 6, "text-anchor": "middle" }, cfg.axisTitle));
      wrap.replaceChildren(svg);
    });
    return outer;
  }

  function distChart(cfg) {
    // cfg.bins: [{bin, rec}] sorted; unit pct. Columns grow from zero.
    var wrap = h("div", { class: "svgchart", role: "img", "aria-label": cfg.ariaLabel });
    measured(wrap, function (W) {
      var H = 250, m = { l: 48, r: 12, t: 22, b: cfg.bands ? 74 : 48 };
      var recs = cfg.bins.map(function (b) { return b.rec; });
      var d = domainFor({ lo: 0, hi: null, fixed: false }, recs.map(function (r) { return { value: r && r.value }; }));
      var hi = d[1], pw = W - m.l - m.r, ph = H - m.t - m.b;
      var slotW = pw / cfg.bins.length, bw = Math.min(28, slotW * 0.7);
      var Y = function (v) { return m.t + (1 - v / hi) * ph; };
      var svg = s("svg", { viewBox: "0 0 " + W + " " + H, width: W, height: H, "aria-hidden": "true", focusable: "false" });
      ticksFor(0, hi, 4).forEach(function (t) {
        svg.appendChild(s("line", { class: t === 0 ? "bl" : "gl", x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t) }));
        svg.appendChild(s("text", { x: m.l - 8, y: Y(t) + 4, "text-anchor": "end" }, tickFmt(t, cfg.unit)));
      });
      cfg.bins.forEach(function (b, i) {
        var cx = m.l + slotW * (i + 0.5), r = b.rec;
        if (shown(r)) {
          var y = Y(r.value), hgt = Math.max(0, Y(0) - y), rad = Math.min(4, hgt / 2, bw / 2);
          svg.appendChild(s("path", { class: "col", d: "M" + (cx - bw / 2) + "," + Y(0) + "V" + (y + rad) + "Q" + (cx - bw / 2) + "," + y + " " + (cx - bw / 2 + rad) + "," + y +
            "H" + (cx + bw / 2 - rad) + "Q" + (cx + bw / 2) + "," + y + " " + (cx + bw / 2) + "," + (y + rad) + "V" + Y(0) + "Z" }));
          if (slotW >= 34) svg.appendChild(s("text", { x: cx, y: y - 6, "text-anchor": "middle", class: "lab" }, Math.round(r.value) + "%"));
        } else {
          svg.appendChild(s("text", { x: cx, y: Y(0) - 6, "text-anchor": "middle" }, "–"));
        }
        svg.appendChild(s("text", { x: cx, y: H - m.b + 16, "text-anchor": "middle" }, String(b.bin)));
        var hit = s("rect", { class: "hit", x: cx - slotW / 2, y: m.t, width: slotW, height: ph, tabindex: "0", role: "img",
          "aria-label": "Score " + b.bin + ": " + (shown(r) ? fmt(r.value, cfg.unit) : "not shown") });
        bindTip(hit, function () {
          var f = document.createDocumentFragment();
          f.appendChild(h("div", { class: "tm" }, "Score " + b.bin));
          f.appendChild(tipRec(r, cfg.unit, null));
          return f;
        });
        svg.appendChild(hit);
      });
      if (cfg.bands) {
        cfg.bands.forEach(function (band) {
          var i0 = cfg.bins.findIndex(function (b) { return b.bin === band.from; });
          var i1 = cfg.bins.findIndex(function (b) { return b.bin === band.to; });
          if (i0 < 0 || i1 < 0) return;
          var xa = m.l + slotW * i0 + 4, xb = m.l + slotW * (i1 + 1) - 4, yb = H - m.b + 26;
          svg.appendChild(s("path", { class: "bracket", d: "M" + xa + "," + yb + "v6H" + xb + "v-6" }));
          svg.appendChild(s("text", { x: (xa + xb) / 2, y: yb + 22, "text-anchor": "middle", class: "lab" }, band.label));
        });
      }
      if (cfg.axisTitle) svg.appendChild(s("text", { x: m.l + pw / 2, y: H - 6, "text-anchor": "middle" }, cfg.axisTitle));
      wrap.replaceChildren(svg);
    });
    return wrap;
  }

  // ------------------------------------------------------------------ tables + CSV
  function recTable(caption, items, unit, firstCol) {
    var head = h("tr", null, h("th", { scope: "col" }, firstCol || "Group"), h("th", { scope: "col", class: "num" }, "Value"),
      h("th", { scope: "col", class: "num" }, "95% range"), h("th", { scope: "col", class: "num" }, "n"),
      h("th", { scope: "col" }, "Who is counted"), h("th", { scope: "col" }, "Notes"));
    var body = items.map(function (it) {
      var r = it.rec;
      return h("tr", null, h("th", { scope: "row" }, it.name),
        h("td", { class: "num" }, r ? (shown(r) ? fmt(r.value, unit) : "not shown") : "—"),
        h("td", { class: "num" }, r ? fmtCI(r, unit) : ""),
        h("td", { class: "num" }, r ? fmtInt(r.n) : ""),
        h("td", null, r ? r.denominator : ""),
        h("td", null, r ? notes(r) : ""));
    });
    return h("div", { class: "tablewrap" }, h("table", null, h("caption", null, caption), h("thead", null, head), h("tbody", null, body)));
  }
  function notes(r) {
    var out = [];
    if (!shown(r)) out.push("Fewer than " + T + " people; hidden.");
    else if (r.small_n) out.push("Small group.");
    if (r.level === "other_pooled") out.push("Small groups combined.");
    if (r.n_missing) out.push(fmtInt(r.n_missing) + " missing or unreadable.");
    if (r.caveat) out.push(r.caveat);
    return out.join(" ");
  }
  function tableDetails(summary, tableEl, csv) {
    var d = h("details", { class: "tbl" }, h("summary", null, summary), tableEl);
    if (csv) d.appendChild(h("div", { class: "tbl-actions" }, h("button", { type: "button", onclick: csv }, "Download as CSV (opens in Excel)")));
    return d;
  }
  function csvCell(v) {
    if (v == null) return "";
    var t = String(v);
    return /[",\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t;
  }
  function downloadCSV(name, header, rows) {
    var text = "﻿" + [header].concat(rows).map(function (r) { return r.map(csvCell).join(","); }).join("\r\n");
    var url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
    var a = h("a", { href: url, download: name });
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }
  var CSV_HEAD = ["id", "measure", "statement", "group_type", "group", "value", "unit", "ci_low", "ci_high", "n", "numerator", "n_missing", "denominator", "small_n", "suppressed", "caveat"];
  function csvRow(m, r) {
    return [r.id, m.measure_label, metricName(m), META.dimension_labels[r.dimension] || r.dimension, r.level_label,
      r.value, r.unit, r.ci_low, r.ci_high, r.n, r.numerator, r.n_missing, r.denominator, r.small_n, r.suppressed, r.caveat];
  }

  // ------------------------------------------------------------------ small building blocks
  function means(meansNodes, todoNodes) {
    return h("div", { class: "means" },
      h("div", null, h("h4", null, "What this means"), meansNodes.map(function (n) { return h("p", null, n); })),
      h("div", null, h("h4", null, "What to do"), todoNodes.map(function (n) { return h("p", null, n); })));
  }
  function tile(label, rec, unit, scaleText) {
    if (!rec) return null;
    return h("div", { class: "tile", title: "ID " + rec.id },
      h("p", { class: "t-label" }, label),
      h("p", { class: "t-value" }, shown(rec) ? fmt(rec.value, unit) : "Not shown", scaleText ? h("span", { class: "t-scale" }, " " + scaleText) : null),
      h("p", { class: "t-n" }, "n = " + fmtInt(rec.n) + " · " + rec.denominator),
      rec.ci_low != null ? h("p", { class: "t-ci" }, "95% range " + fmtCI(rec, unit)) : null,
      flagFor(rec) ? h("p", { class: "t-ci" }, flagFor(rec)) : null);
  }
  function empty(text) { return h("p", { class: "empty" }, text); }
  // The caveat worth a callout: from the overall number first, never a "suppressed" note (the chart already says so).
  function pickCaveat(recs) {
    var r = recs.find(function (x) { return x && shown(x) && x.caveat; });
    return r ? r.caveat : "";
  }
  function sub(text) { return h("p", { class: "sub" }, text); }
  function caveatBox(text) { return h("div", { class: "callout caveat", role: "note" }, h("p", null, h("b", null, "Caution: "), text)); }
  var RETRO = "The “before” answers were collected after the training, by asking people to look back. People tend to rate their past selves lower after learning something, so the before-to-after gap probably overstates how much changed.";

  // ------------------------------------------------------------------ header
  function renderHeader() {
    if (META.synthetic) {
      var parts = [];
      if (META.findings_synthetic) parts.push("survey numbers");
      if (META.themes_synthetic) parts.push("comment themes");
      $("#banner-slot").appendChild(h("div", { class: "banner", role: "note" }, "EXAMPLE DATA: ",
        h("span", null, "the " + parts.join(" and ") + " on this page are synthetic placeholders, not survey results. Do not cite them.")));
    }
    var src = META.source || {};
    var bits = [];
    if (src.n_rows != null) bits.push(fmtInt(src.n_rows) + " survey responses" + (src.sheet ? " (sheet “" + src.sheet + "”)" : ""));
    if (src.file_sha256) bits.push("input file fingerprint " + src.file_sha256.slice(0, 12));
    bits.push(fmtInt(META.n_findings) + " published numbers");
    if (META.findings_schema_version) bits.push("findings format v" + META.findings_schema_version);
    var fr = $("#freshness");
    fr.appendChild(document.createTextNode("Data: " + bits.join(" · ") + ". "));
    if (META.sources_match === "no") fr.appendChild(h("span", { class: "flag" }, "⚠ comments were coded from a different export than the survey numbers"));
  }

  // ------------------------------------------------------------------ sections
  function renderGlance() {
    var el = slot("glance");
    var src = META.source || {};
    if (src.n_rows != null) el.appendChild(h("div", { class: "hero" }, h("span", { class: "big" }, fmtInt(src.n_rows)),
      h("span", { class: "what" }, "survey responses in this data. Each number below says how many of them it is based on.")));
    var tiles = h("div", { class: "tiles" });
    var post = metricsWhere(function (m) { return m.measure === "post" && m.stat === "agree_pct" && m.overall; });
    post.forEach(function (m) { add(tiles, tile(m.item_label + " (agree, after training)", m.overall, "pct")); });
    var rec = metricsWhere(function (m) { return m.measure === "recommend" && (m.stat === "nps" || m.stat === "mean") && m.overall; });
    rec.forEach(function (m) { add(tiles, tile(m.stat === "nps" ? "Net Promoter Score (would recommend)" : "Would recommend: average score", m.overall, m.unit, m.stat === "mean" ? "/ 10" : null)); });
    var call = metricsWhere(function (m) { return m.measure === "call_988" && m.stat === "mean" && m.overall; });
    call.forEach(function (m) { add(tiles, tile("Likely to call 988: average score", m.overall, m.unit, "/ 10")); });
    if (!tiles.childNodes.length) { el.appendChild(empty("No headline numbers in this data build.")); return; }
    el.appendChild(tiles);
    var ps = post.filter(function (m) { return shown(m.overall); }).sort(function (a, b) { return a.overall.value - b.overall.value; });
    if (ps.length) {
      var lo = ps[0];
      el.appendChild(means(
        ["After the training, most people agreed with each statement. The lowest was “" + lc(lo.item_label) + "” at " + fmt(lo.overall.value, "pct") + " of " + fmtInt(lo.overall.n) + " people who answered."],
        ["Use “Compare groups” below to see whether any county, role or language group falls behind, and the comments to see why."]));
    }
  }

  function renderLearning() {
    var el = slot("learning");
    var items = metricsWhere(function (m) { return m.measure === "post" && m.stat === "agree_pct" && m.overall; });
    if (!items.length) { el.appendChild(empty("No after-training items in this data build.")); return; }
    el.appendChild(sub("Share who agreed or strongly agreed with each statement after the training, next to how they rated themselves before it. Both were asked on the same survey, after the training."));
    var rows = items.map(function (m) {
      var pre = overall("pre." + m.item + ".agree_pct");
      var lanes = [{ rec: m.overall, series: { name: SERIES.after.name, short: "After", cls: "" } }];
      if (pre) lanes.push({ rec: pre, series: { name: SERIES.before.name, short: "Before", cls: "s-before" } });
      return { label: m.item_label, sub: "n = " + fmtInt(m.overall.n) + " answered", lanes: lanes, flag: flagFor(m.overall) };
    });
    el.appendChild(h("h3", null, "Agreed or strongly agreed, before and after"));
    el.appendChild(rowChart({ rows: rows, unit: "pct", scale: { lo: 0, hi: 100, mark: "bar", fixed: true },
      series: [{ name: SERIES.after.name, cls: "" }, { name: SERIES.before.name, cls: "s-before" }], laneNamesOnFirst: true,
      axisTitle: "% of people who answered", ariaLabel: "Agreement before and after training, by statement", labelWidth: "260px" }));
    var tItems = [];
    items.forEach(function (m) {
      tItems.push({ name: m.item_label + " (after)", rec: m.overall });
      var pre = overall("pre." + m.item + ".agree_pct");
      if (pre) tItems.push({ name: m.item_label + " (before, recalled)", rec: pre });
    });
    el.appendChild(tableDetails("Show as a table", recTable("Agreement before and after training", tItems, "pct", "Statement")));

    var ch = items.map(function (m) { return { m: m, r: overall("change." + m.item + ".mean_points") }; }).filter(function (x) { return x.r; });
    if (ch.length) {
      el.appendChild(h("h3", null, "Average self-rated change"));
      el.appendChild(sub("Average of each person’s after rating minus their before rating, in points on the 1–5 agreement scale. Zero means no change."));
      var chRec = ch.map(function (x) { return x.r; });
      el.appendChild(rowChart({ rows: ch.map(function (x) { return { label: x.m.item_label, sub: "n = " + fmtInt(x.r.n) + " answered both", lanes: [{ rec: x.r, series: { name: "", cls: "" } }], flag: flagFor(x.r) }; }),
        unit: "points", scale: { lo: null, hi: null, mark: "dot", fixed: false }, series: [{}], axisTitle: "points (after minus before)",
        ariaLabel: "Average self-rated change by statement", labelWidth: "260px" }));
      el.appendChild(tableDetails("Show as a table", recTable("Average self-rated change", ch.map(function (x) { return { name: x.m.item_label, rec: x.r }; }), "points", "Statement")));
      var cav = pickCaveat(chRec);
      el.appendChild(caveatBox(cav || RETRO));
    } else {
      el.appendChild(caveatBox(RETRO));
    }
    var shownPost = items.filter(function (m) { return shown(m.overall); }).sort(function (a, b) { return a.overall.value - b.overall.value; });
    var big = ch.filter(function (x) { return shown(x.r); }).sort(function (a, b) { return b.r.value - a.r.value; })[0];
    var mt = [];
    if (shownPost.length) mt.push("After the training, agreement ranged from " + fmt(shownPost[0].overall.value, "pct") + " (“" + lc(shownPost[0].item_label) + "”) to " +
      fmt(shownPost[shownPost.length - 1].overall.value, "pct") + " (“" + lc(shownPost[shownPost.length - 1].item_label) + "”).");
    if (big) mt.push("The largest self-rated change was on “" + lc(big.m.item_label) + "” (" + fmt(big.r.value, "points") + " points), so that is where people felt they learned most.");
    el.appendChild(means(mt, ["Read the before bars as a rough guide, not a measured baseline.",
      "For a true before-and-after, ask the same three questions at the start of a sample of sessions."]));
  }

  function renderQuality() {
    var el = slot("quality");
    var items = metricsWhere(function (m) { return m.measure === "quality" && m.stat === "agree_pct" && m.overall; });
    if (!items.length) { el.appendChild(empty("No training-quality items in this data build.")); return; }
    el.appendChild(sub("Share who agreed or strongly agreed with each statement about how the training was run. Not everyone answered these; the n under each statement is who did."));
    el.appendChild(rowChart({ rows: items.map(function (m) { return { label: m.item_label, sub: "n = " + fmtInt(m.overall.n) + " answered", lanes: [{ rec: m.overall, series: { name: "", cls: "" } }], flag: flagFor(m.overall) }; }),
      unit: "pct", scale: { lo: 0, hi: 100, mark: "bar", fixed: true }, series: [{}], axisTitle: "% of people who answered",
      ariaLabel: "Training quality ratings", labelWidth: "260px" }));
    el.appendChild(tableDetails("Show as a table", recTable("Training quality", items.map(function (m) { return { name: m.item_label, rec: m.overall }; }), "pct", "Statement")));
    var s2 = items.filter(function (m) { return shown(m.overall); }).sort(function (a, b) { return a.overall.value - b.overall.value; });
    var mt = [];
    if (s2.length) mt.push("Lowest-rated: “" + lc(s2[0].item_label) + "” at " + fmt(s2[0].overall.value, "pct") + " of " + fmtInt(s2[0].overall.n) + ".");
    var miss = s2.find(function (m) { return m.overall.n_missing; });
    if (miss) mt.push(fmtInt(miss.overall.n_missing) + " people did not answer “" + lc(miss.item_label) + "”, so these shares describe those who did.");
    el.appendChild(means(mt, ["Share these results with presenters each quarter, and pair the lowest-rated item with the “how to improve” comments below."]));
  }

  function distBins(prefix) {
    return metricsWhere(function (m) { return m.key.indexOf(prefix + ".") === 0 && m.dist_bin != null && m.overall; })
      .map(function (m) { return { bin: m.dist_bin, rec: m.overall }; })
      .sort(function (a, b) { return a.bin - b.bin; });
  }
  function renderRecommend() {
    var el = slot("recommend");
    var tiles = h("div", { class: "tiles" });
    ["mean", "median", "nps"].forEach(function (st) {
      var m = BY.get("recommend.score." + st);
      if (m && m.overall) add(tiles, tile(st === "nps" ? "Net Promoter Score" : "Would recommend: " + st + " score", m.overall, m.unit, st === "nps" ? "(−100 to +100)" : "/ 10"));
    });
    ["mean", "median"].forEach(function (st) {
      var m = BY.get("call_988.likelihood." + st);
      if (m && m.overall) add(tiles, tile("Likely to call 988: " + st + " score", m.overall, m.unit, "/ 10"));
    });
    if (!tiles.childNodes.length) { el.appendChild(empty("No recommend or call-988 numbers in this data build.")); return; }
    el.appendChild(sub("“How likely are you to recommend the training?” and “How likely are you to call 988?”, both on a 0–10 scale."));
    el.appendChild(tiles);
    var rb = distBins("recommend.score");
    if (rb.length) {
      el.appendChild(h("h3", null, "How people scored “would recommend”"));
      var bands = [{ from: 0, to: 6, label: "Detractors (0–6)" }, { from: 7, to: 8, label: "Passives (7–8)" }, { from: 9, to: 10, label: "Promoters (9–10)" }];
      el.appendChild(distChart({ bins: rb, unit: "pct", bands: bands, axisTitle: "", ariaLabel: "Distribution of recommend scores from 0 to 10" }));
      el.appendChild(tableDetails("Show as a table", recTable("Recommend score distribution", rb.map(function (b) { return { name: "Score " + b.bin, rec: b.rec }; }), "pct", "Score")));
    }
    var cb = distBins("call_988.likelihood");
    if (cb.length) {
      el.appendChild(h("h3", null, "How people scored “likely to call 988”"));
      el.appendChild(distChart({ bins: cb, unit: "pct", axisTitle: "score (0 = not at all likely, 10 = extremely likely)", ariaLabel: "Distribution of likelihood-to-call-988 scores" }));
      el.appendChild(tableDetails("Show as a table", recTable("Likely-to-call-988 score distribution", cb.map(function (b) { return { name: "Score " + b.bin, rec: b.rec }; }), "pct", "Score")));
    }
    var mt = [];
    var nps = overall("recommend.score.nps");
    if (shown(nps)) mt.push("Net Promoter Score is " + fmt(nps.value, "nps") + " (based on " + fmtInt(nps.n) + " people). It is the share who gave 9–10 minus the share who gave 0–6, so it runs from −100 to +100.");
    var call = overall("call_988.likelihood.mean");
    if (call) {
      mt.push("Only " + fmtInt(call.n) + " people answered the call-988 question" + (call.n_missing ? " (" + fmtInt(call.n_missing) + " skipped it)" : "") + ". Treat that number as describing those who answered, not everyone.");
      if (call.caveat && shown(call)) el.appendChild(caveatBox("Likely to call 988: " + call.caveat));
    }
    el.appendChild(means(mt.length ? mt : ["See the tiles above."], ["Track the recommend score month to month as a simple pulse, reading each change next to its n.",
      "Make the call-988 question harder to skip so it can be used as an outcome measure."]));
  }

  // ---- Compare groups (one filter row scopes the chart, table and summary)
  function renderCompare() {
    var el = slot("compare");
    var cands = metricsWhere(function (m) { return Object.keys(m.dims).length > 0 && m.dist_bin == null; });
    if (!cands.length) { el.appendChild(empty("No group breakdowns in this data build.")); return; }
    el.appendChild(sub("Pick a measure and a way to split people into groups. Bars start at zero; the vertical line marks the result for everyone. Groups with fewer than " + T + " people are not shown on their own."));
    var mSel = h("select", { id: "cmp-metric" });
    var groups = {};
    cands.forEach(function (m) {
      var g = groups[m.measure_label];
      if (!g) { g = groups[m.measure_label] = h("optgroup", { label: m.measure_label }); mSel.appendChild(g); }
      g.appendChild(h("option", { value: m.key }, metricName(m)));
    });
    var dSel = h("select", { id: "cmp-dim" });
    el.appendChild(h("div", { class: "filters" },
      h("label", null, "Measure", mSel),
      h("label", null, "Compare by", dSel)));
    var out = h("div", { "aria-live": "polite" });
    el.appendChild(out);
    var def = cands.find(function (m) { return m.measure === "post" && m.stat === "agree_pct"; }) || cands[0];
    mSel.value = def.key;

    function fillDims(m, keep) {
      var dims = m.dim_order || Object.keys(m.dims);
      dSel.replaceChildren.apply(dSel, dims.map(function (d) { return h("option", { value: d }, META.dimension_labels[d] || d); }));
      dSel.value = dims.indexOf(keep) >= 0 ? keep : (dims.indexOf("county") >= 0 ? "county" : dims[0]);
    }
    function draw() {
      hideTip();
      var m = BY.get(mSel.value), dim = dSel.value, recs = m.dims[dim] || [];
      var isTime = META.time_dimensions.indexOf(dim) >= 0;
      var ref = m.overall && shown(m.overall) ? { value: m.overall.value, label: "Everyone: " + fmt(m.overall.value, m.unit) } : null;
      var title = metricName(m) + ", by " + lc(META.dimension_labels[dim] || dim);
      var nodes = [h("h3", null, title)];
      var sn = scaleNote(m);
      if (sn) nodes.push(sub("Shown " + sn + "."));
      var sorted;
      if (isTime) {
        nodes.push(timeChart({ recs: recs, unit: m.unit, scale: m.scale, ref: ref, ariaLabel: title + ". The table below lists every value." }));
        sorted = recs.slice();
      } else {
        sorted = recs.slice().sort(function (a, b) {
          var pa = a.level === "other_pooled", pb = b.level === "other_pooled";
          if (shown(a) !== shown(b)) return shown(a) ? -1 : 1;
          if (pa !== pb) return pa ? 1 : -1;
          if (shown(a)) return b.value - a.value;
          return a.level_label < b.level_label ? -1 : 1;
        });
        nodes.push(rowChart({ rows: sorted.map(function (r) { return { label: r.level_label, sub: "n = " + fmtInt(r.n), lanes: [{ rec: r, series: { name: "", cls: "" } }], flag: flagFor(r) }; }),
          unit: m.unit, scale: m.scale, ref: ref, series: [{}], axisTitle: m.unit === "pct" ? "% of people who answered, in each group" : (sn || ""),
          ariaLabel: title }));
      }
      var table = recTable(title, sorted.map(function (r) { return { name: r.level_label, rec: r }; }), m.unit, META.dimension_labels[dim] || dim);
      nodes.push(tableDetails("Show as a table", table, function () {
        downloadCSV(m.key + "_by_" + dim + ".csv", CSV_HEAD, sorted.map(function (r) { return csvRow(m, r); }).concat(m.overall ? [csvRow(m, m.overall)] : []));
      }));
      var cav = pickCaveat([m.overall].concat(recs));
      if (cav) nodes.push(caveatBox(cav));
      // Plain-language summary: selection only (highest, lowest, whether their ranges overlap).
      var vis = sorted.filter(function (r) { return shown(r) && r.level !== "other_pooled"; });
      var hidden = recs.filter(function (r) { return !shown(r); }).length;
      var mt = [];
      if (vis.length >= 2) {
        var byVal = vis.slice().sort(function (a, b) { return b.value - a.value; });
        var top = byVal[0], bot = byVal[byVal.length - 1];
        var desc = function (r) { return r.level_label + " (" + fmt(r.value, m.unit) + ", n = " + fmtInt(r.n) + (r.ci_low != null ? ", 95% range " + fmtCI(r, m.unit) : "") + ")"; };
        mt.push("Highest: " + desc(top) + ". Lowest: " + desc(bot) + ".");
        if (top.ci_low != null && bot.ci_high != null) {
          mt.push(top.ci_low <= bot.ci_high
            ? "Their 95% ranges overlap, so this gap could be chance."
            : "Their 95% ranges do not overlap, so the gap is unlikely to be chance alone. It may still reflect who was trained (for example, students vs. staff) rather than the training itself.");
        } else mt.push("No uncertainty range is available for these, so treat the gap with caution.");
      } else if (vis.length === 1) {
        mt.push("Only one group is large enough to show: " + vis[0].level_label + " (" + fmt(vis[0].value, m.unit) + ", n = " + fmtInt(vis[0].n) + ").");
      } else mt.push("No group is large enough to show on its own.");
      if (hidden) mt.push(hidden + (hidden === 1 ? " group has" : " groups have") + " fewer than " + T + " people and " + (hidden === 1 ? "is" : "are") + " not shown on " + (hidden === 1 ? "its" : "their") + " own.");
      nodes.push(means(mt, ["Before acting on a gap, check that both groups have enough people (n) and that their ranges don’t overlap.",
        "For a low group, read its comments and talk with the presenters who serve it; then watch whether the gap closes next quarter."]));
      out.replaceChildren.apply(out, nodes);
    }
    mSel.addEventListener("change", function () { fillDims(BY.get(mSel.value), dSel.value); draw(); });
    dSel.addEventListener("change", draw);
    fillDims(def, "county");
    draw();
  }

  function renderComments() {
    var el = slot("comments");
    var th = VM.themes;
    if (!th) { el.appendChild(empty("Comment themes are not in this data build. Run `make themes`.")); return; }
    el.appendChild(sub("Two open questions were coded into themes by a rule-based classifier that runs offline. A comment can touch several themes, so shares don’t add up to 100%. Only counts are shown here, never comment text."));
    var tops = [];
    (th.field_order || Object.keys(th.fields)).forEach(function (field) {
      var ms = METRICS.filter(function (m) { return m.measure === "themes" && m.field === field && m.overall; });
      if (!ms.length) return;
      var isCatch = function (m) { return Object.prototype.hasOwnProperty.call(CATCH_ALL, m.item); };
      ms.sort(function (a, b) {
        if (isCatch(a) !== isCatch(b)) return isCatch(a) ? 1 : -1;
        if (shown(a.overall) !== shown(b.overall)) return shown(a.overall) ? -1 : 1;
        return (b.overall.value || 0) - (a.overall.value || 0) || (a.item_label < b.item_label ? -1 : 1);
      });
      var n0 = ms[0].overall.n;
      el.appendChild(h("h3", null, "“" + th.fields[field] + "”"));
      el.appendChild(sub("n = " + fmtInt(n0) + " people wrote something here."));
      el.appendChild(rowChart({ rows: ms.map(function (m) { var r = m.overall; return { label: m.item_label, sub: shown(r) ? fmtInt(r.numerator) + " of " + fmtInt(r.n) + " comments" : "n = " + fmtInt(r.n), lanes: [{ rec: r, series: { name: "", cls: "" } }],
        flag: isCatch(m) ? h("span", { class: "flag neutral", title: m.description || "" }, CATCH_ALL[m.item]) : flagFor(r) }; }),
        unit: "pct", scale: { lo: 0, hi: 100, mark: "bar", fixed: true }, series: [{}], axisTitle: "% of people who wrote a comment",
        ariaLabel: "Themes in answers to: " + th.fields[field], labelWidth: "260px" }));
      el.appendChild(tableDetails("Show as a table", recTable(th.fields[field], ms.map(function (m) { return { name: m.item_label + (m.description ? " — " + m.description : ""), rec: m.overall }; }), "pct", "Theme"), function () {
        downloadCSV("themes_" + field + ".csv", CSV_HEAD, ms.map(function (m) { return csvRow(m, m.overall); }));
      }));
      var topic = ms.filter(function (m) { return !isCatch(m) && shown(m.overall); })[0];
      if (topic) tops.push({ field: field, m: topic });
      var q = ms.find(function (m) { return m.item === "audience_question" && shown(m.overall); });
      if (q) tops.push({ field: field, m: q, question: true });
    });
    var v = th.validation || {};
    var how = h("div", { class: "notes-grid" });
    var vtext = v.sample_size ? "A person hand-coded " + fmtInt(v.sample_size) + " comments and compared them with the classifier: " +
      (v.agreement_pct != null ? fmt(v.agreement_pct, "pct") + " agreement" : "agreement not yet measured") +
      (v.cohen_kappa != null ? " (Cohen’s kappa " + v.cohen_kappa.toFixed(2) + ")" : "") + "." : "The classifier has not been checked against hand-coding yet.";
    how.appendChild(h("div", { class: "note" }, h("h3", null, "How comments were coded"), h("p", null, th.method), h("p", null, vtext),
      v.procedure ? h("details", null, h("summary", null, "How the check was done"), h("p", null, v.procedure)) : null));
    var sp = th.spanish, pii = th.pii_screen;
    if (sp || pii) how.appendChild(h("div", { class: "note" }, h("h3", null, "Spanish responses and privacy"),
      sp ? h("p", null, (sp.n_comments != null ? fmtInt(sp.n_comments) + " Spanish comments. " : "") + (sp.handling || "")) : null,
      pii ? h("p", null, "Privacy screen: " + (pii.method || "") + (pii.n_flagged != null ? " " + fmtInt(pii.n_flagged) + " comments were flagged and are never quoted." : "")) : null));
    el.appendChild(how);
    var mt = tops.map(function (t) {
      var share = " (" + fmt(t.m.overall.value, "pct") + " of " + fmtInt(t.m.overall.n) + " comments)";
      if (t.question) return "In the “improve” box, " + fmtInt(t.m.overall.numerator) + " comments asked a question about 988 instead of suggesting a change" + share + ". Those are questions the session left unanswered.";
      return (t.field === "improve" ? "Most common concrete suggestion: “" : "Most often named as valuable: “") + t.m.item_label + "”" + share + ".";
    });
    el.appendChild(means(mt.length ? mt : ["See the charts above."], ["Turn the top improvement theme into one concrete change for next quarter’s sessions, then check this chart again.",
      "To see themes for one county or role, pick a “Comments” measure in Compare groups."]));
  }

  function renderNotes() {
    var el = slot("notes");
    var g = h("div", { class: "notes-grid" });
    g.appendChild(h("div", { class: "note" }, h("h3", null, "How to read the charts"), h("ul", null,
      h("li", null, "Bars start at zero, so their lengths compare fairly."),
      h("li", null, "The thin line with end caps is the 95% range: where the true value most likely sits. Wider means less certain, usually because fewer people answered."),
      h("li", null, "n is the number of people a value is based on, and the text next to it says who they are."),
      h("li", null, "⚠ marks a small group. Any group with fewer than " + T + " people is hidden (and pooled into “Other” where possible), for privacy and because such numbers jump around."))));
    g.appendChild(h("div", { class: "note" }, h("h3", null, "Limits to keep in mind"), h("ul", null,
      h("li", null, RETRO),
      h("li", null, "Everything is self-reported, right after the training. It shows confidence, not behavior months later."),
      h("li", null, "Respondents are not spread evenly across counties and roles. Check the n before comparing groups: results for small groups rest on few people."),
      h("li", null, "There is no comparison group of people who did not take the training."))));
    var steps = h("div", { class: "note" }, h("h3", null, "Refresh with next month’s export"),
      h("p", null, "Save the new survey export (.xlsx) anywhere on the computer, then from the project folder run:"),
      h("pre", { class: "cmd" }, "make setup        # first time on a computer only\nmake run DATA=path/to/new_export.xlsx"),
      h("p", null, "This rebuilds every number and this page (outputs/dashboard.html). New counties, roles or answer labels are flagged in the data checks, not dropped silently. Full steps are in agents/tool/RUN.md."));
    g.appendChild(steps);
    var src = META.source || {};
    g.appendChild(h("div", { class: "note" }, h("h3", null, "Where the numbers come from"), h("ul", null,
      h("li", null, "Survey numbers: outputs/findings.json" + (src.file_sha256 ? " (input fingerprint " + src.file_sha256.slice(0, 12) + ")" : "") + "."),
      h("li", null, "Comment themes: outputs/themes.json" + (META.themes_source && META.themes_source.file_sha256 ? " (fingerprint " + META.themes_source.file_sha256.slice(0, 12) + (META.sources_match === "yes" ? ", same export" : META.sources_match === "unconfirmed" ? ", taken from the cleaned file, so it can't be matched to the export fingerprint directly" : "") + ")" : "") + "."),
      h("li", null, "Each number has a stable ID (hover or see “All numbers”). The memo, slides and video cite the same IDs."),
      h("li", null, "This page contains totals only, never individual answers or comment text."))));
    el.appendChild(g);
    if (VM.caveats && VM.caveats.length) {
      el.appendChild(h("h3", null, "Caveats attached to specific numbers"));
      el.appendChild(h("ul", null, VM.caveats.map(function (c) { return h("li", null, c); })));
    }
    if (VM.validation_report && VM.validation_report.length) {
      var rows = VM.validation_report.map(function (kv) { return h("tr", null, h("th", { scope: "row" }, kv[0]), h("td", { class: "num" }, kv[1] == null ? "—" : typeof kv[1] === "number" ? NF.format(kv[1]) : String(kv[1]))); });
      el.appendChild(tableDetails("Data checks run on this export (counts only)", h("div", { class: "tablewrap" },
        h("table", null, h("caption", null, "From outputs/validation_report.json"), h("thead", null, h("tr", null, h("th", { scope: "col" }, "Check"), h("th", { scope: "col", class: "num" }, "Result"))), h("tbody", null, rows)))));
    }
    if (META.warnings && META.warnings.length) {
      el.appendChild(h("div", { class: "callout warn", role: "note" }, h("p", null, h("b", null, "Build warnings: ")), h("ul", null, META.warnings.map(function (w) { return h("li", null, w); }))));
    }
  }

  function renderAll() {
    var el = slot("all");
    var rows = [];
    METRICS.slice().sort(function (a, b) { return order(a) - order(b) || (a.key < b.key ? -1 : 1); }).forEach(function (m) {
      if (m.overall) rows.push({ m: m, r: m.overall });
      (m.dim_order || Object.keys(m.dims)).forEach(function (d) { m.dims[d].forEach(function (r) { rows.push({ m: m, r: r }); }); });
    });
    el.appendChild(sub("Every number behind this page, with its ID. Search by words or ID; download to open in Excel."));
    var q = h("input", { type: "search", placeholder: "e.g. Prince George's, recommend, 988", "aria-label": "Search numbers" });
    var dims = ["all"].concat(Array.from(new Set(rows.map(function (x) { return x.r.dimension; }))));
    var dSel = h("select", { "aria-label": "Group type" }, dims.map(function (d) { return h("option", { value: d }, d === "all" ? "All group types" : META.dimension_labels[d] || d); }));
    var count = h("p", { class: "count-line", "aria-live": "polite" });
    el.appendChild(h("div", { class: "alltools" }, h("label", null, "Search", q), h("label", null, "Group type", dSel),
      h("button", { type: "button", onclick: function () { downloadCSV("all_numbers.csv", CSV_HEAD, filtered().map(function (x) { return csvRow(x.m, x.r); })); } }, "Download as CSV")));
    el.appendChild(count);
    var tbody = h("tbody");
    el.appendChild(h("div", { class: "tablewrap" }, h("table", null, h("caption", { class: "sr" }, "All published numbers"),
      h("thead", null, h("tr", null, ["Measure", "Group", "Value", "95% range", "n", "Who is counted", "Notes", "ID"].map(function (t, i) { return h("th", { scope: "col", class: i >= 2 && i <= 4 ? "num" : null }, t); }))), tbody)));
    function filtered() {
      var words = q.value.toLowerCase().split(/\s+/).filter(Boolean), d = dSel.value;
      return rows.filter(function (x) {
        if (d !== "all" && x.r.dimension !== d) return false;
        if (!words.length) return true;
        var hay = (x.m.measure_label + " " + metricName(x.m) + " " + x.r.level_label + " " + x.r.id + " " + x.r.denominator).toLowerCase();
        return words.every(function (w) { return hay.indexOf(w) >= 0; });
      });
    }
    function draw() {
      var f = filtered(), LIMIT = 400;
      count.textContent = "Showing " + fmtInt(Math.min(f.length, LIMIT)) + " of " + fmtInt(f.length) + " matching numbers (" + fmtInt(rows.length) + " in total).";
      tbody.replaceChildren.apply(tbody, f.slice(0, LIMIT).map(function (x) {
        var r = x.r, m = x.m;
        return h("tr", null, h("td", null, m.measure_label + ": " + metricName(m)),
          h("td", null, (META.dimension_labels[r.dimension] || r.dimension) + (r.dimension === "overall" ? "" : ": " + r.level_label)),
          h("td", { class: "num" }, shown(r) ? fmt(r.value, m.unit) : "not shown"), h("td", { class: "num" }, fmtCI(r, m.unit)),
          h("td", { class: "num" }, fmtInt(r.n)), h("td", null, r.denominator), h("td", null, notes(r)), h("td", null, h("span", { class: "mono" }, r.id)));
      }));
    }
    q.addEventListener("input", draw);
    dSel.addEventListener("change", draw);
    draw();
  }

  function renderFoot() {
    $("#foot").appendChild(h("p", null, "Built by agents/tool/build.py from outputs/findings.json and outputs/themes.json. Totals only: no individual answers or comment text are in this file. It works offline and can be emailed as a single file."));
  }

  window.addEventListener("beforeprint", function () { document.querySelectorAll("details").forEach(function (d) { d.open = true; }); });

  [renderHeader, renderGlance, renderLearning, renderQuality, renderRecommend, renderCompare, renderComments, renderNotes, renderAll, renderFoot]
    .forEach(function (fn) {
      try { fn(); } catch (err) {
        var where = fn.name.replace("render", "").toLowerCase();
        var target = slot(where) || $("#main");
        if (target) target.appendChild(h("p", { class: "callout warn" }, "This part of the page could not be drawn (" + err.message + "). The numbers are still in “All numbers” and in outputs/findings.json."));
        if (window.console) console.error(err);
      }
    });
})();
