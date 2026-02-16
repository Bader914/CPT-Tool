import streamlit as st

st.set_page_config(
    page_title="CPT Su Tool | HHSK",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Modern CSS Styling v5.1 ──
st.markdown("""
<style>
/* === FONTS === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }

/* === DARK THEME === */
[data-testid="stAppViewContainer"] { background: #0a0e1a; color: #e2e8f0; }
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] span, [data-testid="stAppViewContainer"] label { color: #cbd5e1 !important; }
[data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3, [data-testid="stAppViewContainer"] h4 { color: #f1f5f9 !important; }
[data-testid="stHeader"] { background: rgba(10, 14, 26, 0.9) !important; backdrop-filter: blur(10px); }

/* Hide sidebar */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* === REDUCE ALL PADDING === */
.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; }

/* === HORIZONTAL RADIO as pill nav === */
[data-testid="stRadio"] > div { gap: 0 !important; }
[data-testid="stRadio"] [role="radiogroup"] {
    gap: 3px !important; background: rgba(15, 23, 42, 0.8);
    border-radius: 12px; padding: 3px; border: 1px solid rgba(99, 102, 241, 0.12);
    backdrop-filter: blur(12px);
}
[data-testid="stRadio"] [role="radiogroup"] label {
    border-radius: 9px !important; padding: 6px 12px !important;
    margin: 0 !important; font-size: 0.78rem !important; font-weight: 500;
    color: #64748b !important; transition: all 0.2s ease;
    white-space: nowrap;
}
[data-testid="stRadio"] [role="radiogroup"] label:hover {
    background: rgba(99, 102, 241, 0.1) !important; color: #a5b4fc !important;
}
[data-testid="stRadio"] [role="radiogroup"] label[data-checked="true"],
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important; box-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
}
/* Hide radio circles */
[data-testid="stRadio"] [role="radiogroup"] label > div:first-child { display: none !important; }
[data-testid="stRadio"] [role="radiogroup"] label p { font-size: 0.78rem !important; margin: 0; }

/* === WHY CARD === */
.why-card {
    background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1rem;
    border-left: 3px solid #6366f1;
}
.why-card h4 { color: #818cf8 !important; font-size: 0.82rem; font-weight: 700;
    margin: 0 0 0.4rem 0; text-transform: uppercase; letter-spacing: 0.05em; }
.why-card p { color: #cbd5e1 !important; font-size: 0.85rem; line-height: 1.5; margin: 0 0 0.3rem 0; }

/* === NEXT-STEP === */
.next-step {
    background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.25);
    border-radius: 12px; padding: 0.8rem 1.2rem; margin-top: 1rem;
    display: flex; align-items: center; gap: 10px;
}
.next-step .arrow { font-size: 1.2rem; color: #22c55e; }
.next-step p { color: #86efac !important; margin: 0; font-weight: 500; font-size: 0.88rem; }
.next-step b { color: #4ade80 !important; }

/* === METRIC CARDS === */
[data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 12px;
    padding: 14px 18px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}
[data-testid="stMetric"] label { color: #818cf8 !important; font-size: 0.7rem !important;
    font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #f1f5f9 !important;
    font-weight: 800 !important; font-size: 1.4rem !important; }

/* === TABS === */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 2px; background: rgba(30, 41, 59, 0.4); border-radius: 12px;
    padding: 3px; border: 1px solid rgba(99, 102, 241, 0.12);
}
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 9px !important;
    font-weight: 500; padding: 8px 16px; color: #94a3b8 !important; font-size: 0.85rem; }
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(99, 102, 241, 0.18) !important; color: #c7d2fe !important; }

/* === EXPANDERS (compact) === */
[data-testid="stExpander"] { background: rgba(30, 41, 59, 0.35) !important;
    border: 1px solid rgba(99, 102, 241, 0.12) !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary { font-weight: 600; color: #c7d2fe !important; }
[data-testid="stExpander"] summary span { color: #c7d2fe !important; }

/* === BUTTONS === */
.stButton > button { border-radius: 10px !important; font-weight: 600;
    padding: 0.55rem 1.5rem; transition: all 0.2s ease; border: none !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3); }
.stButton > button:hover { transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important; }

/* === DATAFRAMES === */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden;
    border: 1px solid rgba(99, 102, 241, 0.12); }

/* === FILE UPLOADER === */
[data-testid="stFileUploader"] { background: rgba(30, 41, 59, 0.25);
    border: 2px dashed rgba(99, 102, 241, 0.25) !important; border-radius: 12px; padding: 0.8rem; }
[data-testid="stFileUploader"]:hover { border-color: rgba(99, 102, 241, 0.5) !important; }

/* === INPUTS === */
[data-testid="stSelectbox"] > div > div, [data-testid="stNumberInput"] > div > div > input,
[data-testid="stTextInput"] > div > div > input {
    background: rgba(30, 41, 59, 0.5) !important; border: 1px solid rgba(99, 102, 241, 0.15) !important;
    border-radius: 8px !important; color: #e2e8f0 !important; }
[data-testid="stNumberInput"] label, [data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label, [data-testid="stFileUploader"] label {
    color: #a5b4fc !important; font-weight: 500; font-size: 0.85rem; }

/* === ALERTS === */
[data-testid="stAlert"] { border-radius: 10px !important; border: none !important; }

/* === TABLES === */
[data-testid="stAppViewContainer"] table { background: rgba(30, 41, 59, 0.35);
    border-radius: 10px; overflow: hidden; border-collapse: collapse; width: 100%; }
[data-testid="stAppViewContainer"] th { background: rgba(99, 102, 241, 0.12) !important;
    color: #c7d2fe !important; padding: 8px 12px; font-weight: 600; font-size: 0.82rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.15); }
[data-testid="stAppViewContainer"] td { color: #cbd5e1 !important; padding: 7px 12px;
    border-bottom: 1px solid rgba(99, 102, 241, 0.06); font-size: 0.85rem; }

/* === DIVIDERS & SCROLLBAR === */
[data-testid="stAppViewContainer"] hr { border-color: rgba(99, 102, 241, 0.1) !important; margin: 0.8rem 0; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

/* Reduce subheader margins */
[data-testid="stAppViewContainer"] h2 { margin-top: 0.5rem !important; margin-bottom: 0.3rem !important; font-size: 1.1rem !important; }
[data-testid="stAppViewContainer"] h3 { margin-top: 0.3rem !important; margin-bottom: 0.2rem !important; font-size: 1rem !important; }
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

STEPS = [
    {"module": uitgangspunten, "icon": "⚙️", "label": "Parameters", "full": "Uitgangspunten"},
    {"module": data_inladen, "icon": "📁", "label": "Upload", "full": "Data Inladen"},
    {"module": normalisatie, "icon": "📐", "label": "Normalisatie", "full": "Normalisatie"},
    {"module": classificatie, "icon": "🧱", "label": "Classificatie", "full": "Classificatie"},
    {"module": su_berekening, "icon": "📊", "label": "Su", "full": "Su Berekening"},
    {"module": validatie, "icon": "✅", "label": "Validatie", "full": "Validatie"},
    {"module": visualisatie, "icon": "📈", "label": "Rapportage", "full": "Rapportage"},
]

if "current_step" not in st.session_state:
    st.session_state.current_step = 0

# === Determine step completion ===
n_sond = len(st.session_state.get("sonderingen", {}))
has_norm = any(v.get("genormaliseerd") for v in st.session_state.get("sonderingen", {}).values())
has_class = any(v.get("geclassificeerd") for v in st.session_state.get("sonderingen", {}).values())
has_su = any(v.get("su_berekend") for v in st.session_state.get("sonderingen", {}).values())

step_done = [
    "uitgangspunten" in st.session_state,   # 0
    n_sond > 0,                              # 1
    has_norm,                                # 2
    has_class,                               # 3
    has_su,                                  # 4
    False,                                   # 5
    False,                                   # 6
]

su_count = sum(1 for v in st.session_state.get("sonderingen", {}).values() if v.get("su_berekend"))

# === BUILD RADIO LABELS with status icons ===
radio_labels = []
for i, s in enumerate(STEPS):
    check = "✅" if step_done[i] else f"{i}"
    radio_labels.append(f"{check}  {s['icon']} {s['label']}")

active = st.session_state.current_step

# === SINGLE NAV ROW: brand + radio + stats ===
nav_left, nav_mid, nav_right = st.columns([1.5, 8, 1.5])
with nav_left:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; padding:4px 0;">
        <span style="font-size:1.3rem; filter:drop-shadow(0 0 8px rgba(99,102,241,0.5));">🔬</span>
        <span style="font-weight:800; font-size:0.9rem;
            background:linear-gradient(135deg,#c7d2fe,#818cf8);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">CPT Su Tool</span>
    </div>
    """, unsafe_allow_html=True)
with nav_mid:
    selection = st.radio(
        "nav", radio_labels, index=active,
        horizontal=True, label_visibility="collapsed",
        key="step_radio"
    )
    # Sync back
    new_step = radio_labels.index(selection)
    if new_step != active:
        st.session_state.current_step = new_step
        st.rerun()
with nav_right:
    st.markdown(f"""
    <div style="display:flex; gap:16px; justify-content:flex-end; padding:6px 0;">
        <div style="text-align:center;">
            <div style="font-size:1.1rem; font-weight:800; color:#c7d2fe;">{n_sond}</div>
            <div style="font-size:0.55rem; color:#64748b; text-transform:uppercase; letter-spacing:0.08em;">CPT's</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:1.1rem; font-weight:800; color:#c7d2fe;">{su_count}</div>
            <div style="font-size:0.55rem; color:#64748b; text-transform:uppercase; letter-spacing:0.08em;">Su</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# === MAIN CONTENT ===
active = st.session_state.current_step
STEPS[active]["module"].render()
