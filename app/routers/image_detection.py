import base64
import io
import cv2
import numpy as np
from scipy import ndimage
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.models.fingerprint import Fingerprint
from sqlalchemy.orm import Session
from enum import Enum
from app.db import get_db

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
    image_width: int = 700
    image_height: int = 700


class DetectionRequest(BaseModel):
    fingerprint_id: int
    image_type: ImageTypeEnum
    block_size: int = 16
    min_coherence: float = 0.5


class SimpleFingerprintDetector:
    def __init__(self, image_array):
        self.image = image_array
        if self.image is None or self.image.size == 0:
            raise ValueError("Imagem inválida")
        
        self.height, self.width = self.image.shape
    
    def compute_gradients(self):
        self.gx = cv2.Sobel(self.image, cv2.CV_64F, 1, 0, ksize=3)
        self.gy = cv2.Sobel(self.image, cv2.CV_64F, 0, 1, ksize=3)
    
    def compute_orientation_field(self, block_size=16):
        h, w = self.image.shape
        blocks_h = h // block_size
        blocks_w = w // block_size
        
        orientation = np.zeros((blocks_h, blocks_w))
        coherence = np.zeros((blocks_h, blocks_w))
        
        for i in range(blocks_h):
            for j in range(blocks_w):
                y_start = i * block_size
                x_start = j * block_size
                y_end = y_start + block_size
                x_end = x_start + block_size
                
                gx_block = self.gx[y_start:y_end, x_start:x_end]
                gy_block = self.gy[y_start:y_end, x_start:x_end]
                
                Gxx = np.sum(gx_block * gx_block)
                Gyy = np.sum(gy_block * gy_block)
                Gxy = np.sum(gx_block * gy_block)
                
                orientation[i, j] = 0.5 * np.arctan2(2 * Gxy, Gxx - Gyy)
                coherence[i, j] = np.sqrt((Gxx - Gyy)**2 + 4*Gxy**2) / (Gxx + Gyy + 1e-10)
        
        return orientation, coherence, block_size
    
    def smooth_orientation(self, orientation, sigma=1.5):
        sin_ori = np.sin(2 * orientation)
        cos_ori = np.cos(2 * orientation)
        
        sin_smooth = ndimage.gaussian_filter(sin_ori, sigma)
        cos_smooth = ndimage.gaussian_filter(cos_ori, sigma)
        
        orientation_smooth = 0.5 * np.arctan2(sin_smooth, cos_smooth)
        return orientation_smooth
    
    def compute_poincare_index(self, orientation, coherence, min_coherence=0.5):
        h, w = orientation.shape
        poincare = np.zeros((h, w))
        
        for i in range(1, h - 1):
            for j in range(1, w - 1):
                if coherence[i, j] < min_coherence:
                    continue
                
                neighbors = [
                    orientation[i-1, j],
                    orientation[i-1, j+1],
                    orientation[i, j+1],
                    orientation[i+1, j+1],
                    orientation[i+1, j],
                    orientation[i+1, j-1],
                    orientation[i, j-1],
                    orientation[i-1, j-1]
                ]
                
                angle_sum = 0
                for k in range(8):
                    diff = neighbors[(k+1) % 8] - neighbors[k]
                    
                    while diff > np.pi/2:
                        diff -= np.pi
                    while diff < -np.pi/2:
                        diff += np.pi
                    
                    angle_sum += diff
                
                poincare[i, j] = angle_sum / (2 * np.pi)
        
        return poincare
    
    def refine_position(self, poincare, i, j, search_type='delta', radius=2):
        h, w = poincare.shape
        
        i_min = max(0, i - radius)
        i_max = min(h, i + radius + 1)
        j_min = max(0, j - radius)
        j_max = min(w, j + radius + 1)
        
        region = poincare[i_min:i_max, j_min:j_max]
        
        if search_type == 'delta':
            local_min_idx = np.unravel_index(np.argmin(region), region.shape)
            refined_i = i_min + local_min_idx[0]
            refined_j = j_min + local_min_idx[1]
        else:
            local_max_idx = np.unravel_index(np.argmax(region), region.shape)
            refined_i = i_min + local_max_idx[0]
            refined_j = j_min + local_max_idx[1]
        
        return refined_i, refined_j
    
    def find_singular_points(self, poincare, coherence, block_size):
        h, w = poincare.shape
        
        deltas = []
        cores = []
        
        DELTA_MIN, DELTA_MAX = -0.55, -0.45
        CORE_MIN, CORE_MAX = 0.45, 0.55
        MIN_COHERENCE_DELTA = 0.65
        MIN_COHERENCE_CORE = 0.75
        MARGIN = 4
        LOCAL_THRESHOLD = 0.98
        
        for i in range(MARGIN, h - MARGIN):
            for j in range(MARGIN, w - MARGIN):
                pi_value = poincare[i, j]
                coh_value = coherence[i, j]
                
                if DELTA_MIN < pi_value < DELTA_MAX:
                    if coh_value < MIN_COHERENCE_DELTA:
                        continue
                    
                    local_region = np.abs(poincare[i-2:i+3, j-2:j+3])
                    if np.abs(pi_value) >= np.max(local_region) * LOCAL_THRESHOLD:
                        local_coherence = coherence[i-2:i+3, j-2:j+3]
                        avg_coherence = np.mean(local_coherence)
                        
                        if avg_coherence >= 0.55:
                            refined_i, refined_j = self.refine_position(
                                poincare, i, j, search_type='delta'
                            )
                            
                            y = refined_i * block_size + block_size // 2
                            x = refined_j * block_size + block_size // 2
                            deltas.append({
                                'x': int(x), 
                                'y': int(y),
                                'index': float(pi_value),
                                'coherence': float(coh_value),
                                'avg_coherence': float(avg_coherence)
                            })
                
                elif CORE_MIN < pi_value < CORE_MAX:
                    if coh_value < MIN_COHERENCE_CORE:
                        continue
                    
                    local_region = poincare[i-2:i+3, j-2:j+3]
                    if pi_value >= np.max(local_region) * LOCAL_THRESHOLD:
                        local_coherence = coherence[i-2:i+3, j-2:j+3]
                        avg_coherence = np.mean(local_coherence)
                        
                        if avg_coherence >= 0.70:
                            high_coherence_count = np.sum(local_coherence > 0.65)
                            
                            if high_coherence_count >= 15:
                                refined_i, refined_j = self.refine_position(
                                    poincare, i, j, search_type='core'
                                )
                                
                                y = refined_i * block_size + block_size // 2
                                x = refined_j * block_size + block_size // 2
                                cores.append({
                                    'x': int(x), 
                                    'y': int(y),
                                    'index': float(pi_value),
                                    'coherence': float(coh_value),
                                    'avg_coherence': float(avg_coherence)
                                })
        
        return deltas, cores
    
    def remove_duplicates(self, points, min_distance=50):
        if len(points) == 0:
            return []
        
        if points and 'index' in points[0] and 'coherence' in points[0]:
            points_sorted = sorted(points, 
                                  key=lambda p: abs(p['index']) * p['coherence'], 
                                  reverse=True)
        elif points and 'coherence' in points[0]:
            points_sorted = sorted(points, 
                                  key=lambda p: p['coherence'], 
                                  reverse=True)
        else:
            points_sorted = points
        
        filtered = []
        for point in points_sorted:
            is_duplicate = False
            for existing in filtered:
                dist = np.sqrt((point['x'] - existing['x'])**2 + 
                              (point['y'] - existing['y'])**2)
                if dist < min_distance:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(point)
        
        return filtered
    
    def detect(self, block_size=16, min_coherence=0.5):
        self.compute_gradients()
        orientation, coherence, bs = self.compute_orientation_field(block_size)
        orientation = self.smooth_orientation(orientation)
        poincare = self.compute_poincare_index(orientation, coherence, min_coherence)
        deltas, cores = self.find_singular_points(poincare, coherence, bs)
        deltas = self.remove_duplicates(deltas, min_distance=50)
        cores = self.remove_duplicates(cores, min_distance=50)
        
        return deltas, cores


def decode_binary_image(image_bytes: bytes) -> np.ndarray:
    """Decodifica bytes de imagem para array numpy (escala de cinza)."""
    try:
        # Converte bytes para array numpy
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decodifica a imagem
        image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            raise ValueError("Falha ao decodificar a imagem")
        
        return image
    
    except Exception as e:
        raise ValueError(f"Erro ao processar imagem: {str(e)}")


@router.post("/detect-singular-points", response_model=DetectionResult)
async def detect_singular_points(
    request: DetectionRequest,
    db: Session = Depends(get_db)
):
    try:
        fingerprint = db.query(Fingerprint).filter(
            Fingerprint.id == request.fingerprint_id
        ).first()
        
        if not fingerprint:
            raise HTTPException(
                status_code=404,
                detail=f"Fingerprint com ID {request.fingerprint_id} não encontrada"
            )
        
        if request.image_type == ImageTypeEnum.raw:
            image_bytes = fingerprint.image_data
            if not image_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="A fingerprint não possui imagem raw (image_data)"
                )
        else:
            image_bytes = fingerprint.image_filtered
            if not image_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="A fingerprint não possui imagem filtered (image_filtered)"
                )
        
        image = decode_binary_image(image_bytes)
        detector = SimpleFingerprintDetector(image)
        
        deltas, cores = detector.detect(
            block_size=request.block_size,
            min_coherence=request.min_coherence
        )
        
        delta_points = [DetectionPoint(x=d['x'], y=d['y']) for d in deltas]
        core_points = [DetectionPoint(x=c['x'], y=c['y']) for c in cores]
        
        return DetectionResult(
            deltas=delta_points,
            cores=core_points
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar detecção: {str(e)}"
        )