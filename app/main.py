from fastapi import FastAPI
from app.routers import user, patient, fingerprint

app = FastAPI(title="TCC Dermatóglifo API", version="1.0")

app.include_router(user.router)
app.include_router(patient.router)
app.include_router(fingerprint.router)
