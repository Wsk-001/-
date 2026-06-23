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
    bundle_data: dict = {
        "articles": [],
        "urls": [],
        "raw_texts": [],
    }

    spec = body.spec
    if "urls" in spec:
        bundle_data["urls"] = spec["urls"]

    if "keywords" in spec:
        bundle_data["keywords"] = spec["keywords"]

    source_bundle = SourceBundle(
        task_id=body.task_id,
        spec=body.spec,
        bundle=bundle_data,
    )
    db.add(source_bundle)
    await db.flush()
    await db.refresh(source_bundle)
    return source_bundle
