from fastapi import FastAPI
from app.routers import user, fingerprint, auth, volunteer, project, image_detection, count_ridges
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.formparsers import MultiPartParser
import os

MultiPartParser.max_part_size = 10 * 1024 * 1024  # 10 MB

app = FastAPI(title="TCC Dermatóglifo API", version="1.0")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "supersecret"))

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://web-dermo-metrics.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,                
    allow_credentials=True,               
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  
    allow_headers=["*"],                 
    expose_headers=["*"]
)

app.include_router(image_detection.router, prefix="/fingerprint", tags=["fingerprint"])
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(project.router)
app.include_router(volunteer.router)
app.include_router(fingerprint.router)
app.include_router(count_ridges.router, prefix="/fingerprint", tags=["fingerprint"])

