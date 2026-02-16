import streamlit as st

st.set_page_config(
    page_title="CPT Su Tool | HHSK",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Modern CSS Styling v4.0 ──
st.markdown("""
<style>
/* === FONTS === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; }

/* === DARK THEME MAIN AREA === */
[data-testid="stAppViewContainer"] {
    background: #0a0e1a;
    color: #e2e8f0;
}

[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] label {
    color: #cbd5e1 !important;
}

[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
    color: #f1f5f9 !important;
}

[data-testid="stHeader"] {
    background: rgba(10, 14, 26, 0.8) !important;
    backdrop-filter: blur(10px);
}

/* === SIDEBAR === */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1321 0%, #141b2d 50%, #0d1321 100%) !important;
    border-right: 1px solid rgba(99, 102, 241, 0.15);
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
[data-testid="stSidebar"] [data-testid="stMarkdown"] li,
[data-testid="stSidebar"] label {
    color: #94a3b8 !important;
    font-size: 0.88rem;
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: #e2e8f0 !important;
}

/* Sidebar radio buttons - modern pill style */
[data-testid="stSidebar"] [role="radiogroup"] label {
    border-radius: 10px !important;
    padding: 6px 12px !important;
    margin: 2px 0 !important;
    transition: all 0.2s ease;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(99, 102, 241, 0.1) !important;
}

[data-testid="stSidebar"] [role="radiogroup"] [data-checked="true"] ~ label,
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
    background: rgba(99, 102, 241, 0.15) !important;
    border-left: 3px solid #6366f1 !important;
}

/* === METRIC CARDS — Glass morphism === */
[data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.6) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

[data-testid="stMetric"] label {
    color: #818cf8 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-weight: 800 !important;
    font-size: 1.6rem !important;
}

/* === TABS === */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 2px;
    background: rgba(30, 41, 59, 0.5);
    border-radius: 14px;
    padding: 4px;
    border: 1px solid rgba(99, 102, 241, 0.15);
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 500;
    padding: 10px 18px;
    color: #94a3b8 !important;
}

[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(99, 102, 241, 0.2) !important;
    color: #c7d2fe !important;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

/* === EXPANDERS === */
[data-testid="stExpander"] {
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid rgba(99, 102, 241, 0.15) !important;
    border-radius: 14px !important;
    overflow: hidden;
}

[data-testid="stExpander"] summary {
    font-weight: 600;
    color: #c7d2fe !important;
}

[data-testid="stExpander"] summary span {
    color: #c7d2fe !important;
}

/* === BUTTONS === */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600;
    padding: 0.6rem 1.8rem;
    transition: all 0.25s ease;
    border: none !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="stFormSubmitButton"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
}

/* === DATAFRAMES === */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(99, 102, 241, 0.15);
}

/* === FILE UPLOADER === */
[data-testid="stFileUploader"] {
    background: rgba(30, 41, 59, 0.3);
    border: 2px dashed rgba(99, 102, 241, 0.3) !important;
    border-radius: 14px;
    padding: 1rem;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(99, 102, 241, 0.6) !important;
    background: rgba(30, 41, 59, 0.5);
}

/* === SELECTBOX & INPUTS === */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] > div > div > input,
[data-testid="stTextInput"] > div > div > input {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

/* === ALERTS === */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: none !important;
}

/* === HERO SECTION === */
.hero-section {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 30%, #4338ca 60%, #6366f1 100%);
    border-radius: 20px;
    padding: 3rem 2.5rem;
    color: white;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(99, 102, 241, 0.3);
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
    border-radius: 50%;
}

.hero-section .step-label {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    color: #c7d2fe;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.8rem;
    backdrop-filter: blur(4px);
}

.hero-section h1 {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    margin: 0 0 0.4rem 0 !important;
    color: white !important;
    position: relative;
}

.hero-section .subtitle {
    color: #c7d2fe;
    font-size: 1.05rem;
    margin: 0;
    position: relative;
    opacity: 0.9;
}

/* === WHY-CARD (uitleg blokken) === */
.why-card {
    background: rgba(30, 41, 59, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}

.why-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, #6366f1, #8b5cf6);
    border-radius: 4px 0 0 4px;
}

.why-card h4 {
    color: #818cf8 !important;
    font-size: 0.95rem;
    font-weight: 700;
    margin: 0 0 0.6rem 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.why-card p {
    color: #cbd5e1 !important;
    font-size: 0.92rem;
    line-height: 1.6;
    margin: 0 0 0.5rem 0;
}

.why-card .tip {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    background: rgba(99, 102, 241, 0.1);
    border-radius: 10px;
    padding: 10px 14px;
    margin-top: 0.8rem;
}

.why-card .tip p {
    color: #a5b4fc !important;
    font-size: 0.85rem;
    margin: 0;
}

/* === NEXT-STEP CARD === */
.next-step {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin-top: 1.5rem;
    display: flex;
    align-items: center;
    gap: 12px;
}

.next-step .arrow {
    font-size: 1.5rem;
    color: #22c55e;
}

.next-step p {
    color: #86efac !important;
    margin: 0;
    font-weight: 500;
}

.next-step b {
    color: #4ade80 !important;
}

/* === RESULT CARD === */
.result-card {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.result-card h3 {
    color: #e2e8f0 !important;
    font-size: 1.1rem;
    margin: 0 0 1rem 0;
}

/* === STATUS PILL === */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.status-ready { background: rgba(34, 197, 94, 0.15); color: #86efac; }
.status-warning { background: rgba(251, 191, 36, 0.15); color: #fde68a; }
.status-error { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }

/* === TABLE INSIDE MARKDOWN === */
[data-testid="stAppViewContainer"] table {
    background: rgba(30, 41, 59, 0.4);
    border-radius: 12px;
    overflow: hidden;
    border-collapse: collapse;
    width: 100%;
}

[data-testid="stAppViewContainer"] th {
    background: rgba(99, 102, 241, 0.15) !important;
    color: #c7d2fe !important;
    padding: 10px 14px;
    font-weight: 600;
    font-size: 0.85rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
}

[data-testid="stAppViewContainer"] td {
    color: #cbd5e1 !important;
    padding: 8px 14px;
    border-bottom: 1px solid rgba(99, 102, 241, 0.08);
    font-size: 0.88rem;
}

/* === DIVIDERS === */
[data-testid="stAppViewContainer"] hr {
    border-color: rgba(99, 102, 241, 0.12) !important;
    margin: 1.5rem 0;
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

/* Legacy hero-container support */
.hero-container {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 30%, #4338ca 60%, #6366f1 100%);
    border-radius: 20px;
    padding: 3rem 2.5rem;
    color: white;
    margin-bottom: 2rem;
    border: 1px solid rgba(99, 102, 241, 0.3);
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
}

.hero-container h1 {
    font-size: 2.2rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
    color: white !important;
}

.hero-container p {
    color: #c7d2fe;
    font-size: 1.05rem;
}

/* === NUMBER INPUT LABELS === */
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label,
[data-testid="stFileUploader"] label {
    color: #a5b4fc !important;
    font-weight: 500;
    font-size: 0.88rem;
}
</style>
""", unsafe_allow_html=True)


# --- Wachtwoordbeveiliging ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 4rem; margin-bottom: 0.5rem; 
                 filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.5));">🔬</div>
            <h1 style="font-size: 2rem; font-weight: 800; 
                 background: linear-gradient(135deg, #c7d2fe, #818cf8);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 margin-bottom: 0.3rem;">
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
        <p style="text-align: center; color: #475569; font-size: 0.8rem; margin-top: 2rem;">
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
    <div style="text-align: center; padding: 1.2rem 0;">
        <div style="font-size: 2.2rem; filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.4));">🔬</div>
        <h2 style="margin: 0.4rem 0 0 0; font-size: 1.2rem; 
             background: linear-gradient(135deg, #c7d2fe, #818cf8);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;
             font-weight: 800;">CPT Su Tool</h2>
        <p style="margin: 0; font-size: 0.7rem; letter-spacing: 0.12em; 
             text-transform: uppercase; color: #475569 !important;">
            v4.0 &middot; HHSK
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
    
    st.markdown("""
    <p style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; 
       letter-spacing: 0.12em; color: #6366f1 !important; margin-bottom: 0.6rem;">
       Workflow Voortgang
    </p>
    """, unsafe_allow_html=True)
    
    for i, (label, done) in enumerate(steps_status):
        if done:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:10px; padding: 4px 0;">
                <div style="width:24px; height:24px; border-radius:50%; 
                     background:linear-gradient(135deg, #22c55e, #16a34a); 
                     display:flex; align-items:center; justify-content:center;
                     font-size:0.7rem; color:white; font-weight:700; flex-shrink:0;
                     box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);">✓</div>
                <span style="color:#86efac !important; font-size:0.82rem; font-weight:500;">{label}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:10px; padding: 4px 0;">
                <div style="width:24px; height:24px; border-radius:50%; 
                     background:rgba(51, 65, 85, 0.5); border: 1px solid #334155;
                     display:flex; align-items:center; justify-content:center;
                     font-size:0.65rem; color:#475569; font-weight:700; flex-shrink:0;">{i}</div>
                <span style="color:#475569 !important; font-size:0.82rem;">{label}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Data status
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sonderingen", n_sond)
    with col2:
        su_count = sum(1 for v in st.session_state.get("sonderingen", {}).values() if v.get("su_berekend"))
        st.metric("Su berekend", su_count)
    
    st.markdown("""
    <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(51, 65, 85, 0.5); text-align: center;">
        <p style="font-size: 0.7rem; color: #334155 !important; margin: 0;">
            Aqlomate © 2026
        </p>
    </div>
    """, unsafe_allow_html=True)


# === MAIN CONTENT ===
page_info = PAGES[selection]
page_info["module"].render()
