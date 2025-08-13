"""
간단한 메이크업 테스트 - Streamlit 없이 실행
"""
import cv2
import numpy as np
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.enhanced_makeup_utils import *


def test_makeup_with_custom_colors():
    """커스텀 색상으로 메이크업 테스트"""
    print("🎨 커스텀 메이크업 테스트 시작")
    print("-" * 40)
    
    # 샘플 이미지 사용
    image_path = "demo_sample_face.jpg"
    
    if not os.path.exists(image_path):
        print("❌ 샘플 이미지가 없습니다. 먼저 데모를 실행하세요:")
        print("python demo_enhanced_makeup.py --create-sample")
        return
    
    # 이미지 로드
    image = cv2.imread(image_path)
    print(f"✅ 이미지 로드: {image_path}")
    
    # 1. 기본 메이크업 (Reference files 방식)
    print("\n1️⃣ 기본 메이크업 적용...")
    basic_result = apply_simple_makeup_from_reference(image)
    cv2.imwrite("test_basic_makeup.jpg", basic_result)
    print("✅ 저장: test_basic_makeup.jpg")
    
    # 2. 빨간 립스틱 + 검은 아이라이너
    print("\n2️⃣ 빨간 립스틱 + 검은 아이라이너...")
    colors_red_lips = {
        "LIP_UPPER": [0, 0, 200],      # 진한 빨강
        "LIP_LOWER": [0, 0, 200],      # 진한 빨강
        "EYELINER_LEFT": [0, 0, 0],    # 검정
        "EYELINER_RIGHT": [0, 0, 0],   # 검정
        "EYESHADOW_LEFT": [100, 50, 50],   # 연한 갈색
        "EYESHADOW_RIGHT": [100, 50, 50],  # 연한 갈색
        "EYEBROW_LEFT": [50, 50, 100],     # 갈색
        "EYEBROW_RIGHT": [50, 50, 100],    # 갈색
    }
    
    intensity_map = create_intensity_map(0.8, 1.0, 0.5, 0.7)
    result_red, mask_red, detected = apply_makeup(
        image, colors_red_lips, intensity_map, 0.4, 7, 4, False
    )
    
    if detected:
        cv2.imwrite("test_red_lips_makeup.jpg", result_red)
        print("✅ 저장: test_red_lips_makeup.jpg")
    else:
        print("❌ 얼굴 감지 실패")
    
    # 3. 핑크 립스틱 + 브라운 아이섀도
    print("\n3️⃣ 핑크 립스틱 + 브라운 아이섀도...")
    colors_pink = {
        "LIP_UPPER": [150, 100, 200],      # 핑크
        "LIP_LOWER": [150, 100, 200],      # 핑크
        "EYELINER_LEFT": [100, 50, 50],    # 다크 브라운
        "EYELINER_RIGHT": [100, 50, 50],   # 다크 브라운
        "EYESHADOW_LEFT": [100, 100, 150], # 브라운 아이섀도
        "EYESHADOW_RIGHT": [100, 100, 150], # 브라운 아이섀도
        "EYEBROW_LEFT": [50, 80, 120],     # 브라운 눈썹
        "EYEBROW_RIGHT": [50, 80, 120],    # 브라운 눈썹
    }
    
    result_pink, mask_pink, detected = apply_makeup(
        image, colors_pink, intensity_map, 0.35, 9, 5, False
    )
    
    if detected:
        cv2.imwrite("test_pink_makeup.jpg", result_pink)
        print("✅ 저장: test_pink_makeup.jpg")
    else:
        print("❌ 얼굴 감지 실패")
    
    # 4. 비교 이미지 생성
    print("\n4️⃣ 비교 이미지 생성...")
    if 'basic_result' in locals() and 'result_red' in locals() and 'result_pink' in locals():
        h, w = image.shape[:2]
        comparison = np.zeros((h, w * 4, 3), dtype=np.uint8)
        
        comparison[:, :w] = image
        comparison[:, w:w*2] = basic_result
        comparison[:, w*2:w*3] = result_red
        comparison[:, w*3:w*4] = result_pink
        
        # 텍스트 추가
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(comparison, "Original", (10, 30), font, 0.7, (255, 255, 255), 2)
        cv2.putText(comparison, "Basic", (w + 10, 30), font, 0.7, (255, 255, 255), 2)
        cv2.putText(comparison, "Red Lips", (w*2 + 10, 30), font, 0.7, (255, 255, 255), 2)
        cv2.putText(comparison, "Pink Style", (w*3 + 10, 30), font, 0.7, (255, 255, 255), 2)
        
        cv2.imwrite("test_makeup_comparison.jpg", comparison)
        print("✅ 저장: test_makeup_comparison.jpg")
    
    print("\n🎉 테스트 완료!")
    print("\n📁 생성된 파일들:")
    print("- test_basic_makeup.jpg")
    print("- test_red_lips_makeup.jpg") 
    print("- test_pink_makeup.jpg")
    print("- test_makeup_comparison.jpg")


def interactive_color_test():
    """대화형 색상 테스트"""
    print("\n🎨 대화형 색상 테스트")
    print("-" * 40)
    
    image_path = "demo_sample_face.jpg"
    if not os.path.exists(image_path):
        print("❌ 샘플 이미지가 없습니다.")
        return
    
    image = cv2.imread(image_path)
    
    # 사용자 정의 색상들
    color_presets = {
        "자연스러운": {
            "LIP_UPPER": [120, 80, 180],      # 자연스러운 핑크
            "LIP_LOWER": [120, 80, 180],
            "EYELINER_LEFT": [80, 60, 40],    # 브라운
            "EYELINER_RIGHT": [80, 60, 40],
            "EYESHADOW_LEFT": [140, 120, 100], # 베이지
            "EYESHADOW_RIGHT": [140, 120, 100],
            "EYEBROW_LEFT": [60, 80, 100],    # 자연스러운 브라운
            "EYEBROW_RIGHT": [60, 80, 100],
        },
        "드라마틱": {
            "LIP_UPPER": [0, 0, 220],         # 진한 빨강
            "LIP_LOWER": [0, 0, 220],
            "EYELINER_LEFT": [0, 0, 0],       # 검정
            "EYELINER_RIGHT": [0, 0, 0],
            "EYESHADOW_LEFT": [50, 0, 100],   # 퍼플
            "EYESHADOW_RIGHT": [50, 0, 100],
            "EYEBROW_LEFT": [30, 30, 30],     # 다크 그레이
            "EYEBROW_RIGHT": [30, 30, 30],
        },
        "로맨틱": {
            "LIP_UPPER": [180, 120, 200],     # 로즈 핑크
            "LIP_LOWER": [180, 120, 200],
            "EYELINER_LEFT": [120, 80, 60],   # 소프트 브라운
            "EYELINER_RIGHT": [120, 80, 60],
            "EYESHADOW_LEFT": [150, 130, 120], # 피치
            "EYESHADOW_RIGHT": [150, 130, 120],
            "EYEBROW_LEFT": [80, 100, 120],   # 소프트 브라운
            "EYEBROW_RIGHT": [80, 100, 120],
        }
    }
    
    for style_name, colors in color_presets.items():
        print(f"\n💄 {style_name} 스타일 적용...")
        
        intensity_map = create_intensity_map(0.7, 0.8, 0.6, 0.7)
        result, mask, detected = apply_makeup(
            image, colors, intensity_map, 0.35, 7, 4, False
        )
        
        if detected:
            filename = f"test_{style_name}_style.jpg"
            cv2.imwrite(filename, result)
            print(f"✅ 저장: {filename}")
        else:
            print("❌ 얼굴 감지 실패")


if __name__ == "__main__":
    print("🎭 간단한 메이크업 테스트")
    print("=" * 50)
    
    # 기본 테스트
    test_makeup_with_custom_colors()
    
    # 대화형 테스트
    interactive_color_test()
    
    print("\n" + "=" * 50)
    print("🎉 모든 테스트 완료!")
    print("\n💡 Streamlit 대신 이 방식으로 메이크업을 테스트할 수 있습니다.")
    print("필요한 경우 색상 값을 수정해서 다양한 메이크업을 시도해보세요!")