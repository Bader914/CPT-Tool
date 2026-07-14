"""
Project opslaan & openen — een geanalyseerde set sonderingen bewaren.

Alles wat je per sondering invult (maaiveld, a-factor, voorboring, grondopbouw,
waterdruk) wordt samen met de ruwe GEF-tekst in één .json-bestand gezet. Zo kun je
een analyse later weer openen — of naast een andere set leggen.

Wat we WEL opslaan
------------------
- de ruwe GEF-tekst per sondering (zodat het bestand op zichzelf staat: je hebt de
  originele GEF's later niet meer nodig)
- alle handmatige interpretatie: kolom-mapping, maaiveld, a-factor, voorboring,
  funderingslaag, grondopbouw (laagindeling), waterdruk
- de projectuitgangspunten (materialen/Tabel 91, karakteristieke waarde)
- de gekozen methodes (γ-bron, Su-methode)

Wat we NIET opslaan
-------------------
Alles wat je uit het bovenstaande kunt HERBEREKENEN: de DataFrame met qt/u₀/σ/Su,
de afgeleide laaggrenzen en de resultaatvlaggen. Dat is bewust: zo kan een opgeslagen
analyse nooit resultaten bevatten die niet meer bij de invoer passen. Na het openen
druk je op de twee rekenknoppen en krijg je exact dezelfde uitkomst terug.
"""
from __future__ import annotations

import json
from datetime import datetime

from modules.data_inladen import parse_gef

PROJECT_VERSIE = 1

# Per sondering: de invoer die de gebruiker heeft gedaan of die uit de GEF komt.
# (df, lagen_lokaal, laaggrenzen, parameters en de vlaggen zijn afgeleid → niet opslaan)
INVOER_VELDEN = (
    "col_mapping", "maaiveld_nap", "a_factor", "a_factor_gef", "voorboring_gef",
    "voorboring", "funderingslaag", "grondopbouw_lokaal", "waterdruk_lokaal",
    "is_qt_corrected",
)


def maak_project(sonderingen: dict, uitgangspunten: dict, instellingen: dict | None = None) -> dict:
    """Bouw het project-dict uit de huidige sessie."""
    lijst = []
    for naam, data in sonderingen.items():
        gef = data.get("gef_tekst")
        if not gef:
            # Zonder de ruwe tekst kunnen we de sondering later niet reconstrueren.
            continue
        rij = {"bestand": naam, "gef_tekst": gef}
        for veld in INVOER_VELDEN:
            if veld in data:
                rij[veld] = data[veld]
        lijst.append(rij)

    return {
        "versie": PROJECT_VERSIE,
        "opgeslagen": datetime.now().isoformat(timespec="seconds"),
        "uitgangspunten": uitgangspunten,
        "instellingen": instellingen or {},
        "sonderingen": lijst,
    }


def project_naar_json(project: dict) -> str:
    return json.dumps(project, ensure_ascii=False, indent=1, default=str)


def lees_project(json_tekst: str) -> dict:
    """Lees en valideer een projectbestand. Gooit ValueError bij een ongeldig bestand."""
    try:
        project = json.loads(json_tekst)
    except json.JSONDecodeError as e:
        raise ValueError(f"Geen geldig projectbestand (JSON-fout): {e}") from e

    if not isinstance(project, dict) or "sonderingen" not in project:
        raise ValueError("Dit lijkt geen projectbestand van de CPT Su Tool.")

    versie = project.get("versie")
    if versie != PROJECT_VERSIE:
        raise ValueError(
            f"Projectbestand is versie {versie}, deze tool verwacht {PROJECT_VERSIE}."
        )
    return project


def herstel_sonderingen(project: dict) -> dict:
    """Zet het project terug om naar de sonderingen-dict voor session_state.

    De GEF wordt opnieuw geparsed uit de opgeslagen tekst, zodat de DataFrame en de
    GEF-metadata (maaiveld, a-factor, voorboring) exact hetzelfde zijn als de eerste
    keer. Daarna leggen we de opgeslagen interpretatie er weer overheen.
    """
    hersteld = {}
    for rij in project.get("sonderingen", []):
        naam = rij.get("bestand")
        gef = rij.get("gef_tekst")
        if not naam or not gef:
            continue

        df = parse_gef(gef)
        data = {"df": df, "gef_tekst": gef}
        for veld in INVOER_VELDEN:
            if veld in rij:
                data[veld] = rij[veld]

        # Vangnet: ontbreekt de kolom-mapping, dan opnieuw detecteren.
        if not data.get("col_mapping"):
            from modules.data_inladen import detect_columns
            data["col_mapping"] = detect_columns(df)

        # Afgeleide meta die de UI verwacht, opnieuw opbouwen uit de (verse) GEF.
        from modules.data_inladen import check_poriedruk_correctie
        data["poriedruk_check"] = check_poriedruk_correctie(df, data["col_mapping"])
        data["is_qt_corrected"] = data.get("is_qt_corrected",
                                           bool(df.attrs.get("is_qt_corrected", False)))

        hersteld[naam] = data
    return hersteld
