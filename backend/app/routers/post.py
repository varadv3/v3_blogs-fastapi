from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from database import get_database_connection
from schemas import Post, User
from oauth import get_current_user

router = APIRouter(
    tags=['Post'],
    prefix="/posts"
)

@router.get("/home")
async def home(conn: Connection = Depends(get_database_connection), user: User = Depends(get_current_user)):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                *
            FROM 
                posts
            WHERE
                (user_email LIKE %s OR ARRAY[user_email] <@ following(%s)) AND (NOT is_archieved)
            ORDER BY
                posted_on DESC;
            """,
            (user.email, user.email,)
        )

        posts = cursor.fetchall()
    return posts

@router.get("/explore")
async def explore(conn: Connection = Depends(get_database_connection)):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                p.*
            FROM 
                posts p 
                INNER JOIN users u ON p.user_email = u.email AND u.is_public = True
            ORDER BY
                posted_on DESC;
            """
        )
        posts = cursor.fetchall()
    return posts

@router.post("/create")
async def create_post(post: Post, conn: Connection = Depends(get_database_connection), user: User = Depends(get_current_user)):
    with conn.cursor() as cursor:
        cursor.execute(
        """
            INSERT INTO posts (title, content, user_email)
            VALUES (%s, %s, %s)
            RETURNING *;
        """,
        (*post.model_dump().values(), user.email,)
        )
        post = cursor.fetchone()
        print(post)
    conn.commit()
    return post

@router.put("/change_status/{id}/{status}")
async def change_status(id: int, status: bool, conn: Connection = Depends(get_database_connection), user: User = Depends(get_current_user)):
    with conn.cursor() as cursor:
        if status:
            cursor.execute(
                """
                UPDATE 
                    posts
                SET
                    is_archieved = True
                WHERE
                    id = %s
                RETURNING *;
                """,
                (str(id),)
            )
        else:
            cursor.execute(
                """
                UPDATE 
                    posts
                SET
                    is_archieved = False
                WHERE
                    id = %s
                RETURNING *;
                """,
                (str(id),)
            )
        post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with this id = {id} not found!")
    conn.commit()
    return post

@router.put("/vote/{post_id}/{dir}")
async def vote(post_id: int, dir: bool, conn: Connection = Depends(get_database_connection), user: User = Depends(get_current_user)):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                *
            FROM
                posts
            WHERE
                id = %s;
            """,
            (str(post_id),)
        )
        post = cursor.fetchone()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} not found!")
    
    if dir: #upvote
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO votes (post_id, user_email)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING 
                RETURNING *;
                """,
                (str(post_id), user.email,)
            )
            vote = cursor.fetchone()

        if not vote:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User {user.email} has already voted this post!")
        conn.commit()
        return {"message": "success"}
    else:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM 
                    votes
                WHERE
                    post_id = %s AND user_email = %s
                RETURNING *;
                """,
                (str(post_id), user.email)
            )
            post = cursor.fetchone()
        
        if not post:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User {user.email} has not voted this post!")
        
        conn.commit()
        return {"message": "success"}
    
@router.delete("/{post_id}")
async def delete(post_id: int, conn: Connection = Depends(get_database_connection), user: User = Depends(get_current_user)):

    with conn.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM
                posts
            WHERE
                id = %s
            RETURNING*;
            """,
            (str(post_id),)
        )

        post = cursor.fetchone()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {post_id} not found!")
    
    if post['user_email'] != user.email:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Post with id: {post_id} doesn't belongs to you!")
    
    conn.commit()
    return {"messgae": "success"}