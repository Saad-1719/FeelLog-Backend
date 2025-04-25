from app.services.db import SessionLocal


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()