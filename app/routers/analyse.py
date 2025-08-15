from fastapi import APIRouter, Path
from datetime import datetime
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("/", response_model=list[ReviewOut])
def list_reviews():
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


@router.post("/", response_model=ReviewOut)
def create_review(data: ReviewCreate):
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


@router.put("/{review_id}", response_model=ReviewOut)
def update_review(review_id: int = Path(...), data: ReviewCreate = ...):
    return {
        "id": review_id,
        "patient_id": data.patient_id,
        "user_id": data.user_id,
        "sqtl": data.sqtl,
        "delta_indice": data.delta_indice,
        "date": datetime.now(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.delete("/{review_id}")
def delete_review(review_id: int = Path(...)):
    return {"message": f"Review {review_id} deleted successfully"}
