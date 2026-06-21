import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

# Configure structlog for JSON logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger(__name__)

from app.config import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["1000/minute"])

app = FastAPI(
    title="Ticketing System API",
    description="Internal communication & collaboration system",
    version="1.0.0",
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
            return JSONResponse(
                status_code=413, content={"detail": "Payload too large. Maximum size is 50MB."}
            )
        return await call_next(request)


# Add Middlewares (executed bottom to top in Starlette)
@app.middleware("http")
async def structlog_middleware(request: Request, call_next):
    if request.url.path in ["/health", "/"]:
        return await call_next(request)
    logger.info("request_started", method=request.method, path=request.url.path)
    response = await call_next(request)
    logger.info(
        "request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    return response


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(PayloadSizeLimitMiddleware, max_upload_size=50 * 1024 * 1024)  # 50 MB limit
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=getattr(settings, "ALLOWED_ORIGIN_REGEX", None),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.domains.notifications.router import router as notifications_router
from app.domains.rooms.router import router as rooms_router
from app.domains.tickets.router import router as tickets_router
from app.domains.users.router import router as users_router

app.include_router(tickets_router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(rooms_router, prefix="/api/v1/rooms", tags=["rooms"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])


@app.get("/")
def root():
    return {"message": "Welcome to the Ticketing System API"}


@app.get("/health")
def health_check(request: Request):
    return {"status": "ok"}
