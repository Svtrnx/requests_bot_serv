from requests import get_user_by_username
from sqlalchemy.orm import Session

def authenticate_user(db: Session, username: str, user_key: str, hwid: str):
    user = get_user_by_username(db=db, username=username, user_key=user_key, hwid=hwid)
    if not user:
        return False
    return user