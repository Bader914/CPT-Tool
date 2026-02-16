import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="CPT Tool", page_icon="📊", layout="wide")

st.title("📊 CPT Tool")
st.markdown("Upload een CPT bestand (CSV of GEF) en bekijk de grafieken.")

# --- Bestand uploaden ---
uploaded_file = st.file_uploader(
    "Kies een CPT bestand", 
    type=["csv", "gef", "xlsx"],
    help="Upload een CSV, GEF of Excel bestand met CPT data"
)

if uploaded_file is not None:
    # Lees het bestand in
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, sep=None, engine="python")
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            st.warning("GEF-bestanden worden binnenkort ondersteund.")
            st.stop()

        st.success(f"✅ Bestand geladen: {uploaded_file.name} ({len(df)} rijen)")

        # --- Data preview ---
        with st.expander("📋 Data preview", expanded=False):
            st.dataframe(df.head(20), use_container_width=True)

        # --- Kolommen selecteren ---
        st.subheader("Kolommen selecteren")
        col1, col2 = st.columns(2)

        with col1:
            diepte_kolom = st.selectbox(
                "Diepte kolom (Y-as)", 
                options=df.columns.tolist(),
                help="Selecteer de kolom met dieptewaarden"
            )

        with col2:
            waarde_kolommen = st.multiselect(
                "Meetwaarde kolommen (X-as)",
                options=[c for c in df.columns if c != diepte_kolom],
                help="Selecteer een of meer kolommen om te plotten"
            )

        # --- Grafiek maken ---
        if waarde_kolommen:
            st.subheader("📈 CPT Grafiek")

            fig = go.Figure()
            for kolom in waarde_kolommen:
                fig.add_trace(go.Scatter(
                    x=df[kolom],
                    y=df[diepte_kolom],
                    mode="lines",
                    name=kolom
                ))

            fig.update_layout(
                yaxis=dict(autorange="reversed", title=diepte_kolom),
                xaxis=dict(title="Meetwaarde"),
                height=700,
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )

            st.plotly_chart(fig, use_container_width=True)

            # --- Download optie ---
            st.download_button(
                label="⬇️ Download gefilterde data als CSV",
                data=df[[diepte_kolom] + waarde_kolommen].to_csv(index=False),
                file_name="cpt_data_gefilterd.csv",
                mime="text/csv"
            )
        else:
            st.info("👆 Selecteer meetwaarde kolommen om een grafiek te maken.")

    except Exception as e:
        st.error(f"Fout bij het inlezen: {e}")
else:
    st.info("👆 Upload een CPT bestand om te beginnen.")

# --- Footer ---
st.markdown("---")
st.caption("CPT Tool v1.0 | Gemaakt met Streamlit")
