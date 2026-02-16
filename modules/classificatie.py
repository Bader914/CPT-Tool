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


def classificeer_robertson(qt: pd.Series, Rf: pd.Series, sigma_v0: pd.Series) -> pd.Series:
    """
    Vereenvoudigde Robertson classificatie op basis van qt en Rf.
    Gebaseerd op Robertson 1990 SBTn chart.
    
    Returns:
        Series met zone nummers (1-9)
    """
    # Genormaliseerde parameters
    q_net = qt - sigma_v0
    Qt = q_net / sigma_v0.replace(0, np.nan)
    
    zones = pd.Series(index=qt.index, dtype=int)
    
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
    st.markdown("""
    <div class="hero-compact">
        <div class="hero-text">
            <div class="step-tag">Stap 3 van 6</div>
            <h1>🧱 Classificatie</h1>
            <p class="sub">Robertson 1990 — grondsoort & dijkmateriaal</p>
        </div>
        <div class="hero-why">
            Bepaal per meetpunt de <b>grondsoort</b> zodat we alleen Su berekenen voor 
            fijnkorrelig dijkmateriaal (klei, silt, veen).
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Toon verwachte dijkopbouw uit uitgangspunten
    st.markdown("**Verwachte dijkopbouw (uit Uitgangspunten):**")
    up = st.session_state.get("uitgangspunten", {})
    lagen = up.get("lagen", [])
    
    if lagen:
        for laag in lagen:
            dijkmat_icon = "🟢" if laag.get("is_dijkmateriaal") else "⚪"
            top = laag.get("top_nap")
            onder = laag.get("onder_nap")
            positie = f"NAP {top:+.1f}m tot {onder:+.1f}m" if top is not None and onder is not None else "variabel"
            st.markdown(
                f"- {dijkmat_icon} **{laag['naam']}**: {positie} — {laag['materiaal']}"
            )
    
    st.markdown("---")
    
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
            
            if "qt" not in df.columns or "Rf" not in df.columns or "sigma_v0" not in df.columns:
                fout_count += 1
                missing = [c for c in ["qt", "Rf", "sigma_v0"] if c not in df.columns]
                resultaten.append({"Sondering": name, "Status": f"⚠️ Ontbreekt: {', '.join(missing)}", "Zones": "—"})
                continue
            
            # Classificatie
            df["robertson_zone"] = classificeer_robertson(df["qt"], df["Rf"], df["sigma_v0"])
            df["grondsoort"] = df["robertson_zone"].map(lambda z: ROBERTSON_ZONES.get(z, {}).get("naam", "Onbekend"))
            df["materiaal_type"] = df["robertson_zone"].map(lambda z: ROBERTSON_ZONES.get(z, {}).get("type", "onbekend"))
            
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
        diepte = df[cm["diepte"]]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Classificatie profiel
            fig = go.Figure()
            
            for zone_nr, zone_info in ROBERTSON_ZONES.items():
                mask = df["robertson_zone"] == zone_nr
                if mask.any():
                    fig.add_trace(go.Scatter(
                        x=df.loc[mask, "qt"],
                        y=diepte[mask],
                        mode="markers",
                        name=zone_info["naam"],
                        marker=dict(color=zone_info["kleur"], size=4),
                    ))
            
            fig.update_layout(
                title=f"Classificatie: {selected}",
                yaxis=dict(autorange="reversed", title="Diepte [m]"),
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
        st.markdown("---")
        st.subheader("Boringinformatie (optioneel)")
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
