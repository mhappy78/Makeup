#!/usr/bin/env python3
"""
고품질 이미지 처리 및 저장 시스템 테스트
"""
import unittest
import numpy as np
import cv2
import os
import tempfile
import shutil
from typing import List

from models.core import Point3D
from utils.image_processor import (
    ImageProcessor, ImageEnhancer, ImageMetadata, 
    ImageFormat, QualityLevel
)


class TestImageEnhancer(unittest.TestCase):
    """이미지 품질 향상 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.enhancer = ImageEnhancer()
        self.test_image = self._create_test_image()
        self.test_landmarks = self._create_test_landmarks()
    
    def _create_test_image(self) -> np.ndarray:
        """테스트용 이미지 생성"""
        image = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        # 간단한 얼굴 형태 그리기
        center = (320, 240)
        cv2.ellipse(image, center, (100, 140), 0, 0, 360, (180, 150, 120), -1)
        
        # 노이즈 추가
        noise = np.random.randint(-20, 20, image.shape, dtype=np.int16)
        noisy_image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return noisy_image
    
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
    
    def test_enhance_sharpness(self):
        """선명도 향상 테스트"""
        enhanced = self.enhancer.enhance_sharpness(self.test_image, factor=1.2)
        
        self.assertEqual(enhanced.shape, self.test_image.shape)
        self.assertTrue(np.all(enhanced >= 0))
        self.assertTrue(np.all(enhanced <= 255))
        
        # 선명도가 향상되었는지 확인 (라플라시안 분산으로 측정)
        original_sharpness = cv2.Laplacian(self.test_image, cv2.CV_64F).var()
        enhanced_sharpness = cv2.Laplacian(enhanced, cv2.CV_64F).var()
        
        self.assertGreaterEqual(enhanced_sharpness, original_sharpness * 0.9)  # 약간의 여유
    
    def test_enhance_contrast(self):
        """대비 향상 테스트"""
        enhanced = self.enhancer.enhance_contrast(self.test_image, factor=1.1)
        
        self.assertEqual(enhanced.shape, self.test_image.shape)
        self.assertTrue(np.all(enhanced >= 0))
        self.assertTrue(np.all(enhanced <= 255))
        
        # 대비가 향상되었는지 확인 (표준편차로 측정)
        original_std = np.std(self.test_image)
        enhanced_std = np.std(enhanced)
        
        self.assertGreaterEqual(enhanced_std, original_std * 0.9)
    
    def test_enhance_color_saturation(self):
        """색상 채도 향상 테스트"""
        enhanced = self.enhancer.enhance_color_saturation(self.test_image, factor=1.1)
        
        self.assertEqual(enhanced.shape, self.test_image.shape)
        self.assertTrue(np.all(enhanced >= 0))
        self.assertTrue(np.all(enhanced <= 255))
        
        # HSV로 변환해서 채도 확인
        original_hsv = cv2.cvtColor(self.test_image, cv2.COLOR_BGR2HSV)
        enhanced_hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
        
        original_saturation = np.mean(original_hsv[:, :, 1])
        enhanced_saturation = np.mean(enhanced_hsv[:, :, 1])
        
        self.assertGreaterEqual(enhanced_saturation, original_saturation * 0.9)
    
    def test_reduce_noise(self):
        """노이즈 감소 테스트"""
        denoised = self.enhancer.reduce_noise(self.test_image, strength=10)
        
        self.assertEqual(denoised.shape, self.test_image.shape)
        self.assertTrue(np.all(denoised >= 0))
        self.assertTrue(np.all(denoised <= 255))
        
        # 노이즈가 감소했는지 확인 (고주파 성분 비교)
        original_high_freq = cv2.Laplacian(self.test_image, cv2.CV_64F)
        denoised_high_freq = cv2.Laplacian(denoised, cv2.CV_64F)
        
        original_noise_level = np.std(original_high_freq)
        denoised_noise_level = np.std(denoised_high_freq)
        
        self.assertLessEqual(denoised_noise_level, original_noise_level * 1.1)
    
    def test_enhance_skin_tone(self):
        """피부톤 향상 테스트"""
        enhanced = self.enhancer.enhance_skin_tone(self.test_image, self.test_landmarks)
        
        self.assertEqual(enhanced.shape, self.test_image.shape)
        self.assertTrue(np.all(enhanced >= 0))
        self.assertTrue(np.all(enhanced <= 255))
        
        # 이미지가 변경되었는지 확인
        self.assertFalse(np.array_equal(enhanced, self.test_image))


class TestImageMetadata(unittest.TestCase):
    """이미지 메타데이터 테스트"""
    
    def test_metadata_creation(self):
        """메타데이터 생성 테스트"""
        metadata = ImageMetadata(
            filename="test_image",
            format="jpeg",
            width=640,
            height=480,
            channels=3,
            file_size=100000,
            creation_time="2024-01-01T12:00:00",
            applied_effects=["lipstick", "foundation"],
            processing_time=1.5,
            quality_score=0.85
        )
        
        self.assertEqual(metadata.filename, "test_image")
        self.assertEqual(metadata.format, "jpeg")
        self.assertEqual(metadata.width, 640)
        self.assertEqual(metadata.height, 480)
        self.assertEqual(len(metadata.applied_effects), 2)
    
    def test_metadata_serialization(self):
        """메타데이터 직렬화 테스트"""
        metadata = ImageMetadata(
            filename="test_image",
            format="png",
            width=800,
            height=600,
            channels=3,
            file_size=150000,
            creation_time="2024-01-01T12:00:00",
            applied_effects=["eyeshadow", "blush"],
            processing_time=2.0,
            quality_score=0.9,
            custom_tags={"user": "test_user", "session": "session_123"}
        )
        
        # 딕셔너리로 변환
        data_dict = metadata.to_dict()
        self.assertIsInstance(data_dict, dict)
        self.assertEqual(data_dict["filename"], "test_image")
        self.assertEqual(data_dict["custom_tags"]["user"], "test_user")
        
        # 딕셔너리에서 복원
        restored_metadata = ImageMetadata.from_dict(data_dict)
        self.assertEqual(restored_metadata.filename, metadata.filename)
        self.assertEqual(restored_metadata.custom_tags, metadata.custom_tags)


class TestImageProcessor(unittest.TestCase):
    """이미지 프로세서 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.processor = ImageProcessor(output_dir=self.temp_dir)
        
        self.test_image = self._create_test_image()
        self.test_landmarks = self._create_test_landmarks()
    
    def tearDown(self):
        """테스트 정리"""
        # 임시 디렉토리 삭제
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
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
    
    def test_save_image_jpeg(self):
        """JPEG 이미지 저장 테스트"""
        success, filepath = self.processor.save_image(
            self.test_image, 
            "test_jpeg", 
            ImageFormat.JPEG, 
            QualityLevel.HIGH
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.jpg'))
        
        # 저장된 이미지 로드해서 확인
        loaded_image = cv2.imread(filepath)
        self.assertIsNotNone(loaded_image)
        self.assertEqual(loaded_image.shape, self.test_image.shape)
    
    def test_save_image_png(self):
        """PNG 이미지 저장 테스트"""
        success, filepath = self.processor.save_image(
            self.test_image, 
            "test_png", 
            ImageFormat.PNG, 
            QualityLevel.HIGH
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.png'))
    
    def test_save_image_webp(self):
        """WebP 이미지 저장 테스트"""
        success, filepath = self.processor.save_image(
            self.test_image, 
            "test_webp", 
            ImageFormat.WEBP, 
            QualityLevel.MEDIUM
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.webp'))
    
    def test_save_with_metadata(self):
        """메타데이터와 함께 저장 테스트"""
        metadata = self.processor.create_metadata(
            self.test_image,
            "test_with_metadata",
            ImageFormat.JPEG,
            applied_effects=["lipstick", "foundation"],
            processing_time=1.5,
            quality_score=0.85,
            custom_tags={"test": "metadata_test"}
        )
        
        success, filepath = self.processor.save_image(
            self.test_image,
            "test_with_metadata",
            ImageFormat.JPEG,
            QualityLevel.HIGH,
            metadata=metadata
        )
        
        self.assertTrue(success)
        
        # 메타데이터 파일 존재 확인
        metadata_path = os.path.join(self.temp_dir, "metadata", "test_with_metadata_metadata.json")
        self.assertTrue(os.path.exists(metadata_path))
        
        # 메타데이터 로드 테스트
        loaded_metadata = self.processor.load_metadata("test_with_metadata")
        self.assertIsNotNone(loaded_metadata)
        self.assertEqual(loaded_metadata.filename, "test_with_metadata")
        self.assertEqual(loaded_metadata.custom_tags["test"], "metadata_test")
    
    def test_quality_levels(self):
        """품질 레벨별 저장 테스트"""
        for quality in QualityLevel:
            success, filepath = self.processor.save_image(
                self.test_image,
                f"test_quality_{quality.value}",
                ImageFormat.JPEG,
                quality
            )
            
            self.assertTrue(success, f"품질 레벨 {quality.value} 저장 실패")
            self.assertTrue(os.path.exists(filepath))
    
    def test_batch_save(self):
        """배치 저장 테스트"""
        images = [
            (self.test_image, "batch_test_1"),
            (self.test_image, "batch_test_2"),
            (self.test_image, "batch_test_3")
        ]
        
        results = self.processor.batch_save(images, ImageFormat.PNG, QualityLevel.MEDIUM)
        
        self.assertEqual(len(results), 3)
        
        for success, filepath in results:
            self.assertTrue(success)
            self.assertTrue(os.path.exists(filepath))
    
    def test_supported_formats(self):
        """지원 형식 조회 테스트"""
        formats = self.processor.get_supported_formats()
        
        self.assertIsInstance(formats, list)
        self.assertIn("jpeg", formats)
        self.assertIn("png", formats)
        self.assertIn("webp", formats)
    
    def test_quality_levels_list(self):
        """품질 레벨 조회 테스트"""
        levels = self.processor.get_quality_levels()
        
        self.assertIsInstance(levels, list)
        self.assertIn("low", levels)
        self.assertIn("medium", levels)
        self.assertIn("high", levels)
        self.assertIn("ultra", levels)
    
    def test_file_size_estimation(self):
        """파일 크기 추정 테스트"""
        estimated_size = self.processor.estimate_file_size(
            self.test_image, 
            ImageFormat.JPEG, 
            QualityLevel.HIGH
        )
        
        self.assertIsInstance(estimated_size, int)
        self.assertGreater(estimated_size, 0)
        
        # 실제 저장해서 비교
        success, filepath = self.processor.save_image(
            self.test_image,
            "size_test",
            ImageFormat.JPEG,
            QualityLevel.HIGH
        )
        
        if success:
            actual_size = os.path.getsize(filepath)
            # 추정값이 실제값과 어느 정도 비슷해야 함
            self.assertLess(abs(estimated_size - actual_size) / actual_size, 0.5)  # 50% 오차 허용
    
    def test_format_comparison(self):
        """형식별 비교 테스트"""
        comparison = self.processor.compare_formats(self.test_image)
        
        self.assertIsInstance(comparison, dict)
        self.assertGreater(len(comparison), 0)
        
        # 각 비교 항목이 올바른 구조를 가지는지 확인
        for key, value in comparison.items():
            self.assertIn("file_size", value)
            self.assertIn("compression_ratio", value)
            self.assertIn("format", value)
            self.assertIn("quality", value)
            
            self.assertIsInstance(value["file_size"], int)
            self.assertIsInstance(value["compression_ratio"], (int, float))
    
    def test_enhance_quality_flag(self):
        """품질 향상 플래그 테스트"""
        # 품질 향상 적용
        success1, filepath1 = self.processor.save_image(
            self.test_image,
            "enhanced",
            ImageFormat.JPEG,
            QualityLevel.HIGH,
            enhance_quality=True,
            landmarks=self.test_landmarks
        )
        
        # 품질 향상 미적용
        success2, filepath2 = self.processor.save_image(
            self.test_image,
            "not_enhanced",
            ImageFormat.JPEG,
            QualityLevel.HIGH,
            enhance_quality=False
        )
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # 두 파일이 다른지 확인
        if os.path.exists(filepath1) and os.path.exists(filepath2):
            enhanced_image = cv2.imread(filepath1)
            normal_image = cv2.imread(filepath2)
            
            # 완전히 동일하지 않아야 함
            self.assertFalse(np.array_equal(enhanced_image, normal_image))


class TestImageProcessorPerformance(unittest.TestCase):
    """이미지 프로세서 성능 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = ImageProcessor(output_dir=self.temp_dir)
        
        # 큰 이미지로 성능 테스트
        self.large_image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        self.small_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    def tearDown(self):
        """테스트 정리"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_large_image_processing(self):
        """큰 이미지 처리 성능 테스트"""
        import time
        
        start_time = time.time()
        success, filepath = self.processor.save_image(
            self.large_image,
            "large_image_test",
            ImageFormat.JPEG,
            QualityLevel.HIGH,
            enhance_quality=True
        )
        processing_time = time.time() - start_time
        
        self.assertTrue(success)
        self.assertLess(processing_time, 10.0)  # 10초 이내
        
        print(f"큰 이미지 처리 시간: {processing_time:.3f}초")
    
    def test_quality_vs_speed_tradeoff(self):
        """품질 vs 속도 트레이드오프 테스트"""
        import time
        
        times = {}
        
        for quality in QualityLevel:
            start_time = time.time()
            success, _ = self.processor.save_image(
                self.small_image,
                f"speed_test_{quality.value}",
                ImageFormat.JPEG,
                quality,
                enhance_quality=True
            )
            processing_time = time.time() - start_time
            
            self.assertTrue(success)
            times[quality.value] = processing_time
        
        # 일반적으로 품질이 높을수록 처리 시간이 길어야 함
        print("품질별 처리 시간:")
        for quality, time_taken in times.items():
            print(f"  {quality}: {time_taken:.3f}초")
        
        # ULTRA가 LOW보다 오래 걸려야 함
        self.assertGreaterEqual(times["ultra"], times["low"])


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)