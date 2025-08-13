"""
실시간 얼굴 추적 성능 테스트
"""
import unittest
import numpy as np
import cv2
import time
import threading
from unittest.mock import Mock, patch
from engines.face_engine import MediaPipeFaceEngine, VideoStream
from models.core import BoundingBox


class TestRealtimePerformance(unittest.TestCase):
    """실시간 성능 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.face_engine = MediaPipeFaceEngine()
        
        # 성능 테스트용 고해상도 이미지
        self.hd_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.circle(self.hd_frame, (640, 360), 150, (255, 255, 255), -1)
        cv2.circle(self.hd_frame, (600, 330), 15, (0, 0, 0), -1)
        cv2.circle(self.hd_frame, (680, 330), 15, (0, 0, 0), -1)
        cv2.ellipse(self.hd_frame, (640, 390), (30, 15), 0, 0, 180, (0, 0, 0), -1)
        
        # 표준 해상도 이미지
        self.sd_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.circle(self.sd_frame, (320, 240), 100, (255, 255, 255), -1)
        cv2.circle(self.sd_frame, (290, 220), 10, (0, 0, 0), -1)
        cv2.circle(self.sd_frame, (350, 220), 10, (0, 0, 0), -1)
        cv2.ellipse(self.sd_frame, (320, 260), (20, 10), 0, 0, 180, (0, 0, 0), -1)
    
    def test_face_detection_performance(self):
        """얼굴 감지 성능 테스트"""
        # 표준 해상도 성능 측정
        start_time = time.time()
        iterations = 10
        
        for _ in range(iterations):
            result = self.face_engine.detect_face(self.sd_frame)
        
        sd_avg_time = (time.time() - start_time) / iterations
        
        # HD 해상도 성능 측정
        start_time = time.time()
        
        for _ in range(iterations):
            result = self.face_engine.detect_face(self.hd_frame)
        
        hd_avg_time = (time.time() - start_time) / iterations
        
        print(f"SD 평균 감지 시간: {sd_avg_time:.4f}초")
        print(f"HD 평균 감지 시간: {hd_avg_time:.4f}초")
        
        # 성능 기준 검증 (30fps 기준 33ms 이하)
        self.assertLess(sd_avg_time, 0.033, "SD 해상도에서 30fps 성능 미달")
        self.assertLess(hd_avg_time, 0.1, "HD 해상도에서 10fps 성능 미달")
    
    def test_landmark_extraction_performance(self):
        """랜드마크 추출 성능 테스트"""
        iterations = 20
        
        start_time = time.time()
        for _ in range(iterations):
            landmarks = self.face_engine.extract_landmarks(self.sd_frame)
        
        avg_time = (time.time() - start_time) / iterations
        
        print(f"랜드마크 추출 평균 시간: {avg_time:.4f}초")
        
        # 468개 랜드마크 추출이 빠르게 수행되어야 함
        self.assertLess(avg_time, 0.05, "랜드마크 추출 성능 미달")
    
    def test_roi_detection_performance_improvement(self):
        """ROI 기반 감지 성능 향상 테스트"""
        bbox = BoundingBox(x=220, y=140, width=200, height=200)
        iterations = 15
        
        # 전체 프레임 감지 시간 측정
        start_time = time.time()
        for _ in range(iterations):
            result = self.face_engine.detect_face(self.sd_frame)
        full_frame_time = (time.time() - start_time) / iterations
        
        # ROI 기반 감지 시간 측정
        start_time = time.time()
        for _ in range(iterations):
            result = self.face_engine._detect_in_roi(self.sd_frame, bbox)
        roi_time = (time.time() - start_time) / iterations
        
        print(f"전체 프레임 감지 시간: {full_frame_time:.4f}초")
        print(f"ROI 기반 감지 시간: {roi_time:.4f}초")
        print(f"성능 향상: {(full_frame_time / roi_time):.2f}배")
        
        # ROI 기반 감지가 더 빨라야 함
        self.assertLess(roi_time, full_frame_time, "ROI 기반 감지가 더 느림")
    
    def test_memory_usage_stability(self):
        """메모리 사용량 안정성 테스트"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 연속적인 얼굴 감지 수행
        for i in range(100):
            result = self.face_engine.detect_face(self.sd_frame)
            landmarks = self.face_engine.extract_landmarks(self.sd_frame)
            
            # 중간에 메모리 체크
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                print(f"반복 {i}: 메모리 사용량 {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
                
                # 메모리 누수 방지 - 50MB 이상 증가하면 실패
                self.assertLess(memory_increase, 50, f"메모리 누수 의심: {memory_increase:.1f}MB 증가")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"최종 메모리 증가량: {total_increase:.1f}MB")
        self.assertLess(total_increase, 100, "과도한 메모리 사용량 증가")
    
    def test_concurrent_processing_performance(self):
        """동시 처리 성능 테스트"""
        def detection_worker(frame, results, worker_id):
            """워커 스레드 함수"""
            start_time = time.time()
            result = self.face_engine.detect_face(frame)
            processing_time = time.time() - start_time
            results[worker_id] = processing_time
        
        # 단일 스레드 성능
        start_time = time.time()
        for _ in range(4):
            self.face_engine.detect_face(self.sd_frame)
        single_thread_time = time.time() - start_time
        
        # 멀티 스레드 성능 (4개 스레드)
        threads = []
        results = {}
        
        start_time = time.time()
        for i in range(4):
            thread = threading.Thread(
                target=detection_worker, 
                args=(self.sd_frame, results, i)
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        multi_thread_time = time.time() - start_time
        
        print(f"단일 스레드 시간: {single_thread_time:.4f}초")
        print(f"멀티 스레드 시간: {multi_thread_time:.4f}초")
        print(f"병렬 처리 효율: {(single_thread_time / multi_thread_time):.2f}배")
        
        # 멀티스레드가 더 빠르거나 비슷해야 함 (GIL 고려)
        self.assertLessEqual(multi_thread_time, single_thread_time * 1.2)
    
    def test_adaptive_skip_performance_impact(self):
        """적응적 스킵의 성능 영향 테스트"""
        # Mock 비디오 스트림 생성
        frames = [self.sd_frame] * 30  # 30프레임
        mock_stream = Mock()
        mock_stream.is_active = True
        frame_iter = iter(frames + [None])
        mock_stream.read_frame.side_effect = lambda: next(frame_iter, None)
        
        # 실제 감지 결과 Mock
        with patch.object(self.face_engine, 'detect_face') as mock_detect:
            mock_result = Mock()
            mock_result.is_valid.return_value = True
            mock_result.confidence = 0.8
            mock_result.bbox = BoundingBox(x=220, y=140, width=200, height=200)
            mock_result.landmarks = []
            mock_result.face_regions = {}
            mock_detect.return_value = mock_result
            
            start_time = time.time()
            frame_count = 0
            
            for face_frame in self.face_engine.track_face(mock_stream):
                frame_count += 1
                if frame_count >= 20:  # 20프레임 처리
                    break
            
            total_time = time.time() - start_time
            fps = frame_count / total_time
            
            print(f"적응적 추적 FPS: {fps:.1f}")
            print(f"총 감지 호출 횟수: {mock_detect.call_count}")
            print(f"스킵 효율: {((frame_count - mock_detect.call_count) / frame_count * 100):.1f}%")
            
            # 최소 15fps 이상 달성해야 함
            self.assertGreater(fps, 15, "적응적 추적 성능 미달")
            
            # 스킵 로직으로 인해 감지 호출이 프레임 수보다 적어야 함
            self.assertLess(mock_detect.call_count, frame_count)
    
    def test_tracking_quality_vs_performance_tradeoff(self):
        """추적 품질 vs 성능 트레이드오프 테스트"""
        # 다양한 품질 설정으로 성능 측정
        quality_configs = [
            {'min_detection_confidence': 0.3, 'min_tracking_confidence': 0.3},  # 낮은 품질
            {'min_detection_confidence': 0.5, 'min_tracking_confidence': 0.5},  # 중간 품질
            {'min_detection_confidence': 0.7, 'min_tracking_confidence': 0.7},  # 높은 품질
        ]
        
        results = []
        
        for i, config in enumerate(quality_configs):
            # 새로운 엔진 인스턴스 생성
            engine = MediaPipeFaceEngine()
            
            # MediaPipe 설정 업데이트
            engine.face_mesh = engine.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=config['min_detection_confidence'],
                min_tracking_confidence=config['min_tracking_confidence']
            )
            
            # 성능 측정
            start_time = time.time()
            successful_detections = 0
            
            for _ in range(20):
                result = engine.detect_face(self.sd_frame)
                if result and result.is_valid():
                    successful_detections += 1
            
            avg_time = (time.time() - start_time) / 20
            success_rate = successful_detections / 20
            
            results.append({
                'config': f"품질 레벨 {i+1}",
                'avg_time': avg_time,
                'success_rate': success_rate,
                'fps': 1 / avg_time if avg_time > 0 else 0
            })
            
            print(f"{results[-1]['config']}: {avg_time:.4f}초, "
                  f"성공률: {success_rate:.2%}, FPS: {results[-1]['fps']:.1f}")
        
        # 품질이 높을수록 처리 시간이 길어질 수 있음
        # 하지만 모든 설정에서 최소 성능 기준은 만족해야 함
        for result in results:
            self.assertGreater(result['fps'], 10, f"{result['config']}에서 성능 미달")
    
    def test_frame_rate_consistency(self):
        """프레임 레이트 일관성 테스트"""
        # Mock 스트림으로 일정한 프레임 공급
        frame_times = []
        
        def mock_read_frame():
            frame_times.append(time.time())
            if len(frame_times) <= 30:
                return self.sd_frame
            return None
        
        mock_stream = Mock()
        mock_stream.is_active = True
        mock_stream.read_frame.side_effect = mock_read_frame
        
        with patch.object(self.face_engine, 'detect_face') as mock_detect:
            mock_result = Mock()
            mock_result.is_valid.return_value = True
            mock_result.confidence = 0.8
            mock_result.bbox = BoundingBox(x=220, y=140, width=200, height=200)
            mock_result.landmarks = []
            mock_result.face_regions = {}
            mock_detect.return_value = mock_result
            
            processing_times = []
            
            for face_frame in self.face_engine.track_face(mock_stream):
                processing_times.append(time.time())
                if len(processing_times) >= 20:
                    break
            
            # 프레임 간 시간 간격 계산
            if len(processing_times) > 1:
                intervals = []
                for i in range(1, len(processing_times)):
                    interval = processing_times[i] - processing_times[i-1]
                    intervals.append(interval)
                
                avg_interval = sum(intervals) / len(intervals)
                max_interval = max(intervals)
                min_interval = min(intervals)
                
                print(f"평균 프레임 간격: {avg_interval:.4f}초")
                print(f"최대 간격: {max_interval:.4f}초")
                print(f"최소 간격: {min_interval:.4f}초")
                print(f"간격 편차: {(max_interval - min_interval):.4f}초")
                
                # 프레임 간격의 일관성 검증 (편차가 크지 않아야 함)
                variance = sum((interval - avg_interval) ** 2 for interval in intervals) / len(intervals)
                std_dev = variance ** 0.5
                
                print(f"표준편차: {std_dev:.4f}초")
                
                # 표준편차가 평균의 50% 이하여야 함 (일관성)
                self.assertLess(std_dev, avg_interval * 0.5, "프레임 레이트 일관성 부족")
    
    def test_resource_cleanup_performance(self):
        """리소스 정리 성능 테스트"""
        # 여러 엔진 인스턴스 생성 및 해제
        engines = []
        
        start_time = time.time()
        
        # 10개 엔진 생성
        for _ in range(10):
            engine = MediaPipeFaceEngine()
            engines.append(engine)
        
        creation_time = time.time() - start_time
        
        # 각 엔진으로 감지 수행
        for engine in engines:
            result = engine.detect_face(self.sd_frame)
        
        # 엔진 해제
        start_time = time.time()
        engines.clear()
        cleanup_time = time.time() - start_time
        
        print(f"엔진 생성 시간: {creation_time:.4f}초")
        print(f"리소스 정리 시간: {cleanup_time:.4f}초")
        
        # 리소스 정리가 빠르게 수행되어야 함
        self.assertLess(cleanup_time, 1.0, "리소스 정리 시간 과다")
        self.assertLess(creation_time, 5.0, "엔진 생성 시간 과다")


if __name__ == '__main__':
    print("실시간 얼굴 추적 성능 테스트 시작...")
    print("=" * 50)
    
    # 테스트 실행
    unittest.main(verbosity=2)