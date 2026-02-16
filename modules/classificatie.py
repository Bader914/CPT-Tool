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
    <div class="hero-container">
        <h1>🧱 Classificatie</h1>
        <p>Robertson 1990 classificatie — grondsoort & dijkmateriaal selectie</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    We bepalen per meetpunt de **grondsoort** op basis van de CPT-gegevens (Robertson 1990 classificatie), 
    en selecteren vervolgens welke lagen als **dijkmateriaal** beschouwd worden.
    
    **Waarom is dit nodig?**
    - Su wordt alleen berekend voor **fijnkorrelig materiaal** (klei, silt, veen)
    - Zand en grof materiaal hebben geen ongedraineerde schuifsterkte
    - De classificatie helpt bij het identificeren van de dijkopbouw
    
    **Verwachte dijkopbouw (uit Uitgangspunten):**
    """)
    
    # Toon verwachte dijkopbouw uit uitgangspunten
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
    
    # Check of normalisatie is uitgevoerd
    genormaliseerd = {k: v for k, v in st.session_state.get("sonderingen", {}).items() 
                      if v.get("genormaliseerd")}
    
    if not genormaliseerd:
        st.warning("⚠️ Voer eerst de normalisatie uit in Module 2.")
        return
    
    # --- Classificatie uitvoeren ---
    st.subheader("Robertson Classificatie")
    
    if st.button("Classificeer alle sonderingen", type="primary", use_container_width=True):
        for name, data in genormaliseerd.items():
            df = data["df"]
            cm = data["col_mapping"]
            
            if "qt" not in df.columns or "Rf" not in df.columns or "sigma_v0" not in df.columns:
                st.warning(f"⚠️ {name}: qt, Rf of sigma_v0 ontbreekt. Normaliseer eerst.")
                continue
            
            # Classificatie
            df["robertson_zone"] = classificeer_robertson(df["qt"], df["Rf"], df["sigma_v0"])
            df["grondsoort"] = df["robertson_zone"].map(lambda z: ROBERTSON_ZONES.get(z, {}).get("naam", "Onbekend"))
            df["materiaal_type"] = df["robertson_zone"].map(lambda z: ROBERTSON_ZONES.get(z, {}).get("type", "onbekend"))
            
            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["geclassificeerd"] = True
        
        st.success("✅ Alle sonderingen geclassificeerd")
    
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
