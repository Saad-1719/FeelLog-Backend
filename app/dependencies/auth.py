#get current user from token\
from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token
from app.schemas.auth import TokenData
from app.models import user as user_model
from app.dependencies.database import get_session

oauth2_schema=OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_schema),db:Session=Depends(get_session)) -> user_model.User:
    try:
        token_data = decode_token(token)
        if not token_data.email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Token")
        user=db.query(user_model.User).filter(user_model.User.email == token_data.email, user_model.User.is_active==True).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
        return user
        
    except Exception as e:
        print(f"Exception in get_current_user: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )