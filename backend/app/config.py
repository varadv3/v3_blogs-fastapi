from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str
    secret_key: str
    algorithm: str
    access_token_expiration_time: int

    class Config:
        env_file = "/home/varadv3/Documents/Master/Python/fastapi/backend/.env"

settings = Settings()