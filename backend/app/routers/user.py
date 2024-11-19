from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection
from pydantic import EmailStr

from schemas import User, UserProfile
from oauth import get_current_user
from database import get_database_connection

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.get("/profile/{user_email}", response_model=UserProfile)
async def get_profile(user_email: str, user: User = Depends(get_current_user), conn: Connection = Depends(get_database_connection)):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                *
            FROM 
                users
            WHERE
                email LIKE %s
            """,
            (user_email,)
        )

        user_profile = cursor.fetchone()

    if not user_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email: {user_email} not found!")
    return user_profile

@router.put("/change_about", response_model=User)
async def change_about(desc: str = None, conn: Connection = Depends(get_database_connection), user: User = Depends(get_current_user)):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE
                users
            SET 
                description = %s
            WHERE
                email = %s
            RETURNING
                *
            """,
            (desc, user.email,)
        )
        updated_user = cursor.fetchone()

    if not updated_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=["Something went wrong"])
    conn.commit()
    return {"message": "successful"}

@router.put("/follow/{followee_email}")
async def follow(followee_email: EmailStr, conn: Connection = Depends(get_database_connection), user: User = Depends(get_current_user)):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO 
                followers
            VALUES
                (%s, %s)
            ON CONFLICT DO NOTHING
            RETURNING *;
            """,
            (user.email, followee_email,)
        )

        result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"You already follows user {followee_email}")
    
    conn.commit()
    return {"message": "successful"}