#!/usr/bin/env python3
"""
코 성형 시뮬레이션 테스트
"""
import cv2
import numpy as np
from typing import List
import time

from engines.surgery_engine import RealtimeSurgeryEngine
from engines.face_engine import FaceEngine
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


def test_nose_height_adjustment():
    """코 높이 조정 테스트"""
    print("=== 코 높이 조정 테스트 ===")
    
    engine = RealtimeSurgeryEngine()
    image = create_test_image()
    landmarks = create_test_landmarks()
    
    # 다양한 높이 조정값 테스트
    test_values = [-0.8, -0.4, 0.0, 0.4, 0.8]
    
    for height_adj in test_values:
        config = NoseConfig(height_adjustment=height_adj)
        
        start_time = time.time()
        result_image = engine.modify_nose(image, landmarks, config)
        processing_time = time.time() - start_time
        
        print(f"높이 조정 {height_adj:+.1f}: 처리시간 {processing_time:.3f}초")
        
        # 결과 이미지 저장
        filename = f"test_nose_height_{height_adj:+.1f}.jpg".replace("+", "plus").replace("-", "minus")
        cv2.imwrite(filename, result_image)
        
        # 기본 검증
        assert result_image is not None
        assert result_image.shape == image.shape
        print(f"  ✓ 결과 이미지 저장: {filename}")


def test_nose_width_adjustment():
    """코 폭 조정 테스트"""
    print("\n=== 코 폭 조정 테스트 ===")
    
    engine = RealtimeSurgeryEngine()
    image = create_test_image()
    landmarks = create_test_landmarks()
    
    # 다양한 폭 조정값 테스트
    test_values = [-0.6, -0.3, 0.0, 0.3, 0.6]
    
    for width_adj in test_values:
        config = NoseConfig(width_adjustment=width_adj)
        
        start_time = time.time()
        result_image = engine.modify_nose(image, landmarks, config)
        processing_time = time.time() - start_time
        
        print(f"폭 조정 {width_adj:+.1f}: 처리시간 {processing_time:.3f}초")
        
        # 결과 이미지 저장
        filename = f"test_nose_width_{width_adj:+.1f}.jpg".replace("+", "plus").replace("-", "minus")
        cv2.imwrite(filename, result_image)
        
        assert result_image is not None
        assert result_image.shape == image.shape
        print(f"  ✓ 결과 이미지 저장: {filename}")


def test_nose_tip_adjustment():
    """코끝 조정 테스트"""
    print("\n=== 코끝 조정 테스트 ===")
    
    engine = RealtimeSurgeryEngine()
    image = create_test_image()
    landmarks = create_test_landmarks()
    
    # 다양한 코끝 조정값 테스트
    test_values = [-0.5, -0.2, 0.0, 0.2, 0.5]
    
    for tip_adj in test_values:
        config = NoseConfig(tip_adjustment=tip_adj)
        
        start_time = time.time()
        result_image = engine.modify_nose(image, landmarks, config)
        processing_time = time.time() - start_time
        
        print(f"코끝 조정 {tip_adj:+.1f}: 처리시간 {processing_time:.3f}초")
        
        # 결과 이미지 저장
        filename = f"test_nose_tip_{tip_adj:+.1f}.jpg".replace("+", "plus").replace("-", "minus")
        cv2.imwrite(filename, result_image)
        
        assert result_image is not None
        assert result_image.shape == image.shape
        print(f"  ✓ 결과 이미지 저장: {filename}")


def test_nose_bridge_adjustment():
    """콧대 조정 테스트"""
    print("\n=== 콧대 조정 테스트 ===")
    
    engine = RealtimeSurgeryEngine()
    image = create_test_image()
    landmarks = create_test_landmarks()
    
    # 다양한 콧대 조정값 테스트
    test_values = [-0.4, -0.2, 0.0, 0.2, 0.4]
    
    for bridge_adj in test_values:
        config = NoseConfig(bridge_adjustment=bridge_adj)
        
        start_time = time.time()
        result_image = engine.modify_nose(image, landmarks, config)
        processing_time = time.time() - start_time
        
        print(f"콧대 조정 {bridge_adj:+.1f}: 처리시간 {processing_time:.3f}초")
        
        # 결과 이미지 저장
        filename = f"test_nose_bridge_{bridge_adj:+.1f}.jpg".replace("+", "plus").replace("-", "minus")
        cv2.imwrite(filename, result_image)
        
        assert result_image is not None
        assert result_image.shape == image.shape
        print(f"  ✓ 결과 이미지 저장: {filename}")


def test_combined_nose_adjustments():
    """복합 코 조정 테스트"""
    print("\n=== 복합 코 조정 테스트 ===")
    
    engine = RealtimeSurgeryEngine()
    image = create_test_image()
    landmarks = create_test_landmarks()
    
    # 복합 조정 시나리오
    test_scenarios = [
        {
            "name": "자연스러운_코높이증가",
            "config": NoseConfig(height_adjustment=0.3, width_adjustment=-0.1)
        },
        {
            "name": "코폭축소_코끝올리기",
            "config": NoseConfig(width_adjustment=-0.4, tip_adjustment=-0.2)
        },
        {
            "name": "전체적인_코성형",
            "config": NoseConfig(
                height_adjustment=0.2,
                width_adjustment=-0.2,
                tip_adjustment=-0.1,
                bridge_adjustment=0.1
            )
        }
    ]
    
    for scenario in test_scenarios:
        start_time = time.time()
        result_image = engine.modify_nose(image, landmarks, scenario["config"])
        processing_time = time.time() - start_time
        
        print(f"{scenario['name']}: 처리시간 {processing_time:.3f}초")
        
        # 결과 이미지 저장
        filename = f"test_nose_{scenario['name']}.jpg"
        cv2.imwrite(filename, result_image)
        
        assert result_image is not None
        assert result_image.shape == image.shape
        print(f"  ✓ 결과 이미지 저장: {filename}")


def test_edge_cases():
    """경계 케이스 테스트"""
    print("\n=== 경계 케이스 테스트 ===")
    
    engine = RealtimeSurgeryEngine()
    
    # 1. 빈 이미지 테스트
    empty_image = None
    landmarks = create_test_landmarks()
    config = NoseConfig(height_adjustment=0.5)
    
    result = engine.modify_nose(empty_image, landmarks, config)
    assert result is None
    print("  ✓ 빈 이미지 처리 테스트 통과")
    
    # 2. 잘못된 이미지 형태 테스트
    invalid_image = np.ones((100, 100), dtype=np.uint8)  # 2D 이미지
    result = engine.modify_nose(invalid_image, landmarks, config)
    assert np.array_equal(result, invalid_image)
    print("  ✓ 잘못된 이미지 형태 처리 테스트 통과")
    
    # 3. 부족한 랜드마크 테스트
    few_landmarks = [Point3D(100, 100, 0) for _ in range(10)]
    image = create_test_image()
    result = engine.modify_nose(image, few_landmarks, config)
    assert np.array_equal(result, image)
    print("  ✓ 부족한 랜드마크 처리 테스트 통과")
    
    # 4. 극단적인 조정값 테스트
    extreme_config = NoseConfig(
        height_adjustment=1.0,
        width_adjustment=-1.0,
        tip_adjustment=1.0,
        bridge_adjustment=-1.0
    )
    result = engine.modify_nose(image, landmarks, extreme_config)
    assert result is not None
    assert result.shape == image.shape
    print("  ✓ 극단적인 조정값 처리 테스트 통과")


def test_performance():
    """성능 테스트"""
    print("\n=== 성능 테스트 ===")
    
    engine = RealtimeSurgeryEngine()
    image = create_test_image()
    landmarks = create_test_landmarks()
    config = NoseConfig(height_adjustment=0.3, width_adjustment=-0.2)
    
    # 여러 번 실행하여 평균 성능 측정
    times = []
    num_tests = 10
    
    for i in range(num_tests):
        start_time = time.time()
        result = engine.modify_nose(image, landmarks, config)
        end_time = time.time()
        
        times.append(end_time - start_time)
        assert result is not None
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"  평균 처리시간: {avg_time:.3f}초")
    print(f"  최소 처리시간: {min_time:.3f}초")
    print(f"  최대 처리시간: {max_time:.3f}초")
    
    # 실시간 처리 가능 여부 확인 (30fps 기준)
    target_fps = 30
    target_time = 1.0 / target_fps
    
    if avg_time < target_time:
        print(f"  ✓ 실시간 처리 가능 ({target_fps}fps 기준)")
    else:
        print(f"  ⚠ 실시간 처리 어려움 (목표: {target_time:.3f}초, 실제: {avg_time:.3f}초)")


def main():
    """메인 테스트 함수"""
    print("코 성형 시뮬레이션 테스트 시작")
    print("=" * 50)
    
    try:
        test_nose_height_adjustment()
        test_nose_width_adjustment()
        test_nose_tip_adjustment()
        test_nose_bridge_adjustment()
        test_combined_nose_adjustments()
        test_edge_cases()
        test_performance()
        
        print("\n" + "=" * 50)
        print("✅ 모든 코 성형 시뮬레이션 테스트 통과!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)