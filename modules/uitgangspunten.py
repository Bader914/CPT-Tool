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
            "Nkt": 17.1, "VC_su": 0.25,
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
            "Nkt": 16.7, "VC_su": 0.25,
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
            "Nkt": 20.0, "VC_su": 0.25,
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
            "Nkt": 16.8, "VC_su": 0.25,
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
            "Nkt": 18.2, "VC_su": 0.25,
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
            "Nkt": 20.0, "VC_su": 0.25,
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
            "Nkt": 14.5, "VC_su": 0.25,
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
            "Nkt": 14.1, "VC_su": 0.25,
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
            "Nkt": 20.0, "VC_su": 0.25,
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
    "waterdruk": {
        "knik_nap": -5.0,
        "stijghoogte_nap": -2.0,
        "top_zand_nap": -12.0,
        "indringing": 0.0,
        "gamma_w": 9.81,
        "toelichting": "u0-verloop met 4 zones (zie 'waterdrukverloop berekening.xlsx'). "
                       "Boven GWS: 0. GWS->knikpunt: hydrostatisch vanaf GWS. "
                       "Knikpunt->(top zand + indringing): lineaire overgang. "
                       "Onder dat niveau: hydrostatisch vanaf de stijghoogte van het zandpakket.",
    },
    "nkt_factoren": {
        "bron": "Tabel 71 — NKT factoren traject 14-1",
        "toelichting": "Nkt-waarden zijn per grondlaag bepaald. Lagen met * zijn default waarden "
                      "uit de schematiseringshandleiding (onvoldoende proeven beschikbaar).",
    },
    # Karakteristieke waarde: Su_kar = Su_gem·(1 − t·VC). Dit zijn UITGANGSPUNTEN,
    # geen rekenknoppen — daarom hier en niet pas bij de Su-berekening.
    "karakteristiek": {
        # 'materiaal' = VC per grondsoort uit de materialentabel (VC_su). Aanbevolen:
        # de VC hoort een bewuste keuze te zijn over de onzekerheid in de grondsterkte.
        # 'data' = VC uit de spreiding van de Su-punten. Dat meet vooral de punt-op-punt-
        # ruis van de conus (meting per 2 cm) en geeft onrealistisch hoge VC (→ Su_kar = 0).
        "vc_bron": "materiaal",
        "t_factor": 1.645,   # 5%-ondergrens (eenzijdig 95%)
        "toelichting": "Su_kar = Su_gem·(1 − t·VC). VC per materiaal is leidend; de VC uit de "
                       "data wordt als controlegetal getoond (wijkt die sterk af, dan is de "
                       "laagindeling waarschijnlijk te grof).",
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


def bouw_lagen_uit_grondopbouw(rows: list, bibliotheek: list, onderkant_diepste_nap: float,
                               maaiveld_nap: float | None = None) -> list:
    """Zet de grondopbouw-invoertabel om naar een volwaardige `lagen`-lijst.

    Elke rij geeft de BOVENKANT (m NAP) van een laag + een gekozen laagtype uit
    de bibliotheek + (optioneel overschreven) γ_droog, γ_nat, Nkt, dijkmateriaal.

    - De ONDERKANT van een laag = de bovenkant van de volgende (gesorteerd, aflopend).
      De diepste laag loopt door tot `onderkant_diepste_nap`.
    - De BOVENSTE laag loopt door tot `maaiveld_nap` (indien opgegeven), zodat de
      grondkolom vanaf maaiveld volledig gedefinieerd is. Dat is nodig voor een
      correcte σv0: de grond bóven het eerste meetpunt (bv. de voorboorzone)
      weegt wél mee. Zonder maaiveld blijft die zone 'Onbekend'.
    - Bij herhaald laagtype worden unieke namen gemaakt (… #2, #3) zodat de
      naam-gekoppelde rekenketen (laaggrenzen, σv0, Nkt) blijft werken.
    - Overige parameters (S, m, φ, kleur, materiaal) worden uit de bibliotheek
      overgenomen, zodat Tabel 91 en SHANSEP intact blijven.
    """
    biblio = {l["naam"]: l for l in bibliotheek}

    def _geldig(r):
        bk, lt = r.get("bovenkant"), r.get("laagtype")
        return pd.notna(bk) and pd.notna(lt) and str(lt).strip() != ""

    geldig = [r for r in rows if _geldig(r)]
    # Sorteer aflopend op bovenkant (van boven naar beneden).
    geldig.sort(key=lambda r: -float(r["bovenkant"]))

    lagen = []
    seen: dict[str, int] = {}
    for idx, r in enumerate(geldig):
        top = float(r["bovenkant"])
        onder = (float(geldig[idx + 1]["bovenkant"])
                 if idx + 1 < len(geldig) else float(onderkant_diepste_nap))

        type_naam = r["laagtype"]
        basis = dict(biblio.get(type_naam, {}))

        seen[type_naam] = seen.get(type_naam, 0) + 1
        naam = type_naam if seen[type_naam] == 1 else f"{type_naam} #{seen[type_naam]}"

        laag = dict(basis)  # neem S_ratio, m_factor, phi, kleur, materiaal mee
        laag["naam"] = naam
        laag["top_nap"] = top
        laag["onder_nap"] = onder

        gd = r.get("gamma_droog")
        gn = r.get("gamma_nat")
        laag["gamma_droog"] = float(gd) if gd not in (None, "") else basis.get("gamma_droog", 18.0)
        laag["gamma_nat"] = float(gn) if gn not in (None, "") else basis.get("gamma_nat", 18.0)

        nkt = r.get("Nkt")
        laag["Nkt"] = float(nkt) if nkt not in (None, "", 0, 0.0) else basis.get("Nkt")

        # is_dijkmateriaal: gebruik de rijwaarde als die er is, anders de bibliotheek.
        # Zo werkt ook een minimale per-sondering rij (alleen bovenkant + laagtype).
        laag["is_dijkmateriaal"] = bool(r.get("is_dijkmateriaal", basis.get("is_dijkmateriaal", False)))
        laag.setdefault("kleur", "#888888")
        laag.setdefault("materiaal", type_naam)
        lagen.append(laag)

    # Bovenste laag doortrekken tot maaiveld: de grond boven het eerste meetpunt
    # (voorboorzone) telt mee in σv0 met de γ van die bovenste laag.
    if lagen and maaiveld_nap is not None:
        lagen[0]["top_nap"] = max(float(lagen[0]["top_nap"]), float(maaiveld_nap))

    return lagen


def get_lagen_bibliotheek(up: dict) -> list:
    """Geef de stabiele laag-bibliotheek (catalogus van laagtypes met parameters).

    Wordt één keer gesnapshot uit de huidige lagen (of de defaults) en daarna NIET
    meer overschreven door 'Grondopbouw toepassen', zodat dropdowns altijd alle
    laagtypes blijven tonen. Gedeeld door de Grondopbouw-tab en de per-sondering
    interpretatie in Classificatie.
    """
    if "lagen_bibliotheek" not in up:
        up["lagen_bibliotheek"] = [dict(l) for l in up.get("lagen", DEFAULT_UITGANGSPUNTEN["lagen"])]
    return up["lagen_bibliotheek"]


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
    st.caption("Stap 0 — Alle projectparameters op één plek")
    
    # Initialiseer uitgangspunten in session state
    if "uitgangspunten" not in st.session_state:
        st.session_state.uitgangspunten = DEFAULT_UITGANGSPUNTEN.copy()
    
    up = st.session_state.uitgangspunten
    
    # Migratie: voeg waterdruk-defaults toe als ze ontbreken (oude sessies)
    if "waterdruk" not in up:
        up["waterdruk"] = DEFAULT_UITGANGSPUNTEN["waterdruk"].copy()
    else:
        # Migreer oude sleutels (3-zone-model) naar het nieuwe 4-zone-model.
        _w = up["waterdruk"]
        if "knik_nap" not in _w:
            _w["knik_nap"] = -5.0
        if "stijghoogte_nap" not in _w:
            _w["stijghoogte_nap"] = -2.0
        if "top_zand_nap" not in _w:
            # oude 'watervoerend_knik_nap' was de top van het zandpakket
            _w["top_zand_nap"] = _w.get("watervoerend_knik_nap", -12.0)
        if "indringing" not in _w:
            _w["indringing"] = 0.0
        if "gamma_w" not in _w:
            _w["gamma_w"] = 9.81

    # === TABS ===
    tab1, tab_grond, tab2, tab3, tab4, tab_water, tab5, tab6 = st.tabs([
        "🏗️ Dijkopbouw",
        "📋 Grondopbouw (invoer)",
        "💪 Sterkteparameters (Tabel 91)",
        "📐 Conustype & Correctie",
        "🔢 Nkt-factoren",
        "💧 Waterdruk (u₀)",
        "📊 Formules & Methode",
        "📝 Samenvatting"
    ])
    
    # ─── TAB 1: DIJKOPBOUW ───
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            lagen = up.get("lagen", DEFAULT_UITGANGSPUNTEN["lagen"])
            
            for i, laag in enumerate(lagen):
                dijk_label = "[Su]" if laag['is_dijkmateriaal'] else ""
                with st.expander(f"{laag['naam']}  {dijk_label}", expanded=False):
                    st.markdown(f"*{laag['beschrijving']}*")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        top_val = laag.get("top_nap")
                        if top_val is not None:
                            lagen[i]["top_nap"] = st.number_input(
                                f"Top [m NAP]", value=float(top_val), step=0.01, format="%.2f",
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
                                f"Onder [m NAP]", value=float(onder_val), step=0.01, format="%.2f",
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
            c_gwl1, c_gwl2, c_gwl3 = st.columns(3)
            with c_gwl1:
                gwl = st.number_input(
                    "GWS [m NAP] (gebruikt)",
                    value=up.get("dijkopbouw", {}).get("gwl", 0.0),
                    step=0.01, format="%.2f",
                    help="Grondwaterstand die wordt gebruikt voor de berekening. "
                         "Kies een waarde binnen de bandbreedte."
                )
                up["dijkopbouw"]["gwl"] = gwl
            with c_gwl2:
                gwl_max = st.number_input(
                    "GWS max [m NAP]",
                    value=up.get("dijkopbouw", {}).get("gwl_max", 1.0),
                    step=0.01, format="%.2f",
                    help="Hoogste grondwaterstand ten tijde van sonderen."
                )
                up["dijkopbouw"]["gwl_max"] = gwl_max
            with c_gwl3:
                gwl_min = st.number_input(
                    "GWS min [m NAP]",
                    value=up.get("dijkopbouw", {}).get("gwl_min", -0.5),
                    step=0.01, format="%.2f",
                    help="Laagste grondwaterstand ten tijde van sonderen."
                )
                up["dijkopbouw"]["gwl_min"] = gwl_min
            
            st.markdown("---")
            kruinniveau = st.number_input(
                "Kruinniveau [m NAP]",
                value=up.get("dijkopbouw", {}).get("kruinniveau", 4.0),
                step=0.01, format="%.2f",
                help="Bovenkant van de dijk (wegdek niveau)."
            )
            up["dijkopbouw"]["kruinniveau"] = kruinniveau
        
        with col2:
            fig = maak_dijkprofiel_figuur(lagen)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("[Su] = Dijkmateriaal · Blauw = GWS")

    # ─── TAB GRONDOPBOUW: vrije invoer van de grondopbouw per laag ───
    with tab_grond:
        st.caption("Vul de grondopbouw zelf in: per rij de BOVENKANT (m NAP) en het laagtype. "
                   "De onderkant van een laag = de bovenkant van de volgende rij; de diepste "
                   "laag loopt door tot de opgegeven basis.")

        # Stabiele laag-bibliotheek (gedeeld met de per-sondering interpretatie).
        lagen_biblio = get_lagen_bibliotheek(up)

        # === Materiaaleigenschappen (bewerkbaar, à la Deltares CPT-tool) ===
        with st.expander("🧪 Materiaaleigenschappen (γ, S, m, Nkt, VC) — bewerken/toevoegen",
                         expanded=False):
            st.caption("Bewerk de materialen of voeg er toe. Deze lijst voedt de laagtype-keuze "
                       "hieronder en de berekening (γ voor σ, S/m voor SHANSEP, Nkt, VC voor karakteristiek).")
            mat_df = pd.DataFrame([{
                "Materiaal": l["naam"],
                "γ_sat": l.get("gamma_nat"), "γ_unsat": l.get("gamma_droog"),
                "S": l.get("S_ratio"), "m": l.get("m_factor"),
                "Nkt": l.get("Nkt"), "VC_su": l.get("VC_su", 0.25),
                "Dijkmateriaal": bool(l.get("is_dijkmateriaal", False)),
            } for l in lagen_biblio])
            mat_edit = st.data_editor(
                mat_df, num_rows="dynamic", hide_index=True, use_container_width=True,
                key="materialen_editor",
                column_config={
                    "Materiaal": st.column_config.TextColumn("Materiaal", width="large"),
                    "γ_sat": st.column_config.NumberColumn("γ_sat [kN/m³]", format="%.2f", step=0.1),
                    "γ_unsat": st.column_config.NumberColumn("γ_unsat [kN/m³]", format="%.2f", step=0.1),
                    "S": st.column_config.NumberColumn("S [-]", format="%.2f", step=0.01),
                    "m": st.column_config.NumberColumn("m [-]", format="%.2f", step=0.01),
                    "Nkt": st.column_config.NumberColumn("Nkt [-]", format="%.1f", step=0.1),
                    "VC_su": st.column_config.NumberColumn("VC_su [-]", format="%.2f", step=0.01),
                    "Dijkmateriaal": st.column_config.CheckboxColumn("Dijkmateriaal (Su)"),
                },
            )
            if st.button("💾 Materialen opslaan", key="save_materialen", type="primary"):
                def _f(v):
                    return float(v) if pd.notna(v) else None
                nieuwe = []
                for r in mat_edit.to_dict("records"):
                    naam = r.get("Materiaal")
                    if not naam or str(naam).strip() == "":
                        continue
                    laag = next((dict(l) for l in lagen_biblio if l["naam"] == naam), {})
                    laag.update({
                        "naam": str(naam), "gamma_nat": _f(r.get("γ_sat")),
                        "gamma_droog": _f(r.get("γ_unsat")), "S_ratio": _f(r.get("S")),
                        "m_factor": _f(r.get("m")), "Nkt": _f(r.get("Nkt")),
                        "VC_su": _f(r.get("VC_su")), "is_dijkmateriaal": bool(r.get("Dijkmateriaal")),
                    })
                    laag.setdefault("kleur", "#888888")
                    laag.setdefault("materiaal", str(naam))
                    nieuwe.append(laag)
                if nieuwe:
                    up["lagen_bibliotheek"] = nieuwe
                    st.session_state.uitgangspunten = up
                    st.success(f"✅ {len(nieuwe)} materialen opgeslagen.")
                    st.rerun()
                else:
                    st.warning("Geen geldige materialen (vul minstens een naam in).")

        lagen_biblio = get_lagen_bibliotheek(up)
        type_namen = [l["naam"] for l in lagen_biblio]

        # Seed de tabel: uit eerder opgeslagen grondopbouw, anders uit de huidige lagen
        # (alleen lagen met een bekende bovenkant).
        if up.get("grondopbouw"):
            seed_rows = up["grondopbouw"]
        else:
            seed_rows = [
                {
                    "bovenkant": l.get("top_nap"),
                    "laagtype": l["naam"],
                    "gamma_droog": l.get("gamma_droog"),
                    "gamma_nat": l.get("gamma_nat"),
                    "Nkt": l.get("Nkt"),
                    "is_dijkmateriaal": l.get("is_dijkmateriaal", False),
                }
                for l in lagen_biblio if l.get("top_nap") is not None
            ]

        seed_df = pd.DataFrame(seed_rows, columns=[
            "bovenkant", "laagtype", "gamma_droog", "gamma_nat", "Nkt", "is_dijkmateriaal"
        ])

        col_g1, col_g2 = st.columns([1.6, 1])
        with col_g1:
            edited = st.data_editor(
                seed_df,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="grondopbouw_editor",
                column_config={
                    "bovenkant": st.column_config.NumberColumn(
                        "Bovenkant [m NAP]", format="%.2f", step=0.01,
                        help="NAP-niveau van de bovenkant van deze laag (cm-nauwkeurig)."),
                    "laagtype": st.column_config.SelectboxColumn(
                        "Laagtype", options=type_namen, required=False,
                        help="Kies een laagtype uit de bibliotheek (Tabel 91)."),
                    "gamma_droog": st.column_config.NumberColumn(
                        "γ_droog [kN/m³]", format="%.2f", step=0.1,
                        help="Leeg laten = waarde uit bibliotheek."),
                    "gamma_nat": st.column_config.NumberColumn(
                        "γ_nat [kN/m³]", format="%.2f", step=0.1,
                        help="Leeg laten = waarde uit bibliotheek."),
                    "Nkt": st.column_config.NumberColumn(
                        "Nkt [-]", format="%.1f", step=0.1,
                        help="Leeg laten = waarde uit bibliotheek."),
                    "is_dijkmateriaal": st.column_config.CheckboxColumn(
                        "Dijkmateriaal (Su)", help="Aanvinken als hier Su berekend moet worden."),
                },
            )

        with col_g2:
            onderkant_basis = st.number_input(
                "Onderkant diepste laag [m NAP]",
                value=float(up.get("grondopbouw_basis", -25.0)),
                min_value=-60.0, max_value=0.0, step=0.5,
                help="Tot dit niveau loopt de onderste (diepste) laag door.",
            )
            st.markdown("**Hoe het werkt:**")
            st.markdown(
                "- Elke rij = bovenkant van een laag (m NAP)\n"
                "- Onderkant = bovenkant van de volgende rij\n"
                "- Zelfde laagtype mag meerdere keren (wordt #2, #3 …)\n"
                "- γ/Nkt leeg = automatisch uit de bibliotheek\n"
                "- Toepassen overschrijft de lagen in de hele tool"
            )

        if st.button("✅ Grondopbouw toepassen", type="primary", key="apply_grondopbouw"):
            rows = edited.to_dict("records")
            nieuwe_lagen = bouw_lagen_uit_grondopbouw(rows, lagen_biblio, onderkant_basis)
            if not nieuwe_lagen:
                st.warning("⚠️ Geen geldige rijen (vul bovenkant én laagtype in).")
            else:
                up["lagen"] = nieuwe_lagen
                up["grondopbouw"] = rows
                up["grondopbouw_basis"] = onderkant_basis
                st.session_state.uitgangspunten = up
                st.success(f"✅ {len(nieuwe_lagen)} lagen toegepast. De rest van de tool "
                           "(classificatie, σv0, Su) gebruikt nu deze grondopbouw.")
                st.rerun()

        # Voorbeeldweergave van de afgeleide laaggrenzen
        if up.get("grondopbouw"):
            preview = bouw_lagen_uit_grondopbouw(
                up["grondopbouw"], lagen_biblio, up.get("grondopbouw_basis", onderkant_basis))
            if preview:
                st.markdown("**Afgeleide laaggrenzen (huidige grondopbouw):**")
                prev_rows = [{
                    "Laag": l["naam"],
                    "Top [m NAP]": round(l["top_nap"], 2),
                    "Onder [m NAP]": round(l["onder_nap"], 2),
                    "Dikte [m]": round(l["top_nap"] - l["onder_nap"], 2),
                    "γ_nat": l["gamma_nat"],
                    "Nkt": l.get("Nkt") if l.get("Nkt") is not None else "—",
                    "Su": "✅" if l.get("is_dijkmateriaal") else "—",
                } for l in preview]
                st.dataframe(pd.DataFrame(prev_rows), use_container_width=True, hide_index=True)

    # ─── TAB 2: STERKTEPARAMETERS (TABEL 91) ───
    with tab2:
        st.caption("SHANSEP: Su = S · σ'v0 · OCRᵐ  |  * = aanname  |  ** = gedraineerd")
        
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
        st.caption("qt = qc + (1−a) · u2  —  a hangt af van conustype (0.70–0.85)")
        
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
        st.caption("Su = q_net / Nkt  —  * = default waarde uit schematiseringshandleiding")

        # ── Karakteristieke waarde (uitgangspunt, niet pas bij de Su-berekening) ──
        st.markdown("**Karakteristieke waarde — Su_kar = Su_gem · (1 − t · VC)**")
        kar = up.setdefault("karakteristiek", dict(DEFAULT_UITGANGSPUNTEN["karakteristiek"]))
        c_k1, c_k2 = st.columns([1.6, 1])
        with c_k1:
            _opties = ["VC per materiaal (aanbevolen)", "VC uit de data (spreiding Su-punten)"]
            _idx = 0 if kar.get("vc_bron", "materiaal") == "materiaal" else 1
            _keuze = st.radio(
                "VC-bron", _opties, index=_idx, key="vc_bron_radio",
                help="VC per materiaal: je voert de variatiecoëfficiënt per grondsoort in "
                     "(kolom VC_su in de materialentabel). Dit is een bewuste keuze over de "
                     "onzekerheid in de grondsterkte — de aanbevolen route.\n\n"
                     "VC uit de data: berekend uit de spreiding van de Su-punten in een laag. "
                     "Die spreiding is grotendeels punt-op-punt-ruis van de conus (meting per "
                     "2 cm) en geeft vaak VC > 0,6, waardoor Su_kar op 0 uitkomt.",
            )
            kar["vc_bron"] = "materiaal" if _keuze.startswith("VC per materiaal") else "data"
        with c_k2:
            kar["t_factor"] = st.number_input(
                "t-factor [-]", min_value=0.0, max_value=3.0,
                value=float(kar.get("t_factor", 1.645)), step=0.005, format="%.3f",
                help="1,645 = 95%-ondergrens van de NORMALE verdeling (σ bekend, n → ∞). "
                     "De formele aanpak voor waterkeringen gebruikt Student-t met n−1 "
                     "vrijheidsgraden (dus afhankelijk van n) plus ruimtelijke middeling. "
                     "Voorlopige waarde — af te stemmen.",
            )
        st.info(
            "📋 **Voorlopig — de aanpak is nog niet afgestemd.** Een vaste t = 1,645 hoort bij de "
            "normale verdeling. De aanpak voor waterkeringen (NEN 9997-1 / schematiseringshandleiding) "
            "gebruikt **Student-t** (afhankelijk van n) en **ruimtelijke middeling** langs het glijvlak. "
            "Ook of je **uitschieters** meeneemt is een projectafspraak.\n\n"
            "→ Methode afstemmen met **Herman-Jaap**, uitschieters met **Jan**. "
            "Vragenlijst: `OVERLEG_KARAKTERISTIEKE_WAARDE.md`."
        )
        if kar["vc_bron"] == "materiaal":
            st.caption("✅ VC komt uit de kolom **VC_su** in de materialentabel "
                       "(tab 'Grondopbouw (invoer)' → Materiaaleigenschappen). "
                       "De VC uit de data wordt bij de Su-berekening als **controlegetal** getoond.")
        else:
            st.warning("⚠️ VC uit de data geeft bij CPT-metingen vaak een onrealistisch hoge VC "
                       "(punt-op-punt-ruis), waardoor Su_kar naar 0 kan zakken. Alleen gebruiken "
                       "als je bewust de spreiding van de meting wilt meenemen.")
        st.markdown("---")

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
    
    # ─── TAB WATERDRUK: u₀-verloop (4-zone-model) ───
    with tab_water:
        st.caption("u₀ = theoretisch waterdrukverloop met lineaire overgang naar het watervoerend zandpakket "
                   "(conform 'waterdrukverloop berekening.xlsx')")

        water = up.get("waterdruk", DEFAULT_UITGANGSPUNTEN["waterdruk"])

        col_w1, col_w2 = st.columns([1, 1])

        with col_w1:
            water["knik_nap"] = st.number_input(
                "Knikpunt drukverloop [m NAP]",
                value=float(water.get("knik_nap", -5.0)),
                min_value=-30.0, max_value=5.0, step=0.01, format="%.2f",
                help="Einde van het zuiver hydrostatische verloop vanaf GWS; "
                     "begin van de lineaire overgangszone naar het zandpakket."
            )
            water["stijghoogte_nap"] = st.number_input(
                "Stijghoogte 1e zandpakket [m NAP]",
                value=float(water.get("stijghoogte_nap", -2.0)),
                min_value=-30.0, max_value=10.0, step=0.01, format="%.2f",
                help="Piëzometrisch niveau (P) van het watervoerende zandpakket. "
                     "Onder het zand geldt u₀ = γ_w·(stijghoogte − z)."
            )
            water["top_zand_nap"] = st.number_input(
                "Top 1e zandpakket [m NAP]",
                value=float(water.get("top_zand_nap", -12.0)),
                min_value=-40.0, max_value=5.0, step=0.01, format="%.2f",
                help="NAP-niveau van de bovenkant van het 1e watervoerende zandpakket."
            )
            water["indringing"] = st.number_input(
                "Indringingslengte [m]",
                value=float(water.get("indringing", 0.0)),
                min_value=0.0, max_value=5.0, step=0.1,
                help="Tot hoever boven het zand de pakketdruk al gevoeld wordt; "
                     "de zandzone start bij (top zand + indringing). Vaak < 1 m."
            )
            water["gamma_w"] = st.number_input(
                "γ_w (water) [kN/m³]",
                value=float(water.get("gamma_w", 9.81)),
                min_value=9.0, max_value=10.5, step=0.01,
                help="Volumegewicht water. Standaard 9.81 kN/m³."
            )

        with col_w2:
            # Visualisatie van het 4-zone u0-verloop (zelfde formule als normalisatie).
            import numpy as np
            gwl_nap = up.get("dijkopbouw", {}).get("gwl", 0.0)
            knik = water["knik_nap"]
            stijg = water["stijghoogte_nap"]
            top_zand = water["top_zand_nap"]
            indring = water["indringing"]
            gamma_w = water["gamma_w"]
            kruin = up.get("dijkopbouw", {}).get("kruinniveau", 4.0)

            # Ankerpunten overgangszone
            z_top_interp = knik
            u_top_interp = (gwl_nap - knik) * gamma_w
            z_bot_interp = top_zand + indring
            u_bot_interp = (stijg - z_bot_interp) * gamma_w
            denom = z_bot_interp - z_top_interp
            slope = (u_bot_interp - u_top_interp) / denom if denom != 0 else 0.0

            z = np.linspace(kruin, top_zand - 6.0, 300)
            u0 = np.where(
                z > gwl_nap,
                0.0,
                np.where(
                    z > knik,
                    (gwl_nap - z) * gamma_w,
                    np.where(
                        z > z_bot_interp,
                        slope * (z - z_top_interp) + u_top_interp,
                        (stijg - z) * gamma_w,
                    ),
                ),
            )

            fig_u = go.Figure()
            fig_u.add_trace(go.Scatter(
                x=u0, y=z, mode="lines",
                line=dict(color="#1e88e5", width=2.5),
                name="u₀ (theoretisch)"
            ))
            fig_u.add_hline(y=gwl_nap, line_dash="dot", line_color="#64b5f6",
                            annotation_text=f"GWS NAP {gwl_nap:+.1f}m",
                            annotation_position="top right")
            fig_u.add_hline(y=knik, line_dash="dash", line_color="#ff9800",
                            annotation_text=f"Knik NAP {knik:+.1f}m",
                            annotation_position="bottom right")
            fig_u.add_hline(y=top_zand + indring, line_dash="dot", line_color="#fbc02d",
                            annotation_text=f"Top zand{'+i' if indring else ''} NAP {top_zand + indring:+.1f}m",
                            annotation_position="bottom right")
            fig_u.update_layout(
                title="Waterdrukverloop u₀ (4 zones)",
                xaxis=dict(title="u₀ [kPa]"),
                yaxis=dict(title="Niveau [m NAP]"),
                height=400,
                template="plotly_white",
                showlegend=False,
            )
            st.plotly_chart(fig_u, use_container_width=True)

        up["waterdruk"] = water

        st.markdown("---")
        st.markdown("""
        **Belangrijk — u₀ is NIET hetzelfde als u₂:**

        - **u₀** = theoretisch waterdrukverloop op basis van GWS, knikpunt en pakketdruk.
          Wordt gebruikt voor effectieve spanning σ'ᵥ₀ = σᵥ₀ − u₀.
        - **u₂** = gemeten poriedruk tijdens sondering. Wijkt af in klei
          (excess pore pressure dissipeert niet binnen meettijd).

        Voor de Su-berekening gebruiken we **altijd u₀**, niet u₂.
        u₂ wordt alleen gebruikt voor de qt-correctie: qt = qc + (1−a)·u₂.

        **Lokale override per sondering:** in de Normalisatie-stap kun je per sondering
        een afwijkend knikpunt, stijghoogte, top zand of indringingslengte instellen als
        de zandlaag of pakketdruk lokaal verschilt.
        """)

    # ─── TAB 4: FORMULES & METHODE ───
    with tab5:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("""
            | Stap | Formule |
            |---|---|
            | qt correctie | $q_t = q_c + (1-a) \\cdot u_2$ |
            | Spanning | $\\sigma_{v0} = \\sum \\gamma_i \\cdot \\Delta z_i$ |
            | Effectief | $\\sigma'_{v0} = \\sigma_{v0} - u_0$ |
            | q_net | $q_{net} = q_t - \\sigma_{v0}$ |
            """)
        with col_f2:
            st.markdown("""
            | Stap | Formule |
            |---|---|
            | Qt (Robertson) | $Q_t = (q_t - \\sigma_{v0}) / \\sigma'_{v0}$ |
            | Rf | $R_f = (f_s / q_c) \\times 100\\%$ |
            | Su | $S_u = q_{net} / N_{kt}$ |
            | SHANSEP | $S_u = S \\cdot \\sigma'_{v0} \\cdot OCR^m$ |
            """)

        st.markdown("---")
        st.markdown("**u₀-verloop (vier zones, met lineaire overgang):**")
        st.markdown("""
        | Zone | Formule |
        |---|---|
        | boven GWS | $u_0 = 0$ |
        | GWS → knikpunt (klei) | $u_0 = \\gamma_w \\cdot (z_{GWS} - z)$ |
        | knikpunt → top zand+i (overgang) | $u_0 = $ lineaire interpolatie tussen de ankerpunten |
        | onder top zand+i (zand) | $u_0 = \\gamma_w \\cdot (z_{stijghoogte} - z)$ |

        Ankerpunten overgang: boven $(z_{knik},\\ \\gamma_w(z_{GWS}-z_{knik}))$,
        onder $(z_{topzand}+i,\\ \\gamma_w(z_{stijghoogte}-(z_{topzand}+i)))$.

        **u₀ ≠ u₂**: u₀ is theoretisch (voor σ'), u₂ is gemeten (voor qt-correctie).
        """)
    
    # ─── TAB 5: SAMENVATTING ───
    with tab6:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            # Project + Dijkopbouw
            st.markdown(f"**{up['project']['naam']}** — {up['project']['beschrijving']}")
            gwl_val = up['dijkopbouw']['gwl']
            gwl_max_val = up['dijkopbouw'].get('gwl_max', 1.0)
            gwl_min_val = up['dijkopbouw'].get('gwl_min', -0.5)
            st.markdown(f"Kruin NAP {up['dijkopbouw']['kruinniveau']:+.1f}m · "
                       f"GWS NAP {gwl_val:+.1f}m ({gwl_min_val:+.1f} tot {gwl_max_val:+.1f})")
            st.markdown(f"Conus: {up['conustype']['type']} · a = {up['conustype']['a_factor']}")
        
        with col_s2:
            # Lagen overzicht als compacte tabel
            lagen_rows = []
            for laag in up["lagen"]:
                top = laag.get("top_nap")
                onder = laag.get("onder_nap")
                pos = f"{top:+.1f} tot {onder:+.1f}" if top is not None and onder is not None else "var."
                nkt_val = laag.get("Nkt", "—")
                dijk = "✅" if laag["is_dijkmateriaal"] else "—"
                lagen_rows.append({
                    "Laag": laag["naam"], "NAP [m]": pos,
                    "γ_nat": laag["gamma_nat"], "Nkt": nkt_val, "Dijk": dijk
                })
            st.dataframe(pd.DataFrame(lagen_rows), use_container_width=True, hide_index=True, height=300)
    
    # Sla op in session state
    st.session_state.uitgangspunten = up
