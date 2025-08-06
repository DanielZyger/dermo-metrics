from app.db import SessionLocal
from app.models.fingerprint import Fingerprint

def export_fingerprint_image(fingerprint_id, output_path):
    session = SessionLocal()
    try:
        # Busca a impressão digital pelo ID
        fingerprint = session.query(Fingerprint).filter_by(id=fingerprint_id).first()
        if not fingerprint:
            print(f"Nenhuma impressão digital encontrada com ID {fingerprint_id}")
            return

        if fingerprint.image_data:
            # Salva a imagem binária em um arquivo
            with open(output_path, "wb") as out_file:
                out_file.write(fingerprint.image_data)
            print(f"Imagem exportada com sucesso para: {output_path}")
        else:
            print("Impressão digital não contém dados de imagem.")

    except Exception as e:
        print("Erro ao exportar imagem:", e)
    finally:
        session.close()

if __name__ == "__main__":
    export_fingerprint_image(fingerprint_id=1, output_path="output_fingerprint.jpg")
