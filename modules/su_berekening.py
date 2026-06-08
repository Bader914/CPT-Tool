"""
Module 5: Su Berekening
- Su = q_net / Nkt per meetpunt
- Nkt direct uit SHZ-grondlaag (df["grondlaag"] uit classificatie)
- Alleen voor dijkmateriaal (gemarkeerd in classificatie)
- Voorboring-data wordt overgeslagen
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def bereken_Su(q_net: pd.Series, Nkt: pd.Series) -> pd.Series:
    """Su = q_net / Nkt → [kPa]. q_net in MPa, dus *1000."""
    return (q_net * 1000) / Nkt


def render():
    st.caption("Stap 5 — Su = q_net / Nkt per grondlaag")

    genormaliseerd = {k: v for k, v in st.session_state.get("sonderingen", {}).items()
                       if v.get("genormaliseerd")}

    if not genormaliseerd:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Normalisatie nog niet uitgevoerd</h4>
            <p>Ga eerst naar <b>Stap 4 — Normalisatie</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    up = st.session_state.get("uitgangspunten", {})
    lagen = up.get("lagen", [])

    if not lagen:
        st.error("❌ Geen grondlagen. Ga naar Stap 0 — Uitgangspunten.")
        return

    # Nkt per SHZ-grondlaag (direct uit uitgangspunten)
    nkt_per_grondlaag = {l["naam"]: l["Nkt"] for l in lagen if l.get("Nkt") is not None}

    st.subheader("Nkt per grondlaag (Tabel 71)")
    nkt_rows = [{"Grondlaag": n, "Nkt": v} for n, v in nkt_per_grondlaag.items()]
    st.dataframe(pd.DataFrame(nkt_rows), use_container_width=True, hide_index=True)

    missing_dijkmat_nkt = [l["naam"] for l in lagen
                           if l.get("is_dijkmateriaal") and l.get("Nkt") is None]
    if missing_dijkmat_nkt:
        st.warning(f"⚠️ Nkt ontbreekt voor dijkmateriaal-lagen: {', '.join(missing_dijkmat_nkt)}. "
                    "Vul aan in Stap 0.")

    st.markdown("---")

    if st.button("▶️ Bereken Su voor alle sonderingen", type="primary", use_container_width=True):
        progress = st.progress(0)
        total = len(genormaliseerd)
        resultaten = []

        for i, (name, data) in enumerate(genormaliseerd.items()):
            df = data["df"].copy()

            if "q_net" not in df.columns:
                resultaten.append({"Sondering": name, "Status": "❌ q_net ontbreekt"})
                continue
            if "grondlaag" not in df.columns:
                resultaten.append({"Sondering": name, "Status": "❌ grondlaag ontbreekt"})
                continue

            # Nkt per grondlaag — per-sondering lagen indien aanwezig, anders globaal
            lagen_eff = data.get("lagen_lokaal") or lagen
            nkt_map = {l["naam"]: l["Nkt"] for l in lagen_eff if l.get("Nkt") is not None}
            df["Nkt_gebruikt"] = df["grondlaag"].map(nkt_map)

            # Su alleen voor dijkmateriaal (uit classificatie) + Nkt aanwezig + voorboring geldig
            geldig = df.get("is_dijkmateriaal", pd.Series([True] * len(df), index=df.index))
            geldig = geldig.fillna(False).astype(bool)
            if "voorboring_geldig" in df.columns:
                geldig = geldig & df["voorboring_geldig"].astype(bool)
            geldig = geldig & df["Nkt_gebruikt"].notna()

            df["Su"] = np.nan
            df.loc[geldig, "Su"] = bereken_Su(df.loc[geldig, "q_net"], df.loc[geldig, "Nkt_gebruikt"])
            df.loc[df["Su"] < 0, "Su"] = np.nan

            st.session_state.sonderingen[name]["df"] = df
            st.session_state.sonderingen[name]["su_berekend"] = True

            su_valid = df["Su"].notna().sum()
            resultaten.append({
                "Sondering": name, "Status": "✅",
                "Meetpunten met Su": su_valid,
                "Su gem [kPa]": f"{df['Su'].mean():.1f}" if su_valid > 0 else "—",
            })
            progress.progress((i + 1) / total)

        st.success(f"Su berekend voor {total} sondering(en)")
        st.dataframe(pd.DataFrame(resultaten), use_container_width=True, hide_index=True)

    # Resultaten
    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items()
                    if v.get("su_berekend")}
    if not su_berekend:
        return

    st.markdown("---")
    view_mode = st.radio("Weergave", ["Per sondering", "Alle sonderingen samen"],
                         horizontal=True, label_visibility="collapsed")

    if view_mode == "Per sondering":
        _render_per_sondering(su_berekend)
    else:
        _render_alle_samen(su_berekend)


def _render_per_sondering(su_berekend: dict):
    selected = st.selectbox("Selecteer sondering", list(su_berekend.keys()), key="su_select")
    if not selected:
        return

    data = su_berekend[selected]
    df = data["df"]
    cm = data["col_mapping"]

    su_data = df["Su"].dropna()
    if not su_data.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gemiddeld", f"{su_data.mean():.1f} kPa")
        c2.metric("Mediaan", f"{su_data.median():.1f} kPa")
        c3.metric("Min", f"{su_data.min():.1f} kPa")
        c4.metric("Max", f"{su_data.max():.1f} kPa")

    toon_lagen = st.checkbox("Toon SHZ-laagverdeling op achtergrond", value=True,
                              key=f"toon_lagen_su_{selected}")

    fig = make_subplots(rows=1, cols=3,
                        subplot_titles=["qt [MPa]", "Su [kPa]", "Nkt [-]"],
                        shared_yaxes=True, horizontal_spacing=0.05)

    if toon_lagen:
        grenzen = data.get("laaggrenzen", {})
        for naam, g in grenzen.items():
            if g.get("top_nap") is None or g.get("onder_nap") is None:
                continue
            for col in (1, 2, 3):
                fig.add_hrect(y0=g["onder_nap"], y1=g["top_nap"],
                              fillcolor=g.get("kleur", "#888888"),
                              opacity=0.14, line_width=0, row=1, col=col)

    fig.add_trace(go.Scatter(x=df["qt"], y=df["diepte_nap"], name="qt",
                              line=dict(color="#0d47a1", width=1.5)), row=1, col=1)

    su_valid = df["Su"].notna()
    fig.add_trace(go.Scatter(x=df.loc[su_valid, "Su"], y=df.loc[su_valid, "diepte_nap"],
                              name="Su", line=dict(color="#ef4444", width=2.5)), row=1, col=2)

    if "Nkt_gebruikt" in df.columns:
        nkt_valid = df["Nkt_gebruikt"].notna()
        fig.add_trace(go.Scatter(x=df.loc[nkt_valid, "Nkt_gebruikt"],
                                  y=df.loc[nkt_valid, "diepte_nap"],
                                  name="Nkt", line=dict(color="#64748b", width=1.5)), row=1, col=3)

    fig.update_yaxes(title_text="Niveau [m NAP]", row=1, col=1)
    fig.update_layout(height=650, template="plotly_white", title=f"Su-profiel — {selected}")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📊 Data: grondlaag → Nkt → Su per meetpunt", expanded=False):
        show_cols = [c for c in [cm.get("diepte"), "diepte_nap", "grondlaag",
                                  "q_net", "Nkt_gebruikt", "Su"]
                     if c and c in df.columns]
        st.dataframe(df[df["Su"].notna()][show_cols].round(3),
                     use_container_width=True, hide_index=True)


def _render_alle_samen(su_berekend: dict):
    fig = go.Figure()
    colors = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6",
              "#ec4899", "#14b8a6", "#f97316"]

    for i, (name, data) in enumerate(su_berekend.items()):
        df = data["df"]
        su_valid = df["Su"].notna()
        if su_valid.any():
            fig.add_trace(go.Scatter(
                x=df.loc[su_valid, "Su"], y=df.loc[su_valid, "diepte_nap"],
                mode="lines", name=name,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f"<b>{name}</b><br>Su=%{{x:.1f}} kPa<br>NAP %{{y:+.2f}}m<extra></extra>",
            ))

    fig.update_layout(
        title="Su-profielen — alle sonderingen",
        yaxis=dict(title="Niveau [m NAP]"),
        xaxis=dict(title="Su [kPa]"),
        height=700, template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)
