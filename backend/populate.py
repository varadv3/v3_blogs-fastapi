from psycopg import Connection, connect
from psycopg.rows import dict_row
from app.oauth import get_hashed_password

def populate_tables(conn: Connection):
    print(type(conn))
    for i in range(10):
        email = f"user{i + 1}@mail.com"
        username = f"user{i + 1}"
        password = get_hashed_password("12345678")
        first_name = f"User{i + 1}"
        last_name = f"Mouse{i + 1}"
        is_public = False
        
        with conn.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO users (email, username, first_name, last_name, password, is_public)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (email, username, first_name, last_name, password, str(is_public),)
            )

        print(f"{username} created!")

        for j in range(5):
            title = f"post {i + 1} {j + 1}"
            content = f"content {i + 1} {j + 1}"
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO posts (title, content, user_email)
                    VALUES (%s, %s, %s)
                    """,
                    (title, content, email)
                )
            print(f"{title} created!")

def populate_relations(conn: Connection):
    for i in range(7):
        follower = f"user{i + 1}@mail.com"
        for j in range(3):
            followee = f"user{i + 1 + j + 1}@mail.com"
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO followers
                    VALUES (%s, %s)
                    """,
                    (follower, followee,)
                )
            print(follower, followee)

if __name__ == "__main__":
    try:
        conn = connect(
                host='localhost', 
                port='5432', 
                dbname='fastapidb', 
                user='postgres', 
                password='postgres', 
                row_factory=dict_row
            )
        print("Database Connected!")
    except Exception as e:
        conn.rollback()
        print(e)
    else:
        populate_tables(conn)
        populate_relations(conn)
    finally:
        conn.commit()
        conn.close()