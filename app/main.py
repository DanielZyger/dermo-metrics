from fastapi import FastAPI
from app.routers import user, fingerprint, auth, volunteer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TCC Dermatóglifo API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(volunteer.router)
app.include_router(fingerprint.router)
# app.include_router(review.router)

