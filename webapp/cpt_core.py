"""
cpt_core — streamlit-vrij rekenhart van de CPT Su Tool.

Bevat de gevalideerde formules en de GEF-inlees/-classificatielogica, losgekoppeld
van elke UI. Wordt door de FastAPI-backend gebruikt. De formules zijn 1-op-1
gespiegeld aan de gevalideerde Streamlit-modules (u0 exact gelijk aan de Excel).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

GAMMA_W = 9.81          # kN/m³
PA_MPA = 0.1            # atmosferische druk [MPa] (ISBT)

# ── grondsoort-kleuren (boorstaat, NL-conventie) ──
LITHO_KLEUREN = {"zand": "#FFD54F", "klei": "#4CAF50", "veen": "#7B4B27",
                 "silt": "#9E9D24", "onbekend": "#BDBDBD"}


# =====================================================================
# GEF inlezen
# =====================================================================
GEF_QUANTITY_MAPPING = {1: "diepte", 2: "qc", 3: "fs", 4: None, 5: "u2", 6: "u2",
                        7: None, 8: None, 11: "diepte", 13: None, 14: "qc",
                        21: None, 22: None, 23: None}


def parse_gef(content: str) -> dict:
    """Parse GEF-tekst → dict met DataFrame + metadata (maaiveld, eenheden, a-factor)."""
    lines = content.split("\n")
    column_info, quantity_info, column_void, column_units = {}, {}, {}, {}
    data_start, sep, gef_type, zid, a_gef = 0, None, None, None, None
    for i, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("#ZID"):
            p = line.split("=", 1)[1].split(",")
            if len(p) >= 2:
                try:
                    zid = float(p[1].strip())
                except ValueError:
                    pass
        elif line.startswith("#COLUMNINFO"):
            p = line.split("=", 1)[1].split(",")
            if len(p) >= 3:
                try:
                    nr = int(p[0]); column_info[nr] = p[2].strip(); column_units[nr] = p[1].strip()
                    if len(p) >= 4:
                        quantity_info[nr] = int(p[3])
                except ValueError:
                    pass
        elif line.startswith("#COLUMNVOID"):
            p = line.split("=", 1)[1].split(",")
            if len(p) >= 2:
                try:
                    column_void[int(p[0])] = float(p[1])
                except ValueError:
                    pass
        elif line.startswith("#MEASUREMENTVAR"):
            p = line.split("=", 1)[1].split(",")
            if len(p) >= 2:
                try:
                    v = float(p[1]); d = ",".join(p[3:]).lower() if len(p) >= 4 else ""
                    if 0.5 <= v <= 1.0 and any(k in d for k in
                            ("area ratio", "oppervlakteverhouding", "alpha", "netto", "net area")):
                        a_gef = v
                except ValueError:
                    pass
        elif line.startswith("#COLUMNSEPARATOR"):
            sep = line.split("=", 1)[1].strip()
        elif line.startswith("#PROCEDURECODE") or line.startswith("#REPORTCODE"):
            v = line.split("=", 1)[1].lower()
            if "diss" in v or "dsp" in v:
                gef_type = "dissipatie"
        elif line == "#EOH=":
            data_start = i + 1
            break
    data = []
    for raw in lines[data_start:]:
        line = raw.strip()
        if line and not line.startswith("#"):
            vals = line.split(sep) if sep else line.split()
            try:
                data.append([float(v.strip()) for v in vals if v.strip()])
            except ValueError:
                continue
    if not data:
        return {"df": pd.DataFrame(), "maaiveld_nap": zid, "a_factor_gef": a_gef, "gef_type": gef_type}
    df = pd.DataFrame(data)
    if column_info:
        rename = {df.columns[nr - 1]: nm for nr, nm in column_info.items() if nr - 1 < len(df.columns)}
        df.rename(columns=rename, inplace=True)
    for nr, void in column_void.items():
        nm = column_info.get(nr)
        if nm and nm in df.columns:
            df[nm] = df[nm].replace(void, np.nan)
    units = {column_info[nr]: column_units.get(nr, "") for nr in column_info}
    return {"df": df, "maaiveld_nap": zid, "a_factor_gef": a_gef, "gef_type": gef_type,
            "quantity_info": quantity_info, "column_info": column_info, "units": units}


def detect_columns(df: pd.DataFrame, quantity_info: dict, column_info: dict) -> dict:
    mapping = {"diepte": None, "qc": None, "fs": None, "u2": None}
    qc_qty = None
    if quantity_info:
        for nr, qty in sorted(quantity_info.items(), key=lambda x: x[1], reverse=True):
            param = GEF_QUANTITY_MAPPING.get(qty)
            if param and param in mapping:
                nm = column_info.get(nr)
                if nm and nm in df.columns and (mapping[param] is None or qty in (11, 14)):
                    mapping[param] = nm
                    if param == "qc":
                        qc_qty = qty
    names = {"diepte": ["diepte", "sondeerlengte", "gecorrigeerde diepte", "depth", "lengte"],
             "qc": ["qc", "conusweerstand", "puntdruk", "puntweerstand", "cone"],
             "fs": ["fs", "wrijving", "plaatselijke wrijving", "lokale wrijving", "mantelwrijving"],
             "u2": ["u2", "waterspanning", "waterdruk", "poriedruk", "schouder"]}
    low = {c: str(c).lower() for c in df.columns}
    for param, keys in names.items():
        if mapping[param]:
            continue
        for c, cl in low.items():
            if any(k in cl for k in keys):
                mapping[param] = c
                break
    if mapping["diepte"] is None and len(df.columns) >= 2:
        mapping["diepte"], mapping["qc"] = df.columns[0], df.columns[1]
        if len(df.columns) >= 3:
            mapping["fs"] = df.columns[2]
    return {"mapping": mapping, "is_qt_corrected": qc_qty == 14}


def normaliseer_naar_mpa(df: pd.DataFrame, mapping: dict, units: dict) -> list:
    factor = {"kpa": 1e-3, "pa": 1e-6, "mpa": 1.0}
    msgs = []
    for p in ("qc", "fs", "u2"):
        col = mapping.get(p)
        if col and col in df.columns:
            f = factor.get(str(units.get(col, "")).strip().lower())
            if f and f != 1.0:
                df[col] = pd.to_numeric(df[col], errors="coerce") * f
                msgs.append(f"{p} omgerekend → MPa")
    return msgs


# =====================================================================
# Classificatie (Robertson ISBT)
# =====================================================================
def bereken_isbt(qc, rf):
    qc_pa = (qc / PA_MPA).clip(lower=1e-3)
    rf = rf.clip(lower=0.1, upper=12.0)
    return np.sqrt((3.47 - np.log10(qc_pa)) ** 2 + (np.log10(rf) + 1.22) ** 2)


def grondsoort_uit_isbt(isbt):
    """ISBT → grove grondgroep (zand/klei/veen) volgens Ic-grenzen 2,60 / 3,60."""
    g = pd.Series("klei", index=isbt.index)
    g[isbt < 2.60] = "zand"
    g[isbt >= 3.60] = "veen"
    return g


# =====================================================================
# Spanningen & sterkte
# =====================================================================
def bereken_qt(qc, u2, a=0.80):
    return qc + (1 - a) * u2


def bereken_Rf(fs, qt):
    return (fs / qt.replace(0, np.nan)) * 100


def bereken_gamma_sat(qt, rf):
    """Lengkeek (2018): γ_sat = 19 − 4.12·log10(5/qt)/log10(30/Rf) [kN/m³]."""
    qt = qt.clip(lower=0.01); rf = rf.clip(lower=0.1, upper=12.0)
    noemer = np.log10(30.0 / rf).replace(0, np.nan)
    g = 19.0 - 4.12 * (np.log10(5.0 / qt) / noemer)
    return g.replace([np.inf, -np.inf], np.nan).clip(9, 22).fillna(17.0)


def bereken_u0(diepte_nap, gwl, knik, stijg, top_zand, indringing=0.0, gw=GAMMA_W):
    """4-zone waterdrukverloop [kPa] (gevalideerd tegen de Excel)."""
    z = np.asarray(diepte_nap, float)
    z_t, u_t = knik, (gwl - knik) * gw
    z_b, u_b = top_zand + indringing, (stijg - (top_zand + indringing)) * gw
    dn = z_b - z_t
    sl = (u_b - u_t) / dn if dn != 0 else 0.0
    return np.where(z > gwl, 0.0,
                    np.where(z > knik, (gwl - z) * gw,
                             np.where(z > z_b, sl * (z - z_t) + u_t, (stijg - z) * gw)))


def sigma_v0_uit_gamma(diepte_nap, gamma_sat, mv, gwl, boven_gws_reductie=2.0):
    """σv0 [kPa] door integratie van γ per punt (vochtig boven GWS)."""
    z = np.asarray(diepte_nap, float)
    g = np.asarray(gamma_sat, float)
    g_eff = np.where(z > gwl, np.maximum(g - boven_gws_reductie, 0.0), g)
    idx = np.argsort(-z)
    zs, gs = z[idx], g_eff[idx]
    sig = np.zeros_like(zs)
    acc, z_prev = 0.0, mv
    for i, (zi, gi) in enumerate(zip(zs, gs)):
        dz = z_prev - zi
        if dz > 0:
            acc += dz * gi
        sig[i] = acc
        z_prev = zi
    out = np.zeros_like(z); out[idx] = sig
    return out


def bereken_Su(qnet, nkt):
    return (qnet * 1000) / nkt


def karakteristieke_waarde(su, t=1.645):
    s = pd.Series(su).dropna()
    if s.empty:
        return {"n": 0, "gem": None, "VC": None, "kar": None}
    gem = float(s.mean())
    vc = float(s.std(ddof=1) / gem) if len(s) > 1 and gem else 0.0
    return {"n": int(s.size), "gem": gem, "VC": vc, "kar": max(gem * (1 - t * vc), 0.0)}


# =====================================================================
# Volledige analyse (automatisch, met defaults)
# =====================================================================
NKT_PER_GROND = {"klei": 15.0, "veen": 17.0}


def analyseer_gef(content: str, gwl_nap: float = 0.0, a_factor: float | None = None) -> dict:
    """Volledige automatische analyse van één GEF → dict voor de frontend."""
    g = parse_gef(content)
    df = g["df"]
    if df.empty:
        return {"ok": False, "error": "Geen meetdata in dit GEF-bestand."}
    det = detect_columns(df, g.get("quantity_info", {}), g.get("column_info", {}))
    cm = det["mapping"]
    if not cm["diepte"] or not cm["qc"]:
        return {"ok": False, "error": "Kon diepte/qc-kolom niet herkennen."}
    eenheid_msgs = normaliseer_naar_mpa(df, cm, g.get("units", {}))

    mv = g["maaiveld_nap"] if g["maaiveld_nap"] is not None else 0.0
    a = a_factor if a_factor is not None else (g.get("a_factor_gef") or 0.80)

    df = df.dropna(subset=[cm["qc"], cm["diepte"]]).reset_index(drop=True)
    diepte_nap = mv - df[cm["diepte"]]
    qc = df[cm["qc"]].clip(lower=0)
    fs = df[cm["fs"]] if cm["fs"] and cm["fs"] in df.columns else pd.Series(0.0, index=df.index)
    u2 = df[cm["u2"]] if (not det["is_qt_corrected"] and cm["u2"] and cm["u2"] in df.columns) \
        else pd.Series(0.0, index=df.index)

    qt = qc if det["is_qt_corrected"] else bereken_qt(qc, u2, a)
    rf = bereken_Rf(fs, qt).fillna(2.0)
    isbt = bereken_isbt(qc, rf)
    grondsoort = grondsoort_uit_isbt(isbt)
    gamma_sat = bereken_gamma_sat(qt, rf)

    base = float(diepte_nap.min())
    u0 = bereken_u0(diepte_nap, gwl_nap, knik=base - 0.01, stijg=gwl_nap,
                    top_zand=base - 0.01) / 1000.0   # ~hydrostatisch tot basis
    sigma = sigma_v0_uit_gamma(diepte_nap, gamma_sat, mv, gwl_nap) / 1000.0
    sigma_eff = np.clip(sigma - u0, 0, None)
    qnet = qt - sigma

    nkt = grondsoort.map(NKT_PER_GROND)
    geldig = nkt.notna() & (qnet > 0)
    su = pd.Series(np.nan, index=df.index)
    su[geldig] = bereken_Su(qnet[geldig], nkt[geldig])

    # laagsamenvatting (aaneengesloten grondsoort) — eenvoudige boorstaat
    lagen = _segmenteer(diepte_nap.values, grondsoort.values, su.values)
    kw = karakteristieke_waarde(su)

    def arr(s):
        return [None if (v is None or (isinstance(v, float) and np.isnan(v))) else round(float(v), 4)
                for v in s]

    return {
        "ok": True,
        "maaiveld_nap": round(mv, 2),
        "a_factor": round(a, 2),
        "kolommen": cm,
        "eenheid_meldingen": eenheid_msgs,
        "n": int(len(df)),
        "diepte_nap": arr(diepte_nap), "qc": arr(qc), "qt": arr(qt), "fs": arr(fs),
        "Rf": arr(rf), "gamma_sat": arr(gamma_sat), "u0": arr(u0 * 1000),
        "sigma_v0": arr(sigma * 1000), "sigma_eff": arr(sigma_eff * 1000),
        "qnet": arr(qnet), "Su": arr(su), "grondsoort": list(grondsoort.values),
        "lagen": lagen,
        "su_samenvatting": {k: (round(v, 1) if isinstance(v, float) else v) for k, v in kw.items()},
        "kleuren": LITHO_KLEUREN,
    }


def _segmenteer(z, g, su, min_dikte=0.3):
    """Maak laagblokken (boorstaat) uit aaneengesloten grondsoort, met gemiddelde Su."""
    n = len(z)
    if n == 0:
        return []
    order = np.argsort(-z)
    z, g, su = z[order], g[order], su[order]
    segs = []
    start = 0
    for i in range(1, n + 1):
        if i == n or g[i] != g[start]:
            top, onder = float(z[start]), float(z[i - 1] if i == n else z[i])
            sub = su[start:i]
            su_gem = float(np.nanmean(sub)) if np.any(~np.isnan(sub)) else None
            segs.append({"top": round(top, 2), "onder": round(onder, 2),
                         "grondsoort": g[start], "dikte": round(top - onder, 2),
                         "su_gem": round(su_gem, 1) if su_gem is not None else None})
            start = i
    # dunne lagen samenvoegen met dikkere buur
    while len(segs) > 1:
        d = [s["top"] - s["onder"] for s in segs]
        idx = int(np.argmin(d))
        if d[idx] >= min_dikte:
            break
        j = idx - 1 if idx == len(segs) - 1 else (idx + 1 if idx == 0 else
              (idx - 1 if d[idx - 1] >= d[idx + 1] else idx + 1))
        lo, hi = min(idx, j), max(idx, j)
        segs[lo:hi + 1] = [{"top": max(segs[lo]["top"], segs[hi]["top"]),
                            "onder": min(segs[lo]["onder"], segs[hi]["onder"]),
                            "grondsoort": segs[j]["grondsoort"],
                            "dikte": round(max(segs[lo]["top"], segs[hi]["top"]) -
                                           min(segs[lo]["onder"], segs[hi]["onder"]), 2),
                            "su_gem": segs[j]["su_gem"]}]
    # aangrenzende lagen van dezelfde grondsoort samenvoegen
    merged = []
    for s in segs:
        if merged and merged[-1]["grondsoort"] == s["grondsoort"]:
            merged[-1]["onder"] = s["onder"]
            merged[-1]["dikte"] = round(merged[-1]["top"] - s["onder"], 2)
        else:
            merged.append(dict(s))
    return merged
