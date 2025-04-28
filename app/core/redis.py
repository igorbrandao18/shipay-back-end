from typing import Optional
import redis
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool
from app.core.config import settings
from app.core.metrics import metrics

class RedisManager:
    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None

    @classmethod
    async def get_client(cls) -> Redis:
        if cls._client is None:
            await cls.initialize()
        return cls._client

    @classmethod
    async def initialize(cls):
        if cls._pool is None:
            cls._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_TIMEOUT,
                decode_responses=True
            )
            cls._client = Redis(connection_pool=cls._pool)
            metrics.set_db_connections(1)  # Track Redis connection

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.close()
            cls._client = None
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None
            metrics.set_db_connections(0)  # Update connection count

    @classmethod
    async def health_check(cls) -> bool:
        try:
            client = await cls.get_client()
            await client.ping()
            return True
        except redis.RedisError:
            return False

# Dependency for FastAPI
async def get_redis():
    client = await RedisManager.get_client()
    try:
        yield client
    finally:
        # Don't close the client here as it's managed by RedisManager
        pass 