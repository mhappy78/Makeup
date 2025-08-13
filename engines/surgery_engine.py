"""
성형 시뮬레이션 엔진 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import numpy as np
from models.core import Point3D, Vector3D
from models.surgery import (
    SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig,
    FeatureModification, FeatureType
)


class SurgeryResult:
    """성형 시뮬레이션 결과"""
    def __init__(self, image: np.ndarray, modified_landmarks: List[Point3D],
                 applied_modifications: List[str], natural_score: float,
                 processing_time: float):
        self.image = image
        self.modified_landmarks = modified_landmarks
        self.applied_modifications = applied_modifications
        self.natural_score = natural_score  # 0.0 ~ 1.0
        self.processing_time = processing_time
    
    def is_natural(self, threshold: float = 0.7) -> bool:
        """자연스러운 결과인지 확인"""
        return self.natural_score >= threshold
    
    def is_successful(self) -> bool:
        """성형 시뮬레이션이 성공했는지 확인"""
        return (len(self.applied_modifications) > 0 and 
                self.image is not None and 
                len(self.modified_landmarks) > 0)


class ThinPlateSpline:
    """Thin Plate Spline 변형 알고리즘"""
    
    def __init__(self, source_points: np.ndarray, target_points: np.ndarray):
        """
        TPS 초기화
        
        Args:
            source_points: 원본 제어점 (N x 2)
            target_points: 목표 제어점 (N x 2)
        """
        self.source_points = source_points.astype(np.float64)
        self.target_points = target_points.astype(np.float64)
        self.n_points = len(source_points)
        
        # TPS 계수 계산
        self.weights = self._compute_weights()
    
    def _compute_weights(self) -> np.ndarray:
        """TPS 가중치 계산"""
        # 거리 행렬 계산
        K = self._compute_kernel_matrix()
        
        # P 행렬 (아핀 변환용)
        P = np.ones((self.n_points, 3))
        P[:, 1:] = self.source_points
        
        # L 행렬 구성
        L = np.zeros((self.n_points + 3, self.n_points + 3))
        L[:self.n_points, :self.n_points] = K
        L[:self.n_points, self.n_points:] = P
        L[self.n_points:, :self.n_points] = P.T
        
        # Y 벡터 (목표점 + 0 패딩)
        Y = np.zeros((self.n_points + 3, 2))
        Y[:self.n_points] = self.target_points
        
        # 선형 시스템 해결
        try:
            weights = np.linalg.solve(L, Y)
        except np.linalg.LinAlgError:
            # 특이 행렬인 경우 pseudo-inverse 사용
            weights = np.linalg.pinv(L) @ Y
        
        return weights
    
    def _compute_kernel_matrix(self) -> np.ndarray:
        """TPS 커널 행렬 계산"""
        K = np.zeros((self.n_points, self.n_points))
        
        for i in range(self.n_points):
            for j in range(self.n_points):
                if i != j:
                    r_sq = np.sum((self.source_points[i] - self.source_points[j]) ** 2)
                    if r_sq > 0:
                        K[i, j] = r_sq * np.log(r_sq)
        
        return K
    
    def transform_points(self, points: np.ndarray) -> np.ndarray:
        """점들을 TPS로 변형"""
        n_transform = len(points)
        transformed = np.zeros_like(points)
        
        for i in range(n_transform):
            # 아핀 변환 부분
            affine = self.weights[self.n_points:].T @ np.array([1, points[i, 0], points[i, 1]])
            
            # 비선형 변형 부분
            nonlinear = np.zeros(2)
            for j in range(self.n_points):
                r_sq = np.sum((points[i] - self.source_points[j]) ** 2)
                if r_sq > 0:
                    kernel_val = r_sq * np.log(r_sq)
                    nonlinear += self.weights[j] * kernel_val
            
            transformed[i] = affine + nonlinear
        
        return transformed


class MeshWarper:
    """메시 워핑 유틸리티 - Thin Plate Spline 기반"""
    
    def __init__(self):
        """메시 워퍼 초기화"""
        # MediaPipe 얼굴 랜드마크 인덱스 정의
        self.feature_indices = {
            FeatureType.NOSE: [
                # 코 윤곽
                1, 2, 5, 6, 19, 20, 94, 125, 141, 235, 236, 237, 238, 239, 240, 241, 242,
                # 콧구멍
                278, 279, 280, 281, 282, 294, 295, 296, 297, 298, 299, 300, 301, 302
            ],
            FeatureType.EYES: [
                # 왼쪽 눈
                33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246,
                # 오른쪽 눈  
                362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398
            ],
            FeatureType.JAWLINE: [
                # 턱선
                172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323
            ],
            FeatureType.CHEEKBONES: [
                # 광대
                116, 117, 118, 119, 120, 121, 126, 142, 36, 205, 206, 207, 213, 192, 147, 187,
                345, 346, 347, 348, 349, 350, 355, 371, 266, 425, 426, 427, 436, 416, 376, 411
            ]
        }
    
    def create_control_points(self, landmarks: List[Point3D], 
                            feature_type: FeatureType) -> List[Point3D]:
        """특정 특징에 대한 제어점 생성"""
        if feature_type not in self.feature_indices:
            return landmarks
        
        indices = self.feature_indices[feature_type]
        control_points = []
        
        for idx in indices:
            if idx < len(landmarks):
                control_points.append(landmarks[idx])
        
        return control_points
    
    def create_face_mesh(self, landmarks: List[Point3D], image_shape: tuple) -> np.ndarray:
        """얼굴 메시 생성"""
        height, width = image_shape[:2]
        
        # 랜드마크를 numpy 배열로 변환
        points = np.array([[p.x, p.y] for p in landmarks])
        
        # 이미지 경계점 추가 (변형 안정성을 위해)
        boundary_points = np.array([
            [0, 0], [width//2, 0], [width-1, 0],
            [0, height//2], [width-1, height//2],
            [0, height-1], [width//2, height-1], [width-1, height-1]
        ])
        
        # 전체 메시 포인트
        mesh_points = np.vstack([points, boundary_points])
        
        return mesh_points
    
    def apply_feature_modification(self, landmarks: List[Point3D], 
                                 modification: FeatureModification) -> List[Point3D]:
        """특징 변형 적용"""
        modified_landmarks = landmarks.copy()
        
        # 해당 특징의 제어점 가져오기
        control_indices = self.feature_indices.get(modification.feature_type, [])
        
        for idx in control_indices:
            if idx < len(modified_landmarks):
                original_point = modified_landmarks[idx]
                
                # 변형 벡터 적용
                new_x = original_point.x + modification.modification_vector.x * modification.intensity
                new_y = original_point.y + modification.modification_vector.y * modification.intensity
                new_z = original_point.z + modification.modification_vector.z * modification.intensity
                
                # 자연스러운 범위 내로 제한
                if modification.is_within_natural_limit():
                    modified_landmarks[idx] = Point3D(new_x, new_y, new_z)
        
        return modified_landmarks
    
    def warp_image_with_tps(self, image: np.ndarray, source_landmarks: List[Point3D],
                           target_landmarks: List[Point3D]) -> np.ndarray:
        """TPS를 사용한 이미지 워핑"""
        import cv2
        
        # 랜드마크를 numpy 배열로 변환
        source_points = np.array([[p.x, p.y] for p in source_landmarks])
        target_points = np.array([[p.x, p.y] for p in target_landmarks])
        
        # 변화가 있는 점들만 필터링
        changed_indices = []
        for i, (src, tgt) in enumerate(zip(source_points, target_points)):
            if np.linalg.norm(src - tgt) > 1.0:  # 1픽셀 이상 변화
                changed_indices.append(i)
        
        if len(changed_indices) < 3:
            return image  # 변화가 충분하지 않으면 원본 반환
        
        # 변화된 점들로 TPS 생성
        src_control = source_points[changed_indices]
        tgt_control = target_points[changed_indices]
        
        # 이미지 경계점 추가
        h, w = image.shape[:2]
        boundary_src = np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]])
        boundary_tgt = boundary_src.copy()  # 경계는 변형하지 않음
        
        src_all = np.vstack([src_control, boundary_src])
        tgt_all = np.vstack([tgt_control, boundary_tgt])
        
        # TPS 변형 적용
        try:
            tps = ThinPlateSpline(src_all, tgt_all)
            
            # 전체 이미지 좌표 생성
            y_coords, x_coords = np.mgrid[0:h, 0:w]
            coords = np.column_stack([x_coords.ravel(), y_coords.ravel()])
            
            # 변형된 좌표 계산
            warped_coords = tps.transform_points(coords)
            
            # 이미지 리샘플링
            warped_image = self._resample_image(image, coords, warped_coords)
            
            return warped_image
            
        except Exception as e:
            print(f"TPS 워핑 중 오류 발생: {e}")
            return image
    
    def _resample_image(self, image: np.ndarray, original_coords: np.ndarray,
                       warped_coords: np.ndarray) -> np.ndarray:
        """이미지 리샘플링"""
        import cv2
        
        h, w = image.shape[:2]
        
        # 워핑된 좌표를 이미지 크기로 제한
        warped_coords[:, 0] = np.clip(warped_coords[:, 0], 0, w-1)
        warped_coords[:, 1] = np.clip(warped_coords[:, 1], 0, h-1)
        
        # 역방향 매핑을 위한 맵 생성
        map_x = warped_coords[:, 0].reshape(h, w).astype(np.float32)
        map_y = warped_coords[:, 1].reshape(h, w).astype(np.float32)
        
        # OpenCV remap을 사용한 이미지 워핑
        warped_image = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR, 
                                borderMode=cv2.BORDER_REFLECT)
        
        return warped_image
    
    def validate_transformation(self, original_landmarks: List[Point3D],
                              modified_landmarks: List[Point3D]) -> Dict[str, float]:
        """변형 유효성 검증"""
        if len(original_landmarks) != len(modified_landmarks):
            return {"valid": False, "error": "랜드마크 수 불일치"}
        
        # 변형 통계 계산
        distances = []
        for orig, mod in zip(original_landmarks, modified_landmarks):
            dist = np.sqrt((orig.x - mod.x)**2 + (orig.y - mod.y)**2)
            distances.append(dist)
        
        avg_distance = np.mean(distances)
        max_distance = np.max(distances)
        
        # 자연스러운 변형 범위 검증
        natural_threshold = 20.0  # 픽셀
        extreme_threshold = 50.0  # 픽셀
        
        validation_result = {
            "valid": max_distance < extreme_threshold,
            "natural": avg_distance < natural_threshold,
            "avg_distance": avg_distance,
            "max_distance": max_distance,
            "affected_points": len([d for d in distances if d > 1.0])
        }
        
        return validation_result


class SurgeryEngine(ABC):
    """성형 시뮬레이션 엔진 기본 인터페이스"""
    
    @abstractmethod
    def modify_nose(self, image: np.ndarray, landmarks: List[Point3D],
                   config: NoseConfig) -> np.ndarray:
        """
        코 성형 시뮬레이션
        
        Args:
            image: 입력 이미지
            landmarks: 얼굴 랜드마크
            config: 코 성형 설정
            
        Returns:
            코 성형이 적용된 이미지
        """
        pass
    
    @abstractmethod
    def modify_eyes(self, image: np.ndarray, landmarks: List[Point3D],
                   config: EyeConfig) -> np.ndarray:
        """
        눈 성형 시뮬레이션
        
        Args:
            image: 입력 이미지
            landmarks: 얼굴 랜드마크
            config: 눈 성형 설정
            
        Returns:
            눈 성형이 적용된 이미지
        """
        pass
    
    @abstractmethod
    def modify_jawline(self, image: np.ndarray, landmarks: List[Point3D],
                      config: JawlineConfig) -> np.ndarray:
        """
        턱선 성형 시뮬레이션
        
        Args:
            image: 입력 이미지
            landmarks: 얼굴 랜드마크
            config: 턱선 성형 설정
            
        Returns:
            턱선 성형이 적용된 이미지
        """
        pass
    
    @abstractmethod
    def modify_cheekbones(self, image: np.ndarray, landmarks: List[Point3D],
                         config: CheekboneConfig) -> np.ndarray:
        """
        광대 성형 시뮬레이션
        
        Args:
            image: 입력 이미지
            landmarks: 얼굴 랜드마크
            config: 광대 성형 설정
            
        Returns:
            광대 성형이 적용된 이미지
        """
        pass
    
    @abstractmethod
    def apply_full_surgery(self, image: np.ndarray, landmarks: List[Point3D],
                          config: SurgeryConfig) -> SurgeryResult:
        """
        전체 성형 시뮬레이션 적용
        
        Args:
            image: 입력 이미지
            landmarks: 얼굴 랜드마크
            config: 전체 성형 설정
            
        Returns:
            성형 시뮬레이션 결과
        """
        pass
    
    @abstractmethod
    def validate_proportions(self, modified_landmarks: List[Point3D]) -> bool:
        """
        수정된 랜드마크의 비율이 자연스러운지 검증
        
        Args:
            modified_landmarks: 수정된 얼굴 랜드마크
            
        Returns:
            자연스러운 비율인지 여부
        """
        pass
    
    def calculate_natural_score(self, original_landmarks: List[Point3D],
                              modified_landmarks: List[Point3D]) -> float:
        """
        원본과 수정본 간의 자연스러움 점수 계산
        
        Args:
            original_landmarks: 원본 랜드마크
            modified_landmarks: 수정된 랜드마크
            
        Returns:
            자연스러움 점수 (0.0 ~ 1.0)
        """
        if len(original_landmarks) != len(modified_landmarks):
            return 0.0
        
        # 변화량 계산
        total_distance = 0.0
        for orig, mod in zip(original_landmarks, modified_landmarks):
            distance = np.sqrt((orig.x - mod.x)**2 + (orig.y - mod.y)**2)
            total_distance += distance
        
        # 평균 변화량을 기반으로 자연스러움 점수 계산
        avg_distance = total_distance / len(original_landmarks)
        
        # 변화량이 클수록 자연스러움 점수는 낮아짐
        # 임계값을 넘으면 0에 가까워짐
        max_natural_distance = 10.0  # 픽셀 단위
        natural_score = max(0.0, 1.0 - (avg_distance / max_natural_distance))
        
        return min(1.0, natural_score)
    
    def get_modification_intensity(self, config: SurgeryConfig) -> float:
        """전체 수정 강도 계산"""
        return config.get_total_modification_intensity()


class RealtimeSurgeryEngine(SurgeryEngine):
    """실시간 성형 시뮬레이션 엔진 구현"""
    
    def __init__(self):
        """성형 엔진 초기화"""
        self.mesh_warper = MeshWarper()
        
        # 자연스러운 변형 제한값 설정
        self.natural_limits = {
            FeatureType.NOSE: 15.0,      # 코: 15픽셀
            FeatureType.EYES: 10.0,      # 눈: 10픽셀
            FeatureType.JAWLINE: 20.0,   # 턱선: 20픽셀
            FeatureType.CHEEKBONES: 12.0 # 광대: 12픽셀
        }
    
    def modify_nose(self, image: np.ndarray, landmarks: List[Point3D],
                   config: NoseConfig) -> np.ndarray:
        """
        코 성형 시뮬레이션 구현
        
        Args:
            image: 입력 이미지
            landmarks: 얼굴 랜드마크
            config: 코 성형 설정
            
        Returns:
            코 성형이 적용된 이미지
        """
        try:
            # 입력 검증
            if image is None or len(image.shape) != 3:
                return image
            
            if len(landmarks) < 468:  # MediaPipe 랜드마크 수
                return image
            
            # 코 관련 랜드마크 추출
            nose_landmarks = self.mesh_warper.create_control_points(landmarks, FeatureType.NOSE)
            if not nose_landmarks:
                return image
            
            # 변형된 랜드마크 생성
            modified_landmarks = landmarks.copy()
            
            # 코 높이 조정
            if abs(config.height_adjustment) > 0.01:
                self._adjust_nose_height(modified_landmarks, config.height_adjustment)
            
            # 코 폭 조정
            if abs(config.width_adjustment) > 0.01:
                self._adjust_nose_width(modified_landmarks, config.width_adjustment)
            
            # 코끝 조정
            if abs(config.tip_adjustment) > 0.01:
                self._adjust_nose_tip(modified_landmarks, config.tip_adjustment)
            
            # 콧대 조정
            if abs(config.bridge_adjustment) > 0.01:
                self._adjust_nose_bridge(modified_landmarks, config.bridge_adjustment)
            
            # 변형 유효성 검증
            validation = self.mesh_warper.validate_transformation(landmarks, modified_landmarks)
            if not validation.get("valid", False):
                return image
            
            # TPS를 사용한 이미지 워핑
            warped_image = self.mesh_warper.warp_image_with_tps(image, landmarks, modified_landmarks)
            
            return warped_image
            
        except Exception as e:
            print(f"코 성형 시뮬레이션 중 오류 발생: {e}")
            return image
    
    def _adjust_nose_height(self, landmarks: List[Point3D], adjustment: float):
        """코 높이 조정"""
        # 코 관련 랜드마크 인덱스 (MediaPipe 기준)
        nose_tip_indices = [1, 2]  # 코끝
        nose_bridge_indices = [6, 19, 20]  # 콧대
        
        # 조정 강도 제한
        max_adjustment = 15.0  # 최대 15픽셀
        actual_adjustment = adjustment * max_adjustment
        
        # 코끝 높이 조정
        for idx in nose_tip_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y - actual_adjustment,  # 위로 올리기
                    landmarks[idx].z
                )
        
        # 콧대 높이 조정 (더 부드럽게)
        for idx in nose_bridge_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y - actual_adjustment * 0.5,
                    landmarks[idx].z
                )
    
    def _adjust_nose_width(self, landmarks: List[Point3D], adjustment: float):
        """코 폭 조정"""
        # 콧구멍 관련 랜드마크
        left_nostril_indices = [278, 279, 280, 281, 282]
        right_nostril_indices = [294, 295, 296, 297, 298]
        
        max_adjustment = 10.0  # 최대 10픽셀
        actual_adjustment = adjustment * max_adjustment
        
        # 왼쪽 콧구멍 조정
        for idx in left_nostril_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x - actual_adjustment,  # 좁히기/넓히기
                    landmarks[idx].y,
                    landmarks[idx].z
                )
        
        # 오른쪽 콧구멍 조정
        for idx in right_nostril_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x + actual_adjustment,
                    landmarks[idx].y,
                    landmarks[idx].z
                )
    
    def _adjust_nose_tip(self, landmarks: List[Point3D], adjustment: float):
        """코끝 조정"""
        nose_tip_indices = [1, 2, 5]
        
        max_adjustment = 8.0
        actual_adjustment = adjustment * max_adjustment
        
        for idx in nose_tip_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y + actual_adjustment,  # 아래로/위로
                    landmarks[idx].z
                )
    
    def _adjust_nose_bridge(self, landmarks: List[Point3D], adjustment: float):
        """콧대 조정"""
        bridge_indices = [6, 19, 20, 94, 125, 141]
        
        max_adjustment = 5.0
        actual_adjustment = adjustment * max_adjustment
        
        for idx in bridge_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y,
                    landmarks[idx].z + actual_adjustment  # 앞으로/뒤로
                )
    
    def modify_eyes(self, image: np.ndarray, landmarks: List[Point3D],
                   config: EyeConfig) -> np.ndarray:
        """
        눈 성형 시뮬레이션 구현
        
        Args:
            image: 입력 이미지
            landmarks: 얼굴 랜드마크
            config: 눈 성형 설정
            
        Returns:
            눈 성형이 적용된 이미지
        """
        try:
            if image is None or len(image.shape) != 3:
                return image
            
            if len(landmarks) < 468:
                return image
            
            modified_landmarks = landmarks.copy()
            
            # 눈 크기 조정
            if abs(config.size_adjustment) > 0.01:
                self._adjust_eye_size(modified_landmarks, config.size_adjustment)
            
            # 눈 모양 조정
            if abs(config.shape_adjustment) > 0.01:
                self._adjust_eye_shape(modified_landmarks, config.shape_adjustment)
            
            # 눈 위치 조정
            if abs(config.position_adjustment) > 0.01:
                self._adjust_eye_position(modified_landmarks, config.position_adjustment)
            
            # 눈 각도 조정
            if abs(config.angle_adjustment) > 0.01:
                self._adjust_eye_angle(modified_landmarks, config.angle_adjustment)
            
            # 변형 유효성 검증
            validation = self.mesh_warper.validate_transformation(landmarks, modified_landmarks)
            if not validation.get("valid", False):
                return image
            
            # TPS를 사용한 이미지 워핑
            warped_image = self.mesh_warper.warp_image_with_tps(image, landmarks, modified_landmarks)
            
            return warped_image
            
        except Exception as e:
            print(f"눈 성형 시뮬레이션 중 오류 발생: {e}")
            return image
    
    def _adjust_eye_size(self, landmarks: List[Point3D], adjustment: float):
        """눈 크기 조정"""
        # 왼쪽 눈 랜드마크
        left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        # 오른쪽 눈 랜드마크
        right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        max_adjustment = 8.0
        actual_adjustment = adjustment * max_adjustment
        
        # 왼쪽 눈 중심 계산
        left_eye_center = self._calculate_eye_center(landmarks, left_eye_indices)
        # 오른쪽 눈 중심 계산
        right_eye_center = self._calculate_eye_center(landmarks, right_eye_indices)
        
        # 왼쪽 눈 크기 조정
        for idx in left_eye_indices:
            if idx < len(landmarks):
                dx = landmarks[idx].x - left_eye_center.x
                dy = landmarks[idx].y - left_eye_center.y
                
                landmarks[idx] = Point3D(
                    left_eye_center.x + dx * (1 + actual_adjustment * 0.1),
                    left_eye_center.y + dy * (1 + actual_adjustment * 0.1),
                    landmarks[idx].z
                )
        
        # 오른쪽 눈 크기 조정
        for idx in right_eye_indices:
            if idx < len(landmarks):
                dx = landmarks[idx].x - right_eye_center.x
                dy = landmarks[idx].y - right_eye_center.y
                
                landmarks[idx] = Point3D(
                    right_eye_center.x + dx * (1 + actual_adjustment * 0.1),
                    right_eye_center.y + dy * (1 + actual_adjustment * 0.1),
                    landmarks[idx].z
                )
    
    def _calculate_eye_center(self, landmarks: List[Point3D], eye_indices: List[int]) -> Point3D:
        """눈 중심점 계산"""
        if not eye_indices:
            return Point3D(0, 0, 0)
        
        total_x = sum(landmarks[idx].x for idx in eye_indices if idx < len(landmarks))
        total_y = sum(landmarks[idx].y for idx in eye_indices if idx < len(landmarks))
        total_z = sum(landmarks[idx].z for idx in eye_indices if idx < len(landmarks))
        count = len([idx for idx in eye_indices if idx < len(landmarks)])
        
        if count == 0:
            return Point3D(0, 0, 0)
        
        return Point3D(total_x / count, total_y / count, total_z / count)
    
    def _adjust_eye_shape(self, landmarks: List[Point3D], adjustment: float):
        """눈 모양 조정 (둥글게/날카롭게)"""
        # 눈꼬리 부분 랜드마크
        left_eye_corner = [33, 133]
        right_eye_corner = [362, 263]
        
        max_adjustment = 5.0
        actual_adjustment = adjustment * max_adjustment
        
        # 왼쪽 눈꼬리 조정
        for idx in left_eye_corner:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x + actual_adjustment,
                    landmarks[idx].y - actual_adjustment * 0.5,
                    landmarks[idx].z
                )
        
        # 오른쪽 눈꼬리 조정
        for idx in right_eye_corner:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x - actual_adjustment,
                    landmarks[idx].y - actual_adjustment * 0.5,
                    landmarks[idx].z
                )
    
    def _adjust_eye_position(self, landmarks: List[Point3D], adjustment: float):
        """눈 위치 조정 (가깝게/멀게)"""
        left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        max_adjustment = 6.0
        actual_adjustment = adjustment * max_adjustment
        
        # 왼쪽 눈을 중앙으로/바깥으로 이동
        for idx in left_eye_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x + actual_adjustment,
                    landmarks[idx].y,
                    landmarks[idx].z
                )
        
        # 오른쪽 눈을 중앙으로/바깥으로 이동
        for idx in right_eye_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x - actual_adjustment,
                    landmarks[idx].y,
                    landmarks[idx].z
                )
    
    def _adjust_eye_angle(self, landmarks: List[Point3D], adjustment: float):
        """눈 각도 조정 (처짐/올라감)"""
        # 눈꼬리 랜드마크
        left_eye_outer = [33]
        right_eye_outer = [362]
        
        max_adjustment = 4.0
        actual_adjustment = adjustment * max_adjustment
        
        # 왼쪽 눈꼬리 각도 조정
        for idx in left_eye_outer:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y - actual_adjustment,
                    landmarks[idx].z
                )
        
        # 오른쪽 눈꼬리 각도 조정
        for idx in right_eye_outer:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y - actual_adjustment,
                    landmarks[idx].z
                )
    
    def modify_jawline(self, image: np.ndarray, landmarks: List[Point3D],
                      config: JawlineConfig) -> np.ndarray:
        """턱선 성형 시뮬레이션 구현"""
        try:
            if image is None or len(image.shape) != 3:
                return image
            
            if len(landmarks) < 468:
                return image
            
            modified_landmarks = landmarks.copy()
            
            # 턱선 폭 조정
            if abs(config.width_adjustment) > 0.01:
                self._adjust_jawline_width(modified_landmarks, config.width_adjustment)
            
            # 턱선 각도 조정
            if abs(config.angle_adjustment) > 0.01:
                self._adjust_jawline_angle(modified_landmarks, config.angle_adjustment)
            
            # 턱선 길이 조정
            if abs(config.length_adjustment) > 0.01:
                self._adjust_jawline_length(modified_landmarks, config.length_adjustment)
            
            # 변형 유효성 검증
            validation = self.mesh_warper.validate_transformation(landmarks, modified_landmarks)
            if not validation.get("valid", False):
                return image
            
            # TPS를 사용한 이미지 워핑
            warped_image = self.mesh_warper.warp_image_with_tps(image, landmarks, modified_landmarks)
            
            return warped_image
            
        except Exception as e:
            print(f"턱선 성형 시뮬레이션 중 오류 발생: {e}")
            return image
    
    def _adjust_jawline_width(self, landmarks: List[Point3D], adjustment: float):
        """턱선 폭 조정"""
        jawline_indices = [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323]
        
        max_adjustment = 15.0
        actual_adjustment = adjustment * max_adjustment
        
        # 얼굴 중심 계산
        face_center_x = sum(landmarks[idx].x for idx in jawline_indices if idx < len(landmarks)) / len(jawline_indices)
        
        for idx in jawline_indices:
            if idx < len(landmarks):
                # 중심에서의 거리에 따라 조정
                distance_from_center = landmarks[idx].x - face_center_x
                
                landmarks[idx] = Point3D(
                    landmarks[idx].x + (actual_adjustment if distance_from_center > 0 else -actual_adjustment),
                    landmarks[idx].y,
                    landmarks[idx].z
                )
    
    def _adjust_jawline_angle(self, landmarks: List[Point3D], adjustment: float):
        """턱선 각도 조정"""
        jaw_corner_indices = [172, 397]  # 턱 모서리
        
        max_adjustment = 8.0
        actual_adjustment = adjustment * max_adjustment
        
        for idx in jaw_corner_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y + actual_adjustment,
                    landmarks[idx].z
                )
    
    def _adjust_jawline_length(self, landmarks: List[Point3D], adjustment: float):
        """턱선 길이 조정"""
        chin_indices = [152, 175]  # 턱끝
        
        max_adjustment = 10.0
        actual_adjustment = adjustment * max_adjustment
        
        for idx in chin_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y + actual_adjustment,
                    landmarks[idx].z
                )
    
    def modify_cheekbones(self, image: np.ndarray, landmarks: List[Point3D],
                         config: CheekboneConfig) -> np.ndarray:
        """광대 성형 시뮬레이션 구현"""
        try:
            if image is None or len(image.shape) != 3:
                return image
            
            if len(landmarks) < 468:
                return image
            
            modified_landmarks = landmarks.copy()
            
            # 광대 높이 조정
            if abs(config.height_adjustment) > 0.01:
                self._adjust_cheekbone_height(modified_landmarks, config.height_adjustment)
            
            # 광대 폭 조정
            if abs(config.width_adjustment) > 0.01:
                self._adjust_cheekbone_width(modified_landmarks, config.width_adjustment)
            
            # 광대 돌출 조정
            if abs(config.prominence_adjustment) > 0.01:
                self._adjust_cheekbone_prominence(modified_landmarks, config.prominence_adjustment)
            
            # 변형 유효성 검증
            validation = self.mesh_warper.validate_transformation(landmarks, modified_landmarks)
            if not validation.get("valid", False):
                return image
            
            # TPS를 사용한 이미지 워핑
            warped_image = self.mesh_warper.warp_image_with_tps(image, landmarks, modified_landmarks)
            
            return warped_image
            
        except Exception as e:
            print(f"광대 성형 시뮬레이션 중 오류 발생: {e}")
            return image
    
    def _adjust_cheekbone_height(self, landmarks: List[Point3D], adjustment: float):
        """광대 높이 조정"""
        cheekbone_indices = [116, 117, 118, 119, 120, 121, 345, 346, 347, 348, 349, 350]
        
        max_adjustment = 8.0
        actual_adjustment = adjustment * max_adjustment
        
        for idx in cheekbone_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y - actual_adjustment,
                    landmarks[idx].z
                )
    
    def _adjust_cheekbone_width(self, landmarks: List[Point3D], adjustment: float):
        """광대 폭 조정"""
        left_cheek_indices = [116, 117, 118, 119, 120, 121]
        right_cheek_indices = [345, 346, 347, 348, 349, 350]
        
        max_adjustment = 12.0
        actual_adjustment = adjustment * max_adjustment
        
        # 왼쪽 광대
        for idx in left_cheek_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x - actual_adjustment,
                    landmarks[idx].y,
                    landmarks[idx].z
                )
        
        # 오른쪽 광대
        for idx in right_cheek_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x + actual_adjustment,
                    landmarks[idx].y,
                    landmarks[idx].z
                )
    
    def _adjust_cheekbone_prominence(self, landmarks: List[Point3D], adjustment: float):
        """광대 돌출 조정"""
        cheekbone_indices = [116, 117, 118, 345, 346, 347]
        
        max_adjustment = 6.0
        actual_adjustment = adjustment * max_adjustment
        
        for idx in cheekbone_indices:
            if idx < len(landmarks):
                landmarks[idx] = Point3D(
                    landmarks[idx].x,
                    landmarks[idx].y,
                    landmarks[idx].z + actual_adjustment
                )
    
    def apply_full_surgery(self, image: np.ndarray, landmarks: List[Point3D],
                          config: SurgeryConfig) -> SurgeryResult:
        """전체 성형 시뮬레이션 적용"""
        import time
        start_time = time.time()
        
        result_image = image.copy()
        applied_modifications = []
        
        try:
            # 각 성형 요소를 순차적으로 적용
            
            # 1. 코 성형
            if config.nose and self._has_nose_modifications(config.nose):
                result_image = self.modify_nose(result_image, landmarks, config.nose)
                applied_modifications.append("nose")
            
            # 2. 눈 성형
            if config.eyes and self._has_eye_modifications(config.eyes):
                result_image = self.modify_eyes(result_image, landmarks, config.eyes)
                applied_modifications.append("eyes")
            
            # 3. 광대 성형
            if config.cheekbones and self._has_cheekbone_modifications(config.cheekbones):
                result_image = self.modify_cheekbones(result_image, landmarks, config.cheekbones)
                applied_modifications.append("cheekbones")
            
            # 4. 턱선 성형 (마지막에 적용)
            if config.jawline and self._has_jawline_modifications(config.jawline):
                result_image = self.modify_jawline(result_image, landmarks, config.jawline)
                applied_modifications.append("jawline")
            
            # 자연스러움 점수 계산 (실제로는 변형된 랜드마크가 필요하지만 여기서는 설정 기반으로 추정)
            natural_score = self._calculate_natural_score_from_config(config)
            
        except Exception as e:
            print(f"전체 성형 시뮬레이션 중 오류 발생: {e}")
        
        processing_time = time.time() - start_time
        
        return SurgeryResult(
            image=result_image,
            modified_landmarks=landmarks,  # 실제로는 변형된 랜드마크를 반환해야 함
            applied_modifications=applied_modifications,
            natural_score=natural_score,
            processing_time=processing_time
        )
    
    def _has_nose_modifications(self, config: NoseConfig) -> bool:
        """코 성형 설정이 있는지 확인"""
        return (abs(config.height_adjustment) > 0.01 or
                abs(config.width_adjustment) > 0.01 or
                abs(config.tip_adjustment) > 0.01 or
                abs(config.bridge_adjustment) > 0.01)
    
    def _has_eye_modifications(self, config: EyeConfig) -> bool:
        """눈 성형 설정이 있는지 확인"""
        return (abs(config.size_adjustment) > 0.01 or
                abs(config.shape_adjustment) > 0.01 or
                abs(config.position_adjustment) > 0.01 or
                abs(config.angle_adjustment) > 0.01)
    
    def _has_jawline_modifications(self, config: JawlineConfig) -> bool:
        """턱선 성형 설정이 있는지 확인"""
        return (abs(config.width_adjustment) > 0.01 or
                abs(config.angle_adjustment) > 0.01 or
                abs(config.length_adjustment) > 0.01)
    
    def _has_cheekbone_modifications(self, config: CheekboneConfig) -> bool:
        """광대 성형 설정이 있는지 확인"""
        return (abs(config.height_adjustment) > 0.01 or
                abs(config.width_adjustment) > 0.01 or
                abs(config.prominence_adjustment) > 0.01)
    
    def _calculate_natural_score_from_config(self, config: SurgeryConfig) -> float:
        """설정 기반 자연스러움 점수 계산"""
        total_intensity = config.get_total_modification_intensity()
        
        # 강도가 낮을수록 자연스러움 점수가 높음
        if total_intensity <= 0.3:
            return 0.9
        elif total_intensity <= 0.6:
            return 0.7
        elif total_intensity <= 0.8:
            return 0.5
        else:
            return 0.3
    
    def validate_proportions(self, modified_landmarks: List[Point3D]) -> bool:
        """수정된 랜드마크의 비율이 자연스러운지 검증"""
        if len(modified_landmarks) < 468:
            return False
        
        try:
            # 기본적인 얼굴 비율 검증
            
            # 1. 눈 간격 검증
            left_eye_center = self._calculate_eye_center(modified_landmarks, [33, 133])
            right_eye_center = self._calculate_eye_center(modified_landmarks, [362, 263])
            eye_distance = abs(left_eye_center.x - right_eye_center.x)
            
            # 2. 얼굴 폭 대비 눈 간격 비율 (일반적으로 1:5 비율)
            face_width = self._calculate_face_width(modified_landmarks)
            if face_width > 0:
                eye_ratio = eye_distance / face_width
                if not (0.15 <= eye_ratio <= 0.25):  # 정상 범위
                    return False
            
            # 3. 코 비율 검증
            nose_width = self._calculate_nose_width(modified_landmarks)
            if nose_width > 0:
                nose_ratio = nose_width / face_width
                if not (0.08 <= nose_ratio <= 0.15):  # 정상 범위
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_face_width(self, landmarks: List[Point3D]) -> float:
        """얼굴 폭 계산"""
        try:
            # 광대뼈 부분의 폭 계산
            left_cheek = landmarks[116] if 116 < len(landmarks) else Point3D(0, 0, 0)
            right_cheek = landmarks[345] if 345 < len(landmarks) else Point3D(0, 0, 0)
            return abs(right_cheek.x - left_cheek.x)
        except:
            return 0.0
    
    def _calculate_nose_width(self, landmarks: List[Point3D]) -> float:
        """코 폭 계산"""
        try:
            # 콧구멍 간격 계산
            left_nostril = landmarks[278] if 278 < len(landmarks) else Point3D(0, 0, 0)
            right_nostril = landmarks[294] if 294 < len(landmarks) else Point3D(0, 0, 0)
            return abs(right_nostril.x - left_nostril.x)
        except:
            return 0.0