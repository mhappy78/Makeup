#!/usr/bin/env python3
"""
눈 및 턱선 성형 시뮬레이션 간단 테스트
"""
import cv2
import numpy as np
from typing import List
import time
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engines.surgery_engine import RealtimeSurgeryEngine
from models.core import Point3D
from models.surgery import EyeConfig, JawlineConfig, CheekboneConfig


def create_test_landmarks() -> List[Point3D]:
    """테스트용 얼굴 랜드마크 생성"""
    landmarks = []
    center_x, center_y = 320, 240
    face_width, face_height = 200, 280
    
    for i in range(468):
        angle = (i / 468.0) * 2 * np.pi
        x = center_x + np.cos(angle) * (face_width/2)
        y = center_y + np.sin(angle) * (face_height/2)
        landmarks.append(Point3D(x, y, 0))
    
    return landmarks


def create_test_image() -> np.ndarray:
    """테스트용 얼굴 이미지 생성"""
    image = np.ones((480, 640, 3), dtype=np.uint8) * 200
    center = (320, 240)
    
    # 얼굴 윤곽
    cv2.ellipse(image, center, (100, 140), 0, 0, 360, (180, 150, 120), -1)
    
    # 눈
    cv2.ellipse(image, (280, 200), (15, 8), 0, 0, 360, (50, 50, 50), -1)
    cv2.ellipse(image, (360, 200), (15, 8), 0, 0, 360, (50, 50, 50), -1)
    
    # 코
    nose_points = np.array([[320, 220], [315, 250], [325, 250]], np.int32)
    cv2.fillPoly(image, [nose_points], (160, 130, 100))
    
    # 입
    cv2.ellipse(image, (320, 290), (20, 8), 0, 0, 360, (120, 80, 80), -1)
    
    return image


def main():
    """메인 테스트 함수"""
    print("눈 및 턱선 성형 시뮬레이션 간단 테스트")
    print("=" * 50)
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 눈 성형 테스트
        print("=== 눈 성형 테스트 ===")
        eye_config = EyeConfig(size_adjustment=0.3, angle_adjustment=0.2)
        start_time = time.time()
        eye_result = engine.modify_eyes(image, landmarks, eye_config)
        eye_time = time.time() - start_time
        
        if eye_result is not None:
            print(f"  ✓ 눈 성형 성공: 처리시간 {eye_time:.3f}초")
            cv2.imwrite("test_eye_basic_result.jpg", eye_result)
        else:
            print("  ❌ 눈 성형 실패")
            return False
        
        # 턱선 성형 테스트
        print("=== 턱선 성형 테스트 ===")
        jawline_config = JawlineConfig(width_adjustment=-0.2, angle_adjustment=0.1)
        start_time = time.time()
        jawline_result = engine.modify_jawline(image, landmarks, jawline_config)
        jawline_time = time.time() - start_time
        
        if jawline_result is not None:
            print(f"  ✓ 턱선 성형 성공: 처리시간 {jawline_time:.3f}초")
            cv2.imwrite("test_jawline_basic_result.jpg", jawline_result)
        else:
            print("  ❌ 턱선 성형 실패")
            return False
        
        # 광대 성형 테스트
        print("=== 광대 성형 테스트 ===")
        cheekbone_config = CheekboneConfig(height_adjustment=-0.1, width_adjustment=-0.1)
        start_time = time.time()
        cheekbone_result = engine.modify_cheekbones(image, landmarks, cheekbone_config)
        cheekbone_time = time.time() - start_time
        
        if cheekbone_result is not None:
            print(f"  ✓ 광대 성형 성공: 처리시간 {cheekbone_time:.3f}초")
            cv2.imwrite("test_cheekbone_basic_result.jpg", cheekbone_result)
        else:
            print("  ❌ 광대 성형 실패")
            return False
        
        print("\n" + "=" * 50)
        print("✅ 모든 눈 및 턱선 성형 시뮬레이션 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)