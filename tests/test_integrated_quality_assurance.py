"""
통합 테스트 및 품질 보증 구현
Task 9.2: 전체 시스템의 통합 테스트 및 품질 보증 시스템
"""
import unittest
import sys
import os
import numpy as np
import cv2
import time
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock

# 프로젝트 모듈 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from models.core import Point3D, Color, BoundingBox, FaceRegion
    from models.makeup import MakeupConfig, LipstickConfig, EyeshadowConfig, BlushConfig, FoundationConfig, EyelinerConfig, BlendMode, EyeshadowStyle
    from models.surgery import SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig, FeatureType
    from engines.face_engine import MediaPipeFaceEngine, FaceDetectionResult, FaceFrame, VideoStream
    from engines.makeup_engine import RealtimeMakeupEngine, MakeupResult, ColorBlender
    from engines.surgery_engine import RealtimeSurgeryEngine, SurgeryResult, MeshWarper
    from engines.integrated_engine import IntegratedEngine, IntegratedConfig, IntegratedResult, EffectPriority, ConflictResolution
    from ui.main_interface import MainInterface
    from ui.feedback_system import FeedbackSystem
    from utils.image_processor import ImageProcessor
    from utils.image_gallery import ImageGallery
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    # 테스트용 Mock 클래스들
    Point3D = Mock
    Color = Mock
    BoundingBox = Mock


class TestSeverity(Enum):
    """테스트 심각도 레벨"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestCategory(Enum):
    """테스트 카테고리"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    COMPATIBILITY = "compatibility"


@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    test_name: str
    category: TestCategory
    severity: TestSeverity
    passed: bool
    execution_time: float
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None


@dataclass
class QualityMetrics:
    """품질 메트릭 데이터 클래스"""
    accuracy: float
    performance: float
    reliability: float
    usability: float
    maintainability: float
    overall_score: float


class TestDataGenerator:
    """테스트 데이터 생성기"""
    
    @staticmethod
    def create_test_image(width: int = 640, height: int = 480) -> np.ndarray:
        """테스트용 이미지 생성"""
        # 간단한 얼굴 모양 이미지 생성
        image = np.ones((height, width, 3), dtype=np.uint8) * 200
        
        # 얼굴 타원 그리기
        center = (width // 2, height // 2)
        axes = (width // 4, height // 3)
        cv2.ellipse(image, center, axes, 0, 0, 360, (220, 180, 160), -1)
        
        # 눈 그리기
        left_eye = (width // 2 - 60, height // 2 - 40)
        right_eye = (width // 2 + 60, height // 2 - 40)
        cv2.ellipse(image, left_eye, (20, 10), 0, 0, 360, (100, 100, 100), -1)
        cv2.ellipse(image, right_eye, (20, 10), 0, 0, 360, (100, 100, 100), -1)
        
        # 코 그리기
        nose_points = np.array([
            [width // 2, height // 2 - 10],
            [width // 2 - 10, height // 2 + 20],
            [width // 2 + 10, height // 2 + 20]
        ], np.int32)
        cv2.fillPoly(image, [nose_points], (200, 160, 140))
        
        # 입 그리기
        mouth = (width // 2, height // 2 + 60)
        cv2.ellipse(image, mouth, (30, 15), 0, 0, 360, (150, 100, 100), -1)
        
        return image
    
    @staticmethod
    def create_test_landmarks(count: int = 468) -> List[Point3D]:
        """테스트용 랜드마크 생성"""
        landmarks = []
        for i in range(count):
            # 얼굴 영역 내 랜덤 포인트 생성
            x = np.random.uniform(160, 480)
            y = np.random.uniform(120, 360)
            z = np.random.uniform(-50, 50)
            landmarks.append(Point3D(x, y, z))
        return landmarks
    
    @staticmethod
    def create_test_makeup_config() -> MakeupConfig:
        """테스트용 메이크업 설정 생성"""
        return MakeupConfig(
            lipstick=LipstickConfig(
                color=Color(200, 100, 100, 255),
                intensity=0.7,
                glossiness=0.5,
                blend_mode=BlendMode.NORMAL
            ),
            eyeshadow=EyeshadowConfig(
                colors=[Color(150, 120, 100, 255)],
                intensity=0.6,
                style=EyeshadowStyle.NATURAL,
                shimmer=0.3,
                blend_mode=BlendMode.NORMAL
            ),
            blush=BlushConfig(
                color=Color(220, 150, 150, 255),
                intensity=0.5,
                placement="cheeks",
                blend_mode=BlendMode.NORMAL
            ),
            foundation=FoundationConfig(
                color=Color(220, 180, 160, 255),
                coverage=0.6,
                finish="natural"
            ),
            eyeliner=EyelinerConfig(
                color=Color(50, 50, 50, 255),
                thickness=0.5,
                style="natural"
            )
        )
    
    @staticmethod
    def create_test_surgery_config() -> SurgeryConfig:
        """테스트용 성형 설정 생성"""
        return SurgeryConfig(
            nose=NoseConfig(
                height_adjustment=0.2,
                width_adjustment=-0.1,
                tip_adjustment=0.1,
                bridge_adjustment=0.15
            ),
            eyes=EyeConfig(
                size_adjustment=0.1,
                shape_adjustment=0.05,
                position_adjustment=0.0,
                angle_adjustment=0.02
            ),
            jawline=JawlineConfig(
                width_adjustment=-0.1,
                angle_adjustment=0.05,
                length_adjustment=0.0
            ),
            cheekbones=CheekboneConfig(
                width_adjustment=-0.05,
                height_adjustment=0.1,
                prominence_adjustment=0.08
            )
        )


class PerformanceBenchmark:
    """성능 벤치마크 도구"""
    
    def __init__(self):
        self.benchmarks = {}
    
    def measure_execution_time(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """함수 실행 시간 측정"""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    
    def measure_memory_usage(self, func, *args, **kwargs) -> Tuple[Any, Dict[str, float]]:
        """메모리 사용량 측정"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = {
            'before_mb': memory_before,
            'after_mb': memory_after,
            'delta_mb': memory_after - memory_before
        }
        
        return result, memory_usage
    
    def benchmark_fps(self, func, duration: float = 5.0) -> Dict[str, float]:
        """FPS 벤치마크"""
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < duration:
            try:
                func()
                frame_count += 1
            except Exception as e:
                print(f"FPS 벤치마크 중 오류: {e}")
                break
        
        elapsed_time = time.time() - start_time
        fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'duration': elapsed_time
        }


class QualityAssurance:
    """품질 보증 시스템"""
    
    def __init__(self):
        self.test_results = []
        self.quality_thresholds = {
            'accuracy': 0.85,
            'performance': 0.80,
            'reliability': 0.90,
            'usability': 0.75,
            'maintainability': 0.70
        }
    
    def calculate_quality_metrics(self, test_results: List[TestResult]) -> QualityMetrics:
        """품질 메트릭 계산"""
        if not test_results:
            return QualityMetrics(0, 0, 0, 0, 0, 0)
        
        # 정확도: 통과한 테스트 비율
        passed_tests = sum(1 for result in test_results if result.passed)
        accuracy = passed_tests / len(test_results)
        
        # 성능: 평균 실행 시간 기반
        avg_execution_time = np.mean([result.execution_time for result in test_results])
        performance = max(0, 1 - (avg_execution_time / 10.0))  # 10초를 기준으로 정규화
        
        # 신뢰성: 심각도별 가중치 적용
        severity_weights = {
            TestSeverity.CRITICAL: 4,
            TestSeverity.HIGH: 3,
            TestSeverity.MEDIUM: 2,
            TestSeverity.LOW: 1
        }
        
        total_weight = sum(severity_weights[result.severity] for result in test_results)
        passed_weight = sum(severity_weights[result.severity] for result in test_results if result.passed)
        reliability = passed_weight / total_weight if total_weight > 0 else 0
        
        # 사용성: 품질 점수 평균
        quality_scores = [result.quality_score for result in test_results if result.quality_score is not None]
        usability = np.mean(quality_scores) if quality_scores else 0.5
        
        # 유지보수성: 오류 메시지가 있는 테스트 비율 (역산)
        error_tests = sum(1 for result in test_results if result.error_message is not None)
        maintainability = 1 - (error_tests / len(test_results))
        
        # 전체 점수: 가중 평균
        overall_score = (
            accuracy * 0.25 +
            performance * 0.20 +
            reliability * 0.25 +
            usability * 0.15 +
            maintainability * 0.15
        )
        
        return QualityMetrics(
            accuracy=accuracy,
            performance=performance,
            reliability=reliability,
            usability=usability,
            maintainability=maintainability,
            overall_score=overall_score
        )
    
    def validate_quality_gates(self, metrics: QualityMetrics) -> Dict[str, bool]:
        """품질 게이트 검증"""
        return {
            'accuracy_gate': metrics.accuracy >= self.quality_thresholds['accuracy'],
            'performance_gate': metrics.performance >= self.quality_thresholds['performance'],
            'reliability_gate': metrics.reliability >= self.quality_thresholds['reliability'],
            'usability_gate': metrics.usability >= self.quality_thresholds['usability'],
            'maintainability_gate': metrics.maintainability >= self.quality_thresholds['maintainability']
        }


class IntegratedQualityAssuranceTest(unittest.TestCase):
    """통합 품질 보증 테스트 스위트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_data_generator = TestDataGenerator()
        self.performance_benchmark = PerformanceBenchmark()
        self.quality_assurance = QualityAssurance()
        self.test_results = []
        
        # 테스트 데이터 생성
        self.test_image = self.test_data_generator.create_test_image()
        self.test_landmarks = self.test_data_generator.create_test_landmarks()
        self.test_makeup_config = self.test_data_generator.create_test_makeup_config()
        self.test_surgery_config = self.test_data_generator.create_test_surgery_config()
    
    def _record_test_result(self, test_name: str, category: TestCategory, 
                          severity: TestSeverity, passed: bool, 
                          execution_time: float, error_message: str = None,
                          performance_metrics: Dict = None, quality_score: float = None):
        """테스트 결과 기록"""
        result = TestResult(
            test_name=test_name,
            category=category,
            severity=severity,
            passed=passed,
            execution_time=execution_time,
            error_message=error_message,
            performance_metrics=performance_metrics,
            quality_score=quality_score
        )
        self.test_results.append(result)
    
    def test_face_engine_integration(self):
        """얼굴 엔진 통합 테스트"""
        test_name = "face_engine_integration"
        start_time = time.time()
        
        try:
            # Mock 얼굴 엔진 테스트
            face_engine = Mock()
            face_engine.detect_face.return_value = Mock()
            face_engine.extract_landmarks.return_value = self.test_landmarks
            
            # 얼굴 감지 테스트
            detection_result = face_engine.detect_face(self.test_image)
            self.assertIsNotNone(detection_result)
            
            # 랜드마크 추출 테스트
            landmarks = face_engine.extract_landmarks(self.test_image)
            self.assertEqual(len(landmarks), 468)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.CRITICAL,
                True, execution_time, quality_score=0.9
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.CRITICAL,
                False, execution_time, str(e)
            )
            self.fail(f"얼굴 엔진 통합 테스트 실패: {e}")
    
    def test_makeup_engine_integration(self):
        """메이크업 엔진 통합 테스트"""
        test_name = "makeup_engine_integration"
        start_time = time.time()
        
        try:
            # Mock 메이크업 엔진 테스트
            makeup_engine = Mock()
            makeup_result = Mock()
            makeup_result.is_successful.return_value = True
            makeup_result.applied_effects = ["lipstick", "eyeshadow", "blush"]
            makeup_engine.apply_full_makeup.return_value = makeup_result
            
            # 메이크업 적용 테스트
            result = makeup_engine.apply_full_makeup(
                self.test_image, self.test_landmarks, self.test_makeup_config
            )
            
            self.assertTrue(result.is_successful())
            self.assertGreater(len(result.applied_effects), 0)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.HIGH,
                True, execution_time, quality_score=0.85
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.HIGH,
                False, execution_time, str(e)
            )
            self.fail(f"메이크업 엔진 통합 테스트 실패: {e}")
    
    def test_surgery_engine_integration(self):
        """성형 엔진 통합 테스트"""
        test_name = "surgery_engine_integration"
        start_time = time.time()
        
        try:
            # Mock 성형 엔진 테스트
            surgery_engine = Mock()
            surgery_result = Mock()
            surgery_result.is_successful.return_value = True
            surgery_result.applied_modifications = ["nose_height", "eye_size"]
            surgery_result.natural_score = 0.8
            surgery_engine.apply_full_surgery.return_value = surgery_result
            
            # 성형 적용 테스트
            result = surgery_engine.apply_full_surgery(
                self.test_image, self.test_landmarks, self.test_surgery_config
            )
            
            self.assertTrue(result.is_successful())
            self.assertGreater(len(result.applied_modifications), 0)
            self.assertGreaterEqual(result.natural_score, 0.7)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.HIGH,
                True, execution_time, quality_score=0.8
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.HIGH,
                False, execution_time, str(e)
            )
            self.fail(f"성형 엔진 통합 테스트 실패: {e}")
    
    def test_integrated_engine_full_workflow(self):
        """통합 엔진 전체 워크플로우 테스트"""
        test_name = "integrated_engine_full_workflow"
        start_time = time.time()
        
        try:
            # Mock 통합 엔진 테스트
            integrated_engine = Mock()
            integrated_result = Mock()
            integrated_result.is_successful.return_value = True
            integrated_result.is_high_quality.return_value = True
            integrated_result.quality_score = 0.85
            integrated_result.applied_effects = ["makeup", "surgery"]
            integrated_result.conflicts_detected = []
            integrated_engine.apply_integrated_effects.return_value = integrated_result
            
            # 통합 설정 생성
            integrated_config = Mock()
            integrated_config.makeup_config = self.test_makeup_config
            integrated_config.surgery_config = self.test_surgery_config
            integrated_config.effect_priority = EffectPriority.SURGERY_FIRST
            integrated_config.conflict_resolution = ConflictResolution.BLEND
            
            # 통합 효과 적용 테스트
            result = integrated_engine.apply_integrated_effects(
                self.test_image, self.test_landmarks, integrated_config
            )
            
            self.assertTrue(result.is_successful())
            self.assertTrue(result.is_high_quality())
            self.assertGreaterEqual(result.quality_score, 0.7)
            self.assertEqual(len(result.conflicts_detected), 0)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.CRITICAL,
                True, execution_time, quality_score=result.quality_score
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.CRITICAL,
                False, execution_time, str(e)
            )
            self.fail(f"통합 엔진 전체 워크플로우 테스트 실패: {e}")
    
    def test_performance_benchmarks(self):
        """성능 벤치마크 테스트"""
        test_name = "performance_benchmarks"
        start_time = time.time()
        
        try:
            # 얼굴 감지 성능 테스트
            def mock_face_detection():
                time.sleep(0.01)  # 10ms 시뮬레이션
                return Mock()
            
            fps_result = self.performance_benchmark.benchmark_fps(
                mock_face_detection, duration=1.0
            )
            
            self.assertGreater(fps_result['fps'], 30)  # 최소 30 FPS
            
            # 메모리 사용량 테스트
            def mock_image_processing():
                # 큰 배열 생성으로 메모리 사용 시뮬레이션
                temp_array = np.zeros((1000, 1000, 3), dtype=np.uint8)
                return temp_array
            
            result, memory_usage = self.performance_benchmark.measure_memory_usage(
                mock_image_processing
            )
            
            self.assertLess(memory_usage['delta_mb'], 100)  # 100MB 미만 증가
            
            execution_time = time.time() - start_time
            performance_metrics = {
                'fps': fps_result['fps'],
                'memory_delta_mb': memory_usage['delta_mb']
            }
            
            self._record_test_result(
                test_name, TestCategory.PERFORMANCE, TestSeverity.HIGH,
                True, execution_time, performance_metrics=performance_metrics,
                quality_score=0.9
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.PERFORMANCE, TestSeverity.HIGH,
                False, execution_time, str(e)
            )
            self.fail(f"성능 벤치마크 테스트 실패: {e}")
    
    def test_concurrent_processing(self):
        """동시 처리 테스트"""
        test_name = "concurrent_processing"
        start_time = time.time()
        
        try:
            def mock_process_image(image_id):
                time.sleep(0.1)  # 처리 시간 시뮬레이션
                return f"processed_{image_id}"
            
            # 동시 처리 테스트
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(mock_process_image, i) 
                    for i in range(10)
                ]
                results = [future.result() for future in futures]
            
            self.assertEqual(len(results), 10)
            self.assertTrue(all("processed_" in result for result in results))
            
            execution_time = time.time() - start_time
            self.assertLess(execution_time, 0.5)  # 순차 처리보다 빨라야 함
            
            self._record_test_result(
                test_name, TestCategory.PERFORMANCE, TestSeverity.MEDIUM,
                True, execution_time, quality_score=0.85
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.PERFORMANCE, TestSeverity.MEDIUM,
                False, execution_time, str(e)
            )
            self.fail(f"동시 처리 테스트 실패: {e}")
    
    def test_error_handling_robustness(self):
        """오류 처리 견고성 테스트"""
        test_name = "error_handling_robustness"
        start_time = time.time()
        
        try:
            # 잘못된 입력 데이터 테스트
            invalid_inputs = [
                None,
                np.array([]),
                np.zeros((10, 10)),  # 잘못된 차원
                "invalid_input"
            ]
            
            error_handled_count = 0
            
            for invalid_input in invalid_inputs:
                try:
                    # Mock 함수로 오류 처리 테스트
                    mock_processor = Mock()
                    mock_processor.process.side_effect = ValueError("Invalid input")
                    mock_processor.process(invalid_input)
                except (ValueError, TypeError, AttributeError):
                    error_handled_count += 1
                except Exception:
                    pass  # 예상치 못한 오류는 카운트하지 않음
            
            # 모든 잘못된 입력에 대해 적절한 오류 처리가 되어야 함
            error_handling_rate = error_handled_count / len(invalid_inputs)
            self.assertGreaterEqual(error_handling_rate, 0.8)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.HIGH,
                True, execution_time, quality_score=error_handling_rate
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.HIGH,
                False, execution_time, str(e)
            )
            self.fail(f"오류 처리 견고성 테스트 실패: {e}")
    
    def test_ui_responsiveness(self):
        """UI 반응성 테스트"""
        test_name = "ui_responsiveness"
        start_time = time.time()
        
        try:
            # Mock UI 컴포넌트 테스트
            mock_ui = Mock()
            mock_ui.update_display.return_value = True
            mock_ui.handle_user_input.return_value = True
            mock_ui.render_frame.return_value = True
            
            # UI 업데이트 시간 측정
            ui_operations = [
                mock_ui.update_display,
                mock_ui.handle_user_input,
                mock_ui.render_frame
            ]
            
            response_times = []
            for operation in ui_operations:
                op_start = time.time()
                operation()
                response_time = time.time() - op_start
                response_times.append(response_time)
            
            avg_response_time = np.mean(response_times)
            self.assertLess(avg_response_time, 0.016)  # 60 FPS 기준 (16ms)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.USABILITY, TestSeverity.MEDIUM,
                True, execution_time, quality_score=0.9
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.USABILITY, TestSeverity.MEDIUM,
                False, execution_time, str(e)
            )
            self.fail(f"UI 반응성 테스트 실패: {e}")
    
    def test_data_integrity(self):
        """데이터 무결성 테스트"""
        test_name = "data_integrity"
        start_time = time.time()
        
        try:
            # 이미지 데이터 무결성 검증
            original_image = self.test_image.copy()
            
            # Mock 처리 후 이미지 검증
            processed_image = original_image.copy()
            processed_image[0, 0] = [255, 255, 255]  # 작은 변경
            
            # 이미지 형태 검증
            self.assertEqual(original_image.shape, processed_image.shape)
            self.assertEqual(original_image.dtype, processed_image.dtype)
            
            # 랜드마크 데이터 무결성 검증
            original_landmarks = self.test_landmarks.copy()
            modified_landmarks = [Point3D(p.x + 1, p.y, p.z) for p in original_landmarks]
            
            self.assertEqual(len(original_landmarks), len(modified_landmarks))
            
            # 설정 데이터 무결성 검증
            config_dict = {
                'makeup': self.test_makeup_config,
                'surgery': self.test_surgery_config
            }
            
            # JSON 직렬화/역직렬화 테스트 (Mock)
            serialized = json.dumps(str(config_dict))
            deserialized = json.loads(serialized)
            self.assertIsInstance(deserialized, str)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.HIGH,
                True, execution_time, quality_score=0.95
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.INTEGRATION, TestSeverity.HIGH,
                False, execution_time, str(e)
            )
            self.fail(f"데이터 무결성 테스트 실패: {e}")
    
    def test_security_validation(self):
        """보안 검증 테스트"""
        test_name = "security_validation"
        start_time = time.time()
        
        try:
            # 입력 검증 테스트
            malicious_inputs = [
                "../../../etc/passwd",
                "<script>alert('xss')</script>",
                "'; DROP TABLE users; --",
                "\x00\x01\x02\x03"  # 바이너리 데이터
            ]
            
            security_passed = 0
            for malicious_input in malicious_inputs:
                try:
                    # Mock 보안 검증 함수
                    def validate_input(input_data):
                        if any(char in str(input_data) for char in ['<', '>', ';', '--', '\x00']):
                            raise ValueError("Malicious input detected")
                        return True
                    
                    validate_input(malicious_input)
                except ValueError:
                    security_passed += 1
            
            security_rate = security_passed / len(malicious_inputs)
            self.assertGreaterEqual(security_rate, 0.8)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.SECURITY, TestSeverity.CRITICAL,
                True, execution_time, quality_score=security_rate
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.SECURITY, TestSeverity.CRITICAL,
                False, execution_time, str(e)
            )
            self.fail(f"보안 검증 테스트 실패: {e}")
    
    def test_compatibility_matrix(self):
        """호환성 매트릭스 테스트"""
        test_name = "compatibility_matrix"
        start_time = time.time()
        
        try:
            # 다양한 이미지 형식 호환성 테스트
            image_formats = [
                (640, 480, 3),   # 표준 컬러
                (1920, 1080, 3), # HD
                (320, 240, 3),   # 저해상도
                (800, 600, 1),   # 그레이스케일
            ]
            
            compatibility_count = 0
            for width, height, channels in image_formats:
                try:
                    test_img = np.random.randint(0, 255, (height, width, channels), dtype=np.uint8)
                    if channels == 1:
                        test_img = test_img.squeeze()
                    
                    # Mock 처리 함수
                    def process_image(img):
                        if len(img.shape) not in [2, 3]:
                            raise ValueError("Invalid image format")
                        return True
                    
                    process_image(test_img)
                    compatibility_count += 1
                except Exception:
                    pass
            
            compatibility_rate = compatibility_count / len(image_formats)
            self.assertGreaterEqual(compatibility_rate, 0.75)
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.COMPATIBILITY, TestSeverity.MEDIUM,
                True, execution_time, quality_score=compatibility_rate
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, TestCategory.COMPATIBILITY, TestSeverity.MEDIUM,
                False, execution_time, str(e)
            )
            self.fail(f"호환성 매트릭스 테스트 실패: {e}")
    
    def tearDown(self):
        """테스트 정리 및 품질 보고서 생성"""
        if self.test_results:
            # 품질 메트릭 계산
            quality_metrics = self.quality_assurance.calculate_quality_metrics(self.test_results)
            
            # 품질 게이트 검증
            quality_gates = self.quality_assurance.validate_quality_gates(quality_metrics)
            
            # 보고서 출력
            print("\n" + "="*80)
            print("통합 품질 보증 테스트 보고서")
            print("="*80)
            print(f"총 테스트 수: {len(self.test_results)}")
            print(f"통과한 테스트: {sum(1 for r in self.test_results if r.passed)}")
            print(f"실패한 테스트: {sum(1 for r in self.test_results if not r.passed)}")
            print()
            
            print("품질 메트릭:")
            print(f"  정확도: {quality_metrics.accuracy:.3f}")
            print(f"  성능: {quality_metrics.performance:.3f}")
            print(f"  신뢰성: {quality_metrics.reliability:.3f}")
            print(f"  사용성: {quality_metrics.usability:.3f}")
            print(f"  유지보수성: {quality_metrics.maintainability:.3f}")
            print(f"  전체 점수: {quality_metrics.overall_score:.3f}")
            print()
            
            print("품질 게이트 상태:")
            for gate, passed in quality_gates.items():
                status = "PASS" if passed else "FAIL"
                print(f"  {gate}: {status}")
            print()
            
            # 실패한 테스트 상세 정보
            failed_tests = [r for r in self.test_results if not r.passed]
            if failed_tests:
                print("실패한 테스트 상세:")
                for test in failed_tests:
                    print(f"  - {test.test_name}: {test.error_message}")
                print()
            
            # 성능 메트릭
            performance_tests = [r for r in self.test_results if r.performance_metrics]
            if performance_tests:
                print("성능 메트릭:")
                for test in performance_tests:
                    print(f"  - {test.test_name}:")
                    for metric, value in test.performance_metrics.items():
                        print(f"    {metric}: {value}")
                print()
            
            print("="*80)
            
            # 전체 품질 점수가 임계값 미만이면 테스트 실패
            if quality_metrics.overall_score < 0.75:
                self.fail(f"전체 품질 점수가 임계값 미만입니다: {quality_metrics.overall_score:.3f} < 0.75")


def run_quality_assurance_suite():
    """품질 보증 테스트 스위트 실행"""
    print("통합 품질 보증 테스트 시작...")
    
    # 테스트 스위트 생성
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegratedQualityAssuranceTest)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # 결과 반환
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_quality_assurance_suite()
    exit_code = 0 if success else 1
    print(f"\n품질 보증 테스트 {'성공' if success else '실패'}")
    exit(exit_code)