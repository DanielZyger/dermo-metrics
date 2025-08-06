from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas.auth import LoginRequest
from app.schemas.user import UserOut
from app.constants.enum import UserRoles

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=UserOut)
def login(credentials: LoginRequest):
    if credentials.email == "joao@email.com" and credentials.password == "123456":
        return {
            "id": 1,
            "name": "João da Silva",
            "email": credentials.email,
            "role": UserRoles.admin,
            "created_at": datetime.now()
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
def logout():
    return {"message": "Logout successful"}
