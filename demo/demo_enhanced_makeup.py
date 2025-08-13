"""
향상된 메이크업 데모 - Reference Files 완전 통합
image.py, utils.py, web_makeup_gui.py의 모든 기능을 통합한 최종 데모
"""
import cv2
import numpy as np
import sys
import os
import argparse

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_makeup_utils import *
from engines.enhanced_makeup_engine import EnhancedMakeupEngine


def demo_basic_makeup(image_path: str):
    """
    기본 메이크업 데모 - Reference files의 image.py와 완전히 동일
    """
    print("🎨 기본 메이크업 데모 (Reference Files 호환)")
    print("-" * 50)
    
    try:
        # Reference files 방식으로 메이크업 적용
        result = apply_simple_makeup_from_reference(image_path)
        
        # 결과 저장
        output_path = f"demo_basic_makeup_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, result)
        
        print(f"✅ 기본 메이크업 완료: {output_path}")
        
        # 이미지 표시 (선택사항)
        show_image(result, "Basic Makeup Result")
        
        return result
        
    except Exception as e:
        print(f"❌ 기본 메이크업 실패: {e}")
        return None


def demo_advanced_makeup(image_path: str):
    """
    고급 메이크업 데모 - 향상된 기능 사용
    """
    print("\n🎭 고급 메이크업 데모 (향상된 기능)")
    print("-" * 50)
    
    try:
        # 이미지 로드
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
        else:
            image = image_path
            
        if image is None:
            print("❌ 이미지를 로드할 수 없습니다.")
            return None
        
        # 커스텀 색상 맵 (더 생생한 색상)
        colors_map = {
            "LIP_UPPER": [30, 30, 200],      # 더 진한 빨간색
            "LIP_LOWER": [30, 30, 200],      # 더 진한 빨간색
            "EYELINER_LEFT": [200, 50, 50],  # 진한 파란색
            "EYELINER_RIGHT": [200, 50, 50], # 진한 파란색
            "EYESHADOW_LEFT": [100, 150, 50], # 올리브 그린
            "EYESHADOW_RIGHT": [100, 150, 50], # 올리브 그린
            "EYEBROW_LEFT": [50, 100, 150],   # 브라운
            "EYEBROW_RIGHT": [50, 100, 150],  # 브라운
        }
        
        # 부위별 강도 설정
        intensity_map = create_intensity_map(
            lip=0.8,        # 입술 강도
            eyeliner=0.9,   # 아이라이너 강도
            eyeshadow=0.6,  # 아이섀도 강도
            eyebrow=0.7     # 눈썹 강도
        )
        
        # 고급 메이크업 적용
        result, mask, face_detected = apply_makeup(
            image, colors_map, intensity_map, 
            mask_alpha=0.4,      # 더 진한 메이크업
            blur_strength=9,     # 더 부드러운 블렌딩
            blur_sigma=5,        # 더 넓은 확산
            show_landmarks=False
        )
        
        if face_detected:
            # 결과 저장
            output_path = f"demo_advanced_makeup_{os.path.basename(image_path) if isinstance(image_path, str) else 'result.jpg'}"
            cv2.imwrite(output_path, result)
            
            # 마스크도 저장
            mask_path = f"demo_advanced_mask_{os.path.basename(image_path) if isinstance(image_path, str) else 'mask.jpg'}"
            cv2.imwrite(mask_path, mask)
            
            print(f"✅ 고급 메이크업 완료: {output_path}")
            print(f"✅ 마스크 저장: {mask_path}")
            
            # 이미지 표시 (선택사항)
            show_image(result, "Advanced Makeup Result")
            
            return result
        else:
            print("❌ 얼굴을 감지하지 못했습니다.")
            return None
            
    except Exception as e:
        print(f"❌ 고급 메이크업 실패: {e}")
        return None


def demo_engine_makeup(image_path: str):
    """
    엔진 기반 메이크업 데모 - EnhancedMakeupEngine 사용
    """
    print("\n🔧 엔진 기반 메이크업 데모")
    print("-" * 50)
    
    try:
        # 엔진 초기화
        engine = EnhancedMakeupEngine()
        
        # 이미지 로드
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
        else:
            image = image_path
            
        if image is None:
            print("❌ 이미지를 로드할 수 없습니다.")
            return None
        
        # 랜드마크 감지
        landmarks = engine.read_landmarks(image)
        print(f"📍 감지된 랜드마크: {len(landmarks)}개")
        
        if len(landmarks) > 0:
            # 엔진으로 메이크업 적용
            result = engine.apply_simple_makeup(image)
            
            # 결과 저장
            output_path = f"demo_engine_makeup_{os.path.basename(image_path) if isinstance(image_path, str) else 'result.jpg'}"
            cv2.imwrite(output_path, result)
            
            print(f"✅ 엔진 메이크업 완료: {output_path}")
            
            # 랜드마크가 표시된 버전도 생성
            landmark_result = engine.draw_landmarks(result, landmarks)
            landmark_path = f"demo_engine_landmarks_{os.path.basename(image_path) if isinstance(image_path, str) else 'landmarks.jpg'}"
            cv2.imwrite(landmark_path, landmark_result)
            print(f"✅ 랜드마크 버전 저장: {landmark_path}")
            
            # 이미지 표시 (선택사항)
            show_image(result, "Engine Makeup Result")
            
            return result
        else:
            print("❌ 얼굴을 감지하지 못했습니다.")
            return None
            
    except Exception as e:
        print(f"❌ 엔진 메이크업 실패: {e}")
        return None


def demo_comparison(image_path: str):
    """
    비교 데모 - 원본, 기본, 고급 메이크업 비교
    """
    print("\n📊 메이크업 비교 데모")
    print("-" * 50)
    
    try:
        # 원본 이미지 로드
        if isinstance(image_path, str):
            original = cv2.imread(image_path)
        else:
            original = image_path
            
        if original is None:
            print("❌ 이미지를 로드할 수 없습니다.")
            return
        
        # 기본 메이크업
        basic_result = apply_simple_makeup_from_reference(original)
        
        # 고급 메이크업
        colors_map = get_default_colors_map()
        intensity_map = create_intensity_map(0.8, 0.9, 0.7, 0.8)
        advanced_result, _, _ = apply_makeup(
            original, colors_map, intensity_map, 0.35, 7, 4, False
        )
        
        # 비교 이미지 생성 (가로로 3개 배치)
        h, w = original.shape[:2]
        comparison = np.zeros((h, w * 3, 3), dtype=np.uint8)
        
        comparison[:, :w] = original
        comparison[:, w:w*2] = basic_result
        comparison[:, w*2:w*3] = advanced_result
        
        # 텍스트 추가
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(comparison, "Original", (10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, "Basic Makeup", (w + 10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, "Advanced Makeup", (w*2 + 10, 30), font, 1, (255, 255, 255), 2)
        
        # 비교 이미지 저장
        comparison_path = f"demo_comparison_{os.path.basename(image_path) if isinstance(image_path, str) else 'comparison.jpg'}"
        cv2.imwrite(comparison_path, comparison)
        
        print(f"✅ 비교 이미지 생성: {comparison_path}")
        
        # 이미지 표시 (선택사항)
        show_image(comparison, "Makeup Comparison")
        
        return comparison
        
    except Exception as e:
        print(f"❌ 비교 데모 실패: {e}")
        return None


def create_demo_image():
    """데모용 샘플 이미지 생성"""
    print("🎨 데모용 샘플 이미지 생성")
    print("-" * 50)
    
    # 고품질 샘플 얼굴 이미지 생성
    img = np.ones((600, 600, 3), dtype=np.uint8) * 245
    
    # 얼굴 윤곽 (더 자연스럽게)
    cv2.ellipse(img, (300, 300), (140, 180), 0, 0, 360, (220, 200, 180), -1)
    
    # 그림자 효과
    cv2.ellipse(img, (300, 320), (120, 160), 0, 0, 360, (210, 190, 170), -1)
    
    # 눈 (더 정교하게)
    # 왼쪽 눈
    cv2.ellipse(img, (250, 260), (35, 20), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(img, (250, 260), (30, 15), 0, 0, 360, (240, 240, 240), -1)
    cv2.circle(img, (250, 260), 12, (100, 80, 60), -1)  # 홍채
    cv2.circle(img, (250, 260), 6, (0, 0, 0), -1)       # 동공
    cv2.circle(img, (248, 258), 2, (255, 255, 255), -1) # 하이라이트
    
    # 오른쪽 눈
    cv2.ellipse(img, (350, 260), (35, 20), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(img, (350, 260), (30, 15), 0, 0, 360, (240, 240, 240), -1)
    cv2.circle(img, (350, 260), 12, (100, 80, 60), -1)  # 홍채
    cv2.circle(img, (350, 260), 6, (0, 0, 0), -1)       # 동공
    cv2.circle(img, (352, 258), 2, (255, 255, 255), -1) # 하이라이트
    
    # 눈썹 (더 자연스럽게)
    cv2.ellipse(img, (250, 230), (25, 8), 15, 0, 180, (120, 100, 80), -1)
    cv2.ellipse(img, (350, 230), (25, 8), 165, 0, 180, (120, 100, 80), -1)
    
    # 코 (더 입체적으로)
    cv2.ellipse(img, (300, 300), (12, 25), 0, 0, 360, (210, 190, 170), -1)
    cv2.ellipse(img, (295, 310), (4, 6), 0, 0, 360, (200, 180, 160), -1)
    cv2.ellipse(img, (305, 310), (4, 6), 0, 0, 360, (200, 180, 160), -1)
    
    # 입 (더 자연스럽게)
    cv2.ellipse(img, (300, 360), (40, 20), 0, 0, 180, (200, 150, 150), -1)
    cv2.ellipse(img, (300, 360), (35, 15), 0, 0, 180, (180, 120, 120), -1)
    cv2.line(img, (270, 360), (330, 360), (160, 100, 100), 2)
    
    # 볼 (블러시 영역)
    cv2.ellipse(img, (200, 320), (20, 15), 0, 0, 360, (230, 190, 180), -1)
    cv2.ellipse(img, (400, 320), (20, 15), 0, 0, 360, (230, 190, 180), -1)
    
    # 저장
    demo_path = "demo_sample_face.jpg"
    cv2.imwrite(demo_path, img)
    print(f"✅ 데모 샘플 이미지 생성: {demo_path}")
    
    return demo_path


def main():
    """메인 데모 함수"""
    print("🎭 향상된 메이크업 데모 시작")
    print("=" * 60)
    print("Reference Files (image.py, utils.py, web_makeup_gui.py) 완전 통합")
    print("=" * 60)
    
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description="Enhanced Makeup Demo - Reference Files Compatible")
    parser.add_argument("--image", type=str, help="Path to the image file")
    parser.add_argument("--demo", choices=['basic', 'advanced', 'engine', 'comparison', 'all'], 
                       default='all', help="Demo type to run")
    parser.add_argument("--create-sample", action='store_true', help="Create sample image for demo")
    args = parser.parse_args()
    
    # 샘플 이미지 생성 (요청시)
    if args.create_sample or not args.image:
        sample_path = create_demo_image()
        if not args.image:
            args.image = sample_path
    
    # 이미지 경로 확인
    if not args.image or not os.path.exists(args.image):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {args.image}")
        return
    
    print(f"\n📸 사용할 이미지: {args.image}")
    
    # 데모 실행
    if args.demo == 'basic' or args.demo == 'all':
        demo_basic_makeup(args.image)
    
    if args.demo == 'advanced' or args.demo == 'all':
        demo_advanced_makeup(args.image)
    
    if args.demo == 'engine' or args.demo == 'all':
        demo_engine_makeup(args.image)
    
    if args.demo == 'comparison' or args.demo == 'all':
        demo_comparison(args.image)
    
    print("\n" + "=" * 60)
    print("🎉 데모 완료!")
    print("\n💡 생성된 파일들:")
    print("- demo_basic_makeup_*.jpg: 기본 메이크업 결과")
    print("- demo_advanced_makeup_*.jpg: 고급 메이크업 결과")
    print("- demo_advanced_mask_*.jpg: 메이크업 마스크")
    print("- demo_engine_makeup_*.jpg: 엔진 메이크업 결과")
    print("- demo_engine_landmarks_*.jpg: 랜드마크 표시 버전")
    print("- demo_comparison_*.jpg: 비교 이미지")
    
    print("\n🚀 다음 단계:")
    print("1. Streamlit 앱 실행: streamlit run enhanced_makeup_app_reference.py")
    print("2. 기존 앱 실행: streamlit run enhanced_streamlit_makeup_app.py")
    print("3. CLI 메이크업: python enhanced_makeup_app_reference.py --image your_image.jpg")


if __name__ == "__main__":
    main()