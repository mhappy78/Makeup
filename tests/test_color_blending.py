"""
색상 블렌딩 시스템 단위 테스트
"""
import unittest
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from models.core import Color, Point3D
from models.makeup import BlendMode, LipstickConfig, EyeshadowConfig, EyeshadowStyle, BlushConfig
from engines.makeup_engine import ColorBlender, RealtimeMakeupEngine


class TestColorBlender(unittest.TestCase):
    """ColorBlender 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.base_color = Color(200, 150, 100, 255)  # 베이지 색상
        self.overlay_color = Color(255, 100, 100, 255)  # 빨간 색상
        self.skin_tone = Color(220, 180, 140, 255)  # 기본 피부톤
    
    def test_normal_blend_zero_opacity(self):
        """투명도 0일 때 베이스 색상 반환 테스트"""
        result = ColorBlender.blend_colors(
            self.base_color, self.overlay_color, BlendMode.NORMAL, 0.0
        )
        self.assertEqual(result.r, self.base_color.r)
        self.assertEqual(result.g, self.base_color.g)
        self.assertEqual(result.b, self.base_color.b)
        self.assertEqual(result.a, self.base_color.a)
    
    def test_normal_blend_full_opacity(self):
        """투명도 1일 때 오버레이 색상 반환 테스트"""
        result = ColorBlender.blend_colors(
            self.base_color, self.overlay_color, BlendMode.NORMAL, 1.0
        )
        self.assertEqual(result.r, self.overlay_color.r)
        self.assertEqual(result.g, self.overlay_color.g)
        self.assertEqual(result.b, self.overlay_color.b)
    
    def test_normal_blend_half_opacity(self):
        """투명도 0.5일 때 중간값 테스트"""
        result = ColorBlender.blend_colors(
            self.base_color, self.overlay_color, BlendMode.NORMAL, 0.5
        )
        expected_r = int((self.base_color.r + self.overlay_color.r) / 2)
        expected_g = int((self.base_color.g + self.overlay_color.g) / 2)
        expected_b = int((self.base_color.b + self.overlay_color.b) / 2)
        
        self.assertAlmostEqual(result.r, expected_r, delta=1)
        self.assertAlmostEqual(result.g, expected_g, delta=1)
        self.assertAlmostEqual(result.b, expected_b, delta=1)
    
    def test_multiply_blend(self):
        """Multiply 블렌딩 모드 테스트"""
        result = ColorBlender.blend_colors(
            self.base_color, self.overlay_color, BlendMode.MULTIPLY, 1.0
        )
        # Multiply는 어두운 효과를 만들어야 함
        self.assertLessEqual(result.r, self.base_color.r)
        self.assertLessEqual(result.g, self.base_color.g)
        self.assertLessEqual(result.b, self.base_color.b)
    
    def test_overlay_blend(self):
        """Overlay 블렌딩 모드 테스트"""
        result = ColorBlender.blend_colors(
            self.base_color, self.overlay_color, BlendMode.OVERLAY, 0.5
        )
        # 결과가 유효한 색상 범위 내에 있는지 확인
        self.assertTrue(0 <= result.r <= 255)
        self.assertTrue(0 <= result.g <= 255)
        self.assertTrue(0 <= result.b <= 255)
        self.assertTrue(0 <= result.a <= 255)
    
    def test_skin_tone_matching_warm(self):
        """따뜻한 피부톤과의 조화 테스트"""
        warm_skin = Color(230, 190, 150, 255)  # 따뜻한 피부톤
        makeup_color = Color(200, 100, 150, 255)  # 핑크 메이크업
        
        result = ColorBlender.match_skin_tone(makeup_color, warm_skin, 0.5)
        
        # 따뜻한 피부톤에 맞춰 빨간색이 증가하고 파란색이 감소해야 함
        self.assertGreaterEqual(result.r, makeup_color.r)
        self.assertLessEqual(result.b, makeup_color.b)
    
    def test_skin_tone_matching_cool(self):
        """차가운 피부톤과의 조화 테스트"""
        cool_skin = Color(200, 180, 200, 255)  # 차가운 피부톤
        makeup_color = Color(200, 100, 150, 255)  # 핑크 메이크업
        
        result = ColorBlender.match_skin_tone(makeup_color, cool_skin, 0.5)
        
        # 차가운 피부톤에 맞춰 파란색이 증가하고 빨간색이 감소해야 함
        self.assertLessEqual(result.r, makeup_color.r)
        self.assertGreaterEqual(result.b, makeup_color.b)
    
    def test_intensity_adjustment(self):
        """강도 조절 기능 테스트"""
        original_color = Color(255, 100, 100, 255)
        
        # 강도 0.5로 조절
        result = ColorBlender.adjust_intensity(original_color, 0.5)
        expected_alpha = int(original_color.a * 0.5)
        
        self.assertEqual(result.r, original_color.r)
        self.assertEqual(result.g, original_color.g)
        self.assertEqual(result.b, original_color.b)
        self.assertEqual(result.a, expected_alpha)
    
    def test_intensity_adjustment_bounds(self):
        """강도 조절 경계값 테스트"""
        original_color = Color(255, 100, 100, 255)
        
        # 강도가 범위를 벗어날 때 클램핑 테스트
        result_negative = ColorBlender.adjust_intensity(original_color, -0.5)
        self.assertEqual(result_negative.a, 0)
        
        result_over = ColorBlender.adjust_intensity(original_color, 1.5)
        self.assertEqual(result_over.a, original_color.a)
    
    def test_color_range_validation(self):
        """색상 값 범위 검증 테스트"""
        # 극단적인 색상 값으로 테스트
        extreme_base = Color(0, 0, 0, 255)
        extreme_overlay = Color(255, 255, 255, 255)
        
        result = ColorBlender.blend_colors(
            extreme_base, extreme_overlay, BlendMode.NORMAL, 0.5
        )
        
        # 결과가 유효한 범위 내에 있는지 확인
        self.assertTrue(0 <= result.r <= 255)
        self.assertTrue(0 <= result.g <= 255)
        self.assertTrue(0 <= result.b <= 255)
        self.assertTrue(0 <= result.a <= 255)
    
    def test_blend_mode_fallback(self):
        """지원하지 않는 블렌드 모드에 대한 폴백 테스트"""
        # 지원하지 않는 블렌드 모드 사용
        result = ColorBlender.blend_colors(
            self.base_color, self.overlay_color, BlendMode.SOFT_LIGHT, 0.5
        )
        
        # Normal 블렌딩과 같은 결과가 나와야 함
        expected = ColorBlender.blend_colors(
            self.base_color, self.overlay_color, BlendMode.NORMAL, 0.5
        )
        
        self.assertEqual(result.r, expected.r)
        self.assertEqual(result.g, expected.g)
        self.assertEqual(result.b, expected.b)


class TestLipstickApplication(unittest.TestCase):
    """립스틱 적용 기능 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = RealtimeMakeupEngine()
        
        # 테스트용 이미지 생성 (100x100 RGB)
        self.test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # 회색 이미지
        
        # 기본 랜드마크 (입술 영역 중심)
        self.landmarks = []
        for i in range(500):  # MediaPipe는 468개 랜드마크를 사용하지만 테스트용으로 500개 생성
            if i in [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]:  # 상단 입술
                self.landmarks.append(Point3D(45 + (i % 10), 70, 0))
            elif i in [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]:  # 하단 입술
                self.landmarks.append(Point3D(45 + (i % 10), 80, 0))
            else:
                self.landmarks.append(Point3D(50, 50, 0))  # 기본 위치
        
        # 립스틱 설정
        self.lipstick_config = LipstickConfig(
            color=Color(255, 100, 100, 255),  # 빨간색
            intensity=0.7,
            glossiness=0.3,
            blend_mode=BlendMode.NORMAL
        )
    
    def test_lipstick_application_basic(self):
        """기본 립스틱 적용 테스트"""
        result = self.engine.apply_lipstick(self.test_image, self.landmarks, self.lipstick_config)
        
        # 결과 이미지가 원본과 다른지 확인
        self.assertFalse(np.array_equal(result, self.test_image))
        
        # 이미지 크기가 동일한지 확인
        self.assertEqual(result.shape, self.test_image.shape)
    
    def test_lipstick_application_with_invalid_image(self):
        """잘못된 이미지 입력 테스트"""
        # None 이미지
        result = self.engine.apply_lipstick(None, self.landmarks, self.lipstick_config)
        self.assertIsNone(result)
        
        # 2D 이미지 (그레이스케일)
        gray_image = np.ones((100, 100), dtype=np.uint8) * 128
        result = self.engine.apply_lipstick(gray_image, self.landmarks, self.lipstick_config)
        self.assertTrue(np.array_equal(result, gray_image))
    
    def test_lipstick_intensity_effect(self):
        """립스틱 강도에 따른 효과 테스트"""
        # 낮은 강도
        low_config = LipstickConfig(
            color=Color(255, 100, 100, 255),
            intensity=0.2,
            glossiness=0.3,
            blend_mode=BlendMode.NORMAL
        )
        
        # 높은 강도
        high_config = LipstickConfig(
            color=Color(255, 100, 100, 255),
            intensity=0.9,
            glossiness=0.3,
            blend_mode=BlendMode.NORMAL
        )
        
        result_low = self.engine.apply_lipstick(self.test_image, self.landmarks, low_config)
        result_high = self.engine.apply_lipstick(self.test_image, self.landmarks, high_config)
        
        # 높은 강도가 더 많은 변화를 만들어야 함
        diff_low = np.sum(np.abs(result_low.astype(int) - self.test_image.astype(int)))
        diff_high = np.sum(np.abs(result_high.astype(int) - self.test_image.astype(int)))
        
        self.assertGreater(diff_high, diff_low)
    
    def test_lipstick_glossiness_effect(self):
        """립스틱 광택도에 따른 효과 테스트"""
        # 매트 립스틱
        matte_config = LipstickConfig(
            color=Color(255, 100, 100, 255),
            intensity=0.7,
            glossiness=0.1,
            blend_mode=BlendMode.NORMAL
        )
        
        # 글로시 립스틱
        glossy_config = LipstickConfig(
            color=Color(255, 100, 100, 255),
            intensity=0.7,
            glossiness=0.9,
            blend_mode=BlendMode.NORMAL
        )
        
        result_matte = self.engine.apply_lipstick(self.test_image, self.landmarks, matte_config)
        result_glossy = self.engine.apply_lipstick(self.test_image, self.landmarks, glossy_config)
        
        # 두 결과가 달라야 함 (글로시는 그라데이션 효과 적용)
        self.assertFalse(np.array_equal(result_matte, result_glossy))
    
    def test_lipstick_blend_modes(self):
        """다양한 블렌드 모드 테스트"""
        blend_modes = [BlendMode.NORMAL, BlendMode.MULTIPLY, BlendMode.OVERLAY]
        results = []
        
        for mode in blend_modes:
            config = LipstickConfig(
                color=Color(255, 100, 100, 255),
                intensity=0.7,
                glossiness=0.3,
                blend_mode=mode
            )
            result = self.engine.apply_lipstick(self.test_image, self.landmarks, config)
            results.append(result)
        
        # 모든 블렌드 모드가 다른 결과를 만들어야 함
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                self.assertFalse(np.array_equal(results[i], results[j]))
    
    def test_lip_mask_generation(self):
        """입술 마스크 생성 테스트"""
        mask = self.engine._get_lip_mask(self.test_image, self.landmarks)
        
        # 마스크가 올바른 크기인지 확인
        self.assertEqual(mask.shape, self.test_image.shape[:2])
        
        # 마스크에 0이 아닌 값이 있는지 확인 (입술 영역이 마스킹됨)
        self.assertGreater(np.sum(mask), 0)
        
        # 마스크 값이 0-255 범위 내에 있는지 확인
        self.assertTrue(np.all(mask >= 0))
        self.assertTrue(np.all(mask <= 255))
    
    def test_lip_mask_with_insufficient_landmarks(self):
        """랜드마크가 부족한 경우 마스크 생성 테스트"""
        # 랜드마크가 부족한 경우
        few_landmarks = [Point3D(50, 50, 0) for _ in range(10)]
        
        mask = self.engine._get_lip_mask(self.test_image, few_landmarks)
        
        # 기본 마스크가 생성되어야 함
        self.assertEqual(mask.shape, self.test_image.shape[:2])
        self.assertGreater(np.sum(mask), 0)
    
    def test_gradient_effect(self):
        """그라데이션 효과 테스트"""
        # 기본 마스크 생성
        base_mask = np.zeros((100, 100), dtype=np.uint8)
        base_mask[40:60, 40:60] = 255  # 중앙에 사각형 마스크
        
        # 그라데이션 효과 적용
        gradient_mask = self.engine._apply_gradient_effect(base_mask, 0.5)
        
        # 그라데이션이 적용되어 원본과 달라야 함
        self.assertFalse(np.array_equal(base_mask, gradient_mask))
        
        # 결과 마스크가 올바른 범위 내에 있는지 확인
        self.assertTrue(np.all(gradient_mask >= 0))
        self.assertTrue(np.all(gradient_mask <= 255))



class TestEyeshadowApplication(unittest.TestCase):
    """아이섀도 적용 기능 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = RealtimeMakeupEngine()
        
        # 테스트용 이미지 생성 (100x100 RGB)
        self.test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # 회색 이미지
        
        # 기본 랜드마크 (눈 영역 중심)
        self.landmarks = []
        for i in range(500):  # MediaPipe는 468개 랜드마크를 사용하지만 테스트용으로 500개 생성
            if i in [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]:  # 왼쪽 눈
                self.landmarks.append(Point3D(30 + (i % 10), 35, 0))
            elif i in [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]:  # 오른쪽 눈
                self.landmarks.append(Point3D(60 + (i % 10), 35, 0))
            else:
                self.landmarks.append(Point3D(50, 50, 0))  # 기본 위치
        
        # 아이섀도 설정
        self.eyeshadow_config = EyeshadowConfig(
            colors=[Color(150, 100, 200, 255), Color(200, 150, 100, 255)],  # 보라색, 브라운
            style=EyeshadowStyle.NATURAL,
            intensity=0.6,
            blend_mode=BlendMode.NORMAL,
            shimmer=0.2
        )
    
    def test_eyeshadow_application_basic(self):
        """기본 아이섀도 적용 테스트"""
        result = self.engine.apply_eyeshadow(self.test_image, self.landmarks, self.eyeshadow_config)
        
        # 결과 이미지가 원본과 다른지 확인
        self.assertFalse(np.array_equal(result, self.test_image))
        
        # 이미지 크기가 동일한지 확인
        self.assertEqual(result.shape, self.test_image.shape)
    
    def test_eyeshadow_application_with_invalid_image(self):
        """잘못된 이미지 입력 테스트"""
        # None 이미지
        result = self.engine.apply_eyeshadow(None, self.landmarks, self.eyeshadow_config)
        self.assertIsNone(result)
        
        # 2D 이미지 (그레이스케일)
        gray_image = np.ones((100, 100), dtype=np.uint8) * 128
        result = self.engine.apply_eyeshadow(gray_image, self.landmarks, self.eyeshadow_config)
        self.assertTrue(np.array_equal(result, gray_image))
    
    def test_eyeshadow_empty_colors(self):
        """색상이 없는 경우 테스트"""
        # EyeshadowConfig는 빈 색상 리스트를 허용하지 않으므로 ValueError가 발생해야 함
        with self.assertRaises(ValueError):
            EyeshadowConfig(
                colors=[],
                style=EyeshadowStyle.NATURAL,
                intensity=0.6,
                blend_mode=BlendMode.NORMAL
            )
    
    def test_eyeshadow_intensity_effect(self):
        """아이섀도 강도에 따른 효과 테스트"""
        # 낮은 강도
        low_config = EyeshadowConfig(
            colors=[Color(150, 100, 200, 255)],
            style=EyeshadowStyle.NATURAL,
            intensity=0.2,
            blend_mode=BlendMode.NORMAL
        )
        
        # 높은 강도
        high_config = EyeshadowConfig(
            colors=[Color(150, 100, 200, 255)],
            style=EyeshadowStyle.NATURAL,
            intensity=0.9,
            blend_mode=BlendMode.NORMAL
        )
        
        result_low = self.engine.apply_eyeshadow(self.test_image, self.landmarks, low_config)
        result_high = self.engine.apply_eyeshadow(self.test_image, self.landmarks, high_config)
        
        # 높은 강도가 더 많은 변화를 만들어야 함
        diff_low = np.sum(np.abs(result_low.astype(int) - self.test_image.astype(int)))
        diff_high = np.sum(np.abs(result_high.astype(int) - self.test_image.astype(int)))
        
        self.assertGreater(diff_high, diff_low)
    
    def test_eyeshadow_shimmer_effect(self):
        """시머 효과 테스트"""
        # 매트 아이섀도
        matte_config = EyeshadowConfig(
            colors=[Color(150, 100, 200, 255)],
            style=EyeshadowStyle.NATURAL,
            intensity=0.6,
            blend_mode=BlendMode.NORMAL,
            shimmer=0.0
        )
        
        # 시머 아이섀도
        shimmer_config = EyeshadowConfig(
            colors=[Color(150, 100, 200, 255)],
            style=EyeshadowStyle.NATURAL,
            intensity=0.6,
            blend_mode=BlendMode.NORMAL,
            shimmer=0.8
        )
        
        result_matte = self.engine.apply_eyeshadow(self.test_image, self.landmarks, matte_config)
        result_shimmer = self.engine.apply_eyeshadow(self.test_image, self.landmarks, shimmer_config)
        
        # 두 결과가 달라야 함 (시머는 색상을 밝게 만듦)
        self.assertFalse(np.array_equal(result_matte, result_shimmer))
    
    def test_eyeshadow_styles(self):
        """다양한 아이섀도 스타일 테스트"""
        styles = [EyeshadowStyle.NATURAL, EyeshadowStyle.GRADIENT, EyeshadowStyle.SMOKY]
        results = []
        
        for style in styles:
            config = EyeshadowConfig(
                colors=[Color(150, 100, 200, 255), Color(200, 150, 100, 255)],
                style=style,
                intensity=0.6,
                blend_mode=BlendMode.NORMAL
            )
            result = self.engine.apply_eyeshadow(self.test_image, self.landmarks, config)
            results.append(result)
        
        # 모든 스타일이 다른 결과를 만들어야 함
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                self.assertFalse(np.array_equal(results[i], results[j]))
    
    def test_eyeshadow_blend_modes(self):
        """다양한 블렌드 모드 테스트"""
        blend_modes = [BlendMode.NORMAL, BlendMode.MULTIPLY, BlendMode.OVERLAY]
        results = []
        
        for mode in blend_modes:
            config = EyeshadowConfig(
                colors=[Color(150, 100, 200, 255)],
                style=EyeshadowStyle.NATURAL,
                intensity=0.6,
                blend_mode=mode
            )
            result = self.engine.apply_eyeshadow(self.test_image, self.landmarks, config)
            results.append(result)
        
        # 모든 블렌드 모드가 다른 결과를 만들어야 함
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                self.assertFalse(np.array_equal(results[i], results[j]))
    
    def test_eye_mask_generation(self):
        """눈 마스크 생성 테스트"""
        mask = self.engine._get_eye_mask(self.test_image, self.landmarks, "both")
        
        # 마스크가 올바른 크기인지 확인
        self.assertEqual(mask.shape, self.test_image.shape[:2])
        
        # 마스크에 0이 아닌 값이 있는지 확인 (눈 영역이 마스킹됨)
        self.assertGreater(np.sum(mask), 0)
        
        # 마스크 값이 0-255 범위 내에 있는지 확인
        self.assertTrue(np.all(mask >= 0))
        self.assertTrue(np.all(mask <= 255))
    
    def test_eye_mask_with_insufficient_landmarks(self):
        """랜드마크가 부족한 경우 마스크 생성 테스트"""
        # 랜드마크가 부족한 경우
        few_landmarks = [Point3D(50, 50, 0) for _ in range(10)]
        
        mask = self.engine._get_eye_mask(self.test_image, few_landmarks, "both")
        
        # 기본 마스크가 생성되어야 함
        self.assertEqual(mask.shape, self.test_image.shape[:2])
        self.assertGreater(np.sum(mask), 0)
    
    def test_eyeshadow_gradient_generation(self):
        """아이섀도 그라데이션 생성 테스트"""
        # 기본 마스크 생성
        base_mask = np.zeros((100, 100), dtype=np.uint8)
        base_mask[30:50, 30:70] = 255  # 눈 영역에 사각형 마스크
        
        colors = [Color(150, 100, 200, 255), Color(200, 150, 100, 255)]
        
        # 다양한 스타일로 그라데이션 생성
        for style in [EyeshadowStyle.NATURAL, EyeshadowStyle.GRADIENT, EyeshadowStyle.SMOKY]:
            gradient_masks = self.engine._apply_eyeshadow_gradient(base_mask, colors, style)
            
            # 그라데이션 마스크가 생성되었는지 확인
            self.assertGreater(len(gradient_masks), 0)
            
            # 각 마스크가 올바른 범위 내에 있는지 확인
            for mask_name, mask in gradient_masks.items():
                self.assertTrue(np.all(mask >= 0))
                self.assertTrue(np.all(mask <= 255))
    
    def test_multiple_colors_application(self):
        """다중 색상 아이섀도 적용 테스트"""
        multi_color_config = EyeshadowConfig(
            colors=[
                Color(150, 100, 200, 255),  # 보라색
                Color(200, 150, 100, 255),  # 브라운
                Color(100, 150, 200, 255)   # 블루 (3번째 색상은 무시되어야 함)
            ],
            style=EyeshadowStyle.GRADIENT,
            intensity=0.6,
            blend_mode=BlendMode.NORMAL
        )
        
        result = self.engine.apply_eyeshadow(self.test_image, self.landmarks, multi_color_config)
        
        # 결과 이미지가 원본과 다른지 확인
        self.assertFalse(np.array_equal(result, self.test_image))
        
        # 이미지 크기가 동일한지 확인
        self.assertEqual(result.shape, self.test_image.shape)


class TestBlushApplication(unittest.TestCase):
    """블러셔 적용 기능 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = RealtimeMakeupEngine()
        
        # 테스트용 이미지 생성 (100x100 RGB)
        self.test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # 회색 이미지
        
        # 기본 랜드마크 (볼 영역 중심)
        self.landmarks = []
        for i in range(500):  # MediaPipe는 468개 랜드마크를 사용하지만 테스트용으로 500개 생성
            if i in [116, 117, 118, 119, 120, 121, 126, 142, 36, 205, 206, 207, 213, 192, 147, 187]:  # 왼쪽 볼
                self.landmarks.append(Point3D(25 + (i % 10), 55, 0))
            elif i in [345, 346, 347, 348, 349, 350, 355, 371, 266, 425, 426, 427, 436, 416, 376, 411]:  # 오른쪽 볼
                self.landmarks.append(Point3D(75 + (i % 10), 55, 0))
            else:
                self.landmarks.append(Point3D(50, 50, 0))  # 기본 위치
        
        # 블러셔 설정
        self.blush_config = BlushConfig(
            color=Color(255, 150, 150, 255),  # 핑크색
            intensity=0.6,
            placement="cheeks",
            blend_mode=BlendMode.NORMAL
        )
    
    def test_blush_application_basic(self):
        """기본 블러셔 적용 테스트"""
        result = self.engine.apply_blush(self.test_image, self.landmarks, self.blush_config)
        
        # 결과 이미지가 원본과 다른지 확인
        self.assertFalse(np.array_equal(result, self.test_image))
        
        # 이미지 크기가 동일한지 확인
        self.assertEqual(result.shape, self.test_image.shape)
    
    def test_blush_application_with_invalid_image(self):
        """잘못된 이미지 입력 테스트"""
        # None 이미지
        result = self.engine.apply_blush(None, self.landmarks, self.blush_config)
        self.assertIsNone(result)
        
        # 2D 이미지 (그레이스케일)
        gray_image = np.ones((100, 100), dtype=np.uint8) * 128
        result = self.engine.apply_blush(gray_image, self.landmarks, self.blush_config)
        self.assertTrue(np.array_equal(result, gray_image))
    
    def test_blush_intensity_effect(self):
        """블러셔 강도에 따른 효과 테스트"""
        # 낮은 강도
        low_config = BlushConfig(
            color=Color(255, 150, 150, 255),
            intensity=0.2,
            placement="cheeks",
            blend_mode=BlendMode.NORMAL
        )
        
        # 높은 강도
        high_config = BlushConfig(
            color=Color(255, 150, 150, 255),
            intensity=0.9,
            placement="cheeks",
            blend_mode=BlendMode.NORMAL
        )
        
        result_low = self.engine.apply_blush(self.test_image, self.landmarks, low_config)
        result_high = self.engine.apply_blush(self.test_image, self.landmarks, high_config)
        
        # 높은 강도가 더 많은 변화를 만들어야 함
        diff_low = np.sum(np.abs(result_low.astype(int) - self.test_image.astype(int)))
        diff_high = np.sum(np.abs(result_high.astype(int) - self.test_image.astype(int)))
        
        self.assertGreater(diff_high, diff_low)
    
    def test_blush_placement_options(self):
        """블러셔 위치 옵션 테스트"""
        placements = ["cheeks", "temples", "nose"]
        results = []
        
        for placement in placements:
            config = BlushConfig(
                color=Color(255, 150, 150, 255),
                intensity=0.6,
                placement=placement,
                blend_mode=BlendMode.NORMAL
            )
            result = self.engine.apply_blush(self.test_image, self.landmarks, config)
            results.append(result)
        
        # 모든 위치가 다른 결과를 만들어야 함
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                self.assertFalse(np.array_equal(results[i], results[j]))
    
    def test_blush_blend_modes(self):
        """다양한 블렌드 모드 테스트"""
        blend_modes = [BlendMode.NORMAL, BlendMode.MULTIPLY, BlendMode.OVERLAY]
        results = []
        
        for mode in blend_modes:
            config = BlushConfig(
                color=Color(255, 150, 150, 255),
                intensity=0.6,
                placement="cheeks",
                blend_mode=mode
            )
            result = self.engine.apply_blush(self.test_image, self.landmarks, config)
            results.append(result)
        
        # 모든 블렌드 모드가 다른 결과를 만들어야 함
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                self.assertFalse(np.array_equal(results[i], results[j]))
    
    def test_cheek_mask_generation(self):
        """볼 마스크 생성 테스트"""
        mask = self.engine._get_cheek_mask(self.test_image, self.landmarks, "cheeks")
        
        # 마스크가 올바른 크기인지 확인
        self.assertEqual(mask.shape, self.test_image.shape[:2])
        
        # 마스크에 0이 아닌 값이 있는지 확인 (볼 영역이 마스킹됨)
        self.assertGreater(np.sum(mask), 0)
        
        # 마스크 값이 0-255 범위 내에 있는지 확인
        self.assertTrue(np.all(mask >= 0))
        self.assertTrue(np.all(mask <= 255))
    
    def test_cheek_mask_with_insufficient_landmarks(self):
        """랜드마크가 부족한 경우 마스크 생성 테스트"""
        # 랜드마크가 부족한 경우
        few_landmarks = [Point3D(50, 50, 0) for _ in range(10)]
        
        mask = self.engine._get_cheek_mask(self.test_image, few_landmarks, "cheeks")
        
        # 기본 마스크가 생성되어야 함
        self.assertEqual(mask.shape, self.test_image.shape[:2])
        self.assertGreater(np.sum(mask), 0)
    
    def test_nose_placement_mask(self):
        """코 위치 블러셔 마스크 테스트"""
        mask = self.engine._get_cheek_mask(self.test_image, self.landmarks, "nose")
        
        # 마스크가 올바른 크기인지 확인
        self.assertEqual(mask.shape, self.test_image.shape[:2])
        
        # 마스크에 0이 아닌 값이 있는지 확인
        self.assertGreater(np.sum(mask), 0)
        
        # 코 영역은 볼 영역과 다른 위치에 있어야 함
        cheek_mask = self.engine._get_cheek_mask(self.test_image, self.landmarks, "cheeks")
        self.assertFalse(np.array_equal(mask, cheek_mask))

