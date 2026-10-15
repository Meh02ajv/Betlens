from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.deps import CurrentUserId, DbSession
from app.db.models import JobRun, ModelVersion, User

router = APIRouter()


async def require_admin(user_id: CurrentUserId, db: DbSession) -> uuid.UUID:
    user = await db.get(User, user_id)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


AdminUser = Depends(require_admin)


@router.get("/jobs", response_model=list[dict])
async def list_jobs(db: DbSession, _: uuid.UUID = AdminUser) -> list[dict]:
    result = await db.execute(
        select(JobRun).order_by(JobRun.started_at.desc()).limit(100)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "job_name": j.job_name,
            "started_at": j.started_at.isoformat(),
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            "status": j.status,
            "stats": j.stats,
            "error": j.error,
        }
        for j in jobs
    ]


@router.post("/jobs/{job_name}/run", response_model=dict)
async def trigger_job(job_name: str, db: DbSession, _: uuid.UUID = AdminUser) -> dict:
    from app.workers.tasks.ingestion import run_job_by_name
    try:
        run_job_by_name.delay(job_name)
        return {"message": f"Job '{job_name}' queued successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {e}") from e


@router.get("/models", response_model=list[dict])
async def list_models(db: DbSession, _: uuid.UUID = AdminUser) -> list[dict]:
    result = await db.execute(select(ModelVersion).order_by(ModelVersion.trained_at.desc()))
    models = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "sport": m.sport,
            "trained_at": m.trained_at.isoformat(),
            "metrics": m.metrics,
            "is_active": m.is_active,
        }
        for m in models
    ]


@router.get("/users", response_model=list[dict])
async def list_users(
    db: DbSession,
    _: uuid.UUID = AdminUser,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "plan": u.plan,
            "email_verified_at": u.email_verified_at.isoformat() if u.email_verified_at else None,
            "created_at": u.created_at.isoformat(),
            "deleted_at": u.deleted_at.isoformat() if u.deleted_at else None,
        }
        for u in users
    ]