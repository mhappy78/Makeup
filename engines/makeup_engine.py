"""
메이크업 엔진 인터페이스 - MediaPipe 기반 향상된 구현
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import numpy as np
import cv2
import mediapipe as mp
import time
from models.core import Point3D, Color
from models.makeup import (
    MakeupConfig, LipstickConfig, EyeshadowConfig, 
    BlushConfig, FoundationConfig, EyelinerConfig,
    EyeshadowStyle, BlendMode
)

# MediaPipe 기반 정확한 얼굴 랜드마크 포인트 (reference files 기반)
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


class MakeupResult:
    """메이크업 적용 결과"""
    def __init__(self, image: np.ndarray, applied_effects: List[str], 
                 processing_time: float):
        self.image = image
        self.applied_effects = applied_effects
        self.processing_time = processing_time
    
    def is_successful(self) -> bool:
        """메이크업 적용이 성공했는지 확인"""
        return len(self.applied_effects) > 0 and self.image is not None


class ColorBlender:
    """색상 블렌딩 유틸리티 - Alpha, Multiply, Overlay 모드 지원"""
    
    @staticmethod
    def blend_colors(base_color: Color, overlay_color: Color, 
                    mode: BlendMode, opacity: float) -> Color:
        """두 색상을 지정된 모드로 블렌딩"""
        if opacity <= 0:
            return base_color
        if opacity >= 1 and mode == BlendMode.NORMAL:
            return overlay_color
        
        # 색상 값을 0-1 범위로 정규화
        base_r, base_g, base_b = base_color.r / 255.0, base_color.g / 255.0, base_color.b / 255.0
        overlay_r, overlay_g, overlay_b = overlay_color.r / 255.0, overlay_color.g / 255.0, overlay_color.b / 255.0
        
        if mode == BlendMode.NORMAL:
            # Alpha 블렌딩 (선형 보간)
            result_r = base_r * (1 - opacity) + overlay_r * opacity
            result_g = base_g * (1 - opacity) + overlay_g * opacity
            result_b = base_b * (1 - opacity) + overlay_b * opacity
            
        elif mode == BlendMode.MULTIPLY:
            # Multiply 블렌딩 - 어두운 효과
            mult_r = base_r * overlay_r
            mult_g = base_g * overlay_g
            mult_b = base_b * overlay_b
            
            result_r = base_r * (1 - opacity) + mult_r * opacity
            result_g = base_g * (1 - opacity) + mult_g * opacity
            result_b = base_b * (1 - opacity) + mult_b * opacity
            
        elif mode == BlendMode.OVERLAY:
            # Overlay 블렌딩 - 대비 강화
            def overlay_blend(base, overlay):
                if base < 0.5:
                    return 2 * base * overlay
                else:
                    return 1 - 2 * (1 - base) * (1 - overlay)
            
            overlay_r = overlay_blend(base_r, overlay_r)
            overlay_g = overlay_blend(base_g, overlay_g)
            overlay_b = overlay_blend(base_b, overlay_b)
            
            result_r = base_r * (1 - opacity) + overlay_r * opacity
            result_g = base_g * (1 - opacity) + overlay_g * opacity
            result_b = base_b * (1 - opacity) + overlay_b * opacity
            
        else:
            # 기본값으로 Normal 블렌딩 사용
            result_r = base_r * (1 - opacity) + overlay_r * opacity
            result_g = base_g * (1 - opacity) + overlay_g * opacity
            result_b = base_b * (1 - opacity) + overlay_b * opacity
        
        # 0-255 범위로 변환하고 클램핑
        r = max(0, min(255, int(result_r * 255)))
        g = max(0, min(255, int(result_g * 255)))
        b = max(0, min(255, int(result_b * 255)))
        a = base_color.a  # 알파 값은 베이스 색상 유지
        
        return Color(r, g, b, a)
    
    @staticmethod
    def match_skin_tone(makeup_color: Color, skin_tone: Color, harmony_factor: float = 0.3) -> Color:
        """메이크업 색상을 피부톤과 조화시키는 알고리즘"""
        if not 0.0 <= harmony_factor <= 1.0:
            harmony_factor = 0.3
        
        # 피부톤의 따뜻함/차가움 지수 계산 (더 정확한 공식)
        skin_warmth = (skin_tone.r - skin_tone.b) / max(1, skin_tone.g)  # 빨강-파랑 차이를 녹색으로 정규화
        
        # 따뜻한 피부톤이면 메이크업 색상도 따뜻하게 조정
        if skin_warmth > 0.1:  # 따뜻한 피부톤 (빨강이 파랑보다 많음)
            adjusted_r = min(255, int(makeup_color.r * (1 + harmony_factor * 0.2)))
            adjusted_g = makeup_color.g
            adjusted_b = max(0, int(makeup_color.b * (1 - harmony_factor * 0.2)))
        elif skin_warmth < -0.1:  # 차가운 피부톤 (파랑이 빨강보다 많음)
            adjusted_r = max(0, int(makeup_color.r * (1 - harmony_factor * 0.2)))
            adjusted_g = makeup_color.g
            adjusted_b = min(255, int(makeup_color.b * (1 + harmony_factor * 0.2)))
        else:  # 중성 피부톤
            adjusted_r = makeup_color.r
            adjusted_g = makeup_color.g
            adjusted_b = makeup_color.b
        
        return Color(adjusted_r, adjusted_g, adjusted_b, makeup_color.a)
    
    @staticmethod
    def adjust_intensity(color: Color, intensity: float) -> Color:
        """블렌딩 강도 조절 기능"""
        if not 0.0 <= intensity <= 1.0:
            intensity = max(0.0, min(1.0, intensity))
        
        # 강도에 따라 알파 값 조정
        adjusted_alpha = int(color.a * intensity)
        return Color(color.r, color.g, color.b, adjusted_alpha)


class MakeupEngine(ABC):
    """메이크업 엔진 기본 인터페이스"""
    
    @abstractmethod
    def apply_lipstick(self, image: np.ndarray, landmarks: List[Point3D], 
                      config: LipstickConfig) -> np.ndarray:
        pass
    
    @abstractmethod
    def apply_eyeshadow(self, image: np.ndarray, landmarks: List[Point3D],
                       config: EyeshadowConfig) -> np.ndarray:
        pass
    
    @abstractmethod
    def apply_blush(self, image: np.ndarray, landmarks: List[Point3D],
                   config: BlushConfig) -> np.ndarray:
        pass
    
    @abstractmethod
    def apply_foundation(self, image: np.ndarray, landmarks: List[Point3D],
                        config: FoundationConfig) -> np.ndarray:
        pass
    
    @abstractmethod
    def apply_eyeliner(self, image: np.ndarray, landmarks: List[Point3D],
                      config: EyelinerConfig) -> np.ndarray:
        pass
    
    @abstractmethod
    def apply_full_makeup(self, image: np.ndarray, landmarks: List[Point3D],
                         config: MakeupConfig) -> MakeupResult:
        pass
    
    def get_skin_tone(self, image: np.ndarray, landmarks: List[Point3D]) -> Color:
        """얼굴에서 피부톤 추출"""
        return Color(220, 180, 140)  # 기본 피부톤
    
    def validate_makeup_config(self, config: MakeupConfig) -> bool:
        """메이크업 설정 유효성 검증"""
        try:
            return (config.lipstick is not None and
                   config.eyeshadow is not None and
                   config.blush is not None and
                   config.foundation is not None and
                   config.eyeliner is not None)
        except Exception:
            return False


class RealtimeMakeupEngine(MakeupEngine):
    """실시간 메이크업 엔진 구현"""
    
    def __init__(self):
        self.color_blender = ColorBlender()
    
    def _get_lip_mask(self, image: np.ndarray, landmarks: List[Point3D]) -> np.ndarray:
        """입술 영역 정확한 마스킹 알고리즘"""
        import cv2
        
        # 입술 랜드마크 인덱스 (MediaPipe 기준)
        upper_lip_indices = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        lower_lip_indices = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]
        
        # 랜드마크가 충분하지 않은 경우 기본 마스크 생성
        if len(landmarks) < max(max(upper_lip_indices, default=0), max(lower_lip_indices, default=0)):
            h, w = image.shape[:2]
            center_x, center_y = w // 2, int(h * 0.75)
            lip_width, lip_height = w // 8, h // 20
            
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(mask, (center_x, center_y), (lip_width, lip_height), 0, 0, 360, 255, -1)
            return mask
        
        # 실제 랜드마크를 사용한 정확한 마스킹
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        # 상단 입술 포인트
        upper_points = []
        for idx in upper_lip_indices:
            if idx < len(landmarks):
                point = landmarks[idx]
                upper_points.append([int(point.x), int(point.y)])
        
        # 하단 입술 포인트
        lower_points = []
        for idx in lower_lip_indices:
            if idx < len(landmarks):
                point = landmarks[idx]
                lower_points.append([int(point.x), int(point.y)])
        
        # 입술 윤곽 그리기
        if upper_points:
            upper_points = np.array(upper_points, dtype=np.int32)
            cv2.fillPoly(mask, [upper_points], 255)
        
        if lower_points:
            lower_points = np.array(lower_points, dtype=np.int32)
            cv2.fillPoly(mask, [lower_points], 255)
        
        # 마스크 부드럽게 처리
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        
        return mask
    
    def _apply_gradient_effect(self, mask: np.ndarray, gradient_strength: float = 0.3) -> np.ndarray:
        """입술 윤곽 및 그라데이션 효과 구현"""
        import cv2
        
        # 거리 변환을 사용한 그라데이션 생성
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        
        # 정규화
        if dist_transform.max() > 0:
            dist_transform = dist_transform / dist_transform.max()
        
        # 그라데이션 강도 적용
        gradient_mask = mask.astype(np.float32) / 255.0
        gradient_mask = gradient_mask * (1 - gradient_strength) + dist_transform * gradient_strength
        
        return np.clip(gradient_mask * 255, 0, 255).astype(np.uint8)
    
    def apply_lipstick(self, image: np.ndarray, landmarks: List[Point3D], 
                      config: LipstickConfig) -> np.ndarray:
        """자연스러운 립스틱 색상 적용 메서드"""
        try:
            if image is None or len(image.shape) != 3:
                return image
            
            # 입술 마스크 생성
            lip_mask = self._get_lip_mask(image, landmarks)
            
            # 그라데이션 효과 적용
            if config.glossiness > 0.5:
                lip_mask = self._apply_gradient_effect(lip_mask, config.glossiness * 0.3)
            
            # 피부톤과 조화시킨 립스틱 색상 계산
            skin_tone = self.get_skin_tone(image, landmarks)
            adjusted_color = ColorBlender.match_skin_tone(config.color, skin_tone, 0.2)
            final_color = ColorBlender.adjust_intensity(adjusted_color, config.intensity)
            
            # 립스틱 적용
            result_image = image.copy()
            mask_indices = np.where(lip_mask > 0)
            
            if len(mask_indices[0]) > 0:
                for y, x in zip(mask_indices[0], mask_indices[1]):
                    if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
                        original_pixel = Color(
                            int(image[y, x, 2]),  # BGR to RGB
                            int(image[y, x, 1]), 
                            int(image[y, x, 0]),
                            255
                        )
                        
                        mask_strength = lip_mask[y, x] / 255.0
                        blend_opacity = config.intensity * mask_strength
                        
                        blended_color = ColorBlender.blend_colors(
                            original_pixel, final_color, config.blend_mode, blend_opacity
                        )
                        
                        result_image[y, x, 2] = blended_color.r
                        result_image[y, x, 1] = blended_color.g
                        result_image[y, x, 0] = blended_color.b
            
            return result_image
            
        except Exception as e:
            print(f"립스틱 적용 중 오류 발생: {e}")
            return image
    
    def _get_eye_mask(self, image: np.ndarray, landmarks: List[Point3D], eye_side: str = "both") -> np.ndarray:
        """눈꺼풀 영역 감지 및 매핑 알고리즘"""
        import cv2
        
        left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        max_required_idx = max(max(left_eye_indices, default=0), max(right_eye_indices, default=0))
        if len(landmarks) < max_required_idx:
            h, w = image.shape[:2]
            
            if eye_side in ["left", "both"]:
                left_center_x, left_center_y = int(w * 0.35), int(h * 0.4)
                eye_width, eye_height = w // 12, h // 15
                cv2.ellipse(mask, (left_center_x, left_center_y), (eye_width, eye_height), 0, 0, 360, 255, -1)
            
            if eye_side in ["right", "both"]:
                right_center_x, right_center_y = int(w * 0.65), int(h * 0.4)
                eye_width, eye_height = w // 12, h // 15
                cv2.ellipse(mask, (right_center_x, right_center_y), (eye_width, eye_height), 0, 0, 360, 255, -1)
            
            return mask
        
        # 실제 랜드마크를 사용한 정확한 마스킹
        if eye_side in ["left", "both"]:
            left_points = []
            for idx in left_eye_indices:
                if idx < len(landmarks):
                    point = landmarks[idx]
                    left_points.append([int(point.x), int(point.y)])
            
            if left_points:
                left_points = np.array(left_points, dtype=np.int32)
                cv2.fillPoly(mask, [left_points], 255)
        
        if eye_side in ["right", "both"]:
            right_points = []
            for idx in right_eye_indices:
                if idx < len(landmarks):
                    point = landmarks[idx]
                    right_points.append([int(point.x), int(point.y)])
            
            if right_points:
                right_points = np.array(right_points, dtype=np.int32)
                cv2.fillPoly(mask, [right_points], 255)
        
        # 마스크 확장 및 부드럽게 처리
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return mask
    
    def _apply_eyeshadow_gradient(self, mask: np.ndarray, colors: List[Color], style: EyeshadowStyle) -> Dict[str, np.ndarray]:
        """다중 색상 아이섀도 블렌딩 기능"""
        import cv2
        
        gradient_masks = {}
        
        if style == EyeshadowStyle.NATURAL:
            gradient_masks['base'] = mask
            
        elif style == EyeshadowStyle.GRADIENT:
            h, w = mask.shape
            gradient = np.zeros_like(mask, dtype=np.float32)
            
            mask_coords = np.where(mask > 0)
            if len(mask_coords[0]) > 0:
                min_y, max_y = np.min(mask_coords[0]), np.max(mask_coords[0])
                for y, x in zip(mask_coords[0], mask_coords[1]):
                    intensity = 1.0 - (y - min_y) / max(1, max_y - min_y)
                    gradient[y, x] = intensity
            
            for i, color in enumerate(colors[:2]):
                layer_mask = mask.copy().astype(np.float32) / 255.0
                if i == 0:
                    layer_mask *= 0.8
                else:
                    layer_mask *= gradient * 0.6
                
                gradient_masks[f'color_{i}'] = (layer_mask * 255).astype(np.uint8)
                
        elif style == EyeshadowStyle.SMOKY:
            dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
            if dist_transform.max() > 0:
                dist_transform = dist_transform / dist_transform.max()
            
            smoky_mask = mask.astype(np.float32) / 255.0
            smoky_mask *= (1.0 - dist_transform * 0.7)
            gradient_masks['smoky'] = (smoky_mask * 255).astype(np.uint8)
            
        else:
            gradient_masks['base'] = mask
        
        return gradient_masks
    
    def apply_eyeshadow(self, image: np.ndarray, landmarks: List[Point3D],
                       config: EyeshadowConfig) -> np.ndarray:
        """아이섀도 적용 메서드"""
        try:
            if image is None or len(image.shape) != 3:
                return image
            
            if not config.colors:
                return image
            
            eye_mask = self._get_eye_mask(image, landmarks, "both")
            gradient_masks = self._apply_eyeshadow_gradient(eye_mask, config.colors, config.style)
            skin_tone = self.get_skin_tone(image, landmarks)
            
            result_image = image.copy()
            
            for i, (layer_name, layer_mask) in enumerate(gradient_masks.items()):
                if i >= len(config.colors):
                    break
                
                color = config.colors[i]
                adjusted_color = ColorBlender.match_skin_tone(color, skin_tone, 0.15)
                final_color = ColorBlender.adjust_intensity(adjusted_color, config.intensity)
                
                if config.shimmer > 0:
                    shimmer_r = min(255, int(final_color.r * (1 + config.shimmer * 0.3)))
                    shimmer_g = min(255, int(final_color.g * (1 + config.shimmer * 0.3)))
                    shimmer_b = min(255, int(final_color.b * (1 + config.shimmer * 0.3)))
                    final_color = Color(shimmer_r, shimmer_g, shimmer_b, final_color.a)
                
                mask_indices = np.where(layer_mask > 0)
                if len(mask_indices[0]) > 0:
                    for y, x in zip(mask_indices[0], mask_indices[1]):
                        if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
                            original_pixel = Color(
                                int(result_image[y, x, 2]),
                                int(result_image[y, x, 1]), 
                                int(result_image[y, x, 0]),
                                255
                            )
                            
                            mask_strength = layer_mask[y, x] / 255.0
                            blend_opacity = config.intensity * mask_strength * 0.6
                            
                            blended_color = ColorBlender.blend_colors(
                                original_pixel, final_color, config.blend_mode, blend_opacity
                            )
                            
                            result_image[y, x, 2] = blended_color.r
                            result_image[y, x, 1] = blended_color.g
                            result_image[y, x, 0] = blended_color.b
            
            return result_image
            
        except Exception as e:
            print(f"아이섀도 적용 중 오류 발생: {e}")
            return image
    
    def _get_cheek_mask(self, image: np.ndarray, landmarks: List[Point3D], placement: str = "cheeks") -> np.ndarray:
        """볼 영역 자동 감지 및 마스킹"""
        import cv2
        
        left_cheek_indices = [116, 117, 118, 119, 120, 121, 126, 142, 36, 205, 206, 207, 213, 192, 147, 187]
        right_cheek_indices = [345, 346, 347, 348, 349, 350, 355, 371, 266, 425, 426, 427, 436, 416, 376, 411]
        
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        max_required_idx = max(max(left_cheek_indices, default=0), max(right_cheek_indices, default=0))
        if len(landmarks) < max_required_idx:
            h, w = image.shape[:2]
            
            if placement in ["cheeks", "temples"]:
                left_center_x, left_center_y = int(w * 0.25), int(h * 0.55)
                cheek_width, cheek_height = w // 10, h // 12
                cv2.ellipse(mask, (left_center_x, left_center_y), (cheek_width, cheek_height), 0, 0, 360, 255, -1)
                
                right_center_x, right_center_y = int(w * 0.75), int(h * 0.55)
                cv2.ellipse(mask, (right_center_x, right_center_y), (cheek_width, cheek_height), 0, 0, 360, 255, -1)
            
            elif placement == "nose":
                nose_center_x, nose_center_y = int(w * 0.5), int(h * 0.55)
                nose_width, nose_height = w // 15, h // 10
                cv2.ellipse(mask, (nose_center_x, nose_center_y), (nose_width, nose_height), 0, 0, 360, 255, -1)
            
            return mask
        
        if placement in ["cheeks", "temples"]:
            left_points = []
            for idx in left_cheek_indices:
                if idx < len(landmarks):
                    point = landmarks[idx]
                    left_points.append([int(point.x), int(point.y)])
            
            right_points = []
            for idx in right_cheek_indices:
                if idx < len(landmarks):
                    point = landmarks[idx]
                    right_points.append([int(point.x), int(point.y)])
            
            if left_points:
                left_center = np.mean(left_points, axis=0).astype(int)
                cv2.circle(mask, tuple(left_center), 30, 255, -1)
            
            if right_points:
                right_center = np.mean(right_points, axis=0).astype(int)
                cv2.circle(mask, tuple(right_center), 30, 255, -1)
        
        elif placement == "nose":
            h, w = image.shape[:2]
            nose_center_x, nose_center_y = int(w * 0.5), int(h * 0.55)
            nose_width, nose_height = w // 15, h // 10
            cv2.ellipse(mask, (nose_center_x, nose_center_y), (nose_width, nose_height), 0, 0, 360, 255, -1)
        
        # 마스크 부드럽게 처리
        if placement == "nose":
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
        else:
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        return mask
    
    def apply_blush(self, image: np.ndarray, landmarks: List[Point3D],
                   config: BlushConfig) -> np.ndarray:
        """블러셔 적용 메서드"""
        try:
            if image is None or len(image.shape) != 3:
                return image
            
            cheek_mask = self._get_cheek_mask(image, landmarks, config.placement)
            skin_tone = self.get_skin_tone(image, landmarks)
            adjusted_color = ColorBlender.match_skin_tone(config.color, skin_tone, 0.25)
            final_color = ColorBlender.adjust_intensity(adjusted_color, config.intensity)
            
            result_image = image.copy()
            mask_indices = np.where(cheek_mask > 0)
            
            if len(mask_indices[0]) > 0:
                for y, x in zip(mask_indices[0], mask_indices[1]):
                    if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
                        original_pixel = Color(
                            int(image[y, x, 2]),
                            int(image[y, x, 1]), 
                            int(image[y, x, 0]),
                            255
                        )
                        
                        mask_strength = cheek_mask[y, x] / 255.0
                        blend_opacity = config.intensity * mask_strength * 0.4
                        
                        blended_color = ColorBlender.blend_colors(
                            original_pixel, final_color, config.blend_mode, blend_opacity
                        )
                        
                        result_image[y, x, 2] = blended_color.r
                        result_image[y, x, 1] = blended_color.g
                        result_image[y, x, 0] = blended_color.b
            
            return result_image
            
        except Exception as e:
            print(f"블러셔 적용 중 오류 발생: {e}")
            return image
    
    def _get_face_mask(self, image: np.ndarray, landmarks: List[Point3D]) -> np.ndarray:
        """전체 얼굴 영역 마스크 생성"""
        import cv2
        
        face_outline_indices = [
            10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
            397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
            172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109
        ]
        
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        if len(landmarks) < max(face_outline_indices, default=0):
            h, w = image.shape[:2]
            center_x, center_y = w // 2, int(h * 0.5)
            face_width, face_height = int(w * 0.35), int(h * 0.45)
            cv2.ellipse(mask, (center_x, center_y), (face_width, face_height), 0, 0, 360, 255, -1)
            return mask
        
        face_points = []
        for idx in face_outline_indices:
            if idx < len(landmarks):
                point = landmarks[idx]
                face_points.append([int(point.x), int(point.y)])
        
        if face_points:
            face_points = np.array(face_points, dtype=np.int32)
            cv2.fillPoly(mask, [face_points], 255)
        
        # 눈과 입 영역 제외
        eye_mask = self._get_eye_mask(image, landmarks, "both")
        lip_mask = self._get_lip_mask(image, landmarks)
        
        mask = cv2.subtract(mask, eye_mask)
        mask = cv2.subtract(mask, lip_mask)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return mask
    
    def _apply_matte_finish(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """매트 마무리 효과"""
        result = image.copy()
        mask_indices = np.where(mask > 0)
        
        if len(mask_indices[0]) > 0:
            for y, x in zip(mask_indices[0], mask_indices[1]):
                if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
                    mask_strength = mask[y, x] / 255.0 * 0.2
                    
                    for c in range(3):
                        original_val = image[y, x, c]
                        reduced_val = max(0, int(original_val * 0.95))
                        result[y, x, c] = int(original_val * (1 - mask_strength) + reduced_val * mask_strength)
        
        return result
    
    def _apply_dewy_finish(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Dewy finish effect"""
        result = image.copy()
        mask_indices = np.where(mask > 0)
        
        if len(mask_indices[0]) > 0:
            for y, x in zip(mask_indices[0], mask_indices[1]):
                if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
                    mask_strength = mask[y, x] / 255.0 * 0.15
                    
                    for c in range(3):
                        original_val = image[y, x, c]
                        brightened_val = min(255, int(original_val * 1.1))
                        result[y, x, c] = int(original_val * (1 - mask_strength) + brightened_val * mask_strength)
        
        return result
    
    def _apply_skin_smoothing(self, image: np.ndarray, mask: np.ndarray, smoothing_strength: float) -> np.ndarray:
        """자연스러운 경계 블러링 기능"""
        import cv2
        
        if smoothing_strength <= 0:
            return image
        
        kernel_size = max(3, int(smoothing_strength * 15))
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        result = image.copy()
        mask_indices = np.where(mask > 0)
        
        if len(mask_indices[0]) > 0:
            for y, x in zip(mask_indices[0], mask_indices[1]):
                if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
                    mask_strength = mask[y, x] / 255.0 * smoothing_strength
                    
                    for c in range(3):
                        original_val = image[y, x, c]
                        blurred_val = blurred[y, x, c]
                        result[y, x, c] = int(original_val * (1 - mask_strength) + blurred_val * mask_strength)
        
        return result
    
    def apply_foundation(self, image: np.ndarray, landmarks: List[Point3D],
                        config: FoundationConfig) -> np.ndarray:
        """전체 얼굴 파운데이션 적용 알고리즘"""
        try:
            if image is None or len(image.shape) != 3:
                return image
            
            face_mask = self._get_face_mask(image, landmarks)
            result_image = self._apply_skin_smoothing(image, face_mask, config.coverage * 0.5)
            
            if config.coverage > 0.1:
                current_skin_tone = self.get_skin_tone(image, landmarks)
                foundation_color = config.color
                
                mask_indices = np.where(face_mask > 0)
                if len(mask_indices[0]) > 0:
                    for y, x in zip(mask_indices[0], mask_indices[1]):
                        if 0 <= y < result_image.shape[0] and 0 <= x < result_image.shape[1]:
                            original_pixel = Color(
                                int(result_image[y, x, 2]),
                                int(result_image[y, x, 1]), 
                                int(result_image[y, x, 0]),
                                255
                            )
                            
                            mask_strength = face_mask[y, x] / 255.0
                            blend_opacity = config.coverage * mask_strength * 0.3
                            
                            blended_color = ColorBlender.blend_colors(
                                original_pixel, foundation_color, BlendMode.NORMAL, blend_opacity
                            )
                            
                            result_image[y, x, 2] = blended_color.r
                            result_image[y, x, 1] = blended_color.g
                            result_image[y, x, 0] = blended_color.b
            
            # 마무리 효과 적용
            if config.finish == "matte":
                result_image = self._apply_matte_finish(result_image, face_mask)
            elif config.finish == "dewy":
                result_image = self._apply_dewy_finish(result_image, face_mask)
            
            return result_image
            
        except Exception as e:
            print(f"파운데이션 적용 중 오류 발생: {e}")
            return image
    
    def apply_eyeliner(self, image: np.ndarray, landmarks: List[Point3D],
                      config: EyelinerConfig) -> np.ndarray:
        """아이라이너 적용 메서드 - 향후 구현 예정"""
        return image
    
    def apply_full_makeup(self, image: np.ndarray, landmarks: List[Point3D],
                         config: MakeupConfig) -> MakeupResult:
        """전체 메이크업 적용 메서드"""
        start_time = time.time()
        applied_effects = []
        result_image = image.copy()
        
        try:
            # 파운데이션 먼저 적용
            if config.foundation:
                result_image = self.apply_foundation(result_image, landmarks, config.foundation)
                applied_effects.append("foundation")
            
            # 블러셔 적용
            if config.blush:
                result_image = self.apply_blush(result_image, landmarks, config.blush)
                applied_effects.append("blush")
            
            # 아이섀도 적용
            if config.eyeshadow:
                result_image = self.apply_eyeshadow(result_image, landmarks, config.eyeshadow)
                applied_effects.append("eyeshadow")
            
            # 아이라이너 적용
            if config.eyeliner:
                result_image = self.apply_eyeliner(result_image, landmarks, config.eyeliner)
                applied_effects.append("eyeliner")
            
            # 립스틱 마지막에 적용
            if config.lipstick:
                result_image = self.apply_lipstick(result_image, landmarks, config.lipstick)
                applied_effects.append("lipstick")
            
            processing_time = time.time() - start_time
            
            return MakeupResult(
                image=result_image,
                applied_effects=applied_effects,
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"전체 메이크업 적용 중 오류 발생: {e}")
            processing_time = time.time() - start_time
            return MakeupResult(
                image=image,
                applied_effects=[],
                processing_time=processing_time
            )
    
    def get_skin_tone(self, image: np.ndarray, landmarks: List[Point3D]) -> Color:
        """얼굴에서 피부톤 추출"""
        try:
            h, w = image.shape[:2]
            
            sample_regions = [
                (int(w * 0.4), int(h * 0.4), int(w * 0.6), int(h * 0.6)),
                (int(w * 0.3), int(h * 0.5), int(w * 0.4), int(h * 0.6)),
                (int(w * 0.6), int(h * 0.5), int(w * 0.7), int(h * 0.6)),
            ]
            
            if landmarks and len(landmarks) > 50:
                forehead_points = landmarks[10:15] if len(landmarks) > 15 else []
                if forehead_points:
                    forehead_x = int(np.mean([p.x for p in forehead_points]))
                    forehead_y = int(np.mean([p.y for p in forehead_points])) - 20
                    sample_regions.append((
                        max(0, forehead_x - 15), max(0, forehead_y - 15),
                        min(w, forehead_x + 15), min(h, forehead_y + 15)
                    ))
            
            color_samples = []
            for x1, y1, x2, y2 in sample_regions:
                if 0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h:
                    region = image[y1:y2, x1:x2]
                    if region.size > 0:
                        mean_color = np.mean(region.reshape(-1, 3), axis=0)
                        color_samples.append(mean_color)
            
            if color_samples:
                avg_color = np.mean(color_samples, axis=0)
                return Color(
                    int(avg_color[2]),  # BGR to RGB
                    int(avg_color[1]),
                    int(avg_color[0]),
                    255
                )
            else:
                return Color(220, 180, 140, 255)
                
        except Exception as e:
            print(f"피부톤 추출 중 오류 발생: {e}")
            return Color(220, 180, 140, 255)