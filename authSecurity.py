import jwt
from typing import Union
from datetime import datetime, timedelta
from cookie import OAuth2PasswordBearerWithCookie
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, Request, Response, status, HTTPException
from requests import get_user_only_by_username
from connection import get_db
from dotenv import load_dotenv
from config import ALGORITHM, SECRET_KEY, COOKIE_NAME

load_dotenv()

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="signin")

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user = get_user_only_by_username(db=db, username=payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.username != payload.get("sub"):
        raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access forbidden",
    )
    return user