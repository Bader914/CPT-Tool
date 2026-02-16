"""
Module 6: Visualisatie & Rapportage
- Alle sonderingen samen visualiseren
- Trends en afwijkende sonderingen identificeren
- Export naar CSV/Excel
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io


def render():
    st.markdown("""
    <div class="hero-container">
        <h1>📈 Stap 6 — Rapportage & Export</h1>
        <p>Totaaloverzicht Su-profielen — trends, afwijkingen & Excel/CSV export</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); 
         padding: 1.2rem; border-radius: 12px; margin-bottom: 1rem; border-left: 4px solid #1976d2;">
        <h4 style="margin-top:0; color: #1565c0;">Waarom deze stap?</h4>
        <p style="margin-bottom:0;">
            Door <b>alle Su-profielen samen</b> te plotten, zien we of het Su-beeld consistent is 
            over het dijktraject. Grote afwijkingen kunnen wijzen op <b>lokale bodemvariatie</b>, 
            <b>meetfouten</b>, of een <b>verkeerde Nkt-keuze</b>. De resultaten worden geëxporteerd 
            voor verdere verwerking in D-Stability of andere tools.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                   if v.get("su_berekend")}
    
    if not su_berekend:
        st.markdown("""
        <div style="background: #fff3e0; padding: 1rem; border-radius: 10px; border-left: 4px solid #ff9800;">
            <b>⚠️ Su nog niet berekend</b><br>
            Ga eerst naar <b>Stap 4 — Su Berekening</b> om de schuifsterkte te berekenen.
        </div>
        """, unsafe_allow_html=True)
        return
        return
    
    tab1, tab2, tab3 = st.tabs(["📊 Overzicht", "🔍 Afwijkingen", "📥 Export"])
    
    # --- Tab 1: Overzicht alle profielen ---
    with tab1:
        st.subheader("Alle Su-profielen")
        
        col_left, col_right = st.columns([3, 1])
        
        with col_right:
            show_mean = st.checkbox("Toon gemiddelde", value=True)
            show_envelope = st.checkbox("Toon bandbreedte (± 1σ)", value=True)
            show_labels = st.checkbox("Toon labels", value=True)
        
        with col_left:
            fig = go.Figure()
            
            # Verzamel alle Su data
            all_su_data = []
            
            for name, data in su_berekend.items():
                df = data["df"]
                cm = data["col_mapping"]
                diepte = df[cm["diepte"]]
                su_valid = df["Su"].notna()
                
                if su_valid.any():
                    fig.add_trace(go.Scatter(
                        x=df.loc[su_valid, "Su"], y=diepte[su_valid],
                        mode="lines", name=name, opacity=0.6
                    ))
                    
                    for _, row in df.loc[su_valid].iterrows():
                        all_su_data.append({
                            "diepte": row[cm["diepte"]],
                            "Su": row["Su"],
                            "sondering": name
                        })
            
            # Gemiddelde en bandbreedte
            if all_su_data and (show_mean or show_envelope):
                all_df = pd.DataFrame(all_su_data)
                # Bin op diepte
                all_df["diepte_bin"] = (all_df["diepte"] * 2).round() / 2  # 0.5m bins
                stats = all_df.groupby("diepte_bin")["Su"].agg(["mean", "std", "count"]).reset_index()
                stats = stats[stats["count"] >= 2]  # Minimaal 2 sonderingen
                
                if show_mean and not stats.empty:
                    fig.add_trace(go.Scatter(
                        x=stats["mean"], y=stats["diepte_bin"],
                        name="Gemiddelde Su",
                        line=dict(color="black", width=3)
                    ))
                
                if show_envelope and not stats.empty:
                    su_upper = stats["mean"] + stats["std"]
                    su_lower = (stats["mean"] - stats["std"]).clip(lower=0)
                    
                    fig.add_trace(go.Scatter(
                        x=su_upper, y=stats["diepte_bin"],
                        name="+1σ", line=dict(color="gray", dash="dot"), showlegend=False
                    ))
                    fig.add_trace(go.Scatter(
                        x=su_lower, y=stats["diepte_bin"],
                        name="-1σ", line=dict(color="gray", dash="dot"),
                        fill="tonextx", fillcolor="rgba(128,128,128,0.1)", showlegend=False
                    ))
            
            # Labdata toevoegen indien beschikbaar
            for name, data in su_berekend.items():
                if "lab_data" in data and "lab_mapping" in data:
                    lab_df = data["lab_data"]
                    lm = data["lab_mapping"]
                    fig.add_trace(go.Scatter(
                        x=lab_df[lm["su"]], y=lab_df[lm["diepte"]],
                        mode="markers", name=f"Lab: {name}",
                        marker=dict(size=12, symbol="diamond", line=dict(width=2, color="black"))
                    ))
            
            fig.update_layout(
                title="Su Profielen — Totaaloverzicht",
                yaxis=dict(autorange="reversed", title="Diepte [m]"),
                xaxis=dict(title="Su [kPa]"),
                height=800,
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # --- Tab 2: Afwijkende sonderingen ---
    with tab2:
        st.subheader("Afwijkende Sonderingen Identificeren")
        
        if len(su_berekend) < 2:
            st.info("Minimaal 2 sonderingen nodig voor vergelijking.")
            return
        
        # Bereken gemiddelde Su per diepte-interval
        su_summary = []
        for name, data in su_berekend.items():
            df = data["df"]
            cm = data["col_mapping"]
            su_valid = df["Su"].notna()
            
            if su_valid.any():
                su_mean = df.loc[su_valid, "Su"].mean()
                su_median = df.loc[su_valid, "Su"].median()
                su_std = df.loc[su_valid, "Su"].std()
                su_count = su_valid.sum()
                
                su_summary.append({
                    "Sondering": name,
                    "Su gemiddeld [kPa]": round(su_mean, 1),
                    "Su mediaan [kPa]": round(su_median, 1),
                    "Su std [kPa]": round(su_std, 1),
                    "Metingen": su_count,
                })
        
        if su_summary:
            summary_df = pd.DataFrame(su_summary)
            
            # Markeer afwijkende sonderingen (> 1.5σ van gemiddelde)
            global_mean = summary_df["Su gemiddeld [kPa]"].mean()
            global_std = summary_df["Su gemiddeld [kPa]"].std()
            
            summary_df["Afwijking"] = summary_df["Su gemiddeld [kPa]"].apply(
                lambda x: "⚠️ Afwijkend" if abs(x - global_mean) > 1.5 * global_std else "✅ Normaal"
            )
            
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Box plot
            fig = go.Figure()
            for name, data in su_berekend.items():
                df = data["df"]
                su_valid = df["Su"].notna()
                if su_valid.any():
                    fig.add_trace(go.Box(y=df.loc[su_valid, "Su"], name=name))
            
            fig.update_layout(
                title="Su Verdeling per Sondering",
                yaxis=dict(title="Su [kPa]"),
                height=500,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # --- Tab 3: Export ---
    with tab3:
        st.subheader("Data Exporteren")
        
        export_format = st.radio("Export formaat", ["CSV", "Excel"], horizontal=True)
        
        # Combineer alle data
        all_export = []
        for name, data in su_berekend.items():
            df = data["df"].copy()
            cm = data["col_mapping"]
            
            export_cols = {}
            export_cols["Sondering"] = name
            if cm.get("diepte") and cm["diepte"] in df.columns:
                export_cols["Diepte [m]"] = df[cm["diepte"]]
            if cm.get("qc") and cm["qc"] in df.columns:
                export_cols["qc [MPa]"] = df[cm["qc"]]
            if "qt" in df.columns:
                export_cols["qt [MPa]"] = df["qt"]
            if cm.get("fs") and cm["fs"] in df.columns:
                export_cols["fs [MPa]"] = df[cm["fs"]]
            if "Rf" in df.columns:
                export_cols["Rf [%]"] = df["Rf"]
            if cm.get("u2") and cm["u2"] in df.columns:
                export_cols["u2 [MPa]"] = df[cm["u2"]]
            if "q_net" in df.columns:
                export_cols["q_net [MPa]"] = df["q_net"]
            if "Su" in df.columns:
                export_cols["Su [kPa]"] = df["Su"]
            if "Nkt_gebruikt" in df.columns:
                export_cols["Nkt"] = df["Nkt_gebruikt"]
            if "grondsoort" in df.columns:
                export_cols["Grondsoort"] = df["grondsoort"]
            
            export_df = pd.DataFrame(export_cols)
            all_export.append(export_df)
        
        if all_export:
            combined = pd.concat(all_export, ignore_index=True)
            
            st.markdown(f"**Totaal:** {len(combined)} rijen, {combined['Sondering'].nunique()} sonderingen")
            
            with st.expander("📋 Preview export"):
                st.dataframe(combined.head(50), use_container_width=True)
            
            if export_format == "CSV":
                csv_data = combined.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    data=csv_data,
                    file_name="cpt_su_resultaten.csv",
                    mime="text/csv"
                )
            else:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    combined.to_excel(writer, index=False, sheet_name="Resultaten")
                
                st.download_button(
                    "⬇️ Download Excel",
                    data=buffer.getvalue(),
                    file_name="cpt_su_resultaten.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
