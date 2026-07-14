# Af te stemmen: grensspanning (k) en karakteristieke waarde (t, VC, uitschieters)

**Aanleiding.** In de Su-berekening stonden invoervelden voor de grensspannings-factor **k**
en de **t-factor**. Die suggereren een vrije keuze, terwijl het projectafspraken horen te zijn
die aansluiten op de aanpak voor waterkeringen.

**Status in de tool.** De velden zijn nu gemarkeerd als *voorlopig*; `k` is uit het hoofdscherm
gehaald (hij wordt alleen in de controleroute gebruikt). Er is **niets nieuws gebouwd** — eerst
afstemmen, dan bouwen.

---

## Wat de tool nu doet

| Onderdeel | Huidige aanpak in de tool | Waarom dit ter discussie staat |
|---|---|---|
| **Su** | `Su = q_net / Nkt`, met Nkt per grondlaag | Onomstreden; gevalideerd tegen de Deltares CPT-tool (~3 % bij gelijke Nkt) |
| **Grensspanning σ′vy** | *Hoofdroute:* SHANSEP omgekeerd — `σ′vy = σ′v0·(Su/(S·σ′v0))^(1/m)` | Resultaat van de gemeten Su. **Vraag:** is dit de bedoelde route? |
| | *Controleroute:* `σ′vy = k·q_net` (Mayne, k ≈ 0,33) | Generieke CPT-correlatie — **niet** de Nederlandse aanpak |
| **Karakteristieke waarde** | `Su_kar = Su_gem · (1 − t · VC)`, met **vaste t = 1,645** | 1,645 = 95 %-fractiel van de **normale** verdeling (σ bekend, n → ∞) |
| **VC** | Per materiaal (`VC_su`, nu default **0,25**) | **Vraag:** kloppen deze waarden per grondsoort? |
| **Uitschieters** | Worden **niet** verwijderd — alle Su-punten tellen mee | Beïnvloedt gemiddelde én spreiding, dus direct Su_kar |

---

## Vragen voor **Herman-Jaap** — methode

### 1. Grensspanning / POP
- In de Nederlandse aanpak komt de grensspanning uit **samendrukkingsproeven**: je voert
  **POP per grondlaag** in (σ′vy = σ′v0 + POP). Willen we dat zo in de tool, in plaats van
  σ′vy uit de CPT afleiden?
- Zo ja: **POP per grondlaag** aanleveren (karakteristieke waarde). Dan vervalt `k` volledig.
- Zo nee: is de SHANSEP-inversie (σ′vy uit de gemeten Su) de afgesproken route?

### 2. t-factor
- Moeten we naar **Student-t met n−1 vrijheidsgraden** (t hangt dan af van het aantal
  waarnemingen n), in plaats van een vaste 1,645?
- Rekenen we een **lokale** karakteristieke waarde of een **uitgemiddelde** (ruimtelijke
  middeling langs het glijvlak)? Dat scheelt fors:
  - lokaal: `X_kar = μ − t·σ`
  - uitgemiddeld: `X_kar = μ − t·σ·√(1/n + α²)`, met α² het deel van de variantie dat níét uitmiddelt
- Welke **α** (of Γ) hanteren we voor macrostabiliteit?

### 3. VC per grondsoort
- Is **VC = 0,25** de juiste default, of gelden er per grondsoort andere waarden
  (bijv. hoger voor veen)? Graag een tabel per laag.

### 4. Middelingsniveau
- Bepalen we de karakteristieke waarde **per sondering**, **per grondlaag**, of
  **per dijkvak** (over meerdere sonderingen samen)?

---

## Vragen voor **Jan** — uitschieters en subjectiviteit

### 5. Uitschieters
- Verwijderen we uitschieters vóórdat we gemiddelde en spreiding bepalen? Zo ja, met welk
  criterium (bijv. > 2σ, of op basis van de grondsoort-classificatie)?
- Concreet voorbeeld uit sondering **009**: er zit een dun lensje met hoge qc in de klei.
  Dat trekt het gemiddelde omhoog en de spreiding fors omhoog. Meenemen of eruit?

### 6. Laagindeling
- De karakteristieke waarde is heel gevoelig voor de **laagdikte**. Op 009 geeft één kleilaag
  van ~12 m een data-VC van **0,90**; verdeel je hem in vier lagen, dan zakt die sterk.
  Welke minimale laagdikte / indelingsregel spreken we af?

### 7. Voorboorzone en q_net < 0
- Metingen in de voorboorzone worden nu uitgesloten (uit de GEF-header).
- Punten met `q_net < 0` (bovenin, waar qc ≈ 0) geven geen Su. Akkoord?

---

## Wat we doen na het overleg

1. Besluiten vastleggen in dit document.
2. De tool aanpassen: POP-invoer per laag (indien gewenst), Student-t + ruimtelijke middeling,
   uitschieter-behandeling als expliciete, gedocumenteerde optie.
3. Opnieuw valideren tegen de Deltares CPT-tool en tegen labproeven.

---

## Ter info — wat wél al vaststaat

- **Su-berekening zelf is gevalideerd**: bij gelijke Nkt komt onze Su binnen ~3 % overeen met
  de Deltares CPT-tool (sondering 009, per laag).
- De **rekenketen** is inmiddels correct: Nkt levert Su, en de grensspanning volgt daarná uit
  SHANSEP — niet andersom.
- Het openstaande punt gaat **niet over Su**, maar over hoe we van Su naar een
  **karakteristieke** waarde gaan.
