from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.source_bundle import SourceBundle
from schemas.source import SourceCollectRequest, SourceBundleResponse

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.post("/collect", response_model=SourceBundleResponse, status_code=201)
async def collect_sources(body: SourceCollectRequest, db: AsyncSession = Depends(get_db)):
    # FIX: Actually invoke the collect logic instead of just storing
    # the spec verbatim. Previously URLs were never fetched and text
    # sources were silently discarded.
    from steps.collect_sources import CollectSourcesStep
    from core.pipeline_engine import StepContext

    executor = CollectSourcesStep()
    ctx = StepContext(
        task_id=body.task_id or uuid.uuid4(),
        inputs={},
        config={"sources": body.spec.get("sources", [])},
        artifacts={},
    )
    result = await executor.execute(ctx)

    bundle_data = result.artifacts.get("source_bundle", {"sources": body.spec.get("sources", [])})

    source_bundle = SourceBundle(
        task_id=body.task_id,
        spec=body.spec,
        bundle=bundle_data,
    )
    db.add(source_bundle)
    await db.flush()
    await db.refresh(source_bundle)
    return source_bundle
