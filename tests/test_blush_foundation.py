#!/usr/bin/env python3
"""
블러셔 및 파운데이션 기능 테스트
"""

import numpy as np
import cv2
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.core import Point3D, Color
from models.makeup import BlushConfig, FoundationConfig, BlendMode
from engines.makeup_engine import RealtimeMakeupEngine


def create_test_image(width=400, height=400):
    """테스트용 얼굴 이미지 생성"""
    # 기본 피부색 배경
    image = np.full((height, width, 3), [180, 150, 120], dtype=np.uint8)  # BGR 형식
    
    # 얼굴 타원 그리기
    center = (width // 2, height // 2)
    axes = (width // 3, int(height * 0.4))
    cv2.ellipse(image, center, axes, 0, 0, 360, [200, 170, 140], -1)
    
    # 눈 영역 (어두운 색)
    left_eye = (int(width * 0.35), int(height * 0.4))
    right_eye = (int(width * 0.65), int(height * 0.4))
    cv2.ellipse(image, left_eye, (25, 15), 0, 0, 360, [160, 130, 100], -1)
    cv2.ellipse(image, right_eye, (25, 15), 0, 0, 360, [160, 130, 100], -1)
    
    # 입 영역 (분홍색)
    mouth = (width // 2, int(height * 0.75))
    cv2.ellipse(image, mouth, (30, 10), 0, 0, 360, [120, 100, 180], -1)
    
    return image


def create_test_landmarks(width=400, height=400):
    """테스트용 얼굴 랜드마크 생성"""
    landmarks = []
    
    # 얼굴 윤곽 (36개 포인트)
    for i in range(36):
        angle = i * 10 * np.pi / 180
        x = width // 2 + int((width // 3) * np.cos(angle))
        y = height // 2 + int((height * 0.4) * np.sin(angle))
        landmarks.append(Point3D(x, y, 0))
    
    # 볼 영역 랜드마크 추가 (MediaPipe 인덱스에 맞춰)
    # 왼쪽 볼 영역 (116-142 인덱스 범위)
    for i in range(116, 143):
        if i < 200:  # 충분한 랜드마크 생성
            x = int(width * 0.25) + np.random.randint(-20, 20)
            y = int(height * 0.55) + np.random.randint(-15, 15)
            landmarks.append(Point3D(x, y, 0))
    
    # 오른쪽 볼 영역 (345-411 인덱스 범위)
    for i in range(345, 412):
        if i < 500:  # 충분한 랜드마크 생성
            x = int(width * 0.75) + np.random.randint(-20, 20)
            y = int(height * 0.55) + np.random.randint(-15, 15)
            landmarks.append(Point3D(x, y, 0))
    
    # 나머지 랜드마크를 충분히 생성 (총 468개까지)
    while len(landmarks) < 468:
        x = np.random.randint(50, width - 50)
        y = np.random.randint(50, height - 50)
        landmarks.append(Point3D(x, y, 0))
    
    return landmarks


def test_blush_application():
    """블러셔 적용 테스트"""
    print("=== 블러셔 적용 테스트 ===")
    
    # 테스트 데이터 준비
    image = create_test_image()
    landmarks = create_test_landmarks()
    engine = RealtimeMakeupEngine()
    
    # 블러셔 설정
    blush_configs = [
        # 자연스러운 핑크 블러셔
        BlushConfig(
            color=Color(255, 150, 150, 255),  # 연한 핑크
            intensity=0.3,
            placement="cheeks",
            blend_mode=BlendMode.NORMAL
        ),
        # 강한 코랄 블러셔
        BlushConfig(
            color=Color(255, 120, 80, 255),   # 코랄
            intensity=0.6,
            placement="cheeks",
            blend_mode=BlendMode.MULTIPLY
        ),
        # 하이라이터 효과
        BlushConfig(
            color=Color(255, 220, 200, 255),  # 골드 하이라이터
            intensity=0.4,
            placement="nose",
            blend_mode=BlendMode.OVERLAY
        )
    ]
    
    for i, config in enumerate(blush_configs):
        print(f"\n테스트 {i+1}: {config.placement} 블러셔 (강도: {config.intensity})")
        
        try:
            # 블러셔 적용
            result = engine.apply_blush(image.copy(), landmarks, config)
            
            # 결과 검증
            if result is not None and result.shape == image.shape:
                print("✓ 블러셔 적용 성공")
                
                # 변화 감지
                diff = cv2.absdiff(image, result)
                change_pixels = np.sum(diff > 10)
                print(f"  변경된 픽셀 수: {change_pixels}")
                
                if change_pixels > 100:  # 충분한 변화가 있는지 확인
                    print("✓ 시각적 변화 확인됨")
                else:
                    print("⚠ 시각적 변화가 미미함")
                
                # 결과 이미지 저장
                cv2.imwrite(f'test_blush_result_{i+1}.jpg', result)
                print(f"  결과 이미지 저장: test_blush_result_{i+1}.jpg")
                
            else:
                print("✗ 블러셔 적용 실패")
                
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
    
    print("\n블러셔 테스트 완료")


def test_foundation_application():
    """파운데이션 적용 테스트"""
    print("\n=== 파운데이션 적용 테스트 ===")
    
    # 테스트 데이터 준비
    image = create_test_image()
    landmarks = create_test_landmarks()
    engine = RealtimeMakeupEngine()
    
    # 파운데이션 설정
    foundation_configs = [
        # 자연스러운 파운데이션
        FoundationConfig(
            color=Color(220, 180, 140, 255),  # 자연스러운 피부색
            coverage=0.3,
            finish="natural"
        ),
        # 풀 커버리지 매트 파운데이션
        FoundationConfig(
            color=Color(200, 160, 120, 255),  # 약간 어두운 톤
            coverage=0.7,
            finish="matte"
        ),
        # 듀이 파운데이션
        FoundationConfig(
            color=Color(240, 200, 160, 255),  # 밝은 톤
            coverage=0.5,
            finish="dewy"
        )
    ]
    
    for i, config in enumerate(foundation_configs):
        print(f"\n테스트 {i+1}: {config.finish} 파운데이션 (커버리지: {config.coverage})")
        
        try:
            # 파운데이션 적용
            result = engine.apply_foundation(image.copy(), landmarks, config)
            
            # 결과 검증
            if result is not None and result.shape == image.shape:
                print("✓ 파운데이션 적용 성공")
                
                # 변화 감지
                diff = cv2.absdiff(image, result)
                change_pixels = np.sum(diff > 5)  # 파운데이션은 미묘한 변화
                print(f"  변경된 픽셀 수: {change_pixels}")
                
                if change_pixels > 500:  # 파운데이션은 넓은 영역에 적용
                    print("✓ 시각적 변화 확인됨")
                else:
                    print("⚠ 시각적 변화가 미미함")
                
                # 스무딩 효과 확인 (블러 정도 측정)
                original_variance = np.var(cv2.Laplacian(image, cv2.CV_64F))
                result_variance = np.var(cv2.Laplacian(result, cv2.CV_64F))
                
                if result_variance < original_variance:
                    print("✓ 스무딩 효과 확인됨")
                else:
                    print("⚠ 스무딩 효과 미미함")
                
                # 결과 이미지 저장
                cv2.imwrite(f'test_foundation_result_{i+1}.jpg', result)
                print(f"  결과 이미지 저장: test_foundation_result_{i+1}.jpg")
                
            else:
                print("✗ 파운데이션 적용 실패")
                
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
    
    print("\n파운데이션 테스트 완료")


def test_combined_application():
    """블러셔와 파운데이션 조합 테스트"""
    print("\n=== 블러셔 + 파운데이션 조합 테스트 ===")
    
    # 테스트 데이터 준비
    image = create_test_image()
    landmarks = create_test_landmarks()
    engine = RealtimeMakeupEngine()
    
    # 파운데이션 먼저 적용
    foundation_config = FoundationConfig(
        color=Color(210, 170, 130, 255),
        coverage=0.4,
        finish="natural"
    )
    
    # 블러셔 설정
    blush_config = BlushConfig(
        color=Color(255, 140, 140, 255),
        intensity=0.4,
        placement="cheeks",
        blend_mode=BlendMode.NORMAL
    )
    
    try:
        print("1단계: 파운데이션 적용")
        result = engine.apply_foundation(image.copy(), landmarks, foundation_config)
        
        print("2단계: 블러셔 적용")
        final_result = engine.apply_blush(result, landmarks, blush_config)
        
        # 결과 검증
        if final_result is not None and final_result.shape == image.shape:
            print("✓ 조합 메이크업 적용 성공")
            
            # 단계별 변화 확인
            foundation_diff = cv2.absdiff(image, result)
            final_diff = cv2.absdiff(image, final_result)
            
            foundation_changes = np.sum(foundation_diff > 5)
            total_changes = np.sum(final_diff > 5)
            
            print(f"  파운데이션 변화: {foundation_changes} 픽셀")
            print(f"  전체 변화: {total_changes} 픽셀")
            
            if total_changes > foundation_changes:
                print("✓ 블러셔 추가 효과 확인됨")
            
            # 결과 이미지 저장
            cv2.imwrite('test_combined_result.jpg', final_result)
            print("  결과 이미지 저장: test_combined_result.jpg")
            
        else:
            print("✗ 조합 메이크업 적용 실패")
            
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
    
    print("\n조합 테스트 완료")


def test_skin_tone_extraction():
    """피부톤 추출 테스트"""
    print("\n=== 피부톤 추출 테스트 ===")
    
    # 테스트 데이터 준비
    image = create_test_image()
    landmarks = create_test_landmarks()
    engine = RealtimeMakeupEngine()
    
    try:
        # 피부톤 추출
        skin_tone = engine.get_skin_tone(image, landmarks)
        
        print(f"추출된 피부톤: RGB({skin_tone.r}, {skin_tone.g}, {skin_tone.b})")
        
        # 피부톤이 합리적인 범위인지 확인
        if (100 <= skin_tone.r <= 255 and 
            80 <= skin_tone.g <= 220 and 
            60 <= skin_tone.b <= 180):
            print("✓ 피부톤이 합리적인 범위 내에 있음")
        else:
            print("⚠ 피부톤이 예상 범위를 벗어남")
        
        # 색상 조화 테스트
        test_color = Color(255, 100, 100, 255)  # 빨간색
        harmonized = engine.color_blender.match_skin_tone(test_color, skin_tone, 0.3)
        
        print(f"원본 색상: RGB({test_color.r}, {test_color.g}, {test_color.b})")
        print(f"조화된 색상: RGB({harmonized.r}, {harmonized.g}, {harmonized.b})")
        
        if harmonized != test_color:
            print("✓ 색상 조화 기능 작동함")
        else:
            print("⚠ 색상 조화 기능이 작동하지 않음")
            
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
    
    print("\n피부톤 추출 테스트 완료")


def main():
    """메인 테스트 함수"""
    print("블러셔 및 파운데이션 기능 테스트 시작")
    print("=" * 50)
    
    # 개별 기능 테스트
    test_blush_application()
    test_foundation_application()
    test_combined_application()
    test_skin_tone_extraction()
    
    print("\n" + "=" * 50)
    print("모든 테스트 완료!")
    print("\n생성된 테스트 이미지:")
    print("- test_blush_result_1.jpg ~ test_blush_result_3.jpg")
    print("- test_foundation_result_1.jpg ~ test_foundation_result_3.jpg")
    print("- test_combined_result.jpg")


if __name__ == "__main__":
    main()