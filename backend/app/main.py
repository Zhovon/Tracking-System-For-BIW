from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from app.config import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["1000/minute"])

app = FastAPI(
    title="Ticketing System API",
    description="Internal communication & collaboration system",
    version="1.0.0"
)

# Register slowapi exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# DOS Protection: 50MB Payload Size Limit Middleware
class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int):
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: StarletteRequest, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_upload_size:
            return JSONResponse(status_code=413, content={"detail": "Payload too large. Maximum size is 50MB."})
        return await call_next(request)

# Add Middlewares (executed bottom to top in Starlette)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(PayloadSizeLimitMiddleware, max_upload_size=50 * 1024 * 1024) # 50 MB limit
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1 import tickets, users, rooms, notifications

app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(rooms.router, prefix="/api/v1/rooms", tags=["rooms"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])

@app.get("/")
def root():
    return {"message": "Welcome to the Ticketing System API"}

@app.get("/health")
def health_check(request: Request):
    return {"status": "ok"}
