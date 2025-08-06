from app.db import SessionLocal
from app.models.fingerprint import Fingerprint
from app.models.patient import Patient
from app.constants.enum import HandEnum, FingerEnum, PatternEnum

def insert_patient_with_fingerprint(image_path):
    session = SessionLocal()

    try:
        # Cria um novo paciente
        new_patient = Patient(name="João Silva")
        session.add(new_patient)
        session.flush()  # Para garantir que new_patient.id seja populado

        # Lê a imagem em binário
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()

        # Cria uma impressão digital associada ao paciente
        new_fingerprint = Fingerprint(
            patient_id=new_patient.id,
            hand=HandEnum.right,
            finger=FingerEnum.thumb,
            pattern_type=PatternEnum.loop,
            delta=2,
            image_data=img_data,
            notes="Exemplo de teste com imagem"
        )

        session.add(new_fingerprint)
        session.commit()
        print(f"Paciente '{new_patient.name}' e impressão digital inseridos com sucesso!")

    except Exception as e:
        session.rollback()
        print("Erro ao inserir paciente e impressão digital:", e)
    finally:
        session.close()

if __name__ == "__main__":
    insert_patient_with_fingerprint("/home/daniel.santos/Downloads/fingerprint-example.jpg")
