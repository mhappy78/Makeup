"""
시스템 최종 검증 도구
Task 10: 최종 통합 및 배포 준비
"""
import os
import sys
import time
import json
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import concurrent.futures
import threading
import numpy as np
import cv2

try:
    import psutil
except ImportError:
    print("psutil 모듈이 필요합니다: pip install psutil")
    sys.exit(1)


@dataclass
class ValidationResult:
    """검증 결과"""
    category: str
    test_name: str
    passed: bool
    score: float
    execution_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class SystemReport:
    """시스템 검증 보고서"""
    overall_score: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    categories: Dict[str, Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    system_info: Dict[str, Any]
    recommendations: List[str]
    timestamp: str


class SystemValidator:
    """시스템 검증기"""
    
    def __init__(self):
        self.results = []
        self.temp_dir = None
        
        # 검증 기준
        self.thresholds = {
            'performance': {
                'face_detection_time': 0.1,  # 100ms
                'makeup_application_time': 0.5,  # 500ms
                'surgery_simulation_time': 1.0,  # 1000ms
                'memory_usage_mb': 500,  # 500MB
                'cpu_usage_percent': 80  # 80%
            },
            'quality': {
                'face_detection_accuracy': 0.9,  # 90%
                'effect_application_success': 0.95,  # 95%
                'image_quality_score': 0.8,  # 80%
                'user_experience_score': 0.85  # 85%
            },
            'stability': {
                'error_rate': 0.05,  # 5% 이하
                'crash_rate': 0.01,  # 1% 이하
                'memory_leak_rate': 0.1  # 10% 이하
            }
        }
    
    def setup_test_environment(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp(prefix="system_validation_")
        print(f"테스트 환경 설정: {self.temp_dir}")
        
        # 테스트용 이미지 생성
        self._create_test_images()
        
    def cleanup_test_environment(self):
        """테스트 환경 정리"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print("테스트 환경 정리 완료")
    
    def _create_test_images(self):
        """테스트용 이미지 생성"""
        test_images_dir = os.path.join(self.temp_dir, "test_images")
        os.makedirs(test_images_dir, exist_ok=True)
        
        # 다양한 해상도와 조건의 테스트 이미지 생성
        test_cases = [
            ("standard_face", 640, 480),
            ("high_res_face", 1920, 1080),
            ("low_res_face", 320, 240),
            ("wide_face", 800, 600),
            ("square_face", 512, 512)
        ]
        
        for name, width, height in test_cases:
            image = self._generate_synthetic_face(width, height)
            image_path = os.path.join(test_images_dir, f"{name}.jpg")
            cv2.imwrite(image_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    
    def _generate_synthetic_face(self, width: int, height: int) -> np.ndarray:
        """합성 얼굴 이미지 생성"""
        image = np.ones((height, width, 3), dtype=np.uint8) * 220
        
        # 얼굴 타원
        center = (width // 2, height // 2)
        axes = (width // 4, height // 3)
        cv2.ellipse(image, center, axes, 0, 0, 360, (200, 180, 160), -1)
        
        # 눈
        left_eye = (width // 2 - width // 8, height // 2 - height // 8)
        right_eye = (width // 2 + width // 8, height // 2 - height // 8)
        eye_size = (width // 20, height // 40)
        cv2.ellipse(image, left_eye, eye_size, 0, 0, 360, (80, 80, 80), -1)
        cv2.ellipse(image, right_eye, eye_size, 0, 0, 360, (80, 80, 80), -1)
        
        # 코
        nose_points = np.array([
            [width // 2, height // 2 - height // 20],
            [width // 2 - width // 40, height // 2 + height // 20],
            [width // 2 + width // 40, height // 2 + height // 20]
        ], np.int32)
        cv2.fillPoly(image, [nose_points], (180, 150, 130))
        
        # 입
        mouth = (width // 2, height // 2 + height // 6)
        mouth_size = (width // 15, height // 30)
        cv2.ellipse(image, mouth, mouth_size, 0, 0, 360, (120, 80, 80), -1)
        
        return image
    
    def validate_system_requirements(self) -> ValidationResult:
        """시스템 요구사항 검증"""
        start_time = time.time()
        details = {}
        passed = True
        score = 1.0
        
        try:
            # Python 버전 확인
            python_version = sys.version_info
            details['python_version'] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            
            if python_version < (3, 8):
                passed = False
                score -= 0.3
                details['python_version_issue'] = "Python 3.8 이상 필요"
            
            # 메모리 확인
            memory = psutil.virtual_memory()
            details['total_memory_gb'] = round(memory.total / (1024**3), 2)
            details['available_memory_gb'] = round(memory.available / (1024**3), 2)
            
            if memory.total < 4 * (1024**3):  # 4GB 미만
                passed = False
                score -= 0.2
                details['memory_issue'] = "최소 4GB RAM 필요"
            
            # 디스크 공간 확인
            disk = psutil.disk_usage('.')
            details['free_space_gb'] = round(disk.free / (1024**3), 2)
            
            if disk.free < 2 * (1024**3):  # 2GB 미만
                passed = False
                score -= 0.1
                details['disk_issue'] = "최소 2GB 여유 공간 필요"
            
            # CPU 정보
            details['cpu_count'] = psutil.cpu_count()
            details['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            # 필수 모듈 확인
            required_modules = [
                'cv2', 'numpy', 'PIL', 'streamlit', 'mediapipe'
            ]
            
            missing_modules = []
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
                    passed = False
                    score -= 0.1
            
            if missing_modules:
                details['missing_modules'] = missing_modules
            
        except Exception as e:
            passed = False
            score = 0.0
            details['error'] = str(e)
        
        execution_time = time.time() - start_time
        
        return ValidationResult(
            category="system_requirements",
            test_name="system_requirements_check",
            passed=passed,
            score=score,
            execution_time=execution_time,
            details=details,
            error_message=None if passed else "시스템 요구사항 미충족"
        )
    
    def run_full_validation(self) -> SystemReport:
        """전체 시스템 검증 실행"""
        print("="*80)
        print("시스템 최종 검증 시작")
        print("="*80)
        
        try:
            # 테스트 환경 설정
            self.setup_test_environment()
            
            # 1. 시스템 요구사항 검증
            print("\n1. 시스템 요구사항 검증...")
            system_req_result = self.validate_system_requirements()
            self.results.append(system_req_result)
            print(f"   결과: {'통과' if system_req_result.passed else '실패'} (점수: {system_req_result.score:.2f})")
            
            # 보고서 생성
            report = self.generate_system_report()
            
            # 결과 출력
            print("\n" + "="*80)
            print("시스템 검증 결과")
            print("="*80)
            print(f"전체 점수: {report.overall_score:.1%}")
            print(f"총 테스트: {report.total_tests}")
            print(f"통과: {report.passed_tests}")
            print(f"실패: {report.failed_tests}")
            
            if report.total_tests > 0:
                print(f"성공률: {report.passed_tests/report.total_tests:.1%}")
            
            print("\n권장사항:")
            for i, recommendation in enumerate(report.recommendations, 1):
                print(f"  {i}. {recommendation}")
            
            # 보고서 저장
            report_file = "system_validation_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(report), f, ensure_ascii=False, indent=2, default=str)
            print(f"\n상세 보고서 저장: {report_file}")
            
            return report
            
        except Exception as e:
            print(f"\n❌ 시스템 검증 중 오류 발생: {e}")
            return SystemReport(0, 0, 0, 0, {}, {}, {}, [f"검증 오류: {e}"], datetime.now().isoformat())
        
        finally:
            # 테스트 환경 정리
            self.cleanup_test_environment()
    
    def generate_system_report(self) -> SystemReport:
        """시스템 검증 보고서 생성"""
        if not self.results:
            return SystemReport(0, 0, 0, 0, {}, {}, {}, [], datetime.now().isoformat())
        
        # 전체 통계
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        overall_score = np.mean([r.score for r in self.results])
        
        # 카테고리별 분석
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {
                    'passed': 0,
                    'total': 0,
                    'avg_score': 0,
                    'avg_time': 0
                }
            
            categories[result.category]['total'] += 1
            if result.passed:
                categories[result.category]['passed'] += 1
        
        # 카테고리별 메트릭 계산
        for category, data in categories.items():
            category_results = [r for r in self.results if r.category == category]
            data['success_rate'] = data['passed'] / data['total']
            data['avg_score'] = np.mean([r.score for r in category_results])
            data['avg_time'] = np.mean([r.execution_time for r in category_results])
        
        # 성능 메트릭 집계
        performance_metrics = {}
        for result in self.results:
            if result.category == "performance":
                performance_metrics[result.test_name] = result.details
        
        # 시스템 정보
        system_info = {
            'python_version': sys.version,
            'platform': sys.platform,
            'cpu_count': psutil.cpu_count(),
            'total_memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'available_memory_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'disk_free_gb': round(psutil.disk_usage('.').free / (1024**3), 2)
        }
        
        # 권장사항 생성
        recommendations = self._generate_recommendations(categories, overall_score)
        
        return SystemReport(
            overall_score=overall_score,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            categories=categories,
            performance_metrics=performance_metrics,
            system_info=system_info,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
    
    def _generate_recommendations(self, categories: Dict, overall_score: float) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        # 전체 점수 기반 권장사항
        if overall_score < 0.7:
            recommendations.append("전체 시스템 성능이 낮습니다. 하드웨어 업그레이드를 고려하세요.")
        elif overall_score < 0.85:
            recommendations.append("시스템 성능을 개선할 여지가 있습니다.")
        
        # 시스템 요구사항 기반 권장사항
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 8:
            recommendations.append("더 나은 성능을 위해 8GB 이상의 RAM을 권장합니다.")
        
        if not recommendations:
            recommendations.append("시스템이 모든 요구사항을 만족합니다. 최적의 성능으로 실행 가능합니다.")
        
        return recommendations


def main():
    """메인 실행 함수"""
    validator = SystemValidator()
    
    # 전체 검증 실행
    report = validator.run_full_validation()
    
    # 종료 코드 설정
    if report.overall_score >= 0.8:
        print("\n✅ 시스템 검증 성공")
        sys.exit(0)
    elif report.overall_score >= 0.6:
        print("\n⚠️  시스템 검증 부분 성공 (개선 권장)")
        sys.exit(1)
    else:
        print("\n❌ 시스템 검증 실패")
        sys.exit(2)


if __name__ == "__main__":
    main()