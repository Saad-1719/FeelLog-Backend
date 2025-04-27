from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException,status
from dotenv import load_dotenv
import os
import jwt
from app.schemas.auth import TokenData
from uuid import UUID

#load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(eval(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")))

# Check if the environment variables are set
if not SECRET_KEY or not ALGORITHM:
    raise ValueError("SECRET_KEY and ALGORITHM must be set in the environment variables.")

# JWT token creation 
def create_access_token(data:dict,expire_delta:Optional[timedelta] = None) -> str:
    to_encode=data.copy()
    if expire_delta:
        expire=datetime.now(timezone.utc)+ expire_delta
    else:
        expire=datetime.now(timezone.utc)+ timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire,"type":"access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# JWT token refresh
def create_refresh_token(data:dict, expire_delta:Optional[timedelta]=None)->str:
    to_encode=data.copy()
    if expire_delta:
        expire=datetime.now(timezone.utc)+expire_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire,"type":"refresh"})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

#decode Jwt token
def decode_access_token(token:str)->TokenData:
    try:
        payload= jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        user_id:str=payload.get("sub")
        token_type:str=payload.get("type")
        if user_id is None or token_type is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Token",
                headers={"WWW-Authenticate":"Bearer"}
            )
        return TokenData(user_id=user_id,type=token_type)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate":"Bearer"}
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate":"Bearer"}
        )

def decode_refresh_token(token:str)->TokenData:
    try:
        payload= jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        user_id:str=payload.get("sub")
        token_type:str=payload.get("type")
        if user_id is None or token_type is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Token",
                headers={"WWW-Authenticate":"Bearer"}
            )
        return TokenData(user_id=user_id,type=token_type)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate":"Bearer"}
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate":"Bearer"}
        )

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
