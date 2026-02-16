"""
Module 1: Data Inladen & Controle
- Upload GEF/CSV/Excel bestanden (meerdere sonderingen)
- Controleer of conusweerstand gecorrigeerd is voor poriedruk (qc → qt)
- Kolomherkenning en validatie
- Overzicht geladen sonderingen
"""
import streamlit as st
import pandas as pd
import numpy as np


def parse_gef(file_content: str) -> pd.DataFrame:
    """Parse een GEF bestand naar een DataFrame."""
    lines = file_content.split("\n")
    
    # Zoek header info
    column_info = {}
    column_names = []
    data_start = 0
    column_separator = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if line.startswith("#COLUMNINFO"):
            # Format: #COLUMNINFO = col_nr, unit, name, quantity_nr
            parts = line.split("=")[1].strip().split(",")
            if len(parts) >= 3:
                col_nr = int(parts[0].strip())
                col_name = parts[2].strip()
                column_info[col_nr] = col_name
        
        if line.startswith("#COLUMNSEPARATOR"):
            column_separator = line.split("=")[1].strip()
        
        if line == "#EOH=":
            data_start = i + 1
            break
    
    # Lees data
    data_lines = []
    for line in lines[data_start:]:
        line = line.strip()
        if line and not line.startswith("#"):
            if column_separator:
                values = line.split(column_separator)
            else:
                values = line.split()
            try:
                values = [float(v.strip()) for v in values if v.strip()]
                data_lines.append(values)
            except ValueError:
                continue
    
    if not data_lines:
        return pd.DataFrame()
    
    df = pd.DataFrame(data_lines)
    
    # Kolom namen toewijzen
    if column_info:
        for col_nr, col_name in column_info.items():
            if col_nr - 1 < len(df.columns):
                df.rename(columns={df.columns[col_nr - 1]: col_name}, inplace=True)
    
    return df


def detect_columns(df: pd.DataFrame) -> dict:
    """Detecteer automatisch welke kolommen qc, fs, u2, diepte etc. zijn."""
    mapping = {
        "diepte": None,
        "qc": None,
        "fs": None,
        "u2": None,
    }
    
    common_names = {
        "diepte": ["diepte", "depth", "sondeerlengte", "penetration_length", "z"],
        "qc": ["qc", "conusweerstand", "cone_resistance", "conus"],
        "fs": ["fs", "plaatselijke_wrijving", "sleeve_friction", "wrijving", "friction"],
        "u2": ["u2", "u", "poriedruk", "pore_pressure", "waterspanning", "pwp"],
    }
    
    col_lower = {c: c.lower().strip() for c in df.columns}
    
    for param, names in common_names.items():
        for col, col_l in col_lower.items():
            for name in names:
                if name in col_l:
                    mapping[param] = col
                    break
            if mapping[param]:
                break
    
    return mapping


def check_poriedruk_correctie(df: pd.DataFrame, col_mapping: dict) -> dict:
    """Controleer of de conusweerstand gecorrigeerd is voor poriedruk."""
    result = {
        "has_u2": col_mapping["u2"] is not None,
        "has_qc": col_mapping["qc"] is not None,
        "needs_correction": False,
        "message": "",
    }
    
    if not result["has_qc"]:
        result["message"] = "⚠️ Geen conusweerstand (qc) kolom gevonden."
        return result
    
    if not result["has_u2"]:
        result["message"] = "⚠️ Geen poriedruk (u2) kolom gevonden. Kan correctie niet controleren."
        result["needs_correction"] = True
        return result
    
    result["message"] = "✅ Poriedruk (u2) aanwezig. Correctie naar qt kan worden uitgevoerd in Module 2."
    return result


def render():
    st.title("📁 Module 1: Data Inladen & Controle")
    st.markdown("""
    Upload een of meerdere sonderingen (GEF, CSV of Excel). 
    De tool controleert automatisch of de conusweerstand gecorrigeerd is voor poriedruk.
    """)
    
    # --- Initialiseer session state ---
    if "sonderingen" not in st.session_state:
        st.session_state.sonderingen = {}
    
    # --- Bestand uploaden ---
    uploaded_files = st.file_uploader(
        "Upload sonderingen",
        type=["gef", "csv", "xlsx"],
        accept_multiple_files=True,
        help="Selecteer een of meerdere GEF, CSV of Excel bestanden"
    )
    
    if uploaded_files:
        for f in uploaded_files:
            if f.name in st.session_state.sonderingen:
                continue  # Al geladen
            
            try:
                if f.name.lower().endswith(".gef"):
                    content = f.read().decode("utf-8", errors="ignore")
                    df = parse_gef(content)
                elif f.name.lower().endswith(".csv"):
                    df = pd.read_csv(f, sep=None, engine="python")
                elif f.name.lower().endswith(".xlsx"):
                    df = pd.read_excel(f)
                else:
                    continue
                
                if df.empty:
                    st.warning(f"⚠️ {f.name}: Geen data gevonden.")
                    continue
                
                # Kolomherkenning
                col_mapping = detect_columns(df)
                poriedruk_check = check_poriedruk_correctie(df, col_mapping)
                
                st.session_state.sonderingen[f.name] = {
                    "df": df,
                    "col_mapping": col_mapping,
                    "poriedruk_check": poriedruk_check,
                }
                
                st.success(f"✅ {f.name}: {len(df)} metingen geladen")
            
            except Exception as e:
                st.error(f"❌ {f.name}: Fout bij inlezen — {e}")
    
    # --- Overzicht geladen sonderingen ---
    if st.session_state.sonderingen:
        st.markdown("---")
        st.subheader("Overzicht Geladen Sonderingen")
        
        overview_data = []
        for name, data in st.session_state.sonderingen.items():
            df = data["df"]
            cm = data["col_mapping"]
            pc = data["poriedruk_check"]
            
            depth_range = ""
            if cm["diepte"] and cm["diepte"] in df.columns:
                depth_range = f"{df[cm['diepte']].min():.1f} - {df[cm['diepte']].max():.1f} m"
            
            overview_data.append({
                "Sondering": name,
                "Metingen": len(df),
                "Diepte": depth_range,
                "qc": "✅" if cm["qc"] else "❌",
                "fs": "✅" if cm["fs"] else "❌",
                "u2": "✅" if cm["u2"] else "❌",
                "Poriedruk status": pc["message"],
            })
        
        st.dataframe(pd.DataFrame(overview_data), use_container_width=True, hide_index=True)
        
        # --- Detail per sondering ---
        st.subheader("Detail per sondering")
        selected = st.selectbox("Selecteer sondering", list(st.session_state.sonderingen.keys()))
        
        if selected:
            data = st.session_state.sonderingen[selected]
            df = data["df"]
            cm = data["col_mapping"]
            
            tab1, tab2 = st.tabs(["📋 Data", "🔧 Kolom Mapping"])
            
            with tab1:
                st.dataframe(df.head(30), use_container_width=True)
            
            with tab2:
                st.markdown("**Automatische kolomherkenning** (pas aan indien nodig):")
                cols = df.columns.tolist()
                
                new_mapping = {}
                col1, col2 = st.columns(2)
                with col1:
                    new_mapping["diepte"] = st.selectbox(
                        "Diepte kolom", 
                        options=["(niet gevonden)"] + cols,
                        index=cols.index(cm["diepte"]) + 1 if cm["diepte"] in cols else 0,
                        key=f"diepte_{selected}"
                    )
                    new_mapping["qc"] = st.selectbox(
                        "qc (conusweerstand) kolom",
                        options=["(niet gevonden)"] + cols,
                        index=cols.index(cm["qc"]) + 1 if cm["qc"] in cols else 0,
                        key=f"qc_{selected}"
                    )
                with col2:
                    new_mapping["fs"] = st.selectbox(
                        "fs (wrijving) kolom",
                        options=["(niet gevonden)"] + cols,
                        index=cols.index(cm["fs"]) + 1 if cm["fs"] in cols else 0,
                        key=f"fs_{selected}"
                    )
                    new_mapping["u2"] = st.selectbox(
                        "u2 (poriedruk) kolom",
                        options=["(niet gevonden)"] + cols,
                        index=cols.index(cm["u2"]) + 1 if cm["u2"] in cols else 0,
                        key=f"u2_{selected}"
                    )
                
                if st.button("💾 Mapping opslaan", key=f"save_{selected}"):
                    for k, v in new_mapping.items():
                        st.session_state.sonderingen[selected]["col_mapping"][k] = v if v != "(niet gevonden)" else None
                    # Herbereken poriedruk check
                    st.session_state.sonderingen[selected]["poriedruk_check"] = check_poriedruk_correctie(
                        df, st.session_state.sonderingen[selected]["col_mapping"]
                    )
                    st.success("✅ Kolom mapping opgeslagen")
                    st.rerun()
        
        # --- Verwijder sonderingen ---
        st.markdown("---")
        if st.button("🗑️ Alle sonderingen wissen"):
            st.session_state.sonderingen = {}
            st.rerun()
    else:
        st.info("Upload sonderingen om te beginnen.")
