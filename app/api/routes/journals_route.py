from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.models.auth import UserPublic
from app.services.db import get_session
from app.dependencies.helpers import get_current_userId

router=APIRouter()

@router.post("/add-journal")
def add_journal( db:Session=Depends(get_session),user:UserPublic=Depends(get_current_userId)):

    return user

