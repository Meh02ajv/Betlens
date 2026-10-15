import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
key = (os.getenv("FOOTBALL_API_KEY") or "").strip().strip('"')

for season in (2026, 2025):
    r = requests.get(
        "https://v3.football.api-sports.io/standings",
        params={"league": 39, "season": season},
        headers={"x-apisports-key": key},
        timeout=20,
    )
    j = r.json()
    print(f"season {season}: HTTP {r.status_code}, errors={j.get('errors')}, results={j.get('results')}")