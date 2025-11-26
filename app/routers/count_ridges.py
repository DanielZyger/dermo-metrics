import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.fingerprint import Fingerprint
from app.db import get_db
from app.utils.count_ridges import count_ridges_between_minimal
from typing import List
from pydantic import BaseModel

router = APIRouter()


class Point(BaseModel):
    x: float
    y: float


class CountRidgesRequest(BaseModel):
    fingerprint_id: int
    cores: List[Point]
    deltas: List[Point]


@router.post("/count-ridges")
async def count_ridges_endpoint(
    body: CountRidgesRequest,
    db: Session = Depends(get_db),
):
    # 1) Buscar fingerprint
    fingerprint: Fingerprint | None = (
        db.query(Fingerprint)
        .filter(Fingerprint.id == body.fingerprint_id)
        .first()
    )

    if fingerprint is None:
        raise HTTPException(status_code=404, detail="Fingerprint não encontrada.")

    if not getattr(fingerprint, "image_filtered", None):
        raise HTTPException(
            status_code=400,
            detail="Fingerprint não possui image_filtered.",
        )

    # 2) Decodificar image_filtered
    try:
        np_arr = np.frombuffer(fingerprint.image_filtered, np.uint8)
        img_gray = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
    except Exception:
        raise HTTPException(status_code=400, detail="Erro ao decodificar image_filtered.")

    if img_gray is None:
        raise HTTPException(status_code=400, detail="image_filtered inválida ou corrompida.")

    # 3) Usar body.cores e body.deltas DIRETAMENTE
    if not body.cores:
        raise HTTPException(status_code=400, detail="'cores' não pode ser vazio.")

    if not body.deltas:
        raise HTTPException(status_code=400, detail="'deltas' não pode ser vazio.")

    pair_count = min(len(body.cores), len(body.deltas))

    total_count = 0
    per_pair = []

    for idx in range(pair_count):
        core = body.cores[idx]
        delta = body.deltas[idx]

        x1, y1 = int(core.x), int(core.y)
        x2, y2 = int(delta.x), int(delta.y)

        p1 = (x1, y1)
        p2 = (x2, y2)

        try:
            count = count_ridges_between_minimal(
                img_gray,
                p1,
                p2,
                thickness=25,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar par {idx}: {e}",
            )

        total_count += count

        per_pair.append(
            {
                "index": idx,
                "core": {"x": x1, "y": y1},
                "delta": {"x": x2, "y": y2},
                "count": count,
            }
        )

    return {
        "fingerprint_id": body.fingerprint_id,
        "total_count": total_count,
        "pairs_used": pair_count,
        "per_pair": per_pair,
    }
