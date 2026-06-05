from fastapi import HTTPException, Request
from app.core.cache import cache


class RateLimiter:
    def __init__(
        self,
        max_requests: int = 3,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request):
        if cache._redis is None:
            return

        # Kullanıcı ID varsa onu kullan
        user_id = request.headers.get("X-User-Id")

        # Yoksa IP bazlı çalış
        if not user_id:
            user_id = request.client.host

        redis_key = f"rate_limit:{user_id}"

        current = await cache._redis.incr(redis_key)

        if current == 1:
            await cache._redis.expire(
                redis_key,
                self.window_seconds
            )

        if current > self.max_requests:
            ttl = await cache._redis.ttl(redis_key)

            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Çok fazla istek gönderdiniz.",
                    "retry_after": ttl
                }
            )