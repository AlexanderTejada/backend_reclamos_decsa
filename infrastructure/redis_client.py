#infraestructure/redis_client.py
import redis
from infrastructure.settings import Config

class RedisClient:
    def __init__(self):
        self.client = redis.StrictRedis(
            host=Config.REDIS_HOST or "localhost",
            port=Config.REDIS_PORT or 6379,
            db=0,
            decode_responses=True
        )

    def get_client(self):
        return self.client