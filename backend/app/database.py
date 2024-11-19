from psycopg import connect
from psycopg.rows import dict_row
from fastapi import HTTPException, status

from config import settings

def get_database_connection():
    try:
        conn = connect(
                host=settings.database_host, 
                port=settings.database_port, 
                dbname=settings.database_name, 
                user=settings.database_user, 
                password=settings.database_password, 
                row_factory=dict_row
            )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not Connected!")
    else:
        print("Database Connected!")
        yield conn
    finally:
        conn.close()