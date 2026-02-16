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
    st.title("📐 Module 2: Normalisatie (Qt)")
    st.markdown("""
    ### Wat doen we hier?
    In deze stap corrigeren we de **gemeten conusweerstand** ($q_c$) voor het effect van 
    **poriedruk** ($u_2$). Dit is nodig omdat de poriedruk werkt op het verschiloppervlak 
    achter de conuspunt, waardoor de gemeten waarde lager is dan de werkelijke weerstand.
    
    Daarnaast berekenen we **afgeleide parameters** die nodig zijn voor classificatie en 
    Su-berekening:
    
    | Parameter | Formule | Betekenis |
    |---|---|---|
    | $q_t$ | $q_c + (1-a) \\cdot u_2$ | Gecorrigeerde conusweerstand |
    | $q_{net}$ | $q_t - \\sigma_{v0}$ | Netto conusweerstand (gecorrigeerd voor diepte) |
    | $R_f$ | $(f_s / q_c) \\times 100\\%$ | Wrijvingsgetal (indicator grondtype) |
    | $B_q$ | $(u_2 - u_0) / q_{net}$ | Poriedrukratio (indicator drainagegedrag) |
    
    **De parameters worden overgenomen uit de Uitgangspunten (Module 0).** 
    Pas ze daar aan als je andere waarden wilt gebruiken.
    """)
    
    if not st.session_state.get("sonderingen"):
        st.warning("⚠️ Ga eerst naar Module 1 om sonderingen te laden.")
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
    
    if st.button("🔄 Bereken Qt en afgeleide parameters voor alle sonderingen"):
        progress = st.progress(0)
        sonderingen = st.session_state.sonderingen
        total = len(sonderingen)
        
        for i, (name, data) in enumerate(sonderingen.items()):
            df = data["df"].copy()
            cm = data["col_mapping"]
            
            if not cm.get("diepte") or not cm.get("qc"):
                st.warning(f"⚠️ {name}: Diepte of qc kolom ontbreekt. Overgeslagen.")
                continue
            
            diepte = df[cm["diepte"]]
            qc = df[cm["qc"]]
            
            # Spanningsberekening
            sigma_v0, sigma_v0_eff, u0 = bereken_sigma_v0(diepte, gamma, gwl)
            df["sigma_v0"] = sigma_v0 / 1000  # kPa → MPa
            df["sigma_v0_eff"] = sigma_v0_eff / 1000
            df["u0"] = u0 / 1000
            
            # Qt correctie
            if cm.get("u2"):
                u2 = df[cm["u2"]]
                df["qt"] = bereken_qt(qc, u2, a_factor)
                df["Bq"] = bereken_Bq(u2, df["u0"], df["qt"], df["sigma_v0"])
            else:
                df["qt"] = qc  # Geen correctie mogelijk
                st.info(f"ℹ️ {name}: Geen u2 beschikbaar, qt = qc (geen correctie)")
            
            # Afgeleide parameters
            df["q_net"] = bereken_q_net(df["qt"], df["sigma_v0"])
            
            if cm.get("fs"):
                df["Rf"] = bereken_Rf(df[cm["fs"]], qc)
            
            # Sla op
            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["genormaliseerd"] = True
            st.session_state.sonderingen[name]["parameters"] = {
                "a": a_factor, "gamma": gamma, "gwl": gwl
            }
            
            progress.progress((i + 1) / total)
        
        st.success(f"✅ {total} sondering(en) genormaliseerd")
    
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
