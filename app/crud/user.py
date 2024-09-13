from app.models.user import User
from app.db.database import client
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(user: User):
    user.password = pwd_context.hash(user.password)
    result = await client.my_database.users.insert_one(user.dict(by_alias=True))
    return result.inserted_id

async def get_user(user_id: str):
    user = await client.my_database.users.find_one({"_id": user_id})
    return User(**user) if user else None

async def get_user_by_username(username: str):
    user = await client.my_database.users.find_one({"username": username})
    return User(**user) if user else None

async def get_user_by_email(email: str):
    user = await client.my_database.users.find_one({"email": email})
    return User(**user) if user else None

async def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)