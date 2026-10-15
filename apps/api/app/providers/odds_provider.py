"""
The Odds API provider (free tier: 500 requests/month).
Docs: https://the-odds-api.com/liveapi/guides/v4/
"""
from __future__ import annotations
from typing import Any
import httpx

BASE_URL = "https://api.the-odds-api.com/v4"

SPORT_MAP = {
    "premier-league": "soccer_epl",
    "la-liga": "soccer_spain_la_liga",
    "serie-a": "soccer_italy_serie_a",
    "bundesliga": "soccer_germany_bundesliga",
    "ligue-1": "soccer_france_ligue_one",
    "champions-league": "soccer_uefa_champs_league",
    "nba": "basketball_nba",
}


async def get_odds(slug: str, api_key: str, regions: str = "eu,uk", markets: str = "h2h,totals", odds_format: str = "decimal") -> list[dict[str, Any]]:
    sport = SPORT_MAP.get(slug)
    if not sport:
        return []

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{BASE_URL}/sports/{sport}/odds",
            params={"apiKey": api_key, "regions": regions, "markets": markets, "oddsFormat": odds_format},
        )
        remaining = r.headers.get("x-requests-remaining", "?")
        print(f"[OddsAPI] Remaining: {remaining}")
        if r.status_code == 422:
            return []
        r.raise_for_status()
        data = r.json()

    results = []
    for event in data:
        home = event.get("home_team", "")
        away = event.get("away_team", "")
        bookmakers_data = []
        for bm in event.get("bookmakers", []):
            bm_name = bm.get("title", "")
            for market in bm.get("markets", []):
                market_key = market.get("key", "")
                outcomes = market.get("outcomes", [])
                if market_key == "h2h":
                    entry = {"bookmaker": bm_name, "market": "1x2", "outcomes": []}
                    for o in outcomes:
                        name = o.get("name", "")
                        price = o.get("price", 0)
                        selection = "home" if name == home else "away" if name == away else "draw"
                        entry["outcomes"].append({
                            "selection": selection,
                            "price_decimal": price,
                            "implied_probability": round(1 / price, 4) if price > 0 else 0,
                        })
                    bookmakers_data.append(entry)
        results.append({
            "event_id": event.get("id", ""),
            "home_team": home,
            "away_team": away,
            "commence_time": event.get("commence_time", ""),
            "sport": slug,
            "bookmakers": bookmakers_data,
        })
    return results