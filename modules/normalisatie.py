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


def bereken_sigma_v0(diepte: pd.Series, gamma: float = 18.0, gwl: float = 0.0) -> tuple:
    """
    Bereken totale en effectieve verticale spanning.
    
    Parameters:
        diepte: diepte [m]
        gamma: volumegewicht grond [kN/m³]
        gwl: grondwaterstand [m-mv] (positief naar beneden)
    
    Returns:
        sigma_v0: totale verticale spanning [kPa]
        sigma_v0_eff: effectieve verticale spanning [kPa]
        u0: hydrostatische waterspanning [kPa]
    """
    gamma_w = 9.81  # kN/m³
    
    sigma_v0 = diepte * gamma
    u0 = np.maximum(0, (diepte - gwl)) * gamma_w
    sigma_v0_eff = sigma_v0 - u0
    
    return sigma_v0, sigma_v0_eff, u0


def render():
    st.markdown("""
    <div class="hero-container">
        <h1>📐 Stap 2 — Normalisatie</h1>
        <p>Poriedrukcorrectie qt, spanningen σv0, afgeleide parameters Rf & Bq</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Stap uitleg ---
    st.markdown("""
    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); 
         padding: 1.2rem; border-radius: 12px; margin-bottom: 1rem; border-left: 4px solid #1976d2;">
        <h4 style="margin-top:0; color: #1565c0;">Waarom deze stap?</h4>
        <p style="margin-bottom:0.5rem;">
            De <b>gemeten conusweerstand</b> ($q_c$) is niet de werkelijke weerstand. 
            Door poriedruk die werkt op het verschiloppervlak achter de conuspunt, is de gemeten waarde 
            <b>lager</b> dan de werkelijke. Zonder correctie zou je de sterkte van de grond <b>onderschatten</b>.
        </p>
        <p style="margin-bottom:0;">
            Daarnaast berekenen we de <b>spanningen</b> en <b>afgeleide parameters</b> die nodig zijn 
            voor de Robertson classificatie (Stap 3) en de Su-berekening (Stap 4).
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    | Parameter | Formule | Betekenis |
    |---|---|---|
    | $q_t$ | $q_c + (1-a) \\cdot u_2$ | Gecorrigeerde conusweerstand |
    | $q_{net}$ | $q_t - \\sigma_{v0}$ | Netto conusweerstand (gecorrigeerd voor diepte) |
    | $R_f$ | $(f_s / q_c) \\times 100\\%$ | Wrijvingsgetal (indicator grondtype) |
    | $B_q$ | $(u_2 - u_0) / q_{net}$ | Poriedrukratio (indicator drainagegedrag) |
    """)
    
    # --- Check of er sonderingen zijn ---
    if not st.session_state.get("sonderingen"):
        st.markdown("""
        <div style="background: #fff3e0; padding: 1rem; border-radius: 10px; border-left: 4px solid #ff9800;">
            <b>⚠️ Geen sonderingen geladen</b><br>
            Ga eerst naar <b>Stap 1 — Data Inladen</b> om sonderingen te uploaden.
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
    st.info(f"📋 **Uit Uitgangspunten:** a = {default_a} | GWS = NAP {default_gwl:+.1f}m | Kruinniveau = NAP {default_kruin:+.1f}m")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        a_factor = st.number_input(
            "Nettoquotient conus (a)", 
            min_value=0.50, max_value=1.00, value=default_a, step=0.01,
            help="Uit Uitgangspunten. Afhankelijk van conustype."
        )
    with col2:
        gamma = st.number_input(
            "Volumegewicht grond γ [kN/m³]",
            min_value=10.0, max_value=25.0, value=18.0, step=0.5,
            help="Gemiddeld volumegewicht. De tool gebruikt per laag de γ uit de Uitgangspunten."
        )
    with col3:
        gwl = st.number_input(
            "Grondwaterstand [m NAP]",
            min_value=-10.0, max_value=10.0, value=default_gwl, step=0.1,
            help="Uit Uitgangspunten. Dagelijkse grondwaterstand."
        )
    
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
                
                # Spanningsberekening
                sigma_v0, sigma_v0_eff, u0 = bereken_sigma_v0(diepte, gamma, gwl)
                df["sigma_v0"] = sigma_v0 / 1000  # kPa → MPa
                df["sigma_v0_eff"] = sigma_v0_eff / 1000
                df["u0"] = u0 / 1000
                
                # Qt correctie
                if cm.get("u2") and cm["u2"] in df.columns:
                    u2 = df[cm["u2"]]
                    df["qt"] = bereken_qt(qc, u2, a_factor)
                    df["Bq"] = bereken_Bq(u2, df["u0"], df["qt"], df["sigma_v0"])
                    resultaten.append({"Sondering": name, "Status": "✅ Verwerkt", "qt correctie": "Met u2 correctie", "Metingen": len(df)})
                else:
                    df["qt"] = qc  # Geen correctie mogelijk
                    resultaten.append({"Sondering": name, "Status": "✅ Verwerkt", "qt correctie": "Zonder u2 (qt = qc)", "Metingen": len(df)})
                
                # Afgeleide parameters
                df["q_net"] = bereken_q_net(df["qt"], df["sigma_v0"])
                
                if cm.get("fs") and cm["fs"] in df.columns:
                    df["Rf"] = bereken_Rf(df[cm["fs"]], qc)
                
                # Sla op
                st.session_state.sonderingen[name]["df"] = df
                st.session_state.sonderingen[name]["genormaliseerd"] = True
                st.session_state.sonderingen[name]["parameters"] = {
                    "a": a_factor, "gamma": gamma, "gwl": gwl
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
            <div style="background: #e8f5e9; padding: 1rem; border-radius: 10px; border-left: 4px solid #4caf50; margin-top: 1rem;">
                <b>👉 Volgende stap:</b> Ga naar <b>Stap 3 — Classificatie</b> in het zijmenu 
                om de grondsoorten te bepalen op basis van de genormaliseerde parameters.
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
            
            # Plot qt, fs, u2 naast elkaar
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=["qt [MPa]", "fs [MPa]", "Rf [%]"],
                shared_yaxes=True
            )
            
            diepte = df[cm["diepte"]]
            
            # qt
            if "qt" in df.columns:
                fig.add_trace(go.Scatter(x=df["qt"], y=diepte, name="qt", line=dict(color="blue")), row=1, col=1)
                if cm.get("qc"):
                    fig.add_trace(go.Scatter(x=df[cm["qc"]], y=diepte, name="qc", line=dict(color="lightblue", dash="dot")), row=1, col=1)
            
            # fs
            if cm.get("fs"):
                fig.add_trace(go.Scatter(x=df[cm["fs"]], y=diepte, name="fs", line=dict(color="green")), row=1, col=2)
            
            # Rf
            if "Rf" in df.columns:
                fig.add_trace(go.Scatter(x=df["Rf"], y=diepte, name="Rf", line=dict(color="red")), row=1, col=3)
            
            fig.update_yaxes(autorange="reversed", title_text="Diepte [m]", row=1, col=1)
            fig.update_yaxes(autorange="reversed", row=1, col=2)
            fig.update_yaxes(autorange="reversed", row=1, col=3)
            fig.update_layout(height=700, template="plotly_white", showlegend=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data tabel
            with st.expander("📋 Genormaliseerde data"):
                show_cols = [c for c in [cm["diepte"], cm["qc"], "qt", "q_net", cm.get("fs"), "Rf", cm.get("u2"), "Bq", "sigma_v0"] if c and c in df.columns]
                st.dataframe(df[show_cols].head(50), use_container_width=True)
