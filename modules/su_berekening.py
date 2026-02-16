"""
Module 4: Su Berekening
- Bereken ongedraineerde schuifsterkte: Su = q_net / Nkt
- Nkt-factor per grondlaag (Tabel 71 — traject 14-1)
- Alleen voor dijkmateriaal (fijnkorrelig, geselecteerd in Module 3)
- Toon Su-profiel per sondering
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def bereken_Su(q_net: pd.Series, Nkt: float) -> pd.Series:
    """
    Bereken ongedraineerde schuifsterkte.
    Su = q_net / Nkt  →  [kPa]
    """
    return (q_net * 1000) / Nkt  # MPa → kPa


def render():
    st.markdown("""
    <div class="hero-section">
        <span class="step-label">Stap 4 van 6</span>
        <h1>📊 Su Berekening</h1>
        <p class="subtitle">Ongedraineerde schuifsterkte uit CPT — Su = q_net / Nkt</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="why-card">
        <h4>💡 Waarom deze stap?</h4>
        <p>
            De <b>ongedraineerde schuifsterkte</b> ($S_u$) is de sterkteparameter die bepaalt of de dijk 
            stabiel is bij snel optreden van belasting. We berekenen $S_u$ per meetpunt op basis 
            van de <b>netto conusweerstand</b> en de <b>Nkt-factor per grondlaag</b> (Tabel 71). 
            Alleen fijnkorrelig dijkmateriaal (geselecteerd in Stap 3) krijgt een Su-waarde.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check of classificatie is uitgevoerd
    geclassificeerd = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                       if v.get("geclassificeerd")}
    
    if not geclassificeerd:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Classificatie nog niet uitgevoerd</h4>
            <p>Ga eerst naar <b>Stap 3 — Classificatie</b> om de grondsoorten te bepalen.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # --- Haal Nkt per grondlaag uit uitgangspunten ---
    up = st.session_state.get("uitgangspunten", {})
    lagen = up.get("lagen", [])
    
    # Bouw Nkt-mapping per Robertson zone op basis van de grondlagen
    # Robertson zones → meest passende grondlaag Nkt
    nkt_per_robertson = {}
    
    # Zoek Nkt waarden per type grondlaag
    nkt_veen = next((l["Nkt"] for l in lagen if "Veen" in l["naam"] and "kleiig" not in l["naam"] and l.get("Nkt")), 17.1)
    nkt_veen_kleiig = next((l["Nkt"] for l in lagen if "Veen_kleiig" in l["naam"] and l.get("Nkt")), 16.7)
    nkt_klei_humeus = next((l["Nkt"] for l in lagen if "Klei_humeus" in l["naam"] and l.get("Nkt")), 16.8)
    nkt_klei_siltig = next((l["Nkt"] for l in lagen if "Klei_siltig" in l["naam"] and l.get("Nkt")), 18.2)
    nkt_klei_zandig = next((l["Nkt"] for l in lagen if "Klei_zandig" in l["naam"] and l.get("Nkt")), 20.0)
    nkt_dijkmat_boven = next((l["Nkt"] for l in lagen if "7a_" in l["naam"] and l.get("Nkt")), 14.5)
    nkt_dijkmat_onder = next((l["Nkt"] for l in lagen if "7b_Dijksmateriaal klei <" in l["naam"] and l.get("Nkt")), 14.1)
    nkt_klei_diep = next((l["Nkt"] for l in lagen if "Klei_diep" in l["naam"] and l.get("Nkt")), 20.0)
    nkt_basisveen = next((l["Nkt"] for l in lagen if "Basisveen" in l["naam"] and l.get("Nkt")), 20.0)
    
    # Toon overzicht Nkt-toewijzing
    st.markdown("""
    <div class="section-header"><h3>Nkt per grondlaag (Tabel 71)</h3></div>
    """, unsafe_allow_html=True)
    
    nkt_display = []
    for laag in lagen:
        if laag.get("Nkt") is not None:
            nkt_display.append({"Grondlaag": laag["naam"], "Nkt": laag["Nkt"]})
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(pd.DataFrame(nkt_display), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("""
        **Robertson zone → Nkt toewijzing:**
        
        | Robertson zone | Nkt gebruikt |
        |---|---|
        | 1 — Gevoelig fijnkorrelig | Klei diep (default) |
        | 2 — Organisch (veen) | 1 Veen |
        | 3 — Klei (slap) | 7b Dijksmateriaal klei < gws |
        | 4 — Klei tot silt | 4 Klei humeus |
        | 5 — Silt / zandige klei | 5 Klei siltig |
        | 9 — Stijf fijnkorrelig | 8 Klei diep |
        """)
    
    # Robertson zone → Nkt mapping
    nkt_map = {
        1: nkt_klei_diep,        # Gevoelig fijnkorrelig → default
        2: nkt_veen,             # Organisch/veen → 1_Veen
        3: nkt_dijkmat_onder,    # Klei (slap) → 7b dijksmateriaal
        4: nkt_klei_humeus,      # Klei tot silt → 4_Klei_humeus
        5: nkt_klei_siltig,      # Silt → 5_Klei_siltig
        9: nkt_klei_diep,        # Stijf fijnkorrelig → 8_Klei_diep
    }
    
    # --- Bereken Su ---
    st.markdown("---")
    
    if st.button("Bereken Su voor alle sonderingen", type="primary", use_container_width=True):
        progress = st.progress(0)
        total = len(geclassificeerd)
        
        for i, (name, data) in enumerate(geclassificeerd.items()):
            df = data["df"]
            cm = data["col_mapping"]
            
            if "q_net" not in df.columns:
                st.warning(f"{name}: q_net ontbreekt. Normaliseer eerst.")
                continue
            
            # Bepaal Nkt per meting op basis van Robertson classificatie
            if "robertson_zone" in df.columns:
                df["Nkt_gebruikt"] = df["robertson_zone"].map(nkt_map)
            else:
                df["Nkt_gebruikt"] = nkt_dijkmat_onder  # Fallback
            
            # Bereken Su alleen voor dijkmateriaal (fijnkorrelig)
            dijkmat_mask = df.get("is_dijkmateriaal", pd.Series([True] * len(df), index=df.index))
            
            df["Su"] = np.nan
            valid = dijkmat_mask & df["Nkt_gebruikt"].notna()
            df.loc[valid, "Su"] = bereken_Su(df.loc[valid, "q_net"], df.loc[valid, "Nkt_gebruikt"])
            
            # Verwijder negatieve Su
            df.loc[df["Su"] < 0, "Su"] = np.nan
            
            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["su_berekend"] = True
            progress.progress((i + 1) / total)
        
        st.success(f"Su berekend voor {total} sondering(en)")
    
    # --- Resultaten ---
    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                   if v.get("su_berekend")}
    
    if not su_berekend:
        return
    
    st.markdown("---")
    
    # Keuze: individueel of alle samen
    view_mode = st.radio("Weergave", ["Per sondering", "Alle sonderingen samen"], 
                         horizontal=True, label_visibility="collapsed")
    
    if view_mode == "Per sondering":
        selected = st.selectbox("Selecteer sondering", list(su_berekend.keys()), key="su_select")
        
        if selected:
            data = su_berekend[selected]
            df = data["df"]
            cm = data["col_mapping"]
            diepte = df[cm["diepte"]]
            
            # Statistieken bovenaan
            su_data = df["Su"].dropna()
            if not su_data.empty:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Gemiddeld", f"{su_data.mean():.1f} kPa")
                c2.metric("Mediaan", f"{su_data.median():.1f} kPa")
                c3.metric("Min", f"{su_data.min():.1f} kPa")
                c4.metric("Max", f"{su_data.max():.1f} kPa")
            
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=["qt [MPa]", "Su [kPa]", "Nkt [-]"],
                shared_yaxes=True,
                horizontal_spacing=0.06,
            )
            
            fig.add_trace(go.Scatter(x=df["qt"], y=diepte, name="qt", 
                                     line=dict(color="#3b82f6", width=1.5)), row=1, col=1)
            
            su_valid = df["Su"].notna()
            fig.add_trace(go.Scatter(
                x=df.loc[su_valid, "Su"], y=diepte[su_valid], 
                name="Su", line=dict(color="#ef4444", width=2.5)
            ), row=1, col=2)
            
            if "Nkt_gebruikt" in df.columns:
                nkt_valid = df["Nkt_gebruikt"].notna()
                fig.add_trace(go.Scatter(
                    x=df.loc[nkt_valid, "Nkt_gebruikt"], y=diepte[nkt_valid],
                    name="Nkt", line=dict(color="#64748b", width=1), mode="lines"
                ), row=1, col=3)
            
            for col_idx in [1, 2, 3]:
                fig.update_yaxes(autorange="reversed", row=1, col=col_idx)
            fig.update_yaxes(title_text="Diepte [m]", row=1, col=1)
            fig.update_layout(
                height=700, template="plotly_white", 
                title=f"Su Profiel — {selected}",
                font=dict(family="Inter"),
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        fig = go.Figure()
        colors = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]
        
        for i, (name, data) in enumerate(su_berekend.items()):
            df = data["df"]
            cm = data["col_mapping"]
            diepte = df[cm["diepte"]]
            su_valid = df["Su"].notna()
            
            if su_valid.any():
                fig.add_trace(go.Scatter(
                    x=df.loc[su_valid, "Su"], y=diepte[su_valid],
                    mode="lines", name=name,
                    line=dict(color=colors[i % len(colors)], width=2)
                ))
        
        fig.update_layout(
            title="Su Profielen — Alle Sonderingen",
            yaxis=dict(autorange="reversed", title="Diepte [m]"),
            xaxis=dict(title="Su [kPa]"),
            height=700,
            template="plotly_white",
            font=dict(family="Inter"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        
        st.plotly_chart(fig, use_container_width=True)
