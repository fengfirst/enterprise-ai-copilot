import os

import redis
from dotenv import load_dotenv

load_dotenv()


class RedisCache:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
    ):
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6380"))

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True,
        )

    def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        self.client.set(key, value, ex=ttl)

    def get(self, key: str) -> str | None:
        return self.client.get(key)

    def delete(self, key: str) -> None:
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))
        