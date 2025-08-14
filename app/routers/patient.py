from fastapi import APIRouter, Path, Depends
from sqlalchemy.orm import Session
from app.schemas.patient import PatientCreate, PatientOut
from datetime import datetime
from app.models.fingerprint import Fingerprint
from app.models.patient import Patient
from app.db import get_db

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/", response_model=list[PatientOut])
def list_patients():
    return [{
        "id": 1, "name": "Maria Souza", "age": 30, "gender": "female",
        "phone": "11999999999", "description": "Paciente exemplo",
        "created_at": datetime.now()
    }]

@router.post("/", response_model=PatientOut)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    new_patient = Patient(
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        phone=patient.phone,
        description=patient.description,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int = Path(...), patient: PatientCreate = ...):
    return {
        "id": patient_id, "name": patient.name, "age": patient.age,
        "gender": patient.gender, "phone": patient.phone,
        "description": patient.description, "created_at": datetime.now()
    }

@router.delete("/{patient_id}")
def delete_patient(patient_id: int = Path(...)):
    return {"message": f"Patient {patient_id} deleted successfully"}
