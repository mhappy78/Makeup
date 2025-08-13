"""
기본 UI 반응성 테스트
"""
import sys
import os
import numpy as np
from unittest.mock import Mock, patch

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_main_interface_import():
    """메인 인터페이스 임포트 테스트"""
    try:
        from ui.main_interface import MainInterface
        print("✅ MainInterface 임포트 성공")
        return True
    except Exception as e:
        print(f"❌ MainInterface 임포트 실패: {e}")
        return False

def test_interface_initialization():
    """인터페이스 초기화 테스트"""
    try:
        with patch('ui.main_interface.st') as mock_st:
            mock_st.session_state = {}
            
            from ui.main_interface import MainInterface
            interface = MainInterface()
            
            # 엔진들이 초기화되었는지 확인
            assert interface.face_engine is not None
            assert interface.makeup_engine is not None
            assert interface.surgery_engine is not None
            assert interface.integrated_engine is not None
            assert interface.image_processor is not None
            assert interface.image_gallery is not None
            
            print("✅ 인터페이스 초기화 성공")
            return True
    except Exception as e:
        print(f"❌ 인터페이스 초기화 실패: {e}")
        return False

def test_config_creation():
    """설정 생성 테스트"""
    try:
        with patch('ui.main_interface.st') as mock_st:
            mock_st.session_state = {
                'lipstick_color': '#FF1493',
                'lipstick_intensity': 0.6,
                'eyeshadow_color1': '#800080',
                'eyeshadow_color2': '#DDA0DD',
                'eyeshadow_intensity': 0.4,
                'blush_color': '#FFB6C1',
                'blush_intensity': 0.3,
                'foundation_color': '#F5DEB3',
                'foundation_coverage': 0.3,
                'nose_height': 0.3,
                'nose_width': -0.2,
                'eye_size': 0.4,
                'eye_shape': 0.1,
                'jaw_width': -0.1,
                'jaw_angle': 0.2
            }
            
            from ui.main_interface import MainInterface
            interface = MainInterface()
            
            # 메이크업 설정 생성
            makeup_config = interface._create_makeup_config()
            assert makeup_config is not None
            assert makeup_config.lipstick is not None
            assert makeup_config.eyeshadow is not None
            assert makeup_config.blush is not None
            assert makeup_config.foundation is not None
            
            # 성형 설정 생성
            surgery_config = interface._create_surgery_config()
            assert surgery_config is not None
            assert surgery_config.nose is not None
            assert surgery_config.eyes is not None
            assert surgery_config.jawline is not None
            
            print("✅ 설정 생성 테스트 성공")
            return True
    except Exception as e:
        print(f"❌ 설정 생성 테스트 실패: {e}")
        return False

def test_face_detection():
    """얼굴 감지 테스트"""
    try:
        with patch('ui.main_interface.st') as mock_st:
            # Mock session state as a dictionary with proper access
            session_dict = {'face_landmarks': None}
            
            # Create a mock object that supports both dict-like and attribute access
            class MockSessionState:
                def __init__(self, data):
                    self._data = data
                
                def get(self, key, default=None):
                    return self._data.get(key, default)
                
                def __getitem__(self, key):
                    return self._data[key]
                
                def __setitem__(self, key, value):
                    self._data[key] = value
                
                def __contains__(self, key):
                    return key in self._data
                
                def __getattr__(self, key):
                    return self._data.get(key)
                
                def __setattr__(self, key, value):
                    if key.startswith('_'):
                        super().__setattr__(key, value)
                    else:
                        self._data[key] = value
            
            mock_st.session_state = MockSessionState(session_dict)
            
            from ui.main_interface import MainInterface
            from models.core import Point3D
            
            interface = MainInterface()
            
            # Mock face engine
            mock_detection_result = Mock()
            mock_detection_result.is_valid.return_value = True
            test_landmarks = [Point3D(100 + i, 200 + i, 0) for i in range(468)]
            mock_detection_result.landmarks = test_landmarks
            
            interface.face_engine.detect_face = Mock(return_value=mock_detection_result)
            
            # 테스트 이미지
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # 얼굴 감지 실행
            interface._detect_face(test_image)
            
            # 얼굴 감지가 호출되었는지 확인
            interface.face_engine.detect_face.assert_called_once_with(test_image)
            
            # 세션 상태가 업데이트되었는지 확인
            assert mock_st.session_state.face_landmarks == test_landmarks
            
            print("✅ 얼굴 감지 테스트 성공")
            return True
    except Exception as e:
        print(f"❌ 얼굴 감지 테스트 실패: {e}")
        return False

def test_ui_responsiveness():
    """UI 반응성 테스트"""
    try:
        import time
        
        with patch('ui.main_interface.st') as mock_st:
            mock_st.session_state = {
                'lipstick_color': '#FF1493',
                'lipstick_intensity': 0.6,
                'eyeshadow_color1': '#800080',
                'eyeshadow_color2': '#DDA0DD',
                'eyeshadow_intensity': 0.4,
                'blush_color': '#FFB6C1',
                'blush_intensity': 0.3,
                'foundation_color': '#F5DEB3',
                'foundation_coverage': 0.3,
                'nose_height': 0.3,
                'nose_width': -0.2,
                'eye_size': 0.4,
                'eye_shape': 0.1,
                'jaw_width': -0.1,
                'jaw_angle': 0.2
            }
            
            from ui.main_interface import MainInterface
            interface = MainInterface()
            
            # 설정 생성 시간 측정
            start_time = time.time()
            
            for _ in range(10):  # 10번 반복
                makeup_config = interface._create_makeup_config()
                surgery_config = interface._create_surgery_config()
            
            end_time = time.time()
            avg_time = (end_time - start_time) / 10
            
            print(f"✅ UI 반응성 테스트 성공 - 평균 처리 시간: {avg_time:.4f}초")
            
            # 평균 처리 시간이 50ms 이하인지 확인
            assert avg_time < 0.05, f"UI 반응성이 너무 느림: {avg_time:.4f}초"
            
            return True
    except Exception as e:
        print(f"❌ UI 반응성 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 기본 UI 반응성 테스트 시작\n")
    
    tests = [
        ("메인 인터페이스 임포트", test_main_interface_import),
        ("인터페이스 초기화", test_interface_initialization),
        ("설정 생성", test_config_creation),
        ("얼굴 감지", test_face_detection),
        ("UI 반응성", test_ui_responsiveness)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name} 테스트 중...")
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 기본 UI 반응성 테스트 통과!")
        return True
    else:
        print("❌ 일부 테스트 실패")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)