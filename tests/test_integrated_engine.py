#!/usr/bin/env python3
"""
통합 효과 처리 엔진 테스트
"""
import unittest
import numpy as np
import time
import cv2
from typing import List

from models.core import Point3D, Color
from models.makeup import MakeupConfig, LipstickConfig, EyeshadowConfig, BlushConfig, FoundationConfig
from models.surgery import SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig
from engines.integrated_engine import (
    IntegratedEngine, IntegratedConfig, EffectPriority, ConflictResolution,
    ConflictDetector, QualityAssessment, EffectCache
)


class TestEffectCache(unittest.TestCase):
    """효과 캐시 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.cache = EffectCache(max_size=3)
        self.test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        self.test_config = "test_config"
        self.test_result = "test_result"
    
    def test_cache_put_get(self):
        """캐시 저장 및 조회 테스트"""
        # 결과 저장
        self.cache.put(self.test_image, self.test_config, self.test_result)
        
        # 결과 조회
        cached_result = self.cache.get(self.test_image, self.test_config)
        self.assertEqual(cached_result, self.test_result)
    
    def test_cache_miss(self):
        """캐시 미스 테스트"""
        different_image = np.ones((100, 100, 3), dtype=np.uint8) * 64
        result = self.cache.get(different_image, self.test_config)
        self.assertIsNone(result)
    
    def test_cache_size_limit(self):
        """캐시 크기 제한 테스트"""
        # 최대 크기보다 많은 항목 저장
        for i in range(5):
            image = np.ones((100, 100, 3), dtype=np.uint8) * (i * 50)
            config = f"config_{i}"
            result = f"result_{i}"
            self.cache.put(image, config, result)
        
        # 캐시 크기가 제한을 넘지 않는지 확인
        self.assertLessEqual(len(self.cache.cache), self.cache.max_size)
    
    def test_cache_clear(self):
        """캐시 초기화 테스트"""
        self.cache.put(self.test_image, self.test_config, self.test_result)
        self.cache.clear()
        
        self.assertEqual(len(self.cache.cache), 0)
        self.assertEqual(len(self.cache.access_order), 0)


class TestConflictDetector(unittest.TestCase):
    """충돌 감지 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.detector = ConflictDetector()
    
    def test_no_conflicts(self):
        """충돌 없음 테스트"""
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.5)
        )
        surgery_config = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.1)
        )
        
        conflicts = self.detector.detect_conflicts(makeup_config, surgery_config)
        self.assertEqual(len(conflicts), 0)
    
    def test_lipstick_jawline_conflict(self):
        """립스틱-턱선 충돌 테스트"""
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.8)
        )
        surgery_config = SurgeryConfig(
            jawline=JawlineConfig(length_adjustment=0.5)  # 큰 변화
        )
        
        conflicts = self.detector.detect_conflicts(makeup_config, surgery_config)
        self.assertIn("lipstick_jawline_conflict", conflicts)
    
    def test_eyeshadow_eye_surgery_conflict(self):
        """아이섀도-눈성형 충돌 테스트"""
        makeup_config = MakeupConfig(
            eyeshadow=EyeshadowConfig(primary_color=Color(100, 50, 200), opacity=0.7)
        )
        surgery_config = SurgeryConfig(
            eyes=EyeConfig(size_adjustment=0.6)  # 큰 변화
        )
        
        conflicts = self.detector.detect_conflicts(makeup_config, surgery_config)
        self.assertIn("eyeshadow_eye_surgery_conflict", conflicts)
    
    def test_blush_cheekbone_conflict(self):
        """블러셔-광대 충돌 테스트"""
        makeup_config = MakeupConfig(
            blush=BlushConfig(color=Color(255, 100, 100), intensity=0.6)
        )
        surgery_config = SurgeryConfig(
            cheekbones=CheekboneConfig(width_adjustment=0.4)  # 큰 변화
        )
        
        conflicts = self.detector.detect_conflicts(makeup_config, surgery_config)
        self.assertIn("blush_cheekbone_conflict", conflicts)
    
    def test_conflict_resolution_blend(self):
        """충돌 해결 - 블렌딩 테스트"""
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=1.0)
        )
        surgery_config = SurgeryConfig(
            jawline=JawlineConfig(length_adjustment=0.5)
        )
        
        conflicts = ["lipstick_jawline_conflict"]
        
        resolved_makeup, resolved_surgery = self.detector.resolve_conflicts(
            conflicts, ConflictResolution.BLEND, makeup_config, surgery_config
        )
        
        # 강도가 줄어들었는지 확인
        self.assertLess(resolved_makeup.lipstick.opacity, makeup_config.lipstick.opacity)
        self.assertLess(abs(resolved_surgery.jawline.length_adjustment), 
                       abs(surgery_config.jawline.length_adjustment))


class TestQualityAssessment(unittest.TestCase):
    """품질 평가 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.assessor = QualityAssessment()
        self.original_image = np.ones((200, 200, 3), dtype=np.uint8) * 128
        self.landmarks = [Point3D(float(i), float(i), 0.0) for i in range(468)]
    
    def test_identical_images_quality(self):
        """동일한 이미지 품질 평가"""
        quality = self.assessor.assess_quality(
            self.original_image, self.original_image, self.landmarks
        )
        self.assertGreater(quality, 0.8)  # 동일한 이미지는 높은 품질
    
    def test_heavily_modified_image_quality(self):
        """크게 변형된 이미지 품질 평가"""
        modified_image = np.ones((200, 200, 3), dtype=np.uint8) * 255  # 완전히 다른 이미지
        quality = self.assessor.assess_quality(
            self.original_image, modified_image, self.landmarks
        )
        self.assertLess(quality, 0.7)  # 크게 변형된 이미지는 낮은 품질
    
    def test_face_symmetry_assessment(self):
        """얼굴 대칭성 평가 테스트"""
        # 대칭적인 랜드마크
        symmetric_landmarks = []
        center_x = 100
        for i in range(468):
            if i < 234:  # 왼쪽
                x = center_x - 50 + (i % 10) * 5
            else:  # 오른쪽 (대칭)
                x = center_x + 50 - ((i - 234) % 10) * 5
            y = 100 + (i // 10) * 2
            symmetric_landmarks.append(Point3D(x, y, 0))
        
        symmetry_score = self.assessor._assess_face_symmetry(symmetric_landmarks)
        self.assertGreater(symmetry_score, 0.6)


class TestIntegratedEngine(unittest.TestCase):
    """통합 엔진 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = IntegratedEngine()
        self.test_image = self._create_test_image()
        self.test_landmarks = self._create_test_landmarks()
    
    def _create_test_image(self) -> np.ndarray:
        """테스트용 이미지 생성"""
        image = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        # 간단한 얼굴 형태 그리기
        center = (320, 240)
        cv2.ellipse(image, center, (100, 140), 0, 0, 360, (180, 150, 120), -1)
        
        return image
    
    def _create_test_landmarks(self) -> List[Point3D]:
        """테스트용 랜드마크 생성"""
        landmarks = []
        center_x, center_y = 320, 240
        
        for i in range(468):
            angle = (i / 468.0) * 2 * np.pi
            radius_x = 80 + np.random.normal(0, 5)
            radius_y = 110 + np.random.normal(0, 5)
            
            x = center_x + radius_x * np.cos(angle)
            y = center_y + radius_y * np.sin(angle)
            z = np.random.normal(0, 2)
            
            landmarks.append(Point3D(x, y, z))
        
        return landmarks
    
    def test_surgery_first_priority(self):
        """성형 우선 적용 테스트"""
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.6)
        )
        surgery_config = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.2)
        )
        
        integrated_config = IntegratedConfig(
            makeup_config=makeup_config,
            surgery_config=surgery_config,
            effect_priority=EffectPriority.SURGERY_FIRST
        )
        
        result = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        self.assertTrue(result.is_successful())
        self.assertIsNotNone(result.surgery_result)
        self.assertIsNotNone(result.makeup_result)
        self.assertGreater(len(result.applied_effects), 0)
    
    def test_makeup_first_priority(self):
        """메이크업 우선 적용 테스트"""
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.5)
        )
        surgery_config = SurgeryConfig(
            eyes=EyeConfig(size_adjustment=0.3)
        )
        
        integrated_config = IntegratedConfig(
            makeup_config=makeup_config,
            surgery_config=surgery_config,
            effect_priority=EffectPriority.MAKEUP_FIRST
        )
        
        result = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        self.assertTrue(result.is_successful())
        self.assertIsNotNone(result.makeup_result)
        self.assertIsNotNone(result.surgery_result)
    
    def test_conflict_detection_and_resolution(self):
        """충돌 감지 및 해결 테스트"""
        makeup_config = MakeupConfig(
            blush=BlushConfig(color=Color(255, 100, 100), intensity=0.8)
        )
        surgery_config = SurgeryConfig(
            cheekbones=CheekboneConfig(width_adjustment=0.5)  # 큰 변화로 충돌 유발
        )
        
        integrated_config = IntegratedConfig(
            makeup_config=makeup_config,
            surgery_config=surgery_config,
            conflict_resolution=ConflictResolution.BLEND
        )
        
        result = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        self.assertTrue(result.is_successful())
        self.assertGreater(len(result.conflicts_detected), 0)
        self.assertIn("blush_cheekbone_conflict", result.conflicts_detected)
    
    def test_caching_functionality(self):
        """캐싱 기능 테스트"""
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(200, 50, 50), opacity=0.7)
        )
        
        integrated_config = IntegratedConfig(
            makeup_config=makeup_config,
            enable_caching=True
        )
        
        # 첫 번째 실행
        start_time = time.time()
        result1 = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        first_time = time.time() - start_time
        
        # 두 번째 실행 (캐시 사용)
        start_time = time.time()
        result2 = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        second_time = time.time() - start_time
        
        # 캐시 사용으로 더 빨라야 함
        self.assertLess(second_time, first_time * 0.8)  # 20% 이상 빨라야 함
    
    def test_quality_assessment(self):
        """품질 평가 테스트"""
        # 적당한 변화
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(210, 170, 130), coverage=0.3)
        )
        
        integrated_config = IntegratedConfig(
            makeup_config=makeup_config,
            quality_threshold=0.6
        )
        
        result = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        self.assertTrue(result.is_successful())
        self.assertGreater(result.quality_score, 0.0)
        self.assertLessEqual(result.quality_score, 1.0)
    
    def test_no_effects_config(self):
        """효과 없는 설정 테스트"""
        integrated_config = IntegratedConfig()  # 빈 설정
        
        result = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 효과가 없어도 성공적으로 처리되어야 함
        self.assertIsNotNone(result.final_image)
        self.assertEqual(len(result.applied_effects), 0)
    
    def test_cache_statistics(self):
        """캐시 통계 테스트"""
        stats = self.engine.get_cache_stats()
        
        self.assertIn("cache_size", stats)
        self.assertIn("max_size", stats)
        self.assertIsInstance(stats["cache_size"], int)
        self.assertIsInstance(stats["max_size"], int)
    
    def test_cache_clear(self):
        """캐시 초기화 테스트"""
        # 캐시에 데이터 추가
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.5)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config, enable_caching=True)
        
        self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 캐시 초기화
        self.engine.clear_cache()
        
        # 캐시가 비어있는지 확인
        stats = self.engine.get_cache_stats()
        self.assertEqual(stats["cache_size"], 0)


class TestIntegratedEnginePerformance(unittest.TestCase):
    """통합 엔진 성능 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = IntegratedEngine()
        self.test_image = np.ones((480, 640, 3), dtype=np.uint8) * 128
        self.test_landmarks = [Point3D(float(i), float(i), 0.0) for i in range(468)]
    
    def test_performance_makeup_only(self):
        """메이크업만 적용 성능 테스트"""
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4),
            lipstick=LipstickConfig(color=Color(200, 50, 50), opacity=0.6),
            blush=BlushConfig(color=Color(255, 100, 100), intensity=0.5)
        )
        
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        start_time = time.time()
        result = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        processing_time = time.time() - start_time
        
        self.assertTrue(result.is_successful())
        self.assertLess(processing_time, 5.0)  # 5초 이내
    
    def test_performance_surgery_only(self):
        """성형만 적용 성능 테스트"""
        surgery_config = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.2, width_adjustment=-0.1),
            eyes=EyeConfig(size_adjustment=0.3),
            jawline=JawlineConfig(width_adjustment=-0.2)
        )
        
        integrated_config = IntegratedConfig(surgery_config=surgery_config)
        
        start_time = time.time()
        result = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        processing_time = time.time() - start_time
        
        self.assertTrue(result.is_successful())
        self.assertLess(processing_time, 10.0)  # 10초 이내
    
    def test_performance_full_integration(self):
        """전체 통합 효과 성능 테스트"""
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4),
            lipstick=LipstickConfig(color=Color(200, 50, 50), opacity=0.6),
            eyeshadow=EyeshadowConfig(primary_color=Color(100, 50, 150), opacity=0.5),
            blush=BlushConfig(color=Color(255, 100, 100), intensity=0.5)
        )
        
        surgery_config = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.2, width_adjustment=-0.1),
            eyes=EyeConfig(size_adjustment=0.2, shape_adjustment=0.1),
            jawline=JawlineConfig(width_adjustment=-0.1, angle_adjustment=0.1),
            cheekbones=CheekboneConfig(height_adjustment=-0.1, width_adjustment=-0.1)
        )
        
        integrated_config = IntegratedConfig(
            makeup_config=makeup_config,
            surgery_config=surgery_config,
            effect_priority=EffectPriority.SURGERY_FIRST
        )
        
        start_time = time.time()
        result = self.engine.apply_integrated_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        processing_time = time.time() - start_time
        
        self.assertTrue(result.is_successful())
        self.assertLess(processing_time, 15.0)  # 15초 이내
        self.assertGreater(len(result.applied_effects), 0)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)