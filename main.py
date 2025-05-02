from fastapi import FastAPI
from app.api.routes import auth_routes,journals_route
from fastapi.middleware.cors import CORSMiddleware
from app.services.db import engine,Base
import app.schemas
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise
    yield

app = FastAPI(title="FeelLog", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_routes.router,prefix="/api")
app.include_router(journals_route.router,prefix="/api")

@app.get("/")
def root():
    return{"message":"Welcome to FeelLog Backend"}