import asyncio
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.workers.celery_app import celery_app
from app.config import settings
from app.models import Job, Image
from app.services.ai_service import get_ai_provider, MODEL_REGISTRY
from app.services.storage_service import storage_service
from app.services.progress_service import progress_service

sync_url = settings.DATABASE_URL_SYNC or settings.DATABASE_URL
if sync_url.startswith("postgres://"):
    sync_url = sync_url.replace("postgres://", "postgresql://", 1)
elif "+asyncpg" in sync_url:
    sync_url = sync_url.replace("+asyncpg", "")

sync_engine = create_engine(sync_url)
SyncSession = sessionmaker(bind=sync_engine)

def _run_async(coro):
    import asyncio
    return asyncio.run(coro)


def _publish_sync(job_id: str, status: str, progress: int, message: str = ""):
    _run_async(progress_service.publish(job_id, status, progress, message))


def _upload_sync(data: bytes, key: str) -> str:
    return _run_async(storage_service.upload(data, key))


def run_generation_job(job_id: str):
    """Full AI generation pipeline:
       1. Load job from DB
       2. Report progress
       3. Call AI provider
       4. Upload result to storage
       5. Create Image record
       6. Update job status
    """
    db = SyncSession()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found", "job_id": job_id}

        job.status = "PROCESSING"
        db.commit()

        params = job.params or {}
        params["prompt"] = job.prompt
        model_key = params.get("model", "hf-flux")

        _publish_sync(job_id, "PROCESSING", 5, "Initializing AI provider...")

        provider = get_ai_provider(model_key)
        total_images = params.get("num_images", 1)
        created_image_ids = []

        for img_idx in range(total_images):
            img_params = params.copy()
            img_params["num_images"] = 1
            if total_images > 1:
                _publish_sync(job_id, "PROCESSING", 5, f"Generating image {img_idx + 1}/{total_images}...")

            async def on_progress(message: str, progress: int):
                base = (img_idx / total_images) * 80
                scaled = base + (progress / 100) * (80 / total_images)
                await progress_service.publish(job_id, "PROCESSING", int(min(88, scaled)), message)

            try:
                result = _run_async(provider.generate(img_params, on_progress=on_progress))
            except Exception as e:
                from app.services.ai_service import HuggingFaceProvider, PlaceholderProvider
                from app.config import settings
                hf_key = settings.HUGGINGFACE_API_KEY or settings.HF_TOKEN
                result = None
                if hf_key and provider.name != "huggingface":
                    try:
                        _publish_sync(
                            job_id,
                            "PROCESSING",
                            15,
                            "Primary provider unavailable, switching to FLUX.1 Schnell...",
                        )
                        hf_fallback = HuggingFaceProvider()
                        result = _run_async(hf_fallback.generate(img_params, on_progress=on_progress))
                    except Exception:
                        result = None

                if not result:
                    _publish_sync(
                        job_id,
                        "PROCESSING",
                        10,
                        f"Generation error ({str(e)[:50]}). Using fallback provider...",
                    )
                    fallback_provider = PlaceholderProvider()
                    result = _run_async(fallback_provider.generate(img_params, on_progress=on_progress))

            _publish_sync(job_id, "PROCESSING", 89, "Uploading to storage...")

            ext = "png"
            key = storage_service.generate_key(str(job.user_id), ext)
            image_url = _upload_sync(result.image_bytes, key)

            _publish_sync(job_id, "PROCESSING", 93, "Saving to database...")

            seed_to_store = result.seed_used if img_idx == 0 else result.seed_used + img_idx

            image = Image(
                user_id=job.user_id,
                prompt=job.prompt,
                negative_prompt=params.get("negative_prompt"),
                image_url=image_url,
                width=result.width,
                height=result.height,
                steps=params.get("steps", 30),
                cfg_scale=params.get("cfg_scale", 7.5),
                sampler=params.get("sampler", "DPM++ 2M Karras"),
                seed=seed_to_store,
                model=model_key,
                is_public=params.get("is_public", False),
            )
            db.add(image)
            db.flush()
            created_image_ids.append(str(image.id))

        job.image_id = created_image_ids[0] if created_image_ids else None
        job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        _publish_sync(job_id, "COMPLETED", 100, "Done!")
        progress_service._pool = None

        return {
            "job_id": job_id,
            "image_ids": created_image_ids,
            "status": "COMPLETED",
        }

    except Exception as e:
        db.rollback()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.error_message = str(e)[:1000]
            db.commit()
        _publish_sync(job_id, "FAILED", 0, str(e)[:200])
        progress_service._pool = None
        return {"job_id": job_id, "status": "FAILED", "error": str(e)}

    finally:
        db.close()


@celery_app.task(bind=True, name="generate_image", max_retries=2, default_retry_delay=5)
def generate_image_task(self, job_id: str):
    return run_generation_job(job_id)
