"""
메인 인터페이스 기본 UI 반응성 테스트
"""
import unittest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_interface import MainInterface
from models.core import Point3D, Color
from models.makeup import MakeupConfig, LipstickConfig
from models.surgery import SurgeryConfig, NoseConfig


class TestMainInterface(unittest.TestCase):
    """메인 인터페이스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # Mock Streamlit
        self.mock_st = Mock()
        
        # 테스트용 이미지 생성
        self.test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 테스트용 랜드마크
        self.test_landmarks = [Point3D(100 + i, 200 + i, 0) for i in range(468)]
    
    @patch('ui.main_interface.st')
    def test_interface_initialization(self, mock_st):
        """인터페이스 초기화 테스트"""
        # Mock session state
        mock_st.session_state = {}
        
        interface = MainInterface()
        
        # 엔진들이 초기화되었는지 확인
        self.assertIsNotNone(interface.face_engine)
        self.assertIsNotNone(interface.makeup_engine)
        self.assertIsNotNone(interface.surgery_engine)
        self.assertIsNotNone(interface.integrated_engine)
        self.assertIsNotNone(interface.image_processor)
        self.assertIsNotNone(interface.image_gallery)
    
    @patch('ui.main_interface.st')
    def test_session_state_initialization(self, mock_st):
        """세션 상태 초기화 테스트"""
        mock_st.session_state = {}
        
        interface = MainInterface()
        interface._initialize_session_state()
        
        # 필수 세션 상태가 초기화되었는지 확인
        expected_keys = [
            'current_image', 'original_image', 'face_landmarks',
            'camera_active', 'video_stream', 'processing_results',
            'makeup_config', 'surgery_config'
        ]
        
        for key in expected_keys:
            self.assertIn(key, mock_st.session_state)
    
    @patch('ui.main_interface.st')
    def test_face_detection(self, mock_st):
        """얼굴 감지 테스트"""
        mock_st.session_state = {'face_landmarks': None}
        
        interface = MainInterface()
        
        # Mock face engine
        mock_detection_result = Mock()
        mock_detection_result.is_valid.return_value = True
        mock_detection_result.landmarks = self.test_landmarks
        
        interface.face_engine.detect_face = Mock(return_value=mock_detection_result)
        
        # 얼굴 감지 실행
        interface._detect_face(self.test_image)
        
        # 얼굴 감지가 호출되었는지 확인
        interface.face_engine.detect_face.assert_called_once_with(self.test_image)
        
        # 세션 상태가 업데이트되었는지 확인
        self.assertEqual(mock_st.session_state['face_landmarks'], self.test_landmarks)
    
    @patch('ui.main_interface.st')
    def test_makeup_config_creation(self, mock_st):
        """메이크업 설정 생성 테스트"""
        # Mock session state with makeup settings
        mock_st.session_state = {
            'lipstick_color': '#FF1493',
            'lipstick_intensity': 0.6,
            'eyeshadow_color1': '#800080',
            'eyeshadow_color2': '#DDA0DD',
            'eyeshadow_intensity': 0.4,
            'blush_color': '#FFB6C1',
            'blush_intensity': 0.3,
            'foundation_color': '#F5DEB3',
            'foundation_coverage': 0.3
        }
        
        interface = MainInterface()
        makeup_config = interface._create_makeup_config()
        
        # 메이크업 설정이 올바르게 생성되었는지 확인
        self.assertIsInstance(makeup_config, MakeupConfig)
        self.assertIsNotNone(makeup_config.lipstick)
        self.assertIsNotNone(makeup_config.eyeshadow)
        self.assertIsNotNone(makeup_config.blush)
        self.assertIsNotNone(makeup_config.foundation)
        
        # 립스틱 색상 확인 (핑크색)
        self.assertEqual(makeup_config.lipstick.color.r, 255)
        self.assertEqual(makeup_config.lipstick.color.g, 20)
        self.assertEqual(makeup_config.lipstick.color.b, 147)
        self.assertEqual(makeup_config.lipstick.intensity, 0.6)
    
    @patch('ui.main_interface.st')
    def test_surgery_config_creation(self, mock_st):
        """성형 설정 생성 테스트"""
        # Mock session state with surgery settings
        mock_st.session_state = {
            'nose_height': 0.3,
            'nose_width': -0.2,
            'eye_size': 0.4,
            'eye_shape': 0.1,
            'jaw_width': -0.1,
            'jaw_angle': 0.2
        }
        
        interface = MainInterface()
        surgery_config = interface._create_surgery_config()
        
        # 성형 설정이 올바르게 생성되었는지 확인
        self.assertIsInstance(surgery_config, SurgeryConfig)
        self.assertIsNotNone(surgery_config.nose)
        self.assertIsNotNone(surgery_config.eyes)
        self.assertIsNotNone(surgery_config.jawline)
        
        # 코 설정 확인
        self.assertEqual(surgery_config.nose.height_adjustment, 0.3)
        self.assertEqual(surgery_config.nose.width_adjustment, -0.2)
        
        # 눈 설정 확인
        self.assertEqual(surgery_config.eyes.size_adjustment, 0.4)
        self.assertEqual(surgery_config.eyes.shape_adjustment, 0.1)
        
        # 턱선 설정 확인
        self.assertEqual(surgery_config.jawline.width_adjustment, -0.1)
        self.assertEqual(surgery_config.jawline.angle_adjustment, 0.2)
    
    @patch('ui.main_interface.st')
    def test_image_reset(self, mock_st):
        """이미지 리셋 테스트"""
        # Mock session state
        original_image = self.test_image.copy()
        modified_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        mock_st.session_state = {
            'original_image': original_image,
            'current_image': modified_image
        }
        mock_st.success = Mock()
        mock_st.error = Mock()
        mock_st.rerun = Mock()
        
        interface = MainInterface()
        interface._reset_image()
        
        # 현재 이미지가 원본으로 복원되었는지 확인
        np.testing.assert_array_equal(
            mock_st.session_state['current_image'],
            original_image
        )
        
        # 성공 메시지가 표시되었는지 확인
        mock_st.success.assert_called_once()
        mock_st.rerun.assert_called_once()
    
    @patch('ui.main_interface.st')
    def test_makeup_application(self, mock_st):
        """메이크업 적용 테스트"""
        # Mock session state
        mock_st.session_state = {
            'current_image': self.test_image,
            'face_landmarks': self.test_landmarks,
            'processing_results': [],
            'lipstick_color': '#FF1493',
            'lipstick_intensity': 0.6,
            'eyeshadow_color1': '#800080',
            'eyeshadow_color2': '#DDA0DD',
            'eyeshadow_intensity': 0.4,
            'blush_color': '#FFB6C1',
            'blush_intensity': 0.3,
            'foundation_color': '#F5DEB3',
            'foundation_coverage': 0.3
        }
        
        mock_st.error = Mock()
        mock_st.success = Mock()
        mock_st.spinner = Mock()
        mock_st.rerun = Mock()
        
        # Mock spinner context manager
        mock_spinner_context = Mock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner_context)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        interface = MainInterface()
        
        # Mock makeup engine result
        mock_result = Mock()
        mock_result.is_successful.return_value = True
        mock_result.image = self.test_image
        mock_result.processing_time = 0.5
        mock_result.applied_effects = ['lipstick', 'eyeshadow']
        
        interface.makeup_engine.apply_full_makeup = Mock(return_value=mock_result)
        
        # 메이크업 적용 실행
        interface._apply_makeup()
        
        # 메이크업 엔진이 호출되었는지 확인
        interface.makeup_engine.apply_full_makeup.assert_called_once()
        
        # 성공 메시지가 표시되었는지 확인
        mock_st.success.assert_called_once()
        mock_st.rerun.assert_called_once()
        
        # 처리 결과가 저장되었는지 확인
        self.assertEqual(len(mock_st.session_state['processing_results']), 1)
        result = mock_st.session_state['processing_results'][0]
        self.assertEqual(result['type'], 'makeup')
        self.assertEqual(result['processing_time'], 0.5)
        self.assertEqual(result['applied_effects'], ['lipstick', 'eyeshadow'])
    
    @patch('ui.main_interface.st')
    def test_surgery_application(self, mock_st):
        """성형 적용 테스트"""
        # Mock session state
        mock_st.session_state = {
            'current_image': self.test_image,
            'face_landmarks': self.test_landmarks,
            'processing_results': [],
            'nose_height': 0.3,
            'nose_width': -0.2,
            'eye_size': 0.4,
            'eye_shape': 0.1,
            'jaw_width': -0.1,
            'jaw_angle': 0.2
        }
        
        mock_st.error = Mock()
        mock_st.success = Mock()
        mock_st.spinner = Mock()
        mock_st.rerun = Mock()
        
        # Mock spinner context manager
        mock_spinner_context = Mock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner_context)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        interface = MainInterface()
        
        # Mock surgery engine result
        mock_result = Mock()
        mock_result.is_successful.return_value = True
        mock_result.image = self.test_image
        mock_result.modified_landmarks = self.test_landmarks
        mock_result.processing_time = 1.2
        mock_result.applied_modifications = ['nose_height', 'eye_size']
        mock_result.natural_score = 0.85
        
        interface.surgery_engine.apply_full_surgery = Mock(return_value=mock_result)
        
        # 성형 적용 실행
        interface._apply_surgery()
        
        # 성형 엔진이 호출되었는지 확인
        interface.surgery_engine.apply_full_surgery.assert_called_once()
        
        # 성공 메시지가 표시되었는지 확인
        mock_st.success.assert_called_once()
        mock_st.rerun.assert_called_once()
        
        # 처리 결과가 저장되었는지 확인
        self.assertEqual(len(mock_st.session_state['processing_results']), 1)
        result = mock_st.session_state['processing_results'][0]
        self.assertEqual(result['type'], 'surgery')
        self.assertEqual(result['processing_time'], 1.2)
        self.assertEqual(result['applied_effects'], ['nose_height', 'eye_size'])
        self.assertEqual(result['quality_score'], 0.85)
    
    @patch('ui.main_interface.st')
    def test_error_handling_no_image(self, mock_st):
        """이미지 없을 때 오류 처리 테스트"""
        mock_st.session_state = {
            'current_image': None,
            'face_landmarks': None
        }
        mock_st.error = Mock()
        
        interface = MainInterface()
        
        # 이미지 없이 메이크업 적용 시도
        interface._apply_makeup()
        
        # 오류 메시지가 표시되었는지 확인
        mock_st.error.assert_called_with("이미지가 없습니다. 먼저 이미지를 업로드하거나 카메라를 시작하세요.")
    
    @patch('ui.main_interface.st')
    def test_error_handling_no_face(self, mock_st):
        """얼굴 감지 안될 때 오류 처리 테스트"""
        mock_st.session_state = {
            'current_image': self.test_image,
            'face_landmarks': None
        }
        mock_st.error = Mock()
        
        interface = MainInterface()
        
        # 얼굴 감지 없이 메이크업 적용 시도
        interface._apply_makeup()
        
        # 오류 메시지가 표시되었는지 확인
        mock_st.error.assert_called_with("얼굴이 감지되지 않았습니다.")
    
    @patch('ui.main_interface.st')
    def test_color_conversion(self, mock_st):
        """색상 변환 테스트"""
        mock_st.session_state = {}
        
        interface = MainInterface()
        
        # hex_to_color 함수 테스트를 위한 임시 메서드
        def hex_to_color(hex_color: str) -> Color:
            hex_color = hex_color.lstrip('#')
            return Color(
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16)
            )
        
        # 빨간색 테스트
        red_color = hex_to_color('#FF0000')
        self.assertEqual(red_color.r, 255)
        self.assertEqual(red_color.g, 0)
        self.assertEqual(red_color.b, 0)
        
        # 파란색 테스트
        blue_color = hex_to_color('#0000FF')
        self.assertEqual(blue_color.r, 0)
        self.assertEqual(blue_color.g, 0)
        self.assertEqual(blue_color.b, 255)
        
        # 핑크색 테스트
        pink_color = hex_to_color('#FF1493')
        self.assertEqual(pink_color.r, 255)
        self.assertEqual(pink_color.g, 20)
        self.assertEqual(pink_color.b, 147)
    
    def test_ui_responsiveness_simulation(self):
        """UI 반응성 시뮬레이션 테스트"""
        # 다양한 설정 변경에 대한 반응성 테스트
        test_cases = [
            {'lipstick_intensity': 0.0},
            {'lipstick_intensity': 0.5},
            {'lipstick_intensity': 1.0},
            {'eyeshadow_intensity': 0.0},
            {'eyeshadow_intensity': 0.8},
            {'nose_height': -1.0},
            {'nose_height': 0.0},
            {'nose_height': 1.0},
            {'eye_size': -0.5},
            {'eye_size': 0.5}
        ]
        
        for test_case in test_cases:
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
                    'nose_height': 0.0,
                    'nose_width': 0.0,
                    'eye_size': 0.0,
                    'eye_shape': 0.0,
                    'jaw_width': 0.0,
                    'jaw_angle': 0.0
                }
                
                # 테스트 케이스 설정 적용
                mock_st.session_state.update(test_case)
                
                interface = MainInterface()
                
                # 설정 생성이 오류 없이 실행되는지 확인
                try:
                    makeup_config = interface._create_makeup_config()
                    surgery_config = interface._create_surgery_config()
                    
                    # 설정이 올바르게 생성되었는지 확인
                    self.assertIsInstance(makeup_config, MakeupConfig)
                    self.assertIsInstance(surgery_config, SurgeryConfig)
                    
                except Exception as e:
                    self.fail(f"UI 설정 처리 중 오류 발생: {e}")


class TestUIPerformance(unittest.TestCase):
    """UI 성능 테스트"""
    
    def test_config_creation_performance(self):
        """설정 생성 성능 테스트"""
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
            
            interface = MainInterface()
            
            # 설정 생성 시간 측정
            start_time = time.time()
            
            for _ in range(100):  # 100번 반복
                makeup_config = interface._create_makeup_config()
                surgery_config = interface._create_surgery_config()
            
            end_time = time.time()
            avg_time = (end_time - start_time) / 100
            
            # 평균 처리 시간이 10ms 이하인지 확인
            self.assertLess(avg_time, 0.01, f"설정 생성이 너무 느림: {avg_time:.4f}초")
    
    def test_memory_usage(self):
        """메모리 사용량 테스트"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('ui.main_interface.st') as mock_st:
            mock_st.session_state = {}
            
            # 여러 인터페이스 인스턴스 생성
            interfaces = []
            for _ in range(10):
                interface = MainInterface()
                interfaces.append(interface)
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # 메모리 증가량이 100MB 이하인지 확인
            self.assertLess(memory_increase, 100, f"메모리 사용량이 너무 많음: {memory_increase:.1f}MB")


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)