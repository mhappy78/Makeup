"""
품질 보증 테스트 실행기 및 대시보드
Task 9.2: 통합 테스트 실행 및 품질 메트릭 대시보드
"""
import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import concurrent.futures

# HTML 대시보드 생성을 위한 템플릿
HTML_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>품질 보증 대시보드</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .metric-card.success {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        }
        .metric-card.warning {
            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        }
        .metric-card.error {
            background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .test-results {
            margin-top: 30px;
        }
        .test-category {
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
        }
        .category-header {
            background: #f8f9fa;
            padding: 15px;
            font-weight: bold;
            border-bottom: 1px solid #e0e0e0;
        }
        .test-item {
            padding: 10px 15px;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .test-item:last-child {
            border-bottom: none;
        }
        .test-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-pass {
            background: #d4edda;
            color: #155724;
        }
        .status-fail {
            background: #f8d7da;
            color: #721c24;
        }
        .performance-chart {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            transition: width 0.3s ease;
        }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>자연스러운 메이크업 & 성형 시뮬레이션</h1>
            <h2>품질 보증 대시보드</h2>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card {overall_status}">
                <div class="metric-value">{overall_score:.1%}</div>
                <div class="metric-label">전체 품질 점수</div>
            </div>
            <div class="metric-card {accuracy_status}">
                <div class="metric-value">{accuracy:.1%}</div>
                <div class="metric-label">정확도</div>
            </div>
            <div class="metric-card {performance_status}">
                <div class="metric-value">{performance:.1%}</div>
                <div class="metric-label">성능</div>
            </div>
            <div class="metric-card {reliability_status}">
                <div class="metric-value">{reliability:.1%}</div>
                <div class="metric-label">신뢰성</div>
            </div>
            <div class="metric-card {usability_status}">
                <div class="metric-value">{usability:.1%}</div>
                <div class="metric-label">사용성</div>
            </div>
            <div class="metric-card {maintainability_status}">
                <div class="metric-value">{maintainability:.1%}</div>
                <div class="metric-label">유지보수성</div>
            </div>
        </div>
        
        <div class="test-results">
            <h3>테스트 결과 상세</h3>
            {test_results_html}
        </div>
        
        <div class="performance-chart">
            <h3>성능 메트릭</h3>
            {performance_metrics_html}
        </div>
        
        <div class="timestamp">
            마지막 업데이트: {timestamp}
        </div>
    </div>
</body>
</html>
"""


@dataclass
class TestExecutionResult:
    """테스트 실행 결과"""
    test_name: str
    passed: bool
    execution_time: float
    error_message: Optional[str] = None
    category: str = "unknown"
    severity: str = "medium"


@dataclass
class QualityReport:
    """품질 보고서"""
    overall_score: float
    accuracy: float
    performance: float
    reliability: float
    usability: float
    maintainability: float
    test_results: List[TestExecutionResult]
    performance_metrics: Dict[str, Any]
    timestamp: str


class TestRunner:
    """테스트 실행기"""
    
    def __init__(self):
        self.test_files = [
            "test_integrated_quality_assurance.py",
            "test_face_engine.py",
            "test_makeup_engine.py",
            "test_surgery_engine.py",
            "test_integrated_engine.py",
            "test_main_interface.py",
            "test_performance_benchmark.py",
            "test_error_handling.py"
        ]
        self.results = []
    
    def run_single_test(self, test_file: str) -> TestExecutionResult:
        """단일 테스트 파일 실행"""
        start_time = time.time()
        
        try:
            if not os.path.exists(test_file):
                return TestExecutionResult(
                    test_name=test_file,
                    passed=False,
                    execution_time=0,
                    error_message=f"테스트 파일을 찾을 수 없습니다: {test_file}",
                    category="file_error"
                )
            
            # Python 테스트 실행
            result = subprocess.run([
                sys.executable, "-m", "unittest", test_file.replace('.py', '')
            ], capture_output=True, text=True, timeout=300)
            
            execution_time = time.time() - start_time
            
            return TestExecutionResult(
                test_name=test_file,
                passed=result.returncode == 0,
                execution_time=execution_time,
                error_message=result.stderr if result.returncode != 0 else None,
                category=self._categorize_test(test_file)
            )
            
        except subprocess.TimeoutExpired:
            return TestExecutionResult(
                test_name=test_file,
                passed=False,
                execution_time=300,
                error_message="테스트 시간 초과 (5분)",
                category="timeout"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TestExecutionResult(
                test_name=test_file,
                passed=False,
                execution_time=execution_time,
                error_message=str(e),
                category="execution_error"
            )
    
    def _categorize_test(self, test_file: str) -> str:
        """테스트 파일 카테고리 분류"""
        if "performance" in test_file:
            return "performance"
        elif "integration" in test_file or "integrated" in test_file:
            return "integration"
        elif "engine" in test_file:
            return "unit"
        elif "interface" in test_file or "ui" in test_file:
            return "usability"
        elif "error" in test_file:
            return "reliability"
        else:
            return "general"
    
    def run_all_tests(self, parallel: bool = True) -> List[TestExecutionResult]:
        """모든 테스트 실행"""
        print("테스트 실행 시작...")
        
        if parallel:
            # 병렬 실행
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_test = {
                    executor.submit(self.run_single_test, test_file): test_file 
                    for test_file in self.test_files
                }
                
                results = []
                for future in concurrent.futures.as_completed(future_to_test):
                    test_file = future_to_test[future]
                    try:
                        result = future.result()
                        results.append(result)
                        status = "PASS" if result.passed else "FAIL"
                        print(f"  {test_file}: {status} ({result.execution_time:.2f}s)")
                    except Exception as e:
                        print(f"  {test_file}: ERROR - {e}")
                        results.append(TestExecutionResult(
                            test_name=test_file,
                            passed=False,
                            execution_time=0,
                            error_message=str(e)
                        ))
        else:
            # 순차 실행
            results = []
            for test_file in self.test_files:
                result = self.run_single_test(test_file)
                results.append(result)
                status = "PASS" if result.passed else "FAIL"
                print(f"  {test_file}: {status} ({result.execution_time:.2f}s)")
        
        self.results = results
        return results


class QualityAnalyzer:
    """품질 분석기"""
    
    def __init__(self):
        self.thresholds = {
            'accuracy': 0.85,
            'performance': 0.80,
            'reliability': 0.90,
            'usability': 0.75,
            'maintainability': 0.70
        }
    
    def analyze_results(self, test_results: List[TestExecutionResult]) -> QualityReport:
        """테스트 결과 분석"""
        if not test_results:
            return QualityReport(0, 0, 0, 0, 0, 0, [], {}, datetime.now().isoformat())
        
        # 기본 메트릭 계산
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.passed)
        accuracy = passed_tests / total_tests
        
        # 성능 메트릭
        avg_execution_time = sum(r.execution_time for r in test_results) / total_tests
        performance = max(0, 1 - (avg_execution_time / 10.0))  # 10초 기준
        
        # 카테고리별 분석
        category_results = {}
        for result in test_results:
            if result.category not in category_results:
                category_results[result.category] = []
            category_results[result.category].append(result)
        
        # 신뢰성: 중요 테스트 통과율
        critical_categories = ['integration', 'reliability']
        critical_tests = [r for r in test_results if r.category in critical_categories]
        if critical_tests:
            critical_passed = sum(1 for r in critical_tests if r.passed)
            reliability = critical_passed / len(critical_tests)
        else:
            reliability = accuracy
        
        # 사용성: UI 관련 테스트 통과율
        usability_tests = [r for r in test_results if r.category == 'usability']
        if usability_tests:
            usability_passed = sum(1 for r in usability_tests if r.passed)
            usability = usability_passed / len(usability_tests)
        else:
            usability = 0.8  # 기본값
        
        # 유지보수성: 오류 없는 테스트 비율
        error_free_tests = sum(1 for r in test_results if r.passed or r.error_message is None)
        maintainability = error_free_tests / total_tests
        
        # 전체 점수
        overall_score = (
            accuracy * 0.25 +
            performance * 0.20 +
            reliability * 0.25 +
            usability * 0.15 +
            maintainability * 0.15
        )
        
        # 성능 메트릭 상세
        performance_metrics = {
            'total_execution_time': sum(r.execution_time for r in test_results),
            'average_execution_time': avg_execution_time,
            'fastest_test': min(r.execution_time for r in test_results),
            'slowest_test': max(r.execution_time for r in test_results),
            'category_breakdown': {
                category: {
                    'count': len(results),
                    'passed': sum(1 for r in results if r.passed),
                    'avg_time': sum(r.execution_time for r in results) / len(results)
                }
                for category, results in category_results.items()
            }
        }
        
        return QualityReport(
            overall_score=overall_score,
            accuracy=accuracy,
            performance=performance,
            reliability=reliability,
            usability=usability,
            maintainability=maintainability,
            test_results=test_results,
            performance_metrics=performance_metrics,
            timestamp=datetime.now().isoformat()
        )


class DashboardGenerator:
    """대시보드 생성기"""
    
    def generate_html_dashboard(self, quality_report: QualityReport) -> str:
        """HTML 대시보드 생성"""
        
        def get_status_class(score: float) -> str:
            if score >= 0.8:
                return "success"
            elif score >= 0.6:
                return "warning"
            else:
                return "error"
        
        # 테스트 결과 HTML 생성
        test_results_html = self._generate_test_results_html(quality_report.test_results)
        
        # 성능 메트릭 HTML 생성
        performance_metrics_html = self._generate_performance_html(quality_report.performance_metrics)
        
        return HTML_DASHBOARD_TEMPLATE.format(
            overall_score=quality_report.overall_score,
            overall_status=get_status_class(quality_report.overall_score),
            accuracy=quality_report.accuracy,
            accuracy_status=get_status_class(quality_report.accuracy),
            performance=quality_report.performance,
            performance_status=get_status_class(quality_report.performance),
            reliability=quality_report.reliability,
            reliability_status=get_status_class(quality_report.reliability),
            usability=quality_report.usability,
            usability_status=get_status_class(quality_report.usability),
            maintainability=quality_report.maintainability,
            maintainability_status=get_status_class(quality_report.maintainability),
            test_results_html=test_results_html,
            performance_metrics_html=performance_metrics_html,
            timestamp=datetime.fromisoformat(quality_report.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _generate_test_results_html(self, test_results: List[TestExecutionResult]) -> str:
        """테스트 결과 HTML 생성"""
        # 카테고리별 그룹화
        categories = {}
        for result in test_results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        html_parts = []
        for category, results in categories.items():
            category_name = category.replace('_', ' ').title()
            passed_count = sum(1 for r in results if r.passed)
            total_count = len(results)
            
            html_parts.append(f"""
            <div class="test-category">
                <div class="category-header">
                    {category_name} ({passed_count}/{total_count} 통과)
                </div>
            """)
            
            for result in results:
                status_class = "status-pass" if result.passed else "status-fail"
                status_text = "PASS" if result.passed else "FAIL"
                error_info = f" - {result.error_message[:100]}..." if result.error_message else ""
                
                html_parts.append(f"""
                <div class="test-item">
                    <span>{result.test_name} ({result.execution_time:.2f}s){error_info}</span>
                    <span class="test-status {status_class}">{status_text}</span>
                </div>
                """)
            
            html_parts.append("</div>")
        
        return "".join(html_parts)
    
    def _generate_performance_html(self, performance_metrics: Dict[str, Any]) -> str:
        """성능 메트릭 HTML 생성"""
        html_parts = []
        
        # 전체 실행 시간
        total_time = performance_metrics.get('total_execution_time', 0)
        avg_time = performance_metrics.get('average_execution_time', 0)
        
        html_parts.append(f"""
        <div style="margin-bottom: 20px;">
            <h4>실행 시간 통계</h4>
            <p>총 실행 시간: {total_time:.2f}초</p>
            <p>평균 실행 시간: {avg_time:.2f}초</p>
        </div>
        """)
        
        # 카테고리별 성능
        category_breakdown = performance_metrics.get('category_breakdown', {})
        if category_breakdown:
            html_parts.append("<h4>카테고리별 성능</h4>")
            for category, stats in category_breakdown.items():
                category_name = category.replace('_', ' ').title()
                pass_rate = stats['passed'] / stats['count'] if stats['count'] > 0 else 0
                
                html_parts.append(f"""
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>{category_name}</span>
                        <span>{pass_rate:.1%} ({stats['passed']}/{stats['count']})</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pass_rate * 100}%"></div>
                    </div>
                    <small>평균 실행 시간: {stats['avg_time']:.2f}초</small>
                </div>
                """)
        
        return "".join(html_parts)
    
    def save_dashboard(self, quality_report: QualityReport, filename: str = "quality_dashboard.html"):
        """대시보드를 파일로 저장"""
        html_content = self.generate_html_dashboard(quality_report)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"품질 대시보드가 저장되었습니다: {filename}")
        return filename


class QualityAssuranceRunner:
    """품질 보증 실행기 메인 클래스"""
    
    def __init__(self):
        self.test_runner = TestRunner()
        self.quality_analyzer = QualityAnalyzer()
        self.dashboard_generator = DashboardGenerator()
    
    def run_full_quality_assurance(self, parallel: bool = True, 
                                 generate_dashboard: bool = True) -> QualityReport:
        """전체 품질 보증 프로세스 실행"""
        print("="*80)
        print("자연스러운 메이크업 & 성형 시뮬레이션 - 품질 보증 시스템")
        print("="*80)
        
        # 1. 테스트 실행
        print("\n1. 테스트 실행 중...")
        test_results = self.test_runner.run_all_tests(parallel=parallel)
        
        # 2. 품질 분석
        print("\n2. 품질 분석 중...")
        quality_report = self.quality_analyzer.analyze_results(test_results)
        
        # 3. 결과 출력
        print("\n3. 품질 보고서")
        print("-" * 40)
        print(f"전체 품질 점수: {quality_report.overall_score:.1%}")
        print(f"정확도: {quality_report.accuracy:.1%}")
        print(f"성능: {quality_report.performance:.1%}")
        print(f"신뢰성: {quality_report.reliability:.1%}")
        print(f"사용성: {quality_report.usability:.1%}")
        print(f"유지보수성: {quality_report.maintainability:.1%}")
        
        # 4. 품질 게이트 검증
        print("\n4. 품질 게이트 검증")
        print("-" * 40)
        gates_passed = 0
        total_gates = 5
        
        thresholds = self.quality_analyzer.thresholds
        metrics = {
            'accuracy': quality_report.accuracy,
            'performance': quality_report.performance,
            'reliability': quality_report.reliability,
            'usability': quality_report.usability,
            'maintainability': quality_report.maintainability
        }
        
        for metric, value in metrics.items():
            threshold = thresholds[metric]
            passed = value >= threshold
            if passed:
                gates_passed += 1
            status = "PASS" if passed else "FAIL"
            print(f"{metric.capitalize()}: {value:.1%} >= {threshold:.1%} [{status}]")
        
        overall_gate_passed = gates_passed >= 4  # 5개 중 4개 이상 통과
        print(f"\n전체 품질 게이트: {'PASS' if overall_gate_passed else 'FAIL'} ({gates_passed}/{total_gates})")
        
        # 5. 대시보드 생성
        if generate_dashboard:
            print("\n5. 대시보드 생성 중...")
            dashboard_file = self.dashboard_generator.save_dashboard(quality_report)
            print(f"대시보드 URL: file://{os.path.abspath(dashboard_file)}")
        
        # 6. JSON 보고서 저장
        report_file = "quality_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(quality_report), f, ensure_ascii=False, indent=2, default=str)
        print(f"상세 보고서 저장: {report_file}")
        
        print("\n" + "="*80)
        print("품질 보증 프로세스 완료")
        print("="*80)
        
        return quality_report


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="품질 보증 테스트 실행기")
    parser.add_argument("--no-parallel", action="store_true", help="병렬 실행 비활성화")
    parser.add_argument("--no-dashboard", action="store_true", help="대시보드 생성 비활성화")
    parser.add_argument("--continuous", action="store_true", help="지속적 모니터링 모드")
    
    args = parser.parse_args()
    
    runner = QualityAssuranceRunner()
    
    if args.continuous:
        print("지속적 모니터링 모드 시작... (Ctrl+C로 중지)")
        try:
            while True:
                quality_report = runner.run_full_quality_assurance(
                    parallel=not args.no_parallel,
                    generate_dashboard=not args.no_dashboard
                )
                
                # 품질 점수가 임계값 미만이면 경고
                if quality_report.overall_score < 0.75:
                    print(f"\n⚠️  경고: 품질 점수가 임계값 미만입니다! ({quality_report.overall_score:.1%})")
                
                print(f"\n다음 실행까지 대기 중... (60초)")
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n지속적 모니터링 중지됨")
    else:
        quality_report = runner.run_full_quality_assurance(
            parallel=not args.no_parallel,
            generate_dashboard=not args.no_dashboard
        )
        
        # 종료 코드 설정
        exit_code = 0 if quality_report.overall_score >= 0.75 else 1
        sys.exit(exit_code)


if __name__ == "__main__":
    main()