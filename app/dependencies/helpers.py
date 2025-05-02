from app.models.auth import UserId
from app.services.db import get_session
from app.utils.tokens import decode_access_token
from sqlalchemy.orm import Session
from fastapi import FastAPI,HTTPException,Depends,status
from fastapi.security import OAuth2PasswordBearer
from app.schemas import user_schema
from app.models.auth import UserPublic

oauth2_schema=OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_profile(token: str = Depends(oauth2_schema), db: Session = Depends(get_session)) -> UserPublic:
    try:
        token_data = decode_access_token(token)
        if token_data.type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token type",
                                headers={"WWW-Authenticate": "Bearer"})
        user = db.query(user_schema.User).filter(user_schema.User.id == token_data.user_id,
                                                 user_schema.User.is_active == True).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return UserPublic.model_validate(user)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_userId(token:str = Depends(oauth2_schema),db:Session=Depends(get_session))->UserId:
    try:
        token_data=decode_access_token(token)
        if token_data.type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Token Type",
                                headers={"WWW-Authenticate":"Bearer"})
        user=db.query(user_schema.User).filter(user_schema.User.id == token_data.user_id,user_schema.User.is_active==True).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User not Found",headers={"WWW-Authenticate":"Bearer"})
        
        return UserId.model_validate(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    