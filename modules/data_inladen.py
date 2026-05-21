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
    """
    Parse een GEF bestand naar een DataFrame.
    Ondersteunt GEF standaard met COLUMNINFO, COLUMNVOID, en quantity numbers.
    """
    lines = file_content.split("\n")
    
    # Zoek header info
    column_info = {}       # col_nr -> naam
    quantity_info = {}     # col_nr -> quantity nummer
    column_void = {}       # col_nr -> void waarde
    column_units = {}      # col_nr -> eenheid
    data_start = 0
    column_separator = None
    gef_type = None
    zid_value = None        # Maaiveldniveau [m NAP] uit #ZID
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if line.startswith("#ZID"):
            # Format: #ZID = ref_system, z_value  (z_value = maaiveld in m NAP)
            parts = line.split("=", 1)[1].strip().split(",")
            if len(parts) >= 2:
                try:
                    zid_value = float(parts[1].strip())
                except (ValueError, IndexError):
                    pass
        
        elif line.startswith("#COLUMNINFO"):
            # Format: #COLUMNINFO = col_nr, unit, name, quantity_nr
            parts = line.split("=", 1)[1].strip().split(",")
            if len(parts) >= 3:
                try:
                    col_nr = int(parts[0].strip())
                    col_unit = parts[1].strip()
                    col_name = parts[2].strip()
                    column_info[col_nr] = col_name
                    column_units[col_nr] = col_unit
                    if len(parts) >= 4:
                        try:
                            quantity_nr = int(parts[3].strip())
                            quantity_info[col_nr] = quantity_nr
                        except ValueError:
                            pass
                except (ValueError, IndexError):
                    pass
        
        elif line.startswith("#COLUMNVOID"):
            parts = line.split("=", 1)[1].strip().split(",")
            if len(parts) >= 2:
                try:
                    col_nr = int(parts[0].strip())
                    void_val = float(parts[1].strip())
                    column_void[col_nr] = void_val
                except (ValueError, IndexError):
                    pass
        
        elif line.startswith("#COLUMNSEPARATOR"):
            column_separator = line.split("=", 1)[1].strip()
        
        elif line.startswith("#PROCEDURECODE") or line.startswith("#REPORTCODE"):
            val = line.split("=", 1)[1].strip().lower()
            if "diss" in val or "dsp" in val:
                gef_type = "dissipatie"
        
        elif line == "#EOH=":
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
        rename_map = {}
        for col_nr, col_name in column_info.items():
            if col_nr - 1 < len(df.columns):
                rename_map[df.columns[col_nr - 1]] = col_name
        df.rename(columns=rename_map, inplace=True)
    
    # Vervang void waarden door NaN
    for col_nr, void_val in column_void.items():
        col_name = column_info.get(col_nr)
        if col_name and col_name in df.columns:
            df[col_name] = df[col_name].replace(void_val, np.nan)
        elif col_nr - 1 < len(df.columns):
            col = df.columns[col_nr - 1]
            df[col] = df[col].replace(void_val, np.nan)
    
    # Sla metadata op voor kolomdetectie
    df.attrs["gef_quantity_info"] = quantity_info
    df.attrs["gef_column_info"] = column_info
    df.attrs["gef_column_units"] = column_units
    df.attrs["gef_type"] = gef_type
    df.attrs["maaiveld_nap"] = zid_value  # None als niet gevonden
    
    return df


# GEF Quantity Numbers (NEN-EN-ISO 22476-1 / GEF-CPT standaard)
GEF_QUANTITY_MAPPING = {
    1: "diepte",      # Sondeerlengte
    2: "qc",          # Conusweerstand
    3: "fs",          # Plaatselijke wrijving (mantelwrijving)
    4: None,          # Wrijvingsgetal Rf (afgeleid, niet nodig als input)
    5: "u2",          # Waterspanning u1 (soms als u2)
    6: "u2",          # Waterspanning u2
    7: None,          # Waterspanning u3
    8: None,          # Hellingshoek resultante
    11: "diepte",     # Gecorrigeerde diepte (heeft prioriteit)
    13: None,         # Tijd
    14: "qc",         # Gecorrigeerde conusweerstand
    21: None,         # Hellingshoek N-S
    22: None,         # Hellingshoek E-W
    23: None,         # Diepte (gemeten langs sondeerstang)
}


def detect_columns(df: pd.DataFrame) -> dict:
    """
    Detecteer automatisch welke kolommen qc, fs, u2, diepte etc. zijn.
    
    Gebruikt drie methoden in volgorde (betrouwbaarheid):
    1. GEF quantity numbers (meest betrouwbaar)
    2. Kolom naam matching (uitgebreide patronen)
    3. Positie-gebaseerde fallback (standaard GEF-volgorde)
    """
    mapping = {
        "diepte": None,
        "qc": None,
        "fs": None,
        "u2": None,
    }
    
    # ── Methode 1: GEF quantity numbers ──
    quantity_info = df.attrs.get("gef_quantity_info", {})
    column_info = df.attrs.get("gef_column_info", {})
    
    qc_quantity = None
    if quantity_info:
        # Prioriteit: gecorrigeerde diepte (11) boven sondeerlengte (1)
        for col_nr, qty_nr in sorted(quantity_info.items(), key=lambda x: x[1], reverse=True):
            param = GEF_QUANTITY_MAPPING.get(qty_nr)
            if param and param in mapping:
                col_name = column_info.get(col_nr)
                if col_name and col_name in df.columns:
                    # Gecorrigeerde waarden krijgen prioriteit (hogere qty nrs)
                    if mapping[param] is None or qty_nr in (11, 14):
                        mapping[param] = col_name
                        if param == "qc":
                            qc_quantity = qty_nr
    
    # Flag: conusweerstand al gecorrigeerd voor conus area ratio (quantity 14 = qt)?
    df.attrs["is_qt_corrected"] = (qc_quantity == 14)
    
    # ── Methode 2: Kolom naam matching (uitgebreid) ──
    common_names = {
        "diepte": [
            "diepte", "depth", "sondeerlengte", "penetration_length", "z",
            "gecorrigeerde diepte", "corrected depth", "lengte",
            "penetratie lengte", "punt diepte", "meetdiepte",
            "diepte tov maaiveld", "diepte t.o.v. maaiveld",
            "sondeerlengte (m)", "penetratielengte",
        ],
        "qc": [
            "qc", "conusweerstand", "cone_resistance", "conus",
            "punt weerstand", "puntweerstand", "conusweerstand qc",
            "qc (mpa)", "qc [mpa]", "qc(mpa)", "tip resistance",
            "cone resistance", "gecorrigeerde conusweerstand",
            "conusweerstand (mpa)", "conusweerstand in mpa",
            "punt druk", "puntdruk",
        ],
        "fs": [
            "fs", "plaatselijke wrijving", "plaatselijke_wrijving",
            "sleeve_friction", "wrijving", "friction",
            "lokale wrijving", "wrijvingsweerstand", 
            "fs (mpa)", "fs [mpa]", "fs(mpa)", "sleeve friction",
            "wrijvingsweerstand fs", "mantelwrijving", "kleefweerstand",
            "plaatselijke wrijving (mpa)", "plaatselijke wrijving in mpa",
        ],
        "u2": [
            "u2", "poriedruk", "pore_pressure", "waterspanning", "pwp",
            "waterspanning u2", "u2 (mpa)", "u2 [mpa]", "u2(mpa)",
            "pore pressure", "water pressure", "waterdruk",
            "poriedruk u2", "porewaterpressure", "waterspanning u",
            "waterspanning (mpa)", "waterspanning in mpa",
            "poriedruk (mpa)", "poriedruk in mpa",
        ],
    }
    
    col_lower = {c: c.lower().strip() for c in df.columns}
    
    for param, names in common_names.items():
        if mapping[param] is not None:
            continue  # Al gevonden via quantity numbers
        for col, col_l in col_lower.items():
            for name in names:
                if name == col_l or name in col_l:
                    mapping[param] = col
                    break
            if mapping[param]:
                break
    
    # Speciale check: 'u' als losse kolom alleen matchen als het écht u2 kan zijn
    if mapping["u2"] is None:
        for col, col_l in col_lower.items():
            if col_l == "u":
                mapping["u2"] = col
                break
    
    # ── Methode 3: Positie-gebaseerd (standaard GEF volgorde) ──
    # Standaard CPT GEF: kolom 1=diepte, 2=qc, 3=fs, 4=u2 of Rf
    if mapping["diepte"] is None and mapping["qc"] is None:
        num_cols = len(df.columns)
        if num_cols >= 2:
            mapping["diepte"] = df.columns[0]
            mapping["qc"] = df.columns[1]
            if num_cols >= 3 and mapping["fs"] is None:
                mapping["fs"] = df.columns[2]
            if num_cols >= 4 and mapping["u2"] is None:
                # Kolom 4 kan u2 of Rf zijn — check waardebereik
                col4 = df[df.columns[3]].dropna()
                if len(col4) > 0 and col4.abs().median() < 5:
                    mapping["u2"] = df.columns[3]
    
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
    
    # Check of data al gecorrigeerd is (GEF quantity 14 = gecorrigeerde conusweerstand)
    if df.attrs.get("is_qt_corrected", False):
        result["message"] = "ℹ️ Conusweerstand is al gecorrigeerd voor conus area (quantity 14 / qt). Poriedrukcorrectie wordt overgeslagen in Stap 2."
        result["needs_correction"] = False
        return result
    
    if not result["has_u2"]:
        result["message"] = "⚠️ Geen poriedruk (u2) kolom gevonden. Kan correctie niet controleren."
        result["needs_correction"] = True
        return result
    
    result["message"] = "✅ Poriedruk (u2) aanwezig. Correctie naar qt kan worden uitgevoerd in Module 2."
    return result


def render():
    st.caption("Stap 1 — Upload GEF/CSV/Excel, automatische kolomherkenning")
    
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
            
            # Detecteer dissipatie-tests
            is_dissipatie = "_dsp_" in f.name.lower() or "_diss" in f.name.lower()
            
            try:
                if f.name.lower().endswith(".gef"):
                    content = f.read().decode("utf-8", errors="ignore")
                    df = parse_gef(content)
                    
                    # Check of het een dissipatie-test is (via bestandsnaam of GEF type)
                    if df.attrs.get("gef_type") == "dissipatie":
                        is_dissipatie = True
                    
                elif f.name.lower().endswith(".csv"):
                    df = pd.read_csv(f, sep=None, engine="python")
                elif f.name.lower().endswith(".xlsx"):
                    df = pd.read_excel(f)
                else:
                    continue
                
                if df.empty:
                    st.warning(f"⚠️ **{f.name}**: Geen data gevonden in dit bestand.")
                    continue
                
                if is_dissipatie:
                    st.info(f"ℹ️ **{f.name}**: Dit lijkt een **dissipatie-test** te zijn (geen CPT-sondering). "
                            f"Dissipatie-tests worden overgeslagen voor Su-berekening.")
                    continue
                
                # Kolomherkenning
                col_mapping = detect_columns(df)
                poriedruk_check = check_poriedruk_correctie(df, col_mapping)
                
                # Controleer of essentiële kolommen gevonden zijn
                has_diepte = col_mapping["diepte"] is not None
                has_qc = col_mapping["qc"] is not None
                
                maaiveld_nap = df.attrs.get("maaiveld_nap", None)
                
                st.session_state.sonderingen[f.name] = {
                    "df": df,
                    "col_mapping": col_mapping,
                    "poriedruk_check": poriedruk_check,
                    "is_qt_corrected": df.attrs.get("is_qt_corrected", False),
                    "maaiveld_nap": maaiveld_nap,
                }
                
                if has_diepte and has_qc:
                    cols_found = []
                    for k, v in col_mapping.items():
                        if v:
                            cols_found.append(f"{k}='{v}'")
                    st.success(f"✅ **{f.name}**: {len(df)} metingen geladen — Kolommen: {', '.join(cols_found)}")
                else:
                    missing = []
                    if not has_diepte:
                        missing.append("diepte")
                    if not has_qc:
                        missing.append("qc")
                    st.warning(
                        f"⚠️ **{f.name}**: {len(df)} metingen geladen, maar **{', '.join(missing)}** kolom(men) "
                        f"niet automatisch herkend. Ga naar **'Kolom Mapping'** hieronder om de juiste kolommen "
                        f"handmatig te selecteren. Beschikbare kolommen: {list(df.columns)}"
                    )
            
            except Exception as e:
                st.error(f"❌ **{f.name}**: Fout bij inlezen — {e}")
    
    # --- Overzicht geladen sonderingen ---
    if st.session_state.sonderingen:
        st.markdown("---")
        
        # Status samenvatting
        total = len(st.session_state.sonderingen)
        ready = sum(1 for d in st.session_state.sonderingen.values() 
                     if d["col_mapping"].get("diepte") and d["col_mapping"].get("qc"))
        not_ready = total - ready
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Totaal geladen", f"{total} sonderingen")
        with col_m2:
            st.metric("Gereed voor analyse", f"{ready} ✅")
        with col_m3:
            if not_ready > 0:
                st.metric("Actie nodig", f"{not_ready} ⚠️")
            else:
                st.metric("Actie nodig", "0 🎉")
        
        if not_ready > 0:
            st.warning(
                f"⚠️ **{not_ready} sondering(en)** missen essentiële kolommen (diepte/qc). "
                f"Selecteer hieronder de juiste kolommen bij 'Kolom Mapping' voordat je doorgaat naar Stap 2."
            )
        elif ready == total:
            st.success(
                f"✅ **Alle {total} sonderingen gereed** voor de volgende stap! "
                f"Ga naar **Stap 2 — Normalisatie** in het zijmenu."
            )
        
        # Overzichtstabel
        st.subheader("Overzicht Geladen Sonderingen")
        
        overview_data = []
        for name, data in st.session_state.sonderingen.items():
            df = data["df"]
            cm = data["col_mapping"]
            pc = data["poriedruk_check"]
            
            depth_range = ""
            if cm["diepte"] and cm["diepte"] in df.columns:
                depth_range = f"{df[cm['diepte']].min():.1f} — {df[cm['diepte']].max():.1f} m"
            
            status = "✅ Gereed" if (cm["diepte"] and cm["qc"]) else "⚠️ Kolom mapping nodig"
            
            mv_nap = data.get("maaiveld_nap")
            mv_str = f"NAP {mv_nap:+.2f}m" if mv_nap is not None else "⚠️ Onbekend"
            
            overview_data.append({
                "Sondering": name,
                "Status": status,
                "Maaiveld": mv_str,
                "Metingen": len(df),
                "Dieptebereik": depth_range,
                "qc": f"✅ {cm['qc']}" if cm["qc"] else "❌ Niet gevonden",
                "fs": f"✅ {cm['fs']}" if cm["fs"] else "⚠️ Niet gevonden",
                "u2": f"✅ {cm['u2']}" if cm["u2"] else "⚠️ Niet gevonden",
            })
        
        st.dataframe(pd.DataFrame(overview_data), use_container_width=True, hide_index=True)
        
        # --- Detail per sondering ---
        st.markdown("---")
        st.subheader("Detail per sondering")
        selected = st.selectbox("Selecteer sondering", list(st.session_state.sonderingen.keys()))
        
        if selected:
            data = st.session_state.sonderingen[selected]
            df = data["df"]
            cm = data["col_mapping"]
            
            # Status indicator
            if cm["diepte"] and cm["qc"]:
                st.success(f"✅ **{selected}** — Gereed voor analyse")
            else:
                missing = [k for k in ["diepte", "qc"] if not cm.get(k)]
                st.error(
                    f"❌ **{selected}** — Kolom(men) **{', '.join(missing)}** niet gevonden. "
                    f"Selecteer de juiste kolommen hieronder bij 'Kolom Mapping'."
                )
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 Data Preview", "🔧 Kolom Mapping",
                "📏 Referentieniveau", "🪨 Voorboring & Fundering"
            ])
            
            with tab1:
                st.caption(f"Eerste 30 rijen van {len(df)} totaal — Kolommen: {list(df.columns)}")
                st.dataframe(df.head(30), use_container_width=True)
            
            with tab3:
                st.markdown("""
                **Maaiveldniveau (m NAP)** — het niveau waarop de sondering is gestart.  
                Dit wordt uit de GEF-header (`#ZID`) gelezen. Controleer en pas aan indien nodig.  
                Het maaiveldniveau is cruciaal voor de juiste σv0-berekening en laagkoppeling.
                """)
                
                current_mv = data.get("maaiveld_nap")
                gef_mv = df.attrs.get("maaiveld_nap", None) if hasattr(df, 'attrs') else None
                
                if gef_mv is not None:
                    st.info(f"ℹ️ Uit GEF-header: maaiveld = NAP {gef_mv:+.2f}m")
                else:
                    st.warning("⚠️ Geen maaiveldniveau gevonden in GEF-header (#ZID). Vul handmatig in.")
                
                new_mv = st.number_input(
                    "Maaiveld [m NAP]",
                    min_value=-10.0, max_value=20.0,
                    value=float(current_mv) if current_mv is not None else 0.0,
                    step=0.01, format="%.2f",
                    key=f"mv_{selected}",
                    help="Het hoogte-niveau (m NAP) waar de sondering start. Sondeerlengte 0m = dit niveau."
                )
                
                if st.button("💾 Maaiveld opslaan", key=f"save_mv_{selected}", type="primary"):
                    st.session_state.sonderingen[selected]["maaiveld_nap"] = new_mv
                    st.success(f"✅ Maaiveld voor **{selected}** ingesteld op NAP {new_mv:+.2f}m")
                    st.rerun()
            
            with tab2:
                st.markdown("""
                **Automatische kolomherkenning** — controleer en pas aan indien nodig.
                
                De kolommen **diepte** en **qc** zijn **verplicht** voor verdere analyse. 
                Als deze niet automatisch zijn herkend, selecteer ze hier handmatig.
                """)
                
                cols = df.columns.tolist()
                
                new_mapping = {}
                col1, col2 = st.columns(2)
                with col1:
                    idx_diepte = cols.index(cm["diepte"]) + 1 if cm.get("diepte") and cm["diepte"] in cols else 0
                    new_mapping["diepte"] = st.selectbox(
                        "🔴 Diepte kolom (verplicht)", 
                        options=["(niet gevonden)"] + cols,
                        index=idx_diepte,
                        key=f"diepte_{selected}"
                    )
                    idx_qc = cols.index(cm["qc"]) + 1 if cm.get("qc") and cm["qc"] in cols else 0
                    new_mapping["qc"] = st.selectbox(
                        "🔴 qc (conusweerstand) kolom (verplicht)",
                        options=["(niet gevonden)"] + cols,
                        index=idx_qc,
                        key=f"qc_{selected}"
                    )
                with col2:
                    idx_fs = cols.index(cm["fs"]) + 1 if cm.get("fs") and cm["fs"] in cols else 0
                    new_mapping["fs"] = st.selectbox(
                        "🟡 fs (wrijving) kolom (optioneel)",
                        options=["(niet gevonden)"] + cols,
                        index=idx_fs,
                        key=f"fs_{selected}"
                    )
                    idx_u2 = cols.index(cm["u2"]) + 1 if cm.get("u2") and cm["u2"] in cols else 0
                    new_mapping["u2"] = st.selectbox(
                        "🟡 u2 (poriedruk) kolom (optioneel)",
                        options=["(niet gevonden)"] + cols,
                        index=idx_u2,
                        key=f"u2_{selected}"
                    )
                
                if st.button("💾 Mapping opslaan", key=f"save_{selected}", type="primary"):
                    for k, v in new_mapping.items():
                        st.session_state.sonderingen[selected]["col_mapping"][k] = v if v != "(niet gevonden)" else None
                    # Herbereken poriedruk check
                    st.session_state.sonderingen[selected]["poriedruk_check"] = check_poriedruk_correctie(
                        df, st.session_state.sonderingen[selected]["col_mapping"]
                    )
                    st.success("✅ Kolom mapping opgeslagen! Herlaad de pagina om het overzicht bij te werken.")
                    st.rerun()

            with tab4:
                st.markdown("""
                **Voorboring & funderingslaag** — bovenste meters van een sondering zijn vaak
                niet representatief (door wegfundering of vooraf-geboord). Geef hier aan welk
                deel overgeslagen wordt en welke laag eroverheen ligt.
                """)

                voorb = st.session_state.sonderingen[selected].get("voorboring", {}) or {}
                fund = st.session_state.sonderingen[selected].get("funderingslaag", {}) or {}

                col_vb, col_fd = st.columns(2)

                with col_vb:
                    st.markdown("**🕳️ Voorboring**")
                    voorboring_actief = st.checkbox(
                        "Voorboring toepassen",
                        value=voorb.get("actief", False),
                        key=f"vb_actief_{selected}",
                        help="Als ingeschakeld wordt de sondeerdata in het opgegeven dieptebereik genegeerd."
                    )
                    voorboring_diepte = st.number_input(
                        "Voorboring tot [m onder maaiveld]",
                        value=float(voorb.get("diepte", 0.5)),
                        min_value=0.0, max_value=10.0, step=0.1,
                        key=f"vb_diepte_{selected}",
                        disabled=not voorboring_actief,
                        help="Sondeerdata van 0 tot deze diepte wordt niet gebruikt voor Su."
                    )

                with col_fd:
                    st.markdown("**🧱 Funderingslaag**")
                    fund_actief = st.checkbox(
                        "Funderingslaag toepassen",
                        value=fund.get("actief", False),
                        key=f"fd_actief_{selected}",
                        help="Als ingeschakeld wordt deze laag toegevoegd als bovenste laag voor de σᵥ₀-berekening."
                    )
                    fund_dikte = st.number_input(
                        "Dikte [m]",
                        value=float(fund.get("dikte", 1.5)),
                        min_value=0.0, max_value=5.0, step=0.1,
                        key=f"fd_dikte_{selected}",
                        disabled=not fund_actief,
                    )
                    fund_gamma = st.number_input(
                        "γ [kN/m³]",
                        value=float(fund.get("gamma", 21.0)),
                        min_value=10.0, max_value=25.0, step=0.5,
                        key=f"fd_gamma_{selected}",
                        disabled=not fund_actief,
                    )
                    fund_materiaal = st.text_input(
                        "Materiaal",
                        value=fund.get("materiaal", "Puin en zand"),
                        key=f"fd_mat_{selected}",
                        disabled=not fund_actief,
                    )

                if st.button("💾 Voorboring & fundering opslaan", key=f"save_vb_{selected}", type="primary"):
                    st.session_state.sonderingen[selected]["voorboring"] = {
                        "actief": voorboring_actief,
                        "diepte": voorboring_diepte,
                    }
                    st.session_state.sonderingen[selected]["funderingslaag"] = {
                        "actief": fund_actief,
                        "dikte": fund_dikte,
                        "gamma": fund_gamma,
                        "materiaal": fund_materiaal,
                    }
                    st.success(f"✅ Voorboring/fundering voor **{selected}** opgeslagen.")
                    st.rerun()

        # --- Verwijder sonderingen ---
        st.markdown("---")
        if st.button("🗑️ Alle sonderingen wissen", type="secondary"):
            st.session_state.sonderingen = {}
            st.rerun()
    else:
        st.info("👆 Upload sonderingen hierboven om te beginnen.")
