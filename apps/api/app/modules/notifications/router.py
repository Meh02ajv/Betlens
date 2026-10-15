from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import CurrentUserId, DbSession
from app.db.models import Notification, NotificationSetting

router = APIRouter()


@router.get("", response_model=list[dict])
async def get_notifications(
    user_id: CurrentUserId,
    db: DbSession,
    unread_only: bool = False,
) -> list[dict]:
    q = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(50)
    if unread_only:
        q = q.where(Notification.read_at.is_(None))
    result = await db.execute(q)
    notifs = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "type": n.type,
            "payload": n.payload,
            "channel": n.channel,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifs
    ]


@router.patch("/{notification_id}/read", response_model=dict)
async def mark_read(
    notification_id: uuid.UUID,
    user_id: CurrentUserId,
    db: DbSession,
) -> dict:
    from datetime import UTC, datetime
    notif = await db.get(Notification, notification_id)
    if not notif or notif.user_id != user_id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read_at = datetime.now(UTC)
    await db.flush()
    return {"id": str(notif.id), "read_at": notif.read_at.isoformat()}


@router.get("/settings", response_model=dict)
async def get_notification_settings(user_id: CurrentUserId, db: DbSession) -> dict:
    ns = await db.scalar(select(NotificationSetting).where(NotificationSetting.user_id == user_id))
    if not ns:
        return {"in_app": True, "email": True, "push": False, "quiet_hours_start": None, "quiet_hours_end": None}
    return {
        "in_app": ns.in_app,
        "email": ns.email,
        "push": ns.push,
        "quiet_hours_start": ns.quiet_hours_start,
        "quiet_hours_end": ns.quiet_hours_end,
    }


@router.put("/settings", response_model=dict)
async def update_notification_settings(
    data: dict,
    user_id: CurrentUserId,
    db: DbSession,
) -> dict:
    ns = await db.scalar(select(NotificationSetting).where(NotificationSetting.user_id == user_id))
    if not ns:
        ns = NotificationSetting(user_id=user_id)
        db.add(ns)

    for field in ["in_app", "email", "push", "quiet_hours_start", "quiet_hours_end"]:
        if field in data:
            setattr(ns, field, data[field])

    await db.flush()
    return {"message": "Notification settings updated"}


@router.post("/push/subscribe", response_model=dict)
async def subscribe_push(data: dict, user_id: CurrentUserId, db: DbSession) -> dict:
    # In production, store the push subscription endpoint and keys
    return {"message": "Push subscription registered"}