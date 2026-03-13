import redis.asyncio as redis

from app.domain.models import ICacheRepository


class RedisRepository(ICacheRepository):
    def __init__(self, client: redis.Redis):
        self._client = client

    # String / Integer
    async def set_string(self, key: str, value: str, ttl: int | None = None):
        await self._client.set(key, value, ex=ttl)

    async def get_string(self, key: str):
        return await self._client.get(key)

    async def increment(self, key: str, amount: int = 1):
        return await self._client.incr(key, amount=amount)

    # List
    async def list_push(self, key: str, value: str):
        await self._client.rpush(key, value)  # type: ignore

    async def list_get_all(self, key: str):
        return await self._client.lrange(key, 0, -1)  # type: ignore

    async def list_update(self, key: str, index: int, value: str):
        await self._client.lset(key, index, value)  # type: ignore

    async def list_remove_value(self, key: str, value: str, count: int = 0):
        await self._client.lrem(key, count, value)  # type: ignore

    # Hash
    async def hash_set_all(self, key: str, mapping: dict):
        await self._client.hset(key, mapping=mapping)  # type: ignore

    async def hash_get_all(self, key: str):
        return await self._client.hgetall(key)  # type: ignore

    async def hash_delete_field(self, key: str, field: str):
        await self._client.hdel(key, field)  # type: ignore

    # Common
    async def delete(self, key: str):
        await self._client.delete(key)

    async def set_ttl(self, key: str, seconds: int):
        await self._client.expire(key, seconds)
