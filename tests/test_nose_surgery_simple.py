#!/usr/bin/env python3
"""
코 성형 시뮬레이션 간단 테스트
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
from models.surgery import NoseConfig


def create_test_landmarks() -> List[Point3D]:
    """테스트용 얼굴 랜드마크 생성 (MediaPipe 468개 포인트)"""
    landmarks = []
    
    # 기본 얼굴 형태의 랜드마크 생성 (간단한 타원형)
    center_x, center_y = 320, 240
    face_width, face_height = 200, 280
    
    for i in range(468):
        # 각 랜드마크 포인트를 얼굴 영역 내에 배치
        angle = (i / 468.0) * 2 * np.pi
        
        if i in [1, 2, 5]:  # 코끝 영역
            x = center_x + np.cos(angle) * 10
            y = center_y - 20 + np.sin(angle) * 5
        elif i in [6, 19, 20]:  # 콧대 영역
            x = center_x + np.cos(angle) * 8
            y = center_y - 40 + np.sin(angle) * 15
        elif i in range(278, 303):  # 콧구멍 영역
            side = 1 if i < 290 else -1
            x = center_x + side * 15 + np.cos(angle) * 5
            y = center_y - 10 + np.sin(angle) * 3
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
    
    return image


def test_nose_surgery_basic():
    """기본 코 성형 테스트"""
    print("=== 기본 코 성형 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 기본 코 높이 조정 테스트
        config = NoseConfig(height_adjustment=0.3)
        
        start_time = time.time()
        result_image = engine.modify_nose(image, landmarks, config)
        processing_time = time.time() - start_time
        
        print(f"코 높이 조정 테스트: 처리시간 {processing_time:.3f}초")
        
        # 결과 검증
        if result_image is not None:
            print("  ✓ 코 성형 시뮬레이션 성공")
            print(f"  ✓ 결과 이미지 크기: {result_image.shape}")
            
            # 결과 이미지 저장
            cv2.imwrite("test_nose_basic_result.jpg", result_image)
            print("  ✓ 결과 이미지 저장: test_nose_basic_result.jpg")
            
            return True
        else:
            print("  ❌ 코 성형 시뮬레이션 실패")
            return False
            
    except Exception as e:
        print(f"  ❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nose_adjustments():
    """다양한 코 조정 테스트"""
    print("\n=== 다양한 코 조정 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 테스트 시나리오
        test_scenarios = [
            {"name": "높이증가", "config": NoseConfig(height_adjustment=0.5)},
            {"name": "폭축소", "config": NoseConfig(width_adjustment=-0.3)},
            {"name": "코끝조정", "config": NoseConfig(tip_adjustment=0.2)},
            {"name": "콧대조정", "config": NoseConfig(bridge_adjustment=0.1)},
            {"name": "복합조정", "config": NoseConfig(
                height_adjustment=0.2,
                width_adjustment=-0.2,
                tip_adjustment=-0.1,
                bridge_adjustment=0.1
            )}
        ]
        
        success_count = 0
        
        for scenario in test_scenarios:
            try:
                start_time = time.time()
                result_image = engine.modify_nose(image, landmarks, scenario["config"])
                processing_time = time.time() - start_time
                
                if result_image is not None and result_image.shape == image.shape:
                    print(f"  ✓ {scenario['name']}: 처리시간 {processing_time:.3f}초")
                    
                    # 결과 이미지 저장
                    filename = f"test_nose_{scenario['name']}.jpg"
                    cv2.imwrite(filename, result_image)
                    
                    success_count += 1
                else:
                    print(f"  ❌ {scenario['name']}: 실패")
                    
            except Exception as e:
                print(f"  ❌ {scenario['name']}: 오류 - {e}")
        
        print(f"\n총 {len(test_scenarios)}개 시나리오 중 {success_count}개 성공")
        return success_count == len(test_scenarios)
        
    except Exception as e:
        print(f"  ❌ 테스트 중 오류 발생: {e}")
        return False


def test_edge_cases():
    """경계 케이스 테스트"""
    print("\n=== 경계 케이스 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        
        # 1. 빈 이미지 테스트
        empty_image = None
        landmarks = create_test_landmarks()
        config = NoseConfig(height_adjustment=0.5)
        
        result = engine.modify_nose(empty_image, landmarks, config)
        if result is None:
            print("  ✓ 빈 이미지 처리 테스트 통과")
        else:
            print("  ❌ 빈 이미지 처리 테스트 실패")
            return False
        
        # 2. 잘못된 이미지 형태 테스트
        invalid_image = np.ones((100, 100), dtype=np.uint8)  # 2D 이미지
        result = engine.modify_nose(invalid_image, landmarks, config)
        if np.array_equal(result, invalid_image):
            print("  ✓ 잘못된 이미지 형태 처리 테스트 통과")
        else:
            print("  ❌ 잘못된 이미지 형태 처리 테스트 실패")
            return False
        
        # 3. 부족한 랜드마크 테스트
        few_landmarks = [Point3D(100, 100, 0) for _ in range(10)]
        image = create_test_image()
        result = engine.modify_nose(image, few_landmarks, config)
        if np.array_equal(result, image):
            print("  ✓ 부족한 랜드마크 처리 테스트 통과")
        else:
            print("  ❌ 부족한 랜드마크 처리 테스트 실패")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 경계 케이스 테스트 중 오류 발생: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("코 성형 시뮬레이션 간단 테스트 시작")
    print("=" * 50)
    
    try:
        # 기본 테스트
        basic_success = test_nose_surgery_basic()
        
        # 다양한 조정 테스트
        adjustments_success = test_nose_adjustments()
        
        # 경계 케이스 테스트
        edge_cases_success = test_edge_cases()
        
        # 결과 요약
        print("\n" + "=" * 50)
        if basic_success and adjustments_success and edge_cases_success:
            print("✅ 모든 코 성형 시뮬레이션 테스트 통과!")
            return True
        else:
            print("❌ 일부 테스트 실패")
            print(f"  기본 테스트: {'✓' if basic_success else '❌'}")
            print(f"  조정 테스트: {'✓' if adjustments_success else '❌'}")
            print(f"  경계 케이스: {'✓' if edge_cases_success else '❌'}")
            return False
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)