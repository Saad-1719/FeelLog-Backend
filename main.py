from fastapi import FastAPI
from app.api.routes import auth_routes, journals_route
from fastapi.middleware.cors import CORSMiddleware
from app.services.db import engine, Base
from contextlib import asynccontextmanager
from mangum import Mangum
from app.core.config import DATABASE_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise
    yield

app = FastAPI(title="FeelLog", version="1.0.0", lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "https://feel-log-frontend.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api")
app.include_router(journals_route.router, prefix="/api")

@app.get("/")
def root():
    print(f"DATABASE URL: {DATABASE_URL}")
    return {"message": "Welcome to FeelLog Backend"}

# # 👇 Wrap FastAPI app for Vercel/Lambda
# handler = Mangum(app)
