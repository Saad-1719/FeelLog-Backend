from fastapi import APIRouter,Response,Request
from app.schemas import user_schema as user_model
from app.utils.password import verify_password,hash_password
from app.utils.tokens import create_refresh_token,create_access_token,decode_refresh_token
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.auth import UserCreate,UserLogin,Token,UserPublic
from app.services.db import get_session
from app.dependencies.helpers import get_current_userId,get_user_profile
import random
from datetime import timezone,timedelta,datetime
from app.core.config import REFRESH_TOKEN_EXPIRE_MINUTES

router=APIRouter()
profileImg=["https://i.imghippo.com/files/RlV6585mKA.png","https://i.imghippo.com/files/fxla8778FLI.png","https://i.imghippo.com/files/mFFj4453sw.png"]



# Register a new user
@router.post("/auth/register",response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_session), response:Response=None):
    # Check if user already exists
    existing_active_user = db.query(user_model.User).filter(user_model.User.email == user_data.email, user_model.User.is_active== True).first()
    if existing_active_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create a new user with hashed password
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
        access_token=create_access_token(data={"sub":str(new_user.id)})
        refresh_token=create_refresh_token(data={"sub":str(new_user.id)})
        refresh_token_expire=datetime.now(timezone.utc)+timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        new_user.refresh_token=refresh_token
        new_user.refresh_token_expires_at=refresh_token_expire
        db.commit()

        response.set_cookie(key="refresh_token",value=refresh_token,httponly=True,secure=False)
        return Token(
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Login user
@router.post("/auth/login",response_model=Token)
def login(user_login:UserLogin, db:Session=Depends(get_session), response:Response=None):
    print("login triggered")
    # Check if user exists
    user=db.query(user_model.User).filter(user_model.User.email==user_login.email, user_model.User.is_active== True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    try:
        access_token=create_access_token(data={"sub":str(user.id)})
        refresh_token=create_refresh_token(data={"sub":str(user.id)})
        refresh_token_expire=datetime.now(timezone.utc)+timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        user.refresh_token=refresh_token
        user.refresh_token_expires_at=refresh_token_expire
        db.commit()

        response.set_cookie(key="refresh_token",value=refresh_token,httponly=True,secure=False)

        return Token(
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

@router.post("/auth/refresh",response_model=Token)
def refresh_token(request:Request, db: Session = Depends(get_session)):
    # Decode the refresh token
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
        user=db.query(user_model.User).filter(user_model.User.id == user_id, user_model.User.is_active==True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if user.refresh_token != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.refresh_token_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(data={"sub": str(user.id)})
        return Token(
            access_token=access_token,
            token_type="bearer"
        )
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Logout user
@router.post("/auth/logout")
def logout(current_user: UserPublic = Depends(get_current_userId), db: Session = Depends(get_session)):
    # Get user from database using ID
    user = db.query(user_model.User).filter(user_model.User.id == current_user.id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # Clear refresh token
    user.refresh_token = None
    user.refresh_token_expires_at=None
    db.commit()    
    return {"message": "Successfully logged out"}

@router.get("/auth/me",response_model=UserPublic)
def get_profile(current_user:UserPublic=Depends(get_user_profile)):
    return current_user