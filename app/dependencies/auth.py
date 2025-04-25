#get current user from token\
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token
from app.schemas.auth import TokenData

oauth2_schema=OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_schema)) -> TokenData:
    try:
        token_data = decode_token(token)
        return token_data
        
    except Exception as e:
        print(f"Exception in get_current_user: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )