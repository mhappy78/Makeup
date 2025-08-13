"""
성형 시뮬레이션 엔진 테스트
"""
import unittest
import numpy as np
import time
from typing import List
import cv2

from models.core import Point3D, Vector3D
from models.surgery import (
    SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig,
    FeatureModification, FeatureType, ModificationType
)
from engines.surgery_engine import (
    RealtimeSurgeryEngine, MeshWarper, ThinPlateSpline, SurgeryResult
)


class TestThinPlateSpline(unittest.TestCase):
    """Thin Plate Spline 알고리즘 테스트"""
    
    def setUp(self):
        """TPS 테스트 설정"""
        # 간단한 제어점 설정
        self.source_points = np.array([
            [0, 0], [100, 0], [100, 100], [0, 100]
        ])
        self.target_points = np.array([
            [10, 10], [90, 10], [90, 90], [10, 90]
        ])
    
    def test_tps_initialization(self):
        """TPS 초기화 테스트"""
        tps = ThinPlateSpline(self.source_points, self.target_points)
        
        self.assertEqual(tps.n_points, 4)
        self.assertIsNotNone(tps.weights)
        self.assertEqual(tps.weights.shape, (7, 2))  # n_points + 3, 2
    
    def test_tps_transform_identity(self):
        """TPS 항등 변환 테스트"""
        # 동일한 점들로 TPS 생성 (변형 없음)
        tps = ThinPlateSpline(self.source_points, self.source_points)
        
        # 원본 점들을 변형해도 거의 동일해야 함
        transformed = tps.transform_points(self.source_points)
        
        for orig, trans in zip(self.source_points, transformed):
            np.testing.assert_allclose(orig, trans, atol=1e-10)
    
    def test_tps_transform_simple(self):
        """TPS 간단한 변형 테스트"""
        tps = ThinPlateSpline(self.source_points, self.target_points)
        
        # 제어점들이 올바르게 변형되는지 확인
        transformed = tps.transform_points(self.source_points)
        
        for target, trans in zip(self.target_points, transformed):
            np.testing.assert_allclose(target, trans, atol=1e-6)
    
    def test_tps_interpolation(self):
        """TPS 보간 테스트"""
        tps = ThinPlateSpline(self.source_points, self.target_points)
        
        # 중간점 변형 테스트
        middle_point = np.array([[50, 50]])
        transformed = tps.transform_points(middle_point)
        
        # 변형된 점이 합리적인 범위 내에 있는지 확인
        self.assertTrue(0 <= transformed[0, 0] <= 100)
        self.assertTrue(0 <= transformed[0, 1] <= 100)


class TestMeshWarper(unittest.TestCase):
    """메시 워퍼 테스트"""
    
    def setUp(self):
        """메시 워퍼 테스트 설정"""
        self.warper = MeshWarper()
        
        # 테스트용 랜드마크 생성 (468개)
        self.landmarks = []
        for i in range(468):
            x = 320 + np.random.randint(-150, 150)
            y = 240 + np.random.randint(-120, 120)
            z = np.random.uniform(-10, 10)
            self.landmarks.append(Point3D(x, y, z))
        
        # 테스트 이미지
        self.test_image = np.ones((480, 640, 3), dtype=np.uint8) * 128
    
    def test_feature_indices_definition(self):
        """특징별 인덱스 정의 테스트"""
        # 모든 특징 타입에 대한 인덱스가 정의되어 있는지 확인
        expected_features = [FeatureType.NOSE, FeatureType.EYES, 
                           FeatureType.JAWLINE, FeatureType.CHEEKBONES]
        
        for feature in expected_features:
            self.assertIn(feature, self.warper.feature_indices)
            self.assertGreater(len(self.warper.feature_indices[feature]), 0)
    
    def test_create_control_points(self):
        """제어점 생성 테스트"""
        # 코 제어점 생성
        nose_points = self.warper.create_control_points(self.landmarks, FeatureType.NOSE)
        
        self.assertIsInstance(nose_points, list)
        self.assertGreater(len(nose_points), 0)
        
        # 모든 포인트가 Point3D 인스턴스인지 확인
        for point in nose_points:
            self.assertIsInstance(point, Point3D)
    
    def test_create_face_mesh(self):
        """얼굴 메시 생성 테스트"""
        mesh_points = self.warper.create_face_mesh(self.landmarks, self.test_image.shape)
        
        self.assertIsInstance(mesh_points, np.ndarray)
        self.assertEqual(mesh_points.shape[1], 2)  # x, y 좌표
        self.assertGreater(mesh_points.shape[0], len(self.landmarks))  # 경계점 포함
    
    def test_apply_feature_modification(self):
        """특징 변형 적용 테스트"""
        # 코 높이 증가 변형
        modification = FeatureModification(
            feature_type=FeatureType.NOSE,
            modification_type=ModificationType.LIFT,
            modification_vector=Vector3D(0, -5, 0),
            intensity=0.5,
            natural_limit=0.8
        )
        
        modified_landmarks = self.warper.apply_feature_modification(
            self.landmarks, modification
        )
        
        self.assertEqual(len(modified_landmarks), len(self.landmarks))
        
        # 일부 랜드마크가 변경되었는지 확인
        changes_found = False
        for orig, mod in zip(self.landmarks, modified_landmarks):
            if abs(orig.y - mod.y) > 0.1:
                changes_found = True
                break
        
        self.assertTrue(changes_found)
    
    def test_validate_transformation(self):
        """변형 유효성 검증 테스트"""
        # 동일한 랜드마크 (변형 없음)
        validation = self.warper.validate_transformation(self.landmarks, self.landmarks)
        
        self.assertTrue(validation["valid"])
        self.assertTrue(validation["natural"])
        self.assertEqual(validation["avg_distance"], 0.0)
        self.assertEqual(validation["max_distance"], 0.0)
        
        # 약간 변형된 랜드마크
        modified_landmarks = self.landmarks.copy()
        modified_landmarks[0] = Point3D(
            modified_landmarks[0].x + 5,
            modified_landmarks[0].y + 5,
            modified_landmarks[0].z
        )
        
        validation = self.warper.validate_transformation(self.landmarks, modified_landmarks)
        
        self.assertTrue(validation["valid"])
        self.assertGreater(validation["avg_distance"], 0)
        self.assertGreater(validation["max_distance"], 0)
    
    def test_warp_image_with_tps(self):
        """TPS 이미지 워핑 테스트"""
        # 약간 변형된 랜드마크 생성
        modified_landmarks = self.landmarks.copy()
        for i in range(10):  # 처음 10개 점만 변형
            modified_landmarks[i] = Point3D(
                modified_landmarks[i].x + np.random.uniform(-2, 2),
                modified_landmarks[i].y + np.random.uniform(-2, 2),
                modified_landmarks[i].z
            )
        
        warped_image = self.warper.warp_image_with_tps(
            self.test_image, self.landmarks, modified_landmarks
        )
        
        self.assertIsNotNone(warped_image)
        self.assertEqual(warped_image.shape, self.test_image.shape)
        self.assertTrue(np.all(warped_image >= 0))
        self.assertTrue(np.all(warped_image <= 255))


class TestSurgeryEngine(unittest.TestCase):
    """성형 시뮬레이션 엔진 테스트"""
    
    def setUp(self):
        """성형 엔진 테스트 설정"""
        self.engine = RealtimeSurgeryEngine()
        
        # 테스트용 이미지 생성
        self.test_image = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        # 테스트용 랜드마크 생성
        self.landmarks = []
        for i in range(468):
            x = 320 + np.random.randint(-150, 150)
            y = 240 + np.random.randint(-120, 120)
            z = np.random.uniform(-10, 10)
            self.landmarks.append(Point3D(x, y, z))
        
        # 테스트용 성형 설정
        self.nose_config = NoseConfig(
            height_adjustment=0.3,
            width_adjustment=-0.2,
            tip_adjustment=0.1,
            bridge_adjustment=0.2
        )
        
        self.eye_config = EyeConfig(
            size_adjustment=0.2,
            shape_adjustment=0.1,
            position_adjustment=-0.1,
            angle_adjustment=0.15
        )
        
        self.jawline_config = JawlineConfig(
            width_adjustment=-0.3,
            angle_adjustment=0.2,
            length_adjustment=0.1
        )
        
        self.cheekbone_config = CheekboneConfig(
            height_adjustment=-0.2,
            width_adjustment=-0.1,
            prominence_adjustment=0.1
        )
    
    def test_engine_initialization(self):
        """엔진 초기화 테스트"""
        self.assertIsNotNone(self.engine.mesh_warper)
        self.assertIsInstance(self.engine.natural_limits, dict)
        
        # 자연스러운 제한값이 설정되어 있는지 확인
        expected_features = [FeatureType.NOSE, FeatureType.EYES, 
                           FeatureType.JAWLINE, FeatureType.CHEEKBONES]
        
        for feature in expected_features:
            self.assertIn(feature, self.engine.natural_limits)
            self.assertGreater(self.engine.natural_limits[feature], 0)
    
    def test_modify_nose(self):
        """코 성형 테스트"""
        result_image = self.engine.modify_nose(
            self.test_image, self.landmarks, self.nose_config
        )
        
        self.assertIsNotNone(result_image)
        self.assertEqual(result_image.shape, self.test_image.shape)
        self.assertTrue(np.all(result_image >= 0))
        self.assertTrue(np.all(result_image <= 255))
    
    def test_modify_eyes(self):
        """눈 성형 테스트"""
        result_image = self.engine.modify_eyes(
            self.test_image, self.landmarks, self.eye_config
        )
        
        self.assertIsNotNone(result_image)
        self.assertEqual(result_image.shape, self.test_image.shape)
        self.assertTrue(np.all(result_image >= 0))
        self.assertTrue(np.all(result_image <= 255))
    
    def test_modify_jawline(self):
        """턱선 성형 테스트"""
        result_image = self.engine.modify_jawline(
            self.test_image, self.landmarks, self.jawline_config
        )
        
        self.assertIsNotNone(result_image)
        self.assertEqual(result_image.shape, self.test_image.shape)
        self.assertTrue(np.all(result_image >= 0))
        self.assertTrue(np.all(result_image <= 255))
    
    def test_modify_cheekbones(self):
        """광대 성형 테스트"""
        result_image = self.engine.modify_cheekbones(
            self.test_image, self.landmarks, self.cheekbone_config
        )
        
        self.assertIsNotNone(result_image)
        self.assertEqual(result_image.shape, self.test_image.shape)
        self.assertTrue(np.all(result_image >= 0))
        self.assertTrue(np.all(result_image <= 255))
    
    def test_apply_full_surgery(self):
        """전체 성형 시뮬레이션 테스트"""
        surgery_config = SurgeryConfig(
            nose=self.nose_config,
            eyes=self.eye_config,
            jawline=self.jawline_config,
            cheekbones=self.cheekbone_config
        )
        
        result = self.engine.apply_full_surgery(
            self.test_image, self.landmarks, surgery_config
        )
        
        self.assertIsInstance(result, SurgeryResult)
        self.assertTrue(result.is_successful())
        self.assertGreater(len(result.applied_modifications), 0)
        self.assertGreater(result.processing_time, 0)
        self.assertTrue(0.0 <= result.natural_score <= 1.0)
        
        # 결과 이미지 검증
        self.assertIsNotNone(result.image)
        self.assertEqual(result.image.shape, self.test_image.shape)
    
    def test_validate_proportions(self):
        """비율 검증 테스트"""
        # 정상적인 랜드마크
        is_valid = self.engine.validate_proportions(self.landmarks)
        self.assertIsInstance(is_valid, bool)
        
        # 랜드마크 수가 부족한 경우
        short_landmarks = self.landmarks[:100]
        is_valid = self.engine.validate_proportions(short_landmarks)
        self.assertFalse(is_valid)
    
    def test_calculate_natural_score(self):
        """자연스러움 점수 계산 테스트"""
        # 동일한 랜드마크 (변형 없음)
        score = self.engine.calculate_natural_score(self.landmarks, self.landmarks)
        self.assertEqual(score, 1.0)
        
        # 약간 변형된 랜드마크
        modified_landmarks = self.landmarks.copy()
        modified_landmarks[0] = Point3D(
            modified_landmarks[0].x + 5,
            modified_landmarks[0].y + 5,
            modified_landmarks[0].z
        )
        
        score = self.engine.calculate_natural_score(self.landmarks, modified_landmarks)
        self.assertTrue(0.0 <= score < 1.0)
        
        # 크게 변형된 랜드마크
        heavily_modified = self.landmarks.copy()
        for i in range(50):  # 많은 점을 크게 변형
            heavily_modified[i] = Point3D(
                heavily_modified[i].x + 50,
                heavily_modified[i].y + 50,
                heavily_modified[i].z
            )
        
        score = self.engine.calculate_natural_score(self.landmarks, heavily_modified)
        self.assertTrue(0.0 <= score < 0.5)  # 낮은 점수
    
    def test_error_handling_invalid_image(self):
        """잘못된 이미지 입력 오류 처리 테스트"""
        # None 이미지
        result = self.engine.modify_nose(None, self.landmarks, self.nose_config)
        self.assertIsNone(result)
        
        # 잘못된 차원의 이미지
        invalid_image = np.ones((100, 100), dtype=np.uint8)  # 2D 이미지
        result = self.engine.modify_nose(invalid_image, self.landmarks, self.nose_config)
        self.assertTrue(np.array_equal(result, invalid_image))
    
    def test_error_handling_insufficient_landmarks(self):
        """부족한 랜드마크 오류 처리 테스트"""
        short_landmarks = self.landmarks[:100]  # 468개 미만
        
        result = self.engine.modify_nose(self.test_image, short_landmarks, self.nose_config)
        self.assertTrue(np.array_equal(result, self.test_image))
    
    def test_nose_adjustment_methods(self):
        """코 조정 메서드 테스트"""
        landmarks_copy = self.landmarks.copy()
        
        # 각 조정 메서드 테스트
        self.engine._adjust_nose_height(landmarks_copy, 0.5)
        self.engine._adjust_nose_width(landmarks_copy, -0.3)
        self.engine._adjust_nose_tip(landmarks_copy, 0.2)
        self.engine._adjust_nose_bridge(landmarks_copy, 0.4)
        
        # 일부 랜드마크가 변경되었는지 확인
        changes_found = False
        for orig, mod in zip(self.landmarks, landmarks_copy):
            if (abs(orig.x - mod.x) > 0.1 or 
                abs(orig.y - mod.y) > 0.1 or 
                abs(orig.z - mod.z) > 0.1):
                changes_found = True
                break
        
        self.assertTrue(changes_found)
    
    def test_eye_adjustment_methods(self):
        """눈 조정 메서드 테스트"""
        landmarks_copy = self.landmarks.copy()
        
        # 각 조정 메서드 테스트
        self.engine._adjust_eye_size(landmarks_copy, 0.3)
        self.engine._adjust_eye_shape(landmarks_copy, -0.2)
        self.engine._adjust_eye_position(landmarks_copy, 0.1)
        self.engine._adjust_eye_angle(landmarks_copy, 0.25)
        
        # 변경 확인
        changes_found = False
        for orig, mod in zip(self.landmarks, landmarks_copy):
            if (abs(orig.x - mod.x) > 0.1 or 
                abs(orig.y - mod.y) > 0.1):
                changes_found = True
                break
        
        self.assertTrue(changes_found)
    
    def test_performance_single_surgery(self):
        """단일 성형 성능 테스트"""
        start_time = time.time()
        
        result = self.engine.modify_nose(self.test_image, self.landmarks, self.nose_config)
        
        processing_time = time.time() - start_time
        
        # 단일 성형은 0.5초 이내에 처리되어야 함
        self.assertLess(processing_time, 0.5)
        self.assertIsNotNone(result)
    
    def test_performance_full_surgery(self):
        """전체 성형 성능 테스트"""
        surgery_config = SurgeryConfig(
            nose=self.nose_config,
            eyes=self.eye_config,
            jawline=self.jawline_config,
            cheekbones=self.cheekbone_config
        )
        
        start_time = time.time()
        
        result = self.engine.apply_full_surgery(
            self.test_image, self.landmarks, surgery_config
        )
        
        processing_time = time.time() - start_time
        
        # 전체 성형은 2초 이내에 처리되어야 함
        self.assertLess(processing_time, 2.0)
        self.assertTrue(result.is_successful())
    
    def test_natural_score_calculation(self):
        """자연스러움 점수 계산 정확성 테스트"""
        # 다양한 강도의 설정으로 테스트
        configs = [
            # 자연스러운 설정
            SurgeryConfig(
                nose=NoseConfig(height_adjustment=0.1),
                eyes=EyeConfig(size_adjustment=0.05),
                jawline=JawlineConfig(width_adjustment=-0.1),
                cheekbones=CheekboneConfig(height_adjustment=-0.05)
            ),
            # 중간 강도 설정
            SurgeryConfig(
                nose=NoseConfig(height_adjustment=0.5, width_adjustment=-0.3),
                eyes=EyeConfig(size_adjustment=0.3, shape_adjustment=0.2),
                jawline=JawlineConfig(width_adjustment=-0.4, angle_adjustment=0.3),
                cheekbones=CheekboneConfig(height_adjustment=-0.3, width_adjustment=-0.2)
            ),
            # 강한 설정
            SurgeryConfig(
                nose=NoseConfig(height_adjustment=0.8, width_adjustment=-0.7, tip_adjustment=0.6),
                eyes=EyeConfig(size_adjustment=0.7, shape_adjustment=0.5, position_adjustment=-0.4),
                jawline=JawlineConfig(width_adjustment=-0.8, angle_adjustment=0.6, length_adjustment=0.5),
                cheekbones=CheekboneConfig(height_adjustment=-0.7, width_adjustment=-0.6, prominence_adjustment=0.4)
            )
        ]
        
        natural_scores = []
        
        for config in configs:
            result = self.engine.apply_full_surgery(self.test_image, self.landmarks, config)
            natural_scores.append(result.natural_score)
        
        # 강도가 높을수록 자연스러움 점수가 낮아져야 함
        self.assertGreater(natural_scores[0], natural_scores[1])
        self.assertGreater(natural_scores[1], natural_scores[2])
        
        # 모든 점수가 유효한 범위 내에 있어야 함
        for score in natural_scores:
            self.assertTrue(0.0 <= score <= 1.0)


class TestSurgeryEngineIntegration(unittest.TestCase):
    """성형 엔진 통합 테스트"""
    
    def setUp(self):
        """통합 테스트 설정"""
        self.engine = RealtimeSurgeryEngine()
        
        # 더 현실적인 얼굴 이미지 시뮬레이션
        self.realistic_image = self._create_realistic_face_image()
        self.realistic_landmarks = self._create_realistic_landmarks()
    
    def _create_realistic_face_image(self) -> np.ndarray:
        """현실적인 얼굴 이미지 시뮬레이션"""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 얼굴 영역에 피부톤 적용
        center_x, center_y = 320, 240
        for y in range(480):
            for x in range(640):
                # 타원형 얼굴 영역
                if ((x - center_x) / 150) ** 2 + ((y - center_y) / 180) ** 2 <= 1:
                    # 피부톤 (약간의 변화 추가)
                    base_r = 220 + np.random.randint(-20, 20)
                    base_g = 180 + np.random.randint(-15, 15)
                    base_b = 140 + np.random.randint(-10, 10)
                    
                    image[y, x] = [
                        max(0, min(255, base_b)),  # BGR 순서
                        max(0, min(255, base_g)),
                        max(0, min(255, base_r))
                    ]
                else:
                    # 배경
                    image[y, x] = [50, 50, 50]
        
        return image
    
    def _create_realistic_landmarks(self) -> List[Point3D]:
        """현실적인 얼굴 랜드마크 생성"""
        landmarks = []
        center_x, center_y = 320, 240
        
        # MediaPipe 468 포인트 구조를 시뮬레이션
        for i in range(468):
            if i < 17:  # 얼굴 윤곽
                angle = (i / 16) * np.pi
                x = center_x + 120 * np.cos(angle)
                y = center_y + 150 * np.sin(angle)
            elif i < 68:  # 눈썹
                side = 0 if i < 42 else 1
                x = center_x + (-60 + side * 120) + np.random.randint(-10, 10)
                y = center_y - 60 + np.random.randint(-5, 5)
            elif i < 136:  # 눈
                side = 0 if i < 102 else 1
                x = center_x + (-40 + side * 80) + np.random.randint(-15, 15)
                y = center_y - 20 + np.random.randint(-10, 10)
            elif i < 180:  # 코
                x = center_x + np.random.randint(-15, 15)
                y = center_y + np.random.randint(-10, 30)
            elif i < 268:  # 입
                x = center_x + np.random.randint(-30, 30)
                y = center_y + 60 + np.random.randint(-10, 10)
            else:  # 기타 포인트
                x = center_x + np.random.randint(-100, 100)
                y = center_y + np.random.randint(-100, 100)
            
            z = np.random.uniform(-5, 5)
            landmarks.append(Point3D(x, y, z))
        
        return landmarks
    
    def test_realistic_surgery_workflow(self):
        """현실적인 성형 워크플로우 테스트"""
        # 단계별 성형 적용
        result_image = self.realistic_image.copy()
        
        # 1. 코 성형
        nose_config = NoseConfig(height_adjustment=0.3, width_adjustment=-0.2)
        result_image = self.engine.modify_nose(result_image, self.realistic_landmarks, nose_config)
        
        # 2. 눈 성형
        eye_config = EyeConfig(size_adjustment=0.2, shape_adjustment=0.1)
        result_image = self.engine.modify_eyes(result_image, self.realistic_landmarks, eye_config)
        
        # 3. 턱선 성형
        jaw_config = JawlineConfig(width_adjustment=-0.3, angle_adjustment=0.2)
        result_image = self.engine.modify_jawline(result_image, self.realistic_landmarks, jaw_config)
        
        # 4. 광대 성형
        cheek_config = CheekboneConfig(height_adjustment=-0.2, width_adjustment=-0.1)
        result_image = self.engine.modify_cheekbones(result_image, self.realistic_landmarks, cheek_config)
        
        # 결과 검증
        self.assertFalse(np.array_equal(result_image, self.realistic_image))
        self.assertEqual(result_image.shape, self.realistic_image.shape)
        
        # 이미지 품질 검증
        self.assertTrue(np.all(result_image >= 0))
        self.assertTrue(np.all(result_image <= 255))
    
    def test_surgery_intensity_progression(self):
        """성형 강도 단계별 테스트"""
        intensities = [0.1, 0.3, 0.5, 0.7, 0.9]
        results = []
        
        for intensity in intensities:
            config = NoseConfig(height_adjustment=intensity)
            
            result = self.engine.modify_nose(
                self.realistic_image, self.realistic_landmarks, config
            )
            results.append(result)
        
        # 강도가 높을수록 더 많은 변화가 있어야 함
        for i in range(1, len(results)):
            diff_prev = np.sum(np.abs(results[i-1].astype(int) - self.realistic_image.astype(int)))
            diff_curr = np.sum(np.abs(results[i].astype(int) - self.realistic_image.astype(int)))
            
            # 강도가 높을수록 변화량이 커야 함 (단, 워핑 특성상 항상 선형적이지는 않음)
            self.assertGreaterEqual(diff_curr * 0.8, diff_prev, 
                                   f"강도 {intensities[i]}에서 예상보다 변화가 적음")


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)