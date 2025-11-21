import base64
import io
import math
import cv2
import numpy as np
from scipy import ndimage
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.models.fingerprint import Fingerprint
from sqlalchemy.orm import Session
from enum import Enum
from app.db import get_db
from app.utils.count_ridges import count_ridges_between_minimal
from app.utils.type_fingerprint import detect_fingerprint_type

router = APIRouter()

class ImageTypeEnum(str, Enum):
    raw = "raw"
    filtered = "filtered"

class DetectionPoint(BaseModel):
    x: int
    y: int

class DetectionResult(BaseModel):
    deltas: List[DetectionPoint]
    cores: List[DetectionPoint]
    number_deltas: int
    ridge_counts: Optional[int] = None
    pattern_type: Optional[str] = None
    image_width: int = 700
    image_height: int = 700


class DetectionRequest(BaseModel):
    fingerprint_id: int
    image_type: ImageTypeEnum
    block_size: int = 16
    min_coherence: float = 0.5


class SimpleFingerprintDetector:

    def __init__(self, image_array: np.ndarray):
        self.image = image_array
        if self.image is None or self.image.size == 0:
            raise ValueError("Imagem inválida")
        if len(self.image.shape) != 2:
            # força grayscale
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.height, self.width = self.image.shape

    def compute_gradients(self, blur_ksize: int = 5):
        # blur leve para reduzir ruído antes do sobel
        if blur_ksize and blur_ksize > 1:
            img = cv2.GaussianBlur(self.image, (blur_ksize, blur_ksize), 0)
        else:
            img = self.image
        self.gx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
        self.gy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)

    def _gaussian_weights(self, size):
        """Retorna uma máscara gaussiana normalizada de dimensão (size,size)."""
        sigma = max(0.5, size / 6.0)
        ax = np.linspace(-(size-1)/2., (size-1)/2., size)
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-(xx**2 + yy**2) / (2. * sigma**2))
        return kernel / np.sum(kernel)

    def compute_orientation_field(self, block_size=16):
        h, w = self.image.shape
        blocks_h = h // block_size
        blocks_w = w // block_size

        orientation = np.zeros((blocks_h, blocks_w))
        coherence = np.zeros((blocks_h, blocks_w))

        # precompute gaussian weights para o bloco
        gw = self._gaussian_weights(block_size)

        for i in range(blocks_h):
            for j in range(blocks_w):
                y_start = i * block_size
                x_start = j * block_size
                y_end = y_start + block_size
                x_end = x_start + block_size

                gx_block = self.gx[y_start:y_end, x_start:x_end]
                gy_block = self.gy[y_start:y_end, x_start:x_end]

                # if block menor que o esperado (bordas), pad to block_size
                if gx_block.shape != (block_size, block_size):
                    gx_b = np.zeros((block_size, block_size))
                    gy_b = np.zeros((block_size, block_size))
                    gx_b[:gx_block.shape[0], :gx_block.shape[1]] = gx_block
                    gy_b[:gy_block.shape[0], :gy_block.shape[1]] = gy_block
                    gx_block = gx_b
                    gy_block = gy_b

                # weighted sums
                Gxx = np.sum(gw * (gx_block * gx_block))
                Gyy = np.sum(gw * (gy_block * gy_block))
                Gxy = np.sum(gw * (gx_block * gy_block))

                # orientation em radianos (range -pi/2 .. pi/2)
                orientation[i, j] = 0.5 * np.arctan2(2.0 * Gxy, (Gxx - Gyy) + 1e-12)

                # coerência robusta (normalizada)
                denom = (Gxx + Gyy)
                coherence[i, j] = np.sqrt((Gxx - Gyy)**2 + 4.0 * Gxy**2) / (denom + 1e-12)

        return orientation, coherence, block_size

    def smooth_orientation(self, orientation, sigma=2.0):
        # suaviza usando trig-identidade para evitar discontinuidades
        sin_ori = np.sin(2.0 * orientation)
        cos_ori = np.cos(2.0 * orientation)

        sin_smooth = ndimage.gaussian_filter(sin_ori, sigma)
        cos_smooth = ndimage.gaussian_filter(cos_ori, sigma)

        orientation_smooth = 0.5 * np.arctan2(sin_smooth, cos_smooth)
        return orientation_smooth

    @staticmethod
    def _wrap_angle(a):
        """Mantenha ângulo dentro de (-pi, pi]."""
        return (a + np.pi) % (2 * np.pi) - np.pi

    def compute_poincare_index(self, orientation, coherence, min_coherence=0.5):
        """
        Calcula índice de Poincaré numa grade de blocos.
        Valores típicos:
          • ~ +0.5 → core (ponto central)
          • ~ −0.5 → delta
        """
        h, w = orientation.shape
        poincare = np.zeros((h, w), dtype=np.float32)

        for i in range(1, h - 1):
            for j in range(1, w - 1):
                # ignora blocos de baixa coerência
                if coherence[i, j] < min_coherence:
                    continue

                # 8 vizinhos em ordem horária
                neigh = [
                    orientation[i - 1, j],
                    orientation[i - 1, j + 1],
                    orientation[i, j + 1],
                    orientation[i + 1, j + 1],
                    orientation[i + 1, j],
                    orientation[i + 1, j - 1],
                    orientation[i, j - 1],
                    orientation[i - 1, j - 1],
                ]

                angle_sum = 0.0
                for k in range(8):
                    a1 = neigh[k]
                    a2 = neigh[(k + 1) % 8]
                    diff = a2 - a1
                    diff = self._wrap_angle(diff)

                    # orientação de cristas é pi-periódica → limitamos saltos
                    if diff > np.pi / 2:
                        diff -= np.pi
                    elif diff < -np.pi / 2:
                        diff += np.pi

                    angle_sum += diff

                idx = angle_sum / (2.0 * np.pi)
                poincare[i, j] = idx

        # limpa valores absurdos
        poincare[~np.isfinite(poincare)] = 0.0
        return poincare

    def refine_position(self, poincare, coherence, i, j, block_size, search_radius_blocks=2):
        """
        Refinamento sub-pixel:
        - pega região ao redor do bloco (em blocos)
        - calcula centro de massa ponderado por |poincare| * coherence local
        - converte para coordenadas de pixels (centro do bloco) com subpixel
        """
        h, w = poincare.shape

        r = search_radius_blocks
        i_min = max(0, i - r)
        i_max = min(h, i + r + 1)
        j_min = max(0, j - r)
        j_max = min(w, j + r + 1)

        region_pi = poincare[i_min:i_max, j_min:j_max]
        region_coh = coherence[i_min:i_max, j_min:j_max]

        weight = np.abs(region_pi) * (region_coh + 1e-6)

        if np.sum(weight) < 1e-8:
            refined_i = i
            refined_j = j
        else:
            ys, xs = np.indices(weight.shape)
            y_c = np.sum(ys * weight) / np.sum(weight)
            x_c = np.sum(xs * weight) / np.sum(weight)

            refined_i = i_min + y_c
            refined_j = j_min + x_c

        y_pixel = refined_i * block_size + block_size / 2.0
        x_pixel = refined_j * block_size + block_size / 2.0

        return float(x_pixel), float(y_pixel)

    def find_singular_points(
        self,
        poincare,
        coherence,
        block_size,
        min_coherence_override=None,
        radius_blocks=2,
    ):
        """
        Encontra deltas e cores de forma mais robusta:
        - usa magnitude típica do índice de Poincaré (≈ ±0.5)
        - usa coerência, mas sem matar regiões de singularidade
        - exige máximo local em |poincare|
        """
        import numpy as np  # type: ignore

        h, w = poincare.shape

        # Coerência válida
        coh_vals = coherence.flatten()
        coh_vals = coh_vals[~np.isnan(coh_vals)]
        if coh_vals.size == 0:
            return [], []

        # Em regiões de singularidade a coerência tende a ser um pouco menor.
        # Então usamos limiares relativos à mediana, com piso absoluto.
        coh_med = float(np.median(coh_vals))

        base_coh_thr = max(0.4, coh_med * 0.7)      # para considerar ponto válido
        delta_coh_thr = max(0.6, coh_med * 0.9)     # delta → mais exigente
        core_coh_thr  = max(0.65, coh_med * 0.95)   # core → ainda mais exigente

        if min_coherence_override is not None:
            # se o usuário pedir min_coherence maior, respeitamos
            base_coh_thr  = min(base_coh_thr, min_coherence_override)
            delta_coh_thr = max(delta_coh_thr, min_coherence_override)
            core_coh_thr  = max(core_coh_thr, min_coherence_override)

        # Só olha Poincaré onde a coerência não é extremamente baixa
        valid_mask = coherence >= base_coh_thr
        abs_pi_vals = np.abs(poincare[valid_mask])
        abs_pi_vals = abs_pi_vals[~np.isnan(abs_pi_vals)]
        if abs_pi_vals.size == 0:
            return [], []

        # magnitude típica de singularidade (clamp pra não ficar extremo)
        pi_p90 = float(np.percentile(abs_pi_vals, 90))
        min_pi_mag = max(0.2, min(0.7, pi_p90))

        deltas = []
        cores = []

        # margem em blocos para evitar bordas
        MARGIN = max(1, radius_blocks + 1)

        for i in range(MARGIN, h - MARGIN):
            for j in range(MARGIN, w - MARGIN):
                pi_value = float(poincare[i, j])
                coh_value = float(coherence[i, j])

                if np.isnan(pi_value) or np.isnan(coh_value):
                    continue

                # coerência muito baixa ou magnitude muito pequena → descarta
                if coh_value < base_coh_thr:
                    continue
                if abs(pi_value) < min_pi_mag:
                    continue

                # janela pequena para checar máximo local em |pi|
                local_pi_abs = np.abs(poincare[i - 1 : i + 2, j - 1 : j + 2])

                # ========= DELTA (índice negativo forte, próximo de -0.5) =========
                if pi_value < 0:
                    if coh_value < delta_coh_thr:
                        continue
                    # reforço: queremos algo relativamente perto de -0.5
                    if abs(pi_value + 0.5) > 0.45:
                        continue
                    if abs(pi_value) < np.max(local_pi_abs):
                        continue

                    x_px, y_px = self.refine_position(
                        poincare,
                        coherence,
                        i,
                        j,
                        block_size,
                        search_radius_blocks=radius_blocks,
                    )
                    deltas.append(
                        {
                            "x": x_px,
                            "y": y_px,
                            "index": pi_value,
                            "coherence": coh_value,
                        }
                    )

                # ========= CORE (índice positivo forte, próximo de +0.5) =========
                else:
                    if coh_value < core_coh_thr:
                        continue
                    if abs(pi_value - 0.5) > 0.45:
                        continue
                    if abs(pi_value) < np.max(local_pi_abs):
                        continue

                    x_px, y_px = self.refine_position(
                        poincare,
                        coherence,
                        i,
                        j,
                        block_size,
                        search_radius_blocks=radius_blocks,
                    )
                    cores.append(
                        {
                            "x": x_px,
                            "y": y_px,
                            "index": pi_value,
                            "coherence": coh_value,
                        }
                    )

        return deltas, cores

    def remove_duplicates(self, points, min_distance=None):
        """
        Remove pontos muito próximos. min_distance pode ser absoluto ou relativo ao menor dimensão.
        Se None, define como ~3% da menor dimensão.
        Ordena por confiança (|index| * coherence).
        """
        if not points:
            return []

        if min_distance is None:
            min_distance = max(10.0, min(self.width, self.height) * 0.03)

        def score(p):
            idx = abs(p.get("index", 0.0))
            coh = p.get("coherence", 0.0)
            avg = p.get("avg_coherence", 0.0)
            return idx * (coh + 1e-6) * (avg + 1e-6)

        pts_sorted = sorted(points, key=lambda p: score(p), reverse=True)

        filtered = []
        for pt in pts_sorted:
            keep = True
            for ex in filtered:
                dist = math.hypot(pt["x"] - ex["x"], pt["y"] - ex["y"])
                if dist < min_distance:
                    keep = False
                    break
            if keep:
                filtered.append(pt)

        return filtered

    def detect(self, block_size=16, min_coherence=0.4):
        # 1) Gradientes
        self.compute_gradients(blur_ksize=5)

        # 2) Campo de orientação e coerência
        orientation, coherence, bs = self.compute_orientation_field(block_size)

        # 3) Suavizar orientação
        orientation = self.smooth_orientation(orientation, sigma=2.0)

        # 4) Poincaré index
        poincare = self.compute_poincare_index(
            orientation, coherence, min_coherence=min_coherence
        )

        # 5) Encontrar candidatos e refinar
        deltas, cores = self.find_singular_points(
            poincare,
            coherence,
            bs,
            min_coherence_override=min_coherence,
            radius_blocks=max(1, int(2 * (16 / max(8, block_size)))),
        )

        # 6) Remoção de duplicatas (distância relativa)
        deltas = self.remove_duplicates(
            deltas, min_distance=max(8.0, min(self.width, self.height) * 0.02)
        )
        cores = self.remove_duplicates(
            cores, min_distance=max(8.0, min(self.width, self.height) * 0.03)
        )

        # limita a no máximo 2 por tipo (caso haja múltiplos fortes)
        if len(deltas) > 2:
            deltas = deltas[:2]
        if len(cores) > 2:
            cores = cores[:2]

        return deltas, cores


def decode_binary_image(image_bytes: bytes) -> np.ndarray:
    """Decodifica bytes de imagem para array numpy (escala de cinza)."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)

        image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError("Falha ao decodificar a imagem")

        return image

    except Exception as e:
        raise ValueError(f"Erro ao processar imagem: {str(e)}")


@router.post("/detect-singular-points", response_model=DetectionResult)
async def detect_singular_points(
    request: DetectionRequest,
    db: Session = Depends(get_db),
) -> DetectionResult:
    fingerprint = (
        db.query(Fingerprint)
        .filter(Fingerprint.id == request.fingerprint_id)
        .first()
    )

    if not fingerprint:
        raise HTTPException(
            status_code=404,
            detail=f"Fingerprint com ID {request.fingerprint_id} não encontrada",
        )

    if request.image_type == ImageTypeEnum.raw:
        image_bytes = fingerprint.image_data
        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="A fingerprint não possui imagem raw (image_data)",
            )
    else:
        image_bytes = fingerprint.image_filtered
        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="A fingerprint não possui imagem filtered (image_filtered)",
            )

    # Decodifica a imagem (usada apenas para largura/altura neste early-return)
    try:
        image = decode_binary_image(image_bytes)
        img_h, img_w = int(image.shape[0]), int(image.shape[1])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao decodificar imagem: {e}"
        )

    # 🚀 EARLY RETURN (opcional) — se quiser reusar deltas/cores já salvos
    if fingerprint.core and fingerprint.deltas and isinstance(fingerprint.deltas, list) and len(fingerprint.deltas) > 0:
        try:
            delta_points = [
                DetectionPoint(x=int(d.get("x")), y=int(d.get("y")))
                for d in fingerprint.deltas
                if d is not None and "x" in d and "y" in d
            ]
    
            core_points: List[DetectionPoint] = []
            if (
                isinstance(fingerprint.core, dict)
                and "x" in fingerprint.core
                and "y" in fingerprint.core
            ):
                core_points.append(
                    DetectionPoint(
                        x=int(fingerprint.core.get("x")),
                        y=int(fingerprint.core.get("y")),
                    )
                )
    
            return DetectionResult(
                deltas=delta_points,
                cores=core_points,
                number_deltas=len(delta_points),
                ridge_counts=fingerprint.ridge_counts,
                pattern_type=fingerprint.pattern_type,
                image_width=img_w,
                image_height=img_h,
            )
        except Exception:
            pass

    try:
        detector = SimpleFingerprintDetector(image)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao inicializar detector: {e}"
        )

    try:
        deltas, cores = detector.detect(
            block_size=request.block_size, min_coherence=request.min_coherence
        )
        # print(len(cores))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro na detecção de singular points: {e}"
        )

    delta_points = (
        [DetectionPoint(x=int(round(d["x"])), y=int(round(d["y"]))) for d in deltas]
        if deltas
        else []
    )
    core_points = (
        [DetectionPoint(x=int(round(c["x"])), y=int(round(c["y"]))) for c in cores]
        if cores
        else []
    )

    n_deltas = len(delta_points)
    n_cores = len(core_points)

    tipo: Optional[str] = None

    # Caso típico de arco: nenhum core e 0 ou 1 delta perdido (ruído)
    if n_cores == 0 and n_deltas <= 1:
        tipo = "arch"
        # descarta possíveis pontos falsos
        delta_points = []
        core_points = []
        ridge_count_value: Optional[int] = 0
    else:
        # caso contrário, usa o detector de tipo normal
        try:
            tipo = detect_fingerprint_type(
                image_gray=image,
                detector=SimpleFingerprintDetector,
                hand=fingerprint.hand,
            )
        except Exception:
            tipo = None

        ridge_count_value: Optional[int] = None
        nearest_core: Optional[DetectionPoint] = None

        if len(delta_points) > 0 and len(core_points) > 0:
            d = delta_points[0]
            d_coords = np.array([d.x, d.y])
            cores_coords = np.array([[c.x, c.y] for c in core_points])
            dists = np.linalg.norm(cores_coords - d_coords, axis=1)
            nearest_idx = int(np.argmin(dists))
            nearest_core = core_points[nearest_idx]

            try:
                ridge_count_value = int(
                    count_ridges_between_minimal(
                        image_gray=image,
                        p1=(d.x, d.y),
                        p2=(nearest_core.x, nearest_core.y),
                        thickness=25,
                    )
                )
            except Exception:
                ridge_count_value = None

        # persiste no banco (sem quebrar a rota se falhar)
        try:
            fingerprint.pattern_type = tipo if tipo is not None else None
            fingerprint.ridge_counts = ridge_count_value

            if core_points:
                fingerprint.core = [{"x": int(p.x), "y": int(p.y)} for p in core_points]
            else:
                fingerprint.core = None

            if delta_points:
                fingerprint.deltas = [
                    {"x": int(p.x), "y": int(p.y)} for p in delta_points
                ]
            else:
                fingerprint.deltas = None

            db.add(fingerprint)
            db.commit()
            db.refresh(fingerprint)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao salvar resultados no banco: {e}",
            )

    return DetectionResult(
        deltas=delta_points,
        cores=core_points,
        ridge_counts=ridge_count_value,
        number_deltas=len(delta_points),
        pattern_type=tipo,
        image_width=img_w,
        image_height=img_h,
    )
