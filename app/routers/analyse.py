from fastapi import APIRouter, Path
from datetime import datetime
from app.schemas.analyse import AnalyseCreate, AnalyseOut

router = APIRouter(prefix="/analyses", tags=["Analyses"])

@router.get("/", response_model=list[AnalyseOut])
def list_analyses():
    return [{
        "id": 1,
        "patient_id": 1,
        "user_id": 2,
        "sqtl": 40,
        "delta_indice": 3,
        "date": datetime.now(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }]


@router.post("/", response_model=AnalyseOut)
def create_analyse(data: AnalyseCreate):
    return {
        "id": 2,
        "patient_id": data.patient_id,
        "user_id": data.user_id,
        "sqtl": data.sqtl,
        "delta_indice": data.delta_indice,
        "date": datetime.now(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.put("/{analyse_id}", response_model=AnalyseOut)
def update_analyse(analyse_id: int = Path(...), data: AnalyseCreate = ...):
    return {
        "id": analyse_id,
        "patient_id": data.patient_id,
        "user_id": data.user_id,
        "sqtl": data.sqtl,
        "delta_indice": data.delta_indice,
        "date": datetime.now(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.delete("/{analyse_id}")
def delete_analyse(analyse_id: int = Path(...)):
    return {"message": f"Analyse {analyse_id} deleted successfully"}
