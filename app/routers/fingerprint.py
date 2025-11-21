from fastapi import APIRouter, Path, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from app.schemas.fingerprint import FingerprintOut
from datetime import datetime
from app.models.volunteer import Volunteer
from app.models.fingerprint import Fingerprint
from app.constants.enum import FingerEnum, HandEnum, PatternEnum
from app.db import get_db
from app.utils.process_images import process
from app.utils.to_base_64 import to_base64
import base64
import json

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
                "ridge_counts": fp.ridge_counts,
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
    
@router.get("/{fingerprint_id}", response_model=FingerprintOut)
def get_volunteer(
    fingerprint_id: int = Path(..., description="ID da digital"),
    db: Session = Depends(get_db),
):
    fingerprint = (
        db.query(Fingerprint)
        .filter(Fingerprint.id == fingerprint_id)
        .first()
    )
    
    if not fingerprint:
        raise HTTPException(
            status_code=404, 
            detail=f"Fingerprint com ID {fingerprint_id} não encontrado"
        )
    
    return fingerprint

@router.post("/", response_model=FingerprintOut)
async def create_fingerprint(
    volunteer_id: int = Form(...),
    hand: HandEnum = Form(...),
    finger: FingerEnum = Form(...),
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
        deltas=new_fp.deltas,
        core=new_fp.core,
        number_deltas=new_fp.number_deltas,
        notes=new_fp.notes,
        ridge_counts=new_fp.ridge_counts,
        image_data=to_base64(new_fp.image_data),
        image_filtered=to_base64(new_fp.image_filtered)
    )

@router.put("/{fingerprint_id}", response_model=FingerprintOut)
async def update_fingerprint(
    fingerprint_id: int = Path(...),
    volunteer_id: int = Form(...),
    hand: HandEnum = Form(...),
    finger: FingerEnum = Form(...),
    pattern_type: PatternEnum | None = Form(None),
    number_deltas: int | None = Form(None),
    notes: str | None = Form(None),
    ridge_counts: int | None = Form(None),
    core: str | None = Form(None),
    deltas: str | None = Form(None),
    db: Session = Depends(get_db),
):
    existing_fingerprint = (
        db.query(Fingerprint)
        .filter(Fingerprint.id == fingerprint_id)
        .first()
    )
    if not existing_fingerprint:
        raise HTTPException(
            status_code=404,
            detail=f"Fingerprint com ID {fingerprint_id} não encontrado",
        )

    if core is not None:
        core_data = json.loads(core)
        existing_fingerprint.core = {
            "x": int(core_data["x"]),
            "y": int(core_data["y"]),
        }
    if deltas is not None:
        deltas_data = json.loads(deltas)
        existing_fingerprint.deltas = [
            {"x": int(p["x"]), "y": int(p["y"])} for p in deltas_data
        ]

    existing_fingerprint.volunteer_id = volunteer_id
    existing_fingerprint.hand = hand
    existing_fingerprint.finger = finger
    existing_fingerprint.pattern_type = pattern_type
    existing_fingerprint.number_deltas = number_deltas
    existing_fingerprint.notes = notes
    existing_fingerprint.ridge_counts = ridge_counts
    existing_fingerprint.updated_at = datetime.now()

    db.commit()
    db.refresh(existing_fingerprint)

    return FingerprintOut(
        id=existing_fingerprint.id,
        volunteer_id=existing_fingerprint.volunteer_id,
        hand=existing_fingerprint.hand,
        finger=existing_fingerprint.finger,
        pattern_type=existing_fingerprint.pattern_type,
        number_deltas=existing_fingerprint.number_deltas,
        notes=existing_fingerprint.notes,
        ridge_counts=existing_fingerprint.ridge_counts,
        core = existing_fingerprint.core,
        deltas = existing_fingerprint.deltas,
    )

@router.delete("/{fingerprint_id}")
def delete_fingerprint(fingerprint_id: int = Path(...)):
    return {"message": f"Fingerprint {fingerprint_id} deleted successfully"}
