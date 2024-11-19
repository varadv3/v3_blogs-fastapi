from pydantic import BaseModel, EmailStr

class User(BaseModel):
    email: EmailStr
    username: str

class UserProfile(User):
    first_name: str
    last_name: str = None
    description: str | None = None
    is_public: bool = False

class UserRegistration(UserProfile):
    password: str
    confirm_password: str

class UserRegistered(User):
    access_token: str
    type: str

class Post(BaseModel):
    title: str
    content: str

class Token(BaseModel):
    access_token: str = None
    token_type: str = None
