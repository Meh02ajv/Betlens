import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
key = (os.getenv("FOOTBALL_DATA_ORG_KEY") or "").strip().strip('"')

r = requests.get(
    "https://api.football-data.org/v4/competitions/PL/standings",
    headers={"X-Auth-Token": key},
    timeout=20,
)
print("HTTP", r.status_code)
if r.status_code == 200:
    j = r.json()
    print("Season:", j["season"]["startDate"], "to", j["season"]["endDate"])
    for row in j["standings"][0]["table"][:3]:
        print(row["position"], row["team"]["name"], row["points"])
else:
    print(r.text[:300])