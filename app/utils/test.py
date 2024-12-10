import asyncio
import base64
from datetime import datetime, timedelta
import json
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException
from cryptography.fernet import Fernet
from passlib.context import CryptContext

# MongoDB connection settings
MONGO_URL = "mongodb+srv://admin:trustkmp123@cluster0.celqdib.mongodb.net/"
DATABASE_NAME = "grail"
SECRET_KEY = "grail"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]

def encrypt_data(data: dict, key: bytes):
    fernet = Fernet(key)
    data_str = json.dumps(data)
    encrypted_data = fernet.encrypt(data_str.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()

async def connect_to_mongo():
    global client
    client = AsyncIOMotorClient(MONGO_URL)

async def close_mongo_connection():
    global client
    if client:
        client.close()

# Generate a license key
def generate_license_key(user_info: dict, duration: timedelta):
    key = SECRET_KEY.encode()  # Use the secret key from settings
    if len(key) != 32:
        print("Invalid secret key length.")
        print("Creating new one...")
        key = Fernet.generate_key()
    expire_date = (datetime.utcnow() + duration).isoformat()
    data = {
        "user_info": user_info,
        "expire_date": expire_date
    }
    return encrypt_data(data, key)

class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: str
    password: str
    avatar_url: Optional[str] = None

    @validator('id', pre=True, always=True)
    def convert_objectid_to_str(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

class License(BaseModel):
    user_id: str
    license_key: str
    expire_date: str
    device_number: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    avatar_url: Optional[str] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
async def get_user(user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    
    # Convert ObjectId to string for Pydantic model
    return User(**user) if user else None
    
    return None

async def create_user(user: UserCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    
    # Hash the password before saving it to the database
    # user.password = pwd_context.hash(user.password)
    user.password = "123456"
    
    # Insert the user into the database and return the inserted ID
    result = await db["users"].insert_one(user.dict(by_alias=True))
    
    return await get_user(result.inserted_id)

async def create_license(license: License):
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    
    # Insert the license into the database and return the inserted ID
    result = await db["licenses"].insert_one(license.dict())
    
    return result.inserted_id

# Test function to validate MongoDB connection and license creation
async def test_license_creation():
    await connect_to_mongo()
    
    # Create a mock user for testing first
    mock_user = UserCreate(
        username="micwonder2",
        email="tech.guru.k.p2@gmail.com",
        password="123456"
    )
    
    # Create the user in MongoDB and get the user ID
    user = await create_user(mock_user)
    if not user:
        print("User registration error")
        return
    
    # Generate a license key for the newly created user
    duration = timedelta(days=365)  # Example duration of 30 days
    license_key = generate_license_key(mock_user.dict(), duration)
    
    # Create a License object with the new user's ID


    license_data = License(
        user_id=user.id,
        license_key=license_key,
        expire_date=(datetime.utcnow() + duration).isoformat(),
        device_number=None
    )
    
    # Insert the license into MongoDB and get the inserted ID
    print(license_data)
    inserted_id = await create_license(license_data)
    
    print(f"License created with ID: {inserted_id}")

# Run the test function if this script is executed directly
if __name__ == "__main__":
    asyncio.run(test_license_creation())