#!/usr/bin/env python3
"""
성형 시뮬레이션 엔진 검증 테스트
"""

import sys
import os
import numpy as np
import cv2
import time

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.surgery_engine import RealtimeSurgeryEngine, ThinPlateSpline, MeshWarper
from models.core import Point3D
from models.surgery import SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig


def create_test_image():
    """테스트용 이미지 생성"""
    # 간단한 테스트 이미지 생성 (640x480, 3채널)
    image = np.ones((480, 640, 3), dtype=np.uint8) * 128
    
    # 얼굴 모양 그리기 (타원)
    center = (320, 240)
    axes = (120, 160)
    cv2.ellipse(image, center, axes, 0, 0, 360, (200, 180, 160), -1)
    
    return image


def create_test_landmarks():
    """테스트용 랜드마크 생성 (468개)"""
    landmarks = []
    
    # MediaPipe 468개 랜드마크를 시뮬레이션
    # 얼굴 중심을 (320, 240)으로 설정
    center_x, center_y = 320, 240
    
    for i in range(468):
        # 타원 형태로 랜드마크 분포
        angle = (i / 468.0) * 2 * np.pi
        radius_x = 100 + np.random.normal(0, 10)
        radius_y = 130 + np.random.normal(0, 10)
        
        x = center_x + radius_x * np.cos(angle)
        y = center_y + radius_y * np.sin(angle)
        z = np.random.normal(0, 5)
        
        landmarks.append(Point3D(x, y, z))
    
    return landmarks


def test_thin_plate_spline():
    """TPS 알고리즘 테스트"""
    print("=== Thin Plate Spline 테스트 ===")
    
    try:
        # 간단한 제어점 생성
        source_points = np.array([[0, 0], [100, 0], [100, 100], [0, 100]])
        target_points = np.array([[10, 10], [90, 10], [90, 90], [10, 90]])
        
        # TPS 생성
        tps = ThinPlateSpline(source_points, target_points)
        
        # 변형 테스트
        test_points = np.array([[50, 50], [25, 25], [75, 75]])
        transformed = tps.transform_points(test_points)
        
        print(f"  ✓ TPS 변형 성공")
        print(f"  ✓ 원본 점: {test_points}")
        print(f"  ✓ 변형 점: {transformed}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ TPS 테스트 실패: {e}")
        return False


def test_mesh_warper():
    """메시 워퍼 테스트"""
    print("\n=== 메시 워퍼 테스트 ===")
    
    try:
        warper = MeshWarper()
        landmarks = create_test_landmarks()
        
        # 코 제어점 생성 테스트
        from models.surgery import FeatureType
        nose_points = warper.create_control_points(landmarks, FeatureType.NOSE)
        print(f"  ✓ 코 제어점 생성: {len(nose_points)}개")
        
        # 얼굴 메시 생성 테스트
        mesh = warper.create_face_mesh(landmarks, (480, 640))
        print(f"  ✓ 얼굴 메시 생성: {mesh.shape}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 메시 워퍼 테스트 실패: {e}")
        return False


def test_surgery_engine():
    """성형 엔진 기본 테스트"""
    print("\n=== 성형 엔진 기본 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 1. 코 성형 테스트
        nose_config = NoseConfig(height_adjustment=0.2, width_adjustment=-0.1)
        nose_result = engine.modify_nose(image, landmarks, nose_config)
        print(f"  ✓ 코 성형 테스트 성공: {nose_result.shape}")
        
        # 2. 눈 성형 테스트
        eye_config = EyeConfig(size_adjustment=0.3, shape_adjustment=0.1)
        eye_result = engine.modify_eyes(image, landmarks, eye_config)
        print(f"  ✓ 눈 성형 테스트 성공: {eye_result.shape}")
        
        # 3. 턱선 성형 테스트
        jaw_config = JawlineConfig(width_adjustment=-0.2, angle_adjustment=0.1)
        jaw_result = engine.modify_jawline(image, landmarks, jaw_config)
        print(f"  ✓ 턱선 성형 테스트 성공: {jaw_result.shape}")
        
        # 4. 광대 성형 테스트
        cheek_config = CheekboneConfig(height_adjustment=-0.1, width_adjustment=-0.1)
        cheek_result = engine.modify_cheekbones(image, landmarks, cheek_config)
        print(f"  ✓ 광대 성형 테스트 성공: {cheek_result.shape}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 성형 엔진 테스트 실패: {e}")
        return False


def test_full_surgery():
    """전체 성형 시뮬레이션 테스트"""
    print("\n=== 전체 성형 시뮬레이션 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        image = create_test_image()
        landmarks = create_test_landmarks()
        
        # 전체 성형 설정
        surgery_config = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.2, width_adjustment=-0.1),
            eyes=EyeConfig(size_adjustment=0.3, angle_adjustment=0.2),
            jawline=JawlineConfig(width_adjustment=-0.2, angle_adjustment=0.1),
            cheekbones=CheekboneConfig(height_adjustment=-0.1, width_adjustment=-0.1)
        )
        
        start_time = time.time()
        result = engine.apply_full_surgery(image, landmarks, surgery_config)
        processing_time = time.time() - start_time
        
        if result and result.is_successful():
            print(f"  ✓ 전체 성형 시뮬레이션 성공")
            print(f"  ✓ 처리 시간: {processing_time:.3f}초")
            print(f"  ✓ 적용된 효과: {', '.join(result.applied_modifications)}")
            print(f"  ✓ 자연스러움 점수: {result.natural_score:.2f}")
            
            # 결과 이미지 저장
            cv2.imwrite("surgery_verification_result.jpg", result.image)
            
            return True
        else:
            print("  ❌ 전체 성형 시뮬레이션 실패")
            return False
            
    except Exception as e:
        print(f"  ❌ 전체 성형 테스트 실패: {e}")
        return False


def test_proportion_validation():
    """비율 검증 테스트"""
    print("\n=== 비율 검증 테스트 ===")
    
    try:
        engine = RealtimeSurgeryEngine()
        landmarks = create_test_landmarks()
        
        # 정상 비율 테스트
        is_valid = engine.validate_proportions(landmarks)
        print(f"  ✓ 정상 비율 검증: {is_valid}")
        
        # 비정상 비율 테스트 (극단적 변형)
        extreme_landmarks = landmarks.copy()
        for i in range(min(10, len(extreme_landmarks))):
            extreme_landmarks[i] = Point3D(
                extreme_landmarks[i].x + 1000,  # 극단적 변형
                extreme_landmarks[i].y,
                extreme_landmarks[i].z
            )
        
        is_extreme_valid = engine.validate_proportions(extreme_landmarks)
        print(f"  ✓ 극단적 변형 검증: {is_extreme_valid} (False여야 정상)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 비율 검증 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("성형 시뮬레이션 엔진 검증 테스트 시작\n")
    
    test_results = []
    
    # 각 테스트 실행
    test_results.append(test_thin_plate_spline())
    test_results.append(test_mesh_warper())
    test_results.append(test_surgery_engine())
    test_results.append(test_full_surgery())
    test_results.append(test_proportion_validation())
    
    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약:")
    print(f"  성공: {sum(test_results)}/{len(test_results)}")
    print(f"  실패: {len(test_results) - sum(test_results)}/{len(test_results)}")
    
    if all(test_results):
        print("  🎉 모든 테스트 통과!")
        return True
    else:
        print("  ⚠️  일부 테스트 실패")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)