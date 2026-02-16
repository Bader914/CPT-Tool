import streamlit as st

st.set_page_config(
    page_title="CPT Su Tool | HHSK",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Modern CSS Styling ──
st.markdown("""
<style>
/* === GLOBAL THEME === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

[data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
}

/* === SIDEBAR === */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
[data-testid="stSidebar"] [data-testid="stMarkdown"] li,
[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
}

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #f1f5f9 !important;
}

/* === METRIC CARDS === */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

[data-testid="stMetric"] label {
    color: #64748b !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-weight: 700 !important;
}

/* === TABS === */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f1f5f9;
    border-radius: 12px;
    padding: 4px;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500;
    padding: 8px 16px;
}

[data-testid="stTabs"] [aria-selected="true"] {
    background: white !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* === EXPANDERS === */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    overflow: hidden;
}

[data-testid="stExpander"] summary {
    font-weight: 500;
}

/* === BUTTONS === */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* === DATAFRAMES === */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* === HERO SECTION === */
.hero-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0ea5e9 100%);
    border-radius: 16px;
    padding: 2.5rem;
    color: white;
    margin-bottom: 1.5rem;
}

.hero-container h1 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: white !important;
}

.hero-container p {
    color: #94a3b8;
    font-size: 1.05rem;
}

/* === INFO CARDS === */
.info-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: all 0.2s ease;
}

.info-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}

.info-card h4 {
    margin: 0 0 0.3rem 0;
    color: #0f172a;
    font-size: 0.95rem;
}

.info-card p {
    margin: 0;
    color: #64748b;
    font-size: 0.85rem;
}

/* === PROGRESS STEPS === */
.step-badge {
    display: inline-block;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    text-align: center;
    line-height: 28px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-right: 8px;
}

.step-done { background: #22c55e; color: white; }
.step-active { background: #3b82f6; color: white; }
.step-todo { background: #334155; color: #94a3b8; }

/* === LOGIN PAGE === */
.login-box {
    max-width: 400px;
    margin: auto;
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
}

/* === SECTION HEADERS === */
.section-header {
    background: linear-gradient(90deg, #f1f5f9, transparent);
    border-left: 3px solid #3b82f6;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: 1.5rem 0 1rem 0;
}

.section-header h3 {
    margin: 0;
    font-size: 1.1rem;
    color: #0f172a;
}
</style>
""", unsafe_allow_html=True)


# --- Wachtwoordbeveiliging ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br>" * 2, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🔬</div>
            <h1 style="font-size: 1.8rem; font-weight: 700; color: #0f172a; margin-bottom: 0.3rem;">
                CPT Su Tool
            </h1>
            <p style="color: #64748b; font-size: 0.95rem;">
                HHSK Dijkversterking — Traject 14-1
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        pwd = st.text_input("Wachtwoord", type="password", label_visibility="collapsed",
                           placeholder="Voer wachtwoord in...")
        
        if st.button("Inloggen", use_container_width=True, type="primary"):
            if pwd == st.secrets.get("password", ""):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Onjuist wachtwoord")
        
        st.markdown("""
        <p style="text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 2rem;">
            Aqlomate &middot; Geotechnische Automatisering
        </p>
        """, unsafe_allow_html=True)
    
    st.stop()


# --- Navigatie ---
from modules import uitgangspunten, data_inladen, normalisatie, classificatie, su_berekening, validatie, visualisatie

PAGES = {
    "📋 Stap 0 — Uitgangspunten": {"module": uitgangspunten, "step": 0, "short": "Parameters"},
    "📁 Stap 1 — Data Inladen": {"module": data_inladen, "step": 1, "short": "Upload"},
    "📐 Stap 2 — Normalisatie": {"module": normalisatie, "step": 2, "short": "Qt correctie"},
    "🧱 Stap 3 — Classificatie": {"module": classificatie, "step": 3, "short": "Grondtype"},
    "📊 Stap 4 — Su Berekening": {"module": su_berekening, "step": 4, "short": "Su = qnet/Nkt"},
    "✅ Stap 5 — Validatie": {"module": validatie, "step": 5, "short": "Lab check"},
    "📈 Stap 6 — Rapportage": {"module": visualisatie, "step": 6, "short": "Export"},
}


# === SIDEBAR ===
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <span style="font-size: 2rem;">🔬</span>
        <h2 style="margin: 0.3rem 0 0 0; font-size: 1.3rem;">CPT Su Tool</h2>
        <p style="margin: 0; font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.6;">
            v3.0 &middot; HHSK
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    selection = st.radio(
        "Module", 
        list(PAGES.keys()), 
        label_visibility="collapsed",
        format_func=lambda x: x
    )
    
    # --- Workflow Progress ---
    st.markdown("---")
    
    n_sond = len(st.session_state.get("sonderingen", {}))
    has_norm = any(v.get("genormaliseerd") for v in st.session_state.get("sonderingen", {}).values())
    has_class = any(v.get("geclassificeerd") for v in st.session_state.get("sonderingen", {}).values())
    has_su = any(v.get("su_berekend") for v in st.session_state.get("sonderingen", {}).values())
    
    steps_status = [
        ("Uitgangspunten", "uitgangspunten" in st.session_state),
        ("Data geladen", n_sond > 0),
        ("Genormaliseerd", has_norm),
        ("Geclassificeerd", has_class),
        ("Su berekend", has_su),
    ]
    
    st.markdown("**Workflow Voortgang**")
    for i, (label, done) in enumerate(steps_status):
        icon = "✅" if done else "⬜"
        style = "opacity: 1.0;" if done else "opacity: 0.6;"
        st.markdown(f"<span style='{style}'>{icon} Stap {i}: {label}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Data status
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sonderingen", n_sond)
    with col2:
        su_count = sum(1 for v in st.session_state.get("sonderingen", {}).values() if v.get("su_berekend"))
        st.metric("Su berekend", su_count)
    
    st.markdown("""
    <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #334155; text-align: center;">
        <p style="font-size: 0.7rem; opacity: 0.4; margin: 0;">
            Aqlomate © 2026
        </p>
    </div>
    """, unsafe_allow_html=True)


# === MAIN CONTENT ===
page_info = PAGES[selection]
page_info["module"].render()
