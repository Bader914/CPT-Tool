"""
Module 3: Classificatie & Handmatige Laagindeling (SHZ-werkwijze)
- Per sondering laaggrenzen aanwijzen op basis van SHZ-grondlagen
- Robertson 1990 blijft beschikbaar als visuele achtergrondhint
- Output: df["grondlaag"] (SHZ-laagnaam) per meetpunt
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from modules.uitgangspunten import bouw_lagen_uit_grondopbouw, get_lagen_bibliotheek


def grenzen_uit_lagen(lagen_lokaal: list) -> dict:
    """Maak een laaggrenzen-dict (naam → top/onder/kleur/dijk) uit een lagen-lijst."""
    return {
        l["naam"]: {
            "top_nap": l.get("top_nap"),
            "onder_nap": l.get("onder_nap"),
            "kleur": l.get("kleur", "#888888"),
            "is_dijkmateriaal": l.get("is_dijkmateriaal", False),
        }
        for l in lagen_lokaal
    }


def rows_uit_lagen(lagen: list) -> list:
    """Maak grondopbouw-rijen (bovenkant + laagtype) uit lagen met bekende top_nap."""
    return [{"bovenkant": l["top_nap"], "laagtype": l["naam"]}
            for l in lagen if l.get("top_nap") is not None]


# Robertson-zone → grove grondgroep (voor de suggestie-hint).
# Scheiding zand/klei op de gedrags-index ISBT = 2.60 (zone 5 = zand-achtig).
ROBERTSON_GROEP = {1: "klei", 2: "veen", 3: "klei", 4: "klei",
                   5: "zand", 6: "zand", 7: "zand", 8: "zand", 9: "klei"}


def _representatief_laagtype(groep: str, bibliotheek: list) -> str:
    """Kies een representatief bibliotheek-laagtype voor een grove groep (zand/klei/veen)."""
    def vind(keys, exclude=()):
        for l in bibliotheek:
            tekst = f"{l.get('naam', '')} {l.get('materiaal', '')}".lower()
            if any(k in tekst for k in keys) and not any(e in tekst for e in exclude):
                return l["naam"]
        return None

    namen = [l["naam"] for l in bibliotheek]
    fallback = namen[0] if namen else "Onbekend"
    if groep == "veen":
        return vind(["veen"]) or fallback
    if groep == "zand":
        # liefst ophoog-/pleistoceen zand; niet puin/fundering en niet 'zandige klei'
        return (vind(["ophoog"]) or vind(["zand"], exclude=["puin", "fundering", "klei", "veen"])
                or vind(["zand"]) or fallback)
    return vind(["siltig"]) or vind(["klei"]) or fallback  # klei: liefst siltige klei


def suggereer_grondopbouw(df: pd.DataFrame, cm: dict, bibliotheek: list,
                          min_dikte: float = 0.5) -> list:
    """Stel grondopbouw-rijen voor op basis van Robertson (qc/Rf) als startpunt.

    De ruwe per-punt Robertson-zones worden vertaald naar grove groepen
    (zand/klei/veen), met een rolling-mode gladgestreken zodat dunne ruislaagjes
    verdwijnen. Aaneengesloten segmenten worden samengevoegd tot lagen; lagen
    dunner dan `min_dikte` worden in de bovenliggende laag opgenomen.

    Geeft rijen [{"bovenkant": NAP, "laagtype": <bibliotheeknaam>}] — bedoeld als
    suggestie die de gebruiker daarna bijschaaft.
    """
    if "diepte_nap" not in df.columns or not cm.get("qc") or cm["qc"] not in df.columns:
        return []

    qc = df[cm["qc"]]
    if cm.get("fs") and cm["fs"] in df.columns:
        rf = (df[cm["fs"]] / qc.replace(0, np.nan)) * 100
    else:
        rf = pd.Series(2.0, index=df.index)

    zones = classificeer_simple(qc, rf.fillna(2.0))
    groep = zones.map(lambda z: ROBERTSON_GROEP.get(int(z), "klei"))

    # Sorteer van boven naar beneden (aflopend NAP).
    d = pd.DataFrame({"z": df["diepte_nap"], "g": groep}).sort_values("z", ascending=False)
    d = d.reset_index(drop=True)
    n = len(d)
    if n == 0:
        return []

    # Lichte ruisonderdrukking met een KLEIN, VAST venster (los van min_dikte),
    # om losse meetpunt-uitschieters te dempen zonder echte lagen weg te poetsen.
    groepen = ["veen", "klei", "zand"]
    code = {gname: i for i, gname in enumerate(groepen)}
    inv = {i: gname for gname, i in code.items()}
    c = d["g"].map(code).astype(float)
    dz = float(np.median(np.abs(np.diff(d["z"].values)))) if n > 1 else 0.02
    denoise_m = min(0.2, max(min_dikte * 0.5, 0.04))   # max 0,2 m, en ≤ ½·min_dikte
    denoise_win = max(1, int(round(denoise_m / max(dz, 1e-6))))
    if denoise_win > 1 and n > denoise_win:
        from collections import Counter
        c = c.rolling(denoise_win, center=True, min_periods=1).apply(
            lambda w: Counter(w.astype(int)).most_common(1)[0][0], raw=True)
    g = c.round().astype(int).map(inv).values
    z = d["z"].values

    # Segmenteer in aaneengesloten groepen: [top_nap, onder_nap, groep].
    segs = []
    start = 0
    for i in range(1, n + 1):
        if i == n or g[i] != g[start]:
            top = z[start]
            onder = z[i] if i < n else z[n - 1]
            segs.append([top, onder, g[start]])
            start = i

    # Iteratief: voeg telkens de DUNSTE laag < min_dikte samen met de dikkere
    # buurlaag (die groep wint). Werkt voor boven-, midden- en onderlagen.
    def dikte(s):
        return s[0] - s[1]

    while len(segs) > 1:
        idx = min(range(len(segs)), key=lambda k: dikte(segs[k]))
        if dikte(segs[idx]) >= min_dikte:
            break
        if idx == 0:
            j = 1
        elif idx == len(segs) - 1:
            j = idx - 1
        else:
            j = idx - 1 if dikte(segs[idx - 1]) >= dikte(segs[idx + 1]) else idx + 1
        lo, hi = min(idx, j), max(idx, j)
        nieuw = [max(segs[lo][0], segs[hi][0]),
                 min(segs[lo][1], segs[hi][1]),
                 segs[j][2]]
        segs[lo:hi + 1] = [nieuw]

    # Aangrenzende lagen van dezelfde groep samenvoegen.
    samengevoegd = []
    for s in segs:
        if samengevoegd and samengevoegd[-1][2] == s[2]:
            samengevoegd[-1][1] = s[1]
        else:
            samengevoegd.append(s)

    return [{"bovenkant": round(float(s[0]), 2),
             "laagtype": _representatief_laagtype(s[2], bibliotheek)}
            for s in samengevoegd]


# ───────────────────────────────────────────────────────────────
# Robertson 1990 zones (alleen voor achtergrondhint)
# ───────────────────────────────────────────────────────────────
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


# Atmosferische referentiedruk [MPa] (≈ 100 kPa) voor de Robertson ISBT-index.
PA_MPA = 0.1


def bereken_isbt(qc: pd.Series, Rf: pd.Series) -> pd.Series:
    """Niet-genormaliseerde Robertson SBT-index ISBT (Robertson 2010).

        ISBT = √[(3.47 − log₁₀(qc/pₐ))² + (log₁₀(Rf) + 1.22)²]

    qc in MPa, Rf in %. Geschikt vóór de normalisatie-stap; vrijwel gelijk aan de
    genormaliseerde Ic bij σ'v0 ≈ 50–150 kPa (ondiepe dijklagen). Rf wordt
    begrensd op 0,1–10 % zoals in de Deltares-implementatie (geolib-plus).
    """
    qc_pa = (qc / PA_MPA).clip(lower=1e-3)        # voorkom log10(0)
    rf = Rf.clip(lower=0.1, upper=10.0)
    return np.sqrt((3.47 - np.log10(qc_pa)) ** 2 + (np.log10(rf) + 1.22) ** 2)


def classificeer_simple(qc: pd.Series, Rf: pd.Series) -> pd.Series:
    """Robertson SBT-zone (2–7) op basis van de niet-genormaliseerde ISBT-index.

    Officiële Robertson (2010) grenswaarden — dezelfde als de genormaliseerde Ic:

        ISBT ≥ 3.60          → zone 2  organisch / veen
        2.95 ≤ ISBT < 3.60   → zone 3  klei
        2.60 ≤ ISBT < 2.95   → zone 4  siltmengsel (klei-achtig)
        2.05 ≤ ISBT < 2.60   → zone 5  zandmengsel (zand-achtig)
        1.31 ≤ ISBT < 2.05   → zone 6  zand
        ISBT < 1.31          → zone 7  dicht / grindig zand

    De gedrags-scheiding zand/klei ligt op ISBT = 2.60. Zones 1, 8 en 9
    (gevoelig / sterk overgeconsolideerd) vereisen genormaliseerde data en
    worden hier niet onderscheiden.
    """
    isbt = bereken_isbt(qc, Rf)
    zones = pd.Series(index=qc.index, dtype="Int64")
    zones[isbt >= 3.60] = 2
    zones[(isbt >= 2.95) & (isbt < 3.60)] = 3
    zones[(isbt >= 2.60) & (isbt < 2.95)] = 4
    zones[(isbt >= 2.05) & (isbt < 2.60)] = 5
    zones[(isbt >= 1.31) & (isbt < 2.05)] = 6
    zones[isbt < 1.31] = 7
    return zones.fillna(3).astype(int)


# ───────────────────────────────────────────────────────────────
# Handmatige laagtoewijzing
# ───────────────────────────────────────────────────────────────
def toewijs_grondlaag(diepte_nap: pd.Series, laaggrenzen: dict) -> pd.Series:
    """
    Wijs SHZ-grondlaagnaam toe per meting op basis van NAP-niveau.

    laaggrenzen: dict {laag_naam: {"top_nap": float, "onder_nap": float, ...}}
    Een meting hoort bij laag X als onder_nap < diepte_nap <= top_nap.
    """
    grondlaag = pd.Series("Onbekend", index=diepte_nap.index, dtype=object)
    # Sorteer op top_nap (hoog → laag); eerste match wint
    items = [(n, g) for n, g in laaggrenzen.items()
             if g.get("top_nap") is not None and g.get("onder_nap") is not None]
    items.sort(key=lambda kv: -kv[1]["top_nap"])
    for naam, grens in items:
        mask = (diepte_nap <= grens["top_nap"]) & (diepte_nap > grens["onder_nap"])
        # Alleen toewijzen waar nog "Onbekend"
        grondlaag[mask & (grondlaag == "Onbekend")] = naam
    return grondlaag


def default_laaggrenzen(lagen: list) -> dict:
    """
    Bouw default laaggrenzen-dict uit uitgangspunten-lagen.
    Voor lagen zonder vaste NAP-grenzen ("variabel per locatie") wordt geen default
    gezet — de gebruiker moet die handmatig invullen.
    """
    grenzen = {}
    for laag in lagen:
        grenzen[laag["naam"]] = {
            "top_nap": laag.get("top_nap"),
            "onder_nap": laag.get("onder_nap"),
            "kleur": laag.get("kleur", "#888888"),
            "is_dijkmateriaal": laag.get("is_dijkmateriaal", False),
        }
    return grenzen


# ───────────────────────────────────────────────────────────────
# UI
# ───────────────────────────────────────────────────────────────
def render():
    st.caption("Stap 3 — Handmatige laagindeling per sondering (Robertson als hint op achtergrond)")

    up = st.session_state.get("uitgangspunten", {})
    lagen = up.get("lagen", [])
    sonderingen = st.session_state.get("sonderingen", {})

    if not sonderingen:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Geen sonderingen geladen</h4>
            <p>Ga eerst naar <b>Stap 1 — Data Inladen</b> om sonderingen te uploaden.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if not lagen:
        st.error("❌ **Geen grondlagen gevonden.** Ga eerst naar Stap 0 — Uitgangspunten.")
        return

    # Filter sonderingen die bruikbaar zijn (diepte + qc kolommen)
    gereed = {k: v for k, v in sonderingen.items()
              if v.get("col_mapping", {}).get("diepte") and v.get("col_mapping", {}).get("qc")}
    niet_gereed = {k: v for k, v in sonderingen.items() if k not in gereed}

    # Status overzicht
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Totaal sonderingen", f"{len(sonderingen)}")
    with col_s2:
        st.metric("Bruikbaar (diepte+qc)", f"{len(gereed)} ✅")
    with col_s3:
        already = sum(1 for v in sonderingen.values() if v.get("geclassificeerd"))
        st.metric("Geclassificeerd", f"{already} 🔄")

    if niet_gereed:
        with st.expander(f"⚠️ {len(niet_gereed)} sondering(en) missen verplichte kolommen", expanded=False):
            for name in niet_gereed:
                cm = niet_gereed[name].get("col_mapping", {})
                missing = [k for k in ["diepte", "qc"] if not cm.get(k)]
                st.markdown(f"- **{name}**: kolom(men) `{', '.join(missing)}` ontbreken — terug naar Stap 1")

    if not gereed:
        st.error("❌ Geen bruikbare sonderingen. Stel eerst de kolom mapping in (Stap 1).")
        return

    # Toon SHZ-lagen overzicht
    with st.expander("📚 SHZ-grondlagen (uit Uitgangspunten)", expanded=False):
        for laag in lagen:
            tag = " **[Su]**" if laag.get("is_dijkmateriaal") else ""
            top = laag.get("top_nap")
            onder = laag.get("onder_nap")
            pos = f"default NAP {top:+.1f} → {onder:+.1f}m" if top is not None and onder is not None else "variabel per locatie"
            st.markdown(f"- **{laag['naam']}**: {pos} — {laag['materiaal']}{tag}")

    # Pas defaults toe op alle sonderingen die nog niet geclassificeerd zijn
    st.markdown("---")
    st.subheader("Snel-classificatie (defaults toepassen)")

    bibliotheek = get_lagen_bibliotheek(up)
    # Projectdefault als grondopbouw-rijen: globale grondopbouw-tab, anders uit lagen.
    default_rows = up.get("grondopbouw") or rows_uit_lagen(lagen)

    if st.button("▶️ Pas standaard laaggrenzen toe op alle sonderingen", type="primary", use_container_width=True):
        succes = 0
        for name, data in gereed.items():
            df = data["df"].copy()
            cm = data["col_mapping"]
            mv_nap = data.get("maaiveld_nap") or up.get("dijkopbouw", {}).get("kruinniveau", 4.0)

            # Bereken diepte_nap (zonder normalisatie)
            df["diepte_nap"] = mv_nap - df[cm["diepte"]]

            # Bereken Rf voor Robertson-hint
            if cm.get("fs") and cm["fs"] in df.columns:
                df["Rf"] = (df[cm["fs"]] / df[cm["qc"]].replace(0, np.nan)) * 100
            else:
                df["Rf"] = np.nan

            # Robertson achtergrondhint
            rf_for_hint = df["Rf"].fillna(2.0)
            df["robertson_zone"] = classificeer_simple(df[cm["qc"]], rf_for_hint)
            df["grondsoort"] = df["robertson_zone"].map(
                lambda z: ROBERTSON_ZONES.get(z, {}).get("naam", "Onbekend")
            )

            # Per-sondering grondopbouw: bestaande lokale, anders projectdefault.
            rows = data.get("grondopbouw_lokaal") or [dict(r) for r in default_rows]
            basis_nap = float(df["diepte_nap"].min())
            lagen_lokaal = bouw_lagen_uit_grondopbouw(rows, bibliotheek, basis_nap)
            grenzen = grenzen_uit_lagen(lagen_lokaal) if lagen_lokaal else default_laaggrenzen(lagen)

            df["grondlaag"] = toewijs_grondlaag(df["diepte_nap"], grenzen)
            dijkmat_lagen = {n for n, g in grenzen.items() if g.get("is_dijkmateriaal")}
            df["is_dijkmateriaal"] = df["grondlaag"].isin(dijkmat_lagen)

            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["grondopbouw_lokaal"] = rows
            st.session_state.sonderingen[name]["lagen_lokaal"] = lagen_lokaal
            st.session_state.sonderingen[name]["laaggrenzen"] = grenzen
            st.session_state.sonderingen[name]["geclassificeerd"] = True
            succes += 1

        st.success(f"✅ {succes} sondering(en) geclassificeerd met de projectdefault. Pas hieronder per sondering aan.")
        st.rerun()

    # Per-sondering editor
    geclassificeerd = {k: v for k, v in sonderingen.items() if v.get("geclassificeerd")}

    if not geclassificeerd:
        st.info("👆 Klik op de knop hierboven om defaults toe te passen, of bewerk hieronder per sondering.")
        return

    st.markdown("---")
    st.subheader("Laaggrenzen aanpassen per sondering")

    selected = st.selectbox("Selecteer sondering", list(geclassificeerd.keys()), key="class_select")

    if not selected:
        return

    data = geclassificeerd[selected]
    df = data["df"]
    cm = data["col_mapping"]
    grenzen = data.get("laaggrenzen") or default_laaggrenzen(lagen)
    mv_nap = data.get("maaiveld_nap") or up.get("dijkopbouw", {}).get("kruinniveau", 4.0)

    type_namen = [l["naam"] for l in bibliotheek]
    basis_nap = float(df["diepte_nap"].min())

    col_edit, col_plot = st.columns([1, 1.4])

    z_top = float(df["diepte_nap"].max())

    with col_edit:
        st.markdown("**Grondopbouw (bovenkant per laag, m NAP):**")
        st.caption(f"Maaiveld: NAP {mv_nap:+.2f}m · Sondeerbereik: NAP {z_top:+.2f} → "
                   f"{basis_nap:+.2f}m · Default uit de Grondopbouw-tab; pas hier per sondering aan.")

        # Robertson-suggestie als startpunt
        col_sug1, col_sug2 = st.columns([1, 1])
        with col_sug1:
            min_dikte = st.number_input(
                "Min. laagdikte [m]", min_value=0.1, max_value=5.0, value=0.5, step=0.1,
                key=f"min_dikte_{selected}",
                help="Dunner dan dit wordt samengevoegd bij de suggestie.",
            )
        with col_sug2:
            st.caption("")
            if st.button("🔎 Stel laaggrenzen voor (Robertson)", key=f"suggest_{selected}"):
                voorstel = suggereer_grondopbouw(df, cm, bibliotheek, min_dikte)
                if voorstel:
                    st.session_state.sonderingen[selected]["grondopbouw_lokaal"] = voorstel
                    st.success(f"Voorstel met {len(voorstel)} lagen geplaatst — pas aan en klik 'Laaggrenzen opslaan'.")
                    st.rerun()
                else:
                    st.warning("Kon geen voorstel maken (qc/diepte ontbreekt?).")

        # Seed: lokale grondopbouw → projectdefault → uit huidige grenzen.
        if data.get("grondopbouw_lokaal"):
            seed_rows = data["grondopbouw_lokaal"]
        elif default_rows:
            seed_rows = [dict(r) for r in default_rows]
        else:
            seed_rows = [{"bovenkant": g["top_nap"], "laagtype": n}
                         for n, g in grenzen.items() if g.get("top_nap") is not None]

        seed_df = pd.DataFrame(seed_rows, columns=["bovenkant", "laagtype"])

        edited = st.data_editor(
            seed_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key=f"grondopbouw_editor_{selected}",
            column_config={
                "bovenkant": st.column_config.NumberColumn(
                    "Bovenkant [m NAP]", format="%.2f", step=0.1,
                    help="Diepte (m NAP) van de bovenkant van de laag. Onderkant = volgende rij."),
                "laagtype": st.column_config.SelectboxColumn(
                    "Laagtype", options=type_namen, required=False,
                    help="Kies een laagtype uit de bibliotheek (γ/Nkt komen automatisch mee)."),
            },
        )

        st.caption(f"Onderste laag loopt door tot de sondeerbasis (NAP {basis_nap:+.2f}m).")

        # Waarschuw voor lagen die (deels) buiten het meetbereik vallen — niet wegfilteren.
        buiten = []
        for naam, g in grenzen.items():
            top, onder = g.get("top_nap"), g.get("onder_nap")
            if top is None or onder is None:
                continue
            if onder >= z_top:
                buiten.append(f"**{naam}** ligt volledig bóven de bovenste meting (NAP {z_top:+.2f}m)")
            elif top <= basis_nap:
                buiten.append(f"**{naam}** ligt volledig ónder de sondeerbasis (NAP {basis_nap:+.2f}m) — geen meetpunten")
            elif top < onder:
                buiten.append(f"**{naam}** is omgekeerd (top < onder) — controleer de grenzen")
        if buiten:
            st.warning("⚠️ Buiten meetbereik:\n\n- " + "\n- ".join(buiten))

        if st.button("💾 Laaggrenzen opslaan", key=f"save_grenzen_{selected}", type="primary"):
            rows = edited.to_dict("records")
            lagen_lokaal = bouw_lagen_uit_grondopbouw(rows, bibliotheek, basis_nap)
            if not lagen_lokaal:
                st.warning("⚠️ Geen geldige rijen (vul bovenkant én laagtype in).")
            else:
                nieuwe_grenzen = grenzen_uit_lagen(lagen_lokaal)
                df_new = df.copy()
                df_new["grondlaag"] = toewijs_grondlaag(df_new["diepte_nap"], nieuwe_grenzen)
                dijkmat_lagen = {n for n, g in nieuwe_grenzen.items() if g.get("is_dijkmateriaal")}
                df_new["is_dijkmateriaal"] = df_new["grondlaag"].isin(dijkmat_lagen)
                st.session_state.sonderingen[selected]["df"] = df_new
                st.session_state.sonderingen[selected]["grondopbouw_lokaal"] = rows
                st.session_state.sonderingen[selected]["lagen_lokaal"] = lagen_lokaal
                st.session_state.sonderingen[selected]["laaggrenzen"] = nieuwe_grenzen
                st.success(f"✅ Laaggrenzen voor **{selected}** opgeslagen.")
                st.rerun()

    with col_plot:
        toon_robertson = st.checkbox("Toon Robertson-zones (achtergrondhint)", value=False,
                                      key=f"rob_hint_{selected}")
        toon_lagen_band = st.checkbox("Toon SHZ-lagen als achtergrondband", value=True,
                                       key=f"lagen_band_{selected}")

        fig = go.Figure()

        # SHZ-lagen als achtergrondband
        if toon_lagen_band:
            for naam, g in grenzen.items():
                if g.get("top_nap") is None or g.get("onder_nap") is None:
                    continue
                fig.add_hrect(
                    y0=g["onder_nap"], y1=g["top_nap"],
                    fillcolor=g.get("kleur", "#888888"),
                    opacity=0.18, line_width=0,
                    annotation_text=naam, annotation_position="left",
                    annotation_font_size=9,
                )

        # Laaggrens-markers: horizontale lijn op elke bovenkant
        for naam, g in grenzen.items():
            if g.get("top_nap") is None:
                continue
            fig.add_hline(
                y=g["top_nap"], line=dict(color="#455a64", dash="dash", width=1),
                annotation_text=f"{g['top_nap']:+.2f}", annotation_position="right",
                annotation_font_size=8,
            )

        # qt of qc lijn
        x_col = "qt" if "qt" in df.columns else cm["qc"]
        fig.add_trace(go.Scatter(
            x=df[x_col], y=df["diepte_nap"],
            mode="lines", name=x_col,
            line=dict(color="#0d47a1", width=1.5),
        ))

        # Robertson-zones als kleurpunten (optioneel)
        if toon_robertson and "robertson_zone" in df.columns:
            for zone_nr, info in ROBERTSON_ZONES.items():
                mask = df["robertson_zone"] == zone_nr
                if mask.any():
                    fig.add_trace(go.Scatter(
                        x=df.loc[mask, x_col], y=df.loc[mask, "diepte_nap"],
                        mode="markers", name=f"R{zone_nr} — {info['naam']}",
                        marker=dict(color=info["kleur"], size=3, opacity=0.5),
                    ))

        fig.update_layout(
            title=f"{selected}",
            xaxis=dict(title=("qt [MPa]" if x_col == "qt" else "qc [MPa]")),
            yaxis=dict(title="Niveau [m NAP]"),
            height=700,
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=9)),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Samenvatting verdeling
        st.markdown("**Verdeling meetpunten per SHZ-laag:**")
        verdeling = df["grondlaag"].value_counts().reset_index()
        verdeling.columns = ["Grondlaag", "Aantal meetpunten"]
        verdeling["Aandeel"] = (verdeling["Aantal meetpunten"] / len(df) * 100).round(1).astype(str) + "%"
        st.dataframe(verdeling, use_container_width=True, hide_index=True)

    # Doorloop-suggestie
    st.markdown("""
    <div class="next-step">
        <span class="arrow">➡</span>
        <p>Wanneer alle sonderingen een goede laagindeling hebben, ga naar
        <b>Stap 4 — Normalisatie</b> voor qt-correctie en σ-spanningen.</p>
    </div>
    """, unsafe_allow_html=True)
