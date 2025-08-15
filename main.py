from app.db import SessionLocal
from app.models.fingerprint import Fingerprint
from app.models.volunteer import Volunteer
from app.constants.enum import HandEnum, FingerEnum, PatternEnum

def insert_volunteer_with_fingerprint(image_path):
    session = SessionLocal()

    try:
        # Cria um novo paciente
        new_volunteer = Volunteer(name="João Silva")
        session.add(new_volunteer)
        session.flush()

        with open(image_path, "rb") as img_file:
            img_data = img_file.read()

        new_fingerprint = Fingerprint(
            volunteer_id=new_volunteer.id,
            hand=HandEnum.right,
            finger=FingerEnum.thumb,
            pattern_type=PatternEnum.loop,
            delta=2,
            image_data=img_data,
            notes="Exemplo de teste com imagem"
        )

        session.add(new_fingerprint)
        session.commit()
        print(f"Paciente '{new_volunteer.name}' e impressão digital inseridos com sucesso!")

    except Exception as e:
        session.rollback()
        print("Erro ao inserir paciente e impressão digital:", e)
    finally:
        session.close()

if __name__ == "__main__":
    insert_volunteer_with_fingerprint("/home/daniel.santos/Downloads/fingerprint-example.jpg")
