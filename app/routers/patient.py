from fastapi import APIRouter, Path
from app.schemas.patient import PatientCreate, PatientOut
from datetime import datetime

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/", response_model=list[PatientOut])
def list_patients():
    return [{
        "id": 1, "name": "Maria Souza", "age": 30, "gender": "female",
        "phone": "11999999999", "description": "Paciente exemplo",
        "created_at": datetime.now()
    }]

@router.post("/", response_model=PatientOut)
def create_patient(patient: PatientCreate):
    return {
        "id": 2, "name": patient.name, "age": patient.age, "gender": patient.gender,
        "phone": patient.phone, "description": patient.description,
        "created_at": datetime.now()
    }

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
