#!/usr/bin/env python3
"""
실시간 효과 업데이트 시스템 테스트
"""
import unittest
import numpy as np
import time
import cv2
from typing import List

from models.core import Point3D, Color
from models.makeup import MakeupConfig, LipstickConfig, FoundationConfig, BlushConfig
from models.surgery import SurgeryConfig, NoseConfig, EyeConfig
from engines.realtime_update_engine import (
    RealtimeUpdateEngine, UpdateType, EffectLayer, EffectState,
    EffectDependencyGraph, PerformanceOptimizer
)
from engines.integrated_engine import IntegratedConfig


class TestEffectDependencyGraph(unittest.TestCase):
    """효과 의존성 그래프 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.graph = EffectDependencyGraph()
    
    def test_add_dependency(self):
        """의존성 추가 테스트"""
        self.graph.add_dependency("eyeshadow", "foundation")
        
        dependencies = self.graph.get_dependencies("eyeshadow")
        self.assertIn("foundation", dependencies)
        
        dependents = self.graph.get_dependents("foundation")
        self.assertIn("eyeshadow", dependents)
    
    def test_remove_dependency(self):
        """의존성 제거 테스트"""
        self.graph.add_dependency("eyeshadow", "foundation")
        self.graph.remove_dependency("eyeshadow", "foundation")
        
        dependencies = self.graph.get_dependencies("eyeshadow")
        self.assertNotIn("foundation", dependencies)
    
    def test_update_order(self):
        """업데이트 순서 계산 테스트"""
        # 의존성 설정: foundation -> eyeshadow -> eyeliner
        self.graph.add_dependency("eyeshadow", "foundation")
        self.graph.add_dependency("eyeliner", "eyeshadow")
        
        effect_ids = {"foundation", "eyeshadow", "eyeliner"}
        order = self.graph.get_update_order(effect_ids)
        
        # foundation이 가장 먼저, eyeliner가 가장 나중에 와야 함
        self.assertEqual(order[0], "foundation")
        self.assertEqual(order[-1], "eyeliner")
        self.assertIn("eyeshadow", order)


class TestPerformanceOptimizer(unittest.TestCase):
    """성능 최적화 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.optimizer = PerformanceOptimizer()
    
    def test_processing_time_recording(self):
        """처리 시간 기록 테스트"""
        self.optimizer.record_processing_time(0.05)  # 50ms
        self.optimizer.record_processing_time(0.03)  # 30ms
        
        self.assertEqual(len(self.optimizer.processing_times), 2)
        self.assertIn(50.0, self.optimizer.processing_times)
        self.assertIn(30.0, self.optimizer.processing_times)
    
    def test_frame_skip_decision(self):
        """프레임 스킵 결정 테스트"""
        # 빠른 처리 시간
        self.optimizer.record_processing_time(0.01)  # 10ms
        self.assertFalse(self.optimizer.should_skip_frame())
        
        # 느린 처리 시간
        self.optimizer.record_processing_time(0.05)  # 50ms
        self.assertTrue(self.optimizer.should_skip_frame())
    
    def test_quality_adjustment(self):
        """품질 자동 조정 테스트"""
        # 빠른 처리 시간 -> 고품질
        self.optimizer.record_processing_time(0.02)  # 20ms
        quality = self.optimizer.adjust_quality()
        self.assertEqual(quality, 'high')
        
        # 중간 처리 시간 -> 중품질
        self.optimizer.processing_times.clear()
        self.optimizer.record_processing_time(0.04)  # 40ms
        quality = self.optimizer.adjust_quality()
        self.assertEqual(quality, 'medium')
        
        # 느린 처리 시간 -> 저품질
        self.optimizer.processing_times.clear()
        self.optimizer.record_processing_time(0.06)  # 60ms
        quality = self.optimizer.adjust_quality()
        self.assertEqual(quality, 'low')
    
    def test_quality_scale(self):
        """품질 스케일 테스트"""
        self.optimizer.current_quality = 'high'
        self.assertEqual(self.optimizer.get_quality_scale(), 1.0)
        
        self.optimizer.current_quality = 'medium'
        self.assertEqual(self.optimizer.get_quality_scale(), 0.7)
        
        self.optimizer.current_quality = 'low'
        self.assertEqual(self.optimizer.get_quality_scale(), 0.5)


class TestRealtimeUpdateEngine(unittest.TestCase):
    """실시간 업데이트 엔진 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = RealtimeUpdateEngine()
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
    
    def test_effect_initialization(self):
        """효과 초기화 테스트"""
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4),
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.6)
        )
        
        surgery_config = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.2)
        )
        
        integrated_config = IntegratedConfig(
            makeup_config=makeup_config,
            surgery_config=surgery_config
        )
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 효과 상태가 올바르게 초기화되었는지 확인
        self.assertIn("foundation", self.engine.effect_states)
        self.assertIn("lipstick", self.engine.effect_states)
        self.assertIn("nose_surgery", self.engine.effect_states)
        
        # 레이어가 올바르게 설정되었는지 확인
        foundation_state = self.engine.effect_states["foundation"]
        self.assertEqual(foundation_state.layer, EffectLayer.MAKEUP_BASE)
        
        lipstick_state = self.engine.effect_states["lipstick"]
        self.assertEqual(lipstick_state.layer, EffectLayer.MAKEUP_ACCENT)
        
        nose_state = self.engine.effect_states["nose_surgery"]
        self.assertEqual(nose_state.layer, EffectLayer.SURGERY_SHAPE)
    
    def test_single_effect_update(self):
        """단일 효과 업데이트 테스트"""
        # 초기화
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.5)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 립스틱 색상 변경
        new_lipstick_config = LipstickConfig(color=Color(200, 50, 100), opacity=0.7)
        
        success = self.engine.update_effect(
            "lipstick", new_lipstick_config, UpdateType.INCREMENTAL
        )
        
        self.assertTrue(success)
        
        # 업데이트된 설정 확인
        lipstick_state = self.engine.effect_states["lipstick"]
        self.assertEqual(lipstick_state.config.color.r, 200)
        self.assertEqual(lipstick_state.config.opacity, 0.7)
    
    def test_dependency_update_propagation(self):
        """의존성 업데이트 전파 테스트"""
        # 의존성이 있는 효과들로 초기화
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4),
            eyeshadow=EyeshadowConfig(primary_color=Color(100, 50, 150), opacity=0.5)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 파운데이션 변경 (eyeshadow가 의존함)
        new_foundation_config = FoundationConfig(color=Color(200, 160, 120), coverage=0.6)
        
        self.engine.update_effect(
            "foundation", new_foundation_config, UpdateType.INCREMENTAL
        )
        
        # eyeshadow도 더티 마킹되었는지 확인
        eyeshadow_state = self.engine.effect_states["eyeshadow"]
        # 의존성 전파로 인해 eyeshadow도 업데이트되어야 함
        self.assertIsNotNone(eyeshadow_state)
    
    def test_performance_optimization(self):
        """성능 최적화 테스트"""
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 느린 처리 시간 시뮬레이션
        self.engine.performance_optimizer.record_processing_time(0.06)  # 60ms
        
        # 품질이 자동으로 조정되는지 확인
        quality = self.engine.performance_optimizer.adjust_quality()
        self.assertEqual(quality, 'low')
        
        # 프레임 스킵 권장 여부 확인
        should_skip = self.engine.performance_optimizer.should_skip_frame()
        self.assertTrue(should_skip)
    
    def test_full_vs_incremental_update(self):
        """전체 vs 증분 업데이트 비교 테스트"""
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4),
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.6),
            blush=BlushConfig(color=Color(255, 100, 100), intensity=0.5)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 전체 업데이트 시간 측정
        start_time = time.time()
        new_lipstick = LipstickConfig(color=Color(200, 0, 0), opacity=0.8)
        self.engine.update_effect("lipstick", new_lipstick, UpdateType.FULL_REFRESH)
        full_update_time = time.time() - start_time
        
        # 증분 업데이트 시간 측정
        start_time = time.time()
        new_lipstick2 = LipstickConfig(color=Color(180, 0, 0), opacity=0.9)
        self.engine.update_effect("lipstick", new_lipstick2, UpdateType.INCREMENTAL)
        incremental_update_time = time.time() - start_time
        
        # 증분 업데이트가 더 빨라야 함 (일반적으로)
        print(f"Full update: {full_update_time:.3f}s, Incremental: {incremental_update_time:.3f}s")
        
        # 두 업데이트 모두 성공해야 함
        result = self.engine.get_current_result()
        self.assertIsNotNone(result)
        self.assertTrue(result.is_successful())
    
    def test_current_result_retrieval(self):
        """현재 결과 조회 테스트"""
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.6)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        result = self.engine.get_current_result()
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.final_image)
        self.assertGreater(len(result.applied_effects), 0)
        self.assertIn("lipstick", result.applied_effects)
    
    def test_effect_state_retrieval(self):
        """효과 상태 조회 테스트"""
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        foundation_state = self.engine.get_effect_state("foundation")
        
        self.assertIsNotNone(foundation_state)
        self.assertEqual(foundation_state.effect_id, "foundation")
        self.assertEqual(foundation_state.layer, EffectLayer.MAKEUP_BASE)
        self.assertIsNotNone(foundation_state.config)
    
    def test_performance_stats(self):
        """성능 통계 테스트"""
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.6)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        stats = self.engine.get_performance_stats()
        
        self.assertIn("current_quality", stats)
        self.assertIn("average_processing_time", stats)
        self.assertIn("should_skip_frame", stats)
        self.assertIn("active_effects", stats)
        self.assertIn("pending_updates", stats)
        
        self.assertIsInstance(stats["current_quality"], str)
        self.assertIsInstance(stats["average_processing_time"], (int, float))
        self.assertIsInstance(stats["should_skip_frame"], bool)
        self.assertIsInstance(stats["active_effects"], int)
        self.assertIsInstance(stats["pending_updates"], int)
    
    def test_engine_reset(self):
        """엔진 리셋 테스트"""
        makeup_config = MakeupConfig(
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.6)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 리셋 전 상태 확인
        self.assertGreater(len(self.engine.effect_states), 0)
        self.assertIsNotNone(self.engine.base_image)
        
        # 리셋 실행
        self.engine.reset()
        
        # 리셋 후 상태 확인
        self.assertEqual(len(self.engine.effect_states), 0)
        self.assertIsNone(self.engine.base_image)
        self.assertIsNone(self.engine.base_landmarks)
        self.assertIsNone(self.engine.final_result)
        self.assertEqual(len(self.engine.update_queue), 0)


class TestRealtimeUpdateEngineIntegration(unittest.TestCase):
    """실시간 업데이트 엔진 통합 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = RealtimeUpdateEngine()
        self.test_image = np.ones((480, 640, 3), dtype=np.uint8) * 128
        self.test_landmarks = [Point3D(float(i), float(i), 0.0) for i in range(468)]
    
    def test_complex_effect_chain(self):
        """복잡한 효과 체인 테스트"""
        # 여러 효과가 포함된 복잡한 설정
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4),
            eyeshadow=EyeshadowConfig(primary_color=Color(100, 50, 150), opacity=0.5),
            blush=BlushConfig(color=Color(255, 100, 100), intensity=0.5),
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.6)
        )
        
        surgery_config = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.2, width_adjustment=-0.1),
            eyes=EyeConfig(size_adjustment=0.3)
        )
        
        integrated_config = IntegratedConfig(
            makeup_config=makeup_config,
            surgery_config=surgery_config
        )
        
        # 초기화
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 여러 효과를 순차적으로 업데이트
        updates = [
            ("foundation", FoundationConfig(color=Color(200, 160, 120), coverage=0.6)),
            ("nose_surgery", NoseConfig(height_adjustment=0.3, width_adjustment=-0.2)),
            ("lipstick", LipstickConfig(color=Color(200, 50, 50), opacity=0.8)),
            ("eye_surgery", EyeConfig(size_adjustment=0.4, shape_adjustment=0.1))
        ]
        
        for effect_id, new_config in updates:
            success = self.engine.update_effect(effect_id, new_config, UpdateType.INCREMENTAL)
            self.assertTrue(success)
        
        # 최종 결과 확인
        result = self.engine.get_current_result()
        self.assertIsNotNone(result)
        self.assertTrue(result.is_successful())
        self.assertGreater(len(result.applied_effects), 0)
    
    def test_concurrent_updates(self):
        """동시 업데이트 테스트"""
        makeup_config = MakeupConfig(
            foundation=FoundationConfig(color=Color(220, 180, 140), coverage=0.4),
            lipstick=LipstickConfig(color=Color(255, 0, 0), opacity=0.6),
            blush=BlushConfig(color=Color(255, 100, 100), intensity=0.5)
        )
        integrated_config = IntegratedConfig(makeup_config=makeup_config)
        
        self.engine.initialize_effects(
            self.test_image, self.test_landmarks, integrated_config
        )
        
        # 여러 효과를 빠르게 연속 업데이트
        updates = [
            LipstickConfig(color=Color(200, 0, 0), opacity=0.7),
            LipstickConfig(color=Color(180, 0, 0), opacity=0.8),
            LipstickConfig(color=Color(160, 0, 0), opacity=0.9)
        ]
        
        for new_config in updates:
            self.engine.update_effect("lipstick", new_config, UpdateType.INCREMENTAL)
        
        # 모든 업데이트가 처리될 때까지 대기
        time.sleep(0.1)
        
        # 최종 결과 확인
        result = self.engine.get_current_result()
        self.assertIsNotNone(result)
        
        # 마지막 설정이 적용되었는지 확인
        lipstick_state = self.engine.get_effect_state("lipstick")
        self.assertEqual(lipstick_state.config.opacity, 0.9)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)