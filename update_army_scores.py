
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
import sys

# --------------------------------
# SETTINGS
# --------------------------------

SERVER = 2
WORLD = 74
SCORE_TYPE = "army_score_main"
BATCH_SIZE = 5

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "data" / "player_centers.csv"
OUTPUT_FILE = BASE_DIR / "data" / "latest_army_scores.csv"

# --------------------------------
# LOAD PLAYER NAMES
# --------------------------------

df = pd.read_csv(INPUT_FILE)

player_names = (
    df["playerName"]
    .dropna()
    .unique()
    .tolist()
)

print(f"Players to scrape: {len(player_names)}")

if not player_names:
    sys.exit("No player names found. Stopping.")

# --------------------------------
# API
# --------------------------------

url = "https://api.ika-map.com/v1/players/growth-multiple"

session = requests.Session()
all_records = []
failed_batches = 0

batches = [
    player_names[i:i + BATCH_SIZE]
    for i in range(0, len(player_names), BATCH_SIZE)
]

# --------------------------------
# SCRAPE
# --------------------------------

for i, batch in enumerate(batches, start=1):

    print(f"Batch {i}/{len(batches)}")

    params = [
        ("server", SERVER),
        ("world", WORLD),
        ("scoreType", SCORE_TYPE)
    ]

    for name in batch:
        params.append(("name", name))

    try:
        response = session.get(
            url,
            params=params,
            timeout=180
        )

        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            print("API error:", result)
            failed_batches += 1
            continue

        for player in result["data"]:

            for record in player["playerScore"]:

                d = record["d"]

                date_string = (
                    f'{d["y"]}-{int(d["m"]):02d}-{int(d["d"]):02d} '
                    f'{d["t"]}'
                )

                all_records.append({
                    "playerName": player["playerName"],
                    "datetime": datetime.strptime(
                        date_string, "%Y-%m-%d %H:%M"
                    ),
                    "army_score": record["p"]
                })

        print(f"  Retrieved {len(result['data'])} players")

    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"  Request failed: {e}")
        failed_batches += 1

# --------------------------------
# CHECK RESULTS
# --------------------------------

if failed_batches:
    sys.exit(
        f"Scraping incomplete: {failed_batches} batch(es) failed. "
        "Existing CSV has been left untouched."
    )

if not all_records:
    sys.exit("No records retrieved. Existing CSV has been left untouched.")

# --------------------------------
# GET LATEST ARMY SCORE PER PLAYER
# --------------------------------

history_df = pd.DataFrame(all_records)

history_df["datetime"] = pd.to_datetime(history_df["datetime"])

latest_scores = (
    history_df
    .sort_values("datetime")
    .groupby("playerName")
    .tail(1)
    [["playerName", "army_score"]]
    .sort_values("playerName")
    .reset_index(drop=True)
)

# --------------------------------
# EXPORT FINAL CSV
# --------------------------------

latest_scores.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSCRAPING COMPLETE!")
print(f"Players retrieved: {len(latest_scores)}")
print(f"Saved: {OUTPUT_FILE}")
print(latest_scores)
