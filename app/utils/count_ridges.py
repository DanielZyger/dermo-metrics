import cv2
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

def count_ridges_between_minimal(
    image_gray: np.ndarray,
    p1: tuple,
    p2: tuple,
    thickness: int = 32,
) -> int:

    if image_gray is None:
        return 0

    h, w = image_gray.shape
    x1, y1 = int(p1[0]), int(p1[1])
    x2, y2 = int(p2[0]), int(p2[1])

    dx = x2 - x1
    dy = y2 - y1
    length = int(np.hypot(dx, dy))
    if length < 10:
        return 0

    angle = np.degrees(np.arctan2(dy, dx))
    center = ((x1 + x2) // 2, (y1 + y2) // 2)
    box = (center, (length, thickness), angle)
    rect = cv2.boxPoints(box).astype(np.int32)

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [rect], 255)

    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return 0

    x_min, x_max = np.min(xs), np.max(xs)
    y_min, y_max = np.min(ys), np.max(ys)

    patch = image_gray[y_min:y_max+1, x_min:x_max+1]
    patch_mask = mask[y_min:y_max+1, x_min:x_max+1] / 255.0
    patch = patch.astype(np.float32) * patch_mask

    h2, w2 = patch.shape
    M = cv2.getRotationMatrix2D((w2 / 2, h2 / 2), -angle, 1.0)
    rotated = cv2.warpAffine(patch, M, (w2, h2))

    start_row = max(0, (rotated.shape[0] - thickness) // 2)
    rotated_strip = rotated[start_row:start_row + thickness, :]

    # Binarização adaptativa
    rotated_strip = rotated_strip.astype(np.uint8)
    thresh = cv2.adaptiveThreshold(
        rotated_strip,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        21,
        5,
    )

    # Projeção
    proj = np.sum(thresh, axis=0).astype(np.float32)

    # ✅ CORREÇÃO AQUI
    if np.ptp(proj) < 5:
        return 0

    # Suavização
    proj_smooth = gaussian_filter1d(proj, sigma=2.5)

    proj_norm = (proj_smooth - proj_smooth.min()) / (
        proj_smooth.max() - proj_smooth.min() + 1e-6
    )

    dx_est = max(4, int(length / 25))

    peaks, _ = find_peaks(
        proj_norm,
        height=0.25,
        distance=dx_est,
        prominence=0.15,
    )

    return int(len(peaks))
