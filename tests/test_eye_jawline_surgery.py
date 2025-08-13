#!/usr/bin/env python3
"""
눈 및 턱선 성형 시뮬레이션 테스트
"""
import cv2
import numpy as np
from typing import List
import time
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import directly from the surgery engine file
from engines.surgery_engine import RealtimeSurgeryEngine
from models.core import Point3D
from models.surgery import EyeConfig, JawlineConfig, CheekboneConfig, SurgeryConfig, NoseConfig


def create_test_landmarks() -> List[Point3D]:
    """테스트용 얼굴 랜드마크 생성 (MediaPipe 468개 포인트)"""
    landmarks = []
    
    # 기본 얼굴 형태의 랜드마크 생성 (간단한 타원형)
    center_x, center_y = 320, 240
    face_width, face_height = 200, 280
    
    for i in range(468):
        # 각 랜드마크 포인트를 얼굴 영역 내에 배치
        angle = (i / 468.0) * 2 * np.pi
        
        if i in [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]:  # 왼쪽 눈
            x = center_x - 40 + np.cos(angle) * 15
            y = center_y - 40 + np.sin(angle) * 8
        elif i in [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]:  # 오른쪽 눈
            x = center_x + 40 + np.cos(angle) * 15
            y = center_y - 40 + np.sin(angle) * 8
        elif i in [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323]:  # 턱선
            x = center_x + np.cos(angle) * (face_width/2)
            y = center_y + 80 + np.sin(angle) * 20
        elif i in [116, 117, 118, 119, 120, 121, 345, 346, 347, 348, 349, 350]:  # 광대
            side = -1 if i < 200 else 1
            x = center_x + side * 60 + np.cos(angle) * 10
            y = center_y + np.sin(angle) * 10
        else:  # 기타 얼굴 영역
            x = center_x + np.cos(angle) * (face_width/2)
            y = center_y + np.sin(angle) * (face_height/2)
        
        landmarks.append(Point3D(x, y, 0))
    
    return landmarks


def create_test_image() -> np.ndarray:
    """테스트용 얼굴 이미지 생성"""
    # 640x480 크기의 테스트 이미지 생성
    image = np.ones((480, 640, 3), dtype=np.uint8) * 200
    
    # 간단한 얼굴 형태 그리기
    center = (320, 240)
    
    # 얼굴 윤곽
    cv2.ellipse(image, center, (100, 140), 0, 0, 360, (180, 150, 120), -1)
    
    # 눈
    cv2.ellipse(image, (280, 200), (15, 8), 0, 0, 360, (50, 50, 50), -1)
    cv2.ellipse(image, (360, 200), (15, 8), 0, 0, 360, (50, 50, 50), -1)
    
    # 코
    nose_points = np.array([
        [320, 220], [315, 250], [325, 250]
    ], np.int32)
    cv2.fillPoly(image, [nose_points], (160, 130, 100))
    
    # 입
    cv2.ellipse(image, (320, 290), (20, 8), 0, 0, 360, (120, 80, 80), -1)
    
    # 턱선 강조
    jaw_points = np.array([
        [220, 320], [320, 360], [420, 320]
    ], np.int32)
    cv2.polylines(image, [jaw_points], False, (140, 120, 100), 2)
    
    return image


def test_eye_surgery():
    """눈 성형 테스트"""
    print("=== 눈 성형 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 테스트 시나리오
        test_scenarios = [
            {"name": "눈크기확대", "config": EyeConfig(size_adjustment=0.5)},
            {"name": "눈크기축소", "config": EyeConfig(size_adjustment=-0.3)},
            {"name": "눈모양날카롭게", "config": EyeConfig(shape_adjustment=0.4)},
            {"name": "눈모양둥글게", "config": EyeConfig(shape_adjustment=-0.4)},
            {"name": "눈간격좁히기", "config": EyeConfig(position_adjustment=0.3)},
            {"name": "눈간격넓히기", "config": EyeConfig(position_adjustment=-0.3)},
            {"name": "눈꼬리올리기", "config": EyeConfig(angle_adjustment=0.4)},
            {"name": "눈꼬리내리기", "config": EyeConfig(angle_adjustment=-0.4)},
            {"name": "복합눈성형", "config": EyeConfig(
                size_adjustment=0.2,
                shape_adjustment=0.1,
                position_adjustment=-0.1,
                angle_adjustment=0.2
            )}
        ]
        
        success_count = 0
        
        for scenario in test_scenarios:
            try:
                start_time = time.time()
                result_image = engine.modify_eyes(image, landmarks, scenario["config"])
                processing_time = time.time() - start_time
                
                if result_image is not None and result_image.shape == image.shape:
                    print(f"  ✓ {scenario['name']}: 처리시간 {processing_time:.3f}초")
                    
                    # 결과 이미지 저장
                    filename = f"test_eye_{scenario['name']}.jpg"
                    cv2.imwrite(filename, result_image)
                    
                    success_count += 1
                else:
                    print(f"  ❌ {scenario['name']}: 실패")
                    
            except Exception as e:
                print(f"  ❌ {scenario['name']}: 오류 - {e}")
        
        print(f"눈 성형: {len(test_scenarios)}개 시나리오 중 {success_count}개 성공")
        return success_count == len(test_scenarios)
        
    except Exception as e:
        print(f"  ❌ 눈 성형 테스트 중 오류 발생: {e}")
        return False


def test_jawline_surgery():
    """턱선 성형 테스트"""
    print("\n=== 턱선 성형 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 테스트 시나리오
        test_scenarios = [
            {"name": "턱선폭넓히기", "config": JawlineConfig(width_adjustment=0.4)},
            {"name": "턱선폭좁히기", "config": JawlineConfig(width_adjustment=-0.4)},
            {"name": "턱선각도조정", "config": JawlineConfig(angle_adjustment=0.3)},
            {"name": "턱선길이늘리기", "config": JawlineConfig(length_adjustment=0.3)},
            {"name": "턱선길이줄이기", "config": JawlineConfig(length_adjustment=-0.3)},
            {"name": "복합턱선성형", "config": JawlineConfig(
                width_adjustment=-0.2,
                angle_adjustment=0.1,
                length_adjustment=-0.1
            )}
        ]
        
        success_count = 0
        
        for scenario in test_scenarios:
            try:
                start_time = time.time()
                result_image = engine.modify_jawline(image, landmarks, scenario["config"])
                processing_time = time.time() - start_time
                
                if result_image is not None and result_image.shape == image.shape:
                    print(f"  ✓ {scenario['name']}: 처리시간 {processing_time:.3f}초")
                    
                    # 결과 이미지 저장
                    filename = f"test_jawline_{scenario['name']}.jpg"
                    cv2.imwrite(filename, result_image)
                    
                    success_count += 1
                else:
                    print(f"  ❌ {scenario['name']}: 실패")
                    
            except Exception as e:
                print(f"  ❌ {scenario['name']}: 오류 - {e}")
        
        print(f"턱선 성형: {len(test_scenarios)}개 시나리오 중 {success_count}개 성공")
        return success_count == len(test_scenarios)
        
    except Exception as e:
        print(f"  ❌ 턱선 성형 테스트 중 오류 발생: {e}")
        return False


def test_cheekbone_surgery():
    """광대 성형 테스트"""
    print("\n=== 광대 성형 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 테스트 시나리오
        test_scenarios = [
            {"name": "광대높이올리기", "config": CheekboneConfig(height_adjustment=0.4)},
            {"name": "광대높이내리기", "config": CheekboneConfig(height_adjustment=-0.4)},
            {"name": "광대폭넓히기", "config": CheekboneConfig(width_adjustment=0.3)},
            {"name": "광대폭좁히기", "config": CheekboneConfig(width_adjustment=-0.3)},
            {"name": "광대돌출증가", "config": CheekboneConfig(prominence_adjustment=0.3)},
            {"name": "광대돌출감소", "config": CheekboneConfig(prominence_adjustment=-0.3)},
            {"name": "복합광대성형", "config": CheekboneConfig(
                height_adjustment=-0.2,
                width_adjustment=-0.1,
                prominence_adjustment=-0.2
            )}
        ]
        
        success_count = 0
        
        for scenario in test_scenarios:
            try:
                start_time = time.time()
                result_image = engine.modify_cheekbones(image, landmarks, scenario["config"])
                processing_time = time.time() - start_time
                
                if result_image is not None and result_image.shape == image.shape:
                    print(f"  ✓ {scenario['name']}: 처리시간 {processing_time:.3f}초")
                    
                    # 결과 이미지 저장
                    filename = f"test_cheekbone_{scenario['name']}.jpg"
                    cv2.imwrite(filename, result_image)
                    
                    success_count += 1
                else:
                    print(f"  ❌ {scenario['name']}: 실패")
                    
            except Exception as e:
                print(f"  ❌ {scenario['name']}: 오류 - {e}")
        
        print(f"광대 성형: {len(test_scenarios)}개 시나리오 중 {success_count}개 성공")
        return success_count == len(test_scenarios)
        
    except Exception as e:
        print(f"  ❌ 광대 성형 테스트 중 오류 발생: {e}")
        return False


def test_full_surgery():
    """전체 성형 시뮬레이션 테스트"""
    print("\n=== 전체 성형 시뮬레이션 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 전체 성형 설정
        full_config = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.2, width_adjustment=-0.1),
            eyes=EyeConfig(size_adjustment=0.3, angle_adjustment=0.2),
            jawline=JawlineConfig(width_adjustment=-0.2, angle_adjustment=0.1),
            cheekbones=CheekboneConfig(height_adjustment=-0.1, width_adjustment=-0.1)
        )
        
        start_time = time.time()
        result = engine.apply_full_surgery(image, landmarks, full_config)
        processing_time = time.time() - start_time
        
        if result and result.is_successful():
            print(f"  ✓ 전체 성형 시뮬레이션 성공: 처리시간 {processing_time:.3f}초")
            print(f"  ✓ 적용된 효과: {', '.join(result.applied_modifications)}")
            print(f"  ✓ 자연스러움 점수: {result.natural_score:.2f}")
            
            # 결과 이미지 저장
            cv2.imwrite("test_full_surgery_result.jpg", result.image)
            
            return True
        else:
            print("  ❌ 전체 성형 시뮬레이션 실패")
            return False
            
    except Exception as e:
        print(f"  ❌ 전체 성형 테스트 중 오류 발생: {e}")
        return False


def test_edge_cases():
    """경계 케이스 테스트"""
    print("\n=== 경계 케이스 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        
        # 1. 빈 이미지 테스트
        empty_image = None
        landmarks = create_test_landmarks()
        eye_config = EyeConfig(size_adjustment=0.5)
        
        result = engine.modify_eyes(empty_image, landmarks, eye_config)
        if result is None:
            print("  ✓ 빈 이미지 처리 테스트 통과")
        else:
            print("  ❌ 빈 이미지 처리 테스트 실패")
            return False
        
        # 2. 부족한 랜드마크 테스트
        few_landmarks = [Point3D(100, 100, 0) for _ in range(10)]
        image = create_test_image()
        result = engine.modify_eyes(image, few_landmarks, eye_config)
        if np.array_equal(result, image):
            print("  ✓ 부족한 랜드마크 처리 테스트 통과")
        else:
            print("  ❌ 부족한 랜드마크 처리 테스트 실패")
            return False
        
        # 3. 극단적인 조정값 테스트
        extreme_eye_config = EyeConfig(
            size_adjustment=1.0,
            shape_adjustment=-1.0,
            position_adjustment=1.0,
            angle_adjustment=-1.0
        )
        result = engine.modify_eyes(image, landmarks, extreme_eye_config)
        if result is not None and result.shape == image.shape:
            print("  ✓ 극단적인 조정값 처리 테스트 통과")
        else:
            print("  ❌ 극단적인 조정값 처리 테스트 실패")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 경계 케이스 테스트 중 오류 발생: {e}")
        return False


def test_performance():
    """성능 테스트"""
    print("\n=== 성능 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 각 성형 타입별 성능 테스트
        configs = {
            "눈": EyeConfig(size_adjustment=0.3, angle_adjustment=0.2),
            "턱선": JawlineConfig(width_adjustment=-0.2, angle_adjustment=0.1),
            "광대": CheekboneConfig(height_adjustment=-0.1, width_adjustment=-0.1)
        }
        
        for surgery_type, config in configs.items():
            times = []
            num_tests = 5
            
            for i in range(num_tests):
                start_time = time.time()
                
                if surgery_type == "눈":
                    result = engine.modify_eyes(image, landmarks, config)
                elif surgery_type == "턱선":
                    result = engine.modify_jawline(image, landmarks, config)
                elif surgery_type == "광대":
                    result = engine.modify_cheekbones(image, landmarks, config)
                
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"  {surgery_type} 성형 - 평균: {avg_time:.3f}초, 최소: {min_time:.3f}초, 최대: {max_time:.3f}초")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 성능 테스트 중 오류 발생: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("눈 및 턱선 성형 시뮬레이션 테스트 시작")
    print("=" * 60)
    
    try:
        # 개별 성형 테스트
        eye_success = test_eye_surgery()
        jawline_success = test_jawline_surgery()
        cheekbone_success = test_cheekbone_surgery()
        
        # 전체 성형 테스트
        full_surgery_success = test_full_surgery()
        
        # 경계 케이스 테스트
        edge_cases_success = test_edge_cases()
        
        # 성능 테스트
        performance_success = test_performance()
        
        # 결과 요약
        print("\n" + "=" * 60)
        if all([eye_success, jawline_success, cheekbone_success, full_surgery_success, edge_cases_success, performance_success]):
            print("✅ 모든 눈 및 턱선 성형 시뮬레이션 테스트 통과!")
            return True
        else:
            print("❌ 일부 테스트 실패")
            print(f"  눈 성형: {'✓' if eye_success else '❌'}")
            print(f"  턱선 성형: {'✓' if jawline_success else '❌'}")
            print(f"  광대 성형: {'✓' if cheekbone_success else '❌'}")
            print(f"  전체 성형: {'✓' if full_surgery_success else '❌'}")
            print(f"  경계 케이스: {'✓' if edge_cases_success else '❌'}")
            print(f"  성능 테스트: {'✓' if performance_success else '❌'}")
            return False
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)