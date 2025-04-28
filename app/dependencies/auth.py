from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.utils.tokens import decode_access_token
from app.models.auth import UserPublic
from app.schemas import user_schema
from app.services.db import get_session

oauth2_schema=OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_schema),db:Session=Depends(get_session)) -> user_schema.User:
    try:
        token_data = decode_access_token(token)
        if token_data.type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Token type",
                                headers={"WWW-Authenticate": "Bearer"})
        user=db.query(user_schema.User).filter(user_schema.User.id == token_data.user_id, user_schema.User.is_active==True).first()
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