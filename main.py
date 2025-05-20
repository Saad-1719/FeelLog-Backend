from http.client import HTTPException

from fastapi import FastAPI,Request,HTTPException
from app.api.routes import auth_routes, journals_route
from fastapi.middleware.cors import CORSMiddleware
from app.services.db import engine, Base
from contextlib import asynccontextmanager
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Create a custom rate limiter that exempts OPTIONS requests
def custom_key_func(request: Request):
    # Skip rate limiting for OPTIONS requests
    if request.method == "OPTIONS":
        return None
    # Regular rate limiting for all other methods
    return get_remote_address(request)

limiter = Limiter(key_func=custom_key_func)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        raise HTTPException(
            detail=str(e)
        )
    yield

app = FastAPI(title="FeelLog", version="1.0.0", lifespan=lifespan)
#
app.state.limiter = limiter #type: ignore
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

origins = [
    "http://localhost:5173",
    "https://www.feellog.site",
"https://feel-log-backend.vercel.app",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET PUT POST DELETE"],
    allow_headers=["X-Session-ID"],
)

app.include_router(auth_routes.router, prefix="/api")
app.include_router(journals_route.router, prefix="/api")

@app.get("/")
@limiter.limit("30/minute")
def root(request: Request = None):
    return {"message": "Welcome to FeelLog Backend"}
