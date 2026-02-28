from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

from src.routes.api_endpoints import router
from src.routes.api_endpoints import limiter

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# from src.middleware.auth_middleware import AuthenticationMiddleware
# from src.middleware.usage_middleware import UsageCheckMiddleware

load_dotenv(override=True)

app = FastAPI(title="Bank Voice Commands API", version="1.1.0")

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="public"), name="static")

# Middleware order matters! They execute in reverse order (last added = first executed)
# Order: CORS -> Auth -> Usage -> SlowAPI
app.add_middleware(SlowAPIMiddleware)
# app.add_middleware(UsageCheckMiddleware)  # Checks usage limits (runs after auth)
# app.add_middleware(AuthenticationMiddleware)  # Validates JWT tokens (runs first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('src.app:app', host="0.0.0.0", port=8000,reload=True)

