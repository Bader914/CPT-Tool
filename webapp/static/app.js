"use strict";

const HHSK_BLUE = "#1A76BB", HHSK_DARK = "#0D4F86", ACCENT = "#00A3A1", RED = "#e53935";
const $ = (id) => document.getElementById(id);

let soundings = [];   // {file, name, result, manualLagen}
let current = -1;

const fileInput = $("fileInput"), dropzone = $("dropzone");

// ── Upload-interactie ──
dropzone.addEventListener("click", () => fileInput.click());
["dragover", "dragenter"].forEach(ev => dropzone.addEventListener(ev, e => {
  e.preventDefault(); dropzone.classList.add("drag");
}));
["dragleave", "drop"].forEach(ev => dropzone.addEventListener(ev, e => {
  e.preventDefault(); dropzone.classList.remove("drag");
}));
dropzone.addEventListener("drop", e => { e.preventDefault(); addFiles(e.dataTransfer.files); });
fileInput.addEventListener("change", () => addFiles(fileInput.files));

async function addFiles(files) {
  const lijst = Array.from(files).filter(f => f.name.toLowerCase().endsWith(".gef"));
  if (!lijst.length) { setStatus("Geen .gef-bestanden gekozen.", "err"); return; }
  for (const f of lijst) {
    soundings.push({ file: f, name: f.name, result: null, manualLagen: null });
  }
  vulSelect();
  $("dzFile").textContent = `✓ ${soundings.length} sondering(en) geladen`;
  $("resultaten").classList.remove("hidden");
  current = soundings.length - lijst.length; // eerste nieuwe
  $("sondSelect").value = current;
  await analyseHuidige();
}

function vulSelect() {
  $("sondSelect").innerHTML = soundings.map((s, i) =>
    `<option value="${i}">${s.name}</option>`).join("");
}

function setStatus(msg, type = "") {
  $("status").textContent = msg;
  $("status").className = "status" + (type ? " " + type : "");
}

// ── Materialen-editor (uitgangspunten) ──
const GRONDSOORTEN = ["zand", "klei", "veen"];
let matRendered = false;
function rendMatEditor(materialen) {
  const rij = (g, m) => `<tr data-g="${g}">
    <td><span class="swatch" style="background:${({zand:"#FFD54F",klei:"#4CAF50",veen:"#7B4B27"})[g]}"></span>${g}</td>
    <td><input class="m-gs" type="number" step="0.1" value="${m.gamma_sat ?? ""}"></td>
    <td><input class="m-gu" type="number" step="0.1" value="${m.gamma_unsat ?? ""}"></td>
    <td><input class="m-nkt" type="number" step="0.1" value="${m.nkt ?? ""}" placeholder="—"></td>
    <td><input class="m-s" type="number" step="0.01" value="${m.S ?? ""}" placeholder="—"></td>
    <td><input class="m-m" type="number" step="0.01" value="${m.m ?? ""}" placeholder="—"></td>
    <td><input class="m-vc" type="number" step="0.01" value="${m.VC ?? ""}"></td></tr>`;
  $("matEditor").innerHTML =
    `<thead><tr><th>Grondsoort</th><th>γ_sat</th><th>γ_unsat</th><th>Nkt</th><th>S</th><th>m</th><th>VC</th></tr></thead>
     <tbody>${GRONDSOORTEN.map(g => rij(g, materialen[g] || {})).join("")}</tbody>`;
  $("matEditor").querySelectorAll("input").forEach(i => i.addEventListener("change", analyseHuidige));
  matRendered = true;
}
function leesMaterialen() {
  const out = {};
  $("matEditor").querySelectorAll("tbody tr").forEach(tr => {
    const g = tr.dataset.g;
    const v = (cls) => { const x = tr.querySelector(cls).value; return x === "" ? null : parseFloat(x); };
    out[g] = { gamma_sat: v(".m-gs"), gamma_unsat: v(".m-gu"), nkt: v(".m-nkt"),
               S: v(".m-s"), m: v(".m-m"), VC: v(".m-vc") };
  });
  return out;
}

// ── Parameters lezen ──
function huidigeParams() {
  const num = (id) => { const v = $(id).value; return v === "" ? null : parseFloat(v); };
  const p = {
    gwl_nap: num("gwl") ?? 0.0,
    su_methode: $("suMethode").value,
    a_factor: num("afac"),
    gamma_bron: $("gammaBron").value,
    t_factor: num("tfac") ?? 1.645,
    knik_nap: num("knik"), stijghoogte_nap: num("stijg"),
    top_zand_nap: num("topzand"), indringing: num("indr") ?? 0.0,
  };
  if ($("vbChk").checked && num("vbDiepte") != null)
    p.voorboring = { actief: true, diepte: num("vbDiepte") };
  if (matRendered) p.materialen = leesMaterialen();
  if ($("handmatigChk").checked) {
    const lagen = leesLagenEditor();
    if (lagen.length) p.lagen = lagen;
  }
  Object.keys(p).forEach(k => p[k] === null && delete p[k]);
  return p;
}

// ── Analyse ──
async function analyseHuidige() {
  if (current < 0) return;
  const s = soundings[current];
  setStatus("Bezig met analyseren…");
  const fd = new FormData();
  fd.append("file", s.file);
  fd.append("params", JSON.stringify(huidigeParams()));
  try {
    const res = await fetch("/api/analyse", { method: "POST", body: fd });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || res.status); }
    s.result = await res.json();
    toonResultaat(s.result);
    setStatus("Analyse klaar ✓", "ok");
  } catch (e) { setStatus("Fout: " + e.message, "err"); }
}

$("sondSelect").addEventListener("change", e => {
  current = parseInt(e.target.value);
  if (soundings[current].result) toonResultaat(soundings[current].result);
  else analyseHuidige();
});
$("herberekenBtn").addEventListener("click", analyseHuidige);
["suMethode", "gwl", "afac", "knik", "stijg", "topzand", "indr",
 "gammaBron", "vbChk", "vbDiepte", "tfac"].forEach(id =>
  $(id).addEventListener("change", analyseHuidige));

// ── Lagen-editor ──
function lagenEditorRij(l = {}) {
  const opts = GRONDSOORTEN.map(g =>
    `<option ${l.grondsoort === g ? "selected" : ""}>${g}</option>`).join("");
  return `<tr>
    <td><input type="number" step="0.1" class="le-bk" value="${l.bovenkant ?? ""}"></td>
    <td><select class="le-gs">${opts}</select></td>
    <td><input type="number" step="0.1" class="le-nkt" value="${l.nkt ?? ""}" placeholder="auto"></td>
    <td><input type="number" step="0.01" class="le-s" value="${l.S ?? ""}" placeholder="auto"></td>
    <td><input type="number" step="0.01" class="le-m" value="${l.m ?? ""}" placeholder="auto"></td>
    <td><button class="btn ghost mini le-del">✕</button></td></tr>`;
}
function rendLagenEditor(rows) {
  $("lagenEditor").innerHTML =
    `<thead><tr><th>Bovenkant [m NAP]</th><th>Grondsoort</th><th>Nkt</th><th>S</th><th>m</th><th></th></tr></thead>
     <tbody>${rows.map(lagenEditorRij).join("")}</tbody>`;
  $("lagenEditor").querySelectorAll(".le-del").forEach(b =>
    b.addEventListener("click", () => { b.closest("tr").remove(); }));
}
function leesLagenEditor() {
  return Array.from($("lagenEditor").querySelectorAll("tbody tr")).map(tr => {
    const g = (cls) => { const v = tr.querySelector(cls).value; return v === "" ? null : parseFloat(v); };
    return { bovenkant: g(".le-bk"), grondsoort: tr.querySelector(".le-gs").value,
             nkt: g(".le-nkt"), S: g(".le-s"), m: g(".le-m") };
  }).filter(l => l.bovenkant !== null);
}
$("addLaagBtn").addEventListener("click", () => {
  $("lagenEditor").querySelector("tbody").insertAdjacentHTML("beforeend", lagenEditorRij());
  $("lagenEditor").querySelectorAll(".le-del").forEach(b =>
    b.onclick = () => b.closest("tr").remove());
});
$("vulAutoBtn").addEventListener("click", () => {
  const r = soundings[current] && soundings[current].result;
  if (!r) return;
  rendLagenEditor(r.lagen.map(l => ({ bovenkant: l.top, grondsoort: l.grondsoort })));
});

// ── Export ──
$("exportBtn").addEventListener("click", () => {
  const r = soundings[current] && soundings[current].result;
  if (!r) return;
  const cols = ["diepte_nap", "qc", "qt", "fs", "Rf", "gamma_sat", "u0", "sigma_v0", "sigma_eff", "qnet", "Su"];
  const head = ["NAP", "qc", "qt", "fs", "Rf", "gamma_sat", "u0", "sigma_v0", "sigma_eff", "qnet", "Su", "grondsoort"];
  let csv = head.join(";") + "\n";
  for (let i = 0; i < r.n; i++) {
    csv += cols.map(c => r[c][i] ?? "").join(";") + ";" + r.grondsoort[i] + "\n";
  }
  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = (r.bestand || "cpt") + "_resultaat.csv";
  a.click();
});

// ── Resultaat tonen ──
function toonResultaat(d) {
  $("bestandTitel").textContent = "2 · Resultaat — " + (d.bestand || "");
  const s = d.su_samenvatting || {};
  const kpis = [
    ["Maaiveld", d.maaiveld_nap + " m NAP"], ["Meetpunten", d.n], ["a-factor", d.a_factor],
    ["Methode", d.su_methode === "shansep" ? "SHANSEP" : "Nkt"],
    ["Su gemiddeld", (s.gem ?? "—") + " kPa"], ["Su karakteristiek", (s.kar ?? "—") + " kPa"],
  ];
  $("kpis").innerHTML = kpis.map(([l, v]) =>
    `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
  const bron = d.gamma_bron === "materiaal" ? "γ uit materiaaltabel" : "γ uit Lengkeek";
  $("meldingen").textContent = ((d.eenheid_meldingen && d.eenheid_meldingen.length)
    ? "Eenheden genormaliseerd: " + d.eenheid_meldingen.join("; ") + " · " : "")
    + (d.handmatig ? "Handmatige lagen" : "Automatische classificatie (Robertson)") + " · " + bron;
  if (!matRendered && d.materialen) rendMatEditor(d.materialen);
  plotProfiel(d); plotSpanning(d); plotSu(d); lagenTabel(d);
}

// ── Plots ──
function plotProfiel(d) {
  const y = d.diepte_nap, traces = [];
  d.lagen.forEach(l => traces.push({
    type: "bar", x: ["Lithologie"], y: [l.top - l.onder], base: l.onder, width: 0.8,
    marker: { color: d.kleuren[l.grondsoort] || "#bbb", line: { color: "#fff", width: 1 } },
    text: l.grondsoort, textposition: "inside", insidetextanchor: "middle",
    hovertemplate: `${l.grondsoort}<br>NAP ${l.top} → ${l.onder} (${l.dikte} m)<extra></extra>`,
    xaxis: "x", yaxis: "y",
  }));
  traces.push({ x: d.qc, y, mode: "lines", name: "qc", line: { color: "#90caf9", width: 1, dash: "dot" }, xaxis: "x2", yaxis: "y2",
    hovertemplate: "qc=%{x:.2f} MPa<extra></extra>" });
  traces.push({ x: d.qt, y, mode: "lines", name: "qt", line: { color: HHSK_BLUE, width: 1.4 }, xaxis: "x2", yaxis: "y2",
    hovertemplate: "qt=%{x:.2f} MPa<br>NAP %{y:.2f}<extra></extra>" });
  traces.push({ x: d.Rf, y, mode: "lines", line: { color: RED, width: 1 }, xaxis: "x3", yaxis: "y3",
    hovertemplate: "Rf=%{x:.1f}%<extra></extra>" });
  const layout = baseLayout(3);
  layout.xaxis = { domain: [0, 0.16], showticklabels: false, title: "Boorstaat" };
  layout.xaxis2 = { domain: [0.22, 0.62], title: "qc / qt [MPa]" };
  layout.showlegend = false;
  layout.xaxis3 = { domain: [0.70, 1.0], title: "Rf [%]", range: [0, 12] };
  layout.yaxis = { title: "Niveau [m NAP]" };
  layout.yaxis2 = { matches: "y", showticklabels: false };
  layout.yaxis3 = { matches: "y", showticklabels: false };
  layout.barmode = "overlay";
  Plotly.newPlot("plotProfiel", traces, layout, { responsive: true, displayModeBar: false });
}

function plotSpanning(d) {
  const y = d.diepte_nap;
  const traces = [
    { x: d.u0, y, mode: "lines", line: { color: HHSK_BLUE, width: 1.6 }, name: "u₀", xaxis: "x", yaxis: "y" },
    { x: d.sigma_v0, y, mode: "lines", line: { color: "#5d4037", width: 1.6 }, name: "σv0", xaxis: "x2", yaxis: "y2" },
    { x: d.sigma_eff, y, mode: "lines", line: { color: ACCENT, width: 1.6, dash: "dash" }, name: "σ'v0", xaxis: "x2", yaxis: "y2" },
  ];
  const layout = baseLayout(2);
  layout.xaxis = { domain: [0, 0.46], title: "Waterdruk u₀ [kPa]" };
  layout.xaxis2 = { domain: [0.56, 1], title: "σv0 / σ'v0 [kPa]" };
  layout.yaxis = { title: "Niveau [m NAP]" };
  layout.yaxis2 = { matches: "y", showticklabels: false };
  layout.showlegend = true; layout.legend = { orientation: "h", y: 1.08 };
  Plotly.newPlot("plotSpanning", traces, layout, { responsive: true, displayModeBar: false });
}

function plotSu(d) {
  const y = d.diepte_nap;
  const traces = [{ x: d.Su, y, mode: "lines", line: { color: "#ef9a9a", width: 1 }, opacity: 0.8,
    hovertemplate: "Su=%{x:.1f} kPa<br>NAP %{y:.2f}<extra></extra>" }];
  d.lagen.forEach(l => { if (l.su_gem != null)
    traces.push({ x: [l.su_gem, l.su_gem], y: [l.top, l.onder], mode: "lines", line: { color: "#111", width: 2 } }); });
  const layout = {
    height: 540, margin: { l: 55, r: 15, t: 25, b: 45 }, paper_bgcolor: "#fff", plot_bgcolor: "#fff",
    font: { family: "Inter, sans-serif", size: 12, color: HHSK_DARK },
    xaxis: { title: "Su [kPa]" }, yaxis: { title: "Niveau [m NAP]" }, showlegend: false,
  };
  Plotly.newPlot("plotSu", traces, layout, { responsive: true, displayModeBar: false });
}

function lagenTabel(d) {
  const rows = d.lagen.map(l =>
    `<tr><td><span class="swatch" style="background:${d.kleuren[l.grondsoort] || "#bbb"}"></span>${l.grondsoort}</td>
     <td>${l.top}</td><td>${l.onder}</td><td>${l.dikte}</td><td>${l.n ?? "—"}</td>
     <td>${l.su_gem ?? "—"}</td><td>${l.VC_data ?? "—"}</td><td>${l.su_kar ?? "—"}</td>
     <td>${l.su_kar_mat ?? "—"}</td></tr>`).join("");
  $("lagenTabel").innerHTML =
    `<thead><tr><th>Grondsoort</th><th>Top [m NAP]</th><th>Onder [m NAP]</th><th>Dikte [m]</th><th>n</th>
     <th>Su gem [kPa]</th><th>VC</th><th>Su kar (data) [kPa]</th><th>Su kar (mat-VC) [kPa]</th></tr></thead><tbody>${rows}</tbody>`;
}

// ── Alle sonderingen samen ──
const KLEUREN = ["#1A76BB", "#e53935", "#00A3A1", "#f59e0b", "#8b5cf6", "#22c55e", "#ec4899", "#0D4F86"];
$("analyseAlleBtn").addEventListener("click", async () => {
  for (let i = 0; i < soundings.length; i++) {
    if (!soundings[i].result) { current = i; await analyseHuidige(); }
  }
  current = parseInt($("sondSelect").value);
  plotAlle();
});
function plotAlle() {
  const traces = [];
  soundings.forEach((s, i) => {
    if (!s.result) return;
    traces.push({ x: s.result.Su, y: s.result.diepte_nap, mode: "lines", name: s.name,
      line: { color: KLEUREN[i % KLEUREN.length], width: 1.6 },
      hovertemplate: `${s.name}<br>Su=%{x:.1f} kPa<br>NAP %{y:.2f}<extra></extra>` });
  });
  Plotly.newPlot("plotAlle", traces, {
    height: 560, margin: { l: 55, r: 15, t: 30, b: 45 }, paper_bgcolor: "#fff", plot_bgcolor: "#fff",
    font: { family: "Inter, sans-serif", size: 12, color: HHSK_DARK },
    xaxis: { title: "Su [kPa]" }, yaxis: { title: "Niveau [m NAP]" },
    legend: { orientation: "h", y: 1.04, font: { size: 10 } },
  }, { responsive: true, displayModeBar: false });
}

// ── Vergelijk met Deltares ──
const cmpZone = $("cmpZone"), cmpInput = $("cmpInput");
let cmpData = null; // {nap:[], su:[]}
cmpZone.addEventListener("click", () => cmpInput.click());
["dragover", "dragenter"].forEach(ev => cmpZone.addEventListener(ev, e => { e.preventDefault(); cmpZone.classList.add("drag"); }));
["dragleave", "drop"].forEach(ev => cmpZone.addEventListener(ev, e => { e.preventDefault(); cmpZone.classList.remove("drag"); }));
cmpZone.addEventListener("drop", e => { e.preventDefault(); if (e.dataTransfer.files[0]) leesCmp(e.dataTransfer.files[0]); });
cmpInput.addEventListener("change", () => { if (cmpInput.files[0]) leesCmp(cmpInput.files[0]); });

function leesCmp(file) {
  const reader = new FileReader();
  reader.onload = () => {
    const txt = reader.result.trim();
    const sep = txt.includes(";") ? ";" : (txt.includes("\t") ? "\t" : ",");
    const lines = txt.split(/\r?\n/);
    // header met NAP/Su detecteren, anders kolom 0/1
    const head = lines[0].split(sep).map(h => h.trim().toLowerCase());
    let inap = head.findIndex(h => h.includes("nap")), isu = head.findIndex(h => h.includes("su"));
    let start = 1;
    if (inap < 0 || isu < 0) { inap = 0; isu = 1; start = isNaN(parseFloat(head[0])) ? 1 : 0; }
    const nap = [], su = [];
    for (let i = start; i < lines.length; i++) {
      const c = lines[i].split(sep);
      const a = parseFloat(c[inap]), b = parseFloat(c[isu]);
      if (!isNaN(a) && !isNaN(b)) { nap.push(a); su.push(b); }
    }
    if (!nap.length) { $("cmpFile").textContent = "✗ geen geldige rijen"; return; }
    cmpData = { nap, su };
    $("cmpFile").textContent = `✓ ${file.name} (${nap.length} punten)`;
    plotCmp();
  };
  reader.readAsText(file);
}

function plotCmp() {
  const r = soundings[current] && soundings[current].result;
  if (!r || !cmpData) return;
  // ons gemiddelde Su-profiel per 0.5 m NAP-bin
  const bins = {};
  for (let i = 0; i < r.n; i++) {
    if (r.Su[i] == null) continue;
    const b = Math.round(r.diepte_nap[i] * 2) / 2;
    (bins[b] = bins[b] || []).push(r.Su[i]);
  }
  const bnap = Object.keys(bins).map(Number).sort((a, b) => a - b);
  const bsu = bnap.map(b => bins[b].reduce((x, y) => x + y, 0) / bins[b].length);

  const traces = [
    { x: bsu, y: bnap, mode: "lines+markers", name: "Onze tool (gem)", line: { color: HHSK_BLUE, width: 2 } },
    { x: cmpData.su, y: cmpData.nap, mode: "lines+markers", name: "Deltares", line: { color: RED, width: 2, dash: "dash" } },
  ];
  Plotly.newPlot("plotCmp", traces, {
    height: 560, margin: { l: 55, r: 15, t: 30, b: 45 }, paper_bgcolor: "#fff", plot_bgcolor: "#fff",
    font: { family: "Inter, sans-serif", size: 12, color: HHSK_DARK },
    xaxis: { title: "Su [kPa]" }, yaxis: { title: "Niveau [m NAP]" },
    legend: { orientation: "h", y: 1.05 },
  }, { responsive: true, displayModeBar: false });

  // afwijking: interpoleer ons profiel op de Deltares-NAP
  const interp = (x) => {
    if (x >= bnap[bnap.length - 1]) return bsu[bnap.length - 1];
    if (x <= bnap[0]) return bsu[0];
    for (let i = 1; i < bnap.length; i++) {
      if (x <= bnap[i]) {
        const t = (x - bnap[i - 1]) / (bnap[i] - bnap[i - 1]);
        return bsu[i - 1] + t * (bsu[i] - bsu[i - 1]);
      }
    }
    return bsu[0];
  };
  const d = cmpData.nap.map((nap, i) => cmpData.su[i] - interp(nap)).filter(v => !isNaN(v));
  const gem = d.reduce((a, b) => a + b, 0) / d.length;
  const absg = d.reduce((a, b) => a + Math.abs(b), 0) / d.length;
  const rmse = Math.sqrt(d.reduce((a, b) => a + b * b, 0) / d.length);
  $("cmpMetrics").innerHTML = [
    ["Gem. verschil", gem.toFixed(1) + " kPa"], ["Gem. absoluut", absg.toFixed(1) + " kPa"], ["RMSE", rmse.toFixed(1) + " kPa"],
  ].map(([l, v]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
}

function baseLayout(cols) {
  return {
    grid: { rows: 1, columns: cols, pattern: "independent" },
    height: 540, margin: { l: 55, r: 15, t: 40, b: 45 },
    paper_bgcolor: "#fff", plot_bgcolor: "#fff",
    font: { family: "Inter, sans-serif", size: 12, color: HHSK_DARK }, showlegend: false,
  };
}
