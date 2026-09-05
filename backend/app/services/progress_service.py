import json
import asyncio
from typing import Optional, AsyncGenerator
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.config import settings


class ProgressService:
    """Redis-backed real-time progress for generation jobs.

    Each job gets a channel: job:{job_id}:progress
    Events are JSON: {"status": "...", "progress": 0-100, "message": "...", "timestamp": "..."}
    """

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._pool: Optional[aioredis.Redis] = None
        self._memory_state: dict = {}

    async def _get_redis(self) -> aioredis.Redis:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if self._pool is None or getattr(self, "_pool_loop", None) != loop:
            self._pool = aioredis.from_url(self.redis_url, decode_responses=True)
            self._pool_loop = loop
        return self._pool

    def _channel(self, job_id: str) -> str:
        return f"job:{job_id}:progress"

    def _state_key(self, job_id: str) -> str:
        return f"job:{job_id}:state"

    async def publish(self, job_id: str, status: str, progress: int, message: str = "") -> None:
        event_dict = {
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._memory_state[job_id] = event_dict
        event = json.dumps(event_dict)
        try:
            r = await self._get_redis()
            await r.publish(self._channel(job_id), event)
            await r.set(self._state_key(job_id), event, ex=3600)
        except Exception:
            pass

    async def subscribe(self, job_id: str) -> AsyncGenerator[dict, None]:
        try:
            r = await self._get_redis()
            pubsub = r.pubsub()
            await pubsub.subscribe(self._channel(job_id))

            cached = await r.get(self._state_key(job_id))
            if cached:
                try:
                    yield json.loads(cached)
                except json.JSONDecodeError:
                    pass

            async for raw in pubsub.listen():
                if raw["type"] == "message":
                    try:
                        data = json.loads(raw["data"])
                        yield data
                        if data.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
                            break
                    except json.JSONDecodeError:
                        continue

            await pubsub.unsubscribe(self._channel(job_id))
            await pubsub.close()
        except Exception:
            # If Redis pub/sub unavailable, yield current memory state
            if job_id in self._memory_state:
                yield self._memory_state[job_id]

    async def get_state(self, job_id: str) -> Optional[dict]:
        try:
            r = await self._get_redis()
            raw = await r.get(self._state_key(job_id))
            if raw:
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        return self._memory_state.get(job_id)

    async def cleanup(self, job_id: str) -> None:
        self._memory_state.pop(job_id, None)
        try:
            r = await self._get_redis()
            await r.delete(self._state_key(job_id))
        except Exception:
            pass


progress_service = ProgressService()
