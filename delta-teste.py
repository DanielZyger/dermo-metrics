import cv2
import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt

class SimpleFingerprintDetector:
    def __init__(self, image_path):
        """Inicializa o detector com a imagem da impressão digital."""
        self.image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if self.image is None:
            raise ValueError("Não foi possível carregar a imagem")
        
        self.height, self.width = self.image.shape
        print(f"Imagem carregada: {self.width}x{self.height}")
    
    def compute_gradients(self):
        """Calcula os gradientes da imagem usando Sobel."""
        self.gx = cv2.Sobel(self.image, cv2.CV_64F, 1, 0, ksize=3)
        self.gy = cv2.Sobel(self.image, cv2.CV_64F, 0, 1, ksize=3)
        print("✓ Gradientes calculados")
    
    def compute_orientation_field(self, block_size=16):
        """
        Calcula o campo de orientação das cristas.
        Retorna: orientation (matriz com ângulos), coherence (confiabilidade)
        """
        h, w = self.image.shape
        blocks_h = h // block_size
        blocks_w = w // block_size
        
        orientation = np.zeros((blocks_h, blocks_w))
        coherence = np.zeros((blocks_h, blocks_w))
        
        for i in range(blocks_h):
            for j in range(blocks_w):
                # Região do bloco
                y_start = i * block_size
                x_start = j * block_size
                y_end = y_start + block_size
                x_end = x_start + block_size
                
                # Gradientes no bloco
                gx_block = self.gx[y_start:y_end, x_start:x_end]
                gy_block = self.gy[y_start:y_end, x_start:x_end]
                
                # Tensor de estrutura
                Gxx = np.sum(gx_block * gx_block)
                Gyy = np.sum(gy_block * gy_block)
                Gxy = np.sum(gx_block * gy_block)
                
                # Orientação (ângulo dominante)
                orientation[i, j] = 0.5 * np.arctan2(2 * Gxy, Gxx - Gyy)
                
                # Coerência (confiabilidade da orientação)
                coherence[i, j] = np.sqrt((Gxx - Gyy)**2 + 4*Gxy**2) / (Gxx + Gyy + 1e-10)
        
        print(f"✓ Campo de orientação calculado ({blocks_h}x{blocks_w} blocos)")
        return orientation, coherence, block_size
    
    def smooth_orientation(self, orientation, sigma=1.5):
        """Suaviza o campo de orientação para reduzir ruído."""
        # Converte para componentes sin/cos para evitar problemas com ângulos
        sin_ori = np.sin(2 * orientation)
        cos_ori = np.cos(2 * orientation)
        
        # Suaviza separadamente
        sin_smooth = ndimage.gaussian_filter(sin_ori, sigma)
        cos_smooth = ndimage.gaussian_filter(cos_ori, sigma)
        
        # Reconverte para ângulo
        orientation_smooth = 0.5 * np.arctan2(sin_smooth, cos_smooth)
        
        print("✓ Orientação suavizada")
        return orientation_smooth
    
    def compute_poincare_index(self, orientation, coherence, min_coherence=0.5):
        """
        Calcula o Índice de Poincaré para detectar pontos singulares.
        
        Delta: índice ≈ -0.5 (triângulo)
        Core: índice ≈ +0.5 (círculo)
        """
        h, w = orientation.shape
        poincare = np.zeros((h, w))
        
        for i in range(1, h - 1):
            for j in range(1, w - 1):
                # Ignora regiões de baixa coerência
                if coherence[i, j] < min_coherence:
                    continue
                
                # 8 vizinhos ao redor (sentido horário)
                neighbors = [
                    orientation[i-1, j],      # Norte
                    orientation[i-1, j+1],    # Nordeste
                    orientation[i, j+1],      # Leste
                    orientation[i+1, j+1],    # Sudeste
                    orientation[i+1, j],      # Sul
                    orientation[i+1, j-1],    # Sudoeste
                    orientation[i, j-1],      # Oeste
                    orientation[i-1, j-1]     # Noroeste
                ]
                
                # Soma as diferenças angulares
                angle_sum = 0
                for k in range(8):
                    diff = neighbors[(k+1) % 8] - neighbors[k]
                    
                    # Normaliza diferença para [-π/2, π/2]
                    while diff > np.pi/2:
                        diff -= np.pi
                    while diff < -np.pi/2:
                        diff += np.pi
                    
                    angle_sum += diff
                
                # Índice de Poincaré
                poincare[i, j] = angle_sum / (2 * np.pi)
        
        print(f"✓ Índice de Poincaré calculado")
        return poincare
    
    def refine_position(self, poincare, i, j, search_type='delta', radius=2):
        """
        Refina a posição do ponto singular buscando o pico real na vizinhança.
        
        Args:
            poincare: Mapa do índice de Poincaré
            i, j: Posição inicial
            search_type: 'delta' ou 'core'
            radius: Raio de busca
        
        Returns:
            (refined_i, refined_j): Posição refinada
        """
        h, w = poincare.shape
        
        # Define região de busca
        i_min = max(0, i - radius)
        i_max = min(h, i + radius + 1)
        j_min = max(0, j - radius)
        j_max = min(w, j + radius + 1)
        
        region = poincare[i_min:i_max, j_min:j_max]
        
        if search_type == 'delta':
            # Para delta, busca o MÍNIMO (valor mais negativo)
            local_min_idx = np.unravel_index(np.argmin(region), region.shape)
            refined_i = i_min + local_min_idx[0]
            refined_j = j_min + local_min_idx[1]
        else:  # core
            # Para core, busca o MÁXIMO (valor mais positivo)
            local_max_idx = np.unravel_index(np.argmax(region), region.shape)
            refined_i = i_min + local_max_idx[0]
            refined_j = j_min + local_max_idx[1]
        
        return refined_i, refined_j
    
    def find_singular_points(self, poincare, coherence, block_size):
        """
        Identifica deltas e cores baseado no índice de Poincaré.
        
        Parâmetros MAIS RESTRITIVOS para evitar falsos positivos.
        """
        h, w = poincare.shape
        
        deltas = []
        cores = []
        
        # Parâmetros de detecção mais estritos
        DELTA_MIN, DELTA_MAX = -0.55, -0.45     # Range mais estreito para delta
        CORE_MIN, CORE_MAX = 0.45, 0.55         # Range mais estreito para core
        MIN_COHERENCE_DELTA = 0.65              # Coerência mínima para delta
        MIN_COHERENCE_CORE = 0.75               # Coerência ALTA para core (evita falsos positivos)
        MARGIN = 4                              # Margem maior das bordas
        LOCAL_THRESHOLD = 0.98                  # Deve ser 98% do máximo local
        
        for i in range(MARGIN, h - MARGIN):
            for j in range(MARGIN, w - MARGIN):
                pi_value = poincare[i, j]
                coh_value = coherence[i, j]
                
                # Detecta DELTA (índice negativo)
                if DELTA_MIN < pi_value < DELTA_MAX:
                    # Verifica coerência específica para delta
                    if coh_value < MIN_COHERENCE_DELTA:
                        continue
                    
                    # Verifica se é máximo local FORTE (em valor absoluto)
                    local_region = np.abs(poincare[i-2:i+3, j-2:j+3])
                    if np.abs(pi_value) >= np.max(local_region) * LOCAL_THRESHOLD:
                        # Validação adicional: verifica coerência média na vizinhança
                        local_coherence = coherence[i-2:i+3, j-2:j+3]
                        avg_coherence = np.mean(local_coherence)
                        
                        if avg_coherence >= 0.55:  # Região deve ter boa coerência geral
                            # Refina a posição do delta analisando o pico local
                            refined_i, refined_j = self.refine_position(
                                poincare, i, j, search_type='delta'
                            )
                            
                            # Converte para coordenadas da imagem original
                            y = refined_i * block_size + block_size // 2
                            x = refined_j * block_size + block_size // 2
                            deltas.append({
                                'x': x, 'y': y,
                                'index': pi_value,
                                'coherence': coh_value,
                                'avg_coherence': avg_coherence
                            })
                
                # Detecta CORE (índice positivo) - FILTRO MUITO MAIS RIGOROSO
                elif CORE_MIN < pi_value < CORE_MAX:
                    # Coerência ALTA obrigatória para core
                    if coh_value < MIN_COHERENCE_CORE:
                        continue
                    
                    # Verifica se é máximo local MUITO FORTE
                    local_region = poincare[i-2:i+3, j-2:j+3]
                    if pi_value >= np.max(local_region) * LOCAL_THRESHOLD:
                        # Validação RIGOROSA: coerência média ALTA na vizinhança
                        local_coherence = coherence[i-2:i+3, j-2:j+3]
                        avg_coherence = np.mean(local_coherence)
                        
                        # Core precisa de coerência geral MUITO alta
                        if avg_coherence >= 0.70:
                            # Validação extra: verifica se há picos de coerência consistentes
                            high_coherence_count = np.sum(local_coherence > 0.65)
                            
                            # Pelo menos 15 dos 25 blocos vizinhos devem ter alta coerência
                            if high_coherence_count >= 15:
                                # Refina a posição do core analisando o pico local
                                refined_i, refined_j = self.refine_position(
                                    poincare, i, j, search_type='core'
                                )
                                
                                # Converte para coordenadas da imagem original
                                y = refined_i * block_size + block_size // 2
                                x = refined_j * block_size + block_size // 2
                                cores.append({
                                    'x': x, 'y': y,
                                    'index': pi_value,
                                    'coherence': coh_value,
                                    'avg_coherence': avg_coherence,
                                    'high_coh_count': high_coherence_count
                                })
        
        print(f"✓ Pontos encontrados: {len(deltas)} deltas, {len(cores)} cores")
        return deltas, cores
    
    def remove_duplicates(self, points, min_distance=50):
        """Remove pontos duplicados muito próximos."""
        if len(points) == 0:
            return []
        
        # Ordena por qualidade (índice * coerência)
        points_sorted = sorted(points, 
                              key=lambda p: abs(p['index']) * p['coherence'], 
                              reverse=True)
        
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
        """
        Executa a detecção completa de delta e core.
        """
        print("\n" + "="*60)
        print("INICIANDO DETECÇÃO DE PONTOS SINGULARES")
        print("="*60 + "\n")
        
        # 1. Calcula gradientes
        self.compute_gradients()
        
        # 2. Campo de orientação
        orientation, coherence, bs = self.compute_orientation_field(block_size)
        
        # 3. Suaviza orientação
        orientation = self.smooth_orientation(orientation)
        
        # 4. Índice de Poincaré
        poincare = self.compute_poincare_index(orientation, coherence, min_coherence)
        
        # 5. Encontra pontos singulares
        deltas, cores = self.find_singular_points(poincare, coherence, bs)
        
        # 6. Remove duplicatas
        deltas = self.remove_duplicates(deltas, min_distance=50)
        cores = self.remove_duplicates(cores, min_distance=50)
        
        print("\n" + "="*60)
        print("RESULTADOS FINAIS")
        print("="*60)
        print(f"\n🔺 DELTAS: {len(deltas)}")
        for i, d in enumerate(deltas, 1):
            print(f"   Delta {i}: ({d['x']}, {d['y']}) | "
                  f"Índice: {d['index']:.3f} | "
                  f"Coerência: {d['coherence']:.3f} | "
                  f"Média Local: {d['avg_coherence']:.3f}")
        
        print(f"\n🔵 CORES: {len(cores)}")
        for i, c in enumerate(cores, 1):
            print(f"   Core {i}: ({c['x']}, {c['y']}) | "
                  f"Índice: {c['index']:.3f} | "
                  f"Coerência: {c['coherence']:.3f} | "
                  f"Média Local: {c['avg_coherence']:.3f} | "
                  f"Blocos Alta Coh: {c['high_coh_count']}/25")
        print()
        
        return deltas, cores, orientation, coherence, poincare, bs
    
    def visualize(self, deltas, cores, orientation, coherence, poincare, block_size):
        """Visualiza os resultados da detecção."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 14))
        
        # 1. Imagem original com detecções
        result = cv2.cvtColor(self.image, cv2.COLOR_GRAY2BGR)

        # for delta in deltas:
        #     # Desenha triângulo vermelho SEMI-TRANSPARENTE para delta
        #     x, y = delta['x'], delta['y']
        #     pts = np.array([[x, y-25], [x-22, y+15], [x+22, y+15]], np.int32)
            
        #     # Cria uma camada temporária para aplicar transparência
        #     overlay = result.copy()
        #     cv2.fillPoly(overlay, [pts], (0, 0, 255))
            
        #     # Aplica transparência (alpha=0.4 = 40% opaco, 60% transparente)
        #     alpha = 0.4
        #     cv2.addWeighted(overlay, alpha, result, 1 - alpha, 0, result)
            
        #     # Desenha a borda do triângulo (opaca) para melhor visibilidade
        #     cv2.polylines(result, [pts], True, (0, 0, 255), 3)
            
        #     cv2.putText(result, 'DELTA', (x-30, y-35),
        #                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        for delta in deltas:
            # Desenha triângulo vermelho para delta
            x, y = delta['x'], delta['y']
            pts = np.array([[x, y-25], [x-22, y+15], [x+22, y+15]], np.int32)
            overlay = result.copy()
            alpha = 0.6
            cv2.fillPoly(result, [pts], (0, 0, 255))
            cv2.addWeighted(overlay, alpha, result, 1 - alpha, 0, result)
            cv2.polylines(result, [pts], True, (0, 0, 255), 3)
            cv2.putText(result, 'DELTA', (x-30, y-35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        for core in cores:
            # Desenha círculo azul para core
            x, y = core['x'], core['y']
            cv2.circle(result, (x, y), 25, (255, 0, 0), 3)
            cv2.circle(result, (x, y), 5, (255, 0, 0), -1)
            cv2.putText(result, 'CORE', (x-25, y-35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        axes[0, 0].imshow(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
        axes[0, 0].set_title('Detecção Final', fontsize=14, fontweight='bold')
        axes[0, 0].axis('off')
        
        # 2. Campo de orientação
        h, w = orientation.shape
        y, x = np.mgrid[0:h, 0:w]
        u = np.cos(orientation)
        v = np.sin(orientation)
        
        axes[0, 1].imshow(self.image, cmap='gray', alpha=0.6)
        axes[0, 1].quiver(x[::2, ::2], y[::2, ::2], 
                         u[::2, ::2], v[::2, ::2],
                         color='red', scale=25, width=0.004)
        axes[0, 1].set_title('Campo de Orientação', fontsize=14, fontweight='bold')
        axes[0, 1].axis('off')
        
        # 3. Mapa de coerência
        im1 = axes[1, 0].imshow(coherence, cmap='jet')
        axes[1, 0].set_title('Coerência', fontsize=14, fontweight='bold')
        axes[1, 0].axis('off')
        plt.colorbar(im1, ax=axes[1, 0], fraction=0.046)
        
        # 4. Índice de Poincaré
        im2 = axes[1, 1].imshow(poincare, cmap='RdBu_r', vmin=-1, vmax=1)
        axes[1, 1].set_title('Índice de Poincaré', fontsize=14, fontweight='bold')
        axes[1, 1].axis('off')
        plt.colorbar(im2, ax=axes[1, 1], fraction=0.046)
        
        plt.tight_layout()
        return result, fig


if __name__ == "__main__":
    image_path = 'assets/images/deltaandcore.png'
    
    try:
        # Cria o detector
        detector = SimpleFingerprintDetector(image_path)
        
        # Executa a detecção
        deltas, cores, orientation, coherence, poincare, block_size = detector.detect(
            block_size=16,          # Tamanho dos blocos para análise
            min_coherence=0.5       # Coerência mínima para considerar
        )
        
        # Visualiza resultados
        result_img, fig = detector.visualize(deltas, cores, orientation, 
                                            coherence, poincare, block_size)
        
        # Salva resultado
        cv2.imwrite('resultadobemfiltrado.png', result_img)
        print("✓ Resultado salvo em 'resultadobemfiltrado.png'\n")
        
        plt.show()
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()



# 🔍 Filtros Usados - Explicação Simples
# 1. Filtro Sobel (Gradientes)

# O que faz: Detecta mudanças bruscas na imagem (bordas das cristas)
# Por quê: Precisa saber onde as linhas estão e em que direção vão


# 2. Campo de Orientação

# O que faz: Calcula a direção das cristas em cada região (ex: 45°, 90°, etc)
# Por quê: Delta e Core são definidos por como as direções "giram"


# 3. Filtro Gaussiano (Suavização)

# O que faz: Suaviza o mapa de direções, eliminando variações abruptas
# Por quê: Remove ruído e deixa as direções mais consistentes


# 4. Índice de Poincaré ⭐ (Principal)

# O que faz: Analisa como as direções "rodam" ao redor de um ponto

# Se giram +180° = CORE (círculo)
# Se giram -180° = DELTA (triângulo)


# Por quê: É a matemática que define o que é um delta ou core


# 5. Mapa de Coerência

# O que faz: Mede a "confiança" - se as cristas estão bem definidas
# Por quê: Filtra regiões borradas/ruidosas que poderiam dar falsos positivos


# 6. Máximo Local + Refinamento

# O que faz: Garante que o ponto detectado é o "mais forte" na região
# Por quê: Evita marcar múltiplos pontos próximos para o mesmo delta/core


# 🎯 Resumão :
# Detecta onde as linhas estão (Sobel) →
#  Calcula suas direções (Orientação) →
#  Suaviza (Gaussiano) →
#  Identifica onde fazem círculos/triângulos (Poincaré) →
#  Filtra os fracos (Coerência) →
#  Centraliza (Refinamento)