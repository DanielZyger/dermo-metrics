from fastapi import APIRouter, Path
from app.schemas.user import UserCreate, UserOut
from datetime import datetime
from app.constants.enum import UserRoles
from fastapi import HTTPException

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserOut])
def list_users():
    return [{
        "id": 1, "name": "João da Silva", "email": "joao@email.com", "role": UserRoles.admin,
        "created_at": datetime.now()
    }]

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int = Path(...)):
    if user_id == 1:
        return {
            "id": 1, "name": "João da Silva", "email": "joao@email.com",
            "role": UserRoles.admin, "created_at": datetime.now()
        }
    elif user_id == 2:
        return {
            "id": 2, "name": "Maria Souza", "email": "maria@email.com",
            "role": UserRoles.researcher, "created_at": datetime.now()
        }
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/", response_model=UserOut)
def create_user(user: UserCreate):
    return {
        "id": 2, "name": user.name, "email": user.email, "role": UserRoles.researcher, "created_at": datetime.now()
    }

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int = Path(...), user: UserCreate = ...):
    return {
        "id": user_id, "name": user.name, "email": user.email, "role": UserRoles.researcher, "created_at": datetime.now()
    }

@router.delete("/{user_id}")
def delete_user(user_id: int = Path(...)):
    return {"message": f"User {user_id} deleted successfully"}
