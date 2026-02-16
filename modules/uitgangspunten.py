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
        "gwl": 0.0,                  # NAP 0m (gemiddeld t.t.v. sonderen)
        "gwl_max": 1.0,              # NAP +1m (hoogste GWS t.t.v. sonderen)
        "gwl_min": -0.5,             # NAP -0.5m (laagste GWS t.t.v. sonderen)
        "gwl_toelichting": "Grondwaterstand varieert tussen NAP +1m en NAP -0,5m "
                          "ten tijde van sonderen. Uitgezocht a.h.v. notitie Arnold.",
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
            "naam": "0_Funderingslaag",
            "top_nap": 4.0,
            "onder_nap": 2.5,
            "materiaal": "Puin en zand",
            "kleur": "#A0A0A0",
            "is_dijkmateriaal": False,
            "gamma_droog": 21.00,
            "gamma_nat": 19.00,
            "phi": 34.0,
            "S_ratio": None,
            "m_factor": None,
            "Nkt": None,
            "beschrijving": "Wegfundering, 1 tot 2 meter dik, bestaande uit puin en zand onder de weg.",
        },
        {
            "naam": "1_Veen",
            "top_nap": None,  # Variabel per locatie
            "onder_nap": None,
            "materiaal": "Veen",
            "kleur": "#5D4037",
            "is_dijkmateriaal": False,
            "gamma_droog": 10.11,
            "gamma_nat": 10.11,
            "phi": 37.6,
            "S_ratio": 0.44,
            "m_factor": 0.80,
            "Nkt": 17.1,
            "aantal_proeven": 46,
            "beschrijving": "Veenlaag. S-ratio en m-factor bepaald uit 46 proeven.",
        },
        {
            "naam": "2_Veen_kleiig",
            "top_nap": None,
            "onder_nap": None,
            "materiaal": "Kleiig veen",
            "kleur": "#6D4C41",
            "is_dijkmateriaal": False,
            "gamma_droog": 11.47,
            "gamma_nat": 11.47,
            "phi": 35.7,
            "S_ratio": 0.41,
            "m_factor": 0.66,
            "Nkt": 16.7,
            "aantal_proeven": 22,
            "beschrijving": "Kleiig veen. S-ratio en m-factor bepaald uit 22 proeven.",
        },
        {
            "naam": "3_Basisveen",
            "top_nap": None,
            "onder_nap": None,
            "materiaal": "Basisveen",
            "kleur": "#4E342E",
            "is_dijkmateriaal": False,
            "gamma_droog": 12.00,
            "gamma_nat": 12.00,
            "phi": None,
            "S_ratio": None,
            "m_factor": None,
            "Nkt": 20.0,
            "beschrijving": "Basisveen. Nkt is default waarde uit schematiseringshandleiding.",
        },
        {
            "naam": "4_Klei_humeus",
            "top_nap": None,
            "onder_nap": None,
            "materiaal": "Humeuze klei",
            "kleur": "#795548",
            "is_dijkmateriaal": False,
            "gamma_droog": 13.42,
            "gamma_nat": 13.42,
            "phi": 45.4,
            "S_ratio": 0.33,
            "m_factor": 0.84,
            "Nkt": 16.8,
            "aantal_proeven": 23,
            "beschrijving": "Humeuze klei. S-ratio en m-factor bepaald uit 23 proeven.",
        },
        {
            "naam": "5_Klei_siltig",
            "top_nap": None,
            "onder_nap": None,
            "materiaal": "Siltige klei",
            "kleur": "#8D6E63",
            "is_dijkmateriaal": False,
            "gamma_droog": 16.73,
            "gamma_nat": 16.73,
            "phi": 37.8,
            "S_ratio": 0.32,
            "m_factor": 1.00,
            "Nkt": 18.2,
            "aantal_proeven": 35,
            "beschrijving": "Siltige klei. S-ratio en m-factor bepaald uit 35 proeven.",
        },
        {
            "naam": "6_Klei_zandig",
            "top_nap": None,
            "onder_nap": None,
            "materiaal": "Zandige klei",
            "kleur": "#A1887F",
            "is_dijkmateriaal": False,
            "gamma_droog": 17.90,
            "gamma_nat": 17.90,
            "phi": 30.0,
            "S_ratio": 0.28,
            "m_factor": 0.80,
            "Nkt": 20.0,
            "beschrijving": "Zandige klei. Nkt is default waarde uit schematiseringshandleiding.",
        },
        {
            "naam": "7a_Dijksmateriaal klei > gws",
            "top_nap": 2.5,
            "onder_nap": 0.0,
            "materiaal": "Klei (boven GWS)",
            "kleur": "#4CAF50",
            "is_dijkmateriaal": True,
            "gamma_droog": 18.81,
            "gamma_nat": 18.81,
            "phi": 32.9,
            "S_ratio": 0.41,
            "m_factor": 0.88,
            "Nkt": 14.5,
            "aantal_proeven": 28,
            "beschrijving": "Kleiig dijksmateriaal boven de dagelijkse grondwaterstand. "
                           "S-ratio en m-factor bepaald uit 28 proeven.",
        },
        {
            "naam": "7b_Dijksmateriaal klei < gws",
            "top_nap": 0.0,
            "onder_nap": -3.0,
            "materiaal": "Klei (onder GWS)",
            "kleur": "#2E7D32",
            "is_dijkmateriaal": True,
            "gamma_droog": 17.93,
            "gamma_nat": 17.93,
            "phi": 33.4,
            "S_ratio": 0.35,
            "m_factor": 0.79,
            "Nkt": 14.1,
            "aantal_proeven": 40,
            "beschrijving": "Kleiig dijksmateriaal onder de dagelijkse grondwaterstand tot NAP -3m. "
                           "Dit is de primaire zone voor Su-bepaling. "
                           "S-ratio en m-factor bepaald uit 40 proeven.",
        },
        {
            "naam": "7b_Dijksmateriaal zand",
            "top_nap": None,
            "onder_nap": None,
            "materiaal": "Zand (in dijk)",
            "kleur": "#FFC107",
            "is_dijkmateriaal": False,
            "gamma_droog": 18.70,
            "gamma_nat": 17.00,
            "phi": 32.0,
            "S_ratio": None,
            "m_factor": None,
            "Nkt": None,
            "beschrijving": "Zandig dijksmateriaal. Geen Su-berekening (gedraineerd materiaal).",
        },
        {
            "naam": "8_Klei_diep",
            "top_nap": None,
            "onder_nap": None,
            "materiaal": "Diepe klei",
            "kleur": "#1B5E20",
            "is_dijkmateriaal": False,
            "gamma_droog": 19.00,
            "gamma_nat": 19.00,
            "phi": 30.0,
            "S_ratio": 0.38,
            "m_factor": 0.80,
            "Nkt": 20.0,
            "beschrijving": "Diepe kleilaag. Nkt is default waarde uit schematiseringshandleiding.",
        },
        {
            "naam": "9_Zand",
            "top_nap": -12.0,
            "onder_nap": -20.0,
            "materiaal": "Pleistoceen zand",
            "kleur": "#FFD54F",
            "is_dijkmateriaal": False,
            "gamma_droog": 19.00,
            "gamma_nat": 18.00,
            "phi": 32.5,
            "S_ratio": None,
            "m_factor": None,
            "Nkt": None,
            "beschrijving": "Draagkrachtig Pleistoceen zand. Geen Su-berekening (gedraineerd).",
        },
    ],
    "conustype": {
        "type": "Elektrische conus",
        "a_factor": 0.80,
        "beschrijving": "Nettoquotient conus (a). Standaard 0.80 voor gangbare elektrische conussen. "
                       "Waarde is afhankelijk van het conustype en moet worden gecontroleerd in het GEF-bestand.",
    },
    "nkt_factoren": {
        "bron": "Tabel 71 — NKT factoren traject 14-1",
        "toelichting": "Nkt-waarden zijn per grondlaag bepaald. Lagen met * zijn default waarden "
                      "uit de schematiseringshandleiding (onvoldoende proeven beschikbaar).",
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
    """Maak een schematisch dijkprofiel figuur (alleen lagen met bekende top/onder)."""
    fig = go.Figure()
    
    for laag in lagen:
        top = laag.get("top_nap")
        onder = laag.get("onder_nap")
        
        # Sla lagen over zonder gedefinieerde positie
        if top is None or onder is None:
            continue
        
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
    st.markdown("""
    <div class="hero-container">
        <h1>📋 Uitgangspunten</h1>
        <p>Alle projectparameters op één plek — dijkopbouw, sterkteparameters, Nkt-factoren</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialiseer uitgangspunten in session state
    if "uitgangspunten" not in st.session_state:
        st.session_state.uitgangspunten = DEFAULT_UITGANGSPUNTEN.copy()
    
    up = st.session_state.uitgangspunten
    
    # === TABS ===
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏗️ Dijkopbouw", 
        "💪 Sterkteparameters (Tabel 91)",
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
                        top_val = laag.get("top_nap")
                        if top_val is not None:
                            lagen[i]["top_nap"] = st.number_input(
                                f"Top [m NAP]", value=float(top_val), step=0.5,
                                key=f"top_{i}"
                            )
                        else:
                            st.caption("Top: variabel per locatie")
                        
                        lagen[i]["gamma_droog"] = st.number_input(
                            f"γ droog [kN/m³]", value=float(laag["gamma_droog"]), step=0.5,
                            key=f"gd_{i}"
                        )
                    with c2:
                        onder_val = laag.get("onder_nap")
                        if onder_val is not None:
                            lagen[i]["onder_nap"] = st.number_input(
                                f"Onder [m NAP]", value=float(onder_val), step=0.5,
                                key=f"onder_{i}"
                            )
                        else:
                            st.caption("Onder: variabel per locatie")
                        
                        lagen[i]["gamma_nat"] = st.number_input(
                            f"γ nat [kN/m³]", value=float(laag["gamma_nat"]), step=0.5,
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
            st.markdown("""  
            **Grondwaterstand ten tijde van sonderen**  
            De GWS varieert tussen **NAP +1,0m** en **NAP -0,5m** ten tijde van 
            sonderen (bron: notitie Arnold). Dit is relevant voor de poriedrukcorrectie 
            en de effectieve spanningsberekening.
            """)
            
            c_gwl1, c_gwl2, c_gwl3 = st.columns(3)
            with c_gwl1:
                gwl = st.number_input(
                    "GWS [m NAP] (gebruikt)",
                    value=up.get("dijkopbouw", {}).get("gwl", 0.0),
                    step=0.1,
                    help="Grondwaterstand die wordt gebruikt voor de berekening. "
                         "Kies een waarde binnen de bandbreedte."
                )
                up["dijkopbouw"]["gwl"] = gwl
            with c_gwl2:
                gwl_max = st.number_input(
                    "GWS max [m NAP]",
                    value=up.get("dijkopbouw", {}).get("gwl_max", 1.0),
                    step=0.1,
                    help="Hoogste grondwaterstand ten tijde van sonderen."
                )
                up["dijkopbouw"]["gwl_max"] = gwl_max
            with c_gwl3:
                gwl_min = st.number_input(
                    "GWS min [m NAP]",
                    value=up.get("dijkopbouw", {}).get("gwl_min", -0.5),
                    step=0.1,
                    help="Laagste grondwaterstand ten tijde van sonderen."
                )
                up["dijkopbouw"]["gwl_min"] = gwl_min
            
            st.markdown("---")
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
    
    # ─── TAB 2: STERKTEPARAMETERS (TABEL 91) ───
    with tab2:
        st.subheader("Sterkteparameters per Grondlaag — Tabel 91")
        st.markdown("""
        **Samenvatting sterkteparameters traject 14-1**
        
        Deze tabel bevat de volumegewichten, hoek van interne wrijving en SHANSEP-parameters 
        per grondlaag. De SHANSEP-methode relateert de ongedraineerde schuifsterkte aan de 
        effectieve spanning en overconsolidatiegraad:
        
        $$S_u = S \\cdot \\sigma'_{v0} \\cdot OCR^m$$
        
        Waarbij:
        - **S** = S-ratio (Su/σ'v0 bij normaal geconsolideerde toestand)
        - **m** = exponent die de invloed van overconsolidatie beschrijft
        - **OCR** = overconsolidatiegraad
        
        **Let op:** Lagen gemarkeerd met * zijn aannames (onvoldoende proeven beschikbaar).  
        Lagen gemarkeerd met ** hebben geen S en m (gedraineerd materiaal, geen Su-berekening).
        """)
        
        # Maak Tabel 91 dataframe
        lagen = up.get("lagen", DEFAULT_UITGANGSPUNTEN["lagen"])
        
        tabel_data = []
        for laag in lagen:
            row = {
                "Grondlaag": laag["naam"],
                "Aantal proeven": laag.get("aantal_proeven", "—"),
                "γ_droog [kN/m³]": laag["gamma_droog"],
                "γ_nat [kN/m³]": laag["gamma_nat"],
                "φ [°]": laag.get("phi", "—") if laag.get("phi") is not None else "—",
                "S [-]": laag.get("S_ratio", "—") if laag.get("S_ratio") is not None else "—",
                "m [-]": laag.get("m_factor", "—") if laag.get("m_factor") is not None else "—",
                "Nkt [-]": laag.get("Nkt", "—") if laag.get("Nkt") is not None else "—",
            }
            tabel_data.append(row)
        
        tabel_df = pd.DataFrame(tabel_data)
        
        st.dataframe(
            tabel_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Grondlaag": st.column_config.TextColumn("Grondlaag", width="large"),
                "Aantal proeven": st.column_config.TextColumn("Aantal", width="small"),
                "γ_droog [kN/m³]": st.column_config.NumberColumn("γ_droog [kN/m³]", format="%.2f"),
                "γ_nat [kN/m³]": st.column_config.NumberColumn("γ_nat [kN/m³]", format="%.2f"),
                "φ [°]": st.column_config.TextColumn("φ [°]", width="small"),
                "S [-]": st.column_config.TextColumn("S [-]", width="small"),
                "m [-]": st.column_config.TextColumn("m [-]", width="small"),
            }
        )
        
        st.markdown("---")
        
        # Visueel overzicht van S-ratio en m-factor
        st.markdown("**Visueel overzicht SHANSEP-parameters:**")
        
        shansep_lagen = [l for l in lagen if l.get("S_ratio") is not None]
        
        if shansep_lagen:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_s = go.Figure()
                namen = [l["naam"] for l in shansep_lagen]
                s_vals = [l["S_ratio"] for l in shansep_lagen]
                kleuren = [l["kleur"] for l in shansep_lagen]
                
                fig_s.add_trace(go.Bar(
                    x=namen, y=s_vals,
                    marker_color=kleuren,
                    text=[f"{s:.2f}" for s in s_vals],
                    textposition="outside",
                ))
                fig_s.update_layout(
                    title="S-ratio per grondlaag",
                    yaxis=dict(title="S [-]", range=[0, 0.6]),
                    xaxis=dict(tickangle=45),
                    height=400,
                    template="plotly_white",
                )
                st.plotly_chart(fig_s, use_container_width=True)
            
            with col2:
                fig_m = go.Figure()
                m_vals = [l["m_factor"] for l in shansep_lagen]
                
                fig_m.add_trace(go.Bar(
                    x=namen, y=m_vals,
                    marker_color=kleuren,
                    text=[f"{m:.2f}" for m in m_vals],
                    textposition="outside",
                ))
                fig_m.update_layout(
                    title="m-exponent per grondlaag",
                    yaxis=dict(title="m [-]", range=[0, 1.2]),
                    xaxis=dict(tickangle=45),
                    height=400,
                    template="plotly_white",
                )
                st.plotly_chart(fig_m, use_container_width=True)
        
        st.markdown("""
        **Toelichting SHANSEP-parameters:**
        - Een **hogere S-ratio** betekent een hogere sterkte bij gelijke effectieve spanning
        - Een **hogere m** betekent dat de sterkte sterker toeneemt bij overconsolidatie
        - **Veen** (S=0.44) heeft de hoogste S-ratio maar laagste volumegewicht
        - **Klei zandig** (S=0.28) heeft de laagste S-ratio
        - **Klei siltig** (m=1.00) heeft de sterkste OCR-afhankelijkheid
        """)
    
    # ─── TAB 2: CONUSTYPE ───
    with tab3:
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
    
    # ─── TAB 3: NKT-FACTOREN PER GRONDLAAG (TABEL 71) ───
    with tab4:
        st.subheader("Nkt-factoren per Grondlaag — Tabel 71")
        st.markdown("""
        <div class="section-header">
            <h3>Waarom is Nkt belangrijk?</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        De Nkt-factor is de sleutelparameter in de Su-berekening: $S_u = q_{net} / N_{kt}$
        
        - Een **hogere Nkt** geeft een **lagere Su** (conservatiever)  
        - Een **lagere Nkt** geeft een **hogere Su** (optimistischer)
        
        De Nkt-waarden zijn **per grondlaag** bepaald op basis van het project (Tabel 71).  
        Lagen met \\* gebruiken default waarden uit de schematiseringshandleiding.
        """)
        
        lagen = up.get("lagen", DEFAULT_UITGANGSPUNTEN["lagen"])
        
        # Nkt overzichtstabel
        nkt_data = []
        for laag in lagen:
            nkt_val = laag.get("Nkt")
            if nkt_val is not None:
                is_default = "default*" if laag["naam"] in ["3_Basisveen", "6_Klei_zandig", "8_Klei_diep"] else ""
                nkt_data.append({
                    "Grondlaag": laag["naam"],
                    "Nkt [-]": nkt_val,
                    "Type": is_default if is_default else "bepaald",
                })
        
        if nkt_data:
            nkt_df = pd.DataFrame(nkt_data)
            st.dataframe(nkt_df, use_container_width=True, hide_index=True)
        
        # Aanpasbare Nkt per laag
        st.markdown("---")
        st.markdown("**Nkt-waarden aanpassen:**")
        
        cols = st.columns(3)
        for i, laag in enumerate(lagen):
            if laag.get("Nkt") is not None:
                with cols[i % 3]:
                    lagen[i]["Nkt"] = st.number_input(
                        f"{laag['naam']}",
                        value=float(laag["Nkt"]),
                        min_value=5.0, max_value=30.0, step=0.1,
                        key=f"nkt_laag_{i}",
                    )
        
        up["lagen"] = lagen
        
        # Visueel overzicht
        st.markdown("---")
        nkt_lagen = [l for l in lagen if l.get("Nkt") is not None]
        
        if nkt_lagen:
            fig_nkt = go.Figure()
            namen = [l["naam"].replace("_", " ") for l in nkt_lagen]
            nkt_vals = [l["Nkt"] for l in nkt_lagen]
            kleuren = [l["kleur"] for l in nkt_lagen]
            
            fig_nkt.add_trace(go.Bar(
                x=namen, y=nkt_vals,
                marker_color=kleuren,
                text=[f"{v:.1f}" for v in nkt_vals],
                textposition="outside",
                textfont=dict(size=13, color="#0f172a"),
            ))
            fig_nkt.update_layout(
                title="Nkt per grondlaag (Tabel 71)",
                yaxis=dict(title="Nkt [-]", range=[0, max(nkt_vals) * 1.2]),
                xaxis=dict(tickangle=45),
                height=450,
                template="plotly_white",
                margin=dict(b=120),
            )
            st.plotly_chart(fig_nkt, use_container_width=True)
    
    # ─── TAB 4: FORMULES & METHODE ───
    with tab5:
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
        - **Laboratoriumproeven** (triaxiaal, DSS) als ground truth
        
        **Waarom?** Om de gekozen Nkt te kalibreren en de betrouwbaarheid van de 
        CPT-interpretatie te beoordelen.
        """)
    
    # ─── TAB 5: SAMENVATTING ───
    with tab6:
        st.subheader("Samenvatting Uitgangspunten")
        st.markdown("**Alle gehanteerde uitgangspunten op een rij:**")
        
        # Project
        st.markdown("#### 🏢 Project")
        st.markdown(f"- **Naam:** {up['project']['naam']}")
        st.markdown(f"- **Beschrijving:** {up['project']['beschrijving']}")
        
        # Dijkopbouw
        st.markdown("#### 🏗️ Dijkopbouw")
        st.markdown(f"- **Kruinniveau:** NAP {up['dijkopbouw']['kruinniveau']:+.1f}m")
        gwl_val = up['dijkopbouw']['gwl']
        gwl_max_val = up['dijkopbouw'].get('gwl_max', 1.0)
        gwl_min_val = up['dijkopbouw'].get('gwl_min', -0.5)
        st.markdown(f"- **Grondwaterstand (gebruikt):** NAP {gwl_val:+.1f}m")
        st.markdown(f"- **GWS range t.t.v. sonderen:** NAP {gwl_min_val:+.1f}m tot NAP {gwl_max_val:+.1f}m")
        
        for laag in up["lagen"]:
            dijkmat = "✅ dijkmateriaal" if laag["is_dijkmateriaal"] else "—"
            top = laag.get("top_nap")
            onder = laag.get("onder_nap")
            positie = f"NAP {top:+.1f}m tot {onder:+.1f}m" if top is not None and onder is not None else "variabel"
            s_info = f" | S={laag['S_ratio']}, m={laag['m_factor']}" if laag.get("S_ratio") is not None else ""
            st.markdown(
                f"- **{laag['naam']}:** {positie} "
                f"| γ_nat = {laag['gamma_nat']} kN/m³{s_info} | {dijkmat}"
            )
        
        # Conustype
        st.markdown("#### 📐 Conustype")
        st.markdown(f"- **Type:** {up['conustype']['type']}")
        st.markdown(f"- **a-factor:** {up['conustype']['a_factor']}")
        
        # Nkt
        st.markdown("#### 🔢 Nkt-factoren (Tabel 71)")
        for laag in up["lagen"]:
            nkt_val = laag.get("Nkt")
            if nkt_val is not None:
                st.markdown(f"- **{laag['naam']}:** Nkt = {nkt_val}")
        
        st.markdown("---")
        st.caption("Deze uitgangspunten worden automatisch gebruikt in alle modules. "
                   "Wijzigingen worden direct doorgevoerd.")
    
    # Sla op in session state
    st.session_state.uitgangspunten = up
