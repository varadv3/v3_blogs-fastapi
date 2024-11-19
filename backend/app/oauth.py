import jwt
from jwt import PyJWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from pydantic import EmailStr
from psycopg import Connection

from schemas import User
from database import get_database_connection
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRATION_TIME = settings.access_token_expiration_time

oauth_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    scheme_name="JWT"
)

def get_hashed_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(email: EmailStr) -> str:
    
    expires_delta = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME)
    payload = {
        "email": email,
        "exp": expires_delta
    }

    return jwt.encode(payload, SECRET_KEY, ALGORITHM)

def get_current_user(token: str = Depends(oauth_scheme), conn: Connection = Depends(get_database_connection)):
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
    except PyJWTError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials!")
    else:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    email, username
                FROM 
                    users
                WHERE
                    email = %s
                """,
                (payload["email"],)
            )

            user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with these credentials not found!")
        
        return User(**user)