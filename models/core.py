"""
핵심 데이터 모델 클래스 정의
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np


@dataclass
class Point3D:
    """3D 좌표점을 나타내는 클래스"""
    x: float
    y: float
    z: float = 0.0
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
    
    def to_2d(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Color:
    """RGBA 색상을 나타내는 클래스"""
    r: int
    g: int
    b: int
    a: int = 255
    
    def __post_init__(self):
        # 색상 값 범위 검증
        for value in [self.r, self.g, self.b, self.a]:
            if not 0 <= value <= 255:
                raise ValueError("색상 값은 0-255 범위여야 합니다")
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.a)
    
    def to_rgb(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)


@dataclass
class BoundingBox:
    """경계 상자를 나타내는 클래스"""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def x2(self) -> int:
        return self.x + self.width
    
    @property
    def y2(self) -> int:
        return self.y + self.height
    
    @property
    def center(self) -> Point3D:
        return Point3D(
            x=self.x + self.width / 2,
            y=self.y + self.height / 2
        )


@dataclass
class FaceRegion:
    """얼굴 영역을 나타내는 클래스"""
    name: str
    points: List[Point3D]
    center: Point3D
    area: float
    
    def get_bounding_box(self) -> BoundingBox:
        """영역의 경계 상자 계산"""
        if not self.points:
            return BoundingBox(0, 0, 0, 0)
        
        x_coords = [p.x for p in self.points]
        y_coords = [p.y for p in self.points]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        return BoundingBox(
            x=int(min_x),
            y=int(min_y),
            width=int(max_x - min_x),
            height=int(max_y - min_y)
        )


class FaceShape(Enum):
    """얼굴 형태 열거형"""
    OVAL = "oval"
    ROUND = "round"
    SQUARE = "square"
    HEART = "heart"
    DIAMOND = "diamond"
    OBLONG = "oblong"


class EyeShape(Enum):
    """눈 형태 열거형"""
    ALMOND = "almond"
    ROUND = "round"
    MONOLID = "monolid"
    HOODED = "hooded"
    UPTURNED = "upturned"
    DOWNTURNED = "downturned"


class NoseShape(Enum):
    """코 형태 열거형"""
    STRAIGHT = "straight"
    ROMAN = "roman"
    BUTTON = "button"
    HAWK = "hawk"
    SNUB = "snub"
    CROOKED = "crooked"


class LipShape(Enum):
    """입술 형태 열거형"""
    FULL = "full"
    THIN = "thin"
    WIDE = "wide"
    SMALL = "small"
    HEART = "heart"
    ROUND = "round"


@dataclass
class FaceAnalysis:
    """얼굴 분석 결과를 나타내는 클래스"""
    face_shape: FaceShape
    skin_tone: Color
    eye_shape: EyeShape
    nose_shape: NoseShape
    lip_shape: LipShape
    symmetry_score: float  # 0.0 ~ 1.0
    
    def __post_init__(self):
        if not 0.0 <= self.symmetry_score <= 1.0:
            raise ValueError("대칭성 점수는 0.0-1.0 범위여야 합니다")


@dataclass
class Vector3D:
    """3D 벡터를 나타내는 클래스"""
    x: float
    y: float
    z: float
    
    def magnitude(self) -> float:
        """벡터의 크기 계산"""
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Vector3D':
        """벡터 정규화"""
        mag = self.magnitude()
        if mag == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x/mag, self.y/mag, self.z/mag)