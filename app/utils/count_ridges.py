import cv2
import numpy as np
from scipy.signal import find_peaks

def count_ridges_between_minimal(
    image_gray: np.ndarray,
    p1: tuple,
    p2: tuple,
    thickness: int = 25,
) -> int:

    # Necessário:
    # - a imagem deve estar razoavelmente filtrada (alto contraste ridges/valleys)

    if image_gray is None:
        return 0

    h, w = image_gray.shape
    x1, y1 = int(p1[0]), int(p1[1])
    x2, y2 = int(p2[0]), int(p2[1])

    dx = x2 - x1
    dy = y2 - y1
    length = int(np.hypot(dx, dy))
    if length == 0:
        return 0

    # --- criar mascara retangular rotacionada ---
    angle = np.degrees(np.arctan2(dy, dx))
    center = ((x1 + x2) // 2, (y1 + y2) // 2)
    box = (center, (length, thickness), angle)
    rect = cv2.boxPoints(box).astype(np.int32)

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [rect], 255)

    # extrai região útil
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return 0

    x_min, x_max = np.min(xs), np.max(xs)
    y_min, y_max = np.min(ys), np.max(ys)

    patch = image_gray[y_min:y_max+1, x_min:x_max+1]
    patch_mask = mask[y_min:y_max+1, x_min:x_max+1]

    # aplicar máscara
    patch = patch.astype(np.float32) * (patch_mask.astype(np.float32) / 255.0)

    # rotacionar para horizontal
    h2, w2 = patch.shape
    c2 = (w2 / 2, h2 / 2)
    M = cv2.getRotationMatrix2D(c2, -angle, 1.0)
    rotated = cv2.warpAffine(patch, M, (w2, h2), flags=cv2.INTER_LINEAR)

    # recorta faixa central com mesma thickness
    start_row = max(0, (rotated.shape[0] - thickness) // 2)
    rotated_strip = rotated[start_row:start_row+thickness, :]

    # projeção simples (sem filtro)
    proj = np.sum(rotated_strip, axis=0)
    if np.max(proj) - np.min(proj) < 1e-6:
        return 0

    # normalização básica
    proj_norm = (proj - np.min(proj)) / (np.max(proj) - np.min(proj))

    # detectar picos (máximos → cristas)
    peaks, _ = find_peaks(proj_norm, height=0.3, distance=3)

    return int(len(peaks))
