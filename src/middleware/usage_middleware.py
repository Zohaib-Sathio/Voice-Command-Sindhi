

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import os

from src.utils.day_helper import get_current_day
from src.database.db_actions import sync_get_usage, sync_add_usage
from src.utils.logger import log


class UsageCheckMiddleware(BaseHTTPMiddleware):
    
    
    # Public endpoints that don't require usage tracking
    PUBLIC_ENDPOINTS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/v1/api/auth/generate-token",
        "/v1/api/auth/validate-token",
        "/static",
    ]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Get daily limit from environment variable, default to 100
        self.default_daily_limit = int(os.getenv("DEFAULT_DAILY_LIMIT", "100"))
    
    async def dispatch(self, request: Request, call_next):
        # Check if endpoint requires usage tracking
        path = request.url.path
        
        # Skip usage checking for public endpoints
        if any(path.startswith(public_path) for public_path in self.PUBLIC_ENDPOINTS):
            return await call_next(request)
        
        # Get user_id from request.state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            # If no user_id, skip usage checking (shouldn't happen if auth middleware is before this)
            log("⚠️ Usage middleware: No user_id found in request.state, skipping usage check")
            return await call_next(request)
        
        # Get current day
        day = get_current_day()
        
        # Get current usage
        try:
            current_usage = sync_get_usage(user_id, day)
        except Exception as e:
            log(f"❌ Error getting usage for user {user_id}: {e}")
            # On error, allow request to proceed (fail open)
            current_usage = 0
        
        # Get user's daily limit (for now, use default limit)
        # TODO: Can be extended to get per-user limit from database
        daily_limit = self.default_daily_limit
        
        # Check if usage limit exceeded
        if current_usage >= daily_limit:
            log(f"🚫 Rate limit exceeded for user {user_id}: {current_usage}/{daily_limit}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Daily API limit reached. Please try again tomorrow.",
                    "limit": daily_limit,
                    "current_usage": current_usage
                }
            )
        
        # Attach usage info to request.state for potential use in endpoint
        request.state.current_usage = current_usage
        request.state.daily_limit = daily_limit
        request.state.day = day
        
        # Proceed to endpoint
        response = await call_next(request)
        
        # After endpoint execution, increment usage if request was successful
        # Only increment on successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            try:
                new_usage = current_usage + 1
                result = sync_add_usage(user_id, day, new_usage)
                if result.get("success"):
                    log(f"✅ Usage incremented for user {user_id}: {new_usage}/{daily_limit}")
                else:
                    log(f"⚠️ Failed to increment usage for user {user_id}: {result.get('message', 'Unknown error')}")
            except Exception as e:
                log(f"❌ Error incrementing usage for user {user_id}: {e}")
                # Don't fail the request if usage tracking fails
        
        return response

