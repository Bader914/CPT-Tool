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


def classificeer_robertson(Qt: pd.Series, Rf: pd.Series) -> pd.Series:
    """
    Robertson 1990 classificatie op basis van Qt (genormaliseerd) en Rf.
    Behouden voor compatibiliteit en gebruikt als achtergrondhint als Qt al beschikbaar is.
    """
    zones = pd.Series(index=Qt.index, dtype=int)
    zones[(Qt <= 1)] = 2
    zones[(Qt > 1) & (Qt <= 10) & (Rf > 3)] = 3
    zones[(Qt > 1) & (Qt <= 10) & (Rf <= 3) & (Rf > 1)] = 4
    zones[(Qt > 10) & (Qt <= 30) & (Rf > 1)] = 5
    zones[(Qt > 10) & (Qt <= 30) & (Rf <= 1)] = 6
    zones[(Qt > 30) & (Qt <= 100) & (Rf <= 1)] = 7
    zones[(Qt > 100)] = 8
    zones[(Qt > 1) & (Qt <= 10) & (Rf <= 1)] = 1
    zones[(Qt > 30) & (Rf > 1)] = 9
    zones = zones.fillna(3)
    return zones.astype(int)


def classificeer_simple(qc: pd.Series, Rf: pd.Series) -> pd.Series:
    """
    Vereenvoudigde Robertson-achtige zone-bepaling zonder normalisatie.
    Gebruikt qc [MPa] en Rf [%] direct - geschikt voor achtergrondhint
    vóór de normalisatie-stap (waar Qt nog niet bestaat).
    """
    zones = pd.Series(index=qc.index, dtype="Int64")
    zones[qc < 0.5] = 2
    zones[(qc >= 0.5) & (qc < 2.0) & (Rf > 3)] = 3
    zones[(qc >= 0.5) & (qc < 2.0) & (Rf <= 3) & (Rf > 1)] = 4
    zones[(qc >= 0.5) & (qc < 2.0) & (Rf <= 1)] = 1
    zones[(qc >= 2.0) & (qc < 5.0) & (Rf > 1)] = 5
    zones[(qc >= 2.0) & (qc < 5.0) & (Rf <= 1)] = 6
    zones[(qc >= 5.0) & (qc < 15.0) & (Rf <= 1)] = 7
    zones[(qc >= 5.0) & (qc < 15.0) & (Rf > 1)] = 9
    zones[qc >= 15.0] = 8
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

            # Laaggrenzen uit defaults
            grenzen = data.get("laaggrenzen") or default_laaggrenzen(lagen)
            df["grondlaag"] = toewijs_grondlaag(df["diepte_nap"], grenzen)

            # Markeer dijkmateriaal op basis van SHZ-laag (niet Robertson)
            dijkmat_lagen = {laag["naam"] for laag in lagen if laag.get("is_dijkmateriaal")}
            df["is_dijkmateriaal"] = df["grondlaag"].isin(dijkmat_lagen)

            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["laaggrenzen"] = grenzen
            st.session_state.sonderingen[name]["geclassificeerd"] = True
            succes += 1

        st.success(f"✅ {succes} sondering(en) geclassificeerd met defaults. Pas hieronder per sondering aan.")
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

    col_edit, col_plot = st.columns([1, 1.4])

    with col_edit:
        st.markdown("**Top/onder per laag [m NAP]:**")
        st.caption(f"Maaiveld: NAP {mv_nap:+.2f}m · Sondeerbereik: NAP {df['diepte_nap'].max():+.2f} → {df['diepte_nap'].min():+.2f}m")

        nieuwe_grenzen = {}
        for laag in lagen:
            naam = laag["naam"]
            huidig = grenzen.get(naam, {})
            top_default = huidig.get("top_nap") if huidig.get("top_nap") is not None else laag.get("top_nap")
            onder_default = huidig.get("onder_nap") if huidig.get("onder_nap") is not None else laag.get("onder_nap")

            with st.expander(f"{naam}", expanded=False):
                c1, c2, c3 = st.columns([1, 1, 0.6])
                with c1:
                    top_val = st.number_input(
                        "Top [m NAP]",
                        value=float(top_default) if top_default is not None else 0.0,
                        step=0.1, format="%.2f",
                        key=f"top_{selected}_{naam}",
                    )
                with c2:
                    onder_val = st.number_input(
                        "Onder [m NAP]",
                        value=float(onder_default) if onder_default is not None else -1.0,
                        step=0.1, format="%.2f",
                        key=f"onder_{selected}_{naam}",
                    )
                with c3:
                    actief = st.checkbox(
                        "Aanwezig",
                        value=top_default is not None and onder_default is not None,
                        key=f"act_{selected}_{naam}",
                        help="Uitschakelen als deze laag op deze locatie niet voorkomt."
                    )

                nieuwe_grenzen[naam] = {
                    "top_nap": top_val if actief else None,
                    "onder_nap": onder_val if actief else None,
                    "kleur": laag.get("kleur", "#888888"),
                    "is_dijkmateriaal": laag.get("is_dijkmateriaal", False),
                }

        if st.button("💾 Laaggrenzen opslaan", key=f"save_grenzen_{selected}", type="primary"):
            st.session_state.sonderingen[selected]["laaggrenzen"] = nieuwe_grenzen
            df_new = df.copy()
            df_new["grondlaag"] = toewijs_grondlaag(df_new["diepte_nap"], nieuwe_grenzen)
            dijkmat_lagen = {n for n, g in nieuwe_grenzen.items() if g.get("is_dijkmateriaal")}
            df_new["is_dijkmateriaal"] = df_new["grondlaag"].isin(dijkmat_lagen)
            st.session_state.sonderingen[selected]["df"] = df_new
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
            xaxis=dict(title=f"{x_col} [MPa]"),
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
