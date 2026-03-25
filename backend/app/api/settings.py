from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.settings_service import settings_service
from pydantic import BaseModel

router = APIRouter()

class SettingUpdate(BaseModel):
    key: str
    value: str

@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    all_settings = settings_service.get_all(db)
    # Convert to the list format the frontend expects: [{key: "...", value: "..."}]
    return [{"key": k, "value": str(v)} for k, v in all_settings.items()]

@router.post("/update")
def update_setting(update: SettingUpdate, db: Session = Depends(get_db)):
    settings_service.set(db, update.key, update.value)
    return {"status": "success", "message": f"Setting {update.key} updated"}
