from fastapi import APIRouter, Path, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from app.schemas.fingerprint import FingerprintCreate, FingerprintOut
from datetime import datetime
from app.models.volunteer import Volunteer
from app.models.fingerprint import Fingerprint
from app.constants.enum import FingerEnum, HandEnum, PatternEnum
from app.db import get_db


router = APIRouter(prefix="/fingerprints", tags=["Fingerprints"])

@router.get("/", response_model=list[FingerprintOut])
def list_fingerprints():
    return [{
        "id": 1, "volunteer_id": 1, "hand": "left", "finger": "thumb",
        "pattern_type": "loop", "delta": 2, "notes": "Primeira digital",
        "created_at": datetime.now()
    }]

from fastapi import Form, File, UploadFile

@router.post("/", response_model=FingerprintOut)
async def create_fingerprint(
    volunteer_id: int = Form(...),
    hand: HandEnum = Form(...),
    finger: FingerEnum = Form(...),
    pattern_type: PatternEnum = Form(None),
    delta: int = Form(None),
    notes: str = Form(None),
    image_data: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    image_bytes = await image_data.read()

    new_fp = Fingerprint(
        volunteer_id=volunteer_id,
        hand=hand,
        finger=finger,
        pattern_type=pattern_type,
        delta=delta,
        notes=notes,
        image_data=image_bytes,
        created_at=datetime.now()
    )
    db.add(new_fp)
    db.commit()
    db.refresh(new_fp)
    return new_fp


@router.put("/{fingerprint_id}", response_model=FingerprintOut)
def update_fingerprint(fingerprint_id: int = Path(...), fp: FingerprintCreate = ...):
    return {
        "id": fingerprint_id, "volunteer_id": fp.volunteer_id, "hand": fp.hand,
        "finger": fp.finger, "pattern_type": fp.pattern_type,
        "delta": fp.delta, "notes": fp.notes, "created_at": datetime.now()
    }

@router.delete("/{fingerprint_id}")
def delete_fingerprint(fingerprint_id: int = Path(...)):
    return {"message": f"Fingerprint {fingerprint_id} deleted successfully"}
