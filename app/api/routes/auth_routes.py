from fastapi import APIRouter, Response, Request, Depends, HTTPException, status
from app.schemas import user_schema as user_model
from app.utils.password_utils import verify_password, hash_password
from app.utils.tokens_utils import (
    create_refresh_token,
    create_access_token,
    decode_refresh_token,
)
from sqlalchemy.orm import Session
from app.models.auth import UserCreate, UserLogin, Token, UserProfile, UserId,EmailRequest,ResetPassword
from app.services.db import get_session
from app.dependencies.auth import get_current_userId, get_user_profile
from fastapi.responses import JSONResponse
from datetime import timezone, timedelta, datetime
from app.schemas.token_schema import RefreshToken
import random
from app.core.config import REFRESH_TOKEN_EXPIRE_MINUTES
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.utils.email_utils import send_otp_email

# Use the custom key function from main.py
def custom_key_func(request: Request):
    if request.method == "OPTIONS":
        return None
    return get_remote_address(request)

limiter = Limiter(key_func=custom_key_func)
router = APIRouter()
profileImg = [
    "https://res.cloudinary.com/dpb5t5j0u/image/upload/v1747079669/botttsNeutral-1746256710350_puiqlo.png",
    "https://res.cloudinary.com/dpb5t5j0u/image/upload/v1747079669/botttsNeutral-1746256774171_1_ofa2ob.png",
    "https://res.cloudinary.com/dpb5t5j0u/image/upload/v1747079669/botttsNeutral-1746256688992_pvraef.jpg",
    "https://res.cloudinary.com/dpb5t5j0u/image/upload/v1747079668/botttsNeutral-1746256505220_lygmxv.jpg",
    "https://res.cloudinary.com/dpb5t5j0u/image/upload/v1747079668/botttsNeutral-1746256670007_tjmezj.jpg",
    "https://res.cloudinary.com/dpb5t5j0u/image/upload/v1747079668/botttsNeutral-1746256659205_jndnqj.jpg",
    "https://res.cloudinary.com/dpb5t5j0u/image/upload/v1747079668/botttsNeutral-1746256592697_b0zlkl.jpg",
]


# Register a new user
@router.post("/auth/register", response_model=Token)
@limiter.limit("5/minute")
def register(
    user_data: UserCreate, db: Session = Depends(get_session), response: Response = None,request:Request=None
):
    existing_active_user = (
        db.query(user_model.User)
        .filter(
            user_model.User.email == user_data.email, user_model.User.is_active == True
        )
        .first()
    )
    if existing_active_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    hashed_password = hash_password(user_data.password)
    new_user = user_model.User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        profile_photo=random.choice(profileImg),
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        access_token = create_access_token(data={"sub": str(new_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
        refresh_token_expire = datetime.now(timezone.utc) + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )
        MAX_SESSIONS = 5
        refresh_tokens = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == new_user.id)
            .order_by(RefreshToken.expires_at.asc())
            .all()
        )
        if len(refresh_tokens) >= MAX_SESSIONS:
            oldest_token = refresh_tokens[0]
            db.delete(oldest_token)
            db.commit()

        # Store refresh token in RefreshToken table
        new_refresh_token = RefreshToken(
            user_id=new_user.id,
            refresh_token=refresh_token,
            expires_at=refresh_token_expire,
        )
        db.add(new_refresh_token)
        db.commit()

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            path="/",
        )
        return Token(
            access_token=access_token, token_type="bearer"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Login user
@router.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    user_login: UserLogin, db: Session = Depends(get_session), response: Response = None,request: Request = None
):
    user = (
        db.query(user_model.User)
        .filter(
            user_model.User.email == user_login.email, user_model.User.is_active == True
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    try:
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        refresh_token_expire = datetime.now(timezone.utc) + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )
        MAX_SESSIONS = 5
        refresh_tokens = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .order_by(RefreshToken.expires_at.asc())
            .all()
        )
        if len(refresh_tokens) >= MAX_SESSIONS:
            oldest_token = refresh_tokens[0]
            db.delete(oldest_token)
            db.commit()

        # Store refresh token in RefreshToken table
        new_refresh_token = RefreshToken(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=refresh_token_expire,
        )
        db.add(new_refresh_token)
        db.commit()

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            path="/",
        )
        return Token(
            access_token=access_token, token_type="bearer"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Refresh token
@router.post("/auth/refresh", response_model=Token)
@limiter.limit("10/minute")
def refresh_token(request: Request, db: Session = Depends(get_session)):

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_refresh_token(refresh_token)
        user_id = payload.user_id
        refresh_token_entry = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.refresh_token == refresh_token,
                RefreshToken.user_id == user_id,
            )
            .first()
        )
        if not refresh_token_entry:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if refresh_token_entry.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
            timezone.utc
        ):
            # db.delete(refresh_token_entry)
            # db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = (
            db.query(user_model.User)
            .filter(user_model.User.id == user_id, user_model.User.is_active == True)
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        access_token = create_access_token(data={"sub": str(user.id)})
        return Token(
            access_token=access_token, token_type="bearer"
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Logout user
@router.post("/auth/logout")
@limiter.limit("5/minute")
def logout(
    current_user: UserId = Depends(get_current_userId),
    db: Session = Depends(get_session),
    request: Request = None,
    response:Response=None
):
    try:
        refresh_token = request.cookies.get("refresh_token")
        refresh_token_entry = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.refresh_token==refresh_token,
                RefreshToken.user_id == current_user.id,
            )
            .first()
        )

        if not refresh_token_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        response = JSONResponse(content={"message": "Successfully logged out"})
        response.delete_cookie(
            key="refresh_token",
            path="/",
            httponly=True,
            samesite="None",
            secure=True,
        )
        return response
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error During Logout"
        )


@router.post("/forget_password")
@limiter.limit("10/hour")
async def forget_password(body:EmailRequest, db: Session = Depends(get_session),request: Request=None,response:Response=None):

    user=db.query(user_model.User).filter(user_model.User.email==body.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    otp=f"{random.randint(100000,999999)}"
    user.otp_codes=otp
    user.opt_expires=datetime.now(timezone.utc)+timedelta(minutes=15)
    db.commit()
    await send_otp_email(body.email,otp)
    return {"msg":"OTP send to your email"}

@router.post("/reset_password")
def reset_password(request:ResetPassword, db: Session = Depends(get_session), requestObj: Request=None,response:Response=None):
    user=db.query(user_model.User).filter(user_model.User.email==request.email).first()
    if not user or user.otp_codes != request.otp or user.opt_expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP Code",
        )
    user.hashed_password = hash_password(request.password)
    user.otp_codes = None
    user.opt_expires = None
    db.commit()
    return {"msg":"Password Reset Successful"}

@router.get("/auth/me", response_model=UserProfile)
@limiter.limit("8/minute")
def get_profile(current_user: UserProfile = Depends(get_user_profile),request: Request = None,response:Response=None):
    return current_user
