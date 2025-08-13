"""
향상된 메이크업 엔진 - MediaPipe 기반 정확한 랜드마크 사용
Reference files의 기술을 완전히 적용한 고품질 메이크업 구현
- 정확한 MediaPipe 랜드마크 매핑
- 향상된 마스킹 및 블렌딩 알고리즘
- 자연스러운 색상 적용 및 부드러운 전환
"""
import numpy as np
import cv2
import mediapipe as mp
from typing import Dict, List, Tuple, Optional
import sys
import os

# 모델 임포트 (선택적)
try:
    from models.core import Point3D, Color
    from models.makeup import (
        MakeupConfig, LipstickConfig, EyeshadowConfig, 
        BlushConfig, FoundationConfig, EyelinerConfig,
        EyeshadowStyle, BlendMode
    )
except ImportError:
    # 모델이 없는 경우 기본 타입 사용
    Point3D = Tuple[float, float, float]
    Color = Tuple[int, int, int]

# MediaPipe 기반 정확한 얼굴 랜드마크 포인트 (reference files에서 가져옴)
FACE_LANDMARKS = {
    "BLUSH_LEFT": [50],
    "BLUSH_RIGHT": [280],
    "LEFT_EYE": [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7, 33],
    "RIGHT_EYE": [362, 298, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382, 362],
    "EYELINER_LEFT": [243, 112, 26, 22, 23, 24, 110, 25, 226, 130, 33, 7, 163, 144, 145, 153, 154, 155, 133, 243],
    "EYELINER_RIGHT": [463, 362, 382, 381, 380, 374, 373, 390, 249, 263, 359, 446, 255, 339, 254, 253, 252, 256, 341, 463],
    "EYESHADOW_LEFT": [226, 247, 30, 29, 27, 28, 56, 190, 243, 173, 157, 158, 159, 160, 161, 246, 33, 130, 226],
    "EYESHADOW_RIGHT": [463, 414, 286, 258, 257, 259, 260, 467, 446, 359, 263, 466, 388, 387, 386, 385, 384, 398, 362, 463],
    "FACE": [152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10, 338, 297, 332, 284, 251, 389, 454, 323, 401, 361, 435, 288, 397, 365, 379, 378, 400, 377, 152],
    "LIP_UPPER": [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 308, 415, 310, 312, 13, 82, 81, 80, 191, 78],
    "LIP_LOWER": [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 402, 317, 14, 87, 178, 88, 95, 78, 61],
    "EYEBROW_LEFT": [55, 107, 66, 105, 63, 70, 46, 53, 52, 65, 55],
    "EYEBROW_RIGHT": [285, 336, 296, 334, 293, 300, 276, 283, 295, 285]
}

# MediaPipe 초기화
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils


class EnhancedMakeupEngine:
    """향상된 메이크업 엔진 - reference files 기반 구현"""
    
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
    
    def read_landmarks(self, image: np.ndarray) -> Dict[int, Tuple[int, int]]:
        """
        MediaPipe를 사용하여 얼굴 랜드마크 추출
        reference files의 read_landmarks 함수와 완전히 동일한 구현
        """
        landmark_cordinates = {}
        
        # MediaPipe facemesh 로드 및 얼굴 랜드마크 감지
        # 얼굴 랜드마크는 0부터 477까지의 정규화된 포인트를 반환
        with mp_face_mesh.FaceMesh(refine_landmarks=True) as face_mesh:
            results = face_mesh.process(image)
            
            # 얼굴 랜드마크가 감지되었는지 확인
            if results.multi_face_landmarks is None or len(results.multi_face_landmarks) == 0:
                print("No face detected in the image.")
                return landmark_cordinates
                
            face_landmarks = results.multi_face_landmarks[0].landmark

        # 정규화된 포인트를 이미지 차원에 맞게 변환
        for idx, landmark in enumerate(face_landmarks):
            landmark_px = mp_drawing._normalized_to_pixel_coordinates(
                landmark.x, landmark.y, image.shape[1], image.shape[0]
            )
            # 얼굴 랜드마크와 (x,y) 좌표의 맵 생성
            if landmark_px:
                landmark_cordinates[idx] = landmark_px
        return landmark_cordinates
    
    def add_mask(self, mask: np.ndarray, idx_to_coordinates: Dict[int, Tuple[int, int]], 
                 face_connections: List[List[int]], colors: List[List[int]]) -> np.ndarray:
        """
        reference files의 add_mask 함수와 동일한 구현
        얼굴 특징에 대한 마스크 생성
        """
        # 랜드마크가 감지되지 않은 경우
        if not idx_to_coordinates:
            print("No facial landmarks detected. Returning empty mask.")
            return mask
        
        for i, connection in enumerate(face_connections):
            # 모든 필요한 랜드마크가 사용 가능한지 확인
            if all(idx in idx_to_coordinates for idx in connection):
                points = np.array([idx_to_coordinates[idx] for idx in connection])
                # 마스크에 특징 모양 생성 및 색상 추가
                cv2.fillPoly(mask, [points], colors[i])
        
        # 이미지 부드럽게 처리
        mask = cv2.GaussianBlur(mask, (7, 7), 4)
        return mask
    
    def add_enhanced_mask(self, mask: np.ndarray, idx_to_coordinates: Dict[int, Tuple[int, int]], 
                         face_connections: List[List[int]], colors_map: Dict[str, List[int]], 
                         intensity_map: Dict[str, float], face_elements: List[str], 
                         blur_strength: int, blur_sigma: int) -> np.ndarray:
        """
        reference files의 add_enhanced_mask 함수와 동일한 구현
        강화된 마스크 생성 함수
        """
        if not idx_to_coordinates:
            return mask
        
        for i, (connection, element) in enumerate(zip(face_connections, face_elements)):
            if all(idx in idx_to_coordinates for idx in connection):
                points = np.array([idx_to_coordinates[idx] for idx in connection])
                
                # 개별 부위별 마스크 생성
                temp_mask = np.zeros_like(mask)
                color = colors_map[element]
                cv2.fillPoly(temp_mask, [points], color)
                
                # 블러 적용
                temp_mask = cv2.GaussianBlur(temp_mask, (blur_strength, blur_strength), blur_sigma)
                
                # 부위별 강도 적용
                intensity = intensity_map[element]
                temp_mask = (temp_mask * intensity).astype(np.uint8)
                
                # 마스크에 추가
                mask = cv2.add(mask, temp_mask)
        
        return mask
    
    def draw_landmarks(self, image: np.ndarray, landmarks: Dict[int, Tuple[int, int]], 
                      color: Tuple[int, int, int] = (0, 255, 0), radius: int = 2) -> np.ndarray:
        """
        reference files의 draw_landmarks 함수와 동일한 구현
        얼굴 랜드마크를 이미지에 그리기
        """
        result = image.copy()
        for idx, point in landmarks.items():
            cv2.circle(result, point, radius, color, -1)
        return result
    
    def apply_makeup(self, image: np.ndarray, colors_map: Dict[str, List[int]], 
                    intensity_map: Dict[str, float], mask_alpha: float, 
                    blur_strength: int, blur_sigma: int, show_landmarks: bool = False) -> Tuple[np.ndarray, np.ndarray, bool]:
        """
        reference files의 apply_makeup 함수와 동일한 구현
        메이크업을 적용하는 함수
        """
        # 얼굴 부위 설정
        face_elements = [
            "LIP_LOWER", "LIP_UPPER",
            "EYEBROW_LEFT", "EYEBROW_RIGHT",
            "EYELINER_LEFT", "EYELINER_RIGHT",
            "EYESHADOW_LEFT", "EYESHADOW_RIGHT",
        ]
        
        # 얼굴 연결점 추출
        face_connections = [FACE_LANDMARKS[idx] for idx in face_elements]
        
        # 빈 마스크 생성
        mask = np.zeros_like(image)
        
        # 얼굴 랜드마크 추출
        face_landmarks = self.read_landmarks(image=image)
        
        # 향상된 마스크 생성
        mask = self.add_enhanced_mask(
            mask, face_landmarks, face_connections, 
            colors_map, intensity_map, face_elements,
            blur_strength, blur_sigma
        )
        
        # 이미지와 마스크 결합
        output = cv2.addWeighted(image, 1.0, mask, mask_alpha, 1.0)
        
        # 랜드마크 표시
        if show_landmarks and face_landmarks:
            output = self.draw_landmarks(output, face_landmarks)
        
        return output, mask, len(face_landmarks) > 0
    
    def apply_simple_makeup(self, image_path: str, colors_map: Optional[Dict[str, List[int]]] = None) -> np.ndarray:
        """
        reference files의 main 함수와 동일한 구현
        간단한 메이크업 적용
        """
        # 기본 색상 맵 (reference files와 동일)
        if colors_map is None:
            colors_map = {
                # 상하 입술
                "LIP_UPPER": [0, 0, 255],  # Red in BGR
                "LIP_LOWER": [0, 0, 255],  # Red in BGR
                # 아이라이너
                "EYELINER_LEFT": [139, 0, 0],  # Dark Blue in BGR
                "EYELINER_RIGHT": [139, 0, 0],  # Dark Blue in BGR
                # 아이섀도
                "EYESHADOW_LEFT": [0, 100, 0],  # Dark Green in BGR
                "EYESHADOW_RIGHT": [0, 100, 0],  # Dark Green in BGR
                # 눈썹
                "EYEBROW_LEFT": [19, 69, 139],  # Dark Brown in BGR
                "EYEBROW_RIGHT": [19, 69, 139],  # Dark Brown in BGR
            }
        
        # 적용할 얼굴 특징 추출
        face_elements = [
            "LIP_LOWER", "LIP_UPPER",
            "EYEBROW_LEFT", "EYEBROW_RIGHT",
            "EYELINER_LEFT", "EYELINER_RIGHT",
            "EYESHADOW_LEFT", "EYESHADOW_RIGHT",
        ]
        
        # 얼굴 연결점과 색상 추출
        face_connections = [FACE_LANDMARKS[idx] for idx in face_elements]
        colors = [colors_map[idx] for idx in face_elements]
        
        # 이미지 읽기
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
        else:
            image = image_path
        
        if image is None:
            raise ValueError("이미지를 로드할 수 없습니다.")
        
        # 빈 마스크 생성
        mask = np.zeros_like(image)
        
        # 얼굴 랜드마크 추출
        face_landmarks = self.read_landmarks(image=image)
        
        # 얼굴 특징에 대한 마스크 생성
        mask = self.add_mask(
            mask,
            idx_to_coordinates=face_landmarks,
            face_connections=face_connections,
            colors=colors
        )
        
        # 이미지와 마스크를 가중치에 따라 결합
        output = cv2.addWeighted(image, 1.0, mask, 0.2, 1.0)
        
        return output
    
    def show_image(self, image: np.ndarray, msg: str = "Loaded Image"):
        """
        reference files의 show_image 함수와 동일한 구현
        cv2 창에 이미지 표시
        """
        image_copy = image.copy()
        cv2.imshow(msg, image_copy)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def get_available_landmarks(self) -> Dict[str, List[int]]:
        """사용 가능한 랜드마크 포인트 반환"""
        return FACE_LANDMARKS.copy()
    
    def validate_image(self, image: np.ndarray) -> bool:
        """이미지 유효성 검증"""
        if image is None:
            return False
        if len(image.shape) != 3:
            return False
        if image.shape[2] != 3:
            return False
        return True
    
    def __del__(self):
        """소멸자 - MediaPipe 리소스 정리"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()


# 편의 함수들 (reference files와 호환성을 위해)
def create_enhanced_makeup_engine() -> EnhancedMakeupEngine:
    """향상된 메이크업 엔진 인스턴스 생성"""
    return EnhancedMakeupEngine()


def apply_makeup_to_image(image_path: str, output_path: Optional[str] = None, 
                         colors_map: Optional[Dict[str, List[int]]] = None) -> np.ndarray:
    """이미지에 메이크업 적용하는 편의 함수"""
    engine = EnhancedMakeupEngine()
    result = engine.apply_simple_makeup(image_path, colors_map)
    
    if output_path:
        cv2.imwrite(output_path, result)
    
    return result


def get_default_colors() -> Dict[str, List[int]]:
    """기본 메이크업 색상 반환"""
    return {
        "LIP_UPPER": [0, 0, 255],  # Red in BGR
        "LIP_LOWER": [0, 0, 255],  # Red in BGR
        "EYELINER_LEFT": [139, 0, 0],  # Dark Blue in BGR
        "EYELINER_RIGHT": [139, 0, 0],  # Dark Blue in BGR
        "EYESHADOW_LEFT": [0, 100, 0],  # Dark Green in BGR
        "EYESHADOW_RIGHT": [0, 100, 0],  # Dark Green in BGR
        "EYEBROW_LEFT": [19, 69, 139],  # Dark Brown in BGR
        "EYEBROW_RIGHT": [19, 69, 139],  # Dark Brown in BGR
    }