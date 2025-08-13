"""
고품질 이미지 처리 및 저장 시스템
메타데이터 포함, 다양한 형식 지원, 품질 향상 알고리즘
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ExifTags
from PIL.ExifTags import TAGS
import base64

from models.core import Point3D, Color


class ImageFormat(Enum):
    """지원하는 이미지 형식"""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    TIFF = "tiff"
    BMP = "bmp"


class QualityLevel(Enum):
    """품질 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class ImageMetadata:
    """이미지 메타데이터"""
    # 기본 정보
    filename: str
    format: str
    width: int
    height: int
    channels: int
    file_size: int
    creation_time: str
    
    # 처리 정보
    applied_effects: List[str]
    processing_time: float
    quality_score: float
    
    # 설정 정보
    makeup_config: Optional[Dict] = None
    surgery_config: Optional[Dict] = None
    
    # 기술적 정보
    color_space: str = "RGB"
    bit_depth: int = 8
    compression_ratio: Optional[float] = None
    
    # 사용자 정의 태그
    custom_tags: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ImageMetadata':
        """딕셔너리에서 생성"""
        return cls(**data)


class ImageEnhancer:
    """이미지 품질 향상 처리기"""
    
    @staticmethod
    def enhance_sharpness(image: np.ndarray, factor: float = 1.2) -> np.ndarray:
        """선명도 향상"""
        try:
            # OpenCV를 사용한 언샤프 마스킹
            gaussian = cv2.GaussianBlur(image, (0, 0), 2.0)
            unsharp_mask = cv2.addWeighted(image, 1.0 + factor, gaussian, -factor, 0)
            return np.clip(unsharp_mask, 0, 255).astype(np.uint8)
        except Exception:
            return image
    
    @staticmethod
    def enhance_contrast(image: np.ndarray, factor: float = 1.1) -> np.ndarray:
        """대비 향상"""
        try:
            # CLAHE (Contrast Limited Adaptive Histogram Equalization)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(clipLimit=factor, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            enhanced = cv2.merge([l, a, b])
            return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        except Exception:
            return image
    
    @staticmethod
    def enhance_color_saturation(image: np.ndarray, factor: float = 1.1) -> np.ndarray:
        """색상 채도 향상"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            
            # 채도 조정
            s = cv2.multiply(s, factor)
            s = np.clip(s, 0, 255).astype(np.uint8)
            
            enhanced_hsv = cv2.merge([h, s, v])
            return cv2.cvtColor(enhanced_hsv, cv2.COLOR_HSV2BGR)
        except Exception:
            return image
    
    @staticmethod
    def reduce_noise(image: np.ndarray, strength: int = 10) -> np.ndarray:
        """노이즈 감소"""
        try:
            # Non-local means denoising
            if len(image.shape) == 3:
                denoised = cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
            else:
                denoised = cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
            return denoised
        except Exception:
            return image
    
    @staticmethod
    def enhance_skin_tone(image: np.ndarray, landmarks: List[Point3D]) -> np.ndarray:
        """피부톤 향상"""
        try:
            # 얼굴 영역 마스크 생성
            mask = ImageEnhancer._create_face_mask(image, landmarks)
            
            # 피부 영역에만 부드러운 필터 적용
            smoothed = cv2.bilateralFilter(image, 15, 80, 80)
            
            # 마스크를 사용해 얼굴 영역만 적용
            result = image.copy()
            mask_3d = cv2.merge([mask, mask, mask]) / 255.0
            result = (result * (1 - mask_3d) + smoothed * mask_3d).astype(np.uint8)
            
            return result
        except Exception:
            return image
    
    @staticmethod
    def _create_face_mask(image: np.ndarray, landmarks: List[Point3D]) -> np.ndarray:
        """얼굴 마스크 생성"""
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        if len(landmarks) >= 468:
            # 얼굴 윤곽 포인트들로 마스크 생성
            face_points = []
            face_indices = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                           397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172]
            
            for idx in face_indices:
                if idx < len(landmarks):
                    point = landmarks[idx]
                    face_points.append([int(point.x), int(point.y)])
            
            if face_points:
                face_points = np.array(face_points, dtype=np.int32)
                cv2.fillPoly(mask, [face_points], 255)
                
                # 마스크 부드럽게 처리
                mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        return mask


class ImageProcessor:
    """고품질 이미지 처리 및 저장 시스템"""
    
    def __init__(self, output_dir: str = "output"):
        """이미지 프로세서 초기화"""
        self.output_dir = output_dir
        self.enhancer = ImageEnhancer()
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "metadata"), exist_ok=True)
        
        # 품질 설정
        self.quality_settings = {
            QualityLevel.LOW: {
                "jpeg_quality": 70,
                "png_compress": 6,
                "webp_quality": 70,
                "enhance_sharpness": False,
                "enhance_contrast": False,
                "reduce_noise": False
            },
            QualityLevel.MEDIUM: {
                "jpeg_quality": 85,
                "png_compress": 3,
                "webp_quality": 85,
                "enhance_sharpness": True,
                "enhance_contrast": False,
                "reduce_noise": False
            },
            QualityLevel.HIGH: {
                "jpeg_quality": 95,
                "png_compress": 1,
                "webp_quality": 95,
                "enhance_sharpness": True,
                "enhance_contrast": True,
                "reduce_noise": True
            },
            QualityLevel.ULTRA: {
                "jpeg_quality": 100,
                "png_compress": 0,
                "webp_quality": 100,
                "enhance_sharpness": True,
                "enhance_contrast": True,
                "reduce_noise": True
            }
        }
    
    def save_image(self, 
                   image: np.ndarray,
                   filename: str,
                   format: ImageFormat = ImageFormat.JPEG,
                   quality: QualityLevel = QualityLevel.HIGH,
                   metadata: Optional[ImageMetadata] = None,
                   enhance_quality: bool = True,
                   landmarks: Optional[List[Point3D]] = None) -> Tuple[bool, str]:
        """
        고품질 이미지 저장
        
        Args:
            image: 저장할 이미지
            filename: 파일명 (확장자 제외)
            format: 이미지 형식
            quality: 품질 레벨
            metadata: 메타데이터
            enhance_quality: 품질 향상 적용 여부
            landmarks: 얼굴 랜드마크 (피부톤 향상용)
            
        Returns:
            (성공 여부, 저장된 파일 경로)
        """
        try:
            start_time = time.time()
            
            # 이미지 품질 향상
            processed_image = image.copy()
            if enhance_quality:
                processed_image = self._enhance_image_quality(
                    processed_image, quality, landmarks
                )
            
            # 파일 경로 생성
            file_extension = self._get_file_extension(format)
            filepath = os.path.join(self.output_dir, f"{filename}.{file_extension}")
            
            # 형식별 저장
            success = self._save_by_format(processed_image, filepath, format, quality)
            
            if success and metadata:
                # 메타데이터 저장
                self._save_metadata(metadata, filename)
            
            processing_time = time.time() - start_time
            
            if success:
                print(f"이미지 저장 완료: {filepath} (처리시간: {processing_time:.3f}초)")
                return True, filepath
            else:
                return False, ""
                
        except Exception as e:
            print(f"이미지 저장 중 오류 발생: {e}")
            return False, ""
    
    def _enhance_image_quality(self, 
                              image: np.ndarray, 
                              quality: QualityLevel,
                              landmarks: Optional[List[Point3D]] = None) -> np.ndarray:
        """이미지 품질 향상"""
        settings = self.quality_settings[quality]
        enhanced_image = image.copy()
        
        try:
            # 노이즈 감소 (가장 먼저)
            if settings.get("reduce_noise", False):
                enhanced_image = self.enhancer.reduce_noise(enhanced_image)
            
            # 피부톤 향상 (얼굴 영역)
            if landmarks and len(landmarks) >= 468:
                enhanced_image = self.enhancer.enhance_skin_tone(enhanced_image, landmarks)
            
            # 대비 향상
            if settings.get("enhance_contrast", False):
                enhanced_image = self.enhancer.enhance_contrast(enhanced_image)
            
            # 색상 채도 향상
            if quality in [QualityLevel.HIGH, QualityLevel.ULTRA]:
                enhanced_image = self.enhancer.enhance_color_saturation(enhanced_image)
            
            # 선명도 향상 (마지막에)
            if settings.get("enhance_sharpness", False):
                enhanced_image = self.enhancer.enhance_sharpness(enhanced_image)
            
            return enhanced_image
            
        except Exception as e:
            print(f"품질 향상 중 오류 발생: {e}")
            return image
    
    def _save_by_format(self, 
                       image: np.ndarray, 
                       filepath: str, 
                       format: ImageFormat, 
                       quality: QualityLevel) -> bool:
        """형식별 이미지 저장"""
        try:
            settings = self.quality_settings[quality]
            
            if format == ImageFormat.JPEG:
                # JPEG 저장
                jpeg_quality = settings["jpeg_quality"]
                cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                
            elif format == ImageFormat.PNG:
                # PNG 저장
                png_compress = settings["png_compress"]
                cv2.imwrite(filepath, image, [cv2.IMWRITE_PNG_COMPRESSION, png_compress])
                
            elif format == ImageFormat.WEBP:
                # WebP 저장
                webp_quality = settings["webp_quality"]
                cv2.imwrite(filepath, image, [cv2.IMWRITE_WEBP_QUALITY, webp_quality])
                
            elif format == ImageFormat.TIFF:
                # TIFF 저장 (무손실)
                cv2.imwrite(filepath, image)
                
            elif format == ImageFormat.BMP:
                # BMP 저장 (무손실)
                cv2.imwrite(filepath, image)
                
            else:
                # 기본값으로 JPEG
                cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            return True
            
        except Exception as e:
            print(f"이미지 저장 실패 ({format.value}): {e}")
            return False
    
    def _get_file_extension(self, format: ImageFormat) -> str:
        """형식별 파일 확장자 반환"""
        extensions = {
            ImageFormat.JPEG: "jpg",
            ImageFormat.PNG: "png",
            ImageFormat.WEBP: "webp",
            ImageFormat.TIFF: "tiff",
            ImageFormat.BMP: "bmp"
        }
        return extensions.get(format, "jpg")
    
    def _save_metadata(self, metadata: ImageMetadata, filename: str):
        """메타데이터 저장"""
        try:
            metadata_path = os.path.join(self.output_dir, "metadata", f"{filename}_metadata.json")
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"메타데이터 저장 실패: {e}")
    
    def load_metadata(self, filename: str) -> Optional[ImageMetadata]:
        """메타데이터 로드"""
        try:
            metadata_path = os.path.join(self.output_dir, "metadata", f"{filename}_metadata.json")
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return ImageMetadata.from_dict(data)
            
            return None
            
        except Exception as e:
            print(f"메타데이터 로드 실패: {e}")
            return None
    
    def create_metadata(self, 
                       image: np.ndarray,
                       filename: str,
                       format: ImageFormat,
                       applied_effects: List[str],
                       processing_time: float,
                       quality_score: float,
                       makeup_config: Optional[Dict] = None,
                       surgery_config: Optional[Dict] = None,
                       custom_tags: Optional[Dict] = None) -> ImageMetadata:
        """메타데이터 생성"""
        
        # 파일 크기 계산 (추정)
        file_size = image.nbytes
        
        return ImageMetadata(
            filename=filename,
            format=format.value,
            width=image.shape[1],
            height=image.shape[0],
            channels=image.shape[2] if len(image.shape) == 3 else 1,
            file_size=file_size,
            creation_time=datetime.now().isoformat(),
            applied_effects=applied_effects,
            processing_time=processing_time,
            quality_score=quality_score,
            makeup_config=makeup_config,
            surgery_config=surgery_config,
            custom_tags=custom_tags or {}
        )
    
    def batch_save(self, 
                   images: List[Tuple[np.ndarray, str]], 
                   format: ImageFormat = ImageFormat.JPEG,
                   quality: QualityLevel = QualityLevel.HIGH) -> List[Tuple[bool, str]]:
        """배치 이미지 저장"""
        results = []
        
        for image, filename in images:
            success, filepath = self.save_image(image, filename, format, quality)
            results.append((success, filepath))
        
        return results
    
    def get_supported_formats(self) -> List[str]:
        """지원하는 형식 목록 반환"""
        return [format.value for format in ImageFormat]
    
    def get_quality_levels(self) -> List[str]:
        """지원하는 품질 레벨 목록 반환"""
        return [level.value for level in QualityLevel]
    
    def estimate_file_size(self, 
                          image: np.ndarray, 
                          format: ImageFormat, 
                          quality: QualityLevel) -> int:
        """예상 파일 크기 계산 (바이트)"""
        try:
            # 임시 파일로 저장해서 크기 측정
            temp_path = os.path.join(self.output_dir, "temp_size_test.tmp")
            
            success = self._save_by_format(image, temp_path, format, quality)
            
            if success and os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                os.remove(temp_path)
                return file_size
            
            return image.nbytes  # 추정값
            
        except Exception:
            return image.nbytes  # 추정값
    
    def compare_formats(self, 
                       image: np.ndarray) -> Dict[str, Dict[str, Union[int, float]]]:
        """다양한 형식별 파일 크기 및 품질 비교"""
        comparison = {}
        
        for format in ImageFormat:
            for quality in QualityLevel:
                try:
                    file_size = self.estimate_file_size(image, format, quality)
                    compression_ratio = file_size / image.nbytes
                    
                    key = f"{format.value}_{quality.value}"
                    comparison[key] = {
                        "file_size": file_size,
                        "compression_ratio": compression_ratio,
                        "format": format.value,
                        "quality": quality.value
                    }
                    
                except Exception:
                    continue
        
        return comparison