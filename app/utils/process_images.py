import fingerprint_enhancer
import cv2
import numpy as np

def process(image_bytes: bytes) -> bytes:
    """
    Processa uma imagem de digital usando a biblioteca fingerprint_enhancer.
    
    Args:
        image_bytes (bytes): Bytes da imagem de entrada
        
    Returns:
        bytes: Bytes da imagem processada em formato PNG
    """
    try:
        # 1. Converter bytes → imagem em escala de cinza
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            raise ValueError("Não foi possível decodificar a imagem")
        
        # 2. Aplicar o enhancement da biblioteca
        enhanced_img = fingerprint_enhancer.enhance_fingerprint(img)
        
        # 3. Converter o resultado para uint8 (0-255)
        # A biblioteca retorna valores float no range [0,1]
        processed_img = (enhanced_img * 255).astype(np.uint8)
        
        # 4. Converter resultado final para PNG (bytes)
        success, encoded_img = cv2.imencode(".png", processed_img)
        if not success:
            raise ValueError("Erro ao converter imagem processada para PNG")
            
        return encoded_img.tobytes()
        
    except Exception as e:
        # Em caso de erro, retorna a imagem original
        print(f"Erro no processamento: {e}")
        # Tenta retornar pelo menos a imagem em escala de cinza
        try:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
            success, encoded_img = cv2.imencode(".png", img)
            if success:
                return encoded_img.tobytes()
        except:
            pass
        
        # Se tudo falhar, retorna os bytes originais
        return image_bytes