
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.jwt import validate_jwt_token


class AuthenticationMiddleware(BaseHTTPMiddleware):
   
    
    # Public endpoints that don't require authentication
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
    
    async def dispatch(self, request: Request, call_next):
        # Check if endpoint is public
        path = request.url.path
        
        # Skip authentication for public endpoints
        if any(path.startswith(public_path) for public_path in self.PUBLIC_ENDPOINTS):
            return await call_next(request)
        
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Missing Authorization header"
                }
            )
        
        if not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Invalid Authorization header format. Expected 'Bearer <token>'"
                }
            )
        
        token = authorization.split(" ")[1] if len(authorization.split(" ")) > 1 else ""
        if not token:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Token not found in Authorization header"
                }
            )
        
        # Validate token
        try:
            user_id = validate_jwt_token(token)
            # Attach user_id to request.state for use in downstream middleware/endpoints
            request.state.user_id = user_id
        except HTTPException as e:
            # Token validation failed (expired, invalid, etc.)
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": e.detail
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": f"Error validating token: {str(e)}"
                }
            )
        
        # Continue to next middleware/endpoint
        return await call_next(request)

