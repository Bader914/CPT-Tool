"""
Module 5: Su Berekening

Hoofdroute (zoals de Deltares CPT-tool):
  1) Su uit de conusweerstand:     Su   = q_net / Nkt            [kPa]
  2) grensspanning uit SHANSEP:    σ'vy = σ'v0 · (Su/(S·σ'v0))^(1/m)
     (SHANSEP omgekeerd; OCR = σ'vy/σ'v0)

De Nkt-waarde gebruik je dus voor Su; voor de grensspanning heb je SHANSEP nodig
— niet andersom. De omgekeerde volgorde (σ'vy = k·q_net, dan Su via SHANSEP) is
beschikbaar als controleroute.

- Nkt/S/m direct uit de grondlaag (df["grondlaag"] uit classificatie)
- Alleen voor dijkmateriaal (gemarkeerd in classificatie)
- Voorboring-data wordt overgeslagen
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def bereken_Su(q_net: pd.Series, Nkt: pd.Series) -> pd.Series:
    """Su = q_net / Nkt → [kPa]. q_net in MPa, dus *1000."""
    return (q_net * 1000) / Nkt


def bereken_grensspanning(q_net: pd.Series, k: float = 0.33) -> pd.Series:
    """CONTROLEROUTE — grensspanning σ'vy rechtstreeks uit q_net [MPa].

        σ'vy = k · q_net      (q_net = qt − σv0)

    Eerste-orde correlatie volgens Mayne (k ≈ 0,3–0,35 voor klei). Let op: dit is
    NIET de hoofdroute. In de hoofdroute volgt σ'vy uit de gemeten Su via
    `bereken_ocr_en_grensspanning` (SHANSEP omgekeerd). Deze functie dient als
    onafhankelijke controle/vergelijking.
    """
    return (k * q_net).clip(lower=0)


def bereken_ocr_en_grensspanning(su_kpa: pd.Series, sigma_v0_eff: pd.Series,
                                 S: pd.Series | float, m: pd.Series | float):
    """OCR en grensspanning σ'vy door SHANSEP OM TE KEREN, met Su uit de Nkt-methode.

    Dit is de route van de Deltares CPT-tool:
        1) Su uit de conusweerstand:   Su = q_net / Nkt          [kPa]
        2) grensspanning uit SHANSEP:  Su = S · σ'v0 · OCRᵐ
                                    ⇒  OCR  = (Su / (S · σ'v0))^(1/m)
                                    ⇒  σ'vy = σ'v0 · OCR

    Dus NIET andersom (σ'vy uit een qnet-correlatie en dan Su); de grensspanning
    is hier een RESULTAAT van de gemeten Su, niet een aanname vooraf.

    Eenheden: su_kpa in kPa, sigma_v0_eff in MPa → σ'vy in MPa. OCR ≥ 1 (geen
    onderconsolidatie). Retour: (OCR, σ'vy).
    """
    sv = sigma_v0_eff.replace(0, np.nan)
    su_mpa = su_kpa / 1000.0
    basis = su_mpa / (S * sv)              # = OCRᵐ
    basis = basis.where(basis > 0)          # negatieve/0-basis → NaN
    exponent = (1.0 / m.replace(0, np.nan)) if isinstance(m, pd.Series) else (1.0 / m if m else np.nan)
    ocr = (basis ** exponent).clip(lower=1.0)
    return ocr, sv * ocr


def bereken_su_shansep(sigma_v0_eff: pd.Series, sigma_vy: pd.Series,
                       S: float, m: float) -> pd.Series:
    """Ongedraineerde sterkte volgens SHANSEP [kPa]:

        Su = S · σ'v0 · OCRᵐ ,  met OCR = σ'vy / σ'v0

    S = sterkteratio, m = exponent (per grondlaag, Tabel 91). σ'v0 en σ'vy in MPa
    → Su in MPa, ×1000 voor kPa. OCR wordt op ≥ 1 geklemd (geen onderconsolidatie).
    """
    sv = sigma_v0_eff.replace(0, np.nan)
    ocr = (sigma_vy / sv).clip(lower=1.0)
    return S * sigma_v0_eff * (ocr ** m) * 1000.0


def karakteristieke_waarde(su_punten: pd.Series, t_factor: float = 1.645,
                           vc_materiaal: float | None = None) -> dict:
    """Karakteristieke (voorzichtige lage) waarde van Su per laag.

        Su_kar = Su_gem · (1 − t · VC)

    De VC is een UITGANGSPUNT, geen uitkomst van de meting:

    - `vc_materiaal` (aanbevolen): de variatiecoëfficiënt die je per grondsoort
      invoert (VC_su in de materialentabel). Dit drukt de onzekerheid in de
      GRONDSTERKTE uit — de bewuste keuze die de schematiseringshandleiding vraagt.
    - VC uit de data (std/gem van de Su-punten): dit meet vooral de punt-op-punt-
      ruis van de conus (meting per 2 cm), niet de onzekerheid over de laagsterkte.
      Die VC wordt daarom als CONTROLEGETAL teruggegeven ('VC_data'), niet gebruikt
      tenzij `vc_materiaal` None is.

    Retour: n, gem, std, VC_data, VC (gebruikt), VC_bron, kar.
    t_factor = 1,645 → 5%-ondergrens (eenzijdig 95%).
    """
    s = su_punten.dropna()
    n = int(s.size)
    if n == 0:
        return {"n": 0, "gem": np.nan, "std": np.nan, "VC_data": np.nan,
                "VC": np.nan, "VC_bron": "—", "kar": np.nan}
    gem = float(s.mean())
    std = float(s.std(ddof=1)) if n > 1 else 0.0
    vc_data = std / gem if gem else 0.0

    if vc_materiaal is not None:
        vc, bron = float(vc_materiaal), "materiaal"
    else:
        vc, bron = vc_data, "data"

    kar = gem * (1 - t_factor * vc)
    return {"n": n, "gem": gem, "std": std, "VC_data": vc_data,
            "VC": vc, "VC_bron": bron, "kar": max(kar, 0.0)}


def render():
    st.caption("Stap 5 — Su = q_net / Nkt per grondlaag")

    genormaliseerd = {k: v for k, v in st.session_state.get("sonderingen", {}).items()
                       if v.get("genormaliseerd")}

    if not genormaliseerd:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Normalisatie nog niet uitgevoerd</h4>
            <p>Ga eerst naar <b>Stap 4 — Normalisatie</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    up = st.session_state.get("uitgangspunten", {})
    lagen = up.get("lagen", [])

    if not lagen:
        st.error("❌ Geen grondlagen. Ga naar Stap 0 — Uitgangspunten.")
        return

    # Nkt per SHZ-grondlaag (direct uit uitgangspunten)
    nkt_per_grondlaag = {l["naam"]: l["Nkt"] for l in lagen if l.get("Nkt") is not None}

    st.subheader("Nkt per grondlaag (Tabel 71)")
    nkt_rows = [{"Grondlaag": n, "Nkt": v} for n, v in nkt_per_grondlaag.items()]
    st.dataframe(pd.DataFrame(nkt_rows), use_container_width=True, hide_index=True)

    missing_dijkmat_nkt = [l["naam"] for l in lagen
                           if l.get("is_dijkmateriaal") and l.get("Nkt") is None]
    if missing_dijkmat_nkt:
        st.warning(f"⚠️ Nkt ontbreekt voor dijkmateriaal-lagen: {', '.join(missing_dijkmat_nkt)}. "
                    "Vul aan in Stap 0.")

    # Su-methode + parameters
    st.markdown("**Methode & karakteristieke waarde**")
    col_m1, col_m2 = st.columns([1.3, 1])
    with col_m1:
        su_methode = st.radio(
            "Su-methode",
            ["Nkt → Su, SHANSEP → grensspanning", "SHANSEP-voorwaarts (controle, Mayne k)"],
            index=0, key="su_methode",
            help="Hoofdroute (zoals de Deltares CPT-tool): Su = q_net/Nkt uit de conusweerstand; "
                 "dáárna de grensspanning door SHANSEP om te keren: σ'vy = σ'v0·(Su/(S·σ'v0))^(1/m). "
                 "De controleroute doet het omgekeerd: σ'vy = k·q_net (Mayne) en dan Su via SHANSEP.",
        )
    is_shansep = su_methode.startswith("SHANSEP")

    with col_m2:
        # Karakteristieke waarde is een UITGANGSPUNT (Stap 0), geen rekenknop hier.
        kar_cfg = st.session_state.get("uitgangspunten", {}).get("karakteristiek", {})
        t_factor = float(kar_cfg.get("t_factor", 1.645))
        vc_bron = kar_cfg.get("vc_bron", "materiaal")
        _bron_txt = "VC per materiaal" if vc_bron == "materiaal" else "VC uit de data"
        st.markdown("**Karakteristieke waarde**")
        st.caption(f"t = {t_factor:.3f} · {_bron_txt} — in te stellen bij "
                   f"**Stap 0 → 🔢 Nkt-factoren**.")

    # ── Openstaand punt: de aanpak van k en t is nog niet afgestemd. ──
    # Een vaste t = 1,645 is de 95%-fractiel van de NORMALE verdeling (σ bekend).
    # De formele aanpak voor waterkeringen (NEN 9997-1 / schematiseringshandleiding)
    # gebruikt Student-t met n-1 vrijheidsgraden én ruimtelijke middeling langs het
    # glijvlak. Ook de omgang met uitschieters is een projectafspraak, geen code-keuze.
    st.info(
        "📋 **Nog af te stemmen — de karakteristieke waarde is voorlopig.**\n\n"
        f"De tool rekent nu met **Su_kar = Su_gem · (1 − {t_factor:.3f} · VC)**. Een vaste "
        "t = 1,645 is de 95%-ondergrens van de *normale* verdeling. De aanpak voor "
        "waterkeringen gebruikt **Student-t** (afhankelijk van het aantal waarnemingen n) "
        "en houdt rekening met **ruimtelijke middeling** langs het glijvlak. Ook of je "
        "**uitschieters** meeneemt bepaalt het resultaat direct.\n\n"
        "→ Methode afstemmen met **Herman-Jaap**, uitschieters met **Jan**. "
        "Zie `OVERLEG_KARAKTERISTIEKE_WAARDE.md` in de repo."
    )

    # Grensspanning-factor k: ALLEEN relevant voor de controleroute. In de hoofdroute
    # volgt σ'vy uit de gemeten Su (SHANSEP omgekeerd) en wordt k niet gebruikt.
    k_grens = 0.33
    if is_shansep:
        st.warning(
            "⚠️ **Controleroute — niet de waterkeringen-aanpak.** Hier komt de grensspanning "
            "uit een CPT-correlatie (σ′vy = k·q_net, Mayne). In de Nederlandse aanpak volgt de "
            "grensspanning uit **samendrukkingsproeven** (POP per grondlaag), niet uit een "
            "instelbare k. Gebruik deze route alleen als **vergelijking**, niet als resultaat."
        )
        k_grens = st.number_input(
            "Grensspanning-factor k [-]", min_value=0.1, max_value=0.6, value=0.33, step=0.01,
            help="σ'vy = k·q_net (Mayne; k ≈ 0,3–0,35 voor klei). Alleen voor deze controleroute.",
        )

    st.markdown("---")

    if st.button("▶️ Bereken Su voor alle sonderingen", type="primary", use_container_width=True):
        progress = st.progress(0)
        total = len(genormaliseerd)
        resultaten = []
        spreiding_waarschuwing = []

        for i, (name, data) in enumerate(genormaliseerd.items()):
            df = data["df"].copy()

            if "q_net" not in df.columns:
                resultaten.append({"Sondering": name, "Status": "❌ q_net ontbreekt"})
                continue
            if "grondlaag" not in df.columns:
                resultaten.append({"Sondering": name, "Status": "❌ grondlaag ontbreekt"})
                continue

            # Parameters per grondlaag — per-sondering lagen indien aanwezig, anders globaal
            lagen_eff = data.get("lagen_lokaal") or lagen
            nkt_map = {l["naam"]: l["Nkt"] for l in lagen_eff if l.get("Nkt") is not None}
            s_map = {l["naam"]: l.get("S_ratio") for l in lagen_eff if l.get("S_ratio") is not None}
            m_map = {l["naam"]: l.get("m_factor") for l in lagen_eff if l.get("m_factor") is not None}
            df["Nkt_gebruikt"] = df["grondlaag"].map(nkt_map)

            # Geldig: dijkmateriaal + voorboring geldig
            geldig = df.get("is_dijkmateriaal", pd.Series([True] * len(df), index=df.index))
            geldig = geldig.fillna(False).astype(bool)
            if "voorboring_geldig" in df.columns:
                geldig = geldig & df["voorboring_geldig"].astype(bool)

            df["Su"] = np.nan
            df["S_gebruikt"] = df["grondlaag"].map(s_map)
            df["m_gebruikt"] = df["grondlaag"].map(m_map)
            sv_eff = df.get("sigma_v0_eff", pd.Series(np.nan, index=df.index))

            if is_shansep:
                # ALTERNATIEVE route (controle): grensspanning uit een qnet-correlatie
                # (Mayne) en dáárna Su via SHANSEP-voorwaarts.
                df["sigma_vy"] = bereken_grensspanning(df["q_net"], k_grens)
                geldig_sh = geldig & df["S_gebruikt"].notna() & df["m_gebruikt"].notna() & sv_eff.notna()
                su_vals = bereken_su_shansep(
                    df["sigma_v0_eff"], df["sigma_vy"],
                    df["S_gebruikt"].fillna(0), df["m_gebruikt"].fillna(1))
                df.loc[geldig_sh, "Su"] = su_vals[geldig_sh]
                df["OCR"] = (df["sigma_vy"] / sv_eff.replace(0, np.nan)).clip(lower=1.0)
                methode_note = f"SHANSEP-voorwaarts (k={k_grens:.2f})"
            else:
                # HOOFDROUTE (zoals de Deltares CPT-tool):
                #   1) Su uit de conusweerstand:  Su = q_net / Nkt
                #   2) grensspanning uit SHANSEP omgekeerd: σ'vy = σ'v0·(Su/(S·σ'v0))^(1/m)
                geldig_nkt = geldig & df["Nkt_gebruikt"].notna()
                df.loc[geldig_nkt, "Su"] = bereken_Su(
                    df.loc[geldig_nkt, "q_net"], df.loc[geldig_nkt, "Nkt_gebruikt"])
                df.loc[df["Su"] < 0, "Su"] = np.nan
                ocr, sigma_vy = bereken_ocr_en_grensspanning(
                    df["Su"], sv_eff, df["S_gebruikt"], df["m_gebruikt"])
                df["OCR"] = ocr
                df["sigma_vy"] = sigma_vy
                methode_note = "Nkt → Su; SHANSEP → grensspanning"
            df.loc[df["Su"] < 0, "Su"] = np.nan

            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["su_berekend"] = True
            st.session_state.sonderingen[name]["su_methode"] = methode_note
            st.session_state.sonderingen[name]["t_factor"] = t_factor

            # Karakteristieke waarde PER LAAG (elke laag heeft zijn eigen VC_su),
            # daarna gewogen naar de sondering. Eén VC over alle lagen zou de
            # materiaal-VC's door elkaar husselen.
            vc_map = {l["naam"]: l.get("VC_su") for l in lagen_eff} if vc_bron == "materiaal" else {}
            per_laag = []
            for _laag, _sub in df.dropna(subset=["Su"]).groupby("grondlaag"):
                per_laag.append(karakteristieke_waarde(
                    _sub["Su"], t_factor, vc_materiaal=vc_map.get(_laag)))
            n_tot = sum(k["n"] for k in per_laag)
            if n_tot:
                su_gem = sum(k["gem"] * k["n"] for k in per_laag) / n_tot
                su_kar = sum(k["kar"] * k["n"] for k in per_laag) / n_tot
                vc_geb = sum(k["VC"] * k["n"] for k in per_laag) / n_tot
                vc_dat = sum(k["VC_data"] * k["n"] for k in per_laag) / n_tot
            else:
                su_gem = su_kar = vc_geb = vc_dat = np.nan

            ocr_gem = df["OCR"].replace([np.inf, -np.inf], np.nan).mean() if "OCR" in df else np.nan
            svy_gem = df["sigma_vy"].replace([np.inf, -np.inf], np.nan).mean() if "sigma_vy" in df else np.nan
            resultaten.append({
                "Sondering": name, "Status": "✅", "Methode": methode_note,
                "Meetpunten": n_tot,
                "Su gem [kPa]": f"{su_gem:.1f}" if n_tot else "—",
                "VC gebruikt [-]": f"{vc_geb:.2f}" if n_tot else "—",
                "VC data (controle) [-]": f"{vc_dat:.2f}" if n_tot else "—",
                "Su kar [kPa]": f"{su_kar:.1f}" if n_tot else "—",
                "OCR gem [-]": f"{ocr_gem:.2f}" if pd.notna(ocr_gem) else "—",
                "σ'vy gem [kPa]": f"{svy_gem * 1000:.1f}" if pd.notna(svy_gem) else "—",
            })
            st.session_state.sonderingen[name]["vc_bron"] = vc_bron

            # Controle: wijkt de data-VC ver af van de gebruikte VC, dan is de
            # laagindeling waarschijnlijk te grof (één laag over te veel variatie).
            if n_tot and (su_kar <= 0.0 or (vc_bron == "materiaal" and vc_dat > 2 * max(vc_geb, 0.01))
                          or (vc_bron == "data" and vc_geb > 0.5)):
                spreiding_waarschuwing.append(
                    f"**{name}** — VC gebruikt {vc_geb:.2f}, VC uit data {vc_dat:.2f}, "
                    f"Su kar {su_kar:.1f} kPa")
            progress.progress((i + 1) / total)

        st.success(f"Su berekend voor {total} sondering(en)")
        st.dataframe(pd.DataFrame(resultaten), use_container_width=True, hide_index=True)

        if spreiding_waarschuwing:
            st.warning(
                "⚠️ **Grote spreiding in de Su-punten — controleer de laagindeling.**\n\n"
                + "\n".join(f"- {w}" for w in spreiding_waarschuwing)
                + "\n\nDe **VC uit de data** ligt fors boven de **VC die je gebruikt**. Dat betekent "
                  "meestal dat één laag te dik is (bijv. één kleilaag over de hele sondering) en "
                  "daardoor te veel variatie omvat. **Verdeel de laag verder** in Stap 2 — "
                  "Classificatie (verlaag de min. laagdikte of voeg laaggrenzen toe).\n\n"
                  "*Let op: de karakteristieke waarde zelf is hierdoor niet fout — die volgt de "
                  "VC uit je materialentabel. De data-VC is een **controlegetal**.*"
            )

    # Resultaten
    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items()
                    if v.get("su_berekend")}
    if not su_berekend:
        return

    st.markdown("---")
    view_mode = st.radio("Weergave", ["Per sondering", "Alle sonderingen samen"],
                         horizontal=True, label_visibility="collapsed")

    if view_mode == "Per sondering":
        _render_per_sondering(su_berekend)
    else:
        _render_alle_samen(su_berekend)


def _render_per_sondering(su_berekend: dict):
    selected = st.selectbox("Selecteer sondering", list(su_berekend.keys()), key="su_select")
    if not selected:
        return

    data = su_berekend[selected]
    df = data["df"]
    cm = data["col_mapping"]

    up = st.session_state.get("uitgangspunten", {})
    kar_cfg = up.get("karakteristiek", {})
    t_factor = float(kar_cfg.get("t_factor", data.get("t_factor", 1.645)))
    vc_bron = kar_cfg.get("vc_bron", "materiaal")

    su_data = df["Su"].dropna()
    if not su_data.empty:
        lagen_eff = data.get("lagen_lokaal") or up.get("lagen", [])
        vc_mat_map = {l["naam"]: l.get("VC_su") for l in lagen_eff if l.get("VC_su") is not None}

        # Karakteristieke waarde per grondlaag — elke laag met zijn eigen VC.
        rijen, kars, gems, ns = [], [], [], []
        for laag, sub in df.dropna(subset=["Su"]).groupby("grondlaag"):
            vc_mat = vc_mat_map.get(laag) if vc_bron == "materiaal" else None
            kwl = karakteristieke_waarde(sub["Su"], t_factor, vc_materiaal=vc_mat)
            rijen.append({
                "Grondlaag": laag, "n": kwl["n"],
                "Su gem [kPa]": round(kwl["gem"], 1),
                "VC gebruikt [-]": round(kwl["VC"], 2),
                "bron VC": "materiaal" if kwl["VC_bron"] == "materiaal" else "data",
                "VC data (controle) [-]": round(kwl["VC_data"], 2),
                "Su kar [kPa]": round(kwl["kar"], 1),
            })
            kars.append(kwl["kar"] * kwl["n"]); gems.append(kwl["gem"] * kwl["n"]); ns.append(kwl["n"])

        n_tot = sum(ns)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Su gemiddeld", f"{sum(gems)/n_tot:.1f} kPa" if n_tot else "—")
        c2.metric("VC-bron", "materiaal" if vc_bron == "materiaal" else "data")
        c3.metric("Su karakteristiek", f"{sum(kars)/n_tot:.1f} kPa" if n_tot else "—")
        c4.metric("Methode", data.get("su_methode", "Nkt"))

        if rijen:
            _uitleg = ("VC per **materiaal** (uit de materialentabel) is leidend; de VC uit de data "
                       "staat ernaast als **controlegetal**."
                       if vc_bron == "materiaal" else
                       "VC uit de **data** (spreiding van de Su-punten) wordt gebruikt.")
            st.markdown(f"**Karakteristieke waarde per grondlaag** — "
                        f"Su_kar = Su_gem·(1 − {t_factor:.3f}·VC). {_uitleg} "
                        f"Instelbaar bij *Stap 0 → 🔢 Nkt-factoren*.")
            st.dataframe(pd.DataFrame(rijen), use_container_width=True, hide_index=True)

    toon_lagen = st.checkbox("Toon SHZ-laagverdeling op achtergrond", value=True,
                              key=f"toon_lagen_su_{selected}")

    fig = make_subplots(rows=1, cols=3,
                        subplot_titles=["qt [MPa]", "Su [kPa]", "Nkt [-]"],
                        shared_yaxes=True, horizontal_spacing=0.05)

    if toon_lagen:
        grenzen = data.get("laaggrenzen", {})
        for naam, g in grenzen.items():
            if g.get("top_nap") is None or g.get("onder_nap") is None:
                continue
            for col in (1, 2, 3):
                fig.add_hrect(y0=g["onder_nap"], y1=g["top_nap"],
                              fillcolor=g.get("kleur", "#888888"),
                              opacity=0.14, line_width=0, row=1, col=col)

    fig.add_trace(go.Scatter(x=df["qt"], y=df["diepte_nap"], name="qt",
                              line=dict(color="#0d47a1", width=1.5)), row=1, col=1)

    su_valid = df["Su"].notna()
    fig.add_trace(go.Scatter(x=df.loc[su_valid, "Su"], y=df.loc[su_valid, "diepte_nap"],
                              name="Su per punt", line=dict(color="#ef9a9a", width=1),
                              opacity=0.7), row=1, col=2)

    # Meerdere profielen boven elkaar (à la Deltares): gelineariseerd su-profiel
    # en su_kar-profiel per dijkmateriaal-laag.
    grenzen = data.get("laaggrenzen", {})
    eerste = True
    for naam, g in grenzen.items():
        if not g.get("is_dijkmateriaal"):
            continue
        top, onder = g.get("top_nap"), g.get("onder_nap")
        if top is None or onder is None:
            continue
        sub = df[(df["diepte_nap"] <= top) & (df["diepte_nap"] > onder) & df["Su"].notna()]
        if len(sub) < 3:
            continue
        b, a = np.polyfit(sub["diepte_nap"], sub["Su"], 1)   # Su = b·NAP + a
        su_top, su_bot = b * top + a, b * onder + a
        gem = sub["Su"].mean()
        vc = sub["Su"].std(ddof=1) / gem if gem else 0.0
        f = max(1 - t_factor * vc, 0.0)
        fig.add_trace(go.Scatter(
            x=[su_top, su_bot], y=[top, onder], mode="lines",
            name="su (gelineariseerd)", legendgroup="lin", showlegend=eerste,
            line=dict(color="#111111", width=2)), row=1, col=2)
        fig.add_trace(go.Scatter(
            x=[su_top * f, su_bot * f], y=[top, onder], mode="lines",
            name="su_kar (gelineariseerd)", legendgroup="kar", showlegend=eerste,
            line=dict(color="#111111", width=1.5, dash="dot")), row=1, col=2)
        eerste = False

    if "Nkt_gebruikt" in df.columns:
        nkt_valid = df["Nkt_gebruikt"].notna()
        fig.add_trace(go.Scatter(x=df.loc[nkt_valid, "Nkt_gebruikt"],
                                  y=df.loc[nkt_valid, "diepte_nap"],
                                  name="Nkt", line=dict(color="#64748b", width=1.5)), row=1, col=3)

    fig.update_yaxes(title_text="Niveau [m NAP]", row=1, col=1)
    fig.update_layout(height=650, template="plotly_white", title=f"Su-profiel — {selected}")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📊 Data: grondlaag → Nkt → Su per meetpunt", expanded=False):
        show_cols = [c for c in [cm.get("diepte"), "diepte_nap", "grondlaag",
                                  "q_net", "Nkt_gebruikt", "Su"]
                     if c and c in df.columns]
        st.dataframe(df[df["Su"].notna()][show_cols].round(3),
                     use_container_width=True, hide_index=True)


def _render_alle_samen(su_berekend: dict):
    fig = go.Figure()
    colors = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6",
              "#ec4899", "#14b8a6", "#f97316"]

    for i, (name, data) in enumerate(su_berekend.items()):
        df = data["df"]
        su_valid = df["Su"].notna()
        if su_valid.any():
            fig.add_trace(go.Scatter(
                x=df.loc[su_valid, "Su"], y=df.loc[su_valid, "diepte_nap"],
                mode="lines", name=name,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f"<b>{name}</b><br>Su=%{{x:.1f}} kPa<br>NAP %{{y:+.2f}}m<extra></extra>",
            ))

    fig.update_layout(
        title="Su-profielen — alle sonderingen",
        yaxis=dict(title="Niveau [m NAP]"),
        xaxis=dict(title="Su [kPa]"),
        height=700, template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)
