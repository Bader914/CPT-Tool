"""
Module 7: Validatie & Nkt-kalibratie
- Upload lab-Su (triaxiaal, DSS) op NAP-niveau
- Interpoleer CPT-Su op lab-dieptes; bereken bias/RMSE per grondlaag
- Suggested Nkt = Nkt_oud × (Su_cpt / Su_lab) per laag
- Slider voor live Nkt-aanpassing en Su-update
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


def interpoleer_cpt_op_lab(df_cpt: pd.DataFrame, lab_nap: pd.Series) -> pd.Series:
    """Lineaire interpolatie van CPT-Su op lab-NAP-dieptes (CPT Su valid mask)."""
    su_valid = df_cpt["Su"].notna()
    if not su_valid.any():
        return pd.Series([np.nan] * len(lab_nap), index=lab_nap.index)
    # np.interp vereist monotoon stijgende x — sorteer NAP oplopend
    cpt_nap = df_cpt.loc[su_valid, "diepte_nap"].values
    cpt_su = df_cpt.loc[su_valid, "Su"].values
    order = np.argsort(cpt_nap)
    cpt_nap_s, cpt_su_s = cpt_nap[order], cpt_su[order]
    # Interpoleer; buiten range → NaN
    interp = np.interp(lab_nap.values, cpt_nap_s, cpt_su_s,
                        left=np.nan, right=np.nan)
    return pd.Series(interp, index=lab_nap.index)


def koppel_grondlaag_aan_lab(lab_nap: pd.Series, laaggrenzen: dict) -> pd.Series:
    """Wijs SHZ-grondlaag toe aan lab-meetpunten op basis van NAP-niveau."""
    result = pd.Series("Onbekend", index=lab_nap.index, dtype=object)
    for naam, g in laaggrenzen.items():
        if g.get("top_nap") is None or g.get("onder_nap") is None:
            continue
        mask = (lab_nap <= g["top_nap"]) & (lab_nap > g["onder_nap"])
        result[mask & (result == "Onbekend")] = naam
    return result


def render():
    st.caption("Stap 5b — Vergelijk CPT-Su met labproeven, kalibreer Nkt")

    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items()
                    if v.get("su_berekend")}

    if not su_berekend:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Su nog niet berekend</h4>
            <p>Ga eerst naar <b>Stap 5 — Sterkte Su</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.subheader("Upload laboratoriumresultaten")
    st.markdown("""
    **Verwacht formaat:** CSV/Excel met minstens kolommen voor NAP-niveau en Su [kPa].
    Optioneel: proeftype (triax/DSS/vane), sondering-naam, grondlaag.
    """)

    lab_file = st.file_uploader("Upload labdata", type=["csv", "xlsx"], key="lab_upload")
    if not lab_file:
        st.info("Upload labdata om de validatie te starten.")
        return

    try:
        if lab_file.name.lower().endswith(".csv"):
            lab_df = pd.read_csv(lab_file, sep=None, engine="python")
        else:
            lab_df = pd.read_excel(lab_file)
    except Exception as e:
        st.error(f"Fout bij inlezen: {e}")
        return

    st.success(f"✅ Labdata geladen: {len(lab_df)} proeven")
    with st.expander("📋 Lab preview"):
        st.dataframe(lab_df, use_container_width=True)

    # Kolom-mapping
    lcols = lab_df.columns.tolist()
    col1, col2, col3 = st.columns(3)
    with col1:
        l_nap = st.selectbox("NAP-kolom [m NAP]", lcols, key="l_nap")
    with col2:
        l_su = st.selectbox("Su-kolom [kPa]", lcols, key="l_su")
    with col3:
        l_type = st.selectbox("Proeftype-kolom (optioneel)", ["(geen)"] + lcols, key="l_type")

    if not l_nap or not l_su:
        return

    # Welke sondering vergelijken
    selected = st.selectbox("Vergelijk met sondering", list(su_berekend.keys()), key="lab_compare")
    if not selected:
        return

    data = su_berekend[selected]
    df_cpt = data["df"]
    laaggrenzen = data.get("laaggrenzen", {})
    up = st.session_state.get("uitgangspunten", {})
    # Per-sondering lagen (γ/Nkt) indien aanwezig, anders de globale lagen.
    lagen = data.get("lagen_lokaal") or up.get("lagen", [])

    # Filter lab op nuttige rijen
    lab = lab_df[[l_nap, l_su] + ([l_type] if l_type != "(geen)" else [])].copy()
    lab = lab.rename(columns={l_nap: "nap", l_su: "su_lab"})
    if l_type != "(geen)":
        lab = lab.rename(columns={l_type: "proeftype"})
    lab = lab.dropna(subset=["nap", "su_lab"])

    if lab.empty:
        st.warning("Geen geldige lab-rijen na filtering.")
        return

    # Koppel grondlaag aan lab
    lab["grondlaag"] = koppel_grondlaag_aan_lab(lab["nap"], laaggrenzen)
    lab["su_cpt"] = interpoleer_cpt_op_lab(df_cpt, lab["nap"])
    lab["residu"] = lab["su_lab"] - lab["su_cpt"]

    # Metrics per grondlaag
    st.markdown("---")
    st.subheader("Statistieken per grondlaag")

    nkt_per_laag = {l["naam"]: l.get("Nkt") for l in lagen}

    metric_rows = []
    for laag, sub in lab.groupby("grondlaag"):
        valid = sub.dropna(subset=["su_cpt"])
        if valid.empty:
            continue
        nkt_oud = nkt_per_laag.get(laag)
        su_cpt_mean = valid["su_cpt"].mean()
        su_lab_mean = valid["su_lab"].mean()
        nkt_voorstel = (nkt_oud * (su_cpt_mean / su_lab_mean)) if (nkt_oud and su_lab_mean > 0) else None
        metric_rows.append({
            "Grondlaag": laag,
            "n": len(valid),
            "Su CPT [kPa]": round(su_cpt_mean, 1),
            "Su Lab [kPa]": round(su_lab_mean, 1),
            "Bias (lab-cpt)": round(valid["residu"].mean(), 1),
            "RMSE [kPa]": round(np.sqrt((valid["residu"] ** 2).mean()), 1),
            "Nkt huidig": nkt_oud if nkt_oud is not None else "—",
            "Nkt voorstel": round(nkt_voorstel, 1) if nkt_voorstel else "—",
        })

    if metric_rows:
        st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)
        st.caption("Nkt voorstel = Nkt_huidig × (Su_cpt_gem / Su_lab_gem). "
                    "Su_cpt > Su_lab ⇒ huidige Nkt te laag → voorgesteld hoger.")

    # Plot
    st.markdown("---")
    fig = go.Figure()

    su_valid = df_cpt["Su"].notna()
    fig.add_trace(go.Scatter(
        x=df_cpt.loc[su_valid, "Su"], y=df_cpt.loc[su_valid, "diepte_nap"],
        name="Su CPT", line=dict(color="#0d47a1", width=2),
    ))

    if "proeftype" in lab.columns:
        for proeftype, sub in lab.groupby("proeftype"):
            fig.add_trace(go.Scatter(
                x=sub["su_lab"], y=sub["nap"], mode="markers",
                name=f"Lab: {proeftype}",
                marker=dict(size=11, symbol="diamond"),
            ))
    else:
        fig.add_trace(go.Scatter(
            x=lab["su_lab"], y=lab["nap"], mode="markers",
            name="Lab Su",
            marker=dict(size=11, color="#22c55e", symbol="diamond"),
        ))

    # Achtergrondbanden lagen
    for naam, g in laaggrenzen.items():
        if g.get("top_nap") is None or g.get("onder_nap") is None:
            continue
        fig.add_hrect(y0=g["onder_nap"], y1=g["top_nap"],
                      fillcolor=g.get("kleur", "#888888"),
                      opacity=0.12, line_width=0,
                      annotation_text=naam, annotation_position="left",
                      annotation_font_size=9)

    fig.update_layout(
        title=f"CPT vs Lab Su — {selected}",
        yaxis=dict(title="Niveau [m NAP]"),
        xaxis=dict(title="Su [kPa]"),
        height=700, template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Sla labdata op
    st.session_state.sonderingen[selected]["lab_data"] = lab_df
    st.session_state.sonderingen[selected]["lab_mapping"] = {
        "nap": "nap", "su": "su_lab",
        "type": "proeftype" if "proeftype" in lab.columns else None,
    }

    # ── Nkt-kalibratie slider ──
    st.markdown("---")
    st.subheader("🎯 Nkt-kalibratie (live preview)")

    klei_lagen = [l["naam"] for l in lagen if l.get("Nkt") is not None]
    if not klei_lagen:
        return

    kal_laag = st.selectbox("Pas Nkt aan voor laag", klei_lagen, key="kal_laag")
    huidig_nkt = next((l["Nkt"] for l in lagen if l["naam"] == kal_laag), 15.0)

    nieuw_nkt = st.slider(
        f"Nkt voor {kal_laag}",
        min_value=5.0, max_value=30.0,
        value=float(huidig_nkt), step=0.1,
        key=f"slider_nkt_{kal_laag}",
    )

    # Preview: bereken nieuwe Su voor deze laag
    mask = (df_cpt["grondlaag"] == kal_laag) & df_cpt["q_net"].notna()
    if mask.any():
        su_oud = (df_cpt.loc[mask, "q_net"] * 1000) / huidig_nkt
        su_nieuw = (df_cpt.loc[mask, "q_net"] * 1000) / nieuw_nkt

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=su_oud, y=df_cpt.loc[mask, "diepte_nap"],
                                    name=f"Su (Nkt={huidig_nkt})",
                                    line=dict(color="#94a3b8", width=2, dash="dot")))
        fig2.add_trace(go.Scatter(x=su_nieuw, y=df_cpt.loc[mask, "diepte_nap"],
                                    name=f"Su (Nkt={nieuw_nkt:.1f})",
                                    line=dict(color="#ef4444", width=2.5)))
        # Lab-punten in deze laag
        lab_laag = lab[lab["grondlaag"] == kal_laag]
        if not lab_laag.empty:
            fig2.add_trace(go.Scatter(x=lab_laag["su_lab"], y=lab_laag["nap"],
                                        mode="markers", name="Lab",
                                        marker=dict(size=11, color="#22c55e", symbol="diamond")))
        fig2.update_layout(
            title=f"Live preview Nkt — laag {kal_laag}",
            yaxis=dict(title="Niveau [m NAP]"), xaxis=dict(title="Su [kPa]"),
            height=400, template="plotly_white",
        )
        st.plotly_chart(fig2, use_container_width=True)

    heeft_lokaal = bool(data.get("lagen_lokaal"))
    doel = "deze sondering" if heeft_lokaal else "Uitgangspunten (globaal)"
    if st.button(f"💾 Nkt = {nieuw_nkt:.1f} opslaan voor {kal_laag} ({doel})", type="primary"):
        for l in lagen:
            if l["naam"] == kal_laag:
                l["Nkt"] = nieuw_nkt
                break
        if heeft_lokaal:
            # Schrijf terug naar de per-sondering lagen, niet naar de globale lijst.
            st.session_state.sonderingen[selected]["lagen_lokaal"] = lagen
        else:
            st.session_state.uitgangspunten["lagen"] = lagen
        st.success(f"✅ Nkt voor {kal_laag} bijgewerkt naar {nieuw_nkt:.1f}. "
                    "Klik op 'Bereken Su' in Stap 5 om door te rekenen.")
