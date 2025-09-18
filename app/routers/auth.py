from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from datetime import datetime
from fastapi.responses import RedirectResponse
from app.schemas.user import UserOut
from app.models.user import User
from app.db import get_db
import jwt
import os


router = APIRouter(prefix="/auth", tags=["Auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback", response_model=UserOut)
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(status_code=400, detail="Google login failed")

        user = db.query(User).filter(User.email == user_info["email"]).first()

        if not user:
            user = User(
                name=user_info["name"],
                email=user_info["email"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        payload = {"user_id": user.id, "email": user.email}
        jwt_token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm=os.getenv("JWT_ALGORITHM"))

        redirect_url = f"http://localhost:8080/create-project?token={jwt_token}&user_id={user.id}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google login error: {str(e)}")

@router.post("/logout")
def logout():
    return {"message": "Logout successful"}
