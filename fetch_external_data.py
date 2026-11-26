"""Hämtar historiskt väder per bana och loppdag från Open-Meteo (gratis, ingen API-nyckel).

Körs från repots rotmapp:  python fetch_external_data.py
Resultatet sparas i data_external/weather.csv (en rad per lopp).
Skriptet sparar framsteg efter varje bana, så det går bra att köra det igen om det avbryts.
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

FIRST_SEASON = 2014
RAW = Path("data_raw")
OUT = Path("data_external")
OUT.mkdir(exist_ok=True)
PARTIAL = OUT / "weather_partial.csv"     # framsteg sparas här medan skriptet kör
FINAL = OUT / "weather.csv"

URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY = ["precipitation_sum", "temperature_2m_max"]


def read(name):
    return pd.read_csv(RAW / f"{name}.csv", na_values="\\N")


def fetch_circuit(lat, lng, start, end):
    """Dagligt väder för en plats och ett datumintervall. Vid 429 väntar vi en minut och försöker igen."""
    params = {
        "latitude": lat, "longitude": lng,
        "start_date": start, "end_date": end,
        "daily": ",".join(DAILY),
        "timezone": "auto",          # lokal tid på banan, så att datumet matchar loppdagen
    }
    for attempt in range(6):
        r = requests.get(URL, params=params, timeout=60)
        if r.status_code == 200:
            return pd.DataFrame(r.json()["daily"])
        if r.status_code == 429:
            print(f"  För många förfrågningar (429). Väntar 65 sekunder... (försök {attempt + 1}/6)")
            time.sleep(65)
        else:
            r.raise_for_status()
    return None    # gav upp, vi kör vidare nästa gång


def main():
    races = read("races")
    circuits = read("circuits")[["circuitId", "lat", "lng"]]
    races = races[races["year"] >= FIRST_SEASON].merge(circuits, on="circuitId", validate="many_to_one")

    # Arkivet släpar några dagar efter, och framtida lopp har ännu inget väder
    cutoff = (pd.Timestamp.today() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    races = races[races["date"] <= cutoff]

    # Läs in det som redan är hämtat från en tidigare körning
    if PARTIAL.exists():
        done = pd.read_csv(PARTIAL)
        pieces = [done]
        done_races = set(done["raceId"])
        print(f"Hittade sparade framsteg: {len(done_races)} lopp redan hämtade")
    else:
        pieces, done_races = [], set()

    circuit_ids = sorted(races["circuitId"].unique())
    for circuit_id in circuit_ids:
        grp = races[races["circuitId"] == circuit_id]
        if set(grp["raceId"]) <= done_races:
            continue    # hela banan klar sedan tidigare

        lat, lng = grp["lat"].iloc[0], grp["lng"].iloc[0]
        weather = fetch_circuit(lat, lng, grp["date"].min(), grp["date"].max())
        if weather is None:
            print("Gav upp för den här gången. Vänta en stund (gärna en timme) och kör skriptet igen.")
            sys.exit(1)

        merged = grp[["raceId", "date"]].merge(weather, left_on="date", right_on="time", how="left")
        merged = merged.rename(columns={
            "precipitation_sum": "rain_mm",
            "temperature_2m_max": "temp_max",
        })[["raceId", "rain_mm", "temp_max"]]
        pieces.append(merged)
        pd.concat(pieces, ignore_index=True).to_csv(PARTIAL, index=False)   # spara framsteg
        print(f"Bana {circuit_id}: {len(grp)} lopp hämtade")
        time.sleep(3)    # var snäll mot det gratis API:et

    out = pd.concat(pieces, ignore_index=True).drop_duplicates("raceId")
    out.to_csv(FINAL, index=False)
    PARTIAL.unlink(missing_ok=True)       # städa bort mellanfilen
    print(f"Klart! Sparade {len(out)} rader, {out['rain_mm'].isna().sum()} saknar väderdata")


if __name__ == "__main__":
    main()