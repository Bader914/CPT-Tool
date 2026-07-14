import streamlit as st

st.set_page_config(
    page_title="CPT Su Tool | HHSK",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Licht, rustig ontwerp (HHSK) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --bg:#f5f7fb; --surface:#ffffff; --ink:#0f2942; --text:#3f5165; --muted:#7488a0;
  --primary:#1a76bb; --primary-d:#125e97; --primary-soft:#e9f2fb; --border:#e4eaf1;
  --field-border:#c3d2e0;   /* rand van invoervelden/knoppen — bewust zichtbaar */
  --green:#15803d; --green-soft:#eafaf0;
}
html, body, [class*="css"], input, button, select, textarea { font-family:'Inter',sans-serif; }

/* lichte app */
[data-testid="stAppViewContainer"]{ background:var(--bg); color:var(--text); }
[data-testid="stHeader"]{ background:transparent; }
[data-testid="stSidebar"], [data-testid="collapsedControl"]{ display:none !important; }
/* Breed genoeg voor de tabellen (anders moet je horizontaal scrollen), maar met
   een bovengrens zodat tekst leesbaar blijft. */
.block-container{ padding-top:3rem !important; padding-bottom:2rem !important;
  max-width:1500px !important; padding-left:2rem !important; padding-right:2rem !important; }

/* tabellen mogen de volle breedte pakken en netjes afbreken */
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"]{ width:100% !important; }

h1,h2,h3,h4{ color:var(--ink) !important; }
h2{ font-size:1.25rem !important; margin:.5rem 0 .3rem !important; }
h3{ font-size:1.05rem !important; margin:.4rem 0 .2rem !important; }

/* expander-pijl herstellen */
[data-testid="stExpanderToggleIcon"]{ font-size:0 !important; width:1rem; height:1rem;
  display:inline-flex; align-items:center; justify-content:center; }
[data-testid="stExpanderToggleIcon"]::before{ content:"\203A"; font-size:1.3rem; color:var(--muted); line-height:1; }

/* navigatie als lichte pillen */
[data-testid="stRadio"] > div{ gap:0 !important; }
[data-testid="stRadio"] [role="radiogroup"]{
  gap:4px !important; background:var(--surface); border:1px solid var(--border);
  border-radius:14px; padding:5px; box-shadow:0 1px 3px rgba(16,41,66,.05); }
[data-testid="stRadio"] [role="radiogroup"] label{
  border-radius:10px !important; padding:7px 14px !important; margin:0 !important;
  font-size:.8rem !important; font-weight:600; color:var(--muted) !important; white-space:nowrap; transition:all .15s ease; }
[data-testid="stRadio"] [role="radiogroup"] label:hover{ background:var(--primary-soft) !important; color:var(--primary-d) !important; }
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked){
  background:var(--primary) !important; color:#fff !important; box-shadow:0 2px 8px rgba(26,118,187,.28); }
[data-testid="stRadio"] [role="radiogroup"] label > div:first-child{ display:none !important; }
[data-testid="stRadio"] [role="radiogroup"] label p{ font-size:.8rem !important; margin:0; }

/* uitleg-kaart */
.why-card{ background:var(--primary-soft); border:1px solid #d3e6f7; border-left:4px solid var(--primary);
  border-radius:12px; padding:1rem 1.2rem; margin:.4rem 0 1rem; }
.why-card h4{ color:var(--primary-d) !important; font-size:.8rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.05em; margin:0 0 .35rem; }
.why-card p{ color:#33526d !important; font-size:.9rem; line-height:1.55; margin:0 0 .3rem; }

/* volgende-stap */
.next-step{ background:var(--green-soft); border:1px solid #bfe8cf; border-radius:12px;
  padding:.8rem 1.2rem; margin-top:1rem; display:flex; align-items:center; gap:10px; }
.next-step .arrow{ font-size:1.2rem; color:var(--green); }
.next-step p{ color:#166534 !important; margin:0; font-weight:600; font-size:.9rem; }
.next-step b{ color:#14532d !important; }

/* metrics als kaarten */
[data-testid="stMetric"]{ background:var(--surface); border:1px solid var(--border); border-radius:12px;
  padding:14px 18px; box-shadow:0 1px 3px rgba(16,41,66,.05); }
[data-testid="stMetric"] label{ color:var(--muted) !important; font-size:.7rem !important; font-weight:600;
  text-transform:uppercase; letter-spacing:.07em; }
[data-testid="stMetric"] [data-testid="stMetricValue"]{ color:var(--ink) !important; font-weight:800 !important; font-size:1.4rem !important; }

/* tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"]{ gap:3px; background:var(--surface); border:1px solid var(--border);
  border-radius:12px; padding:4px; }
[data-testid="stTabs"] [data-baseweb="tab"]{ border-radius:9px !important; font-weight:600; padding:8px 16px;
  color:var(--muted) !important; font-size:.85rem; }
[data-testid="stTabs"] [aria-selected="true"]{ background:var(--primary-soft) !important; color:var(--primary-d) !important; }

/* expanders */
[data-testid="stExpander"]{ background:var(--surface) !important; border:1px solid var(--border) !important; border-radius:12px !important; }
[data-testid="stExpander"] summary{ font-weight:600; color:var(--ink) !important; }
[data-testid="stExpander"] summary span{ color:var(--ink) !important; }

/* === INVOERVELDEN — duidelijk omlijnd, overal dezelfde vorm === */
/* Zonder rand vielen de velden weg tegen de witte achtergrond. */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] input,
[data-baseweb="select"] > div{
  background:#fff !important;
  border:1.5px solid var(--field-border) !important;
  border-radius:8px !important;
  color:var(--ink) !important;
  box-shadow:none !important;
}
/* het omhulsel van number/text input zelf ook, anders zie je een dubbele rand */
[data-testid="stNumberInput"] > div, [data-testid="stTextInput"] > div{
  border:none !important; background:transparent !important; box-shadow:none !important; }

/* focus: duidelijke blauwe ring */
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-baseweb="select"] > div:focus-within{
  border-color:var(--primary) !important;
  box-shadow:0 0 0 3px rgba(26,118,187,.15) !important;
}
/* hover */
[data-testid="stTextInput"] input:hover,
[data-testid="stNumberInput"] input:hover,
[data-baseweb="select"] > div:hover{ border-color:#9db6cd !important; }

/* uitgeschakelde velden: grijs, duidelijk 'niet aanpasbaar' */
[data-testid="stTextInput"] input:disabled,
[data-testid="stNumberInput"] input:disabled{
  background:#f1f5f9 !important; color:var(--muted) !important;
  border-color:var(--border) !important; cursor:not-allowed; }

/* +/- stappers van number input */
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"]{
  border:1.5px solid var(--field-border) !important; border-radius:6px !important;
  background:#fff !important; color:var(--muted) !important; }
[data-testid="stNumberInputStepUp"]:hover, [data-testid="stNumberInputStepDown"]:hover{
  border-color:var(--primary) !important; color:var(--primary) !important; }

/* labels boven de velden */
[data-testid="stNumberInput"] label, [data-testid="stSelectbox"] label, [data-testid="stTextInput"] label,
[data-testid="stTextArea"] label, [data-testid="stFileUploader"] label, [data-testid="stRadio"] > label,
[data-testid="stCheckbox"] label{ color:var(--ink) !important; font-weight:600; font-size:.85rem; }

/* checkbox duidelijker */
[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child{
  border:1.5px solid var(--field-border) !important; border-radius:5px !important; }

/* === KNOPPEN === */
/* secundair: witte knop met duidelijke rand · primair: gevuld blauw */
.stButton > button, .stDownloadButton > button{
  border-radius:8px !important; font-weight:600; padding:.5rem 1.2rem;
  border:1.5px solid var(--field-border) !important; background:#fff !important;
  color:var(--ink) !important; transition:all .15s ease; box-shadow:none !important; }
.stButton > button:hover, .stDownloadButton > button:hover{
  border-color:var(--primary) !important; color:var(--primary-d) !important;
  background:var(--primary-soft) !important; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"]{
  background:var(--primary) !important; color:#fff !important;
  border:1.5px solid var(--primary) !important; }
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover{
  background:var(--primary-d) !important; border-color:var(--primary-d) !important; color:#fff !important; }

/* bestand-uploader */
[data-testid="stFileUploader"]{ background:#fff; border:2px dashed #b8cfe3 !important; border-radius:12px; padding:.8rem; }
[data-testid="stFileUploader"]:hover{ border-color:var(--primary) !important; background:var(--primary-soft); }

/* tabellen */
[data-testid="stAppViewContainer"] table{ background:var(--surface); border:1px solid var(--border);
  border-radius:10px; border-collapse:separate; border-spacing:0; width:100%; overflow:hidden; }
[data-testid="stAppViewContainer"] th{ background:var(--primary-soft) !important; color:var(--primary-d) !important;
  padding:8px 12px; font-weight:700; font-size:.82rem; }
[data-testid="stAppViewContainer"] td{ color:var(--text) !important; padding:7px 12px; border-top:1px solid var(--border); font-size:.85rem; }

/* alerts */
[data-testid="stAlert"]{ border-radius:10px !important; }

hr{ border-color:var(--border) !important; margin:.8rem 0; }
::-webkit-scrollbar{ width:8px; } ::-webkit-scrollbar-track{ background:var(--bg); }
::-webkit-scrollbar-thumb{ background:#c7d3df; border-radius:4px; }
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
            <div style="font-size: 3.4rem; margin-bottom: 0.5rem;">🌊</div>
            <h1 style="font-size: 1.9rem; font-weight: 800; color:#125e97; margin-bottom: 0.3rem;">
                CPT Su Tool
            </h1>
            <p style="color: #7488a0; font-size: 0.95rem;">
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
    {"module": uitgangspunten, "icon": "⚙️", "label": "Parameters", "full": "Uitgangspunten",
     "titel": "Projectparameters",
     "wat": "We leggen eenmalig de vaste projectgegevens vast: de grondsoorten met hun "
            "sterkte-eigenschappen (Tabel 91), het conustype en de rekenmethode.",
     "waarom": "Dit zijn de gegevens die voor het hele project gelden. Alles wat pér sondering "
               "verschilt (grondlagen, waterstand) doe je later, bij de sondering zelf."},
    {"module": data_inladen, "icon": "📁", "label": "Upload", "full": "Data Inladen",
     "titel": "Sonderingen inladen",
     "wat": "Upload je GEF-bestanden. De tool leest automatisch de meetwaarden, het maaiveld, "
            "de a-factor en de voorboordiepte uit de bestanden.",
     "waarom": "Zo begint elke sondering met de juiste gegevens uit het bestand zelf — je hoeft "
               "niets over te typen. Hier open of bewaar je ook een eerdere analyse."},
    {"module": classificatie, "icon": "🧱", "label": "Grondlagen", "full": "Classificatie",
     "titel": "Grondlagen per sondering",
     "wat": "Per sondering bepalen we de grondopbouw. De tool stelt de lagen automatisch voor "
            "(op basis van de sondering); jij past ze aan waar nodig.",
     "waarom": "De laagindeling bepaalt welke grond waar zit — en dus welke sterkte en gewichten "
               "straks worden gebruikt."},
    {"module": normalisatie, "icon": "📐", "label": "Waterdruk", "full": "Normalisatie",
     "titel": "Waterdruk & spanningen",
     "wat": "Per sondering stel je de grondwaterstand en het waterdrukverloop in. De tool "
            "berekent daarmee de spanningen in de grond (σv0, σ′v0).",
     "waarom": "De korrelspanning σ′v0 is nodig voor de sterkte. Controleer met de grafiek: de "
               "berekende u₀ hoort in de buurt van de gemeten u₂ te liggen."},
    {"module": su_berekening, "icon": "📊", "label": "Sterkte Su", "full": "Su Berekening",
     "titel": "Ongedraineerde sterkte Su",
     "wat": "We berekenen de sterkte Su uit de sondering (Su = qnet / Nkt) en daaruit de "
            "grensspanning, plus een voorzichtige (karakteristieke) waarde.",
     "waarom": "Su is het eindresultaat: hoe sterk de grond is, wat je nodig hebt voor de "
               "dijkbeoordeling."},
    # Voorlopig geblokkeerd: de tool stopt na de Su-berekening.
    {"module": validatie, "icon": "✅", "label": "Validatie", "full": "Validatie",
     "titel": "Validatie", "wat": "", "waarom": "",
     "locked": "Validatie met triaxiaalproeven (Nkt-kalibratie) volgt later."},
    {"module": visualisatie, "icon": "📈", "label": "Rapportage", "full": "Rapportage",
     "titel": "Rapportage", "wat": "", "waarom": "",
     "locked": "Rapportage — incl. het combineren van meerdere sonderingen en de "
               "vergelijking met de Deltares-tool — volgt later."},
]

# Aantal actieve (niet-geblokkeerde) stappen — voor de 'Stap X van Y'-teller.
ACTIEVE_STAPPEN = [i for i, s in enumerate(STEPS) if not s.get("locked")]

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
        # 1-gebaseerd, gelijk aan "Stap X van 5" in de wizard-kop
        check = "✅" if step_done[i] else f"{i + 1}"
        radio_labels.append(f"{check}  {s['icon']} {s['label']}")

active = st.session_state.current_step


# Navigatie loopt via ÉÉN bron van waarheid: current_step. De radio gebruikt
# integer-opties (stabiel, los van de labeltekst) en een callback; knoppen elders
# (Volgende / terug) zetten current_step via _ga_naar(). Zo overschrijft de radio
# de knoppen niet meer.
def _ga_naar(step_index):
    # Zet zowel de bron van waarheid als de radio-waarde (moet in een callback,
    # anders klaagt Streamlit dat de widget al is aangemaakt).
    st.session_state.current_step = step_index
    st.session_state.step_radio = step_index


def _on_nav_change():
    st.session_state.current_step = st.session_state.step_radio


# === SINGLE NAV ROW: brand + radio + stats ===
nav_left, nav_mid, nav_right = st.columns([1.5, 8, 1.5])
with nav_left:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; padding:4px 0;">
        <span style="font-size:1.3rem;">🌊</span>
        <span style="font-weight:800; font-size:0.95rem; color:#125e97;">CPT Su Tool</span>
    </div>
    """, unsafe_allow_html=True)
with nav_mid:
    st.radio(
        "nav", options=list(range(len(STEPS))), index=active,
        format_func=lambda i: radio_labels[i],
        horizontal=True, label_visibility="collapsed",
        key="step_radio", on_change=_on_nav_change,
    )
with nav_right:
    st.markdown(f"""
    <div style="display:flex; gap:16px; justify-content:flex-end; padding:6px 0;">
        <div style="text-align:center;">
            <div style="font-size:1.1rem; font-weight:800; color:#1a76bb;">{n_sond}</div>
            <div style="font-size:0.55rem; color:#7488a0; text-transform:uppercase; letter-spacing:0.08em;">CPT's</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:1.1rem; font-weight:800; color:#1a76bb;">{su_count}</div>
            <div style="font-size:0.55rem; color:#7488a0; text-transform:uppercase; letter-spacing:0.08em;">Su</div>
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
    st.button("⬅️ Terug naar Su Berekening", type="primary",
              on_click=_ga_naar, args=(SU_STEP,))
else:
    # ── Wizard-kader: 'wat doen we nu + waarom' met voortgang ──
    _pos = ACTIEVE_STAPPEN.index(active) + 1
    _tot = len(ACTIEVE_STAPPEN)
    st.markdown(f"""
    <div class="why-card">
        <h4>{_stap['icon']} Stap {_pos} van {_tot} · {_stap.get('titel', _stap['full'])}</h4>
        <p><b>Wat doen we hier?</b> {_stap.get('wat', '')}</p>
        <p style="opacity:.85;"><b>Waarom?</b> {_stap.get('waarom', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    _stap["module"].render()

    # ── Volgende-stap knop (behalve op de laatste actieve stap) ──
    _idx = ACTIEVE_STAPPEN.index(active)
    if _idx + 1 < len(ACTIEVE_STAPPEN):
        _volgende = ACTIEVE_STAPPEN[_idx + 1]
        _v = STEPS[_volgende]
        st.markdown("<hr>", unsafe_allow_html=True)
        _c1, _c2 = st.columns([3, 1])
        with _c2:
            st.button(f"Volgende: {_v.get('titel', _v['full'])}  ➜",
                      type="primary", use_container_width=True, key="wizard_next",
                      on_click=_ga_naar, args=(_volgende,))
