import streamlit as st

st.set_page_config(
    page_title="CPT Su Tool | HHSK",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Modern CSS Styling v5.0 ──
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

/* Hide default sidebar toggle */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* === TOP NAV BAR === */
.topbar {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-radius: 16px;
    padding: 8px 12px;
    margin-bottom: 1rem;
}
.topbar-brand {
    display: flex; align-items: center; gap: 10px;
    padding-right: 16px; border-right: 1px solid rgba(99, 102, 241, 0.15);
    margin-right: 4px; flex-shrink: 0;
}
.topbar-brand span.icon { font-size: 1.4rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5)); }
.topbar-brand .name {
    font-size: 0.95rem; font-weight: 800;
    background: linear-gradient(135deg, #c7d2fe, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

/* Step pills in topbar */
.step-pills { display: flex; gap: 4px; flex-wrap: nowrap; overflow-x: auto; flex: 1; }
.step-pill {
    display: flex; align-items: center; gap: 6px;
    padding: 7px 14px; border-radius: 10px; cursor: pointer;
    transition: all 0.2s ease; white-space: nowrap; flex-shrink: 0;
    font-size: 0.78rem; font-weight: 500; text-decoration: none;
    border: 1px solid transparent;
}
.step-pill.done { background: rgba(34, 197, 94, 0.12); color: #86efac; border-color: rgba(34, 197, 94, 0.2); }
.step-pill.active { background: rgba(99, 102, 241, 0.2); color: #c7d2fe; border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 2px 12px rgba(99, 102, 241, 0.25); }
.step-pill.todo { background: rgba(30, 41, 59, 0.4); color: #475569; }
.step-pill .num {
    width: 20px; height: 20px; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; flex-shrink: 0;
}
.step-pill.done .num { background: #22c55e; color: white; }
.step-pill.active .num { background: #6366f1; color: white; }
.step-pill.todo .num { background: rgba(51, 65, 85, 0.6); color: #64748b; border: 1px solid #334155; }

/* Stats in topbar */
.topbar-stats {
    display: flex; gap: 12px; margin-left: auto; padding-left: 16px;
    border-left: 1px solid rgba(99, 102, 241, 0.15); flex-shrink: 0;
}
.topbar-stat { text-align: center; }
.topbar-stat .val { font-size: 1.1rem; font-weight: 800; color: #c7d2fe; }
.topbar-stat .lbl { font-size: 0.6rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; }

/* === COMPACT HERO === */
.hero-compact {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 100%);
    border-radius: 16px; padding: 1.4rem 2rem; color: white;
    margin-bottom: 1rem; position: relative; overflow: hidden;
    border: 1px solid rgba(99, 102, 241, 0.25);
    display: flex; align-items: center; justify-content: space-between; gap: 2rem;
}
.hero-compact::before {
    content: ''; position: absolute; top: -60%; right: -10%;
    width: 250px; height: 250px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.25) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-compact .hero-text { position: relative; flex: 1; }
.hero-compact .step-tag {
    display: inline-block; background: rgba(255,255,255,0.12);
    color: #c7d2fe; font-size: 0.65rem; font-weight: 700;
    padding: 3px 10px; border-radius: 14px; text-transform: uppercase;
    letter-spacing: 0.1em; margin-bottom: 0.4rem;
}
.hero-compact h1 { font-size: 1.5rem !important; font-weight: 800 !important;
    margin: 0 !important; color: white !important; }
.hero-compact .sub { color: #a5b4fc; font-size: 0.88rem; margin: 0.2rem 0 0 0; }
.hero-compact .hero-why {
    position: relative; max-width: 340px; background: rgba(255,255,255,0.08);
    border-radius: 12px; padding: 0.9rem 1.1rem; font-size: 0.82rem;
    color: #c7d2fe; line-height: 1.5; border: 1px solid rgba(255,255,255,0.08);
}
.hero-compact .hero-why b { color: #e0e7ff; }

/* Legacy hero-section / hero-container now maps to compact */
.hero-section, .hero-container {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 100%);
    border-radius: 16px; padding: 1.4rem 2rem; color: white;
    margin-bottom: 1rem; border: 1px solid rgba(99, 102, 241, 0.25);
    position: relative; overflow: hidden;
}
.hero-section h1, .hero-container h1 { font-size: 1.5rem !important; font-weight: 800 !important;
    margin: 0 0 0.3rem 0 !important; color: white !important; }
.hero-section p, .hero-section .subtitle, .hero-container p { color: #a5b4fc; font-size: 0.88rem; margin: 0; }
.hero-section .step-label { display: inline-block; background: rgba(255,255,255,0.12);
    color: #c7d2fe; font-size: 0.65rem; font-weight: 700; padding: 3px 10px;
    border-radius: 14px; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.4rem; }

/* === WHY CARD (compact) === */
.why-card {
    background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1rem;
    position: relative; border-left: 3px solid #6366f1;
}
.why-card h4 { color: #818cf8 !important; font-size: 0.82rem; font-weight: 700;
    margin: 0 0 0.4rem 0; text-transform: uppercase; letter-spacing: 0.05em; }
.why-card p { color: #cbd5e1 !important; font-size: 0.85rem; line-height: 1.5; margin: 0 0 0.3rem 0; }
.why-card .tip {
    display: flex; align-items: flex-start; gap: 8px;
    background: rgba(99, 102, 241, 0.08); border-radius: 8px;
    padding: 8px 12px; margin-top: 0.5rem;
}
.why-card .tip p { color: #a5b4fc !important; font-size: 0.8rem; margin: 0; }

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

/* === EXPANDERS === */
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
[data-testid="stAppViewContainer"] hr { border-color: rgba(99, 102, 241, 0.1) !important; margin: 1rem 0; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
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
active = st.session_state.current_step

# === TOP NAVIGATION BAR (HTML) ===
pills_html = ""
for i, s in enumerate(STEPS):
    if step_done[i]:
        cls = "done"
    elif i == active:
        cls = "active"
    else:
        cls = "todo"
    pills_html += f'''<div class="step-pill {cls}" id="step-{i}">
        <div class="num">{("✓" if step_done[i] else str(i))}</div>
        {s["icon"]} {s["label"]}
    </div>'''

stats_html = f"""<div class="topbar-stats">
    <div class="topbar-stat"><div class="val">{n_sond}</div><div class="lbl">CPT's</div></div>
    <div class="topbar-stat"><div class="val">{su_count}</div><div class="lbl">Su</div></div>
</div>"""

st.markdown(f"""
<div class="topbar">
    <div class="topbar-brand">
        <span class="icon">🔬</span>
        <div class="name">CPT Su Tool</div>
    </div>
    <div class="step-pills">{pills_html}</div>
    {stats_html}
</div>
""", unsafe_allow_html=True)

# === STEP SELECTOR BUTTONS (Streamlit) ===
btn_cols = st.columns(7)
for i, s in enumerate(STEPS):
    with btn_cols[i]:
        label = f"{'✅ ' if step_done[i] else ''}{s['label']}"
        if st.button(label, key=f"nav_{i}", use_container_width=True,
                     type="primary" if i == active else "secondary"):
            st.session_state.current_step = i
            st.rerun()

# Style the nav buttons to be tiny and match theme
st.markdown("""
<style>
/* Make nav buttons compact, sitting below the visual topbar */
[data-testid="stHorizontalBlock"]:has(button[kind]) {
    gap: 4px !important; margin-top: -0.5rem; margin-bottom: 0.5rem;
}
div[data-testid="stHorizontalBlock"] .stButton > button {
    font-size: 0.7rem !important; padding: 0.3rem 0.4rem !important;
    border-radius: 8px !important; min-height: 0 !important;
    background: rgba(30, 41, 59, 0.3) !important;
    color: #64748b !important; border: 1px solid rgba(99, 102, 241, 0.1) !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"] {
    background: rgba(99, 102, 241, 0.2) !important;
    color: #c7d2fe !important; border-color: rgba(99, 102, 241, 0.3) !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    background: rgba(99, 102, 241, 0.15) !important; color: #a5b4fc !important;
    transform: none !important; box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("---")

# === MAIN CONTENT ===
STEPS[active]["module"].render()
