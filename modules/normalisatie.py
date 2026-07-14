"""
Module 4: Normalisatie (Qt) — DRAAIT NA Classificatie (stap 3)
- u0-verloop met knikpunt bij watervoerend pakket
- σv0 op basis van handmatige SHZ-laagindeling + funderingslaag (per sondering)
- qt-correctie + Rf + Bq + Qt + q_net
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from modules.classificatie import toewijs_grondlaag


# ───────────────────────────────────────────────────────────────
# Basis-formules (ongewijzigd)
# ───────────────────────────────────────────────────────────────
def bereken_qt(qc: pd.Series, u2: pd.Series, a: float = 0.80) -> pd.Series:
    """qt = qc + (1 - a) * u2"""
    return qc + (1 - a) * u2


def bereken_q_net(qt: pd.Series, sigma_v0: pd.Series) -> pd.Series:
    """q_net = qt - sigma_v0"""
    return qt - sigma_v0


def bereken_Rf(fs: pd.Series, qt: pd.Series) -> pd.Series:
    """Wrijvingsgetal Rf = (fs / qt) · 100  [%].

    Robertson/Lengkeek gebruiken de GECORRIGEERDE conusweerstand qt (niet qc).
    Bij ontbrekende qt-correctie geldt qt ≈ qc, dus dan is het verschil klein.
    """
    return (fs / qt.replace(0, np.nan)) * 100


def bereken_Bq(u2: pd.Series, u0: pd.Series, qt: pd.Series, sigma_v0: pd.Series) -> pd.Series:
    """Bq = (u2 - u0) / (qt - sigma_v0)"""
    q_net = qt - sigma_v0
    return (u2 - u0) / q_net.replace(0, np.nan)


def bereken_gamma_sat(qt: pd.Series, Rf: pd.Series, methode: str = "lengkeek",
                      gamma_w: float = 9.81) -> pd.Series:
    """Verzadigd volumegewicht γ_sat [kN/m³] uit qt [MPa] en Rf [%].

    Methodes:
      'lengkeek'  — Lengkeek et al. (2018), afgestemd op NL slappe lagen/veen:
                    γ_sat = 19 − 4.12 · log10(5/qt) / log10(30/Rf)
      'robertson' — Robertson & Cabal (2010):
                    γ_sat = γ_w · (0.27·log10(Rf) + 0.36·log10(qt/pa) + 1.236)
      'simple'    — NEN 9997-1 Tabel 2b (γ uit qc-drempels; qt als proxy)

    Resultaat geklemd op een fysisch bereik [9, 22] kN/m³; niet-bepaalbare punten
    (qc=0 / Rf=0) krijgen 17 kN/m³ als neutrale fallback.
    """
    qt = pd.to_numeric(qt, errors="coerce").clip(lower=0.01)        # MPa, vermijd log(0)
    rf = pd.to_numeric(Rf, errors="coerce").clip(lower=0.1, upper=12.0)  # %

    if methode == "lengkeek":
        noemer = np.log10(30.0 / rf).replace(0, np.nan)
        g = 19.0 - 4.12 * (np.log10(5.0 / qt) / noemer)
    elif methode == "robertson":
        pa = 0.101  # MPa
        g = gamma_w * (0.27 * np.log10(rf) + 0.36 * np.log10(qt / pa) + 1.236)
    elif methode == "simple":
        g = pd.Series(np.nan, index=qt.index)
        g[qt < 0.5] = 14.0
        g[(qt >= 0.5) & (qt < 1.0)] = 17.0
        g[(qt >= 1.0) & (qt < 2.0)] = 19.0
        g[(qt >= 2.0) & (qt < 5.0)] = 20.0
        g[(qt >= 5.0) & (qt < 15.0)] = 19.0
        g[(qt >= 15.0) & (qt < 25.0)] = 20.0
        g[qt >= 25.0] = 21.0
    else:
        raise ValueError(f"Onbekende gamma_sat-methode: {methode}")

    return g.replace([np.inf, -np.inf], np.nan).clip(lower=9.0, upper=22.0).fillna(17.0)


# ───────────────────────────────────────────────────────────────
# u0-verloop met knikpunt (watervoerend pakket)
# ───────────────────────────────────────────────────────────────
def bereken_u0_interpolatie(
    diepte_nap: pd.Series,
    gwl_nap: float,
    knik_nap: float,
    stijghoogte_nap: float,
    top_zand_nap: float,
    indringing: float = 0.0,
    gamma_w: float = 9.81,
) -> pd.Series:
    """
    Theoretisch waterdrukverloop u0 [kPa] — 4-zone-model met lineaire overgang.

    Implementatie van 'waterdrukverloop berekening.xlsx' (cel D31–D38), exact
    gevalideerd in CPT_kern_berekeningen.py. Het verloop is OVERAL CONTINU.

    Invoer (alle niveaus in m NAP, positief omhoog):
      gwl_nap          grondwaterstand (GWS)
      knik_nap         knikpunt: einde zuiver hydrostatisch verloop vanaf GWS
      stijghoogte_nap  stijghoogte (piëzometrisch niveau, P) van het 1e zandpakket
      top_zand_nap     NAP-niveau van de top van het 1e zandpakket
      indringing       indringingslengte i [m]: zandzone start bij top_zand_nap + i

    Vier zones (z = diepte in m NAP):
      z > gwl                     u0 = 0
      knik < z ≤ gwl  (klei)      u0 = γ_w·(gwl − z)                 [hydrostatisch vanaf GWS]
      (top_zand+i) < z ≤ knik     u0 = lineaire interpolatie tussen de twee ankerpunten
      z ≤ (top_zand+i) (zand)     u0 = γ_w·(stijghoogte − z)         [hydrostatisch vanaf stijghoogte]

    Ankerpunten van de overgangszone:
      boven: (knik_nap,         γ_w·(gwl − knik))
      onder: (top_zand_nap + i, γ_w·(stijghoogte − (top_zand+i)))
    """
    z = diepte_nap.values.astype(float)

    # Ankerpunten overgangszone (Excel C22/D22 en C23/D23).
    z_top_interp = knik_nap
    u_top_interp = (gwl_nap - knik_nap) * gamma_w
    z_bot_interp = top_zand_nap + indringing
    u_bot_interp = (stijghoogte_nap - z_bot_interp) * gamma_w

    # Scalaire helling → veilig af te schermen tegen deling door 0.
    denom = z_bot_interp - z_top_interp
    slope = (u_bot_interp - u_top_interp) / denom if denom != 0 else 0.0

    u0 = np.where(
        z > gwl_nap,
        0.0,
        np.where(
            z > knik_nap,
            (gwl_nap - z) * gamma_w,
            np.where(
                z > z_bot_interp,
                slope * (z - z_top_interp) + u_top_interp,
                (stijghoogte_nap - z) * gamma_w,
            ),
        ),
    )
    return pd.Series(u0, index=diepte_nap.index)


# ───────────────────────────────────────────────────────────────
# σv0 op basis van handmatige SHZ-laagindeling
# ───────────────────────────────────────────────────────────────
def bereken_sigma_v0_met_grondlaag(
    diepte_nap: pd.Series,
    grondlaag_per_meting: pd.Series,
    lagen: list,
    mv_nap: float,
    gwl_nap: float,
    funderingslaag: dict | None = None,
) -> pd.Series:
    """
    Bereken σv0 [kPa] door verticaal te integreren met γ per SHZ-laag.

    - Vóór de bovenste laaggrens: funderingslaag γ (indien actief), anders γ van bovenste laag
    - Per laag: γ_droog boven GWS, γ_nat onder GWS
    - Onbekende lagen: gemiddelde γ_nat uit alle gedefinieerde lagen
    """
    gamma_per_naam = {l["naam"]: {"droog": l.get("gamma_droog", l.get("gamma_nat", 18.0)),
                                   "nat": l.get("gamma_nat", 18.0)} for l in lagen}
    gemiddelde_gamma = float(np.mean([l.get("gamma_nat", 18.0) for l in lagen])) if lagen else 18.0

    z = diepte_nap.values.astype(float)
    # Sorteer op diepte (van boven naar beneden in NAP = afnemend)
    sort_idx = np.argsort(-z)
    z_sorted = z[sort_idx]
    namen_sorted = grondlaag_per_meting.values[sort_idx]

    # Funderingslaag bovenop: van maaiveld tot (maaiveld - dikte)
    fund_actief = funderingslaag and funderingslaag.get("actief")
    fund_dikte = funderingslaag.get("dikte", 0.0) if fund_actief else 0.0
    fund_gamma = funderingslaag.get("gamma", 21.0) if fund_actief else None
    fund_onder_nap = mv_nap - fund_dikte if fund_actief else mv_nap

    sigma = np.zeros_like(z_sorted)
    z_prev = mv_nap

    for i, (zi, naam) in enumerate(zip(z_sorted, namen_sorted)):
        dz = z_prev - zi  # positief: gaan naar beneden
        if dz <= 0:
            sigma[i] = sigma[i - 1] if i > 0 else 0.0
            continue

        # Bepaal γ voor dit interval — splits op funderingslaag-grens en GWS
        sigma_acc = sigma[i - 1] if i > 0 else 0.0
        z_top = z_prev
        z_bot = zi

        # Funderingslaag-gedeelte
        if fund_actief and z_top > fund_onder_nap:
            dz_fund = min(z_top, mv_nap) - max(z_bot, fund_onder_nap)
            if dz_fund > 0:
                sigma_acc += dz_fund * fund_gamma
            z_top = min(z_top, fund_onder_nap)

        if z_top > z_bot:
            # Gebruik γ van de grondlaag, droog boven GWS / nat onder GWS
            gamma = gamma_per_naam.get(str(naam), {"droog": gemiddelde_gamma, "nat": gemiddelde_gamma})
            # Splits op GWS
            if z_top > gwl_nap and z_bot < gwl_nap:
                dz_droog = z_top - gwl_nap
                dz_nat = gwl_nap - z_bot
                sigma_acc += dz_droog * gamma["droog"] + dz_nat * gamma["nat"]
            elif z_top <= gwl_nap:
                sigma_acc += (z_top - z_bot) * gamma["nat"]
            else:
                sigma_acc += (z_top - z_bot) * gamma["droog"]

        sigma[i] = sigma_acc
        z_prev = zi

    # Terugzetten in originele volgorde
    sigma_v0 = np.zeros_like(z)
    sigma_v0[sort_idx] = sigma
    return pd.Series(sigma_v0, index=diepte_nap.index)


def bereken_sigma_v0_uit_gamma(
    diepte_nap: pd.Series,
    gamma_sat: pd.Series,
    mv_nap: float,
    gwl_nap: float,
    funderingslaag: dict | None = None,
    boven_gws_reductie: float = 2.0,
) -> pd.Series:
    """Verticale totaalspanning σv0 [kPa] door integratie van een γ-profiel per punt.

    Gebruikt het uit qc/Rf afgeleide γ_sat per meetpunt (zie bereken_gamma_sat):
        - ONDER de GWS: γ_sat (verzadigd)
        - BOVEN de GWS: γ_moist ≈ γ_sat − boven_gws_reductie (vochtig, niet verzadigd)
          conform de standaard: moist boven, saturated onder het grondwater.

    Integratie van maaiveld naar beneden; optioneel een funderingslaag bovenop
    (eigen γ). γ in kN/m³, dz in m → σ in kPa.
    """
    z = diepte_nap.values.astype(float)
    g = pd.to_numeric(gamma_sat, errors="coerce").fillna(17.0).values.astype(float)
    # Boven GWS: vochtig volumegewicht (verzadigd minus reductie, niet negatief).
    g_eff = np.where(z > gwl_nap, np.maximum(g - boven_gws_reductie, 0.0), g)

    sort_idx = np.argsort(-z)
    z_sorted = g_eff[sort_idx] * 0 + z[sort_idx]   # behoud volgorde van z
    g_sorted = g_eff[sort_idx]

    fund_actief = bool(funderingslaag and funderingslaag.get("actief"))
    fund_dikte = funderingslaag.get("dikte", 0.0) if fund_actief else 0.0
    fund_gamma = funderingslaag.get("gamma", 21.0) if fund_actief else None
    fund_onder_nap = mv_nap - fund_dikte if fund_actief else mv_nap

    sigma = np.zeros_like(z_sorted)
    acc = 0.0
    z_prev = mv_nap
    for i, (zi, gi) in enumerate(zip(z_sorted, g_sorted)):
        dz = z_prev - zi
        if dz <= 0:
            sigma[i] = acc
            continue
        z_top, z_bot = z_prev, zi
        if fund_actief and z_top > fund_onder_nap:
            dz_fund = min(z_top, mv_nap) - max(z_bot, fund_onder_nap)
            if dz_fund > 0:
                acc += dz_fund * fund_gamma
            z_top = min(z_top, fund_onder_nap)
        if z_top > z_bot:
            acc += (z_top - z_bot) * gi
        sigma[i] = acc
        z_prev = zi

    out = np.zeros_like(z)
    out[sort_idx] = sigma
    return pd.Series(out, index=diepte_nap.index)


# ───────────────────────────────────────────────────────────────
# Render
# ───────────────────────────────────────────────────────────────
def render():
    st.caption("Stap 4 — qt-correctie, u₀-verloop met knikpunt, σ-spanningen")

    sonderingen = st.session_state.get("sonderingen", {})
    up = st.session_state.get("uitgangspunten", {})
    lagen = up.get("lagen", [])
    waterdruk = up.get("waterdruk", {})

    # Check vereisten: classificatie moet gedaan zijn
    geclassificeerd = {k: v for k, v in sonderingen.items() if v.get("geclassificeerd")}

    if not geclassificeerd:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Classificatie nog niet uitgevoerd</h4>
            <p>Ga eerst naar <b>Stap 3 — Classificatie</b> en stel de laaggrenzen per sondering in.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if not lagen:
        st.error("❌ Geen grondlagen gevonden. Ga eerst naar Stap 0 — Uitgangspunten.")
        return

    # Status
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Geclassificeerd", f"{len(geclassificeerd)}")
    with col_s2:
        st.metric("Genormaliseerd", f"{sum(1 for v in geclassificeerd.values() if v.get('genormaliseerd'))}")
    with col_s3:
        st.metric("Nog te doen", f"{sum(1 for v in geclassificeerd.values() if not v.get('genormaliseerd'))}")

    # Parameters
    st.markdown("---")
    st.subheader("Waterdruk & spanningen")
    st.caption(
        "Het waterdrukverloop stel je hier in — niet bij de uitgangspunten. De **top van het "
        "zandpakket** en het **knikpunt** lees je namelijk af uit de sondering zelf (waar qc "
        "omhoogschiet), en die ken je pas nu de grondlagen zijn bepaald. "
        "Controleer je aanname met de grafiek hieronder: de berekende **u₀** hoort in de buurt "
        "van de **gemeten u₂** te liggen."
    )

    # De a-factor is GEEN invoer meer op deze plek: hij hoort bij de sondering (uit de
    # GEF-header, of eenmalig ingevuld bij Stap 1). Hem hier nog eens kunnen zetten gaf
    # verwarring — je kon 0,80 instellen terwijl de tool met de GEF-waarde rekende.
    # We tonen alleen wat er per sondering wordt gebruikt.
    _a_rijen = []
    for _n, _d in geclassificeerd.items():
        _a = _d.get("a_factor")
        _a_rijen.append({
            "Sondering": _n,
            "a-factor": f"{_a:.2f}" if _a is not None else "⚠️ ontbreekt",
            "Bron": "GEF-header" if _d.get("a_factor_gef") is not None else
                    ("handmatig (Stap 1)" if _a is not None else "—"),
        })
    _ontbreekt = [r["Sondering"] for r in _a_rijen if r["a-factor"].startswith("⚠️")]
    with st.expander("📐 Nettoquotiënt conus (a-factor) — per sondering", expanded=bool(_ontbreekt)):
        st.caption("De a-factor komt uit de GEF-header (MEASUREMENTVAR 3) of is bij "
                   "**Stap 1 — Upload** ingevuld. Hier niet meer aanpasbaar, om verwarring te "
                   "voorkomen. Gebruikt voor: qt = qc + (1 − a)·u₂.")
        st.dataframe(pd.DataFrame(_a_rijen), use_container_width=True, hide_index=True)
        if _ontbreekt:
            st.warning("⚠️ Geen a-factor voor: **" + "**, **".join(_ontbreekt) + "**. "
                       "Vul hem in bij *Stap 1 — Upload → 📏 Referentieniveau & conus*. "
                       "Zonder a-factor rekent de tool met de standaard **0,80**.")

    # ── Waterdruk PER SONDERING (geen globale waarde) ──
    # De GWS, het knikpunt en de top van het zandpakket verschillen per locatie en lees
    # je af uit de sondering zelf. Er is daarom bewust géén projectbrede waarde meer:
    # elke sondering heeft zijn eigen rij. Zo kan er nooit stilletjes een globale waarde
    # worden gebruikt die niet bij deze locatie hoort.
    WD_DEFAULTS = {"gwl": 0.0, "knik_nap": -5.0, "stijghoogte_nap": -2.0,
                   "top_zand_nap": -12.0, "indringing": 0.0}

    st.markdown("**Waterdruk (u₀) — per sondering**")
    st.caption("Elke sondering heeft zijn eigen waarden; er is geen projectbrede GWS meer. "
               "Vul de tabel in en klik op opslaan. Controleer daarna met de grafiek: "
               "de berekende **u₀** hoort in de buurt van de gemeten **u₂** te liggen.")

    _wd_rows = []
    for _naam, _d in geclassificeerd.items():
        _w = _d.get("waterdruk_lokaal") or {}
        _wd_rows.append({
            "Sondering": _naam,
            "GWS [m NAP]": float(_w.get("gwl", WD_DEFAULTS["gwl"])),
            "Knikpunt [m NAP]": float(_w.get("knik_nap", WD_DEFAULTS["knik_nap"])),
            "Stijghoogte [m NAP]": float(_w.get("stijghoogte_nap", WD_DEFAULTS["stijghoogte_nap"])),
            "Top zandpakket [m NAP]": float(_w.get("top_zand_nap", WD_DEFAULTS["top_zand_nap"])),
            "Indringing [m]": float(_w.get("indringing", WD_DEFAULTS["indringing"])),
        })

    _num = lambda t: st.column_config.NumberColumn(t, format="%.2f", step=0.01)
    wd_edit = st.data_editor(
        pd.DataFrame(_wd_rows), hide_index=True, use_container_width=True,
        key="waterdruk_editor", disabled=["Sondering"],
        column_config={
            "Sondering": st.column_config.TextColumn("Sondering", width="medium"),
            "GWS [m NAP]": _num("GWS [m NAP]"),
            "Knikpunt [m NAP]": _num("Knikpunt [m NAP]"),
            "Stijghoogte [m NAP]": _num("Stijghoogte [m NAP]"),
            "Top zandpakket [m NAP]": _num("Top zandpakket [m NAP]"),
            "Indringing [m]": _num("Indringing [m]"),
        },
    )

    col_wd1, col_wd2 = st.columns([1, 1])
    with col_wd1:
        if st.button("💾 Waterdruk per sondering opslaan", use_container_width=True):
            for _r in wd_edit.to_dict("records"):
                st.session_state.sonderingen[_r["Sondering"]]["waterdruk_lokaal"] = {
                    "gwl": float(_r["GWS [m NAP]"]),
                    "knik_nap": float(_r["Knikpunt [m NAP]"]),
                    "stijghoogte_nap": float(_r["Stijghoogte [m NAP]"]),
                    "top_zand_nap": float(_r["Top zandpakket [m NAP]"]),
                    "indringing": float(_r["Indringing [m]"]),
                }
            st.success(f"✅ Waterdruk opgeslagen voor {len(wd_edit)} sondering(en).")
            st.rerun()
    with col_wd2:
        if st.button("📋 Eerste rij naar alle sonderingen kopiëren", use_container_width=True,
                     help="Handig als de waterdruk overal (vrijwel) gelijk is."):
            _eerste = wd_edit.to_dict("records")[0] if len(wd_edit) else None
            if _eerste:
                for _naam in geclassificeerd:
                    st.session_state.sonderingen[_naam]["waterdruk_lokaal"] = {
                        "gwl": float(_eerste["GWS [m NAP]"]),
                        "knik_nap": float(_eerste["Knikpunt [m NAP]"]),
                        "stijghoogte_nap": float(_eerste["Stijghoogte [m NAP]"]),
                        "top_zand_nap": float(_eerste["Top zandpakket [m NAP]"]),
                        "indringing": float(_eerste["Indringing [m]"]),
                    }
                st.success("✅ Waarden van de eerste rij naar alle sonderingen gekopieerd.")
                st.rerun()

    gamma_w = waterdruk.get("gamma_w", 9.81)

    # γ-bron voor σv0: handmatige SHZ-laag-γ (default) of qc-correlatie.
    st.markdown("**Volumegewicht (γ) voor σ-spanningen**")
    col_g1, col_g2 = st.columns([1.4, 1])
    with col_g1:
        gamma_bron = st.radio(
            "γ-bron",
            ["SHZ-laag (Tabel 91)", "qc-correlatie (Lengkeek 2018)",
             "qc-correlatie (Robertson 2010)", "qc-correlatie (NEN simpel)"],
            index=0, horizontal=False, key="gamma_bron",
            help="SHZ: γ per grondlaag uit de uitgangspunten. qc-correlatie: γ_sat "
                 "per meetpunt afgeleid uit qt en Rf.",
        )
    with col_g2:
        gws_reductie = st.number_input(
            "γ-reductie boven GWS [kN/m³]", min_value=0.0, max_value=5.0, value=2.0, step=0.5,
            help="Boven de grondwaterstand is grond niet verzadigd: γ_moist ≈ γ_sat − reductie. "
                 "Alleen voor de qc-correlatie.",
        )
    _bron_map = {"qc-correlatie (Lengkeek 2018)": "lengkeek",
                 "qc-correlatie (Robertson 2010)": "robertson",
                 "qc-correlatie (NEN simpel)": "simple"}
    gamma_methode = _bron_map.get(gamma_bron)  # None = SHZ-laag

    st.markdown("---")

    if st.button("▶️ Bereken qt, u₀ en σ-spanningen voor alle sonderingen", type="primary", use_container_width=True):
        progress = st.progress(0)
        total = len(geclassificeerd)
        resultaten = []

        for i, (name, data) in enumerate(geclassificeerd.items()):
            df = data["df"].copy()
            cm = data["col_mapping"]
            mv_nap = data.get("maaiveld_nap") or up.get("dijkopbouw", {}).get("kruinniveau", 4.0)
            grenzen = data.get("laaggrenzen", {})
            fund = data.get("funderingslaag")
            voorboring = data.get("voorboring")
            # Per-sondering lagen (γ/Nkt) indien aanwezig, anders de globale lagen.
            lagen_eff = data.get("lagen_lokaal") or lagen

            # Waterdruk komt PER SONDERING uit de tabel hierboven (geen globale waarde).
            # Is er nog niets opgeslagen, dan gelden de defaults.
            lokaal = data.get("waterdruk_lokaal") or {}
            gwl_local = lokaal.get("gwl", WD_DEFAULTS["gwl"])
            knik_local = lokaal.get("knik_nap", WD_DEFAULTS["knik_nap"])
            stijghoogte_local = lokaal.get("stijghoogte_nap", WD_DEFAULTS["stijghoogte_nap"])
            top_zand_local = lokaal.get("top_zand_nap", WD_DEFAULTS["top_zand_nap"])
            indringing_local = lokaal.get("indringing", WD_DEFAULTS["indringing"])

            try:
                # diepte_nap ALTIJD vers afleiden uit het actuele maaiveld, zodat een
                # maaiveldwijziging nooit stil verouderde data oplevert.
                df["diepte_nap"] = mv_nap - df[cm["diepte"]]

                # grondlaag + is_dijkmateriaal opnieuw toewijzen op basis van de
                # (absolute NAP-)laaggrenzen en de verse diepte_nap. De laaggrenzen
                # staan in NAP en zijn dus onafhankelijk van het maaiveld.
                if grenzen:
                    df["grondlaag"] = toewijs_grondlaag(df["diepte_nap"], grenzen)
                    dijkmat_lagen = {n for n, g in grenzen.items() if g.get("is_dijkmateriaal")}
                    df["is_dijkmateriaal"] = df["grondlaag"].isin(dijkmat_lagen)
                elif "grondlaag" not in df.columns:
                    resultaten.append({"Sondering": name, "Status": "❌ Geen laaggrenzen — herclassificeer"})
                    continue

                qc = df[cm["qc"]]

                # ── qt-correctie EERST (γ_sat en Rf hebben qt nodig) ──
                # De a-factor hoort bij de sondering: uit de GEF-header, of eenmalig
                # ingevuld bij Stap 1. Valt terug op 0,80 als hij nergens bekend is.
                a_local = data.get("a_factor") or data.get("a_factor_gef") or 0.80
                is_qt_corrected = data.get("is_qt_corrected", False)
                if is_qt_corrected:
                    df["qt"] = qc
                    qt_note = "al gecorrigeerd (qty 14)"
                elif cm.get("u2") and cm["u2"] in df.columns:
                    df["qt"] = bereken_qt(qc, df[cm["u2"]], a_local)
                    qt_note = f"u₂-correctie (a={a_local:.2f})"
                else:
                    df["qt"] = qc
                    qt_note = "geen u₂ (qt = qc)"

                # Rf = fs/qt (Robertson/Lengkeek). Altijd herberekenen met qt.
                if cm.get("fs") and cm["fs"] in df.columns:
                    df["Rf"] = bereken_Rf(df[cm["fs"]], df["qt"])

                # u0 — 4-zone-model met lineaire overgang (zie Excel waterdrukverloop)
                df["u0"] = bereken_u0_interpolatie(
                    df["diepte_nap"], gwl_local, knik_local,
                    stijghoogte_local, top_zand_local, indringing_local, gamma_w,
                ) / 1000.0  # kPa → MPa

                # ── σv0: γ-bron is SHZ-laag (default) of qc-correlatie ──
                if gamma_methode and "Rf" in df.columns:
                    df["gamma_sat"] = bereken_gamma_sat(df["qt"], df["Rf"], gamma_methode, gamma_w)
                    sigma_v0_kpa = bereken_sigma_v0_uit_gamma(
                        df["diepte_nap"], df["gamma_sat"], mv_nap, gwl_local, fund, gws_reductie
                    )
                else:
                    sigma_v0_kpa = bereken_sigma_v0_met_grondlaag(
                        df["diepte_nap"], df["grondlaag"], lagen_eff, mv_nap, gwl_local, fund
                    )
                df["sigma_v0"] = sigma_v0_kpa / 1000.0  # kPa → MPa
                df["sigma_v0_eff"] = (sigma_v0_kpa - df["u0"] * 1000.0).clip(lower=0) / 1000.0

                # Bq (vereist u₂)
                if cm.get("u2") and cm["u2"] in df.columns and not is_qt_corrected:
                    df["Bq"] = bereken_Bq(df[cm["u2"]], df["u0"], df["qt"], df["sigma_v0"])

                # Afgeleide grootheden (alles in MPa → q_net MPa, Qt dimensieloos)
                df["q_net"] = bereken_q_net(df["qt"], df["sigma_v0"])
                df["Qt"] = df["q_net"] / df["sigma_v0_eff"].replace(0, np.nan)

                # Voorboring: metingen in die zone ongeldig maken voor Su.
                # Let op: het GEWICHT van die grond telt wél mee in σv0 (hierboven al
                # berekend vanaf maaiveld) — alleen de metingen zijn onbetrouwbaar.
                if voorboring and voorboring.get("actief"):
                    vb_grens_nap = mv_nap - voorboring["diepte"]
                    df["voorboring_geldig"] = df["diepte_nap"] <= vb_grens_nap
                    n_uit = int((~df["voorboring_geldig"]).sum())
                    vb_note = (f"{voorboring['diepte']:.2f} m → boven NAP {vb_grens_nap:+.2f} m "
                               f"({n_uit} punt{'en' if n_uit != 1 else ''} zonder Su)")
                else:
                    df["voorboring_geldig"] = True
                    vb_note = "—"

                st.session_state.sonderingen[name]["df"] = df
                st.session_state.sonderingen[name]["genormaliseerd"] = True
                st.session_state.sonderingen[name]["parameters"] = {
                    "a": a_local, "gwl": gwl_local, "maaiveld_nap": mv_nap,
                    "knik_nap": knik_local, "stijghoogte_nap": stijghoogte_local,
                    "top_zand_nap": top_zand_local, "indringing": indringing_local,
                    "gamma_bron": gamma_bron,
                }
                resultaten.append({"Sondering": name, "Status": "✅", "qt": qt_note,
                                   "γ-bron": gamma_bron, "Metingen": len(df),
                                   "Voorboring": vb_note})

            except Exception as e:
                resultaten.append({"Sondering": name, "Status": f"❌ {e}", "qt": "—",
                                   "Metingen": 0, "Voorboring": "—"})

            progress.progress((i + 1) / total)

        st.success("Normalisatie voltooid.")
        st.dataframe(pd.DataFrame(resultaten), use_container_width=True, hide_index=True)

    # Resultaat-plots per sondering
    genormaliseerd = {k: v for k, v in sonderingen.items() if v.get("genormaliseerd")}

    if not genormaliseerd:
        return

    st.markdown("---")
    st.subheader("Resultaten")

    selected = st.selectbox("Sondering", list(genormaliseerd.keys()), key="norm_select")
    if not selected:
        return

    data = genormaliseerd[selected]
    df = data["df"]
    cm = data["col_mapping"]

    col_toggle1, col_toggle2 = st.columns(2)
    with col_toggle1:
        toon_u2 = st.checkbox("Toon u₂ (gemeten) ter vergelijking met u₀",
                               value=True, key=f"toon_u2_{selected}",
                               help="u₂ is de gemeten poriedruk; u₀ is het theoretische verloop "
                                    "dat wordt gebruikt voor σ'. Helpt visueel checken dat ze "
                                    "verschillen in klei en convergeren in zand.")
    with col_toggle2:
        toon_lagen = st.checkbox("Toon SHZ-laagverdeling op achtergrond",
                                  value=True, key=f"toon_lagen_norm_{selected}")

    fig = make_subplots(
        rows=1, cols=4,
        subplot_titles=["qt [MPa]", "u [kPa]", "σ [kPa]", "Qt [-]"],
        shared_yaxes=True, horizontal_spacing=0.04,
    )

    # Achtergrondbanden lagen
    if toon_lagen:
        grenzen = data.get("laaggrenzen", {})
        for naam, g in grenzen.items():
            if g.get("top_nap") is None or g.get("onder_nap") is None:
                continue
            for col in (1, 2, 3, 4):
                fig.add_hrect(
                    y0=g["onder_nap"], y1=g["top_nap"],
                    fillcolor=g.get("kleur", "#888888"),
                    opacity=0.14, line_width=0,
                    row=1, col=col,
                )

    # Kolom 1: qt + qc
    fig.add_trace(go.Scatter(x=df["qt"], y=df["diepte_nap"], name="qt",
                              line=dict(color="#0d47a1", width=1.5)), row=1, col=1)
    if cm.get("qc") and cm["qc"] in df.columns:
        fig.add_trace(go.Scatter(x=df[cm["qc"]], y=df["diepte_nap"], name="qc",
                                  line=dict(color="#90caf9", dash="dot", width=1)), row=1, col=1)

    # Kolom 2: u0 (en optioneel u2)
    fig.add_trace(go.Scatter(x=df["u0"] * 1000, y=df["diepte_nap"], name="u₀",
                              line=dict(color="#1e88e5", width=2)), row=1, col=2)
    if toon_u2 and cm.get("u2") and cm["u2"] in df.columns:
        fig.add_trace(go.Scatter(x=df[cm["u2"]] * 1000, y=df["diepte_nap"], name="u₂ (gemeten)",
                                  line=dict(color="#ef4444", dash="dash", width=1.5)), row=1, col=2)

    # Kolom 3: σv0 totaal + effectief
    fig.add_trace(go.Scatter(x=df["sigma_v0"] * 1000, y=df["diepte_nap"], name="σv0",
                              line=dict(color="#5d4037", width=1.5)), row=1, col=3)
    fig.add_trace(go.Scatter(x=df["sigma_v0_eff"] * 1000, y=df["diepte_nap"], name="σ'v0",
                              line=dict(color="#8d6e63", dash="dash", width=1.5)), row=1, col=3)

    # Kolom 4: Qt
    if "Qt" in df.columns:
        fig.add_trace(go.Scatter(x=df["Qt"], y=df["diepte_nap"], name="Qt",
                                  line=dict(color="#8b5cf6", width=1.5)), row=1, col=4)

    # Referentielijnen: uit de parameters die VOOR DEZE SONDERING zijn gebruikt.
    _p = data.get("parameters", {})
    _w = data.get("waterdruk_lokaal") or {}
    gwl_val = _p.get("gwl", _w.get("gwl", 0.0))
    knik_val = _p.get("knik_nap", _w.get("knik_nap", -5.0))
    top_zand_val = _p.get("top_zand_nap", _w.get("top_zand_nap", -12.0))

    for col in (1, 2, 3, 4):
        fig.add_hline(y=gwl_val, line=dict(color="#64b5f6", dash="dot", width=1), row=1, col=col)
        fig.add_hline(y=knik_val, line=dict(color="#ff9800", dash="dash", width=1), row=1, col=col)
        fig.add_hline(y=top_zand_val, line=dict(color="#fbc02d", dash="dot", width=1), row=1, col=col)

    fig.update_yaxes(title_text="Niveau [m NAP]", row=1, col=1)
    fig.update_layout(height=650, template="plotly_white",
                       legend=dict(orientation="h", yanchor="bottom", y=1.04, font=dict(size=10)))

    st.plotly_chart(fig, use_container_width=True)

    # Waarden die voor DEZE sondering zijn gebruikt (invoer staat in de tabel bovenaan).
    _wl = data.get("waterdruk_lokaal") or {}
    if _wl:
        st.caption(
            f"💧 Gebruikte waterdruk voor **{selected}** — GWS NAP {_wl.get('gwl', 0.0):+.2f} m · "
            f"knik {_wl.get('knik_nap', 0.0):+.2f} · stijghoogte {_wl.get('stijghoogte_nap', 0.0):+.2f} · "
            f"top zand {_wl.get('top_zand_nap', 0.0):+.2f} · indringing {_wl.get('indringing', 0.0):.2f} m. "
            "Aanpassen? Gebruik de tabel **Waterdruk (u₀) — per sondering** bovenaan."
        )
    else:
        st.caption("💧 Nog geen waterdruk opgeslagen voor deze sondering — de defaults zijn gebruikt. "
                   "Vul de tabel **Waterdruk (u₀) — per sondering** bovenaan in.")

    # Data tabel
    with st.expander("📋 Genormaliseerde data", expanded=False):
        show_cols = [c for c in [cm["diepte"], "diepte_nap", cm["qc"], "qt", "q_net",
                                  "Qt", "Rf", "u0", "sigma_v0", "sigma_v0_eff", "grondlaag"]
                     if c and c in df.columns]
        st.dataframe(df[show_cols].head(50), use_container_width=True)
