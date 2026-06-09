"""


De volledige keten is:

    GEF-bestand
        │  (sondeerlengte, qc, fs, u2)
        ▼
    [1] Diepte → NAP-niveau          z_NAP = maaiveld_NAP − sondeerlengte
        ▼
    [2] Laagindeling (SHZ)           per meetpunt een grondlaag toewijzen
        ▼
    [3] Waterdruk u0                 theoretisch verloop met knikpunt
        ▼
    [4] Verticale spanning σv0       integratie van γ over de diepte
        ▼
    [5] Effectieve spanning σ'v0     σ'v0 = σv0 − u0
        ▼
    [6] qt-correctie                 qt = qc + (1 − a)·u2
        ▼
    [7] Netto conusweerstand q_net   q_net = qt − σv0
        ▼
    [8] Ongedraineerde sterkte Su    Su = q_net / Nkt
        ▼
    (controle) SHANSEP               Su = S · σ'v0 · OCR^m

Eenheden — LET OP, dit is de belangrijkste bron van fouten:
    - qc, qt, fs, u2, q_net   in de GEF/rekenkern: MPa
    - σv0, σ'v0, u0           intern omgerekend naar MPa zodat q_net klopt
    - Nkt                     dimensieloos [-]
    - Su                      gerapporteerd in kPa  → daarom *1000 bij Su
    - γ (volumegewicht)        kN/m³
    - diepte / NAP            m

Bronnen / normkader
    - Robertson (1990) — grondsoortclassificatie op basis van Qt en Rf
    - Schematiseringshandleiding (WBI/POVM) — Nkt-waarden, SHANSEP
    - NEN-EN-ISO 22476-1 — GEF/CPT quantity numbers
    - Tabel 71 (Nkt traject 14-1) en Tabel 91 (sterkteparameters) van het project

Auteur: rekenkern-export t.b.v. controle — juni 2026
================================================================================
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# Volumegewicht water [kN/m³]. Standaardwaarde; in de app instelbaar (9.81).
GAMMA_W = 9.81


# =============================================================================
# STAP 1 — qt-correctie (poriedrukcorrectie van de conusweerstand)
# =============================================================================
def bereken_qt(qc: pd.Series, u2: pd.Series, a: float = 0.80) -> pd.Series:
    """Gecorrigeerde conusweerstand qt.

        qt = qc + (1 − a) · u2

    Waarom: bij een elektrische conus drukt de poriewaterdruk u2 op de schouder
    achter de conuspunt. Een deel van het gemeten qc is dus géén echte
    grondweerstand maar waterdruk. De netto-oppervlakteverhouding `a` (typisch
    0,70–0,85, project: 0,80) corrigeert hiervoor.

    - a = 1,0  → geen correctie nodig (qt = qc)
    - a < 1,0  → poriedruk compenseert een deel van qc

    Belangrijk: hier gebruiken we de GEMETEN poriedruk u2, NIET het theoretische
    u0. u0 is uitsluitend voor de effectieve spanning (zie stap 3).

    Als de GEF-data al gecorrigeerd is (GEF quantity 14), wordt deze stap
    overgeslagen en geldt qt = qc.
    """
    return qc + (1 - a) * u2


# =============================================================================
# STAP 2 — Theoretisch waterdrukverloop u0 (4-zone-model, conform Excel)
# =============================================================================
def bereken_u0_interpolatie(
    diepte_nap: pd.Series,
    gwl_nap: float,
    knik_nap: float,
    stijghoogte_nap: float,
    top_zand_nap: float,
    indringing: float = 0.0,
    gamma_w: float = GAMMA_W,
) -> pd.Series:
    """Theoretische waterspanning u0 [kPa] — VERFIJND 4-zone-model.

    Dit is de implementatie uit 'waterdrukverloop berekening.xlsx' (cel D31–D38).
    Exact gevalideerd tegen de Excel-uitvoer (zie _demo_waterdruk()).

    Het verloop is OVERAL CONTINU (geen sprong) en kent vier zones, met als
    invoer NIET een druk maar de stijghoogte (piëzometrisch niveau) van het
    1e watervoerende zandpakket plus een indringingslengte.

    Parameters (alle niveaus in m NAP, positief omhoog):
        gwl_nap          grondwaterstand (GWS)
        knik_nap         knikpunt: einde van het zuiver hydrostatische verloop
                         vanaf GWS; begin van de overgangszone
        stijghoogte_nap  stijghoogte (piëzometrisch niveau, "P") van het 1e
                         zandpakket — vervangt de oude druk u_top
        top_zand_nap     NAP-niveau van de top van het 1e zandpakket ("C10")
        indringing       indringingslengte i [m]: tot hoever BOVEN het zand de
                         pakketdruk al gevoeld wordt (zandzone start bij
                         top_zand_nap + i). Vaak < 1 m.

    Ankerpunten van de lineaire overgangszone:
        boven: (knik_nap,            γ_w·(gwl − knik))          [hydrostatisch bij knik]
        onder: (top_zand_nap + i,    γ_w·(stijghoogte − (top_zand+i)))  [piëzometrisch]

    De vier zones (z = diepte in m NAP):
        z > gwl                     u0 = 0
        knik < z ≤ gwl  (klei)      u0 = γ_w·(gwl − z)                  [hydrostatisch vanaf GWS]
        (top_zand+i) < z ≤ knik     u0 = lineaire interpolatie tussen de twee ankerpunten
        z ≤ (top_zand+i) (zand)     u0 = γ_w·(stijghoogte − z)          [hydrostatisch vanaf stijghoogte]

    De interpolatiezone overbrugt soepel het verschil tussen de freatische
    (hydrostatische) druk in de klei en de piëzometrische druk van het zand.
    """
    z = diepte_nap.values.astype(float) if hasattr(diepte_nap, "values") else np.asarray(diepte_nap, float)

    # Ankerpunten van de overgangszone (komen overeen met C22/D22 en C23/D23 in de Excel).
    z_top_interp = knik_nap
    u_top_interp = (gwl_nap - knik_nap) * gamma_w
    z_bot_interp = top_zand_nap + indringing
    u_bot_interp = (stijghoogte_nap - z_bot_interp) * gamma_w

    # Helling van de interpolatie; scalair, dus veilig af te schermen tegen deling door 0.
    denom = z_bot_interp - z_top_interp
    slope = (u_bot_interp - u_top_interp) / denom if denom != 0 else 0.0

    u0 = np.where(
        z > gwl_nap,
        0.0,                                                          # boven GWS
        np.where(
            z > knik_nap,
            (gwl_nap - z) * gamma_w,                                  # klei: hydrostatisch vanaf GWS
            np.where(
                z > z_bot_interp,
                slope * (z - z_top_interp) + u_top_interp,            # overgangszone: lineair
                (stijghoogte_nap - z) * gamma_w,                      # zand: hydrostatisch vanaf stijghoogte
            ),
        ),
    )
    index = diepte_nap.index if hasattr(diepte_nap, "index") else None
    return pd.Series(u0, index=index)


# =============================================================================
# STAP 3 — Verticale totaalspanning σv0 (integratie van γ over de diepte)
# =============================================================================
def bereken_sigma_v0_met_grondlaag(
    diepte_nap: pd.Series,
    grondlaag_per_meting: pd.Series,
    lagen: list[dict],
    mv_nap: float,
    gwl_nap: float,
    funderingslaag: dict | None = None,
) -> pd.Series:
    """Verticale totaalspanning σv0 [kPa] door verticale integratie:

        σv0(z) = Σ γ_i · Δz_i      (van maaiveld tot diepte z)

    Per laag wordt het juiste volumegewicht gebruikt:
        - γ_droog  boven de grondwaterstand (GWS)
        - γ_nat    onder de grondwaterstand

    De laagindeling komt uit de handmatige SHZ-classificatie (stap 2 van de
    keten): `grondlaag_per_meting` bevat per meetpunt de naam van de grondlaag,
    en `lagen` bevat de γ-waarden per laag.

    Bijzonderheden:
      1) Funderingslaag (optioneel): een kunstmatige toplaag (bijv. wegfundering,
         puin/zand) bovenop het maaiveld. Krijgt zijn eigen γ en wordt vóór alle
         SHZ-lagen meegerekend.
      2) Onbekende lagen: meetpunten zonder toegewezen laag krijgen het
         gemiddelde γ_nat van alle gedefinieerde lagen (conservatieve fallback).
      3) Een interval kan zowel de funderingsgrens als de GWS doorsnijden; het
         wordt daarom opgesplitst zodat elk deelinterval het juiste γ krijgt.

    De integratie gebeurt van boven (maaiveld) naar beneden, daarom sorteren we
    op aflopend NAP-niveau en tellen de spanning cumulatief op.
    """
    # γ-waarden per laagnaam ophalen (droog + nat).
    gamma_per_naam = {
        l["naam"]: {
            "droog": l.get("gamma_droog", l.get("gamma_nat", 18.0)),
            "nat": l.get("gamma_nat", 18.0),
        }
        for l in lagen
    }
    # Fallback-γ voor "Onbekend": gemiddelde van alle lagen.
    gemiddelde_gamma = (
        float(np.mean([l.get("gamma_nat", 18.0) for l in lagen])) if lagen else 18.0
    )

    z = diepte_nap.values.astype(float)
    # Sorteren van boven naar beneden = afnemend NAP-niveau.
    sort_idx = np.argsort(-z)
    z_sorted = z[sort_idx]
    namen_sorted = grondlaag_per_meting.values[sort_idx]

    # Funderingslaag bovenop het maaiveld.
    fund_actief = bool(funderingslaag and funderingslaag.get("actief"))
    fund_dikte = funderingslaag.get("dikte", 0.0) if fund_actief else 0.0
    fund_gamma = funderingslaag.get("gamma", 21.0) if fund_actief else None
    fund_onder_nap = mv_nap - fund_dikte if fund_actief else mv_nap

    sigma = np.zeros_like(z_sorted)
    z_prev = mv_nap  # we starten de integratie op maaiveldniveau

    for i, (zi, naam) in enumerate(zip(z_sorted, namen_sorted)):
        dz = z_prev - zi  # positief = we dalen af
        if dz <= 0:
            # Geen diepteverschil (duplicaat/omhoog) → spanning niet ophogen.
            sigma[i] = sigma[i - 1] if i > 0 else 0.0
            continue

        sigma_acc = sigma[i - 1] if i > 0 else 0.0
        z_top = z_prev
        z_bot = zi

        # --- Deel 1: funderingslaag (indien het interval hierin valt) ---
        if fund_actief and z_top > fund_onder_nap:
            dz_fund = min(z_top, mv_nap) - max(z_bot, fund_onder_nap)
            if dz_fund > 0:
                sigma_acc += dz_fund * fund_gamma
            z_top = min(z_top, fund_onder_nap)  # rest van het interval onder de fundering

        # --- Deel 2: grondlaag, eventueel gesplitst op de GWS ---
        if z_top > z_bot:
            gamma = gamma_per_naam.get(
                str(naam), {"droog": gemiddelde_gamma, "nat": gemiddelde_gamma}
            )
            if z_top > gwl_nap and z_bot < gwl_nap:
                # Interval kruist de GWS → splitsen in droog (boven) en nat (onder).
                dz_droog = z_top - gwl_nap
                dz_nat = gwl_nap - z_bot
                sigma_acc += dz_droog * gamma["droog"] + dz_nat * gamma["nat"]
            elif z_top <= gwl_nap:
                # Volledig onder de GWS → nat.
                sigma_acc += (z_top - z_bot) * gamma["nat"]
            else:
                # Volledig boven de GWS → droog.
                sigma_acc += (z_top - z_bot) * gamma["droog"]

        sigma[i] = sigma_acc
        z_prev = zi

    # Terug in oorspronkelijke meetvolgorde zetten.
    sigma_v0 = np.zeros_like(z)
    sigma_v0[sort_idx] = sigma
    return pd.Series(sigma_v0, index=diepte_nap.index)


def bereken_sigma_v0_eff(sigma_v0: pd.Series, u0: pd.Series) -> pd.Series:
    """Effectieve verticale spanning (principe van Terzaghi):

        σ'v0 = σv0 − u0

    De effectieve spanning is de korrelspanning die de grond daadwerkelijk
    draagt. Negatieve waarden zijn fysisch onmogelijk en worden op 0 geklemd.
    σ'v0 wordt gebruikt voor zowel Qt (Robertson) als de SHANSEP-controle.
    """
    return (sigma_v0 - u0).clip(lower=0)


# =============================================================================
# STAP 4 — Afgeleide grootheden (q_net, Rf, Bq, Qt)
# =============================================================================
def bereken_q_net(qt: pd.Series, sigma_v0: pd.Series) -> pd.Series:
    """Netto conusweerstand:

        q_net = qt − σv0

    Dit is de conusweerstand gecorrigeerd voor de aanwezige totaalspanning op
    dat niveau — de "extra" weerstand die door de grondsterkte komt. q_net is de
    directe input voor de Su-berekening.
    """
    return qt - sigma_v0


def bereken_Rf(fs: pd.Series, qt: pd.Series) -> pd.Series:
    """Wrijvingsgetal (friction ratio) [%]:

        Rf = (fs / qt) · 100

    Robertson/Lengkeek gebruiken de GECORRIGEERDE conusweerstand qt (niet qc).
    Een hoge Rf wijst op fijnkorrelig materiaal (klei/veen), een lage Rf op zand.
    Bij ontbrekende qt-correctie geldt qt ≈ qc. Delen door 0 → NaN.
    """
    return (fs / qt.replace(0, np.nan)) * 100


def bereken_Bq(
    u2: pd.Series, u0: pd.Series, qt: pd.Series, sigma_v0: pd.Series
) -> pd.Series:
    """Poriedrukratio:

        Bq = (u2 − u0) / (qt − σv0) = (u2 − u0) / q_net

    Maat voor de excess poriedruk die tijdens het sonderen ontstaat. Hoog in
    slappe klei/veen (water kan niet wegstromen), rond 0 in zand. Aanvullende
    classificatie-indicator.
    """
    q_net = qt - sigma_v0
    return (u2 - u0) / q_net.replace(0, np.nan)


def bereken_Qt(q_net: pd.Series, sigma_v0_eff: pd.Series) -> pd.Series:
    """Genormaliseerde conusweerstand (Robertson 1990):

        Qt = (qt − σv0) / σ'v0 = q_net / σ'v0

    Dimensieloos. Samen met Rf de basis voor de Robertson-grondsoortzones.
    Deling door 0 (σ'v0 = 0 aan maaiveld) → NaN.
    """
    return q_net / sigma_v0_eff.replace(0, np.nan)


# =============================================================================
# γ uit qc/Rf — alternatief voor handmatige SHZ-laag-γ in σv0
# =============================================================================
def bereken_gamma_sat(qt: pd.Series, Rf: pd.Series, methode: str = "lengkeek",
                      gamma_w: float = GAMMA_W) -> pd.Series:
    """Verzadigd volumegewicht γ_sat [kN/m³] uit qt [MPa] en Rf [%].

    In plaats van γ handmatig per SHZ-laag op te geven, kun je γ_sat per meetpunt
    afleiden uit de sondering. Methodes:

      'lengkeek'  — Lengkeek et al. (2018), goed voor NL slappe lagen/veen:
                        γ_sat = 19 − 4.12 · log10(5/qt) / log10(30/Rf)
      'robertson' — Robertson & Cabal (2010):
                        γ_sat = γ_w · (0.27·log10(Rf) + 0.36·log10(qt/pₐ) + 1.236)
      'simple'    — NEN 9997-1 Tabel 2b (γ uit qc-drempels; qt als proxy)

    Let op (veelgemaakte fouten in correlatie-code):
      - Robertson & Cabal moet × γ_w (niet delen door γ_w).
      - Vectoriseer: `df.loc[mask, "col"] = …` (geen chained indexing `df.loc[…].col = …`).

    Resultaat geklemd op [9, 22] kN/m³; onbepaalbare punten → 17 kN/m³.
    """
    qt = pd.to_numeric(qt, errors="coerce").clip(lower=0.01)
    rf = pd.to_numeric(Rf, errors="coerce").clip(lower=0.1, upper=12.0)
    if methode == "lengkeek":
        noemer = np.log10(30.0 / rf).replace(0, np.nan)
        g = 19.0 - 4.12 * (np.log10(5.0 / qt) / noemer)
    elif methode == "robertson":
        pa = 0.101
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
        raise ValueError(f"Onbekende methode: {methode}")
    return g.replace([np.inf, -np.inf], np.nan).clip(lower=9.0, upper=22.0).fillna(17.0)


# =============================================================================
# STAP 5 — Ongedraineerde schuifsterkte Su
# =============================================================================
def bereken_Su(q_net: pd.Series, Nkt: pd.Series | float) -> pd.Series:
    """Ongedraineerde schuifsterkte uit de CPT:

        Su = q_net / Nkt          [kPa]

    Nkt is een empirische, grondsoort-afhankelijke conusfactor (project: per
    SHZ-laag vastgelegd in "Tabel 71"; typisch 14–20). De keuze van Nkt is
    bepalend voor de uitkomst en wordt waar mogelijk gekalibreerd op labproeven
    (triaxiaal/DSS) — zie kalibreer_nkt().

    Eenheden: q_net staat in MPa, daarom × 1000 om naar kPa te komen.
    """
    return (q_net * 1000) / Nkt


# =============================================================================
# CONTROLE — SHANSEP (onafhankelijke check op Su)
# =============================================================================
def bereken_su_shansep(
    sigma_v0_eff: pd.Series, S: float, m: float, OCR: pd.Series | float = 1.0
) -> pd.Series:
    """SHANSEP-relatie voor de ongedraineerde sterkte:

        Su = S · σ'v0 · OCR^m      [zelfde eenheid als σ'v0]

    - S   = sterkteratio (Su/σ'v0 bij OCR=1), per laag (Tabel 91)
    - m   = exponent voor het effect van overconsolidatie (OCR)
    - OCR = overconsolidatieratio (1,0 voor normaal geconsolideerd)

    Dit is een onafhankelijke schatting van Su die niet van de CPT-conusfactor
    Nkt afhangt. Wordt gebruikt als plausibiliteitscontrole op de CPT-Su.
    Let op de eenheid: lever σ'v0 in kPa aan om Su in kPa te krijgen.
    """
    return S * sigma_v0_eff * (OCR ** m)


# =============================================================================
# KALIBRATIE — Nkt afstemmen op labproeven
# =============================================================================
def kalibreer_nkt(nkt_oud: float, su_cpt_gem: float, su_lab_gem: float) -> float:
    """Voorgestelde Nkt op basis van labvalidatie, per grondlaag:

        Nkt_nieuw = Nkt_oud · (Su_cpt_gem / Su_lab_gem)

    Logica: omdat Su = q_net / Nkt geldt Su ∝ 1/Nkt. Is de CPT-Su gemiddeld
    hóger dan de lab-Su, dan was Nkt te laag → voorstel hoger (en omgekeerd).
    Zo "trek" je het CPT-profiel naar de labmetingen.
    """
    if su_lab_gem <= 0:
        return nkt_oud
    return nkt_oud * (su_cpt_gem / su_lab_gem)


# =============================================================================
# CLASSIFICATIE — Robertson (1990) zones
# =============================================================================
def classificeer_robertson(Qt: pd.Series, Rf: pd.Series) -> pd.Series:
    """Grondsoortzone (1–9) volgens Robertson (1990), op basis van Qt en Rf.

    Gebruikt in de tool vooral als visuele achtergrondhint; de uiteindelijke
    laagindeling wordt handmatig (SHZ) gedaan. Vereenvoudigde grenzen:

        zone 2  Qt ≤ 1                          organisch / veen
        zone 3  1 < Qt ≤ 10, Rf > 3             klei
        zone 4  1 < Qt ≤ 10, 1 < Rf ≤ 3         klei tot silt
        zone 1  1 < Qt ≤ 10, Rf ≤ 1             gevoelige fijnkorrelige grond
        zone 5  10 < Qt ≤ 30, Rf > 1            silt tot zandige klei
        zone 6  10 < Qt ≤ 30, Rf ≤ 1            zand tot kleiig zand
        zone 7  30 < Qt ≤ 100, Rf ≤ 1           zand tot zandig grind
        zone 9  Qt > 30, Rf > 1                 stijve fijnkorrelige grond
        zone 8  Qt > 100                        dicht zand
    """
    zones = pd.Series(index=Qt.index, dtype="float")
    zones[(Qt <= 1)] = 2
    zones[(Qt > 1) & (Qt <= 10) & (Rf > 3)] = 3
    zones[(Qt > 1) & (Qt <= 10) & (Rf <= 3) & (Rf > 1)] = 4
    zones[(Qt > 1) & (Qt <= 10) & (Rf <= 1)] = 1
    zones[(Qt > 10) & (Qt <= 30) & (Rf > 1)] = 5
    zones[(Qt > 10) & (Qt <= 30) & (Rf <= 1)] = 6
    zones[(Qt > 30) & (Qt <= 100) & (Rf <= 1)] = 7
    zones[(Qt > 30) & (Rf > 1)] = 9
    zones[(Qt > 100)] = 8
    return zones.fillna(3).astype(int)


# =============================================================================
# VOORBEELD / SANITY-CHECK
# =============================================================================
# Onderstaand voorbeeld rekent de volledige keten door op een klein, met de hand
# narekenbaar profiel. Handig om de eenheden en formules te controleren.
# Draai met:  python CPT_kern_berekeningen.py
def _demo():
    print("=" * 70)
    print(" DEMO — volledige keten op een klein profiel")
    print("=" * 70)

    # Uitgangspunten
    mv_nap = 4.0          # maaiveld op NAP +4 m (kruin van de dijk)
    gwl_nap = 0.0         # grondwaterstand op NAP 0 m
    knik_nap = -5.0       # knikpunt drukverloop [m NAP]
    stijghoogte = -2.0    # stijghoogte 1e zandpakket [m NAP]
    top_zand = -12.0      # top watervoerend zandpakket [m NAP]
    a = 0.80              # netto-oppervlakteverhouding conus

    # Twee SHZ-lagen, met γ en Nkt (vereenvoudigd uit Tabel 71/91)
    lagen = [
        {"naam": "klei_dijk", "gamma_droog": 18.0, "gamma_nat": 18.0, "Nkt": 14.1},
        {"naam": "veen",      "gamma_droog": 10.5, "gamma_nat": 10.5, "Nkt": 17.1},
    ]
    nkt_per_laag = {l["naam"]: l["Nkt"] for l in lagen}

    # Een handvol meetpunten (sondeerlengte → NAP). qc, fs, u2 in MPa.
    sondeerlengte = pd.Series([1.0, 3.0, 5.0, 7.0])
    qc = pd.Series([1.2, 0.8, 0.6, 0.9])    # MPa
    fs = pd.Series([0.03, 0.04, 0.05, 0.04])  # MPa
    u2 = pd.Series([0.02, 0.05, 0.08, 0.11])  # MPa

    diepte_nap = mv_nap - sondeerlengte
    grondlaag = pd.Series(["klei_dijk", "klei_dijk", "veen", "veen"])

    # [2] u0 — 4-zone-model; functie geeft kPa, intern werken we in MPa
    u0_kpa = bereken_u0_interpolatie(diepte_nap, gwl_nap, knik_nap,
                                     stijghoogte, top_zand)
    u0 = u0_kpa / 1000.0  # → MPa

    # [3]+[4] σv0 en σ'v0 (functie geeft kPa → MPa)
    sigma_v0_kpa = bereken_sigma_v0_met_grondlaag(
        diepte_nap, grondlaag, lagen, mv_nap, gwl_nap
    )
    sigma_v0 = sigma_v0_kpa / 1000.0
    sigma_v0_eff = bereken_sigma_v0_eff(sigma_v0, u0)

    # [1] qt, [5..] afgeleiden — Rf met qt (Robertson/Lengkeek)
    qt = bereken_qt(qc, u2, a)
    q_net = bereken_q_net(qt, sigma_v0)
    Rf = bereken_Rf(fs, qt)
    Qt = bereken_Qt(q_net, sigma_v0_eff)

    # [8] Su via Nkt per laag
    nkt = grondlaag.map(nkt_per_laag)
    Su = bereken_Su(q_net, nkt)

    resultaat = pd.DataFrame(
        {
            "z_NAP [m]": diepte_nap.round(2),
            "grondlaag": grondlaag,
            "qc [MPa]": qc,
            "qt [MPa]": qt.round(3),
            "u0 [kPa]": (u0 * 1000).round(1),
            "sv0 [kPa]": (sigma_v0 * 1000).round(1),
            "s'v0 [kPa]": (sigma_v0_eff * 1000).round(1),
            "q_net [MPa]": q_net.round(3),
            "Rf [%]": Rf.round(2),
            "Qt [-]": Qt.round(1),
            "Nkt [-]": nkt,
            "Su [kPa]": Su.round(1),
        }
    )
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print(resultaat.to_string(index=False))

    print("\nSHANSEP-controle (klei_dijk: S=0.35, m=0.79, OCR=1):")
    su_shansep = bereken_su_shansep(sigma_v0_eff * 1000, S=0.35, m=0.79, OCR=1.0)
    print((su_shansep.round(1)).to_string(index=False))


def _demo_waterdruk():
    """Validatie van het 4-zone-waterdrukmodel tegen 'waterdrukverloop berekening.xlsx'.

    De Excel-uitgangspunten zijn:
        GWS = 0 m+NAP, knikpunt = -5 m+NAP, stijghoogte P = -2 m+NAP,
        top 1e zandlaag = -12 m+NAP, indringing i = 0 m, γ_w = 9.81 kN/m³.
    """
    print("\n" + "=" * 70)
    print(" VALIDATIE WATERDRUK — bereken_u0_interpolatie() vs. Excel")
    print("=" * 70)

    gwl, knik, P, top_zand, i = 0.0, -5.0, -2.0, -12.0, 0.0

    # De diepte → waterdruk-paren uit de Excel (blok 'uitvoer berekening', C30:D38).
    excel = {
        1.0: 0.0,
        0.0: 0.0,
        -3.0: 29.43,
        -5.0: 49.050000000000004,
        -6.0: 56.057142857142864,
        -11.0: 91.09285714285716,
        -12.0: 98.10000000000001,
        -17.0: 147.15,
    }
    z = pd.Series(list(excel.keys()))
    verwacht = pd.Series(list(excel.values()))
    berekend = bereken_u0_interpolatie(z, gwl, knik, P, top_zand, i)

    tabel = pd.DataFrame({
        "z [m NAP]": z,
        "Excel [kPa]": verwacht.round(4),
        "tool [kPa]": berekend.round(4),
        "Δ": (berekend - verwacht).abs(),
    })
    print(tabel.to_string(index=False))

    max_afw = float((berekend - verwacht).abs().max())
    status = "✓ EXACT GELIJK" if max_afw < 1e-6 else f"✗ AFWIJKING {max_afw:.2e}"
    print(f"\nMax. afwijking: {max_afw:.2e} kPa  →  {status}")


if __name__ == "__main__":
    _demo()
    _demo_waterdruk()
