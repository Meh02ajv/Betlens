"""
Prediction computation Celery tasks.
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


@celery_app.task(name="app.workers.tasks.predictions.run_predictions", bind=True)
def run_predictions(self) -> dict:  # type: ignore[no-untyped-def]
    """Compute and store probabilities for all upcoming matches."""
    return _run_async(_run_predictions())


@celery_app.task(name="app.workers.tasks.predictions.run_predictions_for_match", bind=True)
def run_predictions_for_match(self, match_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Compute predictions for a specific match (triggered after lineup confirmation)."""
    return _run_async(_run_predictions_for_match(match_id))


async def _run_predictions() -> dict:
    from app.db.models import JobRun, Match, Prediction
    from app.db.session import AsyncSessionLocal
    from app.ml.models.football import FootballModel
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Match).where(Match.status == "scheduled").limit(100)
        )
        matches = result.scalars().all()

        model = FootballModel()
        count = 0

        for match in matches:
            preds = model.predict_match(str(match.id))
            for pred_data in preds:
                # Upsert prediction
                existing = await session.scalar(
                    select(Prediction).where(
                        Prediction.match_id == match.id,
                        Prediction.market == pred_data["market"],
                        Prediction.selection == pred_data["selection"],
                    )
                )
                if existing:
                    existing.probability = pred_data["probability"]
                    existing.generated_at = datetime.now(UTC)
                else:
                    pred = Prediction(
                        match_id=match.id,
                        market=pred_data["market"],
                        selection=pred_data["selection"],
                        subject_type="match",
                        probability=pred_data["probability"],
                        confidence=pred_data["confidence"],
                        model_version=pred_data["model_version"],
                        factors=pred_data["factors"],
                    )
                    session.add(pred)
                count += 1

        await session.commit()

        jr = JobRun(
            job_name="run_predictions",
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            status="success",
            stats={"predictions_computed": count, "matches_processed": len(matches)},
        )
        session.add(jr)
        await session.commit()

    return {"predictions_computed": count, "matches_processed": len(matches)}


async def _run_predictions_for_match(match_id: str) -> dict:
    from app.ml.models.football import FootballModel
    model = FootballModel()
    preds = model.predict_match(match_id)
    return {"match_id": match_id, "predictions": len(preds)}