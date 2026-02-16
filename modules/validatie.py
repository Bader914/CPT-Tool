"""
Module 5: Validatie & Labvergelijking
- Vergelijk Su-profielen met Deltares CPT-tool resultaten
- Vergelijk met laboratoriumproeven (triaxiaalproeven)
- Visualiseer afwijkingen
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


def render():
    st.title("✅ Module 5: Validatie & Labvergelijking")
    st.markdown("""
    ### Wat doen we hier?
    We **valideren** de berekende Su-profielen door ze te vergelijken met onafhankelijke bronnen:
    
    1. **Deltares CPT-tool** — Onafhankelijke herberekening van Su met andere software.
       Hiermee controleren we of onze berekening consistent is.
    2. **Laboratoriumproeven** — Triaxiaalproeven, DSS-proeven of vane tests geven de 
       "echte" Su. Als er labproeven beschikbaar zijn, kunnen we de Nkt-factor kalibreren.
    
    **Waarom is validatie cruciaal?**  
    De Nkt-factor is een empirische aanname. Door te vergelijken met labresultaten 
    kunnen we beoordelen of de gekozen Nkt realistisch is. Als de CPT-Su systematisch 
    hoger of lager is dan de lab-Su, moet de Nkt worden aangepast in Module 0 (Uitgangspunten).
    """)
    
    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                   if v.get("su_berekend")}
    
    if not su_berekend:
        st.warning("⚠️ Bereken eerst Su in Module 4.")
        return
    
    tab1, tab2 = st.tabs(["📊 Deltares CPT-tool", "🧪 Laboratoriumproeven"])
    
    # --- Tab 1: Deltares vergelijking ---
    with tab1:
        st.subheader("Vergelijking met Deltares CPT-tool")
        st.markdown("""
        Upload de resultaten van de Deltares CPT-tool (CSV/Excel) om te vergelijken 
        met de berekende Su-profielen.
        """)
        
        deltares_file = st.file_uploader(
            "Upload Deltares CPT-tool resultaten",
            type=["csv", "xlsx"],
            key="deltares_upload"
        )
        
        if deltares_file:
            try:
                if deltares_file.name.endswith(".csv"):
                    deltares_df = pd.read_csv(deltares_file, sep=None, engine="python")
                else:
                    deltares_df = pd.read_excel(deltares_file)
                
                st.success(f"✅ Deltares data geladen: {len(deltares_df)} rijen")
                
                with st.expander("📋 Deltares data preview"):
                    st.dataframe(deltares_df.head(20), use_container_width=True)
                
                # Kolom mapping voor Deltares data
                st.markdown("**Kolom mapping Deltares data:**")
                dcols = deltares_df.columns.tolist()
                col1, col2 = st.columns(2)
                
                with col1:
                    d_diepte = st.selectbox("Diepte kolom (Deltares)", dcols, key="d_diepte")
                with col2:
                    d_su = st.selectbox("Su kolom (Deltares)", dcols, key="d_su")
                
                # Vergelijk met geselecteerde sondering
                selected = st.selectbox(
                    "Vergelijk met sondering:", 
                    list(su_berekend.keys()), 
                    key="deltares_compare"
                )
                
                if selected and d_diepte and d_su:
                    data = su_berekend[selected]
                    df = data["df"]
                    cm = data["col_mapping"]
                    diepte = df[cm["diepte"]]
                    
                    fig = go.Figure()
                    
                    # Onze Su
                    su_valid = df["Su"].notna()
                    fig.add_trace(go.Scatter(
                        x=df.loc[su_valid, "Su"], y=diepte[su_valid],
                        name="Su (berekend)", line=dict(color="red", width=2)
                    ))
                    
                    # Deltares Su
                    fig.add_trace(go.Scatter(
                        x=deltares_df[d_su], y=deltares_df[d_diepte],
                        name="Su (Deltares)", line=dict(color="blue", width=2, dash="dash")
                    ))
                    
                    fig.update_layout(
                        title=f"Validatie: {selected} vs Deltares",
                        yaxis=dict(autorange="reversed", title="Diepte [m]"),
                        xaxis=dict(title="Su [kPa]"),
                        height=700,
                        template="plotly_white",
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.sonderingen[selected]["deltares_data"] = deltares_df
                    st.session_state.sonderingen[selected]["deltares_mapping"] = {
                        "diepte": d_diepte, "su": d_su
                    }
            
            except Exception as e:
                st.error(f"Fout bij inlezen: {e}")
        
        else:
            st.info("Upload Deltares CPT-tool resultaten (CSV/Excel) om te vergelijken.")
    
    # --- Tab 2: Laboratoriumproeven ---
    with tab2:
        st.subheader("Vergelijking met Laboratoriumproeven")
        st.markdown("""
        Upload laboratoriumresultaten (triaxiaalproeven, DSS, vane tests) 
        om de CPT-gebaseerde Su te valideren.
        
        **Verwacht formaat:** CSV/Excel met kolommen voor diepte en Su (kPa).
        """)
        
        lab_file = st.file_uploader(
            "Upload laboratoriumresultaten",
            type=["csv", "xlsx"],
            key="lab_upload"
        )
        
        if lab_file:
            try:
                if lab_file.name.endswith(".csv"):
                    lab_df = pd.read_csv(lab_file, sep=None, engine="python")
                else:
                    lab_df = pd.read_excel(lab_file)
                
                st.success(f"✅ Labdata geladen: {len(lab_df)} proeven")
                
                with st.expander("📋 Lab data preview"):
                    st.dataframe(lab_df, use_container_width=True)
                
                # Kolom mapping
                lcols = lab_df.columns.tolist()
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    l_diepte = st.selectbox("Diepte kolom (lab)", lcols, key="l_diepte")
                with col2:
                    l_su = st.selectbox("Su kolom (lab)", lcols, key="l_su")
                with col3:
                    l_type = st.selectbox(
                        "Proeftype kolom (optioneel)", 
                        ["(geen)"] + lcols, key="l_type"
                    )
                
                # Vergelijk
                selected = st.selectbox(
                    "Vergelijk met sondering:", 
                    list(su_berekend.keys()), 
                    key="lab_compare"
                )
                
                if selected and l_diepte and l_su:
                    data = su_berekend[selected]
                    df = data["df"]
                    cm = data["col_mapping"]
                    diepte = df[cm["diepte"]]
                    
                    fig = go.Figure()
                    
                    # Onze Su
                    su_valid = df["Su"].notna()
                    fig.add_trace(go.Scatter(
                        x=df.loc[su_valid, "Su"], y=diepte[su_valid],
                        name="Su (CPT)", line=dict(color="red", width=2)
                    ))
                    
                    # Lab Su punten
                    if l_type != "(geen)" and l_type in lab_df.columns:
                        # Kleur per proeftype
                        for proeftype in lab_df[l_type].unique():
                            mask = lab_df[l_type] == proeftype
                            fig.add_trace(go.Scatter(
                                x=lab_df.loc[mask, l_su],
                                y=lab_df.loc[mask, l_diepte],
                                mode="markers",
                                name=f"Lab: {proeftype}",
                                marker=dict(size=10, symbol="diamond")
                            ))
                    else:
                        fig.add_trace(go.Scatter(
                            x=lab_df[l_su], y=lab_df[l_diepte],
                            mode="markers",
                            name="Lab Su",
                            marker=dict(size=10, color="green", symbol="diamond")
                        ))
                    
                    fig.update_layout(
                        title=f"CPT Su vs Laboratorium: {selected}",
                        yaxis=dict(autorange="reversed", title="Diepte [m]"),
                        xaxis=dict(title="Su [kPa]"),
                        height=700,
                        template="plotly_white",
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Statistieken vergelijking
                    st.subheader("Vergelijkingsstatistieken")
                    st.info("💡 Interpoleer CPT Su naar labdieptes voor kwantitatieve vergelijking.")
                    
                    st.session_state.sonderingen[selected]["lab_data"] = lab_df
                    st.session_state.sonderingen[selected]["lab_mapping"] = {
                        "diepte": l_diepte, "su": l_su, "type": l_type
                    }
            
            except Exception as e:
                st.error(f"Fout bij inlezen: {e}")
        
        else:
            st.info("Upload laboratoriumresultaten (CSV/Excel) om te vergelijken met CPT Su.")
