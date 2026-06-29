# Wijzigingen & overgenomen van de Deltares CPT-tool

## Overgenomen uit de Deltares CPT-tool (POVM / schematiseringshandleiding)
- **SHANSEP-methode**: Su = S·σ′v0·OCRᵐ, met grensspanning σ′vy = k·q_net (Mayne,
  k≈0,33). Naast de Nkt-methode, kies je nu per analyse de methode.
- **Karakteristieke waarde**: Su_kar = Su_gem·(1 − t·VC), met t instelbaar
  (1,645 = 5%-ondergrens). Per sondering én per grondlaag.
- **VC_su per materiaal** (variatiecoëfficiënt) — net als de Deltares-tabel.
- **Bewerkbare materialentabel** (γ_sat, γ_unsat, S, m, Nkt, VC) — Deltares
  "Materiaaleigenschappen".
- **Meerdere Su-profielen over elkaar** (Su per punt + gelineariseerd su- en
  su_kar-profiel per laag) — zoals het Deltares Su-paneel.
- **Vergelijk-tab**: laad een Deltares-export (Su per NAP) en zie de afwijking
  (Δ, RMSE). Hiermee is onze tool **gevalideerd tegen de Deltares-tool**
  (sondering 009: ~1–3 % verschil per laag).

## Wat we in onze tool hebben veranderd/toegevoegd

### Waterdruk (u₀)
- Oud 3-zone-knikmodel vervangen door het **4-zone-model uit de Excel van
  Herman-Jaap** (knikpunt → lineaire overgang → stijghoogte zandpakket),
  **exact gevalideerd op 0,00 kPa**. Invoer: GWS, knikpunt, stijghoogte,
  top zandpakket, indringingslengte — globaal én per sondering.

### Classificatie / grondopbouw
- **Officiële Robertson ISBT-classificatie** (Ic-grenzen 1,31/2,05/2,60/2,95/3,60)
  i.p.v. ad-hoc qc-drempels.
- **Flexibele grondopbouwtabel** (bovenkant + laagtype), projectdefault + per
  sondering aanpasbaar, met afgeleide top/onder/dikte.
- **Robertson-suggestieknop** (met instelbare min. laagdikte) en
  **SHZ-dieptezones-knop**.
- **Boorstaat** (gekleurde lithologie: zand=geel, klei=groen, veen=bruin) naast
  qc, met **Rf-curve** en **GWS-lijn**.
- Live preview (grafiek volgt de tabel) en waarschuwingen bij lagen buiten het
  meetbereik.

### Spanningen / normalisatie
- **Eenheidsnormalisatie**: qc/fs/u₂ automatisch naar MPa o.b.v. de GEF-header.
- **a-factor uit de GEF** gelezen (anders standaard 0,80).
- **Rf = fs/qt** (i.p.v. fs/qc), conform Robertson/Lengkeek.
- **γ uit qc/Rf (Lengkeek 2018)** als alternatief naast γ per grondlaag.
- **GWS per sondering** + maaiveld altijd vers (geen stille fouten).
- Tussengrootheden qt, q_net, **Bq**, **Qt** berekend en getoond.

### Su
- **Nkt- én SHANSEP-methode**, karakteristieke waarde per laag.

### Overig
- Audit-fixes: u₂-eenheidcontrole, dode code verwijderd, funderingslaag-waarschuwing.
- **Controlebestand** `CPT_kern_berekeningen.py`: gedocumenteerde, gevalideerde
  rekenkern (los na te rekenen).

## Hosting
- De volledige tool draait als **Docker-container** op de Hetzner-server
  (`http://178.104.119.117:8080`, wachtwoord instelbaar via `APP_PASSWORD`).
- **Auto-deploy**: de server haalt elke ~3 min nieuwe versies van GitHub en
  herbouwt automatisch (`auto-deploy.sh` via cron).
