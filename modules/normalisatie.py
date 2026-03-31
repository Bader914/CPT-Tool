"""
Module 2: Normalisatie (Qt)
- Corrigeer conusweerstand voor poriedruk: qt = qc + (1 - a) * u2
- Bereken afgeleide parameters: Rf, Bq, q_net
- Maak sonderingen onderling vergelijkbaar
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def bereken_qt(qc: pd.Series, u2: pd.Series, a: float = 0.80) -> pd.Series:
    """
    Corrigeer conusweerstand voor poriedruk.
    qt = qc + (1 - a) * u2
    
    Parameters:
        qc: conusweerstand [MPa]
        u2: poriedruk [MPa]
        a: nettoquotient conus (standaard 0.80, afhankelijk van conustype)
    """
    return qc + (1 - a) * u2


def bereken_q_net(qt: pd.Series, sigma_v0: pd.Series) -> pd.Series:
    """
    Bereken netto conusweerstand.
    q_net = qt - sigma_v0
    """
    return qt - sigma_v0


def bereken_Rf(fs: pd.Series, qc: pd.Series) -> pd.Series:
    """
    Bereken wrijvingsgetal.
    Rf = (fs / qc) * 100  [%]
    """
    return (fs / qc.replace(0, np.nan)) * 100


def bereken_Bq(u2: pd.Series, u0: pd.Series, qt: pd.Series, sigma_v0: pd.Series) -> pd.Series:
    """
    Bereken poriedrukratio.
    Bq = (u2 - u0) / (qt - sigma_v0)
    """
    q_net = qt - sigma_v0
    return (u2 - u0) / q_net.replace(0, np.nan)


def bereken_sigma_v0_per_laag(diepte: pd.Series, lagen: list, kruinniveau: float, gwl_nap: float) -> tuple:
    """
    Bereken σv0, σ'v0 en u0 met per-laag volumegewicht uit uitgangspunten.
    Gebruikt gamma_droog boven GWS, gamma_nat onder GWS per grondlaag.
    
    Parameters:
        diepte: sondeerlengte [m] (positief naar beneden, t.o.v. maaiveld/kruin)
        lagen: grondlagen uit uitgangspunten (top_nap, onder_nap, gamma_nat, gamma_droog)
        kruinniveau: bovenkant dijk [m NAP]
        gwl_nap: grondwaterstand [m NAP]
    
    Returns:
        sigma_v0: totale verticale spanning [kPa]
        sigma_v0_eff: effectieve verticale spanning [kPa]
        u0: hydrostatische waterspanning [kPa]
    """
    gamma_w = 9.81  # kN/m³
    gwl_depth = kruinniveau - gwl_nap  # GWS diepte t.o.v. maaiveld [m]
    
    # Bouw lagen profiel: converteer NAP → diepte t.o.v. maaiveld
    defined_layers = []
    for laag in lagen:
        top_nap = laag.get("top_nap")
        onder_nap = laag.get("onder_nap")
        if top_nap is not None and onder_nap is not None:
            defined_layers.append({
                "top": max(0.0, kruinniveau - top_nap),
                "bottom": kruinniveau - onder_nap,
                "gamma_droog": laag.get("gamma_droog", laag.get("gamma_nat", 18.0)),
                "gamma_nat": laag.get("gamma_nat", 18.0),
            })
    defined_layers.sort(key=lambda x: x["top"])
    
    # Gemiddelde gamma voor lagen zonder gedefinieerde grenzen (veen, klei etc.)
    undefined_gammas = [laag["gamma_nat"] for laag in lagen
                        if laag.get("top_nap") is None and laag.get("gamma_nat")]
    gamma_undefined = float(np.mean(undefined_gammas)) if undefined_gammas else 15.0
    
    # Bouw gamma-profiel per meetpunt
    d = diepte.values.astype(float)
    gamma_profile = np.full_like(d, gamma_undefined, dtype=float)
    
    for lg in defined_layers:
        mask = (d >= lg["top"]) & (d < lg["bottom"])
        above_gwl = mask & (d < gwl_depth)
        below_gwl = mask & (d >= gwl_depth)
        gamma_profile[above_gwl] = lg["gamma_droog"]
        gamma_profile[below_gwl] = lg["gamma_nat"]
    
    # Integreer σv0: cumulatieve som van gamma × Δz
    dz = np.diff(d, prepend=0.0)
    dz[0] = d[0]  # eerste punt: van maaiveld tot eerste meting
    sigma_v0 = np.cumsum(gamma_profile * dz)
    
    # Waterspanning (nul boven GWS)
    u0 = np.maximum(0.0, (d - gwl_depth)) * gamma_w
    sigma_v0_eff = np.maximum(0.0, sigma_v0 - u0)
    
    return (
        pd.Series(sigma_v0, index=diepte.index),
        pd.Series(sigma_v0_eff, index=diepte.index),
        pd.Series(u0, index=diepte.index),
    )


# ── Default volumegewicht per Robertson zone (kN/m³) ──
ROBERTSON_GAMMA_DEFAULTS = {
    1: 16.0,   # Gevoelig fijnkorrelig
    2: 10.5,   # Organisch (veen)
    3: 15.0,   # Klei (slap)
    4: 14.0,   # Klei tot silt (humeus)
    5: 17.0,   # Silt tot zandige klei
    6: 18.0,   # Zand tot kleiig zand
    7: 19.0,   # Zand tot zandig gravel
    8: 20.0,   # Zand (dicht)
    9: 18.5,   # Stijf fijnkorrelig
}

# Robertson zone → zoekpatroon in uitgangspunten lagennaam
ROBERTSON_LAAG_MAPPING = {
    1: "Klei_diep",
    2: "Veen",
    3: "Dijksmateriaal klei",
    4: "Klei_humeus",
    5: "Klei_siltig",
    6: "Klei_zandig",
    7: "zand",
    8: "zand",
    9: "Klei_diep",
}


def robertson_zone_naar_gamma(zone: int, lagen: list) -> float:
    """Koppel Robertson zone aan volumegewicht uit uitgangspunten lagen."""
    pattern = ROBERTSON_LAAG_MAPPING.get(zone, "")
    if pattern:
        for laag in lagen:
            if pattern.lower() in laag["naam"].lower():
                return laag.get("gamma_nat", ROBERTSON_GAMMA_DEFAULTS.get(zone, 18.0))
    return ROBERTSON_GAMMA_DEFAULTS.get(zone, 18.0)


def bereken_sigma_v0_met_robertson(
    diepte: pd.Series, robertson_zones: pd.Series,
    lagen: list, kruinniveau: float, gwl_nap: float
) -> tuple:
    """
    Herbereken σv0 met volumegewicht per meetpunt afgeleid uit Robertson classificatie.
    Gebruikt uitgangspunten-lagen om gamma per Robertson zone te bepalen.
    """
    gamma_w = 9.81
    gwl_depth = kruinniveau - gwl_nap

    d = diepte.values.astype(float)
    zones = robertson_zones.values.astype(int)

    gamma_profile = np.array([robertson_zone_naar_gamma(int(z), lagen) for z in zones])

    dz = np.diff(d, prepend=0.0)
    dz[0] = d[0]
    sigma_v0 = np.cumsum(gamma_profile * dz)

    u0 = np.maximum(0.0, (d - gwl_depth)) * gamma_w
    sigma_v0_eff = np.maximum(0.0, sigma_v0 - u0)

    return (
        pd.Series(sigma_v0, index=diepte.index),
        pd.Series(sigma_v0_eff, index=diepte.index),
        pd.Series(u0, index=diepte.index),
    )


def render():
    st.caption("Stap 2 — Poriedrukcorrectie qt, spanningen σv0, Rf & Bq")
    
    # --- Check of er sonderingen zijn ---
    if not st.session_state.get("sonderingen"):
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Geen sonderingen geladen</h4>
            <p>Ga eerst naar <b>Stap 1 — Data Inladen</b> om sonderingen te uploaden.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # --- Check readiness van sonderingen ---
    sonderingen = st.session_state.sonderingen
    gereed = {k: v for k, v in sonderingen.items() 
              if v.get("col_mapping", {}).get("diepte") and v.get("col_mapping", {}).get("qc")}
    niet_gereed = {k: v for k, v in sonderingen.items() 
                   if not (v.get("col_mapping", {}).get("diepte") and v.get("col_mapping", {}).get("qc"))}
    
    # Status overzicht
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Totaal", f"{len(sonderingen)} sonderingen")
    with col_s2:
        st.metric("Gereed voor normalisatie", f"{len(gereed)} ✅")
    with col_s3:
        already_done = sum(1 for v in sonderingen.values() if v.get("genormaliseerd"))
        if already_done > 0:
            st.metric("Al genormaliseerd", f"{already_done} 🔄")
        else:
            st.metric("Nog te verwerken", f"{len(gereed)} ⏳")
    
    if niet_gereed:
        with st.expander(f"⚠️ {len(niet_gereed)} sondering(en) kunnen niet worden verwerkt", expanded=True):
            for name in niet_gereed:
                cm = niet_gereed[name].get("col_mapping", {})
                missing = []
                if not cm.get("diepte"):
                    missing.append("diepte")
                if not cm.get("qc"):
                    missing.append("qc")
                st.markdown(f"- **{name}**: kolom(men) `{', '.join(missing)}` ontbreken — "
                           f"ga terug naar **Stap 1** en stel de kolom mapping in")
    
    if not gereed:
        st.error(
            "❌ **Geen enkele sondering heeft de benodigde kolommen (diepte + qc).** "
            "Ga terug naar Stap 1 en controleer de kolom mapping van elke sondering."
        )
        return
    
    # --- Haal uitgangspunten op ---
    up = st.session_state.get("uitgangspunten", {})
    default_a = up.get("conustype", {}).get("a_factor", 0.80)
    default_gwl = up.get("dijkopbouw", {}).get("gwl", 0.0)
    default_kruin = up.get("dijkopbouw", {}).get("kruinniveau", 4.0)
    lagen = up.get("lagen", [])
    
    # --- Parameters tonen (uit uitgangspunten) ---
    st.subheader("Gebruikte parameters")
    
    if not lagen:
        st.error("❌ **Geen grondlagen gevonden.** Ga eerst naar Stap 0 — Uitgangspunten en vul de dijkopbouw in.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        a_factor = st.number_input(
            "Nettoquotient conus (a)", 
            min_value=0.50, max_value=1.00, value=default_a, step=0.01,
            help="Uit Uitgangspunten. Afhankelijk van conustype."
        )
        gwl = st.number_input(
            "Grondwaterstand [m NAP]",
            min_value=-10.0, max_value=10.0, value=default_gwl, step=0.1,
            help="Uit Uitgangspunten. Dagelijkse grondwaterstand."
        )
    
    with col2:
        # Toon gamma per laag (read-only, uit uitgangspunten)
        gamma_info = []
        for laag in lagen:
            if laag.get("gamma_nat"):
                top = laag.get("top_nap")
                onder = laag.get("onder_nap")
                pos = f"NAP {top:+.1f} tot {onder:+.1f}" if top is not None and onder is not None else "variabel"
                gamma_info.append({
                    "Laag": laag["naam"], "γ_droog": laag.get("gamma_droog", "—"),
                    "γ_nat": laag["gamma_nat"], "Positie": pos
                })
        st.caption(f"σv0 berekend met per-laag γ uit Uitgangspunten · GWS = NAP {default_gwl:+.1f}m · Kruin = NAP {default_kruin:+.1f}m")
        st.dataframe(pd.DataFrame(gamma_info), use_container_width=True, hide_index=True, height=200)
    
    # --- Verwerk per sondering ---
    st.markdown("---")
    
    if st.button("▶️ Bereken Qt en afgeleide parameters", type="primary", use_container_width=True):
        progress = st.progress(0)
        total = len(gereed)
        succes_count = 0
        fout_count = 0
        resultaten = []  # Per-file status bijhouden
        
        for i, (name, data) in enumerate(gereed.items()):
            df = data["df"].copy()
            cm = data["col_mapping"]
            
            try:
                diepte = df[cm["diepte"]]
                qc = df[cm["qc"]]
                
                # Spanningsberekening — per-laag gamma uit uitgangspunten
                sigma_v0, sigma_v0_eff, u0 = bereken_sigma_v0_per_laag(
                    diepte, lagen, default_kruin, gwl
                )
                df["sigma_v0"] = sigma_v0 / 1000  # kPa → MPa
                df["sigma_v0_eff"] = sigma_v0_eff / 1000
                df["u0"] = u0 / 1000
                
                # Qt correctie — check of data al gecorrigeerd is
                is_qt_corrected = st.session_state.sonderingen[name].get("is_qt_corrected", False)
                
                if is_qt_corrected:
                    df["qt"] = qc  # Data bevat al qt (quantity 14), geen dubbele correctie
                    if cm.get("u2") and cm["u2"] in df.columns:
                        df["Bq"] = bereken_Bq(df[cm["u2"]], df["u0"], df["qt"], df["sigma_v0"])
                    resultaten.append({"Sondering": name, "Status": "✅ Verwerkt", "qt correctie": "Al gecorrigeerd (qty 14)", "Metingen": len(df)})
                elif cm.get("u2") and cm["u2"] in df.columns:
                    u2 = df[cm["u2"]]
                    df["qt"] = bereken_qt(qc, u2, a_factor)
                    df["Bq"] = bereken_Bq(u2, df["u0"], df["qt"], df["sigma_v0"])
                    resultaten.append({"Sondering": name, "Status": "✅ Verwerkt", "qt correctie": "Met u2 correctie", "Metingen": len(df)})
                else:
                    df["qt"] = qc  # Geen correctie mogelijk
                    resultaten.append({"Sondering": name, "Status": "✅ Verwerkt", "qt correctie": "Zonder u2 (qt = qc)", "Metingen": len(df)})
                
                # Afgeleide parameters
                df["q_net"] = bereken_q_net(df["qt"], df["sigma_v0"])
                
                # Qt — genormaliseerde conusweerstand (Robertson)
                df["Qt"] = df["q_net"] / df["sigma_v0_eff"].replace(0, np.nan)
                
                if cm.get("fs") and cm["fs"] in df.columns:
                    df["Rf"] = bereken_Rf(df[cm["fs"]], qc)
                
                # Sla op
                st.session_state.sonderingen[name]["df"] = df
                st.session_state.sonderingen[name]["genormaliseerd"] = True
                st.session_state.sonderingen[name]["parameters"] = {
                    "a": a_factor, "gwl": gwl, "kruinniveau": default_kruin,
                    "gamma_methode": "per-laag uit uitgangspunten"
                }
                
                succes_count += 1
                
            except Exception as e:
                fout_count += 1
                resultaten.append({"Sondering": name, "Status": f"❌ Fout: {e}", "qt correctie": "—", "Metingen": 0})
            
            progress.progress((i + 1) / total)
        
        # --- Resultaat samenvatting ---
        st.markdown("---")
        st.markdown("### Resultaat")
        
        if succes_count > 0 and fout_count == 0:
            st.success(f"✅ **{succes_count} van {succes_count} sondering(en)** succesvol genormaliseerd!")
        elif succes_count > 0 and fout_count > 0:
            st.warning(f"⚠️ **{succes_count} van {succes_count + fout_count} sondering(en)** genormaliseerd. {fout_count} mislukt.")
        else:
            st.error(f"❌ **Geen enkele sondering** kon worden genormaliseerd. Controleer de kolom mapping in Stap 1.")
        
        if niet_gereed:
            st.info(f"ℹ️ {len(niet_gereed)} sondering(en) overgeslagen wegens ontbrekende kolommen.")
        
        # Toon per-file resultaten
        if resultaten:
            st.dataframe(pd.DataFrame(resultaten), use_container_width=True, hide_index=True)
        
        if succes_count > 0:
            st.markdown("""
            <div class="next-step">
                <span class="arrow">➡</span>
                <p>Ga naar <b>Stap 3 — Classificatie</b> in het zijmenu 
                om de grondsoorten te bepalen op basis van de genormaliseerde parameters.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # --- Resultaten tonen ---
    genormaliseerd = {k: v for k, v in st.session_state.sonderingen.items() 
                      if v.get("genormaliseerd")}
    
    if genormaliseerd:
        st.markdown("---")
        st.subheader("Resultaten")
        
        selected = st.selectbox("Selecteer sondering", list(genormaliseerd.keys()), key="norm_select")
        
        if selected:
            data = genormaliseerd[selected]
            df = data["df"]
            cm = data["col_mapping"]
            
            # Plot qt, Qt, Rf naast elkaar
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=["qt [MPa]", "Qt [-] (genormaliseerd)", "Rf [%]"],
                shared_yaxes=True
            )
            
            diepte = df[cm["diepte"]]
            
            # qt
            if "qt" in df.columns:
                fig.add_trace(go.Scatter(x=df["qt"], y=diepte, name="qt", line=dict(color="#3b82f6", width=1.5)), row=1, col=1)
                if cm.get("qc"):
                    fig.add_trace(go.Scatter(x=df[cm["qc"]], y=diepte, name="qc", line=dict(color="#93c5fd", dash="dot", width=1)), row=1, col=1)
            
            # Qt (genormaliseerd)
            if "Qt" in df.columns:
                fig.add_trace(go.Scatter(x=df["Qt"], y=diepte, name="Qt", line=dict(color="#8b5cf6", width=1.5)), row=1, col=2)
            
            # Rf
            if "Rf" in df.columns:
                fig.add_trace(go.Scatter(x=df["Rf"], y=diepte, name="Rf", line=dict(color="#ef4444", width=1.5)), row=1, col=3)
            
            fig.update_yaxes(autorange="reversed", title_text="Diepte [m]", row=1, col=1)
            fig.update_yaxes(autorange="reversed", row=1, col=2)
            fig.update_yaxes(autorange="reversed", row=1, col=3)
            fig.update_layout(height=600, template="plotly_white", showlegend=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data tabel
            with st.expander("📋 Genormaliseerde data"):
                show_cols = [c for c in [cm["diepte"], cm["qc"], "qt", "q_net", "Qt", cm.get("fs"), "Rf", cm.get("u2"), "Bq", "sigma_v0", "sigma_v0_eff"] if c and c in df.columns]
                st.dataframe(df[show_cols].head(50), use_container_width=True)
