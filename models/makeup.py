"""
메이크업 관련 데이터 모델
"""
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum
from .core import Color


class BlendMode(Enum):
    """색상 블렌딩 모드"""
    NORMAL = "normal"
    MULTIPLY = "multiply"
    OVERLAY = "overlay"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"


class EyeshadowStyle(Enum):
    """아이섀도 스타일"""
    NATURAL = "natural"
    SMOKY = "smoky"
    CUT_CREASE = "cut_crease"
    HALO = "halo"
    GRADIENT = "gradient"


@dataclass
class LipstickConfig:
    """립스틱 설정"""
    color: Color
    intensity: float  # 0.0 ~ 1.0
    glossiness: float  # 0.0 ~ 1.0 (매트 ~ 글로시)
    blend_mode: BlendMode = BlendMode.NORMAL
    
    def __post_init__(self):
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("강도는 0.0-1.0 범위여야 합니다")
        if not 0.0 <= self.glossiness <= 1.0:
            raise ValueError("광택도는 0.0-1.0 범위여야 합니다")


@dataclass
class EyeshadowConfig:
    """아이섀도 설정"""
    colors: List[Color]
    style: EyeshadowStyle
    intensity: float  # 0.0 ~ 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    shimmer: float = 0.0  # 0.0 ~ 1.0 (매트 ~ 시머)
    
    def __post_init__(self):
        if not self.colors:
            raise ValueError("최소 하나의 색상이 필요합니다")
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("강도는 0.0-1.0 범위여야 합니다")
        if not 0.0 <= self.shimmer <= 1.0:
            raise ValueError("시머는 0.0-1.0 범위여야 합니다")


@dataclass
class BlushConfig:
    """블러셔 설정"""
    color: Color
    intensity: float  # 0.0 ~ 1.0
    placement: str = "cheeks"  # cheeks, temples, nose
    blend_mode: BlendMode = BlendMode.NORMAL
    
    def __post_init__(self):
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("강도는 0.0-1.0 범위여야 합니다")


@dataclass
class FoundationConfig:
    """파운데이션 설정"""
    color: Color
    coverage: float  # 0.0 ~ 1.0 (자연스러움 ~ 풀커버리지)
    finish: str = "natural"  # natural, matte, dewy
    
    def __post_init__(self):
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError("커버리지는 0.0-1.0 범위여야 합니다")


@dataclass
class EyelinerConfig:
    """아이라이너 설정"""
    color: Color
    thickness: float  # 0.0 ~ 1.0
    style: str = "natural"  # natural, winged, dramatic
    intensity: float = 1.0
    
    def __post_init__(self):
        if not 0.0 <= self.thickness <= 1.0:
            raise ValueError("두께는 0.0-1.0 범위여야 합니다")
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("강도는 0.0-1.0 범위여야 합니다")


@dataclass
class MakeupConfig:
    """전체 메이크업 설정"""
    lipstick: LipstickConfig
    eyeshadow: EyeshadowConfig
    blush: BlushConfig
    foundation: FoundationConfig
    eyeliner: EyelinerConfig
    
    def get_total_intensity(self) -> float:
        """전체 메이크업 강도 계산"""
        intensities = [
            self.lipstick.intensity,
            self.eyeshadow.intensity,
            self.blush.intensity,
            self.foundation.coverage,
            self.eyeliner.intensity
        ]
        return sum(intensities) / len(intensities)


@dataclass
class MakeupStyle:
    """메이크업 스타일 프리셋"""
    name: str
    description: str
    config: MakeupConfig
    tags: List[str]  # natural, dramatic, evening, etc.
    
    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("스타일 이름은 필수입니다")