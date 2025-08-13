"""
통합 효과 처리 엔진 - 메이크업과 성형 효과를 동시에 적용
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import time
import cv2
from dataclasses import dataclass
from enum import Enum

from models.core import Point3D, Color
from models.makeup import MakeupConfig
from models.surgery import SurgeryConfig
from engines.makeup_engine import RealtimeMakeupEngine, MakeupResult
from engines.surgery_engine import RealtimeSurgeryEngine, SurgeryResult


class EffectPriority(Enum):
    """효과 적용 우선순위"""
    SURGERY_FIRST = "surgery_first"  # 성형 먼저, 메이크업 나중
    MAKEUP_FIRST = "makeup_first"    # 메이크업 먼저, 성형 나중
    INTERLEAVED = "interleaved"      # 교차 적용


class ConflictResolution(Enum):
    """효과 충돌 해결 방식"""
    OVERRIDE = "override"      # 나중 효과가 이전 효과를 덮어씀
    BLEND = "blend"           # 두 효과를 블렌딩
    PRESERVE = "preserve"     # 이전 효과를 보존하고 새 효과는 적용하지 않음


@dataclass
class IntegratedConfig:
    """통합 효과 설정"""
    makeup_config: Optional[MakeupConfig] = None
    surgery_config: Optional[SurgeryConfig] = None
    effect_priority: EffectPriority = EffectPriority.SURGERY_FIRST
    conflict_resolution: ConflictResolution = ConflictResolution.BLEND
    enable_caching: bool = True
    quality_threshold: float = 0.7  # 품질 임계값


@dataclass
class IntegratedResult:
    """통합 효과 적용 결과"""
    final_image: np.ndarray
    modified_landmarks: List[Point3D]
    makeup_result: Optional[MakeupResult]
    surgery_result: Optional[SurgeryResult]
    applied_effects: List[str]
    processing_time: float
    quality_score: float
    conflicts_detected: List[str]
    
    def is_successful(self) -> bool:
        """통합 효과 적용이 성공했는지 확인"""
        return (self.final_image is not None and 
                len(self.applied_effects) > 0 and
                self.quality_score >= 0.5)
    
    def is_high_quality(self, threshold: float = 0.7) -> bool:
        """고품질 결과인지 확인"""
        return self.quality_score >= threshold


class EffectCache:
    """효과 캐싱 시스템"""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order: List[str] = []
    
    def _generate_key(self, image_hash: str, config_hash: str) -> str:
        """캐시 키 생성"""
        return f"{image_hash}_{config_hash}"
    
    def get(self, image: np.ndarray, config: Any) -> Optional[Any]:
        """캐시에서 결과 조회"""
        try:
            image_hash = str(hash(image.tobytes()))
            config_hash = str(hash(str(config)))
            key = self._generate_key(image_hash, config_hash)
            
            if key in self.cache:
                # 접근 순서 업데이트
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
            
            return None
        except:
            return None
    
    def put(self, image: np.ndarray, config: Any, result: Any):
        """결과를 캐시에 저장"""
        try:
            image_hash = str(hash(image.tobytes()))
            config_hash = str(hash(str(config)))
            key = self._generate_key(image_hash, config_hash)
            
            # 캐시 크기 제한
            if len(self.cache) >= self.max_size:
                # 가장 오래된 항목 제거
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            self.cache[key] = result
            self.access_order.append(key)
        except:
            pass  # 캐싱 실패는 무시
    
    def clear(self):
        """캐시 초기화"""
        self.cache.clear()
        self.access_order.clear()


class ConflictDetector:
    """효과 간 충돌 감지"""
    
    @staticmethod
    def detect_conflicts(makeup_config: Optional[MakeupConfig], 
                        surgery_config: Optional[SurgeryConfig]) -> List[str]:
        """메이크업과 성형 효과 간 충돌 감지"""
        conflicts = []
        
        if not makeup_config or not surgery_config:
            return conflicts
        
        # 입술 영역 충돌 검사
        if (makeup_config.lipstick and 
            surgery_config.jawline and 
            abs(surgery_config.jawline.length_adjustment) > 0.3):
            conflicts.append("lipstick_jawline_conflict")
        
        # 눈 영역 충돌 검사
        if (makeup_config.eyeshadow and 
            surgery_config.eyes and 
            abs(surgery_config.eyes.size_adjustment) > 0.4):
            conflicts.append("eyeshadow_eye_surgery_conflict")
        
        # 볼 영역 충돌 검사
        if (makeup_config.blush and 
            surgery_config.cheekbones and 
            abs(surgery_config.cheekbones.width_adjustment) > 0.3):
            conflicts.append("blush_cheekbone_conflict")
        
        return conflicts
    
    @staticmethod
    def resolve_conflicts(conflicts: List[str], 
                         resolution: ConflictResolution,
                         makeup_config: Optional[MakeupConfig],
                         surgery_config: Optional[SurgeryConfig]) -> Tuple[Optional[MakeupConfig], Optional[SurgeryConfig]]:
        """충돌 해결"""
        if not conflicts:
            return makeup_config, surgery_config
        
        resolved_makeup = makeup_config
        resolved_surgery = surgery_config
        
        if resolution == ConflictResolution.OVERRIDE:
            # 나중 효과가 우선 (설정에 따라)
            pass  # 기본적으로 두 효과 모두 적용
        
        elif resolution == ConflictResolution.BLEND:
            # 효과 강도를 줄여서 블렌딩
            if resolved_makeup and resolved_surgery:
                # 메이크업 강도 조절
                if "lipstick_jawline_conflict" in conflicts and resolved_makeup.lipstick:
                    resolved_makeup.lipstick.opacity *= 0.7
                
                if "eyeshadow_eye_surgery_conflict" in conflicts and resolved_makeup.eyeshadow:
                    resolved_makeup.eyeshadow.opacity *= 0.8
                
                if "blush_cheekbone_conflict" in conflicts and resolved_makeup.blush:
                    resolved_makeup.blush.intensity *= 0.8
                
                # 성형 강도 조절
                if "lipstick_jawline_conflict" in conflicts and resolved_surgery.jawline:
                    resolved_surgery.jawline.length_adjustment *= 0.8
                
                if "eyeshadow_eye_surgery_conflict" in conflicts and resolved_surgery.eyes:
                    resolved_surgery.eyes.size_adjustment *= 0.8
                
                if "blush_cheekbone_conflict" in conflicts and resolved_surgery.cheekbones:
                    resolved_surgery.cheekbones.width_adjustment *= 0.8
        
        elif resolution == ConflictResolution.PRESERVE:
            # 첫 번째 효과만 적용 (우선순위에 따라)
            pass  # 구현 필요시 추가
        
        return resolved_makeup, resolved_surgery


class QualityAssessment:
    """품질 평가 시스템"""
    
    @staticmethod
    def assess_quality(original_image: np.ndarray, 
                      processed_image: np.ndarray,
                      landmarks: List[Point3D]) -> float:
        """이미지 품질 평가"""
        try:
            # 1. 이미지 유사도 평가 (SSIM)
            similarity_score = QualityAssessment._calculate_ssim(original_image, processed_image)
            
            # 2. 얼굴 대칭성 평가
            symmetry_score = QualityAssessment._assess_face_symmetry(landmarks)
            
            # 3. 자연스러움 평가
            naturalness_score = QualityAssessment._assess_naturalness(original_image, processed_image)
            
            # 가중 평균으로 최종 점수 계산
            final_score = (similarity_score * 0.3 + 
                          symmetry_score * 0.4 + 
                          naturalness_score * 0.3)
            
            return max(0.0, min(1.0, final_score))
            
        except Exception:
            return 0.5  # 평가 실패시 중간 점수
    
    @staticmethod
    def _calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
        """구조적 유사도 지수 계산"""
        try:
            # 그레이스케일 변환
            if len(img1.shape) == 3:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            else:
                gray1 = img1
            
            if len(img2.shape) == 3:
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            else:
                gray2 = img2
            
            # 간단한 SSIM 근사치 계산
            mean1 = np.mean(gray1)
            mean2 = np.mean(gray2)
            var1 = np.var(gray1)
            var2 = np.var(gray2)
            cov = np.mean((gray1 - mean1) * (gray2 - mean2))
            
            c1 = 0.01 ** 2
            c2 = 0.03 ** 2
            
            ssim = ((2 * mean1 * mean2 + c1) * (2 * cov + c2)) / \
                   ((mean1 ** 2 + mean2 ** 2 + c1) * (var1 + var2 + c2))
            
            return max(0.0, min(1.0, ssim))
            
        except Exception:
            return 0.7
    
    @staticmethod
    def _assess_face_symmetry(landmarks: List[Point3D]) -> float:
        """얼굴 대칭성 평가"""
        try:
            if len(landmarks) < 468:
                return 0.7
            
            # 얼굴 중심선 계산
            face_center_x = np.mean([p.x for p in landmarks])
            
            # 좌우 대칭 포인트들의 거리 차이 계산
            symmetry_pairs = [
                (33, 362),   # 눈 모서리
                (61, 291),   # 입 모서리
                (116, 345),  # 광대
                (172, 397)   # 턱선
            ]
            
            symmetry_scores = []
            for left_idx, right_idx in symmetry_pairs:
                if left_idx < len(landmarks) and right_idx < len(landmarks):
                    left_point = landmarks[left_idx]
                    right_point = landmarks[right_idx]
                    
                    # 중심선으로부터의 거리 차이
                    left_dist = abs(left_point.x - face_center_x)
                    right_dist = abs(right_point.x - face_center_x)
                    
                    # 대칭성 점수 (거리 차이가 작을수록 높은 점수)
                    max_dist = max(left_dist, right_dist)
                    if max_dist > 0:
                        symmetry = 1.0 - abs(left_dist - right_dist) / max_dist
                        symmetry_scores.append(symmetry)
            
            return np.mean(symmetry_scores) if symmetry_scores else 0.7
            
        except Exception:
            return 0.7
    
    @staticmethod
    def _assess_naturalness(original: np.ndarray, processed: np.ndarray) -> float:
        """자연스러움 평가"""
        try:
            # 색상 분포 변화 평가
            orig_hist = cv2.calcHist([original], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            proc_hist = cv2.calcHist([processed], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            
            # 히스토그램 상관관계 계산
            correlation = cv2.compareHist(orig_hist, proc_hist, cv2.HISTCMP_CORREL)
            
            # 극단적인 변화 감지
            diff = cv2.absdiff(original, processed)
            extreme_changes = np.sum(diff > 100) / diff.size
            
            # 자연스러움 점수 계산
            naturalness = correlation * (1.0 - extreme_changes)
            
            return max(0.0, min(1.0, naturalness))
            
        except Exception:
            return 0.7


class IntegratedEngine:
    """통합 효과 처리 엔진"""
    
    def __init__(self):
        """통합 엔진 초기화"""
        self.makeup_engine = RealtimeMakeupEngine()
        self.surgery_engine = RealtimeSurgeryEngine()
        self.effect_cache = EffectCache()
        self.conflict_detector = ConflictDetector()
        self.quality_assessor = QualityAssessment()
    
    def apply_integrated_effects(self, 
                               image: np.ndarray, 
                               landmarks: List[Point3D],
                               config: IntegratedConfig) -> IntegratedResult:
        """통합 효과 적용"""
        start_time = time.time()
        
        # 캐시 확인
        if config.enable_caching:
            cached_result = self.effect_cache.get(image, config)
            if cached_result:
                return cached_result
        
        # 충돌 감지 및 해결
        conflicts = self.conflict_detector.detect_conflicts(
            config.makeup_config, config.surgery_config
        )
        
        resolved_makeup, resolved_surgery = self.conflict_detector.resolve_conflicts(
            conflicts, config.conflict_resolution, 
            config.makeup_config, config.surgery_config
        )
        
        # 효과 적용
        result_image = image.copy()
        current_landmarks = landmarks.copy()
        makeup_result = None
        surgery_result = None
        applied_effects = []
        
        try:
            if config.effect_priority == EffectPriority.SURGERY_FIRST:
                # 성형 먼저 적용
                if resolved_surgery:
                    surgery_result = self.surgery_engine.apply_full_surgery(
                        result_image, current_landmarks, resolved_surgery
                    )
                    if surgery_result.is_successful():
                        result_image = surgery_result.image
                        current_landmarks = surgery_result.modified_landmarks
                        applied_effects.extend(surgery_result.applied_modifications)
                
                # 메이크업 나중 적용
                if resolved_makeup:
                    makeup_result = self.makeup_engine.apply_full_makeup(
                        result_image, current_landmarks, resolved_makeup
                    )
                    if makeup_result.is_successful():
                        result_image = makeup_result.image
                        applied_effects.extend(makeup_result.applied_effects)
            
            elif config.effect_priority == EffectPriority.MAKEUP_FIRST:
                # 메이크업 먼저 적용
                if resolved_makeup:
                    makeup_result = self.makeup_engine.apply_full_makeup(
                        result_image, current_landmarks, resolved_makeup
                    )
                    if makeup_result.is_successful():
                        result_image = makeup_result.image
                        applied_effects.extend(makeup_result.applied_effects)
                
                # 성형 나중 적용
                if resolved_surgery:
                    surgery_result = self.surgery_engine.apply_full_surgery(
                        result_image, current_landmarks, resolved_surgery
                    )
                    if surgery_result.is_successful():
                        result_image = surgery_result.image
                        current_landmarks = surgery_result.modified_landmarks
                        applied_effects.extend(surgery_result.applied_modifications)
            
            elif config.effect_priority == EffectPriority.INTERLEAVED:
                # 교차 적용 (구현 복잡도로 인해 기본적으로 성형 먼저 적용)
                result_image, current_landmarks, makeup_result, surgery_result, applied_effects = \
                    self._apply_interleaved_effects(
                        result_image, current_landmarks, resolved_makeup, resolved_surgery
                    )
        
        except Exception as e:
            print(f"통합 효과 적용 중 오류 발생: {e}")
        
        # 품질 평가
        quality_score = self.quality_assessor.assess_quality(
            image, result_image, current_landmarks
        )
        
        processing_time = time.time() - start_time
        
        # 결과 생성
        integrated_result = IntegratedResult(
            final_image=result_image,
            modified_landmarks=current_landmarks,
            makeup_result=makeup_result,
            surgery_result=surgery_result,
            applied_effects=applied_effects,
            processing_time=processing_time,
            quality_score=quality_score,
            conflicts_detected=conflicts
        )
        
        # 캐시에 저장
        if config.enable_caching and integrated_result.is_successful():
            self.effect_cache.put(image, config, integrated_result)
        
        return integrated_result
    
    def _apply_interleaved_effects(self, 
                                 image: np.ndarray, 
                                 landmarks: List[Point3D],
                                 makeup_config: Optional[MakeupConfig],
                                 surgery_config: Optional[SurgeryConfig]) -> Tuple[np.ndarray, List[Point3D], Optional[MakeupResult], Optional[SurgeryResult], List[str]]:
        """교차 효과 적용"""
        result_image = image.copy()
        current_landmarks = landmarks.copy()
        applied_effects = []
        makeup_result = None
        surgery_result = None
        
        # 단계별 교차 적용 (예시)
        # 1. 기본 성형 (얼굴 형태 변경)
        if surgery_config and surgery_config.jawline:
            temp_surgery = SurgeryConfig(jawline=surgery_config.jawline)
            surgery_result = self.surgery_engine.apply_full_surgery(
                result_image, current_landmarks, temp_surgery
            )
            if surgery_result.is_successful():
                result_image = surgery_result.image
                current_landmarks = surgery_result.modified_landmarks
                applied_effects.extend(surgery_result.applied_modifications)
        
        # 2. 기본 메이크업 (파운데이션)
        if makeup_config and makeup_config.foundation:
            temp_makeup = MakeupConfig(foundation=makeup_config.foundation)
            makeup_result = self.makeup_engine.apply_full_makeup(
                result_image, current_landmarks, temp_makeup
            )
            if makeup_result.is_successful():
                result_image = makeup_result.image
                applied_effects.extend(makeup_result.applied_effects)
        
        # 3. 나머지 효과들 적용
        # ... (복잡한 교차 로직은 필요에 따라 확장)
        
        return result_image, current_landmarks, makeup_result, surgery_result, applied_effects
    
    def clear_cache(self):
        """캐시 초기화"""
        self.effect_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """캐시 통계 조회"""
        return {
            "cache_size": len(self.effect_cache.cache),
            "max_size": self.effect_cache.max_size
        }