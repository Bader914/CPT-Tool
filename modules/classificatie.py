"""
Module 3: Classificatie & Dijkmateriaal Selectie
- Robertson classificatie op basis van Qt, Rf, Bq
- Bepaal grondsoort per laag
- Selecteer dijkmateriaal zones
- Koppel eventueel boringinformatie
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .normalisatie import bereken_sigma_v0_met_robertson


# Robertson 1990 classificatie zones (vereenvoudigd)
ROBERTSON_ZONES = {
    1: {"naam": "Gevoelige fijnkorrelige grond", "kleur": "#FF6B6B", "type": "fijnkorrelig"},
    2: {"naam": "Organisch materiaal (veen)", "kleur": "#8B4513", "type": "organisch"},
    3: {"naam": "Klei (slap tot vast)", "kleur": "#4CAF50", "type": "fijnkorrelig"},
    4: {"naam": "Klei tot silt (vast)", "kleur": "#81C784", "type": "fijnkorrelig"},
    5: {"naam": "Silt tot zandige klei", "kleur": "#FFC107", "type": "gemengd"},
    6: {"naam": "Zand tot kleiig zand", "kleur": "#FF9800", "type": "grofkorrelig"},
    7: {"naam": "Zand tot zandig gravel", "kleur": "#FFD54F", "type": "grofkorrelig"},
    8: {"naam": "Zand (dicht)", "kleur": "#E0E0E0", "type": "grofkorrelig"},
    9: {"naam": "Stijve fijnkorrelige grond", "kleur": "#9C27B0", "type": "fijnkorrelig"},
}


def classificeer_robertson(Qt: pd.Series, Rf: pd.Series) -> pd.Series:
    """
    Robertson 1990 classificatie op basis van Qt (genormaliseerd) en Rf.
    Gebruikt Qt = q_net / σ'v0 (effectieve spanning) zoals berekend in normalisatie.
    
    Returns:
        Series met zone nummers (1-9)
    """
    zones = pd.Series(index=Qt.index, dtype=int)
    
    # Vereenvoudigde classificatie op basis van Qt en Rf
    zones[(Qt <= 1)] = 2                                    # Organisch/veen
    zones[(Qt > 1) & (Qt <= 10) & (Rf > 3)] = 3           # Klei (slap)
    zones[(Qt > 1) & (Qt <= 10) & (Rf <= 3) & (Rf > 1)] = 4  # Klei tot silt
    zones[(Qt > 10) & (Qt <= 30) & (Rf > 1)] = 5          # Silt tot zandige klei
    zones[(Qt > 10) & (Qt <= 30) & (Rf <= 1)] = 6         # Zand tot kleiig zand
    zones[(Qt > 30) & (Qt <= 100) & (Rf <= 1)] = 7        # Zand
    zones[(Qt > 100)] = 8                                   # Zand (dicht)
    zones[(Qt > 1) & (Qt <= 10) & (Rf <= 1)] = 1          # Gevoelig
    zones[(Qt > 30) & (Rf > 1)] = 9                        # Stijf fijnkorrelig
    
    zones = zones.fillna(3)  # Default naar klei
    
    return zones.astype(int)


def render():
    st.caption("Stap 3 — Robertson 1990 classificatie, grondsoort & dijkmateriaal")
    
    # Toon verwachte dijkopbouw in expander
    up = st.session_state.get("uitgangspunten", {})
    lagen = up.get("lagen", [])
    
    if lagen:
        with st.expander("Verwachte dijkopbouw (uit Uitgangspunten)", expanded=False):
            for laag in lagen:
                dijk_tag = " **[Su]**" if laag.get("is_dijkmateriaal") else ""
                top = laag.get("top_nap")
                onder = laag.get("onder_nap")
                positie = f"NAP {top:+.1f}m tot {onder:+.1f}m" if top is not None and onder is not None else "variabel"
                st.markdown(
                    f"- **{laag['naam']}**: {positie} — {laag['materiaal']}{dijk_tag}"
                )
    
    # --- Check stappen status ---
    sonderingen = st.session_state.get("sonderingen", {})
    
    if not sonderingen:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Geen sonderingen geladen</h4>
            <p>Ga eerst naar <b>Stap 1 — Data Inladen</b> om sonderingen te uploaden.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Check genormaliseerd status per sondering
    genormaliseerd = {k: v for k, v in sonderingen.items() if v.get("genormaliseerd")}
    niet_genormaliseerd = {k: v for k, v in sonderingen.items() if not v.get("genormaliseerd")}
    
    # Status overzicht
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Totaal sonderingen", f"{len(sonderingen)}")
    with col_s2:
        st.metric("Genormaliseerd (Stap 2)", f"{len(genormaliseerd)} ✅")
    with col_s3:
        already_classified = sum(1 for v in sonderingen.values() if v.get("geclassificeerd"))
        st.metric("Al geclassificeerd", f"{already_classified} 🔄")
    
    if niet_genormaliseerd:
        with st.expander(f"⚠️ {len(niet_genormaliseerd)} sondering(en) nog niet genormaliseerd", expanded=False):
            for name in niet_genormaliseerd:
                cm = niet_genormaliseerd[name].get("col_mapping", {})
                has_cols = cm.get("diepte") and cm.get("qc")
                if has_cols:
                    st.markdown(f"- **{name}**: Kolommen gevonden, maar Stap 2 nog niet uitgevoerd")
                else:
                    missing = [k for k in ["diepte", "qc"] if not cm.get(k)]
                    st.markdown(f"- **{name}**: Kolom(men) `{', '.join(missing)}` ontbreken — eerst Stap 1 afronden")
    
    if not genormaliseerd:
        st.markdown("""
        <div class="why-card">
            <h4>❌ Geen genormaliseerde sonderingen</h4>
            <p>Dit kan twee oorzaken hebben:</p>
            <p><b>1.</b> De kolommen (diepte, qc) zijn niet herkend → ga naar <b>Stap 1</b> en stel de kolom mapping in</p>
            <p><b>2.</b> De normalisatie is nog niet uitgevoerd → ga naar <b>Stap 2</b> en klik op "Bereken Qt"</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.success(f"✅ **{len(genormaliseerd)} sondering(en)** gereed voor classificatie")
    
    # --- Classificatie uitvoeren ---
    st.subheader("Robertson Classificatie")
    
    if st.button("▶️ Classificeer alle sonderingen", type="primary", use_container_width=True):
        succes_count = 0
        fout_count = 0
        resultaten = []
        
        for name, data in genormaliseerd.items():
            df = data["df"]
            cm = data["col_mapping"]
            
            if "Qt" not in df.columns or "Rf" not in df.columns:
                fout_count += 1
                missing = [c for c in ["Qt", "Rf"] if c not in df.columns]
                resultaten.append({"Sondering": name, "Status": f"⚠️ Ontbreekt: {', '.join(missing)}", "Zones": "—"})
                continue
            
            # Classificatie — gebruikt Qt (=q_net/σ'v0) uit normalisatie
            df["robertson_zone"] = classificeer_robertson(df["Qt"], df["Rf"])
            df["grondsoort"] = df["robertson_zone"].map(lambda z: ROBERTSON_ZONES.get(z, {}).get("naam", "Onbekend"))
            df["materiaal_type"] = df["robertson_zone"].map(lambda z: ROBERTSON_ZONES.get(z, {}).get("type", "onbekend"))
            
            # Herbereken σv0 met volumegewicht uit Robertson classificatie
            params = st.session_state.sonderingen[name].get("parameters", {})
            mv_nap = params.get("maaiveld_nap", st.session_state.sonderingen[name].get("maaiveld_nap", up.get("dijkopbouw", {}).get("kruinniveau", 4.0)))
            gwl_val = params.get("gwl", up.get("dijkopbouw", {}).get("gwl", 0.0))
            
            sigma_v0_new, sigma_v0_eff_new, u0_new = bereken_sigma_v0_met_robertson(
                df[cm["diepte"]], df["robertson_zone"], lagen, mv_nap, gwl_val
            )
            # Update diepte_nap na herberekening
            df["diepte_nap"] = mv_nap - df[cm["diepte"]]
            df["sigma_v0"] = sigma_v0_new / 1000  # kPa → MPa
            df["sigma_v0_eff"] = sigma_v0_eff_new / 1000
            df["u0"] = u0_new / 1000
            df["q_net"] = df["qt"] - df["sigma_v0"]
            df["Qt"] = df["q_net"] / df["sigma_v0_eff"].replace(0, np.nan)
            
            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["geclassificeerd"] = True
            
            # Samenvatting zones
            zone_counts = df["robertson_zone"].value_counts()
            top_zones = ", ".join([f"Zone {z}" for z in zone_counts.head(3).index])
            
            succes_count += 1
            resultaten.append({"Sondering": name, "Status": "✅ Geclassificeerd", "Zones": top_zones})
        
        # Resultaat
        st.markdown("---")
        st.markdown("### Resultaat")
        
        if succes_count > 0 and fout_count == 0:
            st.success(f"✅ **{succes_count} sondering(en)** succesvol geclassificeerd!")
        elif succes_count > 0:
            st.warning(f"⚠️ {succes_count} succesvol, {fout_count} mislukt")
        else:
            st.error("❌ Geen enkele sondering kon worden geclassificeerd")
        
        if resultaten:
            st.dataframe(pd.DataFrame(resultaten), use_container_width=True, hide_index=True)
        
        if succes_count > 0:
            st.markdown("""
            <div class="next-step">
                <span class="arrow">➡</span>
                <p>Ga naar <b>Stap 4 — Su Berekening</b> in het zijmenu 
                om de ongedraineerde schuifsterkte te berekenen voor de fijnkorrelige lagen.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # --- Resultaten tonen ---
    geclassificeerd = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                       if v.get("geclassificeerd")}
    
    if not geclassificeerd:
        return
    
    st.markdown("---")
    selected = st.selectbox("Selecteer sondering", list(geclassificeerd.keys()), key="class_select")
    
    if selected:
        data = geclassificeerd[selected]
        df = data["df"]
        cm = data["col_mapping"]
        diepte_nap = df["diepte_nap"] if "diepte_nap" in df.columns else df[cm["diepte"]]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Classificatie profiel
            fig = go.Figure()
            
            for zone_nr, zone_info in ROBERTSON_ZONES.items():
                mask = df["robertson_zone"] == zone_nr
                if mask.any():
                    fig.add_trace(go.Scatter(
                        x=df.loc[mask, "qt"],
                        y=diepte_nap[mask],
                        mode="markers",
                        name=zone_info["naam"],
                        marker=dict(color=zone_info["kleur"], size=4),
                    ))
            
            fig.update_layout(
                title=f"Classificatie: {selected}",
                yaxis=dict(title="Niveau [m NAP]"),
                xaxis=dict(title="qt [MPa]"),
                height=700,
                template="plotly_white",
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Legenda / samenvatting
            st.markdown("**Laagverdeling:**")
            
            for zone_nr in sorted(df["robertson_zone"].unique()):
                zone_info = ROBERTSON_ZONES.get(zone_nr, {})
                mask = df["robertson_zone"] == zone_nr
                pct = mask.sum() / len(df) * 100
                st.markdown(f"🔹 **{zone_info.get('naam', '?')}**: {pct:.0f}%")
            
            st.markdown("---")
            st.markdown("**Dijkmateriaal selectie:**")
            
            # Selecteer welke zones als dijkmateriaal tellen
            dijkmat_zones = st.multiselect(
                "Selecteer dijkmateriaal zones",
                options=[(z, info["naam"]) for z, info in ROBERTSON_ZONES.items()],
                format_func=lambda x: x[1],
                default=[(z, info["naam"]) for z, info in ROBERTSON_ZONES.items() if info["type"] == "fijnkorrelig"],
                key=f"dijkmat_{selected}"
            )
            
            if dijkmat_zones:
                selected_zone_nrs = [z[0] for z in dijkmat_zones]
                mask = df["robertson_zone"].isin(selected_zone_nrs)
                df["is_dijkmateriaal"] = mask
                st.session_state.sonderingen[selected]["df"] = df
                
                st.info(f"📌 {mask.sum()} van {len(df)} metingen geselecteerd als dijkmateriaal ({mask.sum()/len(df)*100:.0f}%)")
        
        # --- Boringinformatie (optioneel) ---
        with st.expander("📂 Boringinformatie uploaden (optioneel)", expanded=False):
            boring_file = st.file_uploader(
                "Upload boring (CSV/Excel) om classificatie te valideren",
                type=["csv", "xlsx"],
                key=f"boring_{selected}"
            )
            
            if boring_file:
                try:
                    if boring_file.name.endswith(".csv"):
                        boring_df = pd.read_csv(boring_file, sep=None, engine="python")
                    else:
                        boring_df = pd.read_excel(boring_file)
                    
                    st.session_state.sonderingen[selected]["boring"] = boring_df
                    st.success(f"✅ Boring geladen: {len(boring_df)} lagen")
                    st.dataframe(boring_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Fout bij inlezen boring: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # FIGUUR 1 — OVERZICHT DIJKTRAJECT
    # Alle sonderingen met dijkmateriaal, qt over diepte
    # ═══════════════════════════════════════════════════════════════
    all_classified = {k: v for k, v in st.session_state.get("sonderingen", {}).items()
                      if v.get("geclassificeerd")}
    
    if len(all_classified) >= 1:
        st.markdown("---")
        st.subheader("Figuur 1 — Overzicht Sonderingen Dijktraject")
        st.caption("Alle geclassificeerde sonderingen — alleen dijkmateriaal (fijnkorrelig) — qt over diepte")
        
        # Keuze welke parameter
        param_col = st.radio(
            "Parameter", ["qt [MPa]", "Qt [-] (genormaliseerd)"],
            horizontal=True, key="fig1_param"
        )
        
        fig = go.Figure()
        colors = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", 
                  "#ec4899", "#14b8a6", "#f97316", "#06b6d4", "#84cc16",
                  "#e11d48", "#7c3aed", "#0891b2", "#65a30d"]
        
        for i, (name, data) in enumerate(all_classified.items()):
            df = data["df"]
            cm = data["col_mapping"]
            diepte_col = cm.get("diepte")
            
            if not diepte_col or diepte_col not in df.columns:
                continue
            
            # Filter op dijkmateriaal als kolom beschikbaar is
            if "is_dijkmateriaal" in df.columns:
                mask = df["is_dijkmateriaal"] == True
            elif "materiaal_type" in df.columns:
                mask = df["materiaal_type"].isin(["fijnkorrelig", "organisch"])
            else:
                mask = pd.Series([True] * len(df), index=df.index)
            
            if not mask.any():
                continue
            
            df_dijk = df[mask]
            diepte = df_dijk["diepte_nap"] if "diepte_nap" in df_dijk.columns else df_dijk[diepte_col]
            
            if param_col.startswith("Qt") and "Qt" in df_dijk.columns:
                x_vals = df_dijk["Qt"]
                x_title = "Qt [-]"
            elif "qt" in df_dijk.columns:
                x_vals = df_dijk["qt"]
                x_title = "qt [MPa]"
            else:
                continue
            
            fig.add_trace(go.Scatter(
                x=x_vals, y=diepte,
                mode="lines", name=name,
                line=dict(color=colors[i % len(colors)], width=1.5),
                opacity=0.8,
            ))
        
        # GWS lijn
        up = st.session_state.get("uitgangspunten", {})
        gwl = up.get("dijkopbouw", {}).get("gwl", 0.0)
        
        fig.update_layout(
            title="Overzicht Dijktraject — Dijkmateriaal",
            yaxis=dict(title="Niveau [m NAP]"),
            xaxis=dict(title=x_title if 'x_title' in dir() else "qt [MPa]"),
            height=700,
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)),
            font=dict(family="Inter"),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Samenvattingstabel
        with st.expander("📊 Samenvatting per sondering", expanded=False):
            summary_data = []
            for name, data in all_classified.items():
                df = data["df"]
                cm = data["col_mapping"]
                
                # Dijkmateriaal percentage
                if "is_dijkmateriaal" in df.columns:
                    dijk_pct = df["is_dijkmateriaal"].sum() / len(df) * 100
                elif "materiaal_type" in df.columns:
                    dijk_pct = df["materiaal_type"].isin(["fijnkorrelig", "organisch"]).sum() / len(df) * 100
                else:
                    dijk_pct = 0
                
                # Dieptebereik
                d_col = cm.get("diepte")
                d_range = f"{df[d_col].min():.1f} — {df[d_col].max():.1f}" if d_col and d_col in df.columns else "—"
                
                # qt statistieken voor dijkmateriaal
                qt_mean = df.loc[df.get("is_dijkmateriaal", pd.Series([True]*len(df))).fillna(False), "qt"].mean() if "qt" in df.columns else None
                
                summary_data.append({
                    "Sondering": name,
                    "Diepte [m]": d_range,
                    "Dijkmateriaal [%]": f"{dijk_pct:.0f}%",
                    "qt gem. [MPa]": f"{qt_mean:.2f}" if qt_mean and not np.isnan(qt_mean) else "—",
                    "Metingen": len(df),
                })
            
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
