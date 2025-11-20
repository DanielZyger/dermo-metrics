import fingerprint_enhancer
import cv2
import numpy as np

def process(image_bytes: bytes) -> bytes:
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            raise ValueError("Não foi possível decodificar a imagem")
        
        enhanced = fingerprint_enhancer.enhance_fingerprint(
            img,
            relative_scale_factor_x=1.0,
            relative_scale_factor_y=1.0,
            gradient_sigma=2,
            block_sigma=9,
            orient_smooth_sigma=9,
            ridge_filter_thresh=-0.5,
        )        
        processed_img = (enhanced * 255).astype(np.uint8)

        processed_img = 255 - processed_img

        # 4. Converter resultado final para PNG (bytes)
        success, encoded_img = cv2.imencode(".png", processed_img)
        if not success:
            raise ValueError("Erro ao converter imagem processada para PNG")
            
        return encoded_img.tobytes()
        
    except Exception as e:
        print(f"Erro no processamento: {e}")
        try:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
            success, encoded_img = cv2.imencode(".png", img)
            if success:
                return encoded_img.tobytes()
        except:
            pass
        
        return image_bytes