import cv2
import numpy as np
import math
from scipy.ndimage import gaussian_filter1d


def count_ridges_between_minimal(
    image_gray: np.ndarray,
    p1: tuple,
    p2: tuple,
    thickness: int = 20,     # faixa perpendicular
    oversample: int = 4,
    min_width_px: int = 6,  # ✅ largura mínima de uma crista
    min_gap_px: int = 8,    # ✅ distância mínima entre cristas
) -> int:

    import cv2
    import numpy as np
    import math
    from scipy.ndimage import gaussian_filter1d

    if image_gray is None:
        return 0

    if image_gray.ndim == 3:
        image_gray = cv2.cvtColor(image_gray, cv2.COLOR_BGR2GRAY)
    image_gray = image_gray.astype(np.uint8)

    x1, y1 = float(p1[0]), float(p1[1])
    x2, y2 = float(p2[0]), float(p2[1])

    length = math.hypot(x2 - x1, y2 - y1)
    if length < 5:
        return 0

    n = int(length * oversample)
    if n < 20:
        return 0

    dx = (x2 - x1) / length
    dy = (y2 - y1) / length
    nx = -dy
    ny = dx

    offsets = np.linspace(-thickness / 2.0, thickness / 2.0, thickness)
    t_vals = np.linspace(0, length, n)

    perfis = []

    for off in offsets:
        xs = (x1 + nx * off) + dx * t_vals
        ys = (y1 + ny * off) + dy * t_vals

        map_x = xs.astype(np.float32).reshape(1, -1)
        map_y = ys.astype(np.float32).reshape(1, -1)

        linha = cv2.remap(
            image_gray,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101,
        )

        sig = linha[0].astype(np.float32)
        sig = gaussian_filter1d(sig, sigma=2.0)   # ✅ suavização mais forte
        perfis.append(sig)

    perfis = np.stack(perfis, axis=0)

    sig = (perfis - perfis.min()) / (perfis.max() - perfis.min() + 1e-6)
    sig_inv = 1.0 - sig
    perfil_medio = sig_inv.mean(axis=0)

    perfil_medio = gaussian_filter1d(perfil_medio, sigma=3.0)  # ✅ suaviza o perfil final

    perfil_u8 = np.clip(perfil_medio * 255, 0, 255).astype(np.uint8)

    _, bin_1d = cv2.threshold(
        perfil_u8,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    mask = (bin_1d > 0).ravel()

    if not np.any(mask):
        return 0

    # =========================
    # ✅ FILTRO POR LARGURA E DISTÂNCIA
    # =========================

    count = 0
    i = 0
    last_end = -np.inf
    N = len(mask)

    while i < N:
        if mask[i]:
            start = i
            while i < N and mask[i]:
                i += 1
            end = i
            width = end - start

            # largura mínima da crista
            if width >= min_width_px:

                # distância mínima para a crista anterior
                if start - last_end >= min_gap_px:
                    count += 1
                    last_end = end
        i += 1

    return int(count)
