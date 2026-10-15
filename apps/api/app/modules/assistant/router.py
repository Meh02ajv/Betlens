from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any, AsyncGenerator, Awaitable, Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import CurrentUserId, DbSession
from app.db.models import ChatMessage, ChatSession, UsageCounter

log = logging.getLogger(__name__)

router = APIRouter()

SYSTEM_PROMPT = """You are BetLens Assistant, a sports analytics guide for football and NBA.
Rules:
1. Use tools to get every number you state. Never invent statistics, odds or probabilities.
2. Always give probabilities as percentages, with a confidence level and the top factors.
3. State data freshness when relevant (for example "lineups not yet confirmed").
4. You provide analysis, not guarantees. Never say a result is certain or a "sure bet".
5. Do not encourage betting more, chasing losses or using money the user cannot afford to lose.
6. If asked for advice, compare model probability with implied odds probability, explain the trade-offs, and remind the user the decision is theirs.
7. If the user seems distressed about gambling, respond with empathy and suggest support services.
8. If data is missing or a market is not covered, say so plainly and offer the closest alternative.
9. Be concise: short paragraphs, then a probability card summary.
10. Never use phrases like "sure win", "guaranteed", or "can't lose"."""

# Extra instructions used only by the Gemini path, which has no tools.
LIVE_DATA_RULES = """
IMPORTANT OVERRIDES FOR THIS CHAT:
- No tools are available. The LIVE DATA section below (if present) is your only source of facts.
- Only state scores, dates, standings and odds that appear in LIVE DATA. If something is not there, say you do not have that data.
- No prediction model is connected yet. Do not present win or scoring probabilities as if they came from a model. You may discuss form and context from the data, and explain what a probability would depend on.
- Kickoff times in LIVE DATA are UTC. Mention that when you quote times.
"""

SUGGESTED_PROMPTS = [
    "Who is most likely to score in tonight's match?",
    "Is there value in the top match this weekend?",
    "What are the chances of over 2.5 goals?",
    "Show me the standings for the Premier League",
    "What's the win probability for the next Lakers game?",
]


@router.get("/sessions", response_model=list[dict])
async def list_sessions(user_id: CurrentUserId, db: DbSession) -> list[dict]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.post("/sessions", response_model=dict, status_code=201)
async def create_session(user_id: CurrentUserId, db: DbSession) -> dict:
    session = ChatSession(user_id=user_id, title="New Chat")
    db.add(session)
    await db.flush()
    return {
        "id": str(session.id),
        "title": session.title,
        "suggested_prompts": SUGGESTED_PROMPTS,
    }


@router.patch("/sessions/{session_id}", response_model=dict)
async def rename_session(
    session_id: uuid.UUID,
    data: dict,
    user_id: CurrentUserId,
    db: DbSession,
) -> dict:
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = data.get("title", session.title)
    await db.flush()
    return {"id": str(session.id), "title": session.title}


@router.delete("/sessions/{session_id}", status_code=200)
async def delete_session(
    session_id: uuid.UUID,
    user_id: CurrentUserId,
    db: DbSession,
) -> dict:
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    return {"message": "Deleted"}


@router.get("/sessions/{session_id}/messages", response_model=list[dict])
async def get_messages(
    session_id: uuid.UUID,
    user_id: CurrentUserId,
    db: DbSession,
) -> list[dict]:
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "tool_calls": m.tool_calls,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: uuid.UUID,
    data: dict,
    user_id: CurrentUserId,
    db: DbSession,
) -> StreamingResponse:
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    from app.db.models import User

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()
    counter = await db.scalar(
        select(UsageCounter).where(
            UsageCounter.user_id == user_id,
            UsageCounter.date == today,
        )
    )

    daily_limit = (
        settings.assistant_pro_daily_limit
        if user.plan == "pro"
        else settings.assistant_free_daily_limit
    )
    if counter and counter.assistant_messages >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily message limit of {daily_limit} reached.",
        )

    user_message = data.get("content", "")
    context = data.get("context", {})

    user_msg = ChatMessage(session_id=session_id, role="user", content=user_message)
    db.add(user_msg)
    await db.flush()

    if counter:
        counter.assistant_messages += 1
    else:
        counter = UsageCounter(user_id=user_id, date=today, assistant_messages=1)
        db.add(counter)
    await db.flush()

    return StreamingResponse(
        _stream_response(session_id, user_message, context, db),
        media_type="text/event-stream",
    )


def _detect_ai_provider() -> str:
    import os

    if settings.anthropic_api_key:
        return "claude"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    return "mock"


async def _stream_response(
    session_id: uuid.UUID,
    user_message: str,
    context: dict,
    db: DbSession,
) -> AsyncGenerator[str, None]:
    provider = _detect_ai_provider()
    if provider == "claude":
        async for chunk in _claude_stream(session_id, user_message, context, db):
            yield chunk
    elif provider == "gemini":
        async for chunk in _gemini_stream(session_id, user_message, db):
            yield chunk
    else:
        async for chunk in _mock_stream(session_id, user_message, db):
            yield chunk


async def _mock_stream(
    session_id: uuid.UUID,
    user_message: str,
    db: DbSession,
) -> AsyncGenerator[str, None]:
    response_text = (
        "I'm the BetLens Assistant (mock mode).\n\n"
        "To enable real AI, set one of:\n"
        "- GEMINI_API_KEY — Free at https://aistudio.google.com/apikey\n"
        "- ANTHROPIC_API_KEY — Free credits at https://console.anthropic.com\n\n"
        "⚠️ Estimates based on statistical models. No outcome is guaranteed."
    )

    full_response = ""
    for word in response_text.split(" "):
        chunk = word + " "
        full_response += chunk
        yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        await asyncio.sleep(0.03)

    db.add(
        ChatMessage(
            session_id=session_id, role="assistant", content=full_response.strip()
        )
    )
    await db.flush()
    await db.commit()
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


# ─────────────────────────────────────────────────────────────────────────────
# Live data for the assistant (standings, fixtures, odds, NBA)
# ─────────────────────────────────────────────────────────────────────────────

# League slugs match the slugs in your competitions table / provider.
COMPETITIONS: dict[str, list[str]] = {
    "premier-league": ["premier league", "epl", "english premier"],
    "la-liga": ["la liga", "laliga"],
    "serie-a": ["serie a"],
    "bundesliga": ["bundesliga"],
    "ligue-1": ["ligue 1", "ligue1"],
    "champions-league": ["champions league", "ucl"],
}
ALL_FOOTBALL_SLUGS = list(COMPETITIONS.keys())

STANDINGS_WORDS = [
    "standing",
    "table",
    "rank",
    "position",
    "points",
    "top of the league",
    "relegation",
]
FIXTURE_WORDS = [
    "tonight",
    "today",
    "tomorrow",
    "weekend",
    "next",
    "fixture",
    "match",
    "game",
    "play",
    "score",
    "result",
    "schedule",
    "kick",
    "goal",
    "win",
    "chance",
    "over",
    "under",
    "value",
]
ODDS_WORDS = ["odds", "value", "price", "bookmaker", "implied", "bet"]
NBA_WORDS = [
    "nba",
    "basketball",
    "lakers",
    "celtics",
    "warriors",
    "bulls",
    "knicks",
    "heat",
    "nets",
    "bucks",
    "suns",
    "mavericks",
    "nuggets",
    "clippers",
    "76ers",
    "sixers",
]

# Small in-memory cache so repeated questions do not burn API limits / odds credits.
_CACHE: dict[str, tuple[float, Any]] = {}


async def _cached(key: str, ttl: float, factory: Callable[[], Awaitable[Any]]) -> Any:
    now = time.monotonic()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = await factory()
    if value:  # never cache empty results (they usually mean a failed call)
        _CACHE[key] = (now, value)
    return value


def _compact(obj: Any, limit: int = 4000) -> str:
    return json.dumps(obj, default=str, separators=(",", ":"), ensure_ascii=False)[
        :limit
    ]


def _format_standings(slug: str, rows: list[dict]) -> str:
    league_name = slug.replace("-", " ").title()
    lines = [f"{league_name} standings:"]
    for row in rows[:20]:
        lines.append(
            f"{row.get('rank', '?')}. {row.get('team_name', 'Unknown')} - "
            f"{row.get('points', 0)} points, "
            f"{row.get('played', 0)} played, "
            f"{row.get('won', 0)} wins, "
            f"{row.get('drawn', 0)} draws, "
            f"{row.get('lost', 0)} losses."
        )
    return "\n".join(lines)


def _parse_kickoff(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _pick_matches(
    rows: list[dict], now: datetime | None = None, max_rows: int = 12
) -> list[dict]:
    """Keep matches from yesterday to 4 days ahead; fall back to the next few upcoming."""
    now = now or datetime.now(UTC)
    start, end = now - timedelta(days=1), now + timedelta(days=4)
    dated = []
    for r in rows:
        k = _parse_kickoff(r.get("kickoff_at"))
        if k:
            dated.append((k, r))
    dated.sort(key=lambda x: x[0])
    window = [(k, r) for k, r in dated if start <= k <= end]
    if not window:
        window = [(k, r) for k, r in dated if k > now][:5]
    out = []
    for k, r in window[:max_rows]:
        hs, as_ = r.get("home_score"), r.get("away_score")
        out.append(
            {
                "kickoff_utc": k.strftime("%Y-%m-%d %H:%M"),
                "status": r.get("status"),
                "home": r.get("home_team_name"),
                "away": r.get("away_team_name"),
                "score": f"{hs}-{as_}" if hs is not None and as_ is not None else None,
            }
        )
    return out


async def _build_live_context(user_message: str, db: DbSession) -> str:
    # Imported here so the assistant still loads if the providers module has a problem.
    from app.providers.provider_factory import (
        fetch_fixtures,
        fetch_nba_games,
        fetch_odds,
        fetch_standings,
    )

    text = user_message.lower()
    slugs = [s for s, kws in COMPETITIONS.items() if any(k in text for k in kws)]
    want_nba = any(w in text for w in NBA_WORDS)
    want_standings = any(w in text for w in STANDINGS_WORDS)
    want_odds = any(w in text for w in ODDS_WORDS)
    want_fixtures = any(w in text for w in FIXTURE_WORDS) and not want_nba

    parts: list[str] = []

    if want_standings and not want_nba:
        for slug in slugs or ["premier-league"]:
            try:
                rows = await _cached(
                    f"standings:{slug}", 300, lambda s=slug: fetch_standings(s)
                )
            except Exception:
                log.exception("Could not load standings for %s", slug)
                rows = []
            if not rows:
                from app.db.models import Competition, Standing, Team

                competition = await db.scalar(
                    select(Competition).where(Competition.slug == slug)
                )
                if competition:
                    result = await db.execute(
                        select(Standing)
                        .where(Standing.competition_id == competition.id)
                        .order_by(Standing.rank)
                    )
                    rows = []
                    for standing in result.scalars().all():
                        team = await db.get(Team, standing.team_id)
                        rows.append({
                            "rank": standing.rank,
                            "team_name": team.name if team else "Unknown",
                            "team_logo": team.logo_url if team else None,
                            "played": standing.played,
                            "won": standing.won,
                            "drawn": standing.drawn,
                            "lost": standing.lost,
                            "points": standing.points,
                        })
            if rows:
                parts.append(_format_standings(slug, rows))

    if want_fixtures:
        targets = slugs or ALL_FOOTBALL_SLUGS
        results = await asyncio.gather(
            *[
                _cached(f"fixtures:{s}", 300, lambda s=s: fetch_fixtures(s))
                for s in targets
            ],
            return_exceptions=True,
        )
        for slug, rows in zip(targets, results):
            if isinstance(rows, Exception) or not rows:
                continue
            picked = _pick_matches(rows)
            if picked:
                parts.append(f"FIXTURES ({slug}): {_compact(picked)}")

    if want_odds and slugs and not want_nba:
        # Odds cost API credits, so only fetch when a league was named, and cache for 15 min.
        for slug in slugs[:2]:
            rows = await _cached(f"odds:{slug}", 900, lambda s=slug: fetch_odds(s))
            if rows:
                parts.append(f"ODDS ({slug}): {_compact(rows[:10], 3000)}")
    elif want_odds and not slugs and not want_nba:
        parts.append(
            "NOTE: odds were not loaded because no league was named. Ask the user which league."
        )

    if want_nba:
        try:
            rows = await _cached("nba:games", 300, lambda: fetch_nba_games())
        except Exception:
            log.exception("Could not load NBA games")
            rows = []
        if rows:
            picked = _pick_matches(rows)
            parts.append(
                f"NBA GAMES (may not include today's games): {_compact(picked)}"
            )

    return "\n".join(parts)


def _clean_history(rows: list[Any], user_message: str) -> list[tuple[str, str]]:
    """Turn DB rows into alternating (role, text) pairs ending with the current user message.

    Gemini needs roles to alternate user/model, starting with user. Old failed replies
    (errors, mock-mode text) are dropped so they do not confuse the model.
    """
    msgs: list[tuple[str, str]] = []
    for m in rows:
        content = (m.content or "").strip()
        if not content:
            continue
        if m.role == "assistant" and (
            content.startswith("Error:")
            or content.startswith("Sorry,")
            or "(mock mode)" in content
        ):
            continue
        msgs.append(("user" if m.role == "user" else "model", content))

    # The current message is already saved in the DB; remove it, then add it once at the end.
    if msgs and msgs[-1] == ("user", user_message.strip()):
        msgs.pop()
    msgs.append(("user", user_message.strip()))

    merged: list[tuple[str, str]] = []
    for role, text in msgs:
        if merged and merged[-1][0] == role:
            merged[-1] = (role, merged[-1][1] + "\n\n" + text)
        else:
            merged.append((role, text))
    while merged and merged[0][0] != "user":
        merged.pop(0)
    return merged


async def _gemini_stream(
    session_id: uuid.UUID,
    user_message: str,
    db: DbSession,
) -> AsyncGenerator[str, None]:
    import os

    from google import genai
    from google.genai import types

    api_key = (
        (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", ""))
        .strip()
        .strip('"')
        .strip("'")
    )
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()

    # Latest 20 messages (newest first from the DB, then put back in order).
    history_result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.role.in_(["user", "assistant"]),
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    history = list(reversed(history_result.scalars().all()))
    pairs = _clean_history(history, user_message)
    contents = [types.Content(role=r, parts=[types.Part(text=t)]) for r, t in pairs]

    # Fetch live data (with a time limit so the chat never hangs on a slow provider).
    live_context = ""
    try:
        live_context = await asyncio.wait_for(
            _build_live_context(user_message, db), timeout=20
        )
    except Exception:
        log.exception("Could not build live context for assistant")

    system_text = SYSTEM_PROMPT + "\n" + LIVE_DATA_RULES
    system_text += (
        f"\nToday's date (UTC): {datetime.now(UTC).strftime('%A %Y-%m-%d %H:%M')}\n"
    )
    if live_context:
        system_text += "\nLIVE DATA:\n" + live_context
    else:
        system_text += "\nLIVE DATA: none loaded for this question."

    full_response = ""
    failed = False
    forbidden = ["sure win", "guaranteed win", "can't lose", "cannot lose", "sure bet"]

    try:
        client = genai.Client(api_key=api_key)
        stream = await client.aio.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_text),
        )
        async for chunk in stream:
            text = chunk.text or ""
            if not text:
                continue
            if any(p in (full_response + text).lower() for p in forbidden):
                text = "\n\n*[Filtered for responsible gambling compliance]*"
                full_response += text
                yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"
                break
            full_response += text
            yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"
    except Exception as e:
        log.exception("Gemini request failed")
        fallback = (
            "The AI provider is temporarily unavailable, but I loaded the latest "
            "platform data for you.\n\n"
            + (live_context if live_context else "No live data was available for this question.")
            + "\n\nPlease try again shortly for a natural-language summary."
        )
        full_response = fallback
        yield f"data: {json.dumps({'type': 'text', 'content': fallback})}\n\n"

    if not failed:
        if not full_response.strip():
            full_response = (
                "Sorry, I could not produce an answer for that. Please try rephrasing."
            )
            yield f"data: {json.dumps({'type': 'text', 'content': full_response})}\n\n"
        # Only successful answers are saved, so errors never pollute the chat history.
        db.add(
            ChatMessage(session_id=session_id, role="assistant", content=full_response)
        )
        await db.flush()
        await db.commit()
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


async def _claude_stream(
    session_id: uuid.UUID,
    user_message: str,
    context: dict,
    db: DbSession,
) -> AsyncGenerator[str, None]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    history_result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.role.in_(["user", "assistant"]),
        )
        .order_by(ChatMessage.created_at)
        .limit(20)
    )
    history = history_result.scalars().all()
    messages = [{"role": m.role, "content": m.content} for m in history]

    full_response = ""
    async with client.messages.stream(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            full_response += text
            yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

    db.add(ChatMessage(session_id=session_id, role="assistant", content=full_response))
    await db.flush()
    await db.commit()
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
