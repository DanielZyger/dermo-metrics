from fastapi import FastAPI
from app.routers import user, fingerprint, review, auth, volunteer

app = FastAPI(title="TCC Dermatóglifo API", version="1.0")

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(volunteer.router)
app.include_router(fingerprint.router)
app.include_router(review.router)

