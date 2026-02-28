from redis import Redis
import os
from dotenv import load_dotenv


load_dotenv(override=True)

def get_redis_client():
    return Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=int(os.getenv("REDIS_DB")))


def set_usage(user_id: str, day: str, count: int):
    # get redis client  
    redis_client = get_redis_client()
    redis_client.set(f"usage:{user_id}:{day}", count)
    redis_client.expire(f"usage:{user_id}:{day}", 90000)
    return True


def get_usage(user_id: str, day: str) -> int | None:
    # get redis client
    redis_client = get_redis_client()
    return int(redis_client.get(f"usage:{user_id}:{day}") or 0)
