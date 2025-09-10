from fastapi import APIRouter, Path, Depends, HTTPException
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

@router.get("/{volunteer_id}", response_model=VolunteerOut)
def get_volunteer(volunteer_id: int = Path(..., description="ID do voluntário"), db: Session = Depends(get_db)):
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    
    if not volunteer:
        raise HTTPException(
            status_code=404, 
            detail=f"Voluntário com ID {volunteer_id} não encontrado"
        )
    
    return volunteer

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
def update_volunteer(
    volunteer_id: int = Path(..., description="ID do voluntário"), 
    volunteer: VolunteerCreate = ..., 
    db: Session = Depends(get_db)
):
    existing_volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    
    if not existing_volunteer:
        raise HTTPException(
            status_code=404, 
            detail=f"Voluntário com ID {volunteer_id} não encontrado"
        )
    
    # Atualizar os campos
    existing_volunteer.name = volunteer.name
    existing_volunteer.age = volunteer.age
    existing_volunteer.gender = volunteer.gender
    existing_volunteer.phone = volunteer.phone
    existing_volunteer.description = volunteer.description
    existing_volunteer.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing_volunteer)
    return existing_volunteer

@router.delete("/{volunteer_id}")
def delete_volunteer(volunteer_id: int = Path(..., description="ID do voluntário"), db: Session = Depends(get_db)):
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    
    if not volunteer:
        raise HTTPException(
            status_code=404, 
            detail=f"Voluntário com ID {volunteer_id} não encontrado"
        )
    
    db.delete(volunteer)
    db.commit()
    
    return {"message": f"Voluntário {volunteer_id} deletado com sucesso"}