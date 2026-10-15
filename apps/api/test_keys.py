import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Looks for .env in the project root (betlens/.env)
root = Path(__file__).resolve().parents[2]
load_dotenv(root / ".env")

def key(name):
    return (os.getenv(name) or "").strip().strip('"')

def report(name, ok, detail=""):
    print(f"{'OK  ' if ok else 'FAIL'}  {name}  {detail}")

# 1. API-Football (api-sports.io)
k = key("FOOTBALL_API_KEY")
if not k:
    report("API-Football", False, "FOOTBALL_API_KEY is empty")
else:
    try:
        r = requests.get("https://v3.football.api-sports.io/status",
                         headers={"x-apisports-key": k}, timeout=15)
        j = r.json()
        errs = j.get("errors")
        if r.status_code == 200 and not errs:
            req = j["response"]["requests"]
            report("API-Football", True, f"used {req['current']}/{req['limit_day']} requests today")
        else:
            report("API-Football", False, f"status {r.status_code} {errs}")
    except Exception as e:
        report("API-Football", False, str(e))

# 2. BallDontLie (NBA)
k = key("NBA_API_KEY")
if not k:
    report("BallDontLie", False, "NBA_API_KEY is empty")
else:
    try:
        r = requests.get("https://api.balldontlie.io/v1/teams",
                         headers={"Authorization": k}, timeout=15)
        ok = r.status_code == 200
        n = len(r.json().get("data", [])) if ok else ""
        report("BallDontLie", ok, f"status {r.status_code}" + (f", {n} teams" if ok else ""))
    except Exception as e:
        report("BallDontLie", False, str(e))

# 3. The Odds API (the /sports endpoint does not use credits)
k = key("ODDS_API_KEY")
if not k:
    report("The Odds API", False, "ODDS_API_KEY is empty")
else:
    try:
        r = requests.get("https://api.the-odds-api.com/v4/sports/",
                         params={"apiKey": k}, timeout=15)
        ok = r.status_code == 200
        report("The Odds API", ok,
               f"status {r.status_code}, credits remaining: {r.headers.get('x-requests-remaining')}")
    except Exception as e:
        report("The Odds API", False, str(e))

# 4. Gemini (only if you use it)
k = key("GEMINI_API_KEY")
if k:
    try:
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                         headers={"x-goog-api-key": k}, timeout=15)
        report("Gemini", r.status_code == 200, f"status {r.status_code}")
    except Exception as e:
        report("Gemini", False, str(e))