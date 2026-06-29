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

// ── Parameters lezen ──
function huidigeParams() {
  const num = (id) => { const v = $(id).value; return v === "" ? null : parseFloat(v); };
  const p = {
    gwl_nap: num("gwl") ?? 0.0,
    su_methode: $("suMethode").value,
    a_factor: num("afac"),
    knik_nap: num("knik"), stijghoogte_nap: num("stijg"),
    top_zand_nap: num("topzand"), indringing: num("indr") ?? 0.0,
  };
  if ($("handmatigChk").checked) {
    const lagen = leesLagenEditor();
    if (lagen.length) p.lagen = lagen;
  }
  // null-waarden weglaten zodat backend-defaults gelden
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
["suMethode", "gwl", "afac", "knik", "stijg", "topzand", "indr"].forEach(id =>
  $(id).addEventListener("change", analyseHuidige));

// ── Lagen-editor ──
const GRONDSOORTEN = ["zand", "klei", "veen"];
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
  $("meldingen").textContent = (d.eenheid_meldingen && d.eenheid_meldingen.length)
    ? "Eenheden genormaliseerd: " + d.eenheid_meldingen.join("; ")
    : (d.handmatig ? "Handmatige lagen gebruikt." : "Automatische classificatie (Robertson).");
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
  traces.push({ x: d.qc, y, mode: "lines", line: { color: HHSK_BLUE, width: 1.4 }, xaxis: "x2", yaxis: "y2",
    hovertemplate: "qc=%{x:.2f} MPa<br>NAP %{y:.2f}<extra></extra>" });
  traces.push({ x: d.Rf, y, mode: "lines", line: { color: RED, width: 1 }, xaxis: "x3", yaxis: "y3",
    hovertemplate: "Rf=%{x:.1f}%<extra></extra>" });
  const layout = baseLayout(3);
  layout.xaxis = { domain: [0, 0.16], showticklabels: false, title: "Boorstaat" };
  layout.xaxis2 = { domain: [0.22, 0.62], title: "qc [MPa]" };
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
     <td>${l.top}</td><td>${l.onder}</td><td>${l.dikte}</td><td>${l.su_gem ?? "—"}</td></tr>`).join("");
  $("lagenTabel").innerHTML =
    `<thead><tr><th>Grondsoort</th><th>Top [m NAP]</th><th>Onder [m NAP]</th><th>Dikte [m]</th><th>Su gem [kPa]</th></tr></thead><tbody>${rows}</tbody>`;
}

function baseLayout(cols) {
  return {
    grid: { rows: 1, columns: cols, pattern: "independent" },
    height: 540, margin: { l: 55, r: 15, t: 40, b: 45 },
    paper_bgcolor: "#fff", plot_bgcolor: "#fff",
    font: { family: "Inter, sans-serif", size: 12, color: HHSK_DARK }, showlegend: false,
  };
}
