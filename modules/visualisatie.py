"""
Module 6: Visualisatie & Rapportage
- Alle sonderingen samen visualiseren
- Bin op NAP-niveau OF op SHZ-grondlaag
- Trends en afwijkende sonderingen
- Export naar CSV/Excel
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io


def render():
    st.caption("Stap 6 — Totaaloverzicht, trends & export")

    su_berekend = {k: v for k, v in st.session_state.get("sonderingen", {}).items()
                    if v.get("su_berekend")}

    if not su_berekend:
        st.markdown("""
        <div class="why-card">
            <h4>⚠️ Su nog niet berekend</h4>
            <p>Ga eerst naar <b>Stap 5 — Su Berekening</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    tab1, tab2, tab3 = st.tabs(["📊 Overzicht", "🔍 Afwijkingen", "📥 Export"])

    with tab1:
        _render_overzicht(su_berekend)
    with tab2:
        _render_afwijkingen(su_berekend)
    with tab3:
        _render_export(su_berekend)


def _render_overzicht(su_berekend: dict):
    st.subheader("Alle Su-profielen")

    col_left, col_right = st.columns([3, 1])

    with col_right:
        bin_modus = st.radio("Gemiddeld per", ["NAP 0.5 m bins", "SHZ-grondlaag"],
                              key="bin_modus", help="Hoe het gemiddelde Su wordt berekend.")
        show_mean = st.checkbox("Toon gemiddelde", value=True)
        show_envelope = st.checkbox("Toon bandbreedte (±1σ)", value=True)
        st.button("📏 Bandbreedte zelf bepalen", disabled=True,
                  help="Toekomstige feature — handmatige bandbreedte per laag.")
        st.button("⚡ Grensspanning ondergrond", disabled=True,
                  help="Toekomstige feature.")

    with col_left:
        fig = go.Figure()

        # Verzamel alle Su data
        all_rows = []
        for name, data in su_berekend.items():
            df = data["df"]
            su_valid = df["Su"].notna()
            if not su_valid.any():
                continue

            sub = df.loc[su_valid, ["Su", "diepte_nap"]].copy()
            if "grondlaag" in df.columns:
                sub["grondlaag"] = df.loc[su_valid, "grondlaag"]
            sub["sondering"] = name
            all_rows.append(sub)

            fig.add_trace(go.Scatter(
                x=sub["Su"], y=sub["diepte_nap"],
                mode="lines", name=name, opacity=0.65,
                hovertemplate=f"<b>{name}</b><br>Su=%{{x:.1f}} kPa<br>NAP %{{y:+.2f}}m<extra></extra>",
            ))

        all_df = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()

        # Gemiddelde + bandbreedte
        caption_extra = ""
        if not all_df.empty and (show_mean or show_envelope):
            if bin_modus == "SHZ-grondlaag" and "grondlaag" in all_df.columns:
                # Per SHZ-grondlaag horizontale balk over diepte-bereik laag
                stats = all_df.groupby("grondlaag")["Su"].agg(["mean", "std", "count"]).reset_index()
                stats = stats[stats["count"] >= 2]
                # Voor plot: gebruik top/onder NAP per laag uit eerste sondering die deze laag heeft
                for _, row in stats.iterrows():
                    laag = row["grondlaag"]
                    z_range = all_df.loc[all_df["grondlaag"] == laag, "diepte_nap"]
                    z_top, z_bot = z_range.max(), z_range.min()
                    if show_mean:
                        fig.add_trace(go.Scatter(
                            x=[row["mean"], row["mean"]], y=[z_top, z_bot],
                            mode="lines", line=dict(color="black", width=3),
                            name=f"Su gem ({laag})", showlegend=False,
                            hovertemplate=f"<b>Laag {laag}</b><br>Su gem=%{{x:.1f}} kPa<br>n={row['count']}<extra></extra>",
                        ))
                    if show_envelope and pd.notna(row["std"]):
                        fig.add_trace(go.Scatter(
                            x=[row["mean"] - row["std"], row["mean"] - row["std"],
                               row["mean"] + row["std"], row["mean"] + row["std"]],
                            y=[z_bot, z_top, z_top, z_bot],
                            fill="toself", fillcolor="rgba(128,128,128,0.15)",
                            line=dict(width=0), name=f"±σ ({laag})", showlegend=False,
                        ))
                caption_extra = "Gemiddelde per SHZ-grondlaag (minimaal 2 sonderingen per laag)."
            else:
                # NAP 0.5 m bins
                all_df["nap_bin"] = (all_df["diepte_nap"] * 2).round() / 2
                stats = all_df.groupby("nap_bin")["Su"].agg(["mean", "std", "count"]).reset_index()
                stats = stats[stats["count"] >= 2]
                if show_mean and not stats.empty:
                    fig.add_trace(go.Scatter(
                        x=stats["mean"], y=stats["nap_bin"],
                        name="Gemiddelde Su", line=dict(color="black", width=3),
                        hovertemplate="Su gem=%{x:.1f} kPa<br>NAP %{y:+.2f}m<extra></extra>",
                    ))
                if show_envelope and not stats.empty:
                    su_upper = stats["mean"] + stats["std"]
                    su_lower = (stats["mean"] - stats["std"]).clip(lower=0)
                    fig.add_trace(go.Scatter(x=su_upper, y=stats["nap_bin"], name="+1σ",
                                              line=dict(color="gray", dash="dot"), showlegend=False))
                    fig.add_trace(go.Scatter(x=su_lower, y=stats["nap_bin"], name="-1σ",
                                              line=dict(color="gray", dash="dot"),
                                              fill="tonextx", fillcolor="rgba(128,128,128,0.10)",
                                              showlegend=False))
                caption_extra = "Gemiddelde per 0.5 m NAP-bin (minimaal 2 sonderingen per bin)."

        # Labdata
        for name, data in su_berekend.items():
            if "lab_data" in data and "lab_mapping" in data:
                lab_df = data["lab_data"]
                lm = data["lab_mapping"]
                y_col = lm.get("nap") or lm.get("diepte")
                fig.add_trace(go.Scatter(
                    x=lab_df[lm["su"]], y=lab_df[y_col],
                    mode="markers", name=f"Lab: {name}",
                    marker=dict(size=11, symbol="diamond", line=dict(width=2, color="black")),
                ))

        fig.update_layout(
            title="Su-profielen — totaaloverzicht",
            yaxis=dict(title="Niveau [m NAP]"),
            xaxis=dict(title="Su [kPa]"),
            height=750, template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)),
        )
        st.plotly_chart(fig, use_container_width=True)

        if caption_extra:
            st.caption(caption_extra)


def _render_afwijkingen(su_berekend: dict):
    st.subheader("Afwijkende Sonderingen Identificeren")

    if len(su_berekend) < 2:
        st.info("Minimaal 2 sonderingen nodig voor vergelijking.")
        return

    su_summary = []
    for name, data in su_berekend.items():
        df = data["df"]
        su_valid = df["Su"].notna()
        if not su_valid.any():
            continue
        su_summary.append({
            "Sondering": name,
            "Su gemiddeld [kPa]": round(df.loc[su_valid, "Su"].mean(), 1),
            "Su mediaan [kPa]": round(df.loc[su_valid, "Su"].median(), 1),
            "Su std [kPa]": round(df.loc[su_valid, "Su"].std(), 1),
            "Metingen": int(su_valid.sum()),
        })

    if not su_summary:
        return

    summary_df = pd.DataFrame(su_summary)
    global_mean = summary_df["Su gemiddeld [kPa]"].mean()
    global_std = summary_df["Su gemiddeld [kPa]"].std()

    summary_df["Afwijking"] = summary_df["Su gemiddeld [kPa]"].apply(
        lambda x: "⚠️ Afwijkend" if abs(x - global_mean) > 1.5 * global_std else "✅ Normaal"
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    fig = go.Figure()
    for name, data in su_berekend.items():
        df = data["df"]
        su_valid = df["Su"].notna()
        if su_valid.any():
            fig.add_trace(go.Box(y=df.loc[su_valid, "Su"], name=name))
    fig.update_layout(title="Su-verdeling per sondering", yaxis=dict(title="Su [kPa]"),
                       height=500, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


def _render_export(su_berekend: dict):
    st.subheader("Data Exporteren")
    export_format = st.radio("Export formaat", ["CSV", "Excel"], horizontal=True)

    all_export = []
    for name, data in su_berekend.items():
        df = data["df"]
        cm = data["col_mapping"]
        cols = {"Sondering": name}
        if cm.get("diepte") and cm["diepte"] in df.columns:
            cols["Diepte [m]"] = df[cm["diepte"]]
        if "diepte_nap" in df.columns:
            cols["Niveau [m NAP]"] = df["diepte_nap"]
        if "grondlaag" in df.columns:
            cols["Grondlaag"] = df["grondlaag"]
        for col_in, col_out in [(cm.get("qc"), "qc [MPa]"),
                                  ("qt", "qt [MPa]"),
                                  (cm.get("fs"), "fs [MPa]"),
                                  ("Rf", "Rf [%]"),
                                  (cm.get("u2"), "u2 [MPa]"),
                                  ("u0", "u0 [MPa]"),
                                  ("sigma_v0", "sigma_v0 [MPa]"),
                                  ("sigma_v0_eff", "sigma_v0_eff [MPa]"),
                                  ("q_net", "q_net [MPa]"),
                                  ("Nkt_gebruikt", "Nkt"),
                                  ("Su", "Su [kPa]")]:
            if col_in and col_in in df.columns:
                cols[col_out] = df[col_in]
        all_export.append(pd.DataFrame(cols))

    if not all_export:
        return

    combined = pd.concat(all_export, ignore_index=True)
    st.markdown(f"**Totaal:** {len(combined)} rijen, {combined['Sondering'].nunique()} sonderingen")
    with st.expander("📋 Preview"):
        st.dataframe(combined.head(50), use_container_width=True)

    if export_format == "CSV":
        st.download_button("⬇️ Download CSV", data=combined.to_csv(index=False),
                            file_name="cpt_su_resultaten.csv", mime="text/csv")
    else:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            combined.to_excel(writer, index=False, sheet_name="Resultaten")
        st.download_button("⬇️ Download Excel", data=buffer.getvalue(),
                            file_name="cpt_su_resultaten.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
