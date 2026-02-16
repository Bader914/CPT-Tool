"""
Module 5: Validatie & Labvergelijking
- Vergelijk Su-profielen met laboratoriumproeven (triaxiaalproeven, DSS)
- Visualiseer afwijkingen
- Kalibreer Nkt-factor op basis van meetdata
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


def render():
    st.markdown("""
    <div class="hero-section">
        <span class="step-label">Stap 5 van 6</span>
        <h1>✅ Validatie</h1>
        <p class="subtitle">Vergelijk Su-profielen met laboratoriumproeven — kalibreer Nkt</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="why-card">
        <h4>💡 Waarom deze stap?</h4>
        <p>
            De Nkt-factor is een <b>empirische aanname</b>. Door de CPT-Su te vergelijken met 
            laboratoriumproeven (triaxiaal, DSS, vane test) controleren we of de gekozen Nkt 
            realistisch is. Als de CPT-Su systematisch afwijkt, moet de Nkt worden aangepast 
            in <b>Stap 0 — Uitgangspunten</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                   if v.get("su_berekend")}
    
    if not su_berekend:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Su nog niet berekend</h4>
            <p>Ga eerst naar <b>Stap 4 — Su Berekening</b> om de schuifsterkte te berekenen.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
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
