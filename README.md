# Förutsägelse av pallplatser i Formel 1

Projektuppgift i kursen *Statistisk programmering och maskininlärning* (Nackademin, Business Intelligence & Data Engineering).

Kan man förutsäga vilka förare som tar pallplats (topp 3) i ett Formel 1-lopp, utifrån sådant som är känt **före** start, och vilka faktorer betyder mest?

## Prova appen

**Live-app:** https://f1-podium-prediction-123.streamlit.app/

Välj ett lopp (2014-2026) och se modellens pallplatsprognos per förare, eller mata in ett eget scenario.

## Resultat i korthet

- **Data:** [Formula 1 World Championship (1950-2026)](https://www.kaggle.com/datasets/atharvranjan/formula-1-world-championship-1950-present) (Kaggle, bygger på Jolpica-F1, CC0), säsongerna 2014-2026.
- **Modell:** logistisk regression med sju features i fyra grupper: startposition, kvalresultat, förarens form och stallets form.
- **Utvärdering:** tidsbaserad uppdelning (träning 2014-2022, validering 2023-2024, test 2025-2026) och tidsmedveten korsvalidering.
- **Viktigaste fyndet:** startpositionen är överlägset viktigast. Modellerna är något bättre än en enkel baslinje ("startposition") på testdatan (PR-AUC ca 0,74 mot 0,70), men skillnaden är **inte statistiskt säkerställd** (bootstrap över 39 testlopp).
- **Extra:** extern väderdata (Open-Meteo) och en ensemble gav ingen märkbar förbättring, vilket redovisas i kapitel 8.

## Innehåll

| Fil/mapp | Innehåll |
|---|---|
| `notebooks/f1_podium_prediction.ipynb` | Hela analysen, från problem till slutsats |
| `app.py` | Streamlit-appen |
| `fetch_external_data.py` | Hämtar väderdata från Open-Meteo |
| `data_raw/` | Rådata (CSV-tabeller från Kaggle) |
| `data_external/` | Extern väderdata |
| `data_app/`, `models/` | Data och sparad modell som appen använder |
| `requirements.txt` | Python-paket |

## Köra projektet lokalt

1. Klona repot och skapa en virtuell miljö:
   ```
   git clone https://github.com/felixalfred/f1-podium-prediction.git
   cd f1-podium-prediction
   python -m venv .venv
   .venv\Scripts\activate        # Windows (Mac/Linux: source .venv/bin/activate)
   ```
2. Installera paketen:
   ```
   pip install -r requirements.txt
   ```
3. **Notebooken:** öppna `notebooks/f1_podium_prediction.ipynb` och välj *Run All*.
4. **Appen:** `streamlit run app.py`

## Begränsningar

Modellen ser bara det som är känt före start. Haverier, safety car, regn under loppet och strategi kan den inte förutse. Testdatan är liten (39 lopp), så små skillnader mellan modeller går inte att skilja från slump. Se kapitel 10 i notebooken.