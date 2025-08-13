"""
실시간 효과 업데이트 시스템
개별 효과 수정 시 전체 업데이트 로직, 효과 우선순위 및 레이어링 시스템
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any, Set
import numpy as np
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
import copy

from models.core import Point3D, Color
from models.makeup import MakeupConfig
from models.surgery import SurgeryConfig
from engines.integrated_engine import IntegratedEngine, IntegratedConfig, IntegratedResult


class UpdateType(Enum):
    """업데이트 타입"""
    INCREMENTAL = "incremental"  # 증분 업데이트
    FULL_REFRESH = "full_refresh"  # 전체 새로고침
    SELECTIVE = "selective"      # 선택적 업데이트


class EffectLayer(Enum):
    """효과 레이어 (적용 순서)"""
    BASE = 0           # 기본 레이어 (원본 이미지)
    SURGERY_SHAPE = 1  # 성형 - 형태 변경
    SURGERY_DETAIL = 2 # 성형 - 세부 조정
    MAKEUP_BASE = 3    # 메이크업 - 베이스 (파운데이션)
    MAKEUP_COLOR = 4   # 메이크업 - 색상 (블러셔, 아이섀도)
    MAKEUP_ACCENT = 5  # 메이크업 - 강조 (립스틱, 아이라이너)
    FINAL = 6          # 최종 처리


@dataclass
class EffectState:
    """개별 효과 상태"""
    effect_id: str
    layer: EffectLayer
    config: Any
    result_image: Optional[np.ndarray] = None
    modified_landmarks: Optional[List[Point3D]] = None
    is_dirty: bool = True  # 업데이트 필요 여부
    dependencies: Set[str] = field(default_factory=set)  # 의존성 효과들
    last_update_time: float = 0.0
    processing_time: float = 0.0


@dataclass
class UpdateRequest:
    """업데이트 요청"""
    effect_id: str
    new_config: Any
    update_type: UpdateType = UpdateType.INCREMENTAL
    priority: int = 0  # 높을수록 우선순위 높음
    timestamp: float = field(default_factory=time.time)


class EffectDependencyGraph:
    """효과 의존성 그래프"""
    
    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
    
    def add_dependency(self, effect_id: str, depends_on: str):
        """의존성 추가"""
        if effect_id not in self.dependencies:
            self.dependencies[effect_id] = set()
        if depends_on not in self.reverse_dependencies:
            self.reverse_dependencies[depends_on] = set()
        
        self.dependencies[effect_id].add(depends_on)
        self.reverse_dependencies[depends_on].add(effect_id)
    
    def remove_dependency(self, effect_id: str, depends_on: str):
        """의존성 제거"""
        if effect_id in self.dependencies:
            self.dependencies[effect_id].discard(depends_on)
        if depends_on in self.reverse_dependencies:
            self.reverse_dependencies[depends_on].discard(effect_id)
    
    def get_dependencies(self, effect_id: str) -> Set[str]:
        """특정 효과의 의존성 조회"""
        return self.dependencies.get(effect_id, set())
    
    def get_dependents(self, effect_id: str) -> Set[str]:
        """특정 효과에 의존하는 효과들 조회"""
        return self.reverse_dependencies.get(effect_id, set())
    
    def get_update_order(self, effect_ids: Set[str]) -> List[str]:
        """업데이트 순서 계산 (위상 정렬)"""
        # 간단한 위상 정렬 구현
        in_degree = {}
        for effect_id in effect_ids:
            in_degree[effect_id] = len(self.get_dependencies(effect_id) & effect_ids)
        
        result = []
        queue = [effect_id for effect_id in effect_ids if in_degree[effect_id] == 0]
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for dependent in self.get_dependents(current):
                if dependent in effect_ids:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        return result


class PerformanceOptimizer:
    """성능 최적화 관리자"""
    
    def __init__(self):
        self.frame_skip_threshold = 30.0  # ms
        self.quality_levels = {
            'high': 1.0,
            'medium': 0.7,
            'low': 0.5
        }
        self.current_quality = 'high'
        self.processing_times: List[float] = []
        self.max_history = 10
    
    def record_processing_time(self, processing_time: float):
        """처리 시간 기록"""
        self.processing_times.append(processing_time * 1000)  # ms로 변환
        if len(self.processing_times) > self.max_history:
            self.processing_times.pop(0)
    
    def should_skip_frame(self) -> bool:
        """프레임 스킵 여부 결정"""
        if not self.processing_times:
            return False
        
        avg_time = np.mean(self.processing_times)
        return avg_time > self.frame_skip_threshold
    
    def adjust_quality(self) -> str:
        """품질 자동 조정"""
        if not self.processing_times:
            return self.current_quality
        
        avg_time = np.mean(self.processing_times)
        
        if avg_time > 50.0:  # 50ms 이상
            self.current_quality = 'low'
        elif avg_time > 30.0:  # 30ms 이상
            self.current_quality = 'medium'
        else:
            self.current_quality = 'high'
        
        return self.current_quality
    
    def get_quality_scale(self) -> float:
        """현재 품질 스케일 반환"""
        return self.quality_levels.get(self.current_quality, 1.0)


class RealtimeUpdateEngine:
    """실시간 효과 업데이트 엔진"""
    
    def __init__(self):
        """실시간 업데이트 엔진 초기화"""
        self.integrated_engine = IntegratedEngine()
        self.effect_states: Dict[str, EffectState] = {}
        self.dependency_graph = EffectDependencyGraph()
        self.performance_optimizer = PerformanceOptimizer()
        
        # 업데이트 큐 및 스레딩
        self.update_queue: List[UpdateRequest] = []
        self.update_lock = threading.Lock()
        self.is_processing = False
        
        # 캐시된 결과
        self.base_image: Optional[np.ndarray] = None
        self.base_landmarks: Optional[List[Point3D]] = None
        self.final_result: Optional[IntegratedResult] = None
        
        # 기본 의존성 설정
        self._setup_default_dependencies()
    
    def _setup_default_dependencies(self):
        """기본 효과 의존성 설정"""
        # 성형 효과들 간의 의존성
        self.dependency_graph.add_dependency("eye_surgery", "face_shape")
        self.dependency_graph.add_dependency("nose_surgery", "face_shape")
        self.dependency_graph.add_dependency("jawline_surgery", "face_shape")
        self.dependency_graph.add_dependency("cheekbone_surgery", "face_shape")
        
        # 메이크업 효과들의 의존성
        self.dependency_graph.add_dependency("eyeshadow", "foundation")
        self.dependency_graph.add_dependency("eyeliner", "eyeshadow")
        self.dependency_graph.add_dependency("lipstick", "foundation")
        self.dependency_graph.add_dependency("blush", "foundation")
        
        # 성형과 메이크업 간의 의존성
        self.dependency_graph.add_dependency("eyeshadow", "eye_surgery")
        self.dependency_graph.add_dependency("lipstick", "jawline_surgery")
        self.dependency_graph.add_dependency("blush", "cheekbone_surgery")
    
    def initialize_effects(self, 
                          base_image: np.ndarray, 
                          base_landmarks: List[Point3D],
                          integrated_config: IntegratedConfig):
        """효과 초기화"""
        self.base_image = base_image.copy()
        self.base_landmarks = base_landmarks.copy()
        
        # 개별 효과 상태 초기화
        self._initialize_effect_states(integrated_config)
        
        # 전체 효과 적용
        self._perform_full_update()
    
    def _initialize_effect_states(self, config: IntegratedConfig):
        """효과 상태 초기화"""
        self.effect_states.clear()
        
        # 성형 효과들
        if config.surgery_config:
            if config.surgery_config.nose:
                self.effect_states["nose_surgery"] = EffectState(
                    effect_id="nose_surgery",
                    layer=EffectLayer.SURGERY_SHAPE,
                    config=config.surgery_config.nose
                )
            
            if config.surgery_config.eyes:
                self.effect_states["eye_surgery"] = EffectState(
                    effect_id="eye_surgery",
                    layer=EffectLayer.SURGERY_SHAPE,
                    config=config.surgery_config.eyes
                )
            
            if config.surgery_config.jawline:
                self.effect_states["jawline_surgery"] = EffectState(
                    effect_id="jawline_surgery",
                    layer=EffectLayer.SURGERY_SHAPE,
                    config=config.surgery_config.jawline
                )
            
            if config.surgery_config.cheekbones:
                self.effect_states["cheekbone_surgery"] = EffectState(
                    effect_id="cheekbone_surgery",
                    layer=EffectLayer.SURGERY_SHAPE,
                    config=config.surgery_config.cheekbones
                )
        
        # 메이크업 효과들
        if config.makeup_config:
            if config.makeup_config.foundation:
                self.effect_states["foundation"] = EffectState(
                    effect_id="foundation",
                    layer=EffectLayer.MAKEUP_BASE,
                    config=config.makeup_config.foundation
                )
            
            if config.makeup_config.eyeshadow:
                self.effect_states["eyeshadow"] = EffectState(
                    effect_id="eyeshadow",
                    layer=EffectLayer.MAKEUP_COLOR,
                    config=config.makeup_config.eyeshadow
                )
            
            if config.makeup_config.blush:
                self.effect_states["blush"] = EffectState(
                    effect_id="blush",
                    layer=EffectLayer.MAKEUP_COLOR,
                    config=config.makeup_config.blush
                )
            
            if config.makeup_config.lipstick:
                self.effect_states["lipstick"] = EffectState(
                    effect_id="lipstick",
                    layer=EffectLayer.MAKEUP_ACCENT,
                    config=config.makeup_config.lipstick
                )
            
            if config.makeup_config.eyeliner:
                self.effect_states["eyeliner"] = EffectState(
                    effect_id="eyeliner",
                    layer=EffectLayer.MAKEUP_ACCENT,
                    config=config.makeup_config.eyeliner
                )
    
    def update_effect(self, 
                     effect_id: str, 
                     new_config: Any, 
                     update_type: UpdateType = UpdateType.INCREMENTAL) -> bool:
        """개별 효과 업데이트"""
        with self.update_lock:
            # 업데이트 요청을 큐에 추가
            request = UpdateRequest(
                effect_id=effect_id,
                new_config=new_config,
                update_type=update_type
            )
            
            self.update_queue.append(request)
            self.update_queue.sort(key=lambda x: (-x.priority, x.timestamp))
        
        # 비동기 처리
        if not self.is_processing:
            return self._process_update_queue()
        
        return True
    
    def _process_update_queue(self) -> bool:
        """업데이트 큐 처리"""
        self.is_processing = True
        
        try:
            while self.update_queue:
                with self.update_lock:
                    if not self.update_queue:
                        break
                    request = self.update_queue.pop(0)
                
                self._apply_single_update(request)
            
            return True
            
        except Exception as e:
            print(f"업데이트 처리 중 오류 발생: {e}")
            return False
        
        finally:
            self.is_processing = False
    
    def _apply_single_update(self, request: UpdateRequest):
        """단일 업데이트 적용"""
        start_time = time.time()
        
        # 효과 상태 업데이트
        if request.effect_id in self.effect_states:
            effect_state = self.effect_states[request.effect_id]
            effect_state.config = request.new_config
            effect_state.is_dirty = True
            effect_state.last_update_time = start_time
        
        # 의존성이 있는 효과들도 더티 마킹
        dependents = self.dependency_graph.get_dependents(request.effect_id)
        for dependent_id in dependents:
            if dependent_id in self.effect_states:
                self.effect_states[dependent_id].is_dirty = True
        
        # 업데이트 타입에 따른 처리
        if request.update_type == UpdateType.FULL_REFRESH:
            self._perform_full_update()
        elif request.update_type == UpdateType.INCREMENTAL:
            self._perform_incremental_update(request.effect_id)
        elif request.update_type == UpdateType.SELECTIVE:
            self._perform_selective_update({request.effect_id} | dependents)
        
        processing_time = time.time() - start_time
        self.performance_optimizer.record_processing_time(processing_time)
        
        if request.effect_id in self.effect_states:
            self.effect_states[request.effect_id].processing_time = processing_time
    
    def _perform_full_update(self):
        """전체 업데이트 수행"""
        if not self.base_image or not self.base_landmarks:
            return
        
        # 모든 효과를 레이어 순서대로 적용
        current_image = self.base_image.copy()
        current_landmarks = self.base_landmarks.copy()
        
        # 레이어별로 정렬
        effects_by_layer = {}
        for effect_id, effect_state in self.effect_states.items():
            layer = effect_state.layer
            if layer not in effects_by_layer:
                effects_by_layer[layer] = []
            effects_by_layer[layer].append((effect_id, effect_state))
        
        # 레이어 순서대로 적용
        for layer in sorted(effects_by_layer.keys(), key=lambda x: x.value):
            for effect_id, effect_state in effects_by_layer[layer]:
                current_image, current_landmarks = self._apply_effect(
                    effect_id, effect_state, current_image, current_landmarks
                )
                effect_state.is_dirty = False
        
        # 최종 결과 업데이트
        self._update_final_result(current_image, current_landmarks)
    
    def _perform_incremental_update(self, changed_effect_id: str):
        """증분 업데이트 수행"""
        # 변경된 효과와 그에 의존하는 효과들만 업데이트
        affected_effects = {changed_effect_id}
        affected_effects.update(self.dependency_graph.get_dependents(changed_effect_id))
        
        self._perform_selective_update(affected_effects)
    
    def _perform_selective_update(self, effect_ids: Set[str]):
        """선택적 업데이트 수행"""
        if not self.base_image or not self.base_landmarks:
            return
        
        # 업데이트 순서 계산
        update_order = self.dependency_graph.get_update_order(effect_ids)
        
        # 기존 결과에서 시작
        current_image = self.final_result.final_image.copy() if self.final_result else self.base_image.copy()
        current_landmarks = self.final_result.modified_landmarks.copy() if self.final_result else self.base_landmarks.copy()
        
        # 선택된 효과들만 재적용
        for effect_id in update_order:
            if effect_id in self.effect_states:
                effect_state = self.effect_states[effect_id]
                if effect_state.is_dirty:
                    current_image, current_landmarks = self._apply_effect(
                        effect_id, effect_state, current_image, current_landmarks
                    )
                    effect_state.is_dirty = False
        
        # 최종 결과 업데이트
        self._update_final_result(current_image, current_landmarks)
    
    def _apply_effect(self, 
                     effect_id: str, 
                     effect_state: EffectState,
                     input_image: np.ndarray,
                     input_landmarks: List[Point3D]) -> Tuple[np.ndarray, List[Point3D]]:
        """개별 효과 적용"""
        try:
            # 성능 최적화 적용
            quality_scale = self.performance_optimizer.get_quality_scale()
            
            if quality_scale < 1.0:
                # 품질을 낮춰서 처리 속도 향상
                h, w = input_image.shape[:2]
                new_h, new_w = int(h * quality_scale), int(w * quality_scale)
                scaled_image = cv2.resize(input_image, (new_w, new_h))
                
                # 랜드마크도 스케일링
                scaled_landmarks = []
                for landmark in input_landmarks:
                    scaled_landmarks.append(Point3D(
                        landmark.x * quality_scale,
                        landmark.y * quality_scale,
                        landmark.z
                    ))
            else:
                scaled_image = input_image
                scaled_landmarks = input_landmarks
            
            # 효과 타입에 따른 처리
            if "surgery" in effect_id:
                result_image, result_landmarks = self._apply_surgery_effect(
                    effect_id, effect_state.config, scaled_image, scaled_landmarks
                )
            else:
                result_image, result_landmarks = self._apply_makeup_effect(
                    effect_id, effect_state.config, scaled_image, scaled_landmarks
                )
            
            # 스케일링된 경우 원래 크기로 복원
            if quality_scale < 1.0:
                h, w = input_image.shape[:2]
                result_image = cv2.resize(result_image, (w, h))
                
                # 랜드마크도 원래 스케일로 복원
                restored_landmarks = []
                for landmark in result_landmarks:
                    restored_landmarks.append(Point3D(
                        landmark.x / quality_scale,
                        landmark.y / quality_scale,
                        landmark.z
                    ))
                result_landmarks = restored_landmarks
            
            # 결과 캐싱
            effect_state.result_image = result_image.copy()
            effect_state.modified_landmarks = result_landmarks.copy()
            
            return result_image, result_landmarks
            
        except Exception as e:
            print(f"효과 적용 중 오류 발생 ({effect_id}): {e}")
            return input_image, input_landmarks
    
    def _apply_surgery_effect(self, 
                            effect_id: str, 
                            config: Any,
                            image: np.ndarray,
                            landmarks: List[Point3D]) -> Tuple[np.ndarray, List[Point3D]]:
        """성형 효과 적용"""
        if effect_id == "nose_surgery":
            result_image = self.integrated_engine.surgery_engine.modify_nose(image, landmarks, config)
        elif effect_id == "eye_surgery":
            result_image = self.integrated_engine.surgery_engine.modify_eyes(image, landmarks, config)
        elif effect_id == "jawline_surgery":
            result_image = self.integrated_engine.surgery_engine.modify_jawline(image, landmarks, config)
        elif effect_id == "cheekbone_surgery":
            result_image = self.integrated_engine.surgery_engine.modify_cheekbones(image, landmarks, config)
        else:
            result_image = image
        
        return result_image, landmarks  # 성형은 랜드마크도 변경될 수 있음
    
    def _apply_makeup_effect(self, 
                           effect_id: str, 
                           config: Any,
                           image: np.ndarray,
                           landmarks: List[Point3D]) -> Tuple[np.ndarray, List[Point3D]]:
        """메이크업 효과 적용"""
        if effect_id == "foundation":
            result_image = self.integrated_engine.makeup_engine.apply_foundation(image, landmarks, config)
        elif effect_id == "eyeshadow":
            result_image = self.integrated_engine.makeup_engine.apply_eyeshadow(image, landmarks, config)
        elif effect_id == "blush":
            result_image = self.integrated_engine.makeup_engine.apply_blush(image, landmarks, config)
        elif effect_id == "lipstick":
            result_image = self.integrated_engine.makeup_engine.apply_lipstick(image, landmarks, config)
        elif effect_id == "eyeliner":
            result_image = self.integrated_engine.makeup_engine.apply_eyeliner(image, landmarks, config)
        else:
            result_image = image
        
        return result_image, landmarks  # 메이크업은 랜드마크 변경 없음
    
    def _update_final_result(self, final_image: np.ndarray, final_landmarks: List[Point3D]):
        """최종 결과 업데이트"""
        applied_effects = [effect_id for effect_id, state in self.effect_states.items() 
                          if not state.is_dirty and state.result_image is not None]
        
        total_processing_time = sum(state.processing_time for state in self.effect_states.values())
        
        self.final_result = IntegratedResult(
            final_image=final_image,
            modified_landmarks=final_landmarks,
            makeup_result=None,  # 개별 결과는 별도 관리
            surgery_result=None,
            applied_effects=applied_effects,
            processing_time=total_processing_time,
            quality_score=0.8,  # 간단한 품질 점수
            conflicts_detected=[]
        )
    
    def get_current_result(self) -> Optional[IntegratedResult]:
        """현재 결과 조회"""
        return self.final_result
    
    def get_effect_state(self, effect_id: str) -> Optional[EffectState]:
        """효과 상태 조회"""
        return self.effect_states.get(effect_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        return {
            "current_quality": self.performance_optimizer.current_quality,
            "average_processing_time": np.mean(self.performance_optimizer.processing_times) if self.performance_optimizer.processing_times else 0,
            "should_skip_frame": self.performance_optimizer.should_skip_frame(),
            "active_effects": len([s for s in self.effect_states.values() if not s.is_dirty]),
            "pending_updates": len(self.update_queue)
        }
    
    def reset(self):
        """엔진 리셋"""
        with self.update_lock:
            self.effect_states.clear()
            self.update_queue.clear()
            self.base_image = None
            self.base_landmarks = None
            self.final_result = None
            self.is_processing = False