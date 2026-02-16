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


def bereken_Su(q_net: pd.Series, Nkt: pd.Series) -> pd.Series:
    """
    Bereken ongedraineerde schuifsterkte per meetpunt.
    Su = q_net / Nkt  →  [kPa]
    Nkt varieert per meetpunt (Robertson zone + boven/onder GWS).
    """
    return (q_net * 1000) / Nkt  # MPa → kPa


def render():
    st.caption("Stap 4 — Su = q_net / Nkt per grondlaag")
    
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
    
    if not lagen:
        st.error("❌ **Geen grondlagen gevonden.** Ga eerst naar Stap 0 — Uitgangspunten en vul de lagen in.")
        return
    
    # Zoek Nkt waarden per type grondlaag — uitsluitend uit uitgangspunten
    nkt_veen = next((l["Nkt"] for l in lagen if "Veen" in l["naam"] and "kleiig" not in l["naam"] and l.get("Nkt")), None)
    nkt_veen_kleiig = next((l["Nkt"] for l in lagen if "Veen_kleiig" in l["naam"] and l.get("Nkt")), None)
    nkt_klei_humeus = next((l["Nkt"] for l in lagen if "Klei_humeus" in l["naam"] and l.get("Nkt")), None)
    nkt_klei_siltig = next((l["Nkt"] for l in lagen if "Klei_siltig" in l["naam"] and l.get("Nkt")), None)
    nkt_klei_zandig = next((l["Nkt"] for l in lagen if "Klei_zandig" in l["naam"] and l.get("Nkt")), None)
    nkt_dijkmat_boven = next((l["Nkt"] for l in lagen if "7a_" in l["naam"] and l.get("Nkt")), None)
    nkt_dijkmat_onder = next((l["Nkt"] for l in lagen if "7b_Dijksmateriaal klei <" in l["naam"] and l.get("Nkt")), None)
    nkt_klei_diep = next((l["Nkt"] for l in lagen if "Klei_diep" in l["naam"] and l.get("Nkt")), None)
    nkt_basisveen = next((l["Nkt"] for l in lagen if "Basisveen" in l["naam"] and l.get("Nkt")), None)
    
    # Controleer of alle benodigde Nkt waarden beschikbaar zijn
    missing_nkt = []
    if nkt_veen is None: missing_nkt.append("1_Veen")
    if nkt_dijkmat_boven is None: missing_nkt.append("7a_Dijksmateriaal")
    if nkt_dijkmat_onder is None: missing_nkt.append("7b_Dijksmateriaal")
    if nkt_klei_diep is None: missing_nkt.append("8_Klei_diep")
    
    if missing_nkt:
        st.warning(f"⚠️ Nkt ontbreekt voor: {', '.join(missing_nkt)}. Vul deze in bij Stap 0 — Uitgangspunten.")
    
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
    
    # Robertson zone → Nkt mapping (alleen uit uitgangspunten, geen fallbacks)
    nkt_map = {}
    if nkt_klei_diep is not None: nkt_map[1] = nkt_klei_diep     # Gevoelig fijnkorrelig
    if nkt_veen is not None: nkt_map[2] = nkt_veen               # Organisch/veen
    if nkt_dijkmat_onder is not None: nkt_map[3] = nkt_dijkmat_onder  # Klei (slap)
    if nkt_klei_humeus is not None: nkt_map[4] = nkt_klei_humeus  # Klei tot silt
    if nkt_klei_siltig is not None: nkt_map[5] = nkt_klei_siltig  # Silt
    if nkt_klei_diep is not None: nkt_map[9] = nkt_klei_diep     # Stijf fijnkorrelig
    
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
            
            # Bepaal Nkt per meting op basis van Robertson classificatie (uit uitgangspunten)
            if "robertson_zone" in df.columns:
                df["Nkt_gebruikt"] = df["robertson_zone"].map(nkt_map)
                unmapped = df["Nkt_gebruikt"].isna() & df["robertson_zone"].notna()
                if unmapped.any():
                    st.info(f"{name}: {unmapped.sum()} meetpunten zonder Nkt-toewijzing (zones: {df.loc[unmapped, 'robertson_zone'].unique().tolist()})")
            else:
                st.warning(f"{name}: Geen Robertson zone — classificeer eerst (Stap 3).")
                continue
            
            # Dijksmateriaal klei: onderscheid boven/onder GWS → Nkt 7a / 7b
            gwl = up.get("dijkopbouw", {}).get("gwl", 0.0)
            diepte_col = cm.get("diepte")
            if diepte_col and diepte_col in df.columns:
                diepte_su = df[diepte_col]
                dijkmat_flag = df.get("is_dijkmateriaal", pd.Series([False]*len(df), index=df.index))
                if isinstance(dijkmat_flag, pd.Series):
                    dijkmat_flag = dijkmat_flag.fillna(False).astype(bool)
                # Alleen klei-dijksmateriaal (niet veen, zone 2)
                niet_veen = df.get("robertson_zone", pd.Series(dtype=int)) != 2
                klei_dijkmat = dijkmat_flag & niet_veen
                if klei_dijkmat.any():
                    df.loc[klei_dijkmat & (diepte_su > gwl), "Nkt_gebruikt"] = nkt_dijkmat_boven   # 7a
                    df.loc[klei_dijkmat & (diepte_su <= gwl), "Nkt_gebruikt"] = nkt_dijkmat_onder  # 7b
            
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
            
            # Data tabel: Nkt per meetpunt
            with st.expander("📊 Data: q_net → Nkt → Su per meetpunt", expanded=False):
                d_col = cm.get("diepte")
                show_cols = [c for c in [d_col, "robertson_zone", "q_net", "Nkt_gebruikt", "Su"]
                             if c and c in df.columns]
                su_table = df[df["Su"].notna()][show_cols].copy()
                su_table = su_table.round(3)
                st.caption(f"{len(su_table)} meetpunten met Su — GWS = NAP {up.get('dijkopbouw', {}).get('gwl', 0.0):+.1f}m")
                st.dataframe(su_table, use_container_width=True, hide_index=True)
    
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
