import streamlit as st

st.set_page_config(
    page_title="CPT Su Tool | HHSK",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Wachtwoordbeveiliging ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 CPT Su Tool")
    st.caption("Dijkmateriaal & Ongedraineerde Schuifsterkte")
    pwd = st.text_input("Voer het wachtwoord in:", type="password")
    if st.button("Login"):
        if pwd == st.secrets.get("password", ""):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Onjuist wachtwoord")
    st.stop()

# --- Navigatie ---
from modules import uitgangspunten, data_inladen, normalisatie, classificatie, su_berekening, validatie, visualisatie

PAGES = {
    "📋 0. Uitgangspunten": uitgangspunten,
    "📁 1. Data Inladen & Controle": data_inladen,
    "📐 2. Normalisatie (Qt)": normalisatie,
    "🧱 3. Classificatie & Materiaal": classificatie,
    "📊 4. Su Berekening": su_berekening,
    "✅ 5. Validatie & Labvergelijking": validatie,
    "📈 6. Visualisatie & Rapportage": visualisatie,
}

st.sidebar.title("🔬 CPT Su Tool")
st.sidebar.caption("v2.0")
st.sidebar.markdown("---")

selection = st.sidebar.radio("Module", list(PAGES.keys()))

# Toon status in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**Data status:**")
n_sonderingen = len(st.session_state.get("sonderingen", {}))
st.sidebar.info(f"{n_sonderingen} sondering(en) geladen")

# Render geselecteerde pagina
PAGES[selection].render()
