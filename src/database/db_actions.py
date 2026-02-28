"""
Database Actions Layer - Coordinates between Redis cache and MySQL database.

This module provides business logic for usage tracking that coordinates
between Redis (fast cache) and MySQL (source of truth).
"""

from sqlalchemy.orm import Session
from src.database.config import SessionLocal
from src.database.db_functions import (
    get_usage as db_get_usage,
    add_usage as db_add_usage,
    update_usage as db_update_usage
)
from src.services.redis import (
    get_usage as redis_get_usage,
    set_usage as redis_set_usage
)


def get_usage(user_id: str, day: str) -> int:
    
    try:
        redis_usage = redis_get_usage(user_id, day)
        if redis_usage is not None and redis_usage > 0:
            return redis_usage
    except Exception as e:
        print(f"⚠️ Redis error in get_usage: {e}. Falling back to database.")
    
    db = SessionLocal()
    try:
        db_usage = db_get_usage(db, user_id, day)
        
        try:
            redis_set_usage(user_id, day, db_usage)
        except Exception as e:
            print(f"⚠️ Failed to cache usage in Redis: {e}")
        
        return db_usage
    finally:
        db.close()


def add_usage(user_id: str, day: str, current_usage: int) -> dict:
    
    db = SessionLocal()
    try:
        existing_usage = db_get_usage(db, user_id, day)
        
        # Determine whether to update or add
        if existing_usage > 0:
            # Record exists - update it
            result = db_update_usage(db, user_id, day, current_usage)
        else:
            # Record doesn't exist - add new one
            result = db_add_usage(db, user_id, day, current_usage)
        
        # Update Redis cache if database operation was successful
        if result.get("success", False):
            try:
                redis_set_usage(user_id, day, current_usage)
            except Exception as e:
                # Redis update failed, but DB update succeeded
                print(f"⚠️ Failed to update Redis cache: {e}")
        
        return result
    finally:
        db.close()


# Synchronous wrapper functions for compatibility with existing code
# These can be used with run_in_threadpool in FastAPI routes

def sync_get_usage(user_id: str, day: str) -> int:
    
    return get_usage(user_id, day)


def sync_add_usage(user_id: str, day: str, current_usage: int) -> dict:
    
    return add_usage(user_id, day, current_usage)
