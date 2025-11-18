# app/utils/fingerprint_type.py
from typing import List, Dict, Optional, Tuple

# Resultado possível (português)
FINGERPRINT_TYPES = ("arch", "loop", "whorl", "double_whorl")

def type_from_points(
    deltas: Optional[List[Dict[str, int]]],
    cores: Optional[List[Dict[str, int]]]
) -> str:
    n_cores = len(cores) if cores else 0
    n_deltas = len(deltas) if deltas else 0

    # regras principais
    if n_cores >= 2:
        return "double_whorl"
    if n_cores == 1:
        if n_deltas >= 2:
            return "whorl"
        # um core normalmente sugere loop/loop
        return "loop"
    # n_cores == 0
    if n_deltas == 0:
        return "arch"
    # n_deltas >= 2
    return "whorl"


def detect_fingerprint_type(
    *,
    image_gray: Optional["np.ndarray"] = None,
    deltas: Optional[List[Dict[str, int]]] = None,
    cores: Optional[List[Dict[str, int]]] = None,
    detector=None,
    block_size: int = 16,
    min_coherence: float = 0.5
) -> Tuple[str, Dict[str, int]]:
    """
    Função de conveniência:
      - Se `deltas` e `cores` forem fornecidos, usa `type_from_points`.
      - Caso contrário, tenta usar `detector` (um objeto com método detect(block_size, min_coherence))
        para obter deltas e cores a partir de `image_gray`.
    Retorna (tipo_string, {'n_deltas': int, 'n_cores': int}).
    Exemplo de uso:
      detect_fingerprint_type(deltas=deltas_list, cores=cores_list)
      ou
      detect_fingerprint_type(image_gray=img, detector=SimpleFingerprintDetector())
    Observação: esta função NÃO implementa um detector interno completo — ela delega a detecção ao
    detector que você já tem (reaproveita SimpleFingerprintDetector do seu código).
    """
    # evita import pesado no topo (optional)
    import numpy as np  # type: ignore

    if (deltas is None or cores is None):
        if detector is None:
            raise ValueError("Forneça 'deltas' e 'cores', ou um 'detector' com método detect().")
        # detector deve ter método detect que retorna (deltas, cores)
        if image_gray is None:
            raise ValueError("Quando usando 'detector', passe também 'image_gray'.")
        # se o objeto detector for uma classe, instancie-o
        det_obj = detector
        try:
            # se passaram a classe em vez de instância, instanciar
            if callable(detector) and not hasattr(detector, "detect"):
                det_obj = detector(image_gray)
            elif hasattr(detector, "detect") and getattr(detector, "__call__", None):
                # detector já é uma instância ou functor; se for função que aceita imagem, chamamos:
                # preferir instância com detect()
                if not hasattr(detector, "detect"):
                    det_obj = detector(image_gray)
            # se det_obj tem detect, chamamos
            if not hasattr(det_obj, "detect"):
                raise ValueError("Detector passado não possui método 'detect(block_size, min_coherence)'.")
            deltas_detected, cores_detected = det_obj.detect(block_size=block_size, min_coherence=min_coherence)
            # det_obj.detect provavelmente retorna listas de dicts {'x':..., 'y':...}
            deltas = deltas_detected or []
            cores = cores_detected or []
        except Exception as e:
            raise RuntimeError(f"Falha ao executar detector: {e}") from e

    # garantir listas
    deltas = deltas or []
    cores = cores or []

    tipo = type_from_points(deltas=deltas, cores=cores)
    meta = {"n_deltas": len(deltas), "n_cores": len(cores)}
    return tipo, meta
