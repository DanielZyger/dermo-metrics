from fastapi import FastAPI
from app.routers import user, fingerprint, auth, volunteer, project
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TCC Dermatóglifo API", version="1.0")

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,                
    allow_credentials=True,               
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  
    allow_headers=["*"],                 
    expose_headers=["*"]
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(project.router)
app.include_router(volunteer.router)
app.include_router(fingerprint.router)
# app.include_router(review.router)

