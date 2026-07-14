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
        # GWS staat hier BEWUST niet meer. Er is één waarde nodig (geen bandbreedte:
        # min/max wordt voor sonderingen niet gebruikt), en die stel je pas vast
        # nadat de sondering is ingelezen → Stap 4 — Waterdruk.
        "gwl": 0.0,                  # alleen startwaarde voor Stap 3; niet hier instelbaar
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



def _render_materialen(up: dict):
    """Materiaaleigenschappen (Tabel 91) — projectparameters, los van elke sondering.

    Geen eigen expander meer: render() plaatst dit al in een opvouwbare sectie.
    (Een expander in een expander gaf een dubbele, lege sectiekop.)
    """
    lagen_biblio = get_lagen_bibliotheek(up)
    st.caption("Bewerk de materialen of voeg er toe. Deze lijst voedt de laagtype-keuze per "
               "sondering én de berekening: γ voor de spanningen, S/m voor SHANSEP, Nkt voor Su "
               "en VC voor de karakteristieke waarde.")
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


def render():
    # Geen eigen kop: het wizard-kader in app.py toont al 'Stap 1 van 5'.

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

    # ── Rustig scherm: geen zes tabbladen tegelijk, maar één duidelijke boodschap
    # en opvouwbare secties. Standaard staat alles dicht — je opent alleen wat je wilt
    # aanpassen. De rekenwaardes worden nog steeds gezet: Streamlit voert de inhoud van
    # een expander ook uit als hij dichtgeklapt is.
    _kar = up.get("karakteristiek", DEFAULT_UITGANGSPUNTEN["karakteristiek"])
    _vc_txt = "VC per materiaal" if _kar.get("vc_bron", "materiaal") == "materiaal" else "VC uit de data"

    st.success(
        "✅ **De standaardwaarden voor traject 14-1 staan al ingevuld.** "
        "Je kunt meteen door naar de volgende stap — open hieronder alleen iets als je het "
        "wilt aanpassen."
    )
    _c1, _c2, _c3 = st.columns(3)
    _c1.metric("Grondsoorten", len(get_lagen_bibliotheek(up)))
    _c2.metric("Karakteristieke waarde", f"t = {_kar.get('t_factor', 1.645):.3f}", _vc_txt)
    _c3.metric("Conustype", up.get("conustype", {}).get("type", "—"))

    st.markdown("---")
    st.markdown("**Aanpassen — alleen als het nodig is**")
    tab2 = st.expander("🧪 Materiaaleigenschappen — γ, Nkt, S, m, VC (Tabel 91)", expanded=False)
    tab4 = st.expander("📉 Karakteristieke waarde — VC-bron en t-factor", expanded=False)

    st.markdown("**Naslag**")
    tab1 = st.expander("🏗️ Dijkopbouw (overzicht)", expanded=False)
    tab3 = st.expander("📐 Conustype & correctie", expanded=False)
    tab5 = st.expander("📊 Formules & methode", expanded=False)
    tab6 = st.expander("📝 Samenvatting", expanded=False)

    # ─── TAB 1: DIJKOPBOUW ───
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            lagen = up.get("lagen", DEFAULT_UITGANGSPUNTEN["lagen"])

            # Alleen ter oriëntatie: de algemene SHZ-dijkopbouw. Dit is GEEN invoer.
            # - de laagdieptes bepaal je per sondering (Stap 2 — Classificatie)
            # - γ/Nkt/S/m/VC bewerk je in de materialentabel (tab 'Sterkteparameters')
            # Eerder stonden hier invoervelden voor top/onder NAP en γ. Die schreven naar
            # up["lagen"], terwijl de berekening de materialenbibliotheek gebruikt — ze
            # hadden dus geen effect. Nu read-only, zodat er één bron van waarheid is.
            st.markdown("**Algemene dijkopbouw (SHZ) — ter oriëntatie**")
            st.caption("Dit is een typerend profiel, géén invoer. De **laagdieptes** bepaal je "
                       "per sondering bij **Stap 2 — Classificatie**; de **materiaalparameters** "
                       "(γ, Nkt, S, m, VC) bewerk je bij **💪 Sterkteparameters**.")
            overzicht = pd.DataFrame([{
                "Grondlaag": l["naam"],
                "Top [m NAP]": l["top_nap"] if l.get("top_nap") is not None else "variabel",
                "Onder [m NAP]": l["onder_nap"] if l.get("onder_nap") is not None else "variabel",
                "γ droog": l.get("gamma_droog"),
                "γ nat": l.get("gamma_nat"),
                "Su?": "✅" if l.get("is_dijkmateriaal") else "—",
            } for l in lagen])
            st.dataframe(overzicht, use_container_width=True, hide_index=True)

            # Grondwaterstand staat hier BEWUST NIET meer — ook geen bandbreedte.
            # Voor de sonderingen is één GWS-waarde voldoende (min/max wordt niet
            # gebruikt), en die stel je pas vast nadat de sondering is ingelezen.
            st.markdown("---")
            st.info(
                "💧 **De grondwaterstand stel je hier niet in.** Er is één waarde nodig, en die "
                "bepaal je pas nadat de sondering is ingelezen: bij **Stap 4 — Waterdruk** "
                "(globaal, en per sondering aanpasbaar)."
            )

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

    # ─── TAB 2: STERKTEPARAMETERS (Tabel 91) ───
    with tab2:
        st.caption("SHANSEP: Su = S · σ'v0 · OCRᵐ  |  * = aanname  |  ** = gedraineerd")

        # Materiaaleigenschappen (γ, S, m, Nkt, VC) — projectbreed, los van elke sondering.
        _render_materialen(up)
        st.markdown("---")

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
    
    # ─── TAB 3: CONUSTYPE & CORRECTIE (uitleg — geen invoer) ───
    with tab3:
        st.caption("qt = qc + (1−a) · u₂")

        conus = up.get("conustype", DEFAULT_UITGANGSPUNTEN["conustype"])

        # De a-factor is BEWUST geen invoer meer op deze plek. Hij is een eigenschap van
        # de gebruikte conus en staat in de GEF-header (MEASUREMENTVAR 3). Hem hier
        # projectbreed vastzetten gaf verwarring: je kon 0,80 instellen terwijl de tool
        # met de GEF-waarde rekende. Nu: uitlezen (of eenmalig invullen) bij Stap 1.
        st.info(
            "📐 **De nettoquotiënt (a-factor) stel je hier niet in.**\n\n"
            "Hij is een eigenschap van de gebruikte conus en wordt **automatisch uit de "
            "GEF-header gelezen** (`MEASUREMENTVAR 3`). Staat hij er niet in, dan vul je hem "
            "één keer in bij **Stap 2 — Upload → 📏 Referentieniveau & conus**. Daarna wordt "
            "hij overal gebruikt en is hij niet meer te wijzigen.\n\n"
            "Zo kan er nooit verschil ontstaan tussen wat je instelt en waarmee de tool rekent."
        )

        col1, col2 = st.columns(2)
        with col1:
            conus["type"] = st.text_input(
                "Conustype (documentatie)",
                value=conus.get("type", "Elektrische conus"),
                help="Alleen ter documentatie; heeft geen effect op de berekening."
            )
        with col2:
            st.markdown(
                "**Correctieformule**\n\n"
                "qt = qc + (1 − a) · u₂\n\n"
                "*a is per sondering; zie Stap 1.*"
            )

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
            st.markdown(f"Kruin NAP {up['dijkopbouw']['kruinniveau']:+.1f}m · "
                        f"GWS: *per sondering, Stap 4 — Waterdruk*")
            st.markdown(f"Conus: {up['conustype']['type']} · "
                        f"a-factor: *per sondering uit de GEF (Stap 1)*")
        
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
