from datetime import datetime
from app.models.license import License
from app.db.database import db
from fastapi import HTTPException

async def create_license(license: License):
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    result = await db["licenses"].insert_one(license.dict())
    return result.inserted_id

async def get_available_licenses(user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    
    current_time = datetime.utcnow()
    licenses = await db["licenses"].find({
        "user_id": user_id,
        "expire_date": {"$gt": current_time.isoformat()}
    }).to_list(length=None)

    return licenses