from typing import List, Dict, Optional, Tuple
import numpy as np 

FINGERPRINT_TYPES = (
    "arch",
    "loop",
    "ulnar_loop",
    "radial_loop",
    "whorl",
    "double_whorl",
)

from typing import List, Dict, Optional, Tuple

def type_from_points(
    deltas: Optional[List[Dict[str, int]]],
    cores: Optional[List[Dict[str, int]]]
) -> str:
    n_cores = len(cores) if cores else 0
    n_deltas = len(deltas) if deltas else 0

    # regras principais (formato geométrico)
    if n_cores >= 2:
        return "double_whorl"
    if n_cores == 1:
        if n_deltas >= 2:
            return "whorl"
        # um core normalmente sugere presilha (loop)
        return "loop"
    # n_cores == 0
    if n_deltas == 0:
        return "arch"
    # n_deltas >= 2
    return "whorl"

def _infer_loop_side(
    deltas: List[Dict[str, int]],
    cores: List[Dict[str, int]],
    image_gray: Optional["np.ndarray"] = None,
) -> str:
   
    xs: List[int] = [d["x"] for d in deltas] + [c["x"] for c in cores]
    if not xs:
        # fallback arbitrário se não tiver nada
        return "left"

    x_mean = float(np.mean(xs))

    if image_gray is not None:
        width = image_gray.shape[1]
        center = width / 2.0
    else:
        # se não tiver imagem, usa centro do bounding box dos pontos
        center = (float(max(xs)) + float(min(xs))) / 2.0

    return "left" if x_mean < center else "right"

def detect_fingerprint_type(
    *,
    image_gray: Optional["np.ndarray"] = None,
    deltas: Optional[List[Dict[str, int]]] = None,
    cores: Optional[List[Dict[str, int]]] = None,
    detector=None,
    block_size: int = 16,
    min_coherence: float = 0.5,
    hand: Optional[str] = None,
) -> Tuple[str, Dict[str, int]]:
    import numpy as np  # type: ignore

    # 1) Se não recebemos deltas/cores, usamos o detector
    if (deltas is None or cores is None):
        if detector is None:
            raise ValueError(
                "Forneça 'deltas' e 'cores', ou um 'detector' com método detect()."
            )
        if image_gray is None:
            raise ValueError("Quando usando 'detector', passe também 'image_gray'.")

        try:
            # detector pode ser classe ou instância
            if isinstance(detector, type):
                det_obj = detector(image_gray)  # classe → instancia
            else:
                det_obj = detector               # instância já criada

            if not hasattr(det_obj, "detect"):
                raise ValueError(
                    "Detector passado não possui método 'detect(block_size, min_coherence)'."
                )

            deltas_detected, cores_detected = det_obj.detect(
                block_size=block_size,
                min_coherence=min_coherence,
            )

            # No seu caso, deltas_detected / cores_detected são listas de dicts
            deltas = deltas_detected or []
            cores = cores_detected or []
        except Exception as e:
            raise RuntimeError(f"Falha ao executar detector: {e}") from e

    # 2) garante listas
    deltas = deltas or []
    cores = cores or []

    # 3) tipo base (sem mão)
    tipo_base = type_from_points(deltas=deltas, cores=cores)
    tipo_final = tipo_base

    # 4) refino para ulnar/radial se for loop e hand informado
    if tipo_base == "loop" and hand is not None:
        hand_value = str(hand).lower()
        loop_side = _infer_loop_side(deltas=deltas, cores=cores, image_gray=image_gray)

        if hand_value in ("left", "left_hand", "esquerda", "mao_esquerda"):
            tipo_final = "radial_loop" if loop_side == "left" else "ulnar_loop"
        elif hand_value in ("right", "right_hand", "direita", "mao_direita"):
            tipo_final = "radial_loop" if loop_side == "right" else "ulnar_loop"
        else:
            tipo_final = "loop"

    meta = {"n_deltas": len(deltas), "n_cores": len(cores)}
    return tipo_final, meta
