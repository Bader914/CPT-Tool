"use strict";

const HHSK_BLUE = "#1A76BB", HHSK_DARK = "#0D4F86", ACCENT = "#00A3A1";
const RED = "#e53935";
let gekozenBestand = null;

const $ = (id) => document.getElementById(id);
const fileInput = $("fileInput"), dropzone = $("dropzone");

// ── Upload-interactie ──
dropzone.addEventListener("click", () => fileInput.click());
["dragover", "dragenter"].forEach(ev => dropzone.addEventListener(ev, e => {
  e.preventDefault(); dropzone.classList.add("drag");
}));
["dragleave", "drop"].forEach(ev => dropzone.addEventListener(ev, e => {
  e.preventDefault(); dropzone.classList.remove("drag");
}));
dropzone.addEventListener("drop", e => {
  if (e.dataTransfer.files.length) setBestand(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) setBestand(fileInput.files[0]);
});

function setBestand(f) {
  gekozenBestand = f;
  $("dzFile").textContent = "✓ " + f.name;
  $("analyseBtn").disabled = false;
  setStatus("");
}

function setStatus(msg, type = "") {
  const el = $("status");
  el.textContent = msg;
  el.className = "status" + (type ? " " + type : "");
}

// ── Analyse ──
$("analyseBtn").addEventListener("click", async () => {
  if (!gekozenBestand) return;
  setStatus("Bezig met analyseren…");
  $("analyseBtn").disabled = true;
  const fd = new FormData();
  fd.append("file", gekozenBestand);
  fd.append("gwl_nap", $("gwl").value || "0");
  try {
    const res = await fetch("/api/analyse", { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || ("HTTP " + res.status));
    }
    const data = await res.json();
    toonResultaat(data);
    setStatus("Analyse klaar ✓", "ok");
  } catch (e) {
    setStatus("Fout: " + e.message, "err");
  } finally {
    $("analyseBtn").disabled = false;
  }
});

// ── Resultaat tonen ──
function toonResultaat(d) {
  $("resultaten").classList.remove("hidden");
  $("bestandTitel").textContent = "2 · Resultaat — " + (d.bestand || "");

  // KPI's
  const s = d.su_samenvatting || {};
  const kpis = [
    ["Maaiveld", d.maaiveld_nap + " m NAP"],
    ["Meetpunten", d.n],
    ["a-factor", d.a_factor],
    ["Su gemiddeld", (s.gem ?? "—") + " kPa"],
    ["Su karakteristiek", (s.kar ?? "—") + " kPa"],
    ["VC", s.VC ?? "—"],
  ];
  $("kpis").innerHTML = kpis.map(([l, v]) =>
    `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
  $("meldingen").textContent = (d.eenheid_meldingen && d.eenheid_meldingen.length)
    ? "Eenheden genormaliseerd: " + d.eenheid_meldingen.join("; ") : "";

  plotProfiel(d);
  plotSpanning(d);
  plotSu(d);
  lagenTabel(d);
  $("resultaten").scrollIntoView({ behavior: "smooth" });
}

const yAs = (t) => ({ title: t, autorange: true });
const baseLayout = (titels, widths) => ({
  grid: { rows: 1, columns: titels.length, pattern: "independent" },
  height: 560, margin: { l: 55, r: 15, t: 40, b: 45 },
  paper_bgcolor: "#fff", plot_bgcolor: "#fff",
  font: { family: "Inter, sans-serif", size: 12, color: HHSK_DARK },
  showlegend: false,
});

// Boorstaat | qc | Rf
function plotProfiel(d) {
  const y = d.diepte_nap;
  const traces = [];
  // boorstaat als gekleurde balken (xaxis)
  d.lagen.forEach(l => {
    traces.push({
      type: "bar", x: ["Lithologie"], y: [l.top - l.onder], base: l.onder, width: 0.8,
      marker: { color: d.kleuren[l.grondsoort] || "#bbb", line: { color: "#fff", width: 1 } },
      text: l.grondsoort, textposition: "inside", insidetextanchor: "middle",
      hovertemplate: `${l.grondsoort}<br>NAP ${l.top} → ${l.onder} (${l.dikte} m)<extra></extra>`,
      xaxis: "x", yaxis: "y",
    });
  });
  traces.push({ x: d.qc, y, mode: "lines", line: { color: HHSK_BLUE, width: 1.4 },
    name: "qc", xaxis: "x2", yaxis: "y2", hovertemplate: "qc=%{x:.2f} MPa<br>NAP %{y:.2f}<extra></extra>" });
  traces.push({ x: d.Rf, y, mode: "lines", line: { color: RED, width: 1 },
    name: "Rf", xaxis: "x3", yaxis: "y3", hovertemplate: "Rf=%{x:.1f}%<extra></extra>" });

  const layout = baseLayout();
  layout.grid = { rows: 1, columns: 3, pattern: "independent" };
  layout.xaxis = { domain: [0, 0.16], showticklabels: false, title: "Boorstaat" };
  layout.xaxis2 = { domain: [0.22, 0.62], title: "qc [MPa]" };
  layout.xaxis3 = { domain: [0.70, 1.0], title: "Rf [%]", range: [0, 12] };
  layout.yaxis = { title: "Niveau [m NAP]" };
  layout.yaxis2 = { matches: "y", showticklabels: false };
  layout.yaxis3 = { matches: "y", showticklabels: false };
  layout.barmode = "overlay";
  Plotly.newPlot("plotProfiel", traces, layout, { responsive: true, displayModeBar: false });
}

// u0 | sigma_v0 + sigma_eff
function plotSpanning(d) {
  const y = d.diepte_nap;
  const traces = [
    { x: d.u0, y, mode: "lines", line: { color: HHSK_BLUE, width: 1.6 }, name: "u₀",
      xaxis: "x", yaxis: "y", hovertemplate: "u₀=%{x:.0f} kPa<extra></extra>" },
    { x: d.sigma_v0, y, mode: "lines", line: { color: "#5d4037", width: 1.6 }, name: "σv0",
      xaxis: "x2", yaxis: "y2", hovertemplate: "σv0=%{x:.0f} kPa<extra></extra>" },
    { x: d.sigma_eff, y, mode: "lines", line: { color: ACCENT, width: 1.6, dash: "dash" }, name: "σ'v0",
      xaxis: "x2", yaxis: "y2", hovertemplate: "σ'v0=%{x:.0f} kPa<extra></extra>" },
  ];
  const layout = baseLayout();
  layout.grid = { rows: 1, columns: 2, pattern: "independent" };
  layout.xaxis = { domain: [0, 0.46], title: "Waterdruk u₀ [kPa]" };
  layout.xaxis2 = { domain: [0.56, 1], title: "σv0 / σ'v0 [kPa]" };
  layout.yaxis = { title: "Niveau [m NAP]" };
  layout.yaxis2 = { matches: "y", showticklabels: false };
  layout.showlegend = true;
  layout.legend = { orientation: "h", y: 1.08 };
  Plotly.newPlot("plotSpanning", traces, layout, { responsive: true, displayModeBar: false });
}

// Su
function plotSu(d) {
  const y = d.diepte_nap;
  const traces = [
    { x: d.Su, y, mode: "lines", line: { color: "#ef9a9a", width: 1 }, opacity: 0.8,
      name: "Su per punt", hovertemplate: "Su=%{x:.1f} kPa<br>NAP %{y:.2f}<extra></extra>" },
  ];
  // gemiddelde + karakteristiek per laag (klei/veen) als verticale segmenten
  d.lagen.forEach(l => {
    if (l.su_gem == null) return;
    traces.push({ x: [l.su_gem, l.su_gem], y: [l.top, l.onder], mode: "lines",
      line: { color: "#111", width: 2 }, name: "Su gem (laag)" });
  });
  const layout = {
    height: 560, margin: { l: 55, r: 15, t: 30, b: 45 },
    paper_bgcolor: "#fff", plot_bgcolor: "#fff",
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
