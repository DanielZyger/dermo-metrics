from fastapi import APIRouter, Path, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from app.schemas.fingerprint import FingerprintCreate, FingerprintOut
from datetime import datetime
from app.models.volunteer import Volunteer
from app.models.fingerprint import Fingerprint
from app.constants.enum import FingerEnum, HandEnum, PatternEnum
from app.db import get_db
from app.utils.process_images import process
from app.utils.to_base_64 import to_base64

router = APIRouter(prefix="/fingerprints", tags=["Fingerprints"])

@router.get("/", response_model=list[FingerprintOut])
def list_fingerprints(db: Session = Depends(get_db)):
    
    try:
        fingerprints = db.query(Fingerprint).order_by(Fingerprint.created_at.desc()).all()
        mapped_fingerprints = [
            {
                "id": fp.id,
                "volunteer_id": fp.volunteer_id,
                "hand": fp.hand,
                "finger": fp.finger,
                "pattern_type": fp.pattern_type,
                "delta": fp.delta,
                "notes": fp.notes,
                "image_data": to_base64(fp.image_data),
                "image_filtered": to_base64(fp.image_filtered),
                "created_at": fp.created_at,
            }
            for fp in fingerprints
        ]
        
        return mapped_fingerprints
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )

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
    image_filtered = process(image_bytes)

    new_fp = Fingerprint(
        volunteer_id=volunteer_id,
        hand=hand,
        finger=finger,
        pattern_type=pattern_type,
        delta=delta,
        notes=notes,
        image_data=image_bytes,
        image_filtered=image_filtered,
        created_at=datetime.now()
    )
    db.add(new_fp)
    db.commit()
    db.refresh(new_fp)

    return FingerprintOut(
        id=new_fp.id,
        volunteer_id=new_fp.volunteer_id,
        hand=new_fp.hand,
        finger=new_fp.finger,
        pattern_type=new_fp.pattern_type,
        delta=new_fp.delta,
        notes=new_fp.notes,
        image_data=to_base64(new_fp.image_data),
        image_filtered=to_base64(new_fp.image_filtered),
        created_at=new_fp.created_at
    )


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
