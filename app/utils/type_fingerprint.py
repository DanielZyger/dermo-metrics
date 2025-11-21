from typing import List, Dict, Optional, Tuple

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
    """
    Tenta inferir de que lado a presilha está:
      - "left"  → mais à esquerda da digital
      - "right" → mais à direita da digital
    Usa a média das coordenadas x de deltas+cores em relação ao centro.
    """
    import numpy as np  # type: ignore

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
    hand: Optional[str] = None,   # <--- NOVO: "left" ou "right"
) -> Tuple[str, Dict[str, int]]:

    import numpy as np  # type: ignore

    if (deltas is None or cores is None):
        if detector is None:
            raise ValueError("Forneça 'deltas' e 'cores', ou um 'detector' com método detect().")
        if image_gray is None:
            raise ValueError("Quando usando 'detector', passe também 'image_gray'.")

        det_obj = detector
        try:
            if callable(detector) and not hasattr(detector, "detect"):
                det_obj = detector(image_gray)

            if not hasattr(det_obj, "detect"):
                raise ValueError("Detector passado não possui método 'detect(block_size, min_coherence)'.")

            deltas_detected, cores_detected = det_obj.detect(
                block_size=block_size,
                min_coherence=min_coherence
            )
            deltas = deltas_detected or []
            cores = cores_detected or []
        except Exception as e:
            raise RuntimeError(f"Falha ao executar detector: {e}") from e

    # garantir listas
    deltas = deltas or []
    cores = cores or []

    # 1) tipo base (sem mão)
    tipo_base = type_from_points(deltas=deltas, cores=cores)

    # 2) por padrão, resultado é o tipo base
    tipo_final = tipo_base

    # 3) se for loop e tiver mão, refina para ulnar/radial
    if tipo_base == "loop" and hand is not None:
        hand_value = str(hand).lower()  # funciona com enums também

        loop_side = _infer_loop_side(deltas=deltas, cores=cores, image_gray=image_gray)
        # loop_side: "left" ou "right"

        if hand_value in ("left", "left_hand", "esquerda", "mao_esquerda"):
            # mão esquerda
            if loop_side == "left":
                tipo_final = "ulnar_loop"
            else:
                tipo_final = "radial_loop"

        elif hand_value in ("right", "right_hand", "direita", "mao_direita"):
            # mão direita
            if loop_side == "right":
                tipo_final = "ulnar_loop"
            else:
                tipo_final = "radial_loop"
        else:
            # mão desconhecida → mantém genérico "loop"
            tipo_final = "loop"

    meta = {"n_deltas": len(deltas), "n_cores": len(cores)}
    return tipo_final, meta
