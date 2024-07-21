from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import Connection

from database import get_database_connection
from schemas import User, UserRegistered, UserRegistration
from oauth import get_hashed_password, verify_password, create_access_token

router = APIRouter(
    tags=["auth"]
)

@router.post("/regitser", response_model=UserRegistered)
async def register(user: UserRegistration, conn: Connection = Depends(get_database_connection)):

    if user.password != user.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password not matched!")
    
    with conn.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    *
                FROM 
                    users
                WHERE
                    email = %s;
            """,
            (user.email,)
        )
        
        registered_user = cursor.fetchone()
        if registered_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already Registered!")
        
        cursor.execute(
            """
                SELECT
                    *
                FROM
                    users
                WHERE
                    username = %s;
            """,
            (user.username,)
        )

        registered_user = cursor.fetchone()
        if registered_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already in use. Try another!")
        
        params = user.model_dump()
        params.pop("confirm_password")
        params["password"] = get_hashed_password(params["password"])

        cursor.execute(
            """
                INSERT INTO users (email, username, first_name, last_name, description, is_public, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *;
            """,
            (*params.values(),)
        )
        conn.commit()
        registered_user = cursor.fetchone()
        registered_user.update({
            "access_token": create_access_token(registered_user["email"]),
            "type": "bearer"
        })
        return registered_user
    
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), conn: Connection = Depends(get_database_connection)):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                *
            FROM 
                users
            WHERE
                email = %s;
            """,
            (form_data.username,)
        )
        
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Email or Password")
        
        if not verify_password(form_data.password, user['password']):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Email or Password")
        
        return {
            "access_token": create_access_token(user["email"]),
            "token_type": "bearer"
        }