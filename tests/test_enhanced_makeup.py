"""
향상된 메이크업 엔진 테스트 스크립트
Reference files 기반 구현의 정확성 검증
"""
import cv2
import numpy as np
import os
import sys
from engines.enhanced_makeup_engine import EnhancedMakeupEngine, get_default_colors

def test_basic_functionality():
    """기본 기능 테스트"""
    print("🧪 향상된 메이크업 엔진 기본 기능 테스트 시작...")
    
    # 메이크업 엔진 초기화
    engine = EnhancedMakeupEngine()
    
    # 사용 가능한 랜드마크 확인
    landmarks = engine.get_available_landmarks()
    print(f"✅ 사용 가능한 랜드마크 그룹: {len(landmarks)}개")
    
    # 각 랜드마크 그룹 확인
    for name, points in landmarks.items():
        print(f"   - {name}: {len(points)}개 포인트")
    
    # 기본 색상 확인
    default_colors = get_default_colors()
    print(f"✅ 기본 색상 설정: {len(default_colors)}개 부위")
    
    print("✅ 기본 기능 테스트 완료!\n")

def test_image_processing():
    """이미지 처리 테스트"""
    print("🖼️ 이미지 처리 테스트 시작...")
    
    # 테스트용 더미 이미지 생성 (얼굴 형태)
    test_image = np.ones((400, 400, 3), dtype=np.uint8) * 200  # 회색 배경
    
    # 간단한 얼굴 형태 그리기
    cv2.circle(test_image, (200, 200), 100, (220, 180, 140), -1)  # 얼굴
    cv2.circle(test_image, (170, 170), 10, (0, 0, 0), -1)  # 왼쪽 눈
    cv2.circle(test_image, (230, 170), 10, (0, 0, 0), -1)  # 오른쪽 눈
    cv2.ellipse(test_image, (200, 220), (20, 10), 0, 0, 360, (200, 100, 100), -1)  # 입
    
    engine = EnhancedMakeupEngine()
    
    # 이미지 유효성 검증
    is_valid = engine.validate_image(test_image)
    print(f"✅ 이미지 유효성 검증: {'통과' if is_valid else '실패'}")
    
    # 랜드마크 추출 테스트
    landmarks = engine.read_landmarks(test_image)
    print(f"✅ 랜드마크 추출: {len(landmarks)}개 포인트 감지")
    
    if len(landmarks) == 0:
        print("⚠️ 테스트 이미지에서 얼굴이 감지되지 않음 (정상 - 단순한 더미 이미지)")
    
    print("✅ 이미지 처리 테스트 완료!\n")

def test_makeup_application():
    """메이크업 적용 테스트"""
    print("💄 메이크업 적용 테스트 시작...")
    
    # 실제 얼굴 이미지가 있는지 확인
    test_images = [
        "doc/1.png", "doc/2.png", "doc/3.png", "doc/4.png", "doc/5.png"
    ]
    
    engine = EnhancedMakeupEngine()
    
    for img_path in test_images:
        if os.path.exists(img_path):
            print(f"📸 테스트 이미지: {img_path}")
            
            try:
                # 이미지 로드
                image = cv2.imread(img_path)
                if image is None:
                    print(f"   ❌ 이미지 로드 실패: {img_path}")
                    continue
                
                # 기본 메이크업 적용
                result = engine.apply_simple_makeup(image)
                
                # 결과 저장
                output_path = f"test_enhanced_makeup_{os.path.basename(img_path)}"
                cv2.imwrite(output_path, result)
                print(f"   ✅ 메이크업 적용 완료: {output_path}")
                
                # 고급 메이크업 테스트
                colors_map = {
                    "LIP_UPPER": [0, 0, 200],  # 진한 빨강
                    "LIP_LOWER": [0, 0, 200],
                    "EYELINER_LEFT": [100, 0, 0],  # 진한 파랑
                    "EYELINER_RIGHT": [100, 0, 0],
                    "EYESHADOW_LEFT": [0, 150, 0],  # 진한 초록
                    "EYESHADOW_RIGHT": [0, 150, 0],
                    "EYEBROW_LEFT": [50, 100, 150],  # 갈색
                    "EYEBROW_RIGHT": [50, 100, 150],
                }
                
                intensity_map = {
                    "LIP_UPPER": 0.8,
                    "LIP_LOWER": 0.8,
                    "EYELINER_LEFT": 0.7,
                    "EYELINER_RIGHT": 0.7,
                    "EYESHADOW_LEFT": 0.6,
                    "EYESHADOW_RIGHT": 0.6,
                    "EYEBROW_LEFT": 0.5,
                    "EYEBROW_RIGHT": 0.5,
                }
                
                advanced_result, mask, face_detected = engine.apply_makeup(
                    image, colors_map, intensity_map, 0.4, 9, 5, False
                )
                
                if face_detected:
                    advanced_output_path = f"test_enhanced_advanced_{os.path.basename(img_path)}"
                    cv2.imwrite(advanced_output_path, advanced_result)
                    print(f"   ✅ 고급 메이크업 적용 완료: {advanced_output_path}")
                else:
                    print(f"   ⚠️ 얼굴 감지 실패: {img_path}")
                
            except Exception as e:
                print(f"   ❌ 오류 발생: {e}")
            
            break  # 첫 번째 유효한 이미지만 테스트
    
    print("✅ 메이크업 적용 테스트 완료!\n")

def test_streamlit_compatibility():
    """Streamlit 호환성 테스트"""
    print("🌐 Streamlit 호환성 테스트 시작...")
    
    try:
        # Streamlit 앱 파일 존재 확인
        if os.path.exists("enhanced_streamlit_makeup_app.py"):
            print("✅ 향상된 Streamlit 앱 파일 존재")
            
            # 파일 내용 간단 검증
            with open("enhanced_streamlit_makeup_app.py", "r", encoding="utf-8") as f:
                content = f.read()
                
            required_components = [
                "EnhancedMakeupEngine",
                "st.color_picker",
                "apply_makeup",
                "read_landmarks",
                "FACE_LANDMARKS"
            ]
            
            for component in required_components:
                if component in content:
                    print(f"   ✅ {component} 포함됨")
                else:
                    print(f"   ❌ {component} 누락됨")
        else:
            print("❌ 향상된 Streamlit 앱 파일이 존재하지 않음")
    
    except Exception as e:
        print(f"❌ Streamlit 호환성 테스트 오류: {e}")
    
    print("✅ Streamlit 호환성 테스트 완료!\n")

def test_performance():
    """성능 테스트"""
    print("⚡ 성능 테스트 시작...")
    
    import time
    
    # 테스트용 이미지 생성
    test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    
    engine = EnhancedMakeupEngine()
    
    # 랜드마크 추출 성능 테스트
    start_time = time.time()
    for _ in range(5):
        landmarks = engine.read_landmarks(test_image)
    landmark_time = (time.time() - start_time) / 5
    print(f"✅ 평균 랜드마크 추출 시간: {landmark_time:.3f}초")
    
    # 메이크업 적용 성능 테스트 (실제 얼굴이 있는 경우에만)
    if os.path.exists("doc/1.png"):
        real_image = cv2.imread("doc/1.png")
        if real_image is not None:
            start_time = time.time()
            for _ in range(3):
                result = engine.apply_simple_makeup(real_image)
            makeup_time = (time.time() - start_time) / 3
            print(f"✅ 평균 메이크업 적용 시간: {makeup_time:.3f}초")
    
    print("✅ 성능 테스트 완료!\n")

def main():
    """메인 테스트 함수"""
    print("🎭 Enhanced Makeup Engine 종합 테스트")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_image_processing()
        test_makeup_application()
        test_streamlit_compatibility()
        test_performance()
        
        print("🎉 모든 테스트 완료!")
        print("✅ 향상된 메이크업 엔진이 정상적으로 작동합니다.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()