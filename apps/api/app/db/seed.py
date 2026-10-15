"""
Seed script: populates the database with realistic mock data for development.
Run with: python -m app.db.seed
Demo login: demo@betlens.com / demo123456
"""
from __future__ import annotations

import asyncio
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import random
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models import (
    Bookmaker,
    ChatSession,
    Competition,
    Injury,
    JobRun,
    Lineup,
    Match,
    MatchEvent,
    ModelVersion,
    Notification,
    NotificationSetting,
    Odds,
    Player,
    PlayerStats,
    Prediction,
    Referee,
    Season,
    SeasonSimulation,
    Sport,
    Standing,
    Subscription,
    Team,
    TeamCompetition,
    TeamRating,
    TeamStats,
    User,
    UserFavorite,
    ValueOpportunity,
    Venue,
)
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base


# ─── Helpers ─────────────────────────────────────────────────────────────────

def uid() -> uuid.UUID:
    return uuid.uuid4()


def now_utc() -> datetime:
    return datetime.now(UTC)


def days_ago(n: int) -> datetime:
    return now_utc() - timedelta(days=n)


def days_ahead(n: int) -> datetime:
    return now_utc() + timedelta(days=n)


rng = random.Random(42)


# ─── Reference data ──────────────────────────────────────────────────────────

FOOTBALL_COMPETITIONS = [
    ("Premier League", "premier-league", "England", "PL"),
    ("La Liga", "la-liga", "Spain", "LL"),
    ("Serie A", "serie-a", "Italy", "SA"),
    ("Bundesliga", "bundesliga", "Germany", "BL"),
    ("Ligue 1", "ligue-1", "France", "L1"),
    ("UEFA Champions League", "champions-league", "Europe", "UCL"),
]

COMPETITION_LOGO_URLS = {
    "premier-league": "https://media.api-sports.io/football/leagues/39.png",
    "la-liga": "https://media.api-sports.io/football/leagues/140.png",
    "serie-a": "https://media.api-sports.io/football/leagues/135.png",
    "bundesliga": "https://media.api-sports.io/football/leagues/78.png",
    "ligue-1": "https://media.api-sports.io/football/leagues/61.png",
    "champions-league": "https://media.api-sports.io/football/leagues/2.png",
    "nba": "https://cdn.nba.com/logos/leagues/logo-nba.svg",
}

FOOTBALL_DATA_TEAM_IDS = {
    "man-city": 65,
    "arsenal": 57,
    "liverpool": 64,
    "chelsea": 61,
    "man-utd": 66,
    "tottenham": 73,
    "newcastle": 67,
    "aston-villa": 58,
}

FOOTBALL_TEAMS: dict[str, list[tuple[str, str]]] = {
    "premier-league": [
        ("Manchester City", "man-city"),
        ("Arsenal", "arsenal"),
        ("Liverpool", "liverpool"),
        ("Chelsea", "chelsea"),
        ("Manchester United", "man-utd"),
        ("Tottenham", "tottenham"),
        ("Newcastle", "newcastle"),
        ("Aston Villa", "aston-villa"),
    ],
    "la-liga": [
        ("Real Madrid", "real-madrid"),
        ("Barcelona", "barcelona"),
        ("Atletico Madrid", "atletico-madrid"),
        ("Sevilla", "sevilla"),
        ("Real Sociedad", "real-sociedad"),
        ("Villarreal", "villarreal"),
    ],
    "serie-a": [
        ("Inter Milan", "inter-milan"),
        ("AC Milan", "ac-milan"),
        ("Juventus", "juventus"),
        ("Napoli", "napoli"),
        ("Roma", "roma"),
        ("Lazio", "lazio"),
    ],
    "bundesliga": [
        ("Bayern Munich", "bayern-munich"),
        ("Borussia Dortmund", "dortmund"),
        ("RB Leipzig", "rb-leipzig"),
        ("Bayer Leverkusen", "leverkusen"),
        ("Eintracht Frankfurt", "frankfurt"),
    ],
    "ligue-1": [
        ("Paris Saint-Germain", "psg"),
        ("Marseille", "marseille"),
        ("Monaco", "monaco"),
        ("Lyon", "lyon"),
        ("Lille", "lille"),
    ],
    "champions-league": [],  # uses teams from other leagues
}

NBA_TEAMS = [
    ("Los Angeles Lakers", "lakers"),
    ("Golden State Warriors", "warriors"),
    ("Boston Celtics", "celtics"),
    ("Miami Heat", "heat"),
    ("Chicago Bulls", "bulls"),
    ("Brooklyn Nets", "nets"),
    ("Dallas Mavericks", "mavericks"),
    ("Phoenix Suns", "suns"),
    ("Denver Nuggets", "nuggets"),
    ("Milwaukee Bucks", "bucks"),
]

NBA_TEAM_IDS = {
    "lakers": 14,
    "warriors": 10,
    "celtics": 2,
    "heat": 16,
    "bulls": 5,
    "nets": 3,
    "mavericks": 7,
    "suns": 24,
    "nuggets": 8,
    "bucks": 17,
}

NBA_TEAM_ABBREVIATIONS = {
    "lakers": "lal",
    "warriors": "gsw",
    "celtics": "bos",
    "heat": "mia",
    "bulls": "chi",
    "nets": "bkn",
    "mavericks": "dal",
    "suns": "phx",
    "nuggets": "den",
    "bucks": "mil",
}

BOOKMAKER_NAMES = [
    ("Bet365", "bet365"),
    ("William Hill", "william-hill"),
    ("Betfair", "betfair"),
    ("Pinnacle", "pinnacle"),
    ("DraftKings", "draftkings"),
]

PLAYER_POSITIONS_FOOTBALL = ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"]
PLAYER_POSITIONS_NBA = ["PG", "SG", "SF", "PF", "C"]

FIRST_NAMES = ["James", "Luca", "Marco", "Carlos", "Antoine", "Kai", "Erling", "Vinicius",
               "Kylian", "Pedri", "Jude", "Phil", "Bukayo", "Trent", "Virgil"]
LAST_NAMES = ["Smith", "Müller", "García", "Rossi", "Dupont", "Silva", "Johnson",
              "Williams", "Brown", "Jones", "Davis", "Wilson", "Taylor", "Anderson"]


def random_name() -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def random_form() -> str:
    return "".join(rng.choices("WWDLL", weights=[3, 3, 2, 1, 1], k=5))


async def seed(session: AsyncSession) -> None:
    print("🌱 Seeding BetLens database...")

    # ── Sports ──────────────────────────────────────────────────────────────
    football = Sport(id=uid(), code="football", name="Football")
    basketball = Sport(id=uid(), code="basketball", name="Basketball")
    session.add_all([football, basketball])
    await session.flush()
    print("  ✓ Sports")

    # ── Venues ──────────────────────────────────────────────────────────────
    venues: list[Venue] = []
    venue_names = [
        ("Etihad Stadium", "Manchester"), ("Emirates Stadium", "London"),
        ("Anfield", "Liverpool"), ("Stamford Bridge", "London"),
        ("Old Trafford", "Manchester"), ("Tottenham Hotspur Stadium", "London"),
        ("Santiago Bernabéu", "Madrid"), ("Camp Nou", "Barcelona"),
        ("San Siro", "Milan"), ("Allianz Arena", "Munich"),
        ("Parc des Princes", "Paris"), ("Crypto.com Arena", "Los Angeles"),
        ("Chase Center", "San Francisco"), ("TD Garden", "Boston"),
    ]
    for vname, vcity in venue_names:
        v = Venue(id=uid(), name=vname, city=vcity, country="", capacity=rng.randint(40000, 90000))
        venues.append(v)
        session.add(v)
    await session.flush()
    print("  ✓ Venues")

    # ── Referees ─────────────────────────────────────────────────────────────
    referees: list[Referee] = []
    for _ in range(10):
        r = Referee(
            id=uid(), name=random_name(), country="England",
            avg_cards_per_match=round(rng.uniform(2.5, 5.5), 2),
            avg_pens_per_match=round(rng.uniform(0.1, 0.4), 2),
        )
        referees.append(r)
        session.add(r)
    await session.flush()
    print("  ✓ Referees")

    # ── Football competitions & seasons ──────────────────────────────────────
    football_competitions: dict[str, Competition] = {}
    football_seasons: dict[str, Season] = {}

    for name, slug, country, code in FOOTBALL_COMPETITIONS:
        comp = Competition(
            id=uid(), sport_id=football.id, name=name, slug=slug,
            country=country, provider_id=code, type="league",
            logo_url=COMPETITION_LOGO_URLS.get(slug),
        )
        session.add(comp)
        football_competitions[slug] = comp

    await session.flush()

    for slug, comp in football_competitions.items():
        season = Season(
            id=uid(), competition_id=comp.id, label="2025/26",
            starts_on=date(2025, 8, 1), ends_on=date(2026, 5, 31), is_current=True,
        )
        session.add(season)
        football_seasons[slug] = season
        comp.current_season_id = season.id

    await session.flush()
    print("  ✓ Football competitions & seasons")

    # ── NBA competition & season ──────────────────────────────────────────────
    nba_comp = Competition(
        id=uid(), sport_id=basketball.id, name="NBA", slug="nba",
        country="USA", provider_id="NBA", type="league",
        logo_url="https://cdn.nba.com/logos/leagues/logo-nba.svg",
    )
    session.add(nba_comp)
    await session.flush()

    nba_season = Season(
        id=uid(), competition_id=nba_comp.id, label="2025/26",
        starts_on=date(2025, 10, 22), ends_on=date(2026, 6, 30), is_current=True,
    )
    session.add(nba_season)
    nba_comp.current_season_id = nba_season.id
    await session.flush()
    print("  ✓ NBA competition & season")

    # ── Football teams & players ──────────────────────────────────────────────
    football_teams: dict[str, Team] = {}
    all_football_players: list[Player] = []

    for slug, comp in football_competitions.items():
        if slug == "champions-league":
            continue
        team_list = FOOTBALL_TEAMS.get(slug, [])
        for tname, tslug in team_list:
            team = Team(
                id=uid(), sport_id=football.id, name=tname, short_name=tname[:3].upper(),
                slug=tslug, country=comp.country,
                logo_url=(
                    f"https://crests.football-data.org/{FOOTBALL_DATA_TEAM_IDS[tslug]}.png"
                    if tslug in FOOTBALL_DATA_TEAM_IDS
                    else None
                ),
                venue_id=rng.choice(venues).id,
            )
            session.add(team)
            football_teams[tslug] = team

            tc = TeamCompetition(
                team_id=team.id, competition_id=comp.id, season_id=football_seasons[slug].id,
            )
            session.add(tc)

    await session.flush()

    for tslug, team in football_teams.items():
        for i in range(18):
            pos = PLAYER_POSITIONS_FOOTBALL[i % len(PLAYER_POSITIONS_FOOTBALL)]
            p = Player(
                id=uid(), team_id=team.id, name=random_name(), position=pos,
                birth_date=date(rng.randint(1995, 2004), rng.randint(1, 12), rng.randint(1, 28)),
                nationality="England", jersey_number=i + 1,
            )
            session.add(p)
            all_football_players.append(p)

    await session.flush()
    print(f"  ✓ {len(football_teams)} football teams, {len(all_football_players)} players")

    # ── NBA teams & players ───────────────────────────────────────────────────
    nba_teams: list[Team] = []
    all_nba_players: list[Player] = []

    for tname, tslug in NBA_TEAMS:
        team = Team(
            id=uid(), sport_id=basketball.id, name=tname, short_name=tname[:3].upper(),
            slug=tslug, country="USA",
            logo_url=(
                f"https://a.espncdn.com/i/teamlogos/nba/500/{NBA_TEAM_ABBREVIATIONS[tslug]}.png"
                if tslug in NBA_TEAM_ABBREVIATIONS
                else None
            ),
            venue_id=rng.choice(venues).id,
        )
        session.add(team)
        nba_teams.append(team)

        tc = TeamCompetition(team_id=team.id, competition_id=nba_comp.id, season_id=nba_season.id)
        session.add(tc)

    await session.flush()

    for team in nba_teams:
        for i in range(15):
            pos = PLAYER_POSITIONS_NBA[i % len(PLAYER_POSITIONS_NBA)]
            p = Player(
                id=uid(), team_id=team.id, name=random_name(), position=pos,
                birth_date=date(rng.randint(1993, 2003), rng.randint(1, 12), rng.randint(1, 28)),
                nationality="USA", jersey_number=rng.randint(1, 55),
            )
            session.add(p)
            all_nba_players.append(p)

    await session.flush()
    print(f"  ✓ {len(nba_teams)} NBA teams, {len(all_nba_players)} players")

    # ── Standings ─────────────────────────────────────────────────────────────
    for slug, comp in football_competitions.items():
        if slug == "champions-league":
            continue
        team_list = FOOTBALL_TEAMS.get(slug, [])
        for rank, (_, tslug) in enumerate(team_list, 1):
            team = football_teams[tslug]
            played = rng.randint(6, 10)
            won = rng.randint(0, played)
            drawn = rng.randint(0, played - won)
            lost = played - won - drawn
            gf = won * rng.randint(1, 3) + drawn * rng.randint(0, 1)
            ga = lost * rng.randint(1, 3) + drawn * rng.randint(0, 1)
            s = Standing(
                id=uid(), competition_id=comp.id, season_id=football_seasons[slug].id,
                team_id=team.id, rank=rank, played=played, won=won, drawn=drawn, lost=lost,
                goals_for=gf, goals_against=ga, points=won * 3 + drawn,
                form=random_form(),
            )
            session.add(s)

    await session.flush()
    print("  ✓ Standings")

    # ── Matches (past + upcoming) ─────────────────────────────────────────────
    all_matches: list[Match] = []
    football_team_list = list(football_teams.values())

    for slug, comp in football_competitions.items():
        if slug == "champions-league":
            continue
        teams_in_comp = [football_teams[tslug] for _, tslug in FOOTBALL_TEAMS.get(slug, [])]
        if len(teams_in_comp) < 2:
            continue

        # 5 past matches
        for i in range(5):
            home, away = rng.sample(teams_in_comp, 2)
            m = Match(
                id=uid(), competition_id=comp.id, season_id=football_seasons[slug].id,
                round=f"Matchday {i + 1}", kickoff_at=days_ago(rng.randint(3, 30)),
                status="finished", home_team_id=home.id, away_team_id=away.id,
                home_score=rng.randint(0, 4), away_score=rng.randint(0, 3),
                venue_id=home.venue_id, referee_id=rng.choice(referees).id,
            )
            session.add(m)
            all_matches.append(m)

        # 5 upcoming matches
        for i in range(5):
            home, away = rng.sample(teams_in_comp, 2)
            m = Match(
                id=uid(), competition_id=comp.id, season_id=football_seasons[slug].id,
                round=f"Matchday {i + 6}", kickoff_at=days_ahead(rng.randint(1, 14)),
                status="scheduled", home_team_id=home.id, away_team_id=away.id,
                venue_id=home.venue_id, referee_id=rng.choice(referees).id,
            )
            session.add(m)
            all_matches.append(m)

    # NBA matches
    for i in range(8):
        home, away = rng.sample(nba_teams, 2)
        status = "finished" if i < 4 else "scheduled"
        m = Match(
            id=uid(), competition_id=nba_comp.id, season_id=nba_season.id,
            round=f"Week {i + 1}", kickoff_at=days_ago(i * 2) if status == "finished" else days_ahead(i),
            status=status, home_team_id=home.id, away_team_id=away.id,
            home_score=rng.randint(95, 130) if status == "finished" else None,
            away_score=rng.randint(95, 130) if status == "finished" else None,
            venue_id=home.venue_id,
        )
        session.add(m)
        all_matches.append(m)

    await session.flush()
    print(f"  ✓ {len(all_matches)} matches")

    # ── Match events (for finished matches) ───────────────────────────────────
    finished = [m for m in all_matches if m.status == "finished"]
    for m in finished[:10]:
        for _ in range(rng.randint(1, 4)):
            ev = MatchEvent(
                id=uid(), match_id=m.id, minute=rng.randint(1, 90),
                type=rng.choice(["goal", "yellow", "red", "sub"]),
                team_id=rng.choice([m.home_team_id, m.away_team_id]),
                detail={},
            )
            session.add(ev)

    await session.flush()
    print("  ✓ Match events")

    # ── Lineups ───────────────────────────────────────────────────────────────
    upcoming = [m for m in all_matches if m.status == "scheduled"][:6]
    for m in upcoming:
        for team_id in [m.home_team_id, m.away_team_id]:
            lu = Lineup(
                id=uid(), match_id=m.id, team_id=team_id,
                formation="4-3-3", is_confirmed=False,
                starters=[{"player_id": str(uid()), "position": pos} for pos in PLAYER_POSITIONS_FOOTBALL[:11]],
                bench=[{"player_id": str(uid()), "position": "SUB"} for _ in range(7)],
            )
            session.add(lu)

    await session.flush()
    print("  ✓ Lineups")

    # ── Team ratings ──────────────────────────────────────────────────────────
    for team in football_team_list:
        tr = TeamRating(
            id=uid(), team_id=team.id, as_of_date=date.today(),
            model_version="football-dc-2026.10.1",
            attack=round(rng.uniform(0.7, 1.5), 3),
            defence=round(rng.uniform(0.7, 1.5), 3),
            elo=round(rng.uniform(1300, 1800), 1),
            home_advantage=round(rng.uniform(1.05, 1.2), 3),
        )
        session.add(tr)

    await session.flush()
    print("  ✓ Team ratings")

    # ── Predictions ───────────────────────────────────────────────────────────
    scheduled_matches = [m for m in all_matches if m.status == "scheduled"]
    all_predictions: list[Prediction] = []

    for m in scheduled_matches:
        home_win = round(rng.uniform(0.3, 0.6), 3)
        draw = round(rng.uniform(0.15, 0.3), 3)
        away_win = round(1 - home_win - draw, 3)
        confidence = rng.choice(["low", "medium", "high"])
        factors = [
            {"label": "Home attack strength", "direction": "up", "impact": round(rng.uniform(0.02, 0.08), 3)},
            {"label": "Away defensive record", "direction": "down", "impact": round(rng.uniform(0.01, 0.05), 3)},
            {"label": "Recent form", "direction": rng.choice(["up", "down"]), "impact": round(rng.uniform(0.01, 0.04), 3)},
        ]

        for market, selection, prob in [
            ("1x2", "home", home_win),
            ("1x2", "draw", draw),
            ("1x2", "away", away_win),
            ("totals", "over_2.5", round(rng.uniform(0.4, 0.7), 3)),
            ("btts", "yes", round(rng.uniform(0.35, 0.65), 3)),
        ]:
            pred = Prediction(
                id=uid(), match_id=m.id, market=market, selection=selection,
                subject_type="match", probability=prob, confidence=confidence,
                model_version="football-dc-2026.10.1", factors=factors,
            )
            session.add(pred)
            all_predictions.append(pred)

    await session.flush()
    print(f"  ✓ {len(all_predictions)} predictions")

    # ── Season simulations ────────────────────────────────────────────────────
    for slug, comp in football_competitions.items():
        if slug == "champions-league":
            continue
        for _, tslug in FOOTBALL_TEAMS.get(slug, []):
            team = football_teams[tslug]
            sim = SeasonSimulation(
                id=uid(), competition_id=comp.id, season_id=football_seasons[slug].id,
                team_id=team.id, as_of_date=date.today(),
                outcome_probabilities={
                    "title": round(rng.uniform(0.01, 0.35), 3),
                    "top4": round(rng.uniform(0.1, 0.8), 3),
                    "top6": round(rng.uniform(0.2, 0.9), 3),
                    "relegation": round(rng.uniform(0.01, 0.2), 3),
                },
            )
            session.add(sim)

    await session.flush()
    print("  ✓ Season simulations")

    # ── Bookmakers & Odds ─────────────────────────────────────────────────────
    bookmakers: list[Bookmaker] = []
    for bname, bslug in BOOKMAKER_NAMES:
        bm = Bookmaker(id=uid(), name=bname, slug=bslug)
        session.add(bm)
        bookmakers.append(bm)

    await session.flush()

    value_opps: list[ValueOpportunity] = []
    for m in scheduled_matches[:8]:
        for bm in bookmakers[:3]:
            for market, selection in [("1x2", "home"), ("1x2", "away"), ("totals", "over_2.5")]:
                price = round(rng.uniform(1.5, 5.0), 2)
                o = Odds(
                    id=uid(), match_id=m.id, bookmaker_id=bm.id,
                    market=market, selection=selection, price_decimal=price,
                )
                session.add(o)
                await session.flush()

                # Find matching prediction
                matching_pred = next(
                    (p for p in all_predictions if p.match_id == m.id and p.market == market and p.selection == selection),
                    None,
                )
                if matching_pred:
                    implied = round(1 / price / (1 / price + 0.05), 3)
                    edge = round(matching_pred.probability - implied, 3)
                    if edge >= 0.03:
                        vo = ValueOpportunity(
                            id=uid(), prediction_id=matching_pred.id, odds_id=o.id,
                            model_prob=matching_pred.probability, implied_prob=implied,
                            edge=edge,
                            expected_value=round(matching_pred.probability * (price - 1) - (1 - matching_pred.probability), 3),
                        )
                        session.add(vo)
                        value_opps.append(vo)

    await session.flush()
    print(f"  ✓ Bookmakers, odds, {len(value_opps)} value opportunities")

    # ── Injuries ──────────────────────────────────────────────────────────────
    for player in rng.sample(all_football_players, 12):
        inj = Injury(
            id=uid(), player_id=player.id,
            status=rng.choice(["injured", "doubtful", "suspended"]),
            reason=rng.choice(["Hamstring", "Knee", "Yellow card accumulation", "Illness"]),
            expected_return=date.today() + timedelta(days=rng.randint(3, 30)),
        )
        session.add(inj)

    await session.flush()
    print("  ✓ Injuries")

    # ── Player stats ──────────────────────────────────────────────────────────
    for player in rng.sample(all_football_players, 30):
        ps = PlayerStats(
            id=uid(), player_id=player.id, season_id=rng.choice(list(football_seasons.values())).id,
            metrics={
                "appearances": rng.randint(3, 10),
                "goals": rng.randint(0, 8),
                "assists": rng.randint(0, 6),
                "xg": round(rng.uniform(0.1, 5.0), 2),
                "xa": round(rng.uniform(0.1, 3.0), 2),
                "minutes": rng.randint(200, 900),
                "yellow_cards": rng.randint(0, 3),
                "red_cards": rng.randint(0, 1),
            },
        )
        session.add(ps)

    await session.flush()
    print("  ✓ Player stats")

    # ── Model versions ────────────────────────────────────────────────────────
    mv_football = ModelVersion(
        id=uid(), name="football-dc-2026.10.1", sport="football",
        is_active=True,
        metrics={
            "log_loss": 0.982, "brier_score": 0.218, "calibration_error": 0.024,
            "predictions_evaluated": 1240, "accuracy_vs_market": "+2.1%",
        },
    )
    mv_nba = ModelVersion(
        id=uid(), name="nba-elo-2026.10.1", sport="basketball",
        is_active=True,
        metrics={
            "log_loss": 0.671, "brier_score": 0.198, "calibration_error": 0.019,
            "predictions_evaluated": 380,
        },
    )
    session.add_all([mv_football, mv_nba])

    # ── Job runs ──────────────────────────────────────────────────────────────
    for job_name in ["sync_fixtures", "sync_standings_and_stats", "run_predictions"]:
        jr = JobRun(
            id=uid(), job_name=job_name,
            started_at=days_ago(1), finished_at=days_ago(1) + timedelta(minutes=2),
            status="success", stats={"records_updated": rng.randint(50, 500)},
        )
        session.add(jr)

    await session.flush()
    print("  ✓ Model versions & job runs")

    # ── Demo user ─────────────────────────────────────────────────────────────
    demo_user = User(
        id=uid(), email="demo@betlens.com",
        password_hash=hash_password("demo123456"),
        name="Demo User", role="user", plan="pro",
        email_verified_at=now_utc(), onboarding_completed=True,
        is_adult_confirmed=True, locale="en", timezone="Europe/London",
        odds_format="decimal",
    )
    session.add(demo_user)
    await session.flush()

    # Favorites: first 3 football teams
    fav_teams = list(football_teams.values())[:3]
    for team in fav_teams:
        fav = UserFavorite(
            id=uid(), user_id=demo_user.id, entity_type="team", entity_id=team.id,
        )
        session.add(fav)

    # Favorite competition
    fav_comp = UserFavorite(
        id=uid(), user_id=demo_user.id, entity_type="competition",
        entity_id=football_competitions["premier-league"].id,
    )
    session.add(fav_comp)

    # Subscription
    sub = Subscription(
        id=uid(), user_id=demo_user.id, plan="pro", status="active",
        current_period_end=now_utc() + timedelta(days=30),
    )
    session.add(sub)

    # Notification settings
    ns = NotificationSetting(
        id=uid(), user_id=demo_user.id, in_app=True, email=True, push=False,
    )
    session.add(ns)

    # Sample notification
    notif = Notification(
        id=uid(), user_id=demo_user.id, type="match_soon",
        payload={"message": "Manchester City vs Arsenal kicks off in 2 hours"},
        channel="in_app",
    )
    session.add(notif)

    # Chat session
    chat = ChatSession(
        id=uid(), user_id=demo_user.id, title="Premier League Analysis",
    )
    session.add(chat)

    await session.flush()
    print("  ✓ Demo user (demo@betlens.com / demo123456)")

    # ── Admin user ────────────────────────────────────────────────────────────
    admin_user = User(
        id=uid(), email="admin@betlens.com",
        password_hash=hash_password("admin123456"),
        name="Admin", role="admin", plan="pro",
        email_verified_at=now_utc(), onboarding_completed=True,
        is_adult_confirmed=True,
    )
    session.add(admin_user)
    await session.flush()
    print("  ✓ Admin user (admin@betlens.com / admin123456)")

    await session.commit()
    print("\n✅ Seed complete!")
    print("   Demo login : demo@betlens.com / demo123456")
    print("   Admin login: admin@betlens.com / admin123456")
    print("   API docs   : http://localhost:8000/docs")
    print("   Frontend   : http://localhost:3000")


async def main() -> None:
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print("⚠️  Database already has data. Skipping seed.")
            print("   To re-seed, drop and recreate the database first.")
            return
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())