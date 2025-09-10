import cv2
import numpy as np
import os

# Caminho de entrada e saída
img_path = "assets/images/image.png"
output_dir = "assets/outputs"
os.makedirs(output_dir, exist_ok=True)

# 1. Carregar imagem em escala de cinza
img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
cv2.imwrite(os.path.join(output_dir, "original.jpg"), img)

# 2. Filtro Gaussiano para reduzir ruído
blurred = cv2.GaussianBlur(img, (5, 5), 0)
cv2.imwrite(os.path.join(output_dir, "gaussiano.jpg"), blurred)

# 3. Realce adaptativo (CLAHE)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(blurred)
cv2.imwrite(os.path.join(output_dir, "realce_adaptativo.jpg"), enhanced)

# 4. Banco de filtros de Gabor
def gabor_filter_bank(img, ksize=31, sigma=7, lambd=12, gamma=0.5):
    thetas = [0, np.pi/4, np.pi/2, 3*np.pi/4]  # 4 direções principais
    accum = np.zeros_like(img, dtype=np.float32)
    for theta in thetas:
        kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lambd, gamma, 0, ktype=cv2.CV_32F)
        fimg = cv2.filter2D(img, cv2.CV_8UC3, kernel)
        accum = np.maximum(accum, fimg)
    return cv2.normalize(accum, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

gabor_normalized = gabor_filter_bank(enhanced)
cv2.imwrite(os.path.join(output_dir, "gabor.jpg"), gabor_normalized)

# 5. Binarização com Otsu
_, binary = cv2.threshold(gabor_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
cv2.imwrite(os.path.join(output_dir, "binarizada.jpg"), binary)
