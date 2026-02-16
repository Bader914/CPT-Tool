"""
Module 0: Uitgangspunten
- Verzamelt alle projectuitgangspunten op één plek
- Dijkopbouw, grondwaterstanden, materiaalparameters
- Nkt-factoren, conustype, referentieniveaus
- Dient als naslagwerk en input voor alle andere modules
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


# ============================================================
# STANDAARD UITGANGSPUNTEN (HHSK - Dijkversterking)
# ============================================================

DEFAULT_UITGANGSPUNTEN = {
    "project": {
        "naam": "HHSK Dijkversterking",
        "beschrijving": "Analyse sonderingen t.b.v. bepaling ongedraineerde schuifsterkte dijkmateriaal",
    },
    "dijkopbouw": {
        "kruinniveau": 4.0,          # NAP +4m
        "funderingslaag_dikte": 1.5,  # 1-2m, gemiddeld 1.5m
        "funderingslaag_materiaal": "Puin en zand",
        "gwl": 0.0,                  # NAP 0m (dagelijkse grondwaterstand)
        "dijkmateriaal_droog_top": None,  # Wordt berekend: kruin - funderingslaag
        "dijkmateriaal_droog_onder": 0.0,  # NAP 0m (= GWS)
        "dijkmateriaal_nat_top": 0.0,      # NAP 0m
        "dijkmateriaal_nat_onder": -3.0,   # NAP -3m
        "klei_veen_top": -3.0,             # NAP -3m
        "klei_veen_onder": -12.0,          # NAP -12m
        "pleistoceen_zand": -12.0,         # NAP -12m
    },
    "lagen": [
        {
            "naam": "Funderingslaag",
            "top_nap": 4.0,
            "onder_nap": 2.5,
            "materiaal": "Puin en zand",
            "kleur": "#A0A0A0",
            "is_dijkmateriaal": False,
            "gamma_droog": 19.0,
            "gamma_nat": 20.0,
            "beschrijving": "Wegfundering, 1 tot 2 meter dik, bestaande uit puin en zand onder de weg.",
        },
        {
            "naam": "Dijksmateriaal klei (droog)",
            "top_nap": 2.5,
            "onder_nap": 0.0,
            "materiaal": "Klei",
            "kleur": "#4CAF50",
            "is_dijkmateriaal": True,
            "gamma_droog": 17.0,
            "gamma_nat": 17.0,
            "beschrijving": "Kleiig dijksmateriaal boven de dagelijkse grondwaterstand. "
                           "Dit materiaal is niet verzadigd en heeft een lager volumegewicht.",
        },
        {
            "naam": "Dijksmateriaal klei (nat)",
            "top_nap": 0.0,
            "onder_nap": -3.0,
            "materiaal": "Klei",
            "kleur": "#2E7D32",
            "is_dijkmateriaal": True,
            "gamma_droog": 17.0,
            "gamma_nat": 18.0,
            "beschrijving": "Kleiig dijksmateriaal onder de dagelijkse grondwaterstand tot NAP -3m. "
                           "Dit is de primaire zone voor Su-bepaling.",
        },
        {
            "naam": "Klei/veen wissellagen",
            "top_nap": -3.0,
            "onder_nap": -12.0,
            "materiaal": "Klei en veen (afwisselend)",
            "kleur": "#8B4513",
            "is_dijkmateriaal": False,
            "gamma_droog": 14.0,
            "gamma_nat": 15.0,
            "beschrijving": "Afwisselend klei- en veenlagen tussen het dijksmateriaal en het Pleistocene zand. "
                           "Deze zone is relevant voor de ondergrond maar is geen dijksmateriaal.",
        },
        {
            "naam": "Pleistoceen zand",
            "top_nap": -12.0,
            "onder_nap": -20.0,
            "materiaal": "Zand",
            "kleur": "#FFD54F",
            "is_dijkmateriaal": False,
            "gamma_droog": 18.0,
            "gamma_nat": 20.0,
            "beschrijving": "Draagkrachtig Pleistoceen zand. Dit vormt de diepe fundering.",
        },
    ],
    "conustype": {
        "type": "Elektrische conus",
        "a_factor": 0.80,
        "beschrijving": "Nettoquotient conus (a). Standaard 0.80 voor gangbare elektrische conussen. "
                       "Waarde is afhankelijk van het conustype en moet worden gecontroleerd in het GEF-bestand.",
    },
    "nkt_factoren": {
        "klei_nc": {
            "naam": "Klei (normaal geconsolideerd)",
            "Nkt": 15,
            "range_min": 12,
            "range_max": 18,
            "bron": "Lunne et al. (1997), Robertson (2009)",
            "toelichting": "Voor normaal geconsolideerde klei in dijklichamen. "
                          "Nkt hangt af van plasticiteit en gevoeligheid van de klei.",
        },
        "klei_oc": {
            "naam": "Klei (overgeconsolideerd)",
            "Nkt": 17,
            "range_min": 15,
            "range_max": 20,
            "bron": "Lunne et al. (1997)",
            "toelichting": "Voor overgeconsolideerde klei, hogere Nkt door hogere stijfheid.",
        },
        "veen": {
            "naam": "Veen / organisch materiaal",
            "Nkt": 12,
            "range_min": 8,
            "range_max": 15,
            "bron": "Den Haan & Kruse (2007), Zwanenburg et al. (2012)",
            "toelichting": "Veen heeft een lagere Nkt vanwege het hoge vochtgehalte en lage sterkte. "
                          "Grote spreiding afhankelijk van veensoort (riet, bos, broekveen).",
        },
        "silt": {
            "naam": "Silt / kleiig silt",
            "Nkt": 14,
            "range_min": 10,
            "range_max": 18,
            "bron": "Lunne et al. (1997)",
            "toelichting": "Tussenwaarde voor silt en siltig klei mengsel.",
        },
    },
    "su_berekening": {
        "formule": "Su = q_net / Nkt",
        "q_net_definitie": "q_net = qt - σv0 (netto conusweerstand)",
        "qt_definitie": "qt = qc + (1 - a) × u2 (gecorrigeerde conusweerstand)",
        "toelichting": "De ongedraineerde schuifsterkte Su wordt berekend door de netto conusweerstand "
                      "q_net te delen door een empirische factor Nkt. De keuze van Nkt is cruciaal "
                      "en moet worden onderbouwd met laboratoriumproeven waar beschikbaar.",
    },
}


def maak_dijkprofiel_figuur(lagen: list) -> go.Figure:
    """Maak een schematisch dijkprofiel figuur."""
    fig = go.Figure()
    
    for laag in lagen:
        top = laag["top_nap"]
        onder = laag["onder_nap"]
        
        fig.add_trace(go.Bar(
            x=[laag["naam"]],
            y=[top - onder],
            base=[onder],
            name=laag["naam"],
            marker_color=laag["kleur"],
            text=f"{laag['materiaal']}<br>NAP {top:+.1f} tot {onder:+.1f}m",
            textposition="inside",
            hovertemplate=f"<b>{laag['naam']}</b><br>"
                         f"Top: NAP {top:+.1f}m<br>"
                         f"Onder: NAP {onder:+.1f}m<br>"
                         f"Dikte: {top-onder:.1f}m<br>"
                         f"Materiaal: {laag['materiaal']}<br>"
                         f"γ_nat: {laag['gamma_nat']} kN/m³<extra></extra>",
        ))
    
    fig.update_layout(
        title="Schematisch Dijkprofiel",
        yaxis=dict(title="Niveau [m NAP]", range=[-15, 6]),
        xaxis=dict(showticklabels=False),
        height=500,
        template="plotly_white",
        showlegend=False,
        barmode="stack",
    )
    
    # GWS lijn
    fig.add_hline(y=0, line_dash="dash", line_color="blue", 
                  annotation_text="GWS (NAP 0m)", annotation_position="top right")
    
    return fig


def render():
    st.title("📋 Uitgangspunten")
    st.markdown("""
    **Doel:** Alle projectuitgangspunten op één plek verzameld. Deze parameters worden 
    gebruikt als standaardwaarden in de andere modules. Pas aan indien nodig voor jouw situatie.
    """)
    
    # Initialiseer uitgangspunten in session state
    if "uitgangspunten" not in st.session_state:
        st.session_state.uitgangspunten = DEFAULT_UITGANGSPUNTEN.copy()
    
    up = st.session_state.uitgangspunten
    
    # === TABS ===
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏗️ Dijkopbouw", 
        "📐 Conustype & Correctie",
        "🔢 Nkt-factoren", 
        "📊 Formules & Methode",
        "📝 Samenvatting"
    ])
    
    # ─── TAB 1: DIJKOPBOUW ───
    with tab1:
        st.subheader("Globale Dijkopbouw")
        st.markdown("""
        **Waarom is dit belangrijk?**  
        De dijkopbouw bepaalt welke lagen we als dijkmateriaal beschouwen en waar we Su berekenen.
        De grondwaterstand bepaalt of de klei droog of verzadigd is, wat invloed heeft op het 
        volumegewicht en daarmee op de spanningsberekening.
        """)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Laagopbouw aanpassen:**")
            
            lagen = up.get("lagen", DEFAULT_UITGANGSPUNTEN["lagen"])
            
            for i, laag in enumerate(lagen):
                with st.expander(f"{'🟢' if laag['is_dijkmateriaal'] else '⚪'} {laag['naam']}", expanded=False):
                    st.markdown(f"*{laag['beschrijving']}*")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        lagen[i]["top_nap"] = st.number_input(
                            f"Top [m NAP]", value=laag["top_nap"], step=0.5,
                            key=f"top_{i}"
                        )
                        lagen[i]["gamma_droog"] = st.number_input(
                            f"γ droog [kN/m³]", value=laag["gamma_droog"], step=0.5,
                            key=f"gd_{i}"
                        )
                    with c2:
                        lagen[i]["onder_nap"] = st.number_input(
                            f"Onder [m NAP]", value=laag["onder_nap"], step=0.5,
                            key=f"onder_{i}"
                        )
                        lagen[i]["gamma_nat"] = st.number_input(
                            f"γ nat [kN/m³]", value=laag["gamma_nat"], step=0.5,
                            key=f"gn_{i}"
                        )
                    
                    lagen[i]["is_dijkmateriaal"] = st.checkbox(
                        "Is dijkmateriaal (Su berekenen)", 
                        value=laag["is_dijkmateriaal"],
                        key=f"dijkmat_{i}"
                    )
            
            up["lagen"] = lagen
            
            # Grondwaterstand
            st.markdown("---")
            gwl = st.number_input(
                "Dagelijkse grondwaterstand [m NAP]",
                value=up.get("dijkopbouw", {}).get("gwl", 0.0),
                step=0.1,
                help="De dagelijkse grondwaterstand bepaalt de waterspanning in de grond "
                     "en daarmee de effectieve spanning en de netto conusweerstand."
            )
            up["dijkopbouw"]["gwl"] = gwl
            
            kruinniveau = st.number_input(
                "Kruinniveau [m NAP]",
                value=up.get("dijkopbouw", {}).get("kruinniveau", 4.0),
                step=0.1,
                help="Bovenkant van de dijk (wegdek niveau)."
            )
            up["dijkopbouw"]["kruinniveau"] = kruinniveau
        
        with col2:
            st.markdown("**Schematisch profiel:**")
            fig = maak_dijkprofiel_figuur(lagen)
            st.plotly_chart(fig, use_container_width=True)
            
            # Legenda
            st.markdown("**Legenda:**")
            st.markdown("🟢 = Dijkmateriaal (Su wordt berekend)")
            st.markdown("⚪ = Geen dijkmateriaal")
            st.markdown("🔵 --- = Grondwaterstand")
    
    # ─── TAB 2: CONUSTYPE ───
    with tab2:
        st.subheader("Conustype & Poriedrukcorrectie")
        st.markdown("""
        **Waarom corrigeren we voor poriedruk?**  
        
        De gemeten conusweerstand $q_c$ is niet de werkelijke weerstand aan de conuspunt.
        Door de poriedruk ($u_2$) die werkt op het ongelijke oppervlak achter de conuspunt, 
        wordt een deel van de weerstand niet gemeten. De correctie hangt af van het conustype:
        
        $$q_t = q_c + (1 - a) \\cdot u_2$$
        
        Het **nettoquotient** $a$ is een eigenschap van de conus en varieert typisch tussen 0.70 en 0.85.
        
        **Controleer altijd** of de waarde van $a$ in het GEF-bestand staat en gebruik die waarde.
        """)
        
        conus = up.get("conustype", DEFAULT_UITGANGSPUNTEN["conustype"])
        
        col1, col2 = st.columns(2)
        with col1:
            conus["a_factor"] = st.slider(
                "Nettoquotient conus (a)",
                min_value=0.50, max_value=1.00, 
                value=conus.get("a_factor", 0.80), 
                step=0.01,
                help="a = 1.0 betekent geen correctie nodig. a < 1.0 betekent dat de poriedruk "
                     "een deel van de conusweerstand compenseert."
            )
            conus["type"] = st.text_input(
                "Conustype", 
                value=conus.get("type", "Elektrische conus"),
                help="Noteer het gebruikte conustype voor documentatie."
            )
        
        with col2:
            st.info(f"""
            **Huidige instelling:**  
            - Conustype: {conus['type']}  
            - a = {conus['a_factor']}  
            - Correctie: qt = qc + {1 - conus['a_factor']:.2f} × u2
            """)
            
            st.markdown("""
            **Typische waarden:**
            | Conustype | a-factor |
            |---|---|
            | Oude mechanische conus | 0.70 – 0.75 |
            | Standaard elektrisch | 0.75 – 0.85 |
            | Moderne conus | 0.80 – 0.85 |
            """)
        
        up["conustype"] = conus
    
    # ─── TAB 3: NKT-FACTOREN ───
    with tab3:
        st.subheader("Nkt-factoren per Grondtype")
        st.markdown("""
        **Waarom is Nkt belangrijk?**  
        
        De Nkt-factor is de sleutelparameter in de Su-berekening: $S_u = q_{net} / N_{kt}$
        
        Een **hogere Nkt** geeft een **lagere Su** (conservatiever voor sterkte).  
        Een **lagere Nkt** geeft een **hogere Su** (optimistischer).
        
        De juiste Nkt hangt af van:
        - **Grondtype** (klei, veen, silt)
        - **Plasticiteit** en **gevoeligheid** van de klei
        - **Lokale ervaring** en kalibratie met labproeven
        
        **Aanbeveling:** Start met literatuurwaarden en kalibreer met beschikbare 
        laboratoriumproeven (triaxiaal, DSS).
        """)
        
        nkt = up.get("nkt_factoren", DEFAULT_UITGANGSPUNTEN["nkt_factoren"])
        
        for key, nkt_info in nkt.items():
            with st.expander(f"📌 {nkt_info['naam']} — Nkt = {nkt_info['Nkt']}", expanded=False):
                st.markdown(f"*{nkt_info['toelichting']}*")
                st.caption(f"Bron: {nkt_info['bron']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    nkt_info["Nkt"] = st.number_input(
                        "Nkt waarde", 
                        value=float(nkt_info["Nkt"]),
                        min_value=5.0, max_value=30.0, step=0.5,
                        key=f"nkt_{key}"
                    )
                with col2:
                    nkt_info["range_min"] = st.number_input(
                        "Range min", value=float(nkt_info["range_min"]),
                        min_value=5.0, max_value=25.0, step=0.5,
                        key=f"nkt_min_{key}"
                    )
                with col3:
                    nkt_info["range_max"] = st.number_input(
                        "Range max", value=float(nkt_info["range_max"]),
                        min_value=5.0, max_value=30.0, step=0.5,
                        key=f"nkt_max_{key}"
                    )
        
        up["nkt_factoren"] = nkt
        
        # Visueel overzicht
        st.markdown("---")
        st.markdown("**Overzicht Nkt-waarden:**")
        
        nkt_overview = []
        for key, info in nkt.items():
            nkt_overview.append({
                "Grondtype": info["naam"],
                "Nkt": info["Nkt"],
                "Range": f"{info['range_min']} – {info['range_max']}",
                "Bron": info["bron"],
            })
        st.dataframe(pd.DataFrame(nkt_overview), use_container_width=True, hide_index=True)
    
    # ─── TAB 4: FORMULES & METHODE ───
    with tab4:
        st.subheader("Berekeningsformules & Methode")
        st.markdown("""
        ### Stap 1: Poriedrukcorrectie
        De gemeten conusweerstand wordt gecorrigeerd voor het effect van poriedruk:
        
        $$q_t = q_c + (1 - a) \\cdot u_2$$
        
        **Waarom?** De poriedruk werkt op het verschiloppervlak achter de conuspunt, 
        waardoor de gemeten $q_c$ lager is dan de werkelijke weerstand.
        
        ---
        
        ### Stap 2: Spanningsberekening
        De totale en effectieve verticale spanning worden berekend:
        
        $$\\sigma_{v0} = \\sum \\gamma_i \\cdot \\Delta z_i$$
        
        $$u_0 = \\gamma_w \\cdot (z - z_{gwl})$$  (alleen onder grondwaterstand)
        
        $$\\sigma'_{v0} = \\sigma_{v0} - u_0$$
        
        **Waarom?** De netto conusweerstand moet worden berekend t.o.v. de in-situ spanning.
        
        ---
        
        ### Stap 3: Netto conusweerstand
        
        $$q_{net} = q_t - \\sigma_{v0}$$
        
        **Waarom?** Om de conusweerstand te normaliseren voor diepte-effecten, zodat 
        sonderingen op verschillende dieptes vergelijkbaar zijn.
        
        ---
        
        ### Stap 4: Classificatie (Robertson 1990)
        Op basis van $Q_t$ en $R_f$ wordt de grondsoort geclassificeerd:
        
        $$Q_t = \\frac{q_t - \\sigma_{v0}}{\\sigma'_{v0}}$$
        
        $$R_f = \\frac{f_s}{q_c} \\times 100\\%$$
        
        **Waarom?** Om te bepalen welke lagen klei (dijkmateriaal) zijn en welke niet.
        
        ---
        
        ### Stap 5: Ongedraineerde schuifsterkte
        
        $$S_u = \\frac{q_{net}}{N_{kt}}$$
        
        **Waarom?** Su is de sterkteparameter die nodig is voor stabiliteitsberekeningen 
        van de dijk. De Nkt-factor is empirisch en moet worden gevalideerd met labproeven.
        
        ---
        
        ### Stap 6: Validatie
        De berekende Su wordt vergeleken met:
        - **Deltares CPT-tool** resultaten (onafhankelijke controle)
        - **Laboratoriumproeven** (triaxiaal, DSS) als ground truth
        
        **Waarom?** Om de gekozen Nkt te kalibreren en de betrouwbaarheid van de 
        CPT-interpretatie te beoordelen.
        """)
    
    # ─── TAB 5: SAMENVATTING ───
    with tab5:
        st.subheader("Samenvatting Uitgangspunten")
        st.markdown("**Alle gehanteerde uitgangspunten op een rij:**")
        
        # Project
        st.markdown("#### 🏢 Project")
        st.markdown(f"- **Naam:** {up['project']['naam']}")
        st.markdown(f"- **Beschrijving:** {up['project']['beschrijving']}")
        
        # Dijkopbouw
        st.markdown("#### 🏗️ Dijkopbouw")
        st.markdown(f"- **Kruinniveau:** NAP {up['dijkopbouw']['kruinniveau']:+.1f}m")
        st.markdown(f"- **Grondwaterstand:** NAP {up['dijkopbouw']['gwl']:+.1f}m")
        
        for laag in up["lagen"]:
            dijkmat = "✅ dijkmateriaal" if laag["is_dijkmateriaal"] else "—"
            st.markdown(
                f"- **{laag['naam']}:** NAP {laag['top_nap']:+.1f}m tot {laag['onder_nap']:+.1f}m "
                f"| γ_nat = {laag['gamma_nat']} kN/m³ | {dijkmat}"
            )
        
        # Conustype
        st.markdown("#### 📐 Conustype")
        st.markdown(f"- **Type:** {up['conustype']['type']}")
        st.markdown(f"- **a-factor:** {up['conustype']['a_factor']}")
        
        # Nkt
        st.markdown("#### 🔢 Nkt-factoren")
        for key, info in up["nkt_factoren"].items():
            st.markdown(f"- **{info['naam']}:** Nkt = {info['Nkt']} (range {info['range_min']} – {info['range_max']})")
        
        st.markdown("---")
        st.caption("Deze uitgangspunten worden automatisch gebruikt in alle modules. "
                   "Wijzigingen worden direct doorgevoerd.")
    
    # Sla op in session state
    st.session_state.uitgangspunten = up
