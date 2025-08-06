from fastapi import APIRouter, Path
from app.schemas.fingerprint import FingerprintCreate, FingerprintOut
from datetime import datetime

router = APIRouter(prefix="/fingerprints", tags=["Fingerprints"])

@router.get("/", response_model=list[FingerprintOut])
def list_fingerprints():
    return [{
        "id": 1, "patient_id": 1, "hand": "left", "finger": "thumb",
        "pattern_type": "loop", "delta": 2, "notes": "Primeira digital",
        "created_at": datetime.now()
    }]

@router.post("/", response_model=FingerprintOut)
def create_fingerprint(fp: FingerprintCreate):
    return {
        "id": 2, "patient_id": fp.patient_id, "hand": fp.hand,
        "finger": fp.finger, "pattern_type": fp.pattern_type,
        "delta": fp.delta, "notes": fp.notes, "created_at": datetime.now()
    }

@router.put("/{fingerprint_id}", response_model=FingerprintOut)
def update_fingerprint(fingerprint_id: int = Path(...), fp: FingerprintCreate = ...):
    return {
        "id": fingerprint_id, "patient_id": fp.patient_id, "hand": fp.hand,
        "finger": fp.finger, "pattern_type": fp.pattern_type,
        "delta": fp.delta, "notes": fp.notes, "created_at": datetime.now()
    }

@router.delete("/{fingerprint_id}")
def delete_fingerprint(fingerprint_id: int = Path(...)):
    return {"message": f"Fingerprint {fingerprint_id} deleted successfully"}
