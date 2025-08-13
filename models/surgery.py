"""
성형 시뮬레이션 관련 데이터 모델
"""
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum
from .core import Vector3D


class FeatureType(Enum):
    """성형 가능한 얼굴 특징 타입"""
    NOSE = "nose"
    EYES = "eyes"
    JAWLINE = "jawline"
    CHEEKBONES = "cheekbones"
    LIPS = "lips"
    FOREHEAD = "forehead"
    CHIN = "chin"


class ModificationType(Enum):
    """변형 타입"""
    ENLARGE = "enlarge"
    REDUCE = "reduce"
    LIFT = "lift"
    NARROW = "narrow"
    WIDEN = "widen"
    STRAIGHTEN = "straighten"
    CURVE = "curve"


@dataclass
class FeatureModification:
    """특징 변형 정보"""
    feature_type: FeatureType
    modification_type: ModificationType
    modification_vector: Vector3D
    intensity: float  # 0.0 ~ 1.0
    natural_limit: float  # 자연스러운 변형 한계
    
    def __post_init__(self):
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("강도는 0.0-1.0 범위여야 합니다")
        if not 0.0 <= self.natural_limit <= 1.0:
            raise ValueError("자연스러운 한계는 0.0-1.0 범위여야 합니다")
    
    def is_within_natural_limit(self) -> bool:
        """자연스러운 범위 내인지 확인"""
        return self.intensity <= self.natural_limit


@dataclass
class NoseConfig:
    """코 성형 설정"""
    height_adjustment: float = 0.0  # -1.0 ~ 1.0
    width_adjustment: float = 0.0   # -1.0 ~ 1.0
    tip_adjustment: float = 0.0     # -1.0 ~ 1.0
    bridge_adjustment: float = 0.0  # -1.0 ~ 1.0
    
    def __post_init__(self):
        adjustments = [
            self.height_adjustment, self.width_adjustment,
            self.tip_adjustment, self.bridge_adjustment
        ]
        for adj in adjustments:
            if not -1.0 <= adj <= 1.0:
                raise ValueError("조정값은 -1.0에서 1.0 범위여야 합니다")


@dataclass
class EyeConfig:
    """눈 성형 설정"""
    size_adjustment: float = 0.0      # -1.0 ~ 1.0
    shape_adjustment: float = 0.0     # -1.0 ~ 1.0 (둥글게 ~ 날카롭게)
    position_adjustment: float = 0.0  # -1.0 ~ 1.0 (가깝게 ~ 멀게)
    angle_adjustment: float = 0.0     # -1.0 ~ 1.0 (처짐 ~ 올라감)
    
    def __post_init__(self):
        adjustments = [
            self.size_adjustment, self.shape_adjustment,
            self.position_adjustment, self.angle_adjustment
        ]
        for adj in adjustments:
            if not -1.0 <= adj <= 1.0:
                raise ValueError("조정값은 -1.0에서 1.0 범위여야 합니다")


@dataclass
class JawlineConfig:
    """턱선 성형 설정"""
    width_adjustment: float = 0.0     # -1.0 ~ 1.0
    angle_adjustment: float = 0.0     # -1.0 ~ 1.0
    length_adjustment: float = 0.0    # -1.0 ~ 1.0
    
    def __post_init__(self):
        adjustments = [
            self.width_adjustment, self.angle_adjustment, self.length_adjustment
        ]
        for adj in adjustments:
            if not -1.0 <= adj <= 1.0:
                raise ValueError("조정값은 -1.0에서 1.0 범위여야 합니다")


@dataclass
class CheekboneConfig:
    """광대 성형 설정"""
    height_adjustment: float = 0.0    # -1.0 ~ 1.0
    width_adjustment: float = 0.0     # -1.0 ~ 1.0
    prominence_adjustment: float = 0.0 # -1.0 ~ 1.0
    
    def __post_init__(self):
        adjustments = [
            self.height_adjustment, self.width_adjustment, self.prominence_adjustment
        ]
        for adj in adjustments:
            if not -1.0 <= adj <= 1.0:
                raise ValueError("조정값은 -1.0에서 1.0 범위여야 합니다")


@dataclass
class SurgeryConfig:
    """전체 성형 설정"""
    nose: NoseConfig
    eyes: EyeConfig
    jawline: JawlineConfig
    cheekbones: CheekboneConfig
    
    def get_total_modification_intensity(self) -> float:
        """전체 변형 강도 계산"""
        nose_intensity = abs(self.nose.height_adjustment) + abs(self.nose.width_adjustment)
        eye_intensity = abs(self.eyes.size_adjustment) + abs(self.eyes.shape_adjustment)
        jaw_intensity = abs(self.jawline.width_adjustment) + abs(self.jawline.angle_adjustment)
        cheek_intensity = abs(self.cheekbones.height_adjustment) + abs(self.cheekbones.width_adjustment)
        
        return (nose_intensity + eye_intensity + jaw_intensity + cheek_intensity) / 8.0


@dataclass
class SurgeryPreset:
    """성형 프리셋"""
    name: str
    description: str
    config: SurgeryConfig
    tags: List[str]  # subtle, dramatic, korean-style, etc.
    natural_score: float  # 0.0 ~ 1.0 (자연스러움 점수)
    
    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("프리셋 이름은 필수입니다")
        if not 0.0 <= self.natural_score <= 1.0:
            raise ValueError("자연스러움 점수는 0.0-1.0 범위여야 합니다")