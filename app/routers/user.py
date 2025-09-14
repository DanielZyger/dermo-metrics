from fastapi import APIRouter, Path, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.schemas.user import UserCreate, UserOut
from app.models.user import User
from app.schemas.project import ProjectOut
from app.models.user_project import UserProject
from app.db import get_db

router = APIRouter(prefix="/users", tags=["Users"])

def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        projects=[ProjectOut.from_orm(up.project) for up in user.projects]
    )

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [to_user_out(user) for user in users]

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int = Path(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return to_user_out(user)

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    new_user = User(
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role or "researcher",
        created_at=now,
        updated_at=now,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # se vier project_id, cria o vínculo
    if user.project_id:
        user_project = UserProject(user_id=new_user.id, project_id=user.project_id)
        db.add(user_project)
        db.commit()

    return to_user_out(user)

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int = Path(...),
    user: UserCreate = ...,
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.name = user.name
    db_user.email = user.email
    db_user.password = user.password
    db_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_user)
    return to_user_out(user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int = Path(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(db_user)
    db.commit()
    return None
