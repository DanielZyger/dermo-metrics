import cv2
import numpy as np
import os

def power_law_transformation(image, gamma=1.4):
    image = image / 255.0
    image = np.power(image, gamma)
    return np.uint8(image * 255)

def contrast_stretching(image):
    min_val = np.min(image)
    max_val = np.max(image)
    stretched = (image - min_val) * (255 / (max_val - min_val))
    return np.uint8(stretched)

def adaptive_enhancement(image, gamma=1.4):
    img_power = power_law_transformation(image, gamma)
    img_stretched = contrast_stretching(img_power)
    return img_stretched

def gabor_filter_bank(image, ksize=9, sigma=3, lambd=8, gamma=0.5):
    """Aplica Gabor em várias orientações e combina resultados (média)."""
    thetas = [0, np.pi/4, np.pi/2, 3*np.pi/4]  # 0°, 45°, 90°, 135°
    accum = np.zeros_like(image, dtype=np.float32)
    for theta in thetas:
        kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lambd, gamma, 0, ktype=cv2.CV_32F)
        filtered = cv2.filter2D(image, cv2.CV_32F, kernel)
        accum += filtered
    accum /= len(thetas)  # média das orientações
    return cv2.normalize(accum, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def process_image(path, output_dir="assets/output"):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Imagem não encontrada em: {path}")
    
    # 1. Suavização Gaussiana leve
    img_gauss = cv2.GaussianBlur(img, (3, 3), 1.0)

    # 2. Realce adaptativo
    img_enhanced = adaptive_enhancement(img_gauss, gamma=1.4)

    # 3. Filtro de Gabor em várias orientações
    img_gabor = gabor_filter_bank(img_enhanced)

    # 4. Binarização adaptativa
    img_bin = cv2.adaptiveThreshold(img_gabor, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 15, 5)

    # Criar diretório
    os.makedirs(output_dir, exist_ok=True)

    # Salvar resultados
    cv2.imwrite(os.path.join(output_dir, "original.jpg"), img)
    cv2.imwrite(os.path.join(output_dir, "gaussiano.jpg"), img_gauss)
    cv2.imwrite(os.path.join(output_dir, "realce_adaptativo.jpg"), img_enhanced)
    cv2.imwrite(os.path.join(output_dir, "gabor.jpg"), img_gabor)
    cv2.imwrite(os.path.join(output_dir, "binarizada.jpg"), img_bin)

    print(f"✅ Processamento concluído! Resultados salvos em: {output_dir}")

if __name__ == "__main__":
    process_image("assets/images/fingerprint1.jpeg")
