import fingerprint_enhancer
import cv2
import os

output_dir = 'assets/teste'
os.makedirs(output_dir, exist_ok=True)

img = cv2.imread('assets/images/image.png', cv2.IMREAD_GRAYSCALE)  # read input image
out = fingerprint_enhancer.enhance_fingerprint(img)  # enhance the fingerprint image


out = (out * 255).astype("uint8")

# Converter de bool para uint8 (0 ou 255)

cv2.imwrite(os.path.join(output_dir, "lib_pronta.jpg"), out)
