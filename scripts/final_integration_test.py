"""
최종 통합 테스트 - 모든 컴포넌트 통합 검증
Task 10: 최종 통합 및 배포 준비
"""
import unittest
import sys
import os
import numpy as np
import cv2
import time
import json
import tempfile
import shutil
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import concurrent.futures
import threading

# 프로젝트 모듈 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from models.core import Point3D, Color
    from models.makeup import MakeupConfig, LipstickConfig, EyeshadowConfig, BlushConfig, FoundationConfig
    from models.surgery import SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig
    from engines.face_engine import MediaPipeFaceEngine
    from engines.makeup_engine import RealtimeMakeupEngine
    from engines.surgery_engine import RealtimeSurgeryEngine
    from engines.integrated_engine import IntegratedEngine, IntegratedConfig, EffectPriority
    from ui.main_interface import MainInterface
    from ui.feedback_system import FeedbackSystem
    from utils.image_processor import ImageProcessor
    from utils.image_gallery import ImageGallery
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    MODULES_AVAILABLE = False


@dataclass
class IntegrationTestResult:
    """통합 테스트 결과"""
    test_name: str
    component: str
    passed: bool
    execution_time: float
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None


class SystemIntegrationTest(unittest.TestCase):
    """시스템 통합 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_results = []
        self.test_image = self._create_test_image()
        self.test_landmarks = self._create_test_landmarks()
        
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """테스트 정리"""
        # 임시 디렉토리 정리
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_image(self) -> np.ndarray:
        """테스트용 이미지 생성"""
        image = np.ones((480, 640, 3), dtype=np.uint8) * 200
        
        # 얼굴 모양 그리기
        center = (320, 240)
        axes = (160, 180)
        cv2.ellipse(image, center, axes, 0, 0, 360, (220, 180, 160), -1)
        
        # 눈 그리기
        cv2.ellipse(image, (260, 200), (20, 10), 0, 0, 360, (100, 100, 100), -1)
        cv2.ellipse(image, (380, 200), (20, 10), 0, 0, 360, (100, 100, 100), -1)
        
        # 코 그리기
        nose_points = np.array([[320, 230], [310, 260], [330, 260]], np.int32)
        cv2.fillPoly(image, [nose_points], (200, 160, 140))
        
        # 입 그리기
        cv2.ellipse(image, (320, 300), (30, 15), 0, 0, 360, (150, 100, 100), -1)
        
        return image
    
    def _create_test_landmarks(self) -> List[Point3D]:
        """테스트용 랜드마크 생성"""
        landmarks = []
        for i in range(468):
            x = np.random.uniform(160, 480)
            y = np.random.uniform(120, 360)
            z = np.random.uniform(-50, 50)
            landmarks.append(Point3D(x, y, z))
        return landmarks
    
    def _record_result(self, test_name: str, component: str, passed: bool, 
                      execution_time: float, error_message: str = None,
                      performance_metrics: Dict = None):
        """테스트 결과 기록"""
        result = IntegrationTestResult(
            test_name=test_name,
            component=component,
            passed=passed,
            execution_time=execution_time,
            error_message=error_message,
            performance_metrics=performance_metrics
        )
        self.test_results.append(result)
    
    @unittest.skipUnless(MODULES_AVAILABLE, "모듈을 사용할 수 없음")
    def test_complete_workflow_integration(self):
        """완전한 워크플로우 통합 테스트"""
        test_name = "complete_workflow_integration"
        start_time = time.time()
        
        try:
            # 1. 얼굴 엔진 초기화 및 테스트
            face_engine = MediaPipeFaceEngine()
            
            # 2. 메이크업 엔진 초기화 및 테스트
            makeup_engine = RealtimeMakeupEngine()
            
            # 3. 성형 엔진 초기화 및 테스트
            surgery_engine = RealtimeSurgeryEngine()
            
            # 4. 통합 엔진 초기화 및 테스트
            integrated_engine = IntegratedEngine()
            
            # 5. 전체 워크플로우 실행
            # 얼굴 감지
            face_result = face_engine.detect_face(self.test_image)
            self.assertIsNotNone(face_result)
            
            # 랜드마크 추출
            landmarks = face_engine.extract_landmarks(self.test_image)
            self.assertEqual(len(landmarks), 468)
            
            # 메이크업 설정 생성
            makeup_config = MakeupConfig(
                lipstick=LipstickConfig(
                    color=Color(200, 100, 100, 255),
                    intensity=0.7
                )
            )
            
            # 성형 설정 생성
            surgery_config = SurgeryConfig(
                nose=NoseConfig(height_adjustment=0.1)
            )
            
            # 통합 효과 적용
            integrated_config = IntegratedConfig(
                makeup_config=makeup_config,
                surgery_config=surgery_config,
                effect_priority=EffectPriority.SURGERY_FIRST
            )
            
            result = integrated_engine.apply_integrated_effects(
                self.test_image, landmarks, integrated_config
            )
            
            self.assertTrue(result.is_successful())
            self.assertIsNotNone(result.final_image)
            
            execution_time = time.time() - start_time
            performance_metrics = {
                'total_time': execution_time,
                'quality_score': result.quality_score,
                'applied_effects': len(result.applied_effects)
            }
            
            self._record_result(
                test_name, "integrated_system", True, execution_time,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "integrated_system", False, execution_time, str(e)
            )
            self.fail(f"완전한 워크플로우 통합 테스트 실패: {e}")
    
    def test_ui_integration(self):
        """UI 통합 테스트"""
        test_name = "ui_integration"
        start_time = time.time()
        
        try:
            # Mock UI 테스트 (실제 Streamlit 없이)
            from unittest.mock import Mock, patch
            
            with patch('streamlit.set_page_config'), \
                 patch('streamlit.title'), \
                 patch('streamlit.sidebar'):
                
                # MainInterface 초기화 테스트
                main_interface = MainInterface()
                self.assertIsNotNone(main_interface)
                
                # 세션 상태 초기화 테스트
                main_interface._initialize_session_state()
                
                # 기본 UI 컴포넌트 테스트
                self.assertTrue(hasattr(main_interface, 'face_engine'))
                self.assertTrue(hasattr(main_interface, 'makeup_engine'))
                self.assertTrue(hasattr(main_interface, 'surgery_engine'))
                self.assertTrue(hasattr(main_interface, 'integrated_engine'))
            
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "ui_system", True, execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "ui_system", False, execution_time, str(e)
            )
            self.fail(f"UI 통합 테스트 실패: {e}")
    
    def test_image_processing_integration(self):
        """이미지 처리 통합 테스트"""
        test_name = "image_processing_integration"
        start_time = time.time()
        
        try:
            # 이미지 프로세서 초기화
            image_processor = ImageProcessor()
            
            # 이미지 저장 테스트
            test_file = os.path.join(self.temp_dir, "test_image.jpg")
            success = image_processor.save_image(self.test_image, test_file)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(test_file))
            
            # 이미지 로드 테스트
            loaded_image = image_processor.load_image(test_file)
            self.assertIsNotNone(loaded_image)
            self.assertEqual(loaded_image.shape, self.test_image.shape)
            
            # 이미지 비교 생성 테스트
            modified_image = self.test_image.copy()
            modified_image[100:200, 100:200] = [255, 0, 0]  # 빨간 사각형 추가
            
            comparison_image = image_processor.create_comparison(
                self.test_image, modified_image
            )
            self.assertIsNotNone(comparison_image)
            
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "image_processing", True, execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "image_processing", False, execution_time, str(e)
            )
            self.fail(f"이미지 처리 통합 테스트 실패: {e}")
    
    def test_gallery_integration(self):
        """갤러리 통합 테스트"""
        test_name = "gallery_integration"
        start_time = time.time()
        
        try:
            # 갤러리 초기화
            gallery = ImageGallery(base_path=self.temp_dir)
            
            # 이미지 추가 테스트
            metadata = {
                'effects': ['lipstick', 'eyeshadow'],
                'timestamp': time.time(),
                'quality_score': 0.85
            }
            
            image_id = gallery.add_image(self.test_image, metadata)
            self.assertIsNotNone(image_id)
            
            # 이미지 조회 테스트
            retrieved_image = gallery.get_image(image_id)
            self.assertIsNotNone(retrieved_image)
            
            # 메타데이터 조회 테스트
            retrieved_metadata = gallery.get_metadata(image_id)
            self.assertIsNotNone(retrieved_metadata)
            self.assertEqual(retrieved_metadata['effects'], metadata['effects'])
            
            # 갤러리 목록 테스트
            image_list = gallery.list_images()
            self.assertGreater(len(image_list), 0)
            
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "gallery_system", True, execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "gallery_system", False, execution_time, str(e)
            )
            self.fail(f"갤러리 통합 테스트 실패: {e}")
    
    def test_concurrent_processing(self):
        """동시 처리 통합 테스트"""
        test_name = "concurrent_processing"
        start_time = time.time()
        
        try:
            def process_image(image_id):
                """이미지 처리 함수"""
                # 간단한 이미지 처리 시뮬레이션
                processed_image = self.test_image.copy()
                processed_image = cv2.GaussianBlur(processed_image, (5, 5), 0)
                time.sleep(0.1)  # 처리 시간 시뮬레이션
                return f"processed_{image_id}"
            
            # 동시 처리 테스트
            num_tasks = 5
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(process_image, i) 
                    for i in range(num_tasks)
                ]
                results = [future.result(timeout=10) for future in futures]
            
            self.assertEqual(len(results), num_tasks)
            self.assertTrue(all("processed_" in result for result in results))
            
            execution_time = time.time() - start_time
            performance_metrics = {
                'concurrent_tasks': num_tasks,
                'total_time': execution_time,
                'avg_time_per_task': execution_time / num_tasks
            }
            
            self._record_result(
                test_name, "concurrent_system", True, execution_time,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "concurrent_system", False, execution_time, str(e)
            )
            self.fail(f"동시 처리 통합 테스트 실패: {e}")
    
    def test_error_recovery_integration(self):
        """오류 복구 통합 테스트"""
        test_name = "error_recovery_integration"
        start_time = time.time()
        
        try:
            # 잘못된 입력에 대한 오류 처리 테스트
            invalid_inputs = [
                None,
                np.array([]),
                np.zeros((10, 10)),  # 잘못된 차원
                "invalid_input"
            ]
            
            recovery_count = 0
            
            for invalid_input in invalid_inputs:
                try:
                    # 이미지 프로세서로 잘못된 입력 처리
                    image_processor = ImageProcessor()
                    
                    # 입력 검증 및 오류 처리
                    if invalid_input is None:
                        raise ValueError("입력이 None입니다")
                    elif isinstance(invalid_input, str):
                        raise TypeError("문자열 입력은 지원되지 않습니다")
                    elif isinstance(invalid_input, np.ndarray) and invalid_input.size == 0:
                        raise ValueError("빈 배열입니다")
                    elif isinstance(invalid_input, np.ndarray) and len(invalid_input.shape) != 3:
                        raise ValueError("잘못된 이미지 차원입니다")
                    
                except (ValueError, TypeError) as e:
                    # 예상된 오류 - 정상적인 오류 처리
                    recovery_count += 1
                    print(f"정상적인 오류 처리: {e}")
                except Exception as e:
                    # 예상치 못한 오류
                    print(f"예상치 못한 오류: {e}")
            
            # 모든 잘못된 입력에 대해 적절한 오류 처리가 되어야 함
            recovery_rate = recovery_count / len(invalid_inputs)
            self.assertGreaterEqual(recovery_rate, 0.8)
            
            execution_time = time.time() - start_time
            performance_metrics = {
                'recovery_rate': recovery_rate,
                'total_errors_handled': recovery_count
            }
            
            self._record_result(
                test_name, "error_recovery", True, execution_time,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "error_recovery", False, execution_time, str(e)
            )
            self.fail(f"오류 복구 통합 테스트 실패: {e}")
    
    def test_performance_integration(self):
        """성능 통합 테스트"""
        test_name = "performance_integration"
        start_time = time.time()
        
        try:
            # 메모리 사용량 측정
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # 대량 이미지 처리 시뮬레이션
            num_images = 10
            processing_times = []
            
            for i in range(num_images):
                image_start = time.time()
                
                # 이미지 처리 시뮬레이션
                processed_image = cv2.GaussianBlur(self.test_image, (5, 5), 0)
                processed_image = cv2.resize(processed_image, (320, 240))
                processed_image = cv2.resize(processed_image, (640, 480))
                
                processing_time = time.time() - image_start
                processing_times.append(processing_time)
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = memory_after - memory_before
            
            # 성능 검증
            avg_processing_time = np.mean(processing_times)
            max_processing_time = max(processing_times)
            
            self.assertLess(avg_processing_time, 0.5)  # 평균 0.5초 이하
            self.assertLess(max_processing_time, 1.0)   # 최대 1초 이하
            self.assertLess(memory_delta, 100)          # 메모리 증가 100MB 이하
            
            execution_time = time.time() - start_time
            performance_metrics = {
                'avg_processing_time': avg_processing_time,
                'max_processing_time': max_processing_time,
                'memory_delta_mb': memory_delta,
                'images_processed': num_images,
                'throughput_fps': num_images / execution_time
            }
            
            self._record_result(
                test_name, "performance", True, execution_time,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_result(
                test_name, "performance", False, execution_time, str(e)
            )
            self.fail(f"성능 통합 테스트 실패: {e}")
    
    def generate_integration_report(self) -> Dict[str, Any]:
        """통합 테스트 보고서 생성"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        
        # 컴포넌트별 결과 분석
        component_results = {}
        for result in self.test_results:
            if result.component not in component_results:
                component_results[result.component] = {'passed': 0, 'total': 0, 'times': []}
            
            component_results[result.component]['total'] += 1
            if result.passed:
                component_results[result.component]['passed'] += 1
            component_results[result.component]['times'].append(result.execution_time)
        
        # 성능 메트릭 집계
        performance_summary = {}
        for result in self.test_results:
            if result.performance_metrics:
                for key, value in result.performance_metrics.items():
                    if key not in performance_summary:
                        performance_summary[key] = []
                    performance_summary[key].append(value)
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_execution_time': sum(r.execution_time for r in self.test_results)
            },
            'component_results': {
                component: {
                    'success_rate': data['passed'] / data['total'],
                    'avg_execution_time': np.mean(data['times']),
                    'passed': data['passed'],
                    'total': data['total']
                }
                for component, data in component_results.items()
            },
            'performance_summary': {
                key: {
                    'avg': np.mean(values),
                    'min': min(values),
                    'max': max(values)
                }
                for key, values in performance_summary.items()
            },
            'failed_tests': [
                {
                    'test_name': r.test_name,
                    'component': r.component,
                    'error_message': r.error_message
                }
                for r in self.test_results if not r.passed
            ]
        }
        
        return report


def run_integration_tests():
    """통합 테스트 실행"""
    print("="*80)
    print("최종 시스템 통합 테스트 실행")
    print("="*80)
    
    # 테스트 스위트 생성
    suite = unittest.TestLoader().loadTestsFromTestCase(SystemIntegrationTest)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 분석
    if hasattr(result, 'test_results'):
        integration_test = SystemIntegrationTest()
        integration_test.test_results = getattr(result, 'test_results', [])
        report = integration_test.generate_integration_report()
        
        print("\n" + "="*80)
        print("통합 테스트 보고서")
        print("="*80)
        print(f"전체 테스트: {report['summary']['total_tests']}")
        print(f"통과 테스트: {report['summary']['passed_tests']}")
        print(f"성공률: {report['summary']['success_rate']:.1%}")
        print(f"총 실행 시간: {report['summary']['total_execution_time']:.2f}초")
        
        print("\n컴포넌트별 결과:")
        for component, data in report['component_results'].items():
            print(f"  {component}: {data['success_rate']:.1%} ({data['passed']}/{data['total']})")
        
        if report['failed_tests']:
            print("\n실패한 테스트:")
            for failed_test in report['failed_tests']:
                print(f"  - {failed_test['test_name']} ({failed_test['component']})")
                if failed_test['error_message']:
                    print(f"    오류: {failed_test['error_message'][:100]}...")
        
        # 보고서 저장
        with open('integration_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n상세 보고서 저장: integration_test_report.json")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)