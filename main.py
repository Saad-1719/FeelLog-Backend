from fastapi import FastAPI,Request
from app.api.routes import auth_routes, journals_route
from fastapi.middleware.cors import CORSMiddleware
from app.services.db import engine, Base
from contextlib import asynccontextmanager
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter=Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise
    yield

app = FastAPI(title="FeelLog", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter #type: ignore
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

origins = [
    "http://localhost:5173",
    "https://www.feellog.site",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET PUT POST DELETE"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api")
app.include_router(journals_route.router, prefix="/api")

@app.get("/")
@limiter.limit("30/minute")
def root(request: Request = None):
    return {"message": "Welcome to FeelLog Backend"}
