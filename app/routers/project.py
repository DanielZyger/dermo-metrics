from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.project import ProjectCreate, ProjectOut
from datetime import datetime
from app.models.project import Project
from app.db import get_db

router = APIRouter(prefix="/projects", tags=["Project"])

@router.get("/", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int = Path(..., description="ID do projeto"), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=404, 
            detail=f"Projeto com ID {project_id} não encontrado"
        )
    
    return project

@router.post("/", response_model=ProjectOut)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    new_project = Project(
        name=project.name,
        description=project.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int = Path(..., description="ID do projeto"), 
    project: ProjectCreate = ..., 
    db: Session = Depends(get_db)
):
    existing_project = db.query(Project).filter(Project.id == project_id).first()
    
    if not existing_project:
        raise HTTPException(
            status_code=404, 
            detail=f"Projeto com ID {project_id} não encontrado"
        )
    
    existing_project.name = project.name
    existing_project.description = project.description
    existing_project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(existing_project)
    return existing_project

@router.delete("/{project_id}")
def delete_project(project_id: int = Path(..., description="ID do projeto"), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=404, 
            detail=f"Projeto com ID {project_id} não encontrado"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": f"Projeto {project_id} deletado com sucesso"}