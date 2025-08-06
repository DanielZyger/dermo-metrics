from app.db import engine, SessionLocal
from app.models import Base, Patient

Base.metadata.create_all(bind=engine)

def insert_patient_with_image(name, image_path):
    session = SessionLocal()
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()
    new_patient = Patient(name=name, fingerprint_image=img_data)
    session.add(new_patient)
    session.commit()
    session.close()
    print(f"Paciente '{name}' inserido com sucesso!")

if __name__ == "__main__":
    insert_patient_with_image("João Silva", "images/test_fingerprint.png")
