from sqlalchemy import create_engine
from app.models.fingerprint import Base
from app.models.volunteer import Volunteer
from app.models.user import User
from app.models.fingerprint import Fingerprint
from app.models.review import Review

from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

Base.metadata.create_all(bind=engine)

print("Tabelas criadas com sucesso!")
