"""
Reference Files 통합 테스트
image.py, utils.py, web_makeup_gui.py의 기능이 완전히 통합되었는지 검증
"""
import cv2
import numpy as np
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.enhanced_makeup_utils import *
from engines.enhanced_makeup_engine import EnhancedMakeupEngine


def test_reference_compatibility():
    """Reference files와의 호환성 테스트"""
    print("🧪 Reference Files 호환성 테스트 시작...")
    
    # 테스트 이미지 생성 (간단한 얼굴 형태)
    test_image = np.ones((400, 400, 3), dtype=np.uint8) * 255
    
    # 간단한 얼굴 모양 그리기 (테스트용)
    cv2.circle(test_image, (200, 200), 100, (200, 180, 160), -1)  # 얼굴
    cv2.circle(test_image, (170, 180), 10, (0, 0, 0), -1)  # 왼쪽 눈
    cv2.circle(test_image, (230, 180), 10, (0, 0, 0), -1)  # 오른쪽 눈
    cv2.ellipse(test_image, (200, 220), (20, 10), 0, 0, 180, (200, 100, 100), -1)  # 입
    
    print("✅ 테스트 이미지 생성 완료")
    
    # 1. Reference files 함수들 테스트
    print("\n📋 Reference Files 함수 테스트:")
    
    # read_landmarks 테스트
    landmarks = read_landmarks(test_image)
    print(f"   - read_landmarks: {len(landmarks)}개 랜드마크 감지")
    
    # face_points 접근 테스트
    face_points_data = get_face_points()
    print(f"   - face_points: {len(face_points_data)}개 얼굴 부위 정의")
    
    # 기본 색상 맵 테스트
    default_colors = get_default_colors_map()
    print(f"   - default_colors: {len(default_colors)}개 색상 정의")
    
    # 2. 기본 메이크업 적용 테스트 (reference files 방식)
    print("\n🎨 기본 메이크업 적용 테스트:")
    try:
        result_basic = apply_simple_makeup_from_reference(test_image)
        print("   ✅ 기본 메이크업 적용 성공")
    except Exception as e:
        print(f"   ❌ 기본 메이크업 적용 실패: {e}")
    
    # 3. 고급 메이크업 적용 테스트
    print("\n🎭 고급 메이크업 적용 테스트:")
    try:
        colors_map = {
            "LIP_UPPER": [0, 0, 255],
            "LIP_LOWER": [0, 0, 255],
            "EYELINER_LEFT": [139, 0, 0],
            "EYELINER_RIGHT": [139, 0, 0],
            "EYESHADOW_LEFT": [0, 100, 0],
            "EYESHADOW_RIGHT": [0, 100, 0],
            "EYEBROW_LEFT": [19, 69, 139],
            "EYEBROW_RIGHT": [19, 69, 139],
        }
        
        intensity_map = create_intensity_map(1.0, 1.0, 1.0, 1.0)
        
        result_advanced, mask, face_detected = apply_makeup(
            test_image, colors_map, intensity_map, 0.3, 7, 4, False
        )
        print("   ✅ 고급 메이크업 적용 성공")
        print(f"   - 얼굴 감지: {'성공' if face_detected else '실패'}")
    except Exception as e:
        print(f"   ❌ 고급 메이크업 적용 실패: {e}")
    
    # 4. EnhancedMakeupEngine 테스트
    print("\n🔧 EnhancedMakeupEngine 테스트:")
    try:
        engine = EnhancedMakeupEngine()
        
        # 랜드마크 읽기 테스트
        engine_landmarks = engine.read_landmarks(test_image)
        print(f"   - 엔진 랜드마크: {len(engine_landmarks)}개 감지")
        
        # 간단한 메이크업 적용 테스트
        engine_result = engine.apply_simple_makeup(test_image)
        print("   ✅ 엔진 메이크업 적용 성공")
        
        # 고급 메이크업 적용 테스트
        engine_advanced, engine_mask, engine_detected = engine.apply_makeup(
            test_image, colors_map, intensity_map, 0.3, 7, 4, False
        )
        print("   ✅ 엔진 고급 메이크업 적용 성공")
        
    except Exception as e:
        print(f"   ❌ EnhancedMakeupEngine 테스트 실패: {e}")
    
    # 5. 유틸리티 함수 테스트
    print("\n🛠️ 유틸리티 함수 테스트:")
    
    # 색상 변환 테스트
    rgb_color = "#FF0000"
    bgr_color = convert_rgb_to_bgr_color(rgb_color)
    print(f"   - 색상 변환: {rgb_color} -> {bgr_color}")
    
    # 이미지 유효성 검증 테스트
    is_valid = validate_image_input(test_image)
    print(f"   - 이미지 유효성: {'유효' if is_valid else '무효'}")
    
    # 얼굴 요소 리스트 테스트
    face_elements = get_face_elements()
    print(f"   - 얼굴 요소: {len(face_elements)}개 ({', '.join(face_elements)})")
    
    print("\n🎉 모든 테스트 완료!")
    return True


def test_real_image_if_available():
    """실제 이미지가 있다면 테스트"""
    print("\n📸 실제 이미지 테스트:")
    
    # 테스트 이미지 경로들
    test_paths = [
        "test_image.jpg",
        "sample.jpg", 
        "face.jpg",
        "test.png"
    ]
    
    for path in test_paths:
        if os.path.exists(path):
            print(f"   🖼️ {path} 발견 - 테스트 진행")
            try:
                # Reference 방식으로 메이크업 적용
                result = apply_simple_makeup_from_reference(path)
                
                # 결과 저장
                output_path = f"test_result_{os.path.basename(path)}"
                cv2.imwrite(output_path, result)
                print(f"   ✅ 결과 저장: {output_path}")
                
                return True
            except Exception as e:
                print(f"   ❌ 테스트 실패: {e}")
    
    print("   ℹ️ 테스트용 실제 이미지를 찾을 수 없습니다.")
    return False


def create_sample_test_image():
    """샘플 테스트 이미지 생성"""
    print("\n🎨 샘플 테스트 이미지 생성:")
    
    # 더 정교한 테스트 이미지 생성
    img = np.ones((500, 500, 3), dtype=np.uint8) * 240
    
    # 얼굴 윤곽
    cv2.ellipse(img, (250, 250), (120, 150), 0, 0, 360, (220, 200, 180), -1)
    
    # 눈
    cv2.ellipse(img, (210, 220), (25, 15), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(img, (290, 220), (25, 15), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img, (210, 220), 8, (0, 0, 0), -1)
    cv2.circle(img, (290, 220), 8, (0, 0, 0), -1)
    
    # 눈썹
    cv2.ellipse(img, (210, 200), (20, 8), 0, 0, 180, (100, 80, 60), -1)
    cv2.ellipse(img, (290, 200), (20, 8), 0, 0, 180, (100, 80, 60), -1)
    
    # 코
    cv2.ellipse(img, (250, 250), (8, 15), 0, 0, 360, (200, 180, 160), -1)
    
    # 입
    cv2.ellipse(img, (250, 300), (30, 15), 0, 0, 180, (180, 120, 120), -1)
    
    # 저장
    cv2.imwrite("sample_test_face.jpg", img)
    print("   ✅ 샘플 이미지 저장: sample_test_face.jpg")
    
    # 생성된 이미지로 테스트
    try:
        result = apply_simple_makeup_from_reference("sample_test_face.jpg")
        cv2.imwrite("sample_test_result.jpg", result)
        print("   ✅ 샘플 이미지 메이크업 테스트 성공: sample_test_result.jpg")
        return True
    except Exception as e:
        print(f"   ❌ 샘플 이미지 테스트 실패: {e}")
        return False


def performance_test():
    """성능 테스트"""
    print("\n⚡ 성능 테스트:")
    
    import time
    
    # 테스트 이미지 생성
    test_img = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
    
    # 기본 메이크업 성능 테스트
    start_time = time.time()
    try:
        result = apply_simple_makeup_from_reference(test_img)
        end_time = time.time()
        print(f"   - 기본 메이크업 처리 시간: {end_time - start_time:.3f}초")
    except:
        print("   - 기본 메이크업 성능 테스트 실패 (얼굴 미감지)")
    
    # 엔진 성능 테스트
    engine = EnhancedMakeupEngine()
    start_time = time.time()
    try:
        landmarks = engine.read_landmarks(test_img)
        end_time = time.time()
        print(f"   - 랜드마크 감지 시간: {end_time - start_time:.3f}초")
        print(f"   - 감지된 랜드마크 수: {len(landmarks)}개")
    except Exception as e:
        print(f"   - 랜드마크 감지 실패: {e}")


if __name__ == "__main__":
    print("🚀 Reference Files 통합 테스트 시작")
    print("=" * 50)
    
    # 기본 호환성 테스트
    test_reference_compatibility()
    
    # 실제 이미지 테스트
    test_real_image_if_available()
    
    # 샘플 이미지 생성 및 테스트
    create_sample_test_image()
    
    # 성능 테스트
    performance_test()
    
    print("\n" + "=" * 50)
    print("🎉 모든 테스트 완료!")
    print("\n💡 사용 방법:")
    print("1. CLI 모드: python enhanced_makeup_app_reference.py --image path/to/image.jpg")
    print("2. Streamlit 모드: streamlit run enhanced_makeup_app_reference.py")
    print("3. 기존 앱: streamlit run enhanced_streamlit_makeup_app.py")