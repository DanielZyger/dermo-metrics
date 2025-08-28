from fastapi import APIRouter, Path, Depends
from sqlalchemy.orm import Session
from app.schemas.volunteer import VolunteerCreate, VolunteerOut
from datetime import datetime
from app.models.volunteer import Volunteer
from app.db import get_db

router = APIRouter(prefix="/volunteers", tags=["Volunteer"])

@router.get("/", response_model=list[VolunteerOut])
def list_volunteers(db: Session = Depends(get_db)):
    volunteers = db.query(Volunteer).all()
    return volunteers

@router.post("/", response_model=VolunteerOut)
def create_volunteer(volunteer: VolunteerCreate, db: Session = Depends(get_db)):
    new_volunteer = Volunteer(
        name=volunteer.name,
        age=volunteer.age,
        gender=volunteer.gender,
        phone=volunteer.phone,
        description=volunteer.description,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_volunteer)
    db.commit()
    db.refresh(new_volunteer)
    return new_volunteer


@router.put("/{volunteer_id}", response_model=VolunteerOut)
def update_volunteer(volunteer_id: int = Path(...), volunteer: VolunteerCreate = ...):
    return {
        "id": volunteer_id, "name": volunteer.name, "age": volunteer.age,
        "gender": volunteer.gender, "phone": volunteer.phone,
        "description": volunteer.description, "created_at": datetime.now()
    }

@router.delete("/{volunteer_id}")
def delete_volunteer(volunteer_id: int = Path(...)):
    return {"message": f"volunteer {volunteer_id} deleted successfully"}
