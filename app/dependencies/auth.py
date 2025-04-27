from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from app.schemas.auth import UserPublic
from app.models import user as user_model
from app.dependencies.database import get_session

oauth2_schema=OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_schema),db:Session=Depends(get_session)) -> user_model.User:
    try:
        token_data = decode_access_token(token)
        if token_data.type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Token type",
                                headers={"WWW-Authenticate": "Bearer"})
        user=db.query(user_model.User).filter(user_model.User.id == token_data.user_id, user_model.User.is_active==True).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        print(user)
        return UserPublic.model_validate(user)
        
    except Exception as e:
        print(f"Exception in get_current_user: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )