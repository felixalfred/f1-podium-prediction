"""Streamlit-app: förutsäger pallplatser i Formel 1 (2014-2026)."""
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

HERE = Path(__file__).parent
FEATURES = [
    "grid_adj", "gap_to_pole_pct", "grid_vs_quali",
    "driver_avg_finish_5", "driver_podium_rate_5",
    "team_avg_finish_5", "team_podium_rate_5",
]
LAST_TRAIN_YEAR = 2024   # modellen är tränad på 2014-2024


@st.cache_resource
def load_model():
    return joblib.load(HERE / "models" / "podium_model.joblib")


@st.cache_data
def load_data():
    return pd.read_csv(HERE / "data_app" / "race_features.csv")


st.set_page_config(page_title="F1: pallplatsprognos", page_icon="🏁")

model = load_model()
data = load_data()

st.title("🏁 Vem hamnar på pallen?")
st.write(
    "En maskininlärningsmodell (logistisk regression) som gissar vilka förare som tar "
    "pallplats i ett Formel 1-lopp, utifrån sådant som är känt **före** start: "
    "startposition, kvalresultat samt förarens och stallets form."
)

tab_race, tab_own, tab_about = st.tabs(["Välj ett lopp", "Eget scenario", "Om modellen"])

# ------------------------------------------------------------------ Flik 1
with tab_race:
    year = st.selectbox("Säsong", sorted(data["year"].unique(), reverse=True))
    races = data[data["year"] == year].sort_values("round")
    race_name = st.selectbox("Lopp", races["race_name"].unique())

    race = races[races["race_name"] == race_name].copy()
    race["Chans till pallplats"] = model.predict_proba(race[FEATURES])[:, 1]
    race = race.sort_values("Chans till pallplats", ascending=False).reset_index(drop=True)
    race["Modellens topp 3"] = ["✅" if i < 3 else "" for i in race.index]

    if year > LAST_TRAIN_YEAR:
        st.info(f"{year} ligger utanför modellens träningsdata (2014-{LAST_TRAIN_YEAR}), "
                "så modellen har aldrig sett det här loppet.")
    else:
        st.caption(f"{year} ingår i modellens träningsdata, så träffsäkerheten här ser bättre ut än den är på nya lopp.")

    shown = pd.DataFrame({
        "Förare": race["driver"],
        "Stall": race["constructor_name"],
        "Startplats": race["grid"],
        "Chans till pallplats": (race["Chans till pallplats"] * 100).round(1),
        "Modellens topp 3": race["Modellens topp 3"],
        "Verklig målplats": race["position"].apply(lambda p: "Bröt/ej klassad" if pd.isna(p) else str(int(p))),
    })
    st.dataframe(shown, hide_index=True, width="stretch")
    st.bar_chart(shown.set_index("Förare")["Chans till pallplats"], y_label="Chans till pallplats (%)")

    hits = int(race.head(3)["podium"].sum())
    st.write(f"**Resultat:** {hits} av modellens 3 favoriter tog pallplats.")

# ------------------------------------------------------------------ Flik 2
with tab_own:
    st.write("Skriv in uppgifter om en tänkt förare i ett tänkt lopp och se vad modellen gissar.")
    c1, c2 = st.columns(2)
    with c1:
        grid = st.slider("Startposition", 1, 22, 5)
        gap = st.slider("Avstånd till pole i kvalet (%)", 0.0, 8.0, 1.0, 0.1,
                        help="0 = pole. 1 betyder att kvaltiden är 1 % långsammare än polepositionen.")
        gvq = st.slider("Kvalplats minus startplats", -10, 10, 0,
                        help="Positivt = föraren startar längre fram än han kvalade. Negativt = bakåtflyttad.")
    with c2:
        d_avg = st.slider("Förarens snittplacering, 5 senaste lopp", 1.0, 20.0, 8.0, 0.5)
        d_pod = st.slider("Förarens andel pallplatser, 5 senaste", 0.0, 1.0, 0.2, 0.1)
        t_avg = st.slider("Stallets snittplacering, 5 senaste lopp", 1.0, 20.0, 8.0, 0.5)
        t_pod = st.slider("Stallets andel pallplatser, 5 senaste", 0.0, 1.0, 0.2, 0.1)

    x = pd.DataFrame([{
        "grid_adj": grid, "gap_to_pole_pct": gap, "grid_vs_quali": gvq,
        "driver_avg_finish_5": d_avg, "driver_podium_rate_5": d_pod,
        "team_avg_finish_5": t_avg, "team_podium_rate_5": t_pod,
    }])[FEATURES]
    p = model.predict_proba(x)[0, 1]
    st.metric("Modellens chans till pallplats", f"{p:.1%}")
    st.caption("Varning: modellen har inte tränats på orimliga kombinationer (t.ex. pole med 8 % avstånd), "
               "så svaret är mest meningsfullt för realistiska värden.")

# ------------------------------------------------------------------ Flik 3
with tab_about:
    st.markdown(
        """
**Data:** Formula 1 World Championship (Kaggle, bygger på Jolpica-F1), säsongerna 2014-2026.

**Modell:** logistisk regression, tränad på 2014-2024. Lopp från 2025-2026 användes som testdata.

**Hur bra är den?** På testdatan (39 lopp) hamnade i snitt ungefär två av modellens tre favoriter på pallen,
men en enkel regel ("de tre som startar längst fram") klarade sig nästan lika bra.
Startpositionen är den överlägset viktigaste faktorn.

**Begränsningar:** Modellen ser bara det som är känt före start. Haverier, safety car, regn och strategi
kan den inte förutse. Se det som en kvalificerad gissning, inte ett facit.

Källkod och analys: se GitHub-repot.
"""
    )