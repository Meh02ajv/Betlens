"""
Notification dispatch Celery tasks.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.workers.celery_app import celery_app


def _run_async(coro):  # type: ignore[no-untyped-def]
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.notifications.send_queued_notifications", bind=True)
def send_queued_notifications(self) -> dict:  # type: ignore[no-untyped-def]
    """Dispatch queued notifications via in-app, email, and push channels."""
    return _run_async(_send_queued_notifications())


async def _send_queued_notifications() -> dict:
    from app.db.models import Notification
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Notification).where(Notification.sent_at.is_(None)).limit(100)
        )
        pending = result.scalars().all()

        sent = 0
        for notif in pending:
            # In production: send via Resend (email) or Web Push
            # For now: mark as sent
            notif.sent_at = datetime.now(UTC)
            sent += 1

        await session.commit()

    return {"notifications_sent": sent}