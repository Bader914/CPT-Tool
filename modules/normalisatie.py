"""
Module 4: Normalisatie (Qt) — DRAAIT NA Classificatie (stap 3)
- u0-verloop met knikpunt bij watervoerend pakket
- σv0 op basis van handmatige SHZ-laagindeling + funderingslaag (per sondering)
- qt-correctie + Rf + Bq + Qt + q_net
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ───────────────────────────────────────────────────────────────
# Basis-formules (ongewijzigd)
# ───────────────────────────────────────────────────────────────
def bereken_qt(qc: pd.Series, u2: pd.Series, a: float = 0.80) -> pd.Series:
    """qt = qc + (1 - a) * u2"""
    return qc + (1 - a) * u2


def bereken_q_net(qt: pd.Series, sigma_v0: pd.Series) -> pd.Series:
    """q_net = qt - sigma_v0"""
    return qt - sigma_v0


def bereken_Rf(fs: pd.Series, qc: pd.Series) -> pd.Series:
    """Rf = (fs / qc) * 100  [%]"""
    return (fs / qc.replace(0, np.nan)) * 100


def bereken_Bq(u2: pd.Series, u0: pd.Series, qt: pd.Series, sigma_v0: pd.Series) -> pd.Series:
    """Bq = (u2 - u0) / (qt - sigma_v0)"""
    q_net = qt - sigma_v0
    return (u2 - u0) / q_net.replace(0, np.nan)


# ───────────────────────────────────────────────────────────────
# u0-verloop met knikpunt (watervoerend pakket)
# ───────────────────────────────────────────────────────────────
def bereken_u0_met_knik(
    diepte_nap: pd.Series,
    gwl_nap: float,
    knik_nap: float,
    u_top_watervoerend_kpa: float,
    gamma_w: float = 9.81,
) -> pd.Series:
    """
    Theoretisch waterdrukverloop met knikpunt bij overgang klei → watervoerend zandpakket.

    Drie segmenten (z_NAP = diepte_nap):
      boven GWS (z > gwl_nap):           u0 = 0
      GWS → knik (klei):                 u0 = gamma_w * (gwl_nap - z_NAP)
      onder knik (zand):                 u0 = u_top_watervoerend_kpa
                                              + gamma_w * (knik_nap - z_NAP)
    """
    z = diepte_nap.values.astype(float)
    u0 = np.where(
        z > gwl_nap,
        0.0,
        np.where(
            z > knik_nap,
            gamma_w * (gwl_nap - z),
            u_top_watervoerend_kpa + gamma_w * (knik_nap - z),
        ),
    )
    return pd.Series(u0, index=diepte_nap.index)


# ───────────────────────────────────────────────────────────────
# σv0 op basis van handmatige SHZ-laagindeling
# ───────────────────────────────────────────────────────────────
def bereken_sigma_v0_met_grondlaag(
    diepte_nap: pd.Series,
    grondlaag_per_meting: pd.Series,
    lagen: list,
    mv_nap: float,
    gwl_nap: float,
    funderingslaag: dict | None = None,
) -> pd.Series:
    """
    Bereken σv0 [kPa] door verticaal te integreren met γ per SHZ-laag.

    - Vóór de bovenste laaggrens: funderingslaag γ (indien actief), anders γ van bovenste laag
    - Per laag: γ_droog boven GWS, γ_nat onder GWS
    - Onbekende lagen: gemiddelde γ_nat uit alle gedefinieerde lagen
    """
    gamma_per_naam = {l["naam"]: {"droog": l.get("gamma_droog", l.get("gamma_nat", 18.0)),
                                   "nat": l.get("gamma_nat", 18.0)} for l in lagen}
    gemiddelde_gamma = float(np.mean([l.get("gamma_nat", 18.0) for l in lagen])) if lagen else 18.0

    z = diepte_nap.values.astype(float)
    # Sorteer op diepte (van boven naar beneden in NAP = afnemend)
    sort_idx = np.argsort(-z)
    z_sorted = z[sort_idx]
    namen_sorted = grondlaag_per_meting.values[sort_idx]

    # Funderingslaag bovenop: van maaiveld tot (maaiveld - dikte)
    fund_actief = funderingslaag and funderingslaag.get("actief")
    fund_dikte = funderingslaag.get("dikte", 0.0) if fund_actief else 0.0
    fund_gamma = funderingslaag.get("gamma", 21.0) if fund_actief else None
    fund_onder_nap = mv_nap - fund_dikte if fund_actief else mv_nap

    sigma = np.zeros_like(z_sorted)
    z_prev = mv_nap

    for i, (zi, naam) in enumerate(zip(z_sorted, namen_sorted)):
        dz = z_prev - zi  # positief: gaan naar beneden
        if dz <= 0:
            sigma[i] = sigma[i - 1] if i > 0 else 0.0
            continue

        # Bepaal γ voor dit interval — splits op funderingslaag-grens en GWS
        sigma_acc = sigma[i - 1] if i > 0 else 0.0
        z_top = z_prev
        z_bot = zi

        # Funderingslaag-gedeelte
        if fund_actief and z_top > fund_onder_nap:
            dz_fund = min(z_top, mv_nap) - max(z_bot, fund_onder_nap)
            if dz_fund > 0:
                sigma_acc += dz_fund * fund_gamma
            z_top = min(z_top, fund_onder_nap)

        if z_top > z_bot:
            # Gebruik γ van de grondlaag, droog boven GWS / nat onder GWS
            gamma = gamma_per_naam.get(str(naam), {"droog": gemiddelde_gamma, "nat": gemiddelde_gamma})
            # Splits op GWS
            if z_top > gwl_nap and z_bot < gwl_nap:
                dz_droog = z_top - gwl_nap
                dz_nat = gwl_nap - z_bot
                sigma_acc += dz_droog * gamma["droog"] + dz_nat * gamma["nat"]
            elif z_top <= gwl_nap:
                sigma_acc += (z_top - z_bot) * gamma["nat"]
            else:
                sigma_acc += (z_top - z_bot) * gamma["droog"]

        sigma[i] = sigma_acc
        z_prev = zi

    # Terugzetten in originele volgorde
    sigma_v0 = np.zeros_like(z)
    sigma_v0[sort_idx] = sigma
    return pd.Series(sigma_v0, index=diepte_nap.index)


# ───────────────────────────────────────────────────────────────
# Render
# ───────────────────────────────────────────────────────────────
def render():
    st.caption("Stap 4 — qt-correctie, u₀-verloop met knikpunt, σ-spanningen")

    sonderingen = st.session_state.get("sonderingen", {})
    up = st.session_state.get("uitgangspunten", {})
    lagen = up.get("lagen", [])
    waterdruk = up.get("waterdruk", {})

    # Check vereisten: classificatie moet gedaan zijn
    geclassificeerd = {k: v for k, v in sonderingen.items() if v.get("geclassificeerd")}

    if not geclassificeerd:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Classificatie nog niet uitgevoerd</h4>
            <p>Ga eerst naar <b>Stap 3 — Classificatie</b> en stel de laaggrenzen per sondering in.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if not lagen:
        st.error("❌ Geen grondlagen gevonden. Ga eerst naar Stap 0 — Uitgangspunten.")
        return

    # Status
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Geclassificeerd", f"{len(geclassificeerd)}")
    with col_s2:
        st.metric("Genormaliseerd", f"{sum(1 for v in geclassificeerd.values() if v.get('genormaliseerd'))}")
    with col_s3:
        st.metric("Nog te doen", f"{sum(1 for v in geclassificeerd.values() if not v.get('genormaliseerd'))}")

    # Parameters
    st.markdown("---")
    st.subheader("Parameters (uit Uitgangspunten)")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        a_factor = st.number_input(
            "Nettoquotient conus (a)",
            min_value=0.50, max_value=1.00,
            value=up.get("conustype", {}).get("a_factor", 0.80),
            step=0.01,
            help="Voor qt-correctie: qt = qc + (1−a)·u₂."
        )
        gwl_nap = st.number_input(
            "Grondwaterstand [m NAP]",
            min_value=-10.0, max_value=10.0,
            value=up.get("dijkopbouw", {}).get("gwl", 0.0), step=0.1,
        )
    with col_p2:
        knik_nap = st.number_input(
            "Knikpunt watervoerend pakket [m NAP]",
            min_value=-30.0, max_value=5.0,
            value=waterdruk.get("watervoerend_knik_nap", -12.0), step=0.5,
        )
        u_top_kpa = st.number_input(
            "u_top watervoerend pakket [kPa]",
            min_value=0.0, max_value=500.0,
            value=waterdruk.get("u_top_watervoerend_kpa", 30.0), step=1.0,
        )

    gamma_w = waterdruk.get("gamma_w", 9.81)

    st.markdown("---")

    if st.button("▶️ Bereken qt, u₀ en σ-spanningen voor alle sonderingen", type="primary", use_container_width=True):
        progress = st.progress(0)
        total = len(geclassificeerd)
        resultaten = []

        for i, (name, data) in enumerate(geclassificeerd.items()):
            df = data["df"].copy()
            cm = data["col_mapping"]
            mv_nap = data.get("maaiveld_nap") or up.get("dijkopbouw", {}).get("kruinniveau", 4.0)
            grenzen = data.get("laaggrenzen", {})
            fund = data.get("funderingslaag")
            voorboring = data.get("voorboring")

            # Lokale waterdruk-override
            lokaal = data.get("waterdruk_lokaal") or {}
            knik_local = lokaal.get("knik_nap", knik_nap)
            u_top_local = lokaal.get("u_top", u_top_kpa)

            try:
                # Zorg dat diepte_nap bestaat
                if "diepte_nap" not in df.columns:
                    df["diepte_nap"] = mv_nap - df[cm["diepte"]]

                qc = df[cm["qc"]]

                # u0 met knikpunt
                df["u0"] = bereken_u0_met_knik(
                    df["diepte_nap"], gwl_nap, knik_local, u_top_local, gamma_w
                ) / 1000.0  # kPa → MPa

                # σv0 op handmatige laagindeling
                if "grondlaag" not in df.columns:
                    resultaten.append({"Sondering": name, "Status": "❌ Geen grondlaag — herclassificeer"})
                    continue

                sigma_v0_kpa = bereken_sigma_v0_met_grondlaag(
                    df["diepte_nap"], df["grondlaag"], lagen, mv_nap, gwl_nap, fund
                )
                df["sigma_v0"] = sigma_v0_kpa / 1000.0  # kPa → MPa
                df["sigma_v0_eff"] = (sigma_v0_kpa - df["u0"] * 1000.0).clip(lower=0) / 1000.0

                # qt-correctie
                is_qt_corrected = data.get("is_qt_corrected", False)
                if is_qt_corrected:
                    df["qt"] = qc
                    qt_note = "al gecorrigeerd (qty 14)"
                elif cm.get("u2") and cm["u2"] in df.columns:
                    df["qt"] = bereken_qt(qc, df[cm["u2"]], a_factor)
                    df["Bq"] = bereken_Bq(df[cm["u2"]], df["u0"], df["qt"], df["sigma_v0"])
                    qt_note = "met u₂-correctie"
                else:
                    df["qt"] = qc
                    qt_note = "geen u₂ (qt = qc)"

                # Afgeleide grootheden
                df["q_net"] = bereken_q_net(df["qt"], df["sigma_v0"])
                df["Qt"] = df["q_net"] / df["sigma_v0_eff"].replace(0, np.nan)
                if cm.get("fs") and cm["fs"] in df.columns and "Rf" not in df.columns:
                    df["Rf"] = bereken_Rf(df[cm["fs"]], qc)

                # Voorboring: data in dat dieptebereik ongeldig maken voor Su
                if voorboring and voorboring.get("actief"):
                    vb_grens_nap = mv_nap - voorboring["diepte"]
                    df["voorboring_geldig"] = df["diepte_nap"] <= vb_grens_nap
                else:
                    df["voorboring_geldig"] = True

                st.session_state.sonderingen[name]["df"] = df
                st.session_state.sonderingen[name]["genormaliseerd"] = True
                st.session_state.sonderingen[name]["parameters"] = {
                    "a": a_factor, "gwl": gwl_nap, "maaiveld_nap": mv_nap,
                    "knik_nap": knik_local, "u_top_kpa": u_top_local,
                }
                resultaten.append({"Sondering": name, "Status": "✅", "qt": qt_note, "Metingen": len(df)})

            except Exception as e:
                resultaten.append({"Sondering": name, "Status": f"❌ {e}", "qt": "—", "Metingen": 0})

            progress.progress((i + 1) / total)

        st.success("Normalisatie voltooid.")
        st.dataframe(pd.DataFrame(resultaten), use_container_width=True, hide_index=True)

    # Resultaat-plots per sondering
    genormaliseerd = {k: v for k, v in sonderingen.items() if v.get("genormaliseerd")}

    if not genormaliseerd:
        return

    st.markdown("---")
    st.subheader("Resultaten")

    selected = st.selectbox("Sondering", list(genormaliseerd.keys()), key="norm_select")
    if not selected:
        return

    data = genormaliseerd[selected]
    df = data["df"]
    cm = data["col_mapping"]

    col_toggle1, col_toggle2 = st.columns(2)
    with col_toggle1:
        toon_u2 = st.checkbox("Toon u₂ (gemeten) ter vergelijking met u₀",
                               value=False, key=f"toon_u2_{selected}",
                               help="u₂ is de gemeten poriedruk; u₀ is het theoretische verloop "
                                    "dat wordt gebruikt voor σ'. Helpt visueel checken dat ze "
                                    "verschillen in klei en convergeren in zand.")
    with col_toggle2:
        toon_lagen = st.checkbox("Toon SHZ-laagverdeling op achtergrond",
                                  value=True, key=f"toon_lagen_norm_{selected}")

    fig = make_subplots(
        rows=1, cols=4,
        subplot_titles=["qt [MPa]", "u [kPa]", "σ [kPa]", "Qt [-]"],
        shared_yaxes=True, horizontal_spacing=0.04,
    )

    # Achtergrondbanden lagen
    if toon_lagen:
        grenzen = data.get("laaggrenzen", {})
        for naam, g in grenzen.items():
            if g.get("top_nap") is None or g.get("onder_nap") is None:
                continue
            for col in (1, 2, 3, 4):
                fig.add_hrect(
                    y0=g["onder_nap"], y1=g["top_nap"],
                    fillcolor=g.get("kleur", "#888888"),
                    opacity=0.14, line_width=0,
                    row=1, col=col,
                )

    # Kolom 1: qt + qc
    fig.add_trace(go.Scatter(x=df["qt"], y=df["diepte_nap"], name="qt",
                              line=dict(color="#0d47a1", width=1.5)), row=1, col=1)
    if cm.get("qc") and cm["qc"] in df.columns:
        fig.add_trace(go.Scatter(x=df[cm["qc"]], y=df["diepte_nap"], name="qc",
                                  line=dict(color="#90caf9", dash="dot", width=1)), row=1, col=1)

    # Kolom 2: u0 (en optioneel u2)
    fig.add_trace(go.Scatter(x=df["u0"] * 1000, y=df["diepte_nap"], name="u₀",
                              line=dict(color="#1e88e5", width=2)), row=1, col=2)
    if toon_u2 and cm.get("u2") and cm["u2"] in df.columns:
        fig.add_trace(go.Scatter(x=df[cm["u2"]] * 1000, y=df["diepte_nap"], name="u₂ (gemeten)",
                                  line=dict(color="#ef4444", dash="dash", width=1.5)), row=1, col=2)

    # Kolom 3: σv0 totaal + effectief
    fig.add_trace(go.Scatter(x=df["sigma_v0"] * 1000, y=df["diepte_nap"], name="σv0",
                              line=dict(color="#5d4037", width=1.5)), row=1, col=3)
    fig.add_trace(go.Scatter(x=df["sigma_v0_eff"] * 1000, y=df["diepte_nap"], name="σ'v0",
                              line=dict(color="#8d6e63", dash="dash", width=1.5)), row=1, col=3)

    # Kolom 4: Qt
    if "Qt" in df.columns:
        fig.add_trace(go.Scatter(x=df["Qt"], y=df["diepte_nap"], name="Qt",
                                  line=dict(color="#8b5cf6", width=1.5)), row=1, col=4)

    # GWS lijn
    gwl_val = data.get("parameters", {}).get("gwl", gwl_nap)
    for col in (1, 2, 3, 4):
        fig.add_hline(y=gwl_val, line=dict(color="#64b5f6", dash="dot", width=1), row=1, col=col)

    # Knik lijn
    knik_val = data.get("parameters", {}).get("knik_nap", knik_nap)
    for col in (1, 2, 3, 4):
        fig.add_hline(y=knik_val, line=dict(color="#ff9800", dash="dash", width=1), row=1, col=col)

    fig.update_yaxes(title_text="Niveau [m NAP]", row=1, col=1)
    fig.update_layout(height=650, template="plotly_white",
                       legend=dict(orientation="h", yanchor="bottom", y=1.04, font=dict(size=10)))

    st.plotly_chart(fig, use_container_width=True)

    # Per-sondering waterdruk override
    with st.expander("💧 Lokale waterdruk-override (deze sondering)", expanded=False):
        st.caption("Default = waarden uit Uitgangspunten. Pas alleen aan als de zandlaag of "
                   "pakketdruk lokaal afwijkt.")
        lokaal = data.get("waterdruk_lokaal") or {}
        new_knik = st.number_input(
            "Knikpunt [m NAP]",
            value=float(lokaal.get("knik_nap", knik_nap)),
            min_value=-30.0, max_value=5.0, step=0.5,
            key=f"knik_local_{selected}",
        )
        new_utop = st.number_input(
            "u_top [kPa]",
            value=float(lokaal.get("u_top", u_top_kpa)),
            min_value=0.0, max_value=500.0, step=1.0,
            key=f"utop_local_{selected}",
        )
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💾 Override opslaan", key=f"save_water_{selected}"):
                st.session_state.sonderingen[selected]["waterdruk_lokaal"] = {
                    "knik_nap": new_knik, "u_top": new_utop
                }
                st.success("Opgeslagen. Klik nogmaals op ‘Bereken’ bovenaan om door te rekenen.")
        with col_b2:
            if st.button("🔄 Reset naar globaal", key=f"reset_water_{selected}"):
                st.session_state.sonderingen[selected]["waterdruk_lokaal"] = None
                st.success("Reset.")

    # Data tabel
    with st.expander("📋 Genormaliseerde data", expanded=False):
        show_cols = [c for c in [cm["diepte"], "diepte_nap", cm["qc"], "qt", "q_net",
                                  "Qt", "Rf", "u0", "sigma_v0", "sigma_v0_eff", "grondlaag"]
                     if c and c in df.columns]
        st.dataframe(df[show_cols].head(50), use_container_width=True)
