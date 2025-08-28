import cv2
import numpy as np

def process(image_bytes: bytes) -> bytes:
    # 0. Converter bytes → imagem em escala de cinza
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)

    # 1. Suavização inicial (Gaussiano)
    blurred = cv2.GaussianBlur(img, (5, 5), 0)

    # 2. Realce adaptativo (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    # 3. Filtro de Gabor (realce de texturas, útil em digitais)
    #   usamos múltiplas orientações e somamos os resultados
    gabor_sum = np.zeros_like(enhanced, dtype=np.float32)
    num_orientations = 8
    ksize = 15  # tamanho do kernel
    sigma = 4.0
    lambd = 10.0
    gamma = 0.5

    for theta in np.linspace(0, np.pi, num_orientations, endpoint=False):
        kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lambd, gamma, 0, ktype=cv2.CV_32F)
        filtered = cv2.filter2D(enhanced, cv2.CV_32F, kernel)
        gabor_sum = np.maximum(gabor_sum, filtered)

    gabor_normalized = cv2.normalize(gabor_sum, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # erosão
    # opening

    # 4. Binarização (Otsu)
    _, binary = cv2.threshold(gabor_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # ✅ Converte resultado final para PNG (bytes)
    success, encoded_img = cv2.imencode(".png", binary)
    if not success:
        raise ValueError("Erro ao converter imagem processada para PNG")
    return encoded_img.tobytes()
