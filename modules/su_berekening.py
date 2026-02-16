"""
Module 4: Su Berekening
- Bereken ongedraineerde schuifsterkte: Su = q_net / Nkt
- Nkt-factor instelbaar per grondtype (literatuur + projectervaring)
- Alleen voor dijkmateriaal (fijnkorrelig, geselecteerd in Module 3)
- Toon Su-profiel per sondering
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Standaard Nkt waarden per grondtype (literatuur)
DEFAULT_NKT = {
    "Klei (normaal geconsolideerd)": {"Nkt": 15, "range": (12, 18)},
    "Klei (overgeconsolideerd)": {"Nkt": 17, "range": (15, 20)},
    "Veen / organisch": {"Nkt": 12, "range": (8, 15)},
    "Silt / kleiig silt": {"Nkt": 14, "range": (10, 18)},
}


def bereken_Su(q_net: pd.Series, Nkt: float) -> pd.Series:
    """
    Bereken ongedraineerde schuifsterkte.
    Su = q_net / Nkt
    
    Parameters:
        q_net: netto conusweerstand [MPa]
        Nkt: conusfactor [-]
    
    Returns:
        Su [kPa]
    """
    return (q_net * 1000) / Nkt  # MPa → kPa, dan delen door Nkt


def render():
    st.title("📊 Module 4: Su Berekening")
    st.markdown("""
    ### Wat doen we hier?
    We berekenen de **ongedraineerde schuifsterkte** ($S_u$) van het dijkmateriaal. 
    Dit is de belangrijkste sterkteparameter voor stabiliteitsberekeningen van dijken.
    
    $$S_u = \\frac{q_{net}}{N_{kt}}$$
    
    **Hoe werkt het?**
    - We nemen de **netto conusweerstand** ($q_{net}$) uit Module 2
    - We delen door de **Nkt-factor** die afhangt van het grondtype (uit Module 3)
    - Su wordt **alleen berekend voor het dijkmateriaal** (fijnkorrelig, geselecteerd in Module 3)
    - Zand en grof materiaal hebben geen ongedraineerde schuifsterkte
    
    **De Nkt-waarden worden overgenomen uit de Uitgangspunten (Module 0).**
    Pas ze daar aan als je andere waarden wilt gebruiken op basis van labresultaten.
    """)
    
    # Check of classificatie is uitgevoerd
    geclassificeerd = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                       if v.get("geclassificeerd")}
    
    if not geclassificeerd:
        st.warning("⚠️ Voer eerst de classificatie uit in Module 3.")
        return
    
    # --- Haal Nkt uit uitgangspunten ---
    up = st.session_state.get("uitgangspunten", {})
    nkt_up = up.get("nkt_factoren", {})
    
    default_nkt_klei = nkt_up.get("klei_nc", {}).get("Nkt", 15.0)
    default_nkt_veen = nkt_up.get("veen", {}).get("Nkt", 12.0)
    default_nkt_silt = nkt_up.get("silt", {}).get("Nkt", 14.0)
    default_nkt_overig = nkt_up.get("klei_oc", {}).get("Nkt", 17.0)
    
    # --- Nkt instellingen ---
    st.subheader("Nkt-factor Instellingen")
    st.info("📋 **Uit Uitgangspunten overgenomen.** Pas aan in Module 0 of hieronder voor deze berekening.")
    
    col1, col2 = st.columns(2)
    with col1:
        Nkt_klei = st.slider("Nkt — Klei (NC)", 8.0, 25.0, float(default_nkt_klei), 0.5, key="nkt_klei",
                             help="Normaal geconsolideerde klei. Hogere Nkt = lagere Su (conservatiever).")
    with col2:
        Nkt_veen = st.slider("Nkt — Veen / Organisch", 5.0, 20.0, float(default_nkt_veen), 0.5, key="nkt_veen",
                             help="Veen heeft typisch een lagere Nkt vanwege hoog vochtgehalte.")
    
    col3, col4 = st.columns(2)
    with col3:
        Nkt_silt = st.slider("Nkt — Silt", 8.0, 22.0, float(default_nkt_silt), 0.5, key="nkt_silt",
                             help="Tussenwaarde voor silt en siltig klei.")
    with col4:
        Nkt_overig = st.slider("Nkt — Overgeconsolideerde klei", 10.0, 22.0, float(default_nkt_overig), 0.5, key="nkt_overig",
                               help="OC klei heeft hogere Nkt door hogere stijfheid.")
    
    # --- Bereken Su ---
    st.markdown("---")
    
    if st.button("🔄 Bereken Su voor alle sonderingen"):
        for name, data in geclassificeerd.items():
            df = data["df"]
            cm = data["col_mapping"]
            
            if "q_net" not in df.columns:
                st.warning(f"⚠️ {name}: q_net ontbreekt. Normaliseer eerst.")
                continue
            
            # Bepaal Nkt per meting op basis van classificatie
            nkt_map = {
                1: Nkt_overig,       # Gevoelig fijnkorrelig
                2: Nkt_veen,         # Organisch/veen
                3: Nkt_klei,         # Klei (slap)
                4: Nkt_klei,         # Klei tot silt (vast)
                5: Nkt_silt,         # Silt
                9: Nkt_overig,       # Stijf fijnkorrelig
            }
            
            if "robertson_zone" in df.columns:
                df["Nkt_gebruikt"] = df["robertson_zone"].map(nkt_map)
            else:
                df["Nkt_gebruikt"] = Nkt_klei  # Fallback
            
            # Bereken Su alleen voor dijkmateriaal (fijnkorrelig)
            dijkmat_mask = df.get("is_dijkmateriaal", pd.Series([True] * len(df), index=df.index))
            
            df["Su"] = np.nan
            valid = dijkmat_mask & df["Nkt_gebruikt"].notna()
            df.loc[valid, "Su"] = bereken_Su(df.loc[valid, "q_net"], df.loc[valid, "Nkt_gebruikt"])
            
            # Verwijder negatieve Su waarden
            df.loc[df["Su"] < 0, "Su"] = np.nan
            
            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["su_berekend"] = True
        
        st.success("✅ Su berekend voor alle sonderingen")
    
    # --- Resultaten ---
    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                   if v.get("su_berekend")}
    
    if not su_berekend:
        return
    
    st.markdown("---")
    st.subheader("Su Profielen")
    
    # Keuze: individueel of alle samen
    view_mode = st.radio("Weergave", ["Per sondering", "Alle sonderingen samen"], horizontal=True)
    
    if view_mode == "Per sondering":
        selected = st.selectbox("Selecteer sondering", list(su_berekend.keys()), key="su_select")
        
        if selected:
            data = su_berekend[selected]
            df = data["df"]
            cm = data["col_mapping"]
            diepte = df[cm["diepte"]]
            
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=["qt [MPa]", "Su [kPa]", "Nkt [-]"],
                shared_yaxes=True
            )
            
            # qt
            fig.add_trace(go.Scatter(x=df["qt"], y=diepte, name="qt", line=dict(color="blue")), row=1, col=1)
            
            # Su
            su_valid = df["Su"].notna()
            fig.add_trace(go.Scatter(
                x=df.loc[su_valid, "Su"], y=diepte[su_valid], 
                name="Su", line=dict(color="red", width=2)
            ), row=1, col=2)
            
            # Nkt
            if "Nkt_gebruikt" in df.columns:
                nkt_valid = df["Nkt_gebruikt"].notna()
                fig.add_trace(go.Scatter(
                    x=df.loc[nkt_valid, "Nkt_gebruikt"], y=diepte[nkt_valid],
                    name="Nkt", line=dict(color="gray")
                ), row=1, col=3)
            
            fig.update_yaxes(autorange="reversed", title_text="Diepte [m]", row=1, col=1)
            fig.update_yaxes(autorange="reversed", row=1, col=2)
            fig.update_yaxes(autorange="reversed", row=1, col=3)
            fig.update_layout(height=700, template="plotly_white", title=f"Su Profiel: {selected}")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistieken
            su_data = df["Su"].dropna()
            if not su_data.empty:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Su gemiddeld", f"{su_data.mean():.1f} kPa")
                col2.metric("Su mediaan", f"{su_data.median():.1f} kPa")
                col3.metric("Su min", f"{su_data.min():.1f} kPa")
                col4.metric("Su max", f"{su_data.max():.1f} kPa")
    
    else:
        # Alle sonderingen samen
        fig = go.Figure()
        
        for name, data in su_berekend.items():
            df = data["df"]
            cm = data["col_mapping"]
            diepte = df[cm["diepte"]]
            su_valid = df["Su"].notna()
            
            if su_valid.any():
                fig.add_trace(go.Scatter(
                    x=df.loc[su_valid, "Su"], y=diepte[su_valid],
                    mode="lines", name=name
                ))
        
        fig.update_layout(
            title="Su Profielen — Alle Sonderingen",
            yaxis=dict(autorange="reversed", title="Diepte [m]"),
            xaxis=dict(title="Su [kPa]"),
            height=700,
            template="plotly_white",
        )
        
        st.plotly_chart(fig, use_container_width=True)
