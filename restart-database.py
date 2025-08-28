from sqlalchemy import create_engine, text
from app.models.fingerprint import Base
from app.models.volunteer import Volunteer
from app.models.project import Project
from app.models.user_project import UserProject
from app.models.user import User
from app.models.fingerprint import Fingerprint
from app.models.review import Review

from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE;"))
    conn.execute(text("CREATE SCHEMA public;"))
    conn.commit()

print("Schema limpo com sucesso!")

print("Criando tabelas...")
Base.metadata.create_all(bind=engine)

print("Banco de dados resetado com sucesso!")