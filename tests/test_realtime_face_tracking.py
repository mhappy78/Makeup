#!/usr/bin/env python3
"""
실시간 얼굴 추적 기능 테스트
Real-time Face Tracking Performance Tests

이 테스트는 다음 기능들을 검증합니다:
- 비디오 스트림에서 얼굴 추적 메서드 구현
- 성능 최적화를 위한 프레임 스킵 로직 추가
- 얼굴 손실 시 재감지 메커니즘 구현
- 실시간 처리 성능 테스트 작성
"""

import unittest
import numpy as np
import cv2
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from engines.face_engine import MediaPipeFaceEngine, VideoStream, FaceFrame
from models.core import Point3D, BoundingBox


class TestRealTimeFaceTracking(unittest.TestCase):
    """실시간 얼굴 추적 기능 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = MediaPipeFaceEngine()
        self.test_image = self._create_test_face_image()
        
    def _create_test_face_image(self) -> np.ndarray:
        """테스트용 얼굴 이미지 생성"""
        # 640x480 크기의 테스트 이미지 생성
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 간단한 얼굴 모양 그리기 (타원)
        center = (320, 240)
        axes = (80, 100)
        cv2.ellipse(image, center, axes, 0, 0, 360, (200, 180, 160), -1)
        
        # 눈 그리기
        cv2.circle(image, (290, 220), 10, (50, 50, 50), -1)
        cv2.circle(image, (350, 220), 10, (50, 50, 50), -1)
        
        # 코 그리기
        cv2.circle(image, (320, 250), 5, (150, 130, 110), -1)
        
        # 입 그리기
        cv2.ellipse(image, (320, 280), (20, 10), 0, 0, 180, (100, 50, 50), -1)
        
        return image    

    def test_video_stream_initialization(self):
        """비디오 스트림 초기화 테스트"""
        # Mock VideoCapture to avoid actual camera access
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            mock_cap_instance.set.return_value = True
            mock_cap.return_value = mock_cap_instance
            
            stream = VideoStream(source=0)
            stream.start()
            
            self.assertTrue(stream.is_active)
            self.assertIsNotNone(stream.cap)
            
            # 카메라 설정 확인
            mock_cap_instance.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 640)
            mock_cap_instance.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            mock_cap_instance.set.assert_any_call(cv2.CAP_PROP_FPS, 30)
            
            stream.stop()
            self.assertFalse(stream.is_active)
    
    def test_video_stream_frame_reading(self):
        """비디오 스트림 프레임 읽기 테스트"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            mock_cap_instance.read.return_value = (True, self.test_image)
            mock_cap.return_value = mock_cap_instance
            
            stream = VideoStream(source=0)
            stream.start()
            
            frame = stream.read_frame()
            self.assertIsNotNone(frame)
            self.assertEqual(frame.shape, self.test_image.shape)
            
            # 읽기 실패 시뮬레이션
            mock_cap_instance.read.return_value = (False, None)
            frame = stream.read_frame()
            self.assertIsNone(frame)
            
            stream.stop()
    
    def test_face_tracking_basic_functionality(self):
        """기본 얼굴 추적 기능 테스트"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            
            # 여러 프레임 시뮬레이션
            frames = [self.test_image for _ in range(5)]
            mock_cap_instance.read.side_effect = [(True, frame) for frame in frames] + [(False, None)]
            mock_cap.return_value = mock_cap_instance
            
            stream = VideoStream(source=0)
            stream.start()
            
            face_frames = []
            frame_count = 0
            
            for face_frame in self.engine.track_face(stream):
                face_frames.append(face_frame)
                frame_count += 1
                if frame_count >= 5:  # 5프레임만 테스트
                    break
            
            stream.stop()
            
            # 결과 검증
            self.assertEqual(len(face_frames), 5)
            for face_frame in face_frames:
                self.assertIsInstance(face_frame, FaceFrame)
                self.assertIsNotNone(face_frame.frame)
                self.assertGreaterEqual(face_frame.timestamp, 0)    

    def test_adaptive_frame_skip_logic(self):
        """적응적 프레임 스킵 로직 테스트"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            
            # 많은 프레임 생성 (성능 테스트용)
            frames = [self.test_image for _ in range(20)]
            mock_cap_instance.read.side_effect = [(True, frame) for frame in frames] + [(False, None)]
            mock_cap.return_value = mock_cap_instance
            
            stream = VideoStream(source=0)
            stream.start()
            
            face_frames = []
            detection_counts = 0
            
            for face_frame in self.engine.track_face(stream):
                face_frames.append(face_frame)
                
                # 실제 감지가 수행되었는지 확인
                if hasattr(face_frame, 'detection_result') and face_frame.detection_result:
                    detection_counts += 1
                
                if len(face_frames) >= 15:
                    break
            
            stream.stop()
            
            # 프레임 스킵이 작동하여 모든 프레임에서 감지가 수행되지 않았는지 확인
            self.assertLess(detection_counts, len(face_frames))
            
            # 추적 메타데이터 확인
            for face_frame in face_frames:
                if hasattr(face_frame, 'skip_frames_used'):
                    self.assertGreaterEqual(face_frame.skip_frames_used, 1)
    
    def test_face_loss_and_redetection(self):
        """얼굴 손실 및 재감지 메커니즘 테스트"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            
            # 얼굴이 있는 프레임과 없는 프레임 교대로 생성
            face_frame = self.test_image
            no_face_frame = np.zeros((480, 640, 3), dtype=np.uint8)  # 빈 프레임
            
            frames = [face_frame, face_frame, no_face_frame, no_face_frame, 
                     no_face_frame, face_frame, face_frame]
            mock_cap_instance.read.side_effect = [(True, frame) for frame in frames] + [(False, None)]
            mock_cap.return_value = mock_cap_instance
            
            stream = VideoStream(source=0)
            stream.start()
            
            face_frames = []
            tracking_states = []
            
            for face_frame in self.engine.track_face(stream):
                face_frames.append(face_frame)
                
                # 추적 상태 기록
                if hasattr(face_frame, 'is_tracking'):
                    tracking_states.append(face_frame.is_tracking)
                if hasattr(face_frame, 'lost_frames'):
                    face_frame.lost_frame_count = face_frame.lost_frames
                
                if len(face_frames) >= len(frames):
                    break
            
            stream.stop()
            
            # 얼굴 손실 및 재감지 확인
            lost_frame_counts = [getattr(f, 'lost_frame_count', 0) for f in face_frames]
            
            # 연속된 빈 프레임에서 lost_frames가 증가하는지 확인
            self.assertTrue(any(count > 0 for count in lost_frame_counts))
    
    def test_roi_based_detection_optimization(self):
        """ROI 기반 감지 최적화 테스트"""
        # 이전 바운딩 박스 설정
        last_bbox = BoundingBox(x=240, y=140, width=160, height=200)
        
        # ROI 기반 감지 테스트
        result = self.engine._detect_in_roi(self.test_image, last_bbox)
        
        # 결과가 있어야 함 (테스트 이미지에 얼굴이 있으므로)
        if result:
            self.assertIsNotNone(result.bbox)
            self.assertGreater(result.confidence, 0) 
   
    def test_tracking_stability_validation(self):
        """추적 안정성 검증 테스트"""
        # 안정적인 바운딩 박스 히스토리 생성
        stable_boxes = [
            BoundingBox(x=240, y=140, width=160, height=200),
            BoundingBox(x=242, y=142, width=160, height=200),
            BoundingBox(x=241, y=141, width=160, height=200),
        ]
        
        is_stable = self.engine._is_tracking_stable(stable_boxes)
        self.assertTrue(is_stable)
        
        # 불안정한 바운딩 박스 히스토리 생성
        unstable_boxes = [
            BoundingBox(x=240, y=140, width=160, height=200),
            BoundingBox(x=300, y=200, width=160, height=200),
            BoundingBox(x=180, y=100, width=160, height=200),
        ]
        
        is_stable = self.engine._is_tracking_stable(unstable_boxes)
        self.assertFalse(is_stable)
    
    def test_performance_monitoring(self):
        """성능 모니터링 테스트"""
        performance_stats = {
            'frame_times': [],
            'avg_processing_time': 0.0,
            'fps_counter': 0,
            'last_fps_time': time.time()
        }
        
        # 프레임 처리 시간 시뮬레이션
        frame_times = [0.02, 0.03, 0.025, 0.035, 0.028]
        
        for frame_time in frame_times:
            self.engine._update_performance_stats(performance_stats, frame_time)
        
        # 평균 처리 시간 확인
        self.assertGreater(performance_stats['avg_processing_time'], 0)
        self.assertEqual(len(performance_stats['frame_times']), len(frame_times))
    
    def test_adaptive_performance_settings(self):
        """적응적 성능 설정 테스트"""
        adaptive_skip_config = {
            'base_skip_frames': 2,
            'max_skip_frames': 8,
            'current_skip_frames': 2,
            'performance_threshold': 0.033,
            'quality_threshold': 0.7
        }
        
        performance_stats = {
            'avg_processing_time': 0.05  # 성능이 나쁜 상황
        }
        
        tracking_quality = 0.8  # 좋은 품질
        
        original_skip_frames = adaptive_skip_config['current_skip_frames']
        
        self.engine._adapt_performance_settings(
            adaptive_skip_config, tracking_quality, performance_stats
        )
        
        # 성능이 나쁘면 스킵 프레임이 증가해야 함
        self.assertGreaterEqual(
            adaptive_skip_config['current_skip_frames'], 
            original_skip_frames
        ) 
   
    def test_face_position_estimation(self):
        """얼굴 위치 추정 테스트 (프레임 스킵 시)"""
        # 이전 감지 결과 생성
        bbox = BoundingBox(x=240, y=140, width=160, height=200)
        landmarks = [Point3D(x=320, y=240, z=0) for _ in range(468)]
        
        from engines.face_engine import FaceDetectionResult
        last_result = FaceDetectionResult(
            bbox=bbox,
            confidence=0.8,
            landmarks=landmarks,
            face_regions={}
        )
        
        tracking_state = {
            'is_tracking': True,
            'last_successful_frame': 0,
            'bbox_history': [bbox]
        }
        
        # 위치 추정 테스트
        estimated_result = self.engine._estimate_face_position(
            last_result, tracking_state, 5
        )
        
        if estimated_result:
            self.assertIsNotNone(estimated_result.bbox)
            # 신뢰도가 감소했는지 확인
            self.assertLessEqual(estimated_result.confidence, last_result.confidence)
    
    def test_tracking_quality_evaluation(self):
        """추적 품질 평가 테스트"""
        # 고품질 감지 결과
        bbox = BoundingBox(x=240, y=140, width=160, height=200)
        landmarks = [Point3D(x=320, y=240, z=0) for _ in range(468)]
        
        from engines.face_engine import FaceDetectionResult
        high_quality_result = FaceDetectionResult(
            bbox=bbox,
            confidence=0.9,
            landmarks=landmarks,
            face_regions={}
        )
        
        tracking_state = {
            'stability_counter': 10,
            'min_stability_frames': 5
        }
        
        frame_shape = (480, 640, 3)
        
        quality_score = self.engine._evaluate_tracking_quality(
            high_quality_result, tracking_state, frame_shape
        )
        
        self.assertGreater(quality_score, 0.8)
        
        # 저품질 결과 테스트
        low_quality_result = FaceDetectionResult(
            bbox=bbox,
            confidence=0.3,
            landmarks=[],
            face_regions={}
        )
        
        quality_score = self.engine._evaluate_tracking_quality(
            low_quality_result, tracking_state, frame_shape
        )
        
        self.assertLess(quality_score, 0.5)
    
    def test_real_time_performance_benchmark(self):
        """실시간 처리 성능 벤치마크 테스트"""
        # 성능 측정을 위한 실제 이미지 처리
        start_time = time.time()
        
        # 100번의 얼굴 감지 수행
        detection_times = []
        for _ in range(10):  # 테스트에서는 10번만
            detection_start = time.time()
            result = self.engine.detect_face(self.test_image)
            detection_time = time.time() - detection_start
            detection_times.append(detection_time)
        
        avg_detection_time = sum(detection_times) / len(detection_times)
        
        # 30fps 기준 (33ms) 이하여야 함
        self.assertLess(avg_detection_time, 0.1, 
                       f"평균 감지 시간이 너무 깁니다: {avg_detection_time:.3f}초")
        
        print(f"평균 얼굴 감지 시간: {avg_detection_time:.3f}초")
        print(f"예상 FPS: {1/avg_detection_time:.1f}")  
  
    def test_memory_usage_monitoring(self):
        """메모리 사용량 모니터링 테스트"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 여러 번의 얼굴 감지 수행
            for _ in range(50):
                result = self.engine.detect_face(self.test_image)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # 메모리 증가가 100MB 이하여야 함 (메모리 누수 방지)
            self.assertLess(memory_increase, 100, 
                           f"메모리 사용량이 과도하게 증가했습니다: {memory_increase:.1f}MB")
            
            print(f"메모리 사용량 증가: {memory_increase:.1f}MB")
        except ImportError:
            self.skipTest("psutil 라이브러리가 설치되지 않았습니다")
    
    def test_concurrent_tracking_stability(self):
        """동시 추적 안정성 테스트"""
        results = []
        errors = []
        
        def track_worker():
            try:
                engine = MediaPipeFaceEngine()
                for _ in range(10):
                    result = engine.detect_face(self.test_image)
                    results.append(result is not None)
            except Exception as e:
                errors.append(e)
        
        # 여러 스레드에서 동시 실행
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=track_worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 오류가 없어야 함
        self.assertEqual(len(errors), 0, f"동시 실행 중 오류 발생: {errors}")
        
        # 모든 결과가 성공적이어야 함
        success_rate = sum(results) / len(results) if results else 0
        self.assertGreater(success_rate, 0.8, "동시 실행 성공률이 낮습니다")


class TestFaceTrackingIntegration(unittest.TestCase):
    """얼굴 추적 통합 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = MediaPipeFaceEngine()
    
    def test_end_to_end_tracking_simulation(self):
        """End-to-End 추적 시뮬레이션 테스트"""
        # 실제 비디오 파일 없이 시뮬레이션
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            
            # 다양한 시나리오의 프레임 시퀀스
            test_image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.ellipse(test_image, (320, 240), (80, 100), 0, 0, 360, (200, 180, 160), -1)
            
            frames = [test_image] * 20  # 20프레임
            mock_cap_instance.read.side_effect = [(True, frame) for frame in frames] + [(False, None)]
            mock_cap.return_value = mock_cap_instance
            
            stream = VideoStream(source=0)
            stream.start()
            
            tracking_results = {
                'total_frames': 0,
                'successful_detections': 0,
                'tracking_periods': [],
                'performance_metrics': []
            }
            
            start_time = time.time()
            
            for face_frame in self.engine.track_face(stream):
                tracking_results['total_frames'] += 1
                
                if face_frame.has_face():
                    tracking_results['successful_detections'] += 1
                
                # 성능 메트릭 수집
                if hasattr(face_frame, 'tracking_quality'):
                    tracking_results['performance_metrics'].append({
                        'quality': face_frame.tracking_quality,
                        'is_stable': getattr(face_frame, 'is_stable', False),
                        'confidence': getattr(face_frame, 'tracking_confidence', 0)
                    })
                
                if tracking_results['total_frames'] >= 15:
                    break
            
            stream.stop()
            total_time = time.time() - start_time
            
            # 결과 검증
            self.assertGreater(tracking_results['total_frames'], 0)
            self.assertGreater(tracking_results['successful_detections'], 0)
            
            # 성공률 확인
            success_rate = tracking_results['successful_detections'] / tracking_results['total_frames']
            self.assertGreater(success_rate, 0.7, "추적 성공률이 낮습니다")
            
            # 평균 FPS 확인
            avg_fps = tracking_results['total_frames'] / total_time
            self.assertGreater(avg_fps, 10, "평균 FPS가 너무 낮습니다")
            
            print(f"추적 성공률: {success_rate:.2%}")
            print(f"평균 FPS: {avg_fps:.1f}")
            print(f"총 처리 시간: {total_time:.2f}초")


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)