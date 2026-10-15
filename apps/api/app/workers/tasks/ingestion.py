"""
Data ingestion Celery tasks.
All external API calls happen here — never in the web request path.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.workers.celery_app import celery_app


def _run_async(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.ingestion.sync_reference_data", bind=True)
def sync_reference_data(self) -> dict:  # type: ignore[no-untyped-def]
    """Sync competitions, teams, squads, venues, referees."""
    return _run_async(_sync_reference_data())


@celery_app.task(name="app.workers.tasks.ingestion.sync_fixtures", bind=True)
def sync_fixtures(self) -> dict:  # type: ignore[no-untyped-def]
    """Sync upcoming fixtures and schedule changes."""
    return _run_async(_sync_fixtures())


@celery_app.task(name="app.workers.tasks.ingestion.sync_standings_and_stats", bind=True)
def sync_standings_and_stats(self) -> dict:  # type: ignore[no-untyped-def]
    """Sync standings, player and team stats."""
    return _run_async(_sync_standings())


@celery_app.task(name="app.workers.tasks.ingestion.sync_injuries", bind=True)
def sync_injuries(self) -> dict:  # type: ignore[no-untyped-def]
    """Sync injury and suspension reports."""
    return _run_async(_sync_injuries())


@celery_app.task(name="app.workers.tasks.ingestion.sync_odds", bind=True)
def sync_odds(self) -> dict:  # type: ignore[no-untyped-def]
    """Sync bookmaker odds."""
    return _run_async(_sync_odds())


@celery_app.task(name="app.workers.tasks.ingestion.run_job_by_name", bind=True)
def run_job_by_name(self, job_name: str) -> dict:  # type: ignore[no-untyped-def]
    """Manually trigger a named job (from admin panel)."""
    job_map = {
        "sync_reference_data": _sync_reference_data,
        "sync_fixtures": _sync_fixtures,
        "sync_standings_and_stats": _sync_standings,
        "sync_injuries": _sync_injuries,
        "sync_odds": _sync_odds,
    }
    if job_name not in job_map:
        return {"error": f"Unknown job: {job_name}"}
    return _run_async(job_map[job_name]())


# ── Async implementations ─────────────────────────────────────────────────────

async def _record_job_run(job_name: str, status: str, stats: dict, error: str | None = None) -> None:
    from app.db.models import JobRun
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        jr = JobRun(
            job_name=job_name,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            status=status,
            stats=stats,
            error=error,
        )
        session.add(jr)
        await session.commit()


async def _sync_reference_data() -> dict:
    # In production: call football/NBA provider APIs
    # For now: mock implementation
    stats = {"competitions": 9, "teams": 0, "players": 0}
    await _record_job_run("sync_reference_data", "success", stats)
    return stats


async def _sync_fixtures() -> dict:
    stats = {"fixtures_updated": 0}
    await _record_job_run("sync_fixtures", "success", stats)
    return stats


async def _sync_standings() -> dict:
    stats = {"standings_updated": 0}
    await _record_job_run("sync_standings_and_stats", "success", stats)
    return stats


async def _sync_injuries() -> dict:
    stats = {"injuries_updated": 0}
    await _record_job_run("sync_injuries", "success", stats)
    return stats


async def _sync_odds() -> dict:
    stats = {"odds_updated": 0}
    await _record_job_run("sync_odds", "success", stats)
    return stats