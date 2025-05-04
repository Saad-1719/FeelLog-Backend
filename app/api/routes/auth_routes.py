from fastapi import APIRouter, Response, Request, Depends, HTTPException, status
from app.schemas import user_schema as user_model
from app.utils.password import verify_password, hash_password
from app.utils.tokens import create_refresh_token, create_access_token, decode_refresh_token
from sqlalchemy.orm import Session
from app.models.auth import UserCreate, UserLogin, Token, UserPublic
from app.services.db import get_session
from app.dependencies.helpers import get_current_userId, get_user_profile
from fastapi.responses import JSONResponse
from uuid import uuid4
from datetime import timezone, timedelta, datetime
from app.schemas.token_schema import RefreshToken
import random
from app.core.config import REFRESH_TOKEN_EXPIRE_MINUTES

router = APIRouter()
profileImg = [
    "https://i.imghippo.com/files/RlV6585mKA.png",
    "https://i.imghippo.com/files/fxla8778FLI.png",
    "https://i.imghippo.com/files/mFFj4453sw.png"
]

# Register a new user
@router.post("/auth/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_session), response: Response = None):
    existing_active_user = db.query(user_model.User).filter(
        user_model.User.email == user_data.email, user_model.User.is_active == True
    ).first()
    if existing_active_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = hash_password(user_data.password)
    new_user = user_model.User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        profile_photo=random.choice(profileImg)
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        session_id = str(uuid4())
        access_token = create_access_token(data={"sub": str(new_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
        refresh_token_expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        MAX_SESSIONS = 5
        refresh_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == existing_active_user.id).order_by(RefreshToken.expires_at.asc()).all()
        if len(refresh_tokens) >= MAX_SESSIONS:
            oldest_token = refresh_tokens[0]
            db.delete(oldest_token)
            db.commit()

        # Store refresh token in RefreshToken table
        new_refresh_token = RefreshToken(
            user_id=new_user.id,
            session_id=session_id,
            refresh_token=refresh_token,
            expires_at=refresh_token_expire
        )
        db.add(new_refresh_token)
        db.commit()

        response.set_cookie(
            key=f"refresh_token_{session_id}",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            path="/"
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Login user
@router.post("/auth/login", response_model=Token)
def login(user_login: UserLogin, db: Session = Depends(get_session), response: Response = None):
    user = db.query(user_model.User).filter(
        user_model.User.email == user_login.email, user_model.User.is_active == True
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    try:
        session_id = str(uuid4())
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        refresh_token_expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        MAX_SESSIONS = 5
        refresh_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id).order_by(RefreshToken.expires_at.asc()).all()
        if len(refresh_tokens) >= MAX_SESSIONS:
            oldest_token = refresh_tokens[0]
            db.delete(oldest_token)
            db.commit()

        # Store refresh token in RefreshToken table
        new_refresh_token = RefreshToken(
            user_id=user.id,
            session_id=session_id,
            refresh_token=refresh_token,
            expires_at=refresh_token_expire
        )
        db.add(new_refresh_token)
        db.commit()

        response.set_cookie(
            key=f"refresh_token_{session_id}",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            path="/"
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Refresh token
@router.post("/auth/refresh", response_model=Token)
def refresh_token(request: Request, db: Session = Depends(get_session)):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session ID not provided")

    refresh_token = request.cookies.get(f"refresh_token_{session_id}")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_refresh_token(refresh_token)
        user_id = payload.user_id
        refresh_token_entry = db.query(RefreshToken).filter(
            RefreshToken.session_id == session_id,
            RefreshToken.refresh_token == refresh_token,
            RefreshToken.user_id == user_id
        ).first()
        if not refresh_token_entry:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if refresh_token_entry.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(user_model.User).filter(
            user_model.User.id == user_id, user_model.User.is_active == True
        ).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        access_token = create_access_token(data={"sub": str(user.id)})
        return Token(
            access_token=access_token,
            token_type="bearer",
            session_id=session_id
        )
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Logout user
@router.post("/auth/logout")
def logout(current_user: UserPublic = Depends(get_current_userId), db: Session = Depends(get_session), request: Request = None):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session ID not provided")

    refresh_token_entry = db.query(RefreshToken).filter(
        RefreshToken.session_id == session_id,
        RefreshToken.user_id == current_user.id
    ).first()
    if not refresh_token_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    db.delete(refresh_token_entry)
    db.commit()

    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(
        key=f"refresh_token_{session_id}",
        path="/",
        httponly=True,
        samesite="None",
        secure=True
    )
    return response

# Get profile (unchanged)
@router.get("/auth/me", response_model=UserPublic)
def get_profile(current_user: UserPublic = Depends(get_user_profile)):
    return current_user