import json
import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Job, Image
from app.schemas import (
    GenerateRequest, GenerateResponse, JobResponse, JobStatus,
    SSEProgressEvent, ModelInfo, SAMPLERS_LIST, MODELS_LIST,
)
from app.dependencies import require_credits
from app.services.credit_service import deduct_credits
from app.services.progress_service import progress_service
from app.services.ai_service import MODEL_REGISTRY
from app.workers.tasks import generate_image_task

router = APIRouter(prefix="/api/generate", tags=["generate"])

ESTIMATED_TIME_PER_IMAGE = 12


@router.get("/models", response_model=list[ModelInfo])
async def list_models():
    return [
        ModelInfo(
            id=key,
            name=val["name"],
            default_steps=val.get("default_steps", 30),
            default_cfg=val.get("default_cfg", 7.5),
            default_width=val.get("default_width", 1024),
            default_height=val.get("default_height", 1024),
            max_steps=val.get("max_steps", 100),
        )
        for key, val in MODEL_REGISTRY.items()
    ]


@router.get("/samplers")
async def list_samplers():
    return {"samplers": SAMPLERS_LIST}


@router.post("", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def submit_generation(body: GenerateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(require_credits)):
    if body.model not in MODEL_REGISTRY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown model: {body.model}")

    if body.sampler not in SAMPLERS_LIST:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown sampler: {body.sampler}")

    credits_to_deduct = body.num_images
    try:
        tx = await deduct_credits(
            db, str(user.id), credits_to_deduct,
            action="generate",
            description=f"Generated {credits_to_deduct} image(s) with {body.model}",
            model=body.model,
            metadata={"prompt": body.prompt[:200], "width": body.width, "height": body.height},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(e))

    user.credits = tx.balance_after

    params = body.model_dump()
    job = Job(user_id=user.id, prompt=body.prompt, params=params)
    db.add(job)
    await db.flush()

    await progress_service.publish(str(job.id), "PENDING", 0, "Job submitted")
    try:
        generate_image_task.delay(str(job.id))
    except Exception:
        # Fallback to background thread if Celery/Redis is unreachable (e.g. Render single-service tier)
        import threading
        from app.workers.tasks import run_generation_job
        threading.Thread(target=run_generation_job, args=(str(job.id),), daemon=True).start()

    return GenerateResponse(
        job_id=job.id,
        status=JobStatus.PENDING,
        estimated_time=ESTIMATED_TIME_PER_IMAGE * body.num_images,
        credits_deducted=credits_to_deduct,
        credits_remaining=user.credits,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_credits)):
    job = await db.get(Job, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    state = await progress_service.get_state(job_id)

    image_url = None
    if job.image_id:
        img = await db.get(Image, job.image_id)
        if img:
            image_url = img.image_url

    return JobResponse(
        id=job.id,
        status=job.status,
        prompt=job.prompt,
        params=job.params,
        image_id=job.image_id,
        image_url=image_url,
        error_message=job.error_message,
        progress=state.get("progress") if state else None,
        progress_message=state.get("message") if state else None,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/{job_id}/stream")
async def stream_job_progress(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_credits)):
    job = await db.get(Job, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    async def event_generator():
        async for event in progress_service.subscribe(job_id):
            data = json.dumps(event)
            yield f"data: {data}\n\n"
            if event.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
                break

        from app.database import async_session
        async with async_session() as local_db:
            fresh_job = await local_db.get(Job, job_id)
            if fresh_job and fresh_job.status == "COMPLETED" and fresh_job.image_id:
                img = await local_db.get(Image, fresh_job.image_id)
                if img:
                    final = json.dumps({
                        "status": "COMPLETED",
                        "progress": 100,
                        "message": "Done!",
                        "image_id": str(img.id),
                        "image_url": img.image_url,
                    })
                    yield f"data: {final}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_generation(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_credits)):
    job = await db.get(Job, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status in ("PENDING", "PROCESSING"):
        job.status = "FAILED"
        job.error_message = "Cancelled by user"
        await db.flush()
        await progress_service.publish(job_id, "CANCELLED", 0, "Cancelled by user")

    return None
