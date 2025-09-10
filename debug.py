import cv2
import numpy as np
import os

def process(path, output_dir="assets/output"):
    # 0. Converter bytes → imagem em escala de cinza
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

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
        kernel = cv2.getGaborKernel((20, 20), sigma, theta, lambd, gamma, 0, ktype=cv2.CV_32F)
        filtered = cv2.filter2D(enhanced, cv2.CV_32F, kernel)
        gabor_sum = np.maximum(gabor_sum, filtered)

    gabor_normalized = cv2.normalize(gabor_sum, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    kernel = np.ones((3,3), np.uint8)
    cleaned = cv2.morphologyEx(gabor_normalized, cv2.MORPH_OPEN, kernel)
    median = cv2.medianBlur(gabor_normalized, 3)

    # cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
    # erosão
    # opening

    # 4. Binarização (Otsu)
    _, binary = cv2.threshold(gabor_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # k = np.ones((3, 3), np.uint8)  # Define 5x5 kernel
    # inv = cv2.bitwise_not(binary)                                 
    # out = cv2.erode(inv, k, 1)              

    # ✅ Converte resultado final para PNG (bytes)
    cv2.imwrite(os.path.join(output_dir, "original.jpg"), img)
    cv2.imwrite(os.path.join(output_dir, "gaussiano.jpg"), blurred)
    cv2.imwrite(os.path.join(output_dir, "realce_adaptativo.jpg"), enhanced)
    cv2.imwrite(os.path.join(output_dir, "gabor.jpg"), gabor_normalized)
    cv2.imwrite(os.path.join(output_dir, "erosao.jpg"), median)

    cv2.imwrite(os.path.join(output_dir, "binarizada.jpg"), binary)



if __name__ == "__main__":
    process("assets/images/fingerprint.jpeg")