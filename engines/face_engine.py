"""
얼굴 처리 엔진 구현
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Iterator, Dict, Tuple
import numpy as np
import cv2
import mediapipe as mp
import time
from models.core import Point3D, FaceAnalysis, BoundingBox, FaceRegion, FaceShape, EyeShape, NoseShape, LipShape, Color


class FaceDetectionResult:
    """얼굴 감지 결과"""
    def __init__(self, bbox: BoundingBox, confidence: float, 
                 landmarks: List[Point3D], face_regions: Dict[str, FaceRegion]):
        self.bbox = bbox
        self.confidence = confidence
        self.landmarks = landmarks
        self.face_regions = face_regions
    
    def is_valid(self) -> bool:
        """유효한 감지 결과인지 확인"""
        return self.confidence > 0.5 and len(self.landmarks) > 0


class FaceFrame:
    """비디오 프레임의 얼굴 정보"""
    def __init__(self, frame: np.ndarray, detection_result: Optional[FaceDetectionResult], 
                 timestamp: float):
        self.frame = frame
        self.detection_result = detection_result
        self.timestamp = timestamp
    
    def has_face(self) -> bool:
        """얼굴이 감지되었는지 확인"""
        return self.detection_result is not None and self.detection_result.is_valid()


class VideoStream:
    """비디오 스트림 추상화"""
    def __init__(self, source: int = 0):
        self.source = source
        self.is_active = False
        self.cap = None
    
    def start(self):
        """스트림 시작"""
        self.cap = cv2.VideoCapture(self.source)
        if self.cap.isOpened():
            self.is_active = True
            # 카메라 설정 최적화
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
        else:
            raise RuntimeError(f"카메라 {self.source}를 열 수 없습니다")
    
    def stop(self):
        """스트림 중지"""
        self.is_active = False
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def read_frame(self) -> Optional[np.ndarray]:
        """프레임 읽기"""
        if not self.is_active or not self.cap:
            return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None
    
    def __del__(self):
        """소멸자에서 리소스 정리"""
        self.stop()


class FaceEngine(ABC):
    """얼굴 처리 엔진 기본 인터페이스"""
    
    @abstractmethod
    def detect_face(self, image: np.ndarray) -> Optional[FaceDetectionResult]:
        """
        이미지에서 얼굴 감지
        
        Args:
            image: 입력 이미지 (numpy array)
            
        Returns:
            FaceDetectionResult 또는 None (얼굴이 감지되지 않은 경우)
        """
        pass
    
    @abstractmethod
    def extract_landmarks(self, image: np.ndarray) -> List[Point3D]:
        """
        얼굴 랜드마크 추출 (468개 3D 포인트)
        
        Args:
            image: 입력 이미지
            
        Returns:
            3D 랜드마크 포인트 리스트
        """
        pass
    
    @abstractmethod
    def analyze_face_structure(self, landmarks: List[Point3D]) -> FaceAnalysis:
        """
        랜드마크를 기반으로 얼굴 구조 분석
        
        Args:
            landmarks: 얼굴 랜드마크 포인트들
            
        Returns:
            얼굴 분석 결과
        """
        pass
    
    @abstractmethod
    def track_face(self, video_stream: VideoStream) -> Iterator[FaceFrame]:
        """
        비디오 스트림에서 실시간 얼굴 추적
        
        Args:
            video_stream: 비디오 스트림
            
        Yields:
            FaceFrame 객체들
        """
        pass
    
    @abstractmethod
    def get_face_regions(self, landmarks: List[Point3D]) -> Dict[str, FaceRegion]:
        """
        랜드마크를 기반으로 얼굴 영역 분할
        
        Args:
            landmarks: 얼굴 랜드마크 포인트들
            
        Returns:
            영역별 FaceRegion 딕셔너리
        """
        pass
    
    def is_face_centered(self, detection_result: FaceDetectionResult, 
                        image_shape: tuple) -> bool:
        """얼굴이 이미지 중앙에 위치하는지 확인"""
        if not detection_result:
            return False
        
        image_center_x = image_shape[1] / 2
        image_center_y = image_shape[0] / 2
        face_center = detection_result.bbox.center
        
        # 중앙에서 20% 이내에 있으면 중앙으로 간주
        threshold_x = image_shape[1] * 0.2
        threshold_y = image_shape[0] * 0.2
        
        return (abs(face_center.x - image_center_x) < threshold_x and 
                abs(face_center.y - image_center_y) < threshold_y)


class MediaPipeFaceEngine(FaceEngine):
    """MediaPipe 기반 얼굴 처리 엔진 구현"""
    
    def __init__(self):
        """MediaPipe 솔루션 초기화"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Face Mesh 초기화 (468개 랜드마크)
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Face Detection 초기화
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )
    
    def detect_face(self, image: np.ndarray) -> Optional[FaceDetectionResult]:
        """이미지에서 얼굴 감지"""
        if image is None or image.size == 0:
            return None
        
        # RGB로 변환 (MediaPipe는 RGB 입력 필요)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 얼굴 감지
        detection_results = self.face_detection.process(rgb_image)
        
        if not detection_results.detections:
            return None
        
        # 첫 번째 얼굴만 처리
        detection = detection_results.detections[0]
        
        # 바운딩 박스 계산
        h, w, _ = image.shape
        bbox_data = detection.location_data.relative_bounding_box
        bbox = BoundingBox(
            x=int(bbox_data.xmin * w),
            y=int(bbox_data.ymin * h),
            width=int(bbox_data.width * w),
            height=int(bbox_data.height * h)
        )
        
        # 랜드마크 추출
        landmarks = self.extract_landmarks(image)
        
        # 얼굴 영역 분할
        face_regions = self.get_face_regions(landmarks) if landmarks else {}
        
        return FaceDetectionResult(
            bbox=bbox,
            confidence=detection.score[0],
            landmarks=landmarks,
            face_regions=face_regions
        )
    
    def extract_landmarks(self, image: np.ndarray) -> List[Point3D]:
        """얼굴 랜드마크 추출 (468개 3D 포인트)"""
        if image is None or image.size == 0:
            return []
        
        # RGB로 변환
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Face Mesh 처리
        results = self.face_mesh.process(rgb_image)
        
        if not results.multi_face_landmarks:
            return []
        
        # 첫 번째 얼굴의 랜드마크만 처리
        face_landmarks = results.multi_face_landmarks[0]
        
        # 이미지 크기
        h, w, _ = image.shape
        
        # 3D 랜드마크 포인트 변환
        landmarks = []
        for landmark in face_landmarks.landmark:
            landmarks.append(Point3D(
                x=landmark.x * w,
                y=landmark.y * h,
                z=landmark.z * w  # z는 상대적 깊이
            ))
        
        return landmarks
    
    def get_face_regions(self, landmarks: List[Point3D]) -> Dict[str, FaceRegion]:
        """랜드마크를 기반으로 얼굴 영역 분할"""
        if not landmarks or len(landmarks) < 468:
            return {}
        
        regions = {}
        
        # MediaPipe Face Mesh 랜드마크 인덱스 정의
        # 왼쪽 눈 영역 (33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246)
        left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        left_eye_points = [landmarks[i] for i in left_eye_indices]
        regions['left_eye'] = self._create_face_region('left_eye', left_eye_points)
        
        # 오른쪽 눈 영역
        right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        right_eye_points = [landmarks[i] for i in right_eye_indices]
        regions['right_eye'] = self._create_face_region('right_eye', right_eye_points)
        
        # 코 영역
        nose_indices = [1, 2, 5, 4, 6, 19, 20, 94, 125, 141, 235, 236, 3, 51, 48, 115, 131, 134, 102, 49, 220, 305, 281, 363, 360, 279]
        nose_points = [landmarks[i] for i in nose_indices]
        regions['nose'] = self._create_face_region('nose', nose_points)
        
        # 입술 영역
        lips_indices = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308]
        lips_points = [landmarks[i] for i in lips_indices]
        regions['lips'] = self._create_face_region('lips', lips_points)
        
        # 얼굴 윤곽
        face_oval_indices = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
        face_oval_points = [landmarks[i] for i in face_oval_indices]
        regions['face_oval'] = self._create_face_region('face_oval', face_oval_points)
        
        return regions
    
    def _create_face_region(self, name: str, points: List[Point3D]) -> FaceRegion:
        """얼굴 영역 객체 생성"""
        if not points:
            return FaceRegion(name, [], Point3D(0, 0, 0), 0.0)
        
        # 중심점 계산
        center_x = sum(p.x for p in points) / len(points)
        center_y = sum(p.y for p in points) / len(points)
        center_z = sum(p.z for p in points) / len(points)
        center = Point3D(center_x, center_y, center_z)
        
        # 면적 계산 (단순화된 방법)
        if len(points) >= 3:
            # 볼록 껍질의 면적 근사치
            x_coords = [p.x for p in points]
            y_coords = [p.y for p in points]
            area = 0.5 * abs(sum(x_coords[i] * y_coords[i+1] - x_coords[i+1] * y_coords[i] 
                                for i in range(-1, len(points)-1)))
        else:
            area = 0.0
        
        return FaceRegion(name, points, center, area)
    
    def analyze_face_structure(self, landmarks: List[Point3D]) -> FaceAnalysis:
        """랜드마크를 기반으로 얼굴 구조 분석"""
        if not landmarks or len(landmarks) < 468:
            # 기본값 반환
            return FaceAnalysis(
                face_shape=FaceShape.OVAL,
                skin_tone=Color(200, 180, 160),  # 기본 피부톤
                eye_shape=EyeShape.ALMOND,
                nose_shape=NoseShape.STRAIGHT,
                lip_shape=LipShape.FULL,
                symmetry_score=0.5
            )
        
        # 얼굴 형태 분석
        face_shape = self._analyze_face_shape(landmarks)
        
        # 눈 형태 분석
        eye_shape = self._analyze_eye_shape(landmarks)
        
        # 코 형태 분석
        nose_shape = self._analyze_nose_shape(landmarks)
        
        # 입술 형태 분석
        lip_shape = self._analyze_lip_shape(landmarks)
        
        # 대칭성 점수 계산
        symmetry_score = self._calculate_symmetry_score(landmarks)
        
        return FaceAnalysis(
            face_shape=face_shape,
            skin_tone=Color(200, 180, 160),  # 실제 구현에서는 이미지에서 추출
            eye_shape=eye_shape,
            nose_shape=nose_shape,
            lip_shape=lip_shape,
            symmetry_score=symmetry_score
        )
    
    def _analyze_face_shape(self, landmarks: List[Point3D]) -> FaceShape:
        """얼굴 형태 분석"""
        # 얼굴 윤곽 주요 포인트들
        forehead_width = abs(landmarks[21].x - landmarks[251].x)
        cheek_width = abs(landmarks[234].x - landmarks[454].x)
        jaw_width = abs(landmarks[172].x - landmarks[397].x)
        face_length = abs(landmarks[10].y - landmarks[152].y)
        
        # 비율 계산
        width_ratio = cheek_width / face_length if face_length > 0 else 1
        jaw_ratio = jaw_width / cheek_width if cheek_width > 0 else 1
        
        # 형태 분류
        if width_ratio > 0.8:
            return FaceShape.ROUND
        elif jaw_ratio > 0.9:
            return FaceShape.SQUARE
        elif width_ratio < 0.6:
            return FaceShape.OBLONG
        else:
            return FaceShape.OVAL
    
    def _analyze_eye_shape(self, landmarks: List[Point3D]) -> EyeShape:
        """눈 형태 분석"""
        # 왼쪽 눈 분석 (간단한 구현)
        eye_width = abs(landmarks[33].x - landmarks[133].x)
        eye_height = abs(landmarks[159].y - landmarks[145].y)
        
        height_ratio = eye_height / eye_width if eye_width > 0 else 0.5
        
        if height_ratio > 0.6:
            return EyeShape.ROUND
        elif height_ratio < 0.3:
            return EyeShape.MONOLID
        else:
            return EyeShape.ALMOND
    
    def _analyze_nose_shape(self, landmarks: List[Point3D]) -> NoseShape:
        """코 형태 분석"""
        # 코의 직선성 분석
        nose_tip = landmarks[1]
        nose_bridge_top = landmarks[6]
        nose_bridge_mid = landmarks[5]
        
        # 직선성 계산 (간단한 구현)
        return NoseShape.STRAIGHT  # 기본값
    
    def _analyze_lip_shape(self, landmarks: List[Point3D]) -> LipShape:
        """입술 형태 분석"""
        # 입술 너비와 높이
        lip_width = abs(landmarks[61].x - landmarks[291].x)
        lip_height = abs(landmarks[13].y - landmarks[14].y)
        
        height_ratio = lip_height / lip_width if lip_width > 0 else 0.3
        
        if height_ratio > 0.4:
            return LipShape.FULL
        elif height_ratio < 0.2:
            return LipShape.THIN
        else:
            return LipShape.FULL
    
    def _calculate_symmetry_score(self, landmarks: List[Point3D]) -> float:
        """대칭성 점수 계산"""
        # 얼굴 중심선 계산
        face_center_x = (landmarks[10].x + landmarks[152].x) / 2
        
        # 좌우 대칭 포인트들의 거리 차이 계산
        symmetry_pairs = [
            (33, 362),    # 눈 모서리
            (61, 291),    # 입 모서리
            (234, 454),   # 볼
        ]
        
        total_asymmetry = 0
        for left_idx, right_idx in symmetry_pairs:
            left_point = landmarks[left_idx]
            right_point = landmarks[right_idx]
            
            # 중심선으로부터의 거리 차이
            left_distance = abs(left_point.x - face_center_x)
            right_distance = abs(right_point.x - face_center_x)
            asymmetry = abs(left_distance - right_distance)
            total_asymmetry += asymmetry
        
        # 정규화 (0~1 범위)
        max_asymmetry = 50.0  # 최대 비대칭 기준값
        symmetry_score = max(0, 1 - (total_asymmetry / max_asymmetry))
        
        return min(1.0, symmetry_score)
    
    def track_face(self, video_stream: VideoStream) -> Iterator[FaceFrame]:
        """
        비디오 스트림에서 실시간 얼굴 추적
        
        향상된 기능:
        - 적응적 프레임 스킵 로직으로 성능 최적화
        - 얼굴 손실 시 지능적 재감지 메커니즘
        - 추적 품질 기반 동적 처리 조정
        - 안정성 검증 및 노이즈 필터링
        
        Args:
            video_stream: 비디오 스트림
            
        Yields:
            FaceFrame 객체들
        """
        if not video_stream.is_active:
            return
        
        frame_count = 0
        start_time = time.time()
        last_detection_result = None
        detection_skip_counter = 0
        
        # 동적 프레임 스킵 설정
        adaptive_skip_config = {
            'base_skip_frames': 2,      # 기본 스킵 프레임 수
            'max_skip_frames': 8,       # 최대 스킵 프레임 수
            'current_skip_frames': 2,   # 현재 스킵 프레임 수
            'performance_threshold': 0.033,  # 30fps 기준 (33ms)
            'quality_threshold': 0.7    # 품질 기준점
        }
        
        # 향상된 추적 상태 관리
        tracking_state = {
            'is_tracking': False,
            'lost_frames': 0,
            'max_lost_frames': 15,      # 더 관대한 손실 허용
            'consecutive_detections': 0,
            'min_consecutive_detections': 3,  # 안정적 추적을 위한 최소 연속 감지
            'last_bbox': None,
            'bbox_history': [],         # 바운딩 박스 히스토리 (안정성 검증용)
            'stability_counter': 0,
            'min_stability_frames': 5,
            'tracking_confidence': 0.0,
            'search_region_expansion': 1.0,  # 재감지 시 검색 영역 확장 비율
            'last_successful_frame': None
        }
        
        # 성능 모니터링
        performance_stats = {
            'frame_times': [],
            'avg_processing_time': 0.0,
            'fps_counter': 0,
            'last_fps_time': time.time()
        }
        
        while video_stream.is_active:
            frame_start_time = time.time()
            
            # 프레임 읽기
            frame = video_stream.read_frame()
            if frame is None:
                continue
            
            current_time = time.time()
            timestamp = current_time - start_time
            detection_result = None
            
            # 적응적 감지 전략 결정
            should_detect = self._should_perform_detection(
                detection_skip_counter, 
                adaptive_skip_config, 
                tracking_state,
                performance_stats
            )
            
            if should_detect:
                # 전체 얼굴 감지 또는 영역 기반 재감지 수행
                if tracking_state['is_tracking'] and tracking_state['last_bbox']:
                    # 추적 중일 때는 ROI 기반 감지로 성능 향상
                    detection_result = self._detect_in_roi(frame, tracking_state['last_bbox'])
                else:
                    # 전체 프레임 감지
                    detection_result = self.detect_face(frame)
                
                detection_skip_counter = 0
                
                # 감지 결과 처리
                self._process_detection_result(
                    detection_result, tracking_state, frame.shape
                )
                
                if detection_result and detection_result.is_valid():
                    last_detection_result = detection_result
                    tracking_state['last_successful_frame'] = frame_count
                
            else:
                # 프레임 스킵 - 이전 결과 기반 추정
                detection_result = self._estimate_face_position(
                    last_detection_result, tracking_state, frame_count
                )
                detection_skip_counter += 1
            
            # 추적 손실 감지 및 복구 시도
            if tracking_state['lost_frames'] > tracking_state['max_lost_frames'] // 2:
                detection_result = self._attempt_face_recovery(
                    frame, tracking_state, last_detection_result
                )
            
            # 추적 품질 평가 및 동적 조정
            tracking_quality = self._evaluate_tracking_quality(
                detection_result, tracking_state, frame.shape
            )
            
            # 성능 기반 적응적 조정
            self._adapt_performance_settings(
                adaptive_skip_config, tracking_quality, performance_stats
            )
            
            # FaceFrame 객체 생성 및 메타데이터 추가
            face_frame = FaceFrame(
                frame=frame,
                detection_result=detection_result,
                timestamp=timestamp
            )
            
            # 확장된 추적 메타데이터
            face_frame.tracking_quality = tracking_quality
            face_frame.is_stable = (
                tracking_state['stability_counter'] >= tracking_state['min_stability_frames'] and
                tracking_state['consecutive_detections'] >= tracking_state['min_consecutive_detections']
            )
            face_frame.frame_number = frame_count
            face_frame.tracking_confidence = tracking_state['tracking_confidence']
            face_frame.is_tracking = tracking_state['is_tracking']
            face_frame.lost_frames = tracking_state['lost_frames']
            face_frame.skip_frames_used = adaptive_skip_config['current_skip_frames']
            
            yield face_frame
            
            frame_count += 1
            
            # 성능 통계 업데이트
            frame_processing_time = time.time() - frame_start_time
            self._update_performance_stats(performance_stats, frame_processing_time)
            
            # 적응적 FPS 제어
            self._control_frame_rate(
                tracking_state, performance_stats, frame_start_time
            )
    
    def _evaluate_tracking_quality(self, detection_result: Optional[FaceDetectionResult], 
                                 tracking_state: dict, frame_shape: tuple) -> float:
        """
        추적 품질 평가
        
        Args:
            detection_result: 현재 감지 결과
            tracking_state: 추적 상태 정보
            frame_shape: 프레임 크기
            
        Returns:
            품질 점수 (0.0 ~ 1.0)
        """
        if not detection_result or not detection_result.is_valid():
            return 0.0
        
        quality_score = detection_result.confidence
        
        # 안정성 보너스
        if tracking_state['stability_counter'] >= tracking_state['min_stability_frames']:
            quality_score += 0.1
        
        # 중앙 위치 보너스
        if self.is_face_centered(detection_result, frame_shape):
            quality_score += 0.1
        
        # 크기 적절성 평가
        face_area = detection_result.bbox.width * detection_result.bbox.height
        frame_area = frame_shape[0] * frame_shape[1]
        face_ratio = face_area / frame_area
        
        if 0.1 <= face_ratio <= 0.4:  # 적절한 얼굴 크기
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _should_perform_detection(self, detection_skip_counter: int, 
                                adaptive_skip_config: dict, tracking_state: dict,
                                performance_stats: dict) -> bool:
        """
        적응적 감지 전략 결정
        
        Args:
            detection_skip_counter: 현재 스킵 카운터
            adaptive_skip_config: 적응적 스킵 설정
            tracking_state: 추적 상태
            performance_stats: 성능 통계
            
        Returns:
            감지를 수행할지 여부
        """
        # 기본 조건들
        if detection_skip_counter >= adaptive_skip_config['current_skip_frames']:
            return True
        
        if not tracking_state['is_tracking']:
            return True
        
        if tracking_state['lost_frames'] > 0:
            return True
        
        # 성능 기반 조건
        if performance_stats['avg_processing_time'] > adaptive_skip_config['performance_threshold']:
            # 성능이 떨어지면 더 많이 스킵
            return detection_skip_counter >= adaptive_skip_config['current_skip_frames'] * 1.5
        
        # 품질 기반 조건
        if tracking_state['tracking_confidence'] < adaptive_skip_config['quality_threshold']:
            # 품질이 낮으면 더 자주 감지
            return detection_skip_counter >= max(1, adaptive_skip_config['current_skip_frames'] // 2)
        
        return False
    
    def _detect_in_roi(self, frame: np.ndarray, last_bbox: BoundingBox) -> Optional[FaceDetectionResult]:
        """
        ROI(Region of Interest) 기반 얼굴 감지로 성능 최적화
        
        Args:
            frame: 입력 프레임
            last_bbox: 이전 바운딩 박스
            
        Returns:
            감지 결과 또는 None
        """
        if not last_bbox:
            return self.detect_face(frame)
        
        # ROI 영역 확장 (움직임 허용)
        expansion_factor = 1.3
        h, w = frame.shape[:2]
        
        # 확장된 ROI 계산
        roi_x = max(0, int(last_bbox.x - last_bbox.width * (expansion_factor - 1) / 2))
        roi_y = max(0, int(last_bbox.y - last_bbox.height * (expansion_factor - 1) / 2))
        roi_w = min(w - roi_x, int(last_bbox.width * expansion_factor))
        roi_h = min(h - roi_y, int(last_bbox.height * expansion_factor))
        
        # ROI 추출
        roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        
        if roi_frame.size == 0:
            return self.detect_face(frame)
        
        # ROI에서 얼굴 감지
        roi_result = self.detect_face(roi_frame)
        
        if roi_result and roi_result.is_valid():
            # 좌표를 전체 프레임 기준으로 변환
            adjusted_bbox = BoundingBox(
                x=roi_result.bbox.x + roi_x,
                y=roi_result.bbox.y + roi_y,
                width=roi_result.bbox.width,
                height=roi_result.bbox.height
            )
            
            # 랜드마크 좌표도 조정
            adjusted_landmarks = []
            for landmark in roi_result.landmarks:
                adjusted_landmarks.append(Point3D(
                    x=landmark.x + roi_x,
                    y=landmark.y + roi_y,
                    z=landmark.z
                ))
            
            return FaceDetectionResult(
                bbox=adjusted_bbox,
                confidence=roi_result.confidence,
                landmarks=adjusted_landmarks,
                face_regions=self.get_face_regions(adjusted_landmarks)
            )
        
        # ROI에서 감지 실패 시 전체 프레임에서 재시도
        return self.detect_face(frame)
    
    def _process_detection_result(self, detection_result: Optional[FaceDetectionResult],
                                tracking_state: dict, frame_shape: tuple) -> None:
        """
        감지 결과 처리 및 추적 상태 업데이트
        
        Args:
            detection_result: 감지 결과
            tracking_state: 추적 상태 (수정됨)
            frame_shape: 프레임 크기
        """
        if detection_result and detection_result.is_valid():
            # 성공적인 감지
            tracking_state['consecutive_detections'] += 1
            tracking_state['lost_frames'] = 0
            tracking_state['last_bbox'] = detection_result.bbox
            tracking_state['tracking_confidence'] = detection_result.confidence
            
            # 바운딩 박스 히스토리 업데이트 (안정성 검증용)
            tracking_state['bbox_history'].append(detection_result.bbox)
            if len(tracking_state['bbox_history']) > 5:
                tracking_state['bbox_history'].pop(0)
            
            # 안정성 검증
            if self._is_tracking_stable(tracking_state['bbox_history']):
                tracking_state['stability_counter'] += 1
                tracking_state['is_tracking'] = True
            else:
                tracking_state['stability_counter'] = max(0, tracking_state['stability_counter'] - 1)
            
            # 검색 영역 축소 (성공적 추적 시)
            tracking_state['search_region_expansion'] = max(1.0, 
                tracking_state['search_region_expansion'] - 0.1)
        
        else:
            # 감지 실패
            tracking_state['lost_frames'] += 1
            tracking_state['consecutive_detections'] = 0
            tracking_state['tracking_confidence'] *= 0.9  # 신뢰도 감소
            
            # 검색 영역 확대 (추적 실패 시)
            tracking_state['search_region_expansion'] = min(2.0,
                tracking_state['search_region_expansion'] + 0.2)
            
            # 장기간 추적 실패 시 추적 상태 리셋
            if tracking_state['lost_frames'] > tracking_state['max_lost_frames']:
                tracking_state['is_tracking'] = False
                tracking_state['stability_counter'] = 0
                tracking_state['bbox_history'].clear()
    
    def _is_tracking_stable(self, bbox_history: List[BoundingBox]) -> bool:
        """
        바운딩 박스 히스토리를 기반으로 추적 안정성 검증
        
        Args:
            bbox_history: 바운딩 박스 히스토리
            
        Returns:
            추적이 안정적인지 여부
        """
        if len(bbox_history) < 3:
            return False
        
        # 최근 3개 바운딩 박스의 변화량 계산
        recent_boxes = bbox_history[-3:]
        
        total_movement = 0
        for i in range(1, len(recent_boxes)):
            prev_center = recent_boxes[i-1].center
            curr_center = recent_boxes[i].center
            
            movement = ((curr_center.x - prev_center.x) ** 2 + 
                       (curr_center.y - prev_center.y) ** 2) ** 0.5
            total_movement += movement
        
        # 평균 이동량이 임계값 이하면 안정적
        avg_movement = total_movement / (len(recent_boxes) - 1)
        stability_threshold = 10.0  # 픽셀 단위
        
        return avg_movement < stability_threshold
    
    def _estimate_face_position(self, last_detection_result: Optional[FaceDetectionResult],
                              tracking_state: dict, frame_count: int) -> Optional[FaceDetectionResult]:
        """
        이전 결과를 기반으로 얼굴 위치 추정 (프레임 스킵 시 사용)
        
        Args:
            last_detection_result: 마지막 감지 결과
            tracking_state: 추적 상태
            frame_count: 현재 프레임 번호
            
        Returns:
            추정된 감지 결과 또는 None
        """
        if not last_detection_result or not tracking_state['is_tracking']:
            return None
        
        # 신뢰도 감소 (시간이 지날수록)
        frames_since_detection = frame_count - (tracking_state['last_successful_frame'] or frame_count)
        confidence_decay = max(0.3, last_detection_result.confidence - frames_since_detection * 0.05)
        
        # 위치 추정 (단순한 선형 예측)
        estimated_bbox = last_detection_result.bbox
        
        # 바운딩 박스 히스토리가 있으면 움직임 예측
        if len(tracking_state['bbox_history']) >= 2:
            prev_bbox = tracking_state['bbox_history'][-2]
            curr_bbox = tracking_state['bbox_history'][-1]
            
            # 움직임 벡터 계산
            dx = curr_bbox.center.x - prev_bbox.center.x
            dy = curr_bbox.center.y - prev_bbox.center.y
            
            # 다음 위치 예측 (보수적으로)
            predicted_x = curr_bbox.x + dx * 0.5
            predicted_y = curr_bbox.y + dy * 0.5
            
            estimated_bbox = BoundingBox(
                x=int(predicted_x),
                y=int(predicted_y),
                width=curr_bbox.width,
                height=curr_bbox.height
            )
        
        # 추정 결과 생성
        return FaceDetectionResult(
            bbox=estimated_bbox,
            confidence=confidence_decay,
            landmarks=last_detection_result.landmarks,  # 랜드마크는 그대로 유지
            face_regions=last_detection_result.face_regions
        )
    
    def _attempt_face_recovery(self, frame: np.ndarray, tracking_state: dict,
                             last_detection_result: Optional[FaceDetectionResult]) -> Optional[FaceDetectionResult]:
        """
        얼굴 손실 시 재감지 메커니즘
        
        Args:
            frame: 현재 프레임
            tracking_state: 추적 상태
            last_detection_result: 마지막 감지 결과
            
        Returns:
            감지 결과 또는 None
        """
        # 얼굴이 완전히 손실된 경우 전체 프레임 검색
        if tracking_state['lost_frames'] > tracking_state['max_lost_frames']:
            return self.detect_face(frame)
        
        # 마지막 감지 위치 주변에서 확장된 영역 검색
        if last_detection_result and tracking_state['last_bbox']:
            # 검색 영역 확장 (손실 시간에 따라 점점 확장)
            expansion = tracking_state['search_region_expansion']
            h, w = frame.shape[:2]
            last_bbox = tracking_state['last_bbox']
            
            # 확장된 ROI 계산
            roi_x = max(0, int(last_bbox.x - last_bbox.width * (expansion - 1)))
            roi_y = max(0, int(last_bbox.y - last_bbox.height * (expansion - 1)))
            roi_w = min(w - roi_x, int(last_bbox.width * expansion * 2))
            roi_h = min(h - roi_y, int(last_bbox.height * expansion * 2))
            
            # 확장된 ROI가 너무 크면 전체 프레임 검색
            if roi_w > w * 0.8 or roi_h > h * 0.8:
                return self.detect_face(frame)
            
            # 확장된 ROI 추출
            roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            
            if roi_frame.size == 0:
                return self.detect_face(frame)
            
            # 확장된 ROI에서 얼굴 감지
            roi_result = self.detect_face(roi_frame)
            
            if roi_result and roi_result.is_valid():
                # 좌표를 전체 프레임 기준으로 변환
                adjusted_bbox = BoundingBox(
                    x=roi_result.bbox.x + roi_x,
                    y=roi_result.bbox.y + roi_y,
                    width=roi_result.bbox.width,
                    height=roi_result.bbox.height
                )
                
                # 랜드마크 좌표도 조정
                adjusted_landmarks = []
                for landmark in roi_result.landmarks:
                    adjusted_landmarks.append(Point3D(
                        x=landmark.x + roi_x,
                        y=landmark.y + roi_y,
                        z=landmark.z
                    ))
                
                return FaceDetectionResult(
                    bbox=adjusted_bbox,
                    confidence=roi_result.confidence,
                    landmarks=adjusted_landmarks,
                    face_regions=self.get_face_regions(adjusted_landmarks)
                )
        
        # 모든 시도 실패 시 전체 프레임 검색
        return self.detect_face(frame)
    
    def _update_performance_stats(self, performance_stats: dict, frame_time: float) -> None:
        """
        성능 통계 업데이트
        
        Args:
            performance_stats: 성능 통계 (수정됨)
            frame_time: 프레임 처리 시간
        """
        # 프레임 시간 기록 (최근 10개만 유지)
        performance_stats['frame_times'].append(frame_time)
        if len(performance_stats['frame_times']) > 10:
            performance_stats['frame_times'].pop(0)
        
        # 평균 처리 시간 계산
        if performance_stats['frame_times']:
            performance_stats['avg_processing_time'] = sum(performance_stats['frame_times']) / len(performance_stats['frame_times'])
        
        # FPS 계산 (1초마다 업데이트)
        current_time = time.time()
        performance_stats['fps_counter'] += 1
        
        if current_time - performance_stats['last_fps_time'] >= 1.0:
            fps = performance_stats['fps_counter'] / (current_time - performance_stats['last_fps_time'])
            performance_stats['fps'] = fps
            performance_stats['fps_counter'] = 0
            performance_stats['last_fps_time'] = current_time
    
    def _adapt_performance_settings(self, adaptive_skip_config: dict, 
                                  tracking_quality: float, performance_stats: dict) -> None:
        """
        성능 기반 적응적 설정 조정
        
        Args:
            adaptive_skip_config: 적응적 스킵 설정 (수정됨)
            tracking_quality: 추적 품질 점수
            performance_stats: 성능 통계
        """
        # 성능이 좋지 않으면 스킵 프레임 증가
        if performance_stats['avg_processing_time'] > adaptive_skip_config['performance_threshold'] * 1.2:
            adaptive_skip_config['current_skip_frames'] = min(
                adaptive_skip_config['max_skip_frames'],
                adaptive_skip_config['current_skip_frames'] + 1
            )
        
        # 성능이 좋고 품질이 낮으면 스킵 프레임 감소
        elif (performance_stats['avg_processing_time'] < adaptive_skip_config['performance_threshold'] * 0.8 and
              tracking_quality < adaptive_skip_config['quality_threshold']):
            adaptive_skip_config['current_skip_frames'] = max(
                1,
                adaptive_skip_config['current_skip_frames'] - 1
            )
        
        # 성능과 품질이 모두 좋으면 기본값 유지
        elif (performance_stats['avg_processing_time'] < adaptive_skip_config['performance_threshold'] and
              tracking_quality > adaptive_skip_config['quality_threshold']):
            adaptive_skip_config['current_skip_frames'] = adaptive_skip_config['base_skip_frames']
    
    def _control_frame_rate(self, tracking_state: dict, performance_stats: dict, 
                          frame_start_time: float) -> None:
        """
        적응적 FPS 제어
        
        Args:
            tracking_state: 추적 상태
            performance_stats: 성능 통계
            frame_start_time: 프레임 처리 시작 시간
        """
        # 목표 프레임 시간 (30fps = 33.3ms)
        target_frame_time = 0.033
        
        # 현재 프레임 처리 시간
        elapsed = time.time() - frame_start_time
        
        # 추적 상태에 따른 목표 FPS 조정
        if not tracking_state['is_tracking'] or tracking_state['lost_frames'] > 0:
            # 추적 손실 시 더 빠른 프레임 레이트 (지연 없음)
            return
        
        # 처리가 너무 빠르면 약간의 지연 추가
        if elapsed < target_frame_time:
            sleep_time = target_frame_time - elapsed
            time.sleep(sleep_time * 0.5)  # 완전한 지연은 피하기 위해 절반만 적용