import hashlib
import os

# from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext

from app.services.models import User

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)
SECRET_KEY = os.getenv('SECRET_KEY')  # Use env var in prod
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*1

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Pre-hash with SHA-256 (same as in get_password_hash)
    prehashed = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(prehashed, hashed_password)

def get_password_hash(password: str) -> str:
    # Pre-hash with SHA-256 to handle any length password
    prehashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(prehashed)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user