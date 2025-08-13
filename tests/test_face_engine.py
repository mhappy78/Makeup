"""
얼굴 처리 엔진 테스트
"""
import numpy as np
import cv2
from engines.face_engine import MediaPipeFaceEngine, VideoStream
from models.core import Point3D, Color


def test_face_detection():
    """얼굴 감지 기능 테스트"""
    print("얼굴 감지 기능 테스트 시작...")
    
    # 테스트용 이미지 생성 (실제로는 카메라나 이미지 파일에서 읽어옴)
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image.fill(128)  # 회색 배경
    
    # MediaPipe 얼굴 엔진 초기화
    face_engine = MediaPipeFaceEngine()
    
    # 얼굴 감지 시도
    detection_result = face_engine.detect_face(test_image)
    
    if detection_result:
        print(f"✓ 얼굴 감지 성공! 신뢰도: {detection_result.confidence:.2f}")
        print(f"  - 바운딩 박스: ({detection_result.bbox.x}, {detection_result.bbox.y}, "
              f"{detection_result.bbox.width}, {detection_result.bbox.height})")
        print(f"  - 랜드마크 개수: {len(detection_result.landmarks)}")
        print(f"  - 얼굴 영역 개수: {len(detection_result.face_regions)}")
    else:
        print("✗ 얼굴이 감지되지 않았습니다 (테스트 이미지에는 얼굴이 없음)")
    
    print("얼굴 감지 기능 테스트 완료\n")


def test_landmark_extraction():
    """랜드마크 추출 기능 테스트"""
    print("랜드마크 추출 기능 테스트 시작...")
    
    # 테스트용 이미지
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    face_engine = MediaPipeFaceEngine()
    landmarks = face_engine.extract_landmarks(test_image)
    
    print(f"추출된 랜드마크 개수: {len(landmarks)}")
    
    if landmarks:
        print("✓ 랜드마크 추출 성공!")
        # 첫 번째 랜드마크 정보 출력
        first_landmark = landmarks[0]
        print(f"  - 첫 번째 랜드마크: ({first_landmark.x:.2f}, {first_landmark.y:.2f}, {first_landmark.z:.2f})")
    else:
        print("✗ 랜드마크가 추출되지 않았습니다 (테스트 이미지에는 얼굴이 없음)")
    
    print("랜드마크 추출 기능 테스트 완료\n")


def test_face_analysis():
    """얼굴 분석 기능 테스트"""
    print("얼굴 분석 기능 테스트 시작...")
    
    face_engine = MediaPipeFaceEngine()
    
    # 더미 랜드마크 데이터 생성 (468개)
    dummy_landmarks = []
    for i in range(468):
        dummy_landmarks.append(Point3D(
            x=100 + (i % 20) * 10,
            y=100 + (i // 20) * 5,
            z=0
        ))
    
    # 얼굴 분석 수행
    analysis = face_engine.analyze_face_structure(dummy_landmarks)
    
    print("✓ 얼굴 분석 완료!")
    print(f"  - 얼굴 형태: {analysis.face_shape.value}")
    print(f"  - 피부톤: RGB({analysis.skin_tone.r}, {analysis.skin_tone.g}, {analysis.skin_tone.b})")
    print(f"  - 눈 형태: {analysis.eye_shape.value}")
    print(f"  - 코 형태: {analysis.nose_shape.value}")
    print(f"  - 입술 형태: {analysis.lip_shape.value}")
    print(f"  - 대칭성 점수: {analysis.symmetry_score:.2f}")
    
    print("얼굴 분석 기능 테스트 완료\n")


def test_face_regions():
    """얼굴 영역 분할 기능 테스트"""
    print("얼굴 영역 분할 기능 테스트 시작...")
    
    face_engine = MediaPipeFaceEngine()
    
    # 더미 랜드마크 데이터 생성 (468개)
    dummy_landmarks = []
    for i in range(468):
        dummy_landmarks.append(Point3D(
            x=100 + (i % 20) * 10,
            y=100 + (i // 20) * 5,
            z=0
        ))
    
    # 얼굴 영역 분할 수행
    face_regions = face_engine.get_face_regions(dummy_landmarks)
    
    print("✓ 얼굴 영역 분할 완료!")
    print(f"  - 총 영역 개수: {len(face_regions)}")
    
    for region_name, region in face_regions.items():
        print(f"  - {region_name}: 포인트 {len(region.points)}개, "
              f"중심 ({region.center.x:.1f}, {region.center.y:.1f}), "
              f"면적 {region.area:.1f}")
    
    print("얼굴 영역 분할 기능 테스트 완료\n")


def test_video_stream():
    """비디오 스트림 기능 테스트"""
    print("비디오 스트림 기능 테스트 시작...")
    
    try:
        # 비디오 스트림 생성 (카메라가 없으면 실패할 수 있음)
        video_stream = VideoStream(source=0)
        
        print("✓ VideoStream 객체 생성 성공")
        print(f"  - 소스: {video_stream.source}")
        print(f"  - 활성 상태: {video_stream.is_active}")
        
        # 스트림 시작 시도 (카메라가 없으면 예외 발생)
        try:
            video_stream.start()
            print("✓ 비디오 스트림 시작 성공")
            
            # 프레임 읽기 테스트
            frame = video_stream.read_frame()
            if frame is not None:
                print(f"✓ 프레임 읽기 성공: {frame.shape}")
            else:
                print("✗ 프레임 읽기 실패")
            
            video_stream.stop()
            print("✓ 비디오 스트림 정지 성공")
            
        except RuntimeError as e:
            print(f"✗ 비디오 스트림 시작 실패: {e}")
            print("  (카메라가 연결되지 않았거나 사용 중일 수 있습니다)")
    
    except Exception as e:
        print(f"✗ 비디오 스트림 테스트 실패: {e}")
    
    print("비디오 스트림 기능 테스트 완료\n")


if __name__ == "__main__":
    print("=== 얼굴 처리 엔진 테스트 시작 ===\n")
    
    try:
        test_face_detection()
        test_landmark_extraction()
        test_face_analysis()
        test_face_regions()
        test_video_stream()
        
        print("=== 모든 테스트 완료 ===")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()