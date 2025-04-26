from fastapi import APIRouter
from app.models import user as user_model
from app.services.db import engine
from app.core.security import verify_password,hash_password,create_refresh_token,create_access_token,decode_refresh_token
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import UserCreate,UserLogin,Token,TokenData,UserPublic
from app.dependencies.database import get_session
from app.dependencies.auth import get_current_user
import random
router=APIRouter()
profileImg=["https://i.imghippo.com/files/RlV6585mKA.png","https://i.imghippo.com/files/fxla8778FLI.png","https://i.imghippo.com/files/mFFj4453sw.png"]

user_model.Base.metadata.create_all(bind=engine)

    
@router.post("/auth/register",response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_session)):
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
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token=create_access_token(data={"sub":new_user.email})
    refresh_token=create_refresh_token(data={"sub":new_user.email})
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/auth/login",response_model=Token)
def login(user_login:UserLogin, db:Session=Depends(get_session)):
    user=db.query(user_model.User).filter(user_model.User.email==user_login.email, user_model.User.is_active== True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token=create_access_token(data={"sub":user.email})
    refresh_token=create_refresh_token(data={"sub":user.email})
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
    
@router.post("/auth/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_session)):
    # Verify the refresh token
    try:
        user_email = decode_refresh_token(refresh_token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(user_model.User).filter(user_model.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    # Return the new access token and refresh token
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )

@router.get("/auth/me",response_model=UserPublic)
def get_profile(current_user:UserPublic=Depends(get_current_user)):
    return current_user