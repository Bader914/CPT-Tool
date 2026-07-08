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
body, p, label, h1, h2, h3, h4, h5, h6, div, input, button, select, textarea, td, th, li, a {
    font-family: 'Inter', sans-serif !important;
}

/* === FIX EXPANDER ICON — replace broken Material Icon with CSS arrow === */
[data-testid="stExpanderToggleIcon"] {
    font-size: 0 !important;
    width: 1rem !important;
    height: 1rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stExpanderToggleIcon"]::before {
    content: "\\203A" !important;
    font-size: 1.4rem !important;
    font-family: 'Inter', sans-serif !important;
    color: #78909c !important;
    line-height: 1 !important;
}

/* === DARK BLUE/BLACK THEME === */
[data-testid="stAppViewContainer"] { background: #04080f; color: #e3f2fd; }
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] span:not([data-testid="stExpanderToggleIcon"]),
[data-testid="stAppViewContainer"] label { color: #bbdefb !important; }
[data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3, [data-testid="stAppViewContainer"] h4 { color: #e3f2fd !important; }
[data-testid="stHeader"] { background: rgba(4, 8, 15, 0.92) !important; backdrop-filter: blur(10px); }

/* Hide sidebar */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* === REDUCE ALL PADDING === */
.block-container { padding-top: 3.5rem !important; padding-bottom: 0 !important; }

/* === HORIZONTAL RADIO as pill nav === */
[data-testid="stRadio"] > div { gap: 0 !important; }
[data-testid="stRadio"] [role="radiogroup"] {
    gap: 3px !important; background: rgba(6, 17, 38, 0.85);
    border-radius: 12px; padding: 3px; border: 1px solid rgba(30, 136, 229, 0.15);
    backdrop-filter: blur(12px);
}
[data-testid="stRadio"] [role="radiogroup"] label {
    border-radius: 9px !important; padding: 6px 12px !important;
    margin: 0 !important; font-size: 0.78rem !important; font-weight: 500;
    color: #546e7a !important; transition: all 0.2s ease;
    white-space: nowrap;
}
[data-testid="stRadio"] [role="radiogroup"] label:hover {
    background: rgba(30, 136, 229, 0.12) !important; color: #90caf9 !important;
}
[data-testid="stRadio"] [role="radiogroup"] label[data-checked="true"],
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, #0d47a1, #1e88e5) !important;
    color: white !important; box-shadow: 0 2px 10px rgba(30, 136, 229, 0.35);
}
/* Hide radio circles */
[data-testid="stRadio"] [role="radiogroup"] label > div:first-child { display: none !important; }
[data-testid="stRadio"] [role="radiogroup"] label p { font-size: 0.78rem !important; margin: 0; }

/* === WHY CARD === */
.why-card {
    background: rgba(8, 22, 48, 0.6); border: 1px solid rgba(30, 136, 229, 0.18);
    border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1rem;
    border-left: 3px solid #1e88e5;
}
.why-card h4 { color: #64b5f6 !important; font-size: 0.82rem; font-weight: 700;
    margin: 0 0 0.4rem 0; text-transform: uppercase; letter-spacing: 0.05em; }
.why-card p { color: #bbdefb !important; font-size: 0.85rem; line-height: 1.5; margin: 0 0 0.3rem 0; }

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
    background: rgba(8, 22, 48, 0.55) !important;
    border: 1px solid rgba(30, 136, 229, 0.18); border-radius: 12px;
    padding: 14px 18px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}
[data-testid="stMetric"] label { color: #64b5f6 !important; font-size: 0.7rem !important;
    font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #e3f2fd !important;
    font-weight: 800 !important; font-size: 1.4rem !important; }

/* === TABS === */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 2px; background: rgba(8, 22, 48, 0.45); border-radius: 12px;
    padding: 3px; border: 1px solid rgba(30, 136, 229, 0.15);
}
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 9px !important;
    font-weight: 500; padding: 8px 16px; color: #78909c !important; font-size: 0.85rem; }
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(30, 136, 229, 0.2) !important; color: #90caf9 !important; }

/* === EXPANDERS === */
[data-testid="stExpander"] { background: rgba(8, 22, 48, 0.4) !important;
    border: 1px solid rgba(30, 136, 229, 0.15) !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary { font-weight: 600; color: #90caf9 !important; }
[data-testid="stExpander"] summary > span:not([data-testid="stExpanderToggleIcon"]) { color: #90caf9 !important; }

/* === BUTTONS === */
.stButton > button { border-radius: 10px !important; font-weight: 600;
    padding: 0.55rem 1.5rem; transition: all 0.2s ease; border: none !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0d47a1 0%, #1e88e5 100%) !important;
    color: white !important; box-shadow: 0 4px 15px rgba(30, 136, 229, 0.35); }
.stButton > button:hover { transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(30, 136, 229, 0.4) !important; }

/* === DATAFRAMES === */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden;
    border: 1px solid rgba(30, 136, 229, 0.15); }

/* === FILE UPLOADER === */
[data-testid="stFileUploader"] { background: rgba(8, 22, 48, 0.3);
    border: 2px dashed rgba(30, 136, 229, 0.28) !important; border-radius: 12px; padding: 0.8rem; }
[data-testid="stFileUploader"]:hover { border-color: rgba(30, 136, 229, 0.55) !important; }

/* === INPUTS === */
[data-testid="stSelectbox"] > div > div, [data-testid="stNumberInput"] > div > div > input,
[data-testid="stTextInput"] > div > div > input {
    background: rgba(8, 22, 48, 0.55) !important; border: 1px solid rgba(30, 136, 229, 0.18) !important;
    border-radius: 8px !important; color: #e3f2fd !important; }
[data-testid="stNumberInput"] label, [data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label, [data-testid="stFileUploader"] label {
    color: #90caf9 !important; font-weight: 500; font-size: 0.85rem; }

/* === ALERTS === */
[data-testid="stAlert"] { border-radius: 10px !important; border: none !important; }

/* === TABLES === */
[data-testid="stAppViewContainer"] table { background: rgba(8, 22, 48, 0.4);
    border-radius: 10px; overflow: hidden; border-collapse: collapse; width: 100%; }
[data-testid="stAppViewContainer"] th { background: rgba(30, 136, 229, 0.14) !important;
    color: #90caf9 !important; padding: 8px 12px; font-weight: 600; font-size: 0.82rem;
    border-bottom: 1px solid rgba(30, 136, 229, 0.18); }
[data-testid="stAppViewContainer"] td { color: #bbdefb !important; padding: 7px 12px;
    border-bottom: 1px solid rgba(30, 136, 229, 0.08); font-size: 0.85rem; }

/* === DIVIDERS & SCROLLBAR === */
[data-testid="stAppViewContainer"] hr { border-color: rgba(30, 136, 229, 0.12) !important; margin: 0.8rem 0; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #04080f; }
::-webkit-scrollbar-thumb { background: #1a3a5c; border-radius: 3px; }

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
                 filter: drop-shadow(0 0 20px rgba(30, 136, 229, 0.5));">🔬</div>
            <h1 style="font-size: 2rem; font-weight: 800; 
                 background: linear-gradient(135deg, #90caf9, #1e88e5);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 margin-bottom: 0.3rem;">
                CPT Su Tool
            </h1>
            <p style="color: #546e7a; font-size: 0.95rem;">
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
    {"module": classificatie, "icon": "🧱", "label": "Classificatie", "full": "Classificatie"},
    {"module": normalisatie, "icon": "📐", "label": "Normalisatie", "full": "Normalisatie"},
    {"module": su_berekening, "icon": "📊", "label": "Su", "full": "Su Berekening"},
    # Voorlopig geblokkeerd: de tool stopt na de Su-berekening. Validatie met
    # triaxiaalproeven en de rapportage worden later vrijgegeven.
    {"module": validatie, "icon": "✅", "label": "Validatie", "full": "Validatie",
     "locked": "Validatie met triaxiaalproeven (Nkt-kalibratie) volgt later."},
    {"module": visualisatie, "icon": "📈", "label": "Rapportage", "full": "Rapportage",
     "locked": "Rapportage — incl. het combineren van meerdere sonderingen en de "
               "vergelijking met de Deltares-tool — volgt later."},
]

# Index van de laatste vrijgegeven stap (Su Berekening) — afgeleid, niet hardcoded.
SU_STEP = next(i for i, s in enumerate(STEPS) if s["module"] is su_berekening)

if "current_step" not in st.session_state:
    st.session_state.current_step = 0

# === Determine step completion ===
n_sond = len(st.session_state.get("sonderingen", {}))
has_norm = any(v.get("genormaliseerd") for v in st.session_state.get("sonderingen", {}).values())
has_class = any(v.get("geclassificeerd") for v in st.session_state.get("sonderingen", {}).values())
has_su = any(v.get("su_berekend") for v in st.session_state.get("sonderingen", {}).values())

step_done = [
    "uitgangspunten" in st.session_state,   # 0 Uitgangspunten
    n_sond > 0,                              # 1 Data Inladen
    has_class,                               # 2 Classificatie
    has_norm,                                # 3 Normalisatie
    has_su,                                  # 4 Su
    False,                                   # 5 Validatie
    False,                                   # 6 Rapportage
]

su_count = sum(1 for v in st.session_state.get("sonderingen", {}).values() if v.get("su_berekend"))

# === BUILD RADIO LABELS with status icons ===
radio_labels = []
for i, s in enumerate(STEPS):
    if s.get("locked"):
        radio_labels.append(f"🔒  {s['icon']} {s['label']}")
    else:
        check = "✅" if step_done[i] else f"{i}"
        radio_labels.append(f"{check}  {s['icon']} {s['label']}")

active = st.session_state.current_step

# === SINGLE NAV ROW: brand + radio + stats ===
nav_left, nav_mid, nav_right = st.columns([1.5, 8, 1.5])
with nav_left:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; padding:4px 0;">
        <span style="font-size:1.3rem; filter:drop-shadow(0 0 8px rgba(30,136,229,0.5));">🔬</span>
        <span style="font-weight:800; font-size:0.9rem;
            background:linear-gradient(135deg,#90caf9,#1e88e5);
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
            <div style="font-size:1.1rem; font-weight:800; color:#90caf9;">{n_sond}</div>
            <div style="font-size:0.55rem; color:#546e7a; text-transform:uppercase; letter-spacing:0.08em;">CPT's</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:1.1rem; font-weight:800; color:#90caf9;">{su_count}</div>
            <div style="font-size:0.55rem; color:#546e7a; text-transform:uppercase; letter-spacing:0.08em;">Su</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# === MAIN CONTENT ===
active = st.session_state.current_step
_stap = STEPS[active]
if _stap.get("locked"):
    # Geblokkeerde stap: de module wordt bewust NIET uitgevoerd.
    st.markdown(f"""
    <div class="why-card">
        <h4>🔒 {_stap['full']} — nog niet beschikbaar</h4>
        <p>De tool loopt op dit moment tot en met <b>Su Berekening</b>.
        {_stap['locked']}</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⬅️ Terug naar Su Berekening", type="primary"):
        st.session_state.current_step = SU_STEP
        st.rerun()
else:
    _stap["module"].render()
