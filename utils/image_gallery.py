"""
이미지 비교 및 갤러리 시스템
원본-수정본 나란히 비교, 여러 스타일 갤러리, 메타데이터 관리
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
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

from utils.image_processor import ImageProcessor, ImageMetadata, ImageFormat, QualityLevel


class ComparisonMode(Enum):
    """비교 모드"""
    SIDE_BY_SIDE = "side_by_side"      # 나란히 비교
    OVERLAY = "overlay"                # 오버레이 비교
    DIFFERENCE = "difference"          # 차이점 강조
    SPLIT_VIEW = "split_view"          # 분할 뷰


class GalleryLayout(Enum):
    """갤러리 레이아웃"""
    GRID = "grid"                      # 격자 레이아웃
    LIST = "list"                      # 리스트 레이아웃
    CAROUSEL = "carousel"              # 캐러셀 레이아웃
    TIMELINE = "timeline"              # 타임라인 레이아웃


@dataclass
class ComparisonResult:
    """비교 결과"""
    original_path: str
    modified_path: str
    comparison_image: np.ndarray
    similarity_score: float
    difference_regions: List[Tuple[int, int, int, int]]  # (x, y, w, h)
    comparison_mode: ComparisonMode
    metadata: Dict[str, Any]


@dataclass
class GalleryItem:
    """갤러리 아이템"""
    id: str
    name: str
    image_path: str
    thumbnail_path: str
    metadata: ImageMetadata
    tags: List[str]
    creation_time: datetime
    last_modified: datetime
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "image_path": self.image_path,
            "thumbnail_path": self.thumbnail_path,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "tags": self.tags,
            "creation_time": self.creation_time.isoformat(),
            "last_modified": self.last_modified.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GalleryItem':
        """딕셔너리에서 생성"""
        return cls(
            id=data["id"],
            name=data["name"],
            image_path=data["image_path"],
            thumbnail_path=data["thumbnail_path"],
            metadata=ImageMetadata.from_dict(data["metadata"]) if data["metadata"] else None,
            tags=data["tags"],
            creation_time=datetime.fromisoformat(data["creation_time"]),
            last_modified=datetime.fromisoformat(data["last_modified"])
        )


class ImageComparator:
    """이미지 비교 도구"""
    
    @staticmethod
    def calculate_similarity(image1: np.ndarray, image2: np.ndarray) -> float:
        """이미지 유사도 계산 (SSIM 기반)"""
        try:
            # 그레이스케일 변환
            if len(image1.shape) == 3:
                gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
            else:
                gray1 = image1
            
            if len(image2.shape) == 3:
                gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
            else:
                gray2 = image2
            
            # 크기 맞추기
            if gray1.shape != gray2.shape:
                gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
            
            # 간단한 SSIM 계산
            mean1 = np.mean(gray1)
            mean2 = np.mean(gray2)
            var1 = np.var(gray1)
            var2 = np.var(gray2)
            cov = np.mean((gray1 - mean1) * (gray2 - mean2))
            
            c1 = 0.01 ** 2
            c2 = 0.03 ** 2
            
            ssim = ((2 * mean1 * mean2 + c1) * (2 * cov + c2)) / \
                   ((mean1 ** 2 + mean2 ** 2 + c1) * (var1 + var2 + c2))
            
            return max(0.0, min(1.0, ssim))
            
        except Exception:
            return 0.0
    
    @staticmethod
    def find_difference_regions(image1: np.ndarray, image2: np.ndarray, 
                               threshold: int = 30) -> List[Tuple[int, int, int, int]]:
        """차이점 영역 찾기"""
        try:
            # 크기 맞추기
            if image1.shape != image2.shape:
                image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
            
            # 차이 계산
            diff = cv2.absdiff(image1, image2)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # 임계값 적용
            _, thresh = cv2.threshold(gray_diff, threshold, 255, cv2.THRESH_BINARY)
            
            # 윤곽선 찾기
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 경계 상자 계산
            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 10 and h > 10:  # 너무 작은 영역 제외
                    regions.append((x, y, w, h))
            
            return regions
            
        except Exception:
            return []
    
    @staticmethod
    def create_side_by_side_comparison(image1: np.ndarray, image2: np.ndarray,
                                     title1: str = "Original", 
                                     title2: str = "Modified") -> np.ndarray:
        """나란히 비교 이미지 생성"""
        try:
            # 크기 맞추기
            h1, w1 = image1.shape[:2]
            h2, w2 = image2.shape[:2]
            
            # 높이를 맞춤
            target_height = max(h1, h2)
            if h1 != target_height:
                image1 = cv2.resize(image1, (int(w1 * target_height / h1), target_height))
            if h2 != target_height:
                image2 = cv2.resize(image2, (int(w2 * target_height / h2), target_height))
            
            # 나란히 배치
            combined = np.hstack([image1, image2])
            
            # 제목 추가
            combined_with_title = ImageComparator._add_titles(
                combined, [title1, title2], [image1.shape[1], image2.shape[1]]
            )
            
            return combined_with_title
            
        except Exception:
            return np.hstack([image1, image2])
    
    @staticmethod
    def create_overlay_comparison(image1: np.ndarray, image2: np.ndarray,
                                alpha: float = 0.5) -> np.ndarray:
        """오버레이 비교 이미지 생성"""
        try:
            # 크기 맞추기
            if image1.shape != image2.shape:
                image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
            
            # 오버레이
            overlay = cv2.addWeighted(image1, 1 - alpha, image2, alpha, 0)
            return overlay
            
        except Exception:
            return image1
    
    @staticmethod
    def create_difference_visualization(image1: np.ndarray, image2: np.ndarray) -> np.ndarray:
        """차이점 시각화 이미지 생성"""
        try:
            # 크기 맞추기
            if image1.shape != image2.shape:
                image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
            
            # 차이 계산
            diff = cv2.absdiff(image1, image2)
            
            # 차이점 강조
            enhanced_diff = cv2.multiply(diff, 3)  # 차이를 3배로 강조
            enhanced_diff = np.clip(enhanced_diff, 0, 255).astype(np.uint8)
            
            # 차이점 영역 표시
            regions = ImageComparator.find_difference_regions(image1, image2)
            result = image1.copy()
            
            for x, y, w, h in regions:
                cv2.rectangle(result, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            return result
            
        except Exception:
            return image1
    
    @staticmethod
    def create_split_view(image1: np.ndarray, image2: np.ndarray, 
                         split_ratio: float = 0.5) -> np.ndarray:
        """분할 뷰 생성"""
        try:
            # 크기 맞추기
            if image1.shape != image2.shape:
                image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
            
            h, w = image1.shape[:2]
            split_x = int(w * split_ratio)
            
            # 분할 이미지 생성
            result = image1.copy()
            result[:, split_x:] = image2[:, split_x:]
            
            # 분할선 그리기
            cv2.line(result, (split_x, 0), (split_x, h), (255, 255, 255), 2)
            
            return result
            
        except Exception:
            return image1
    
    @staticmethod
    def _add_titles(image: np.ndarray, titles: List[str], 
                   widths: List[int]) -> np.ndarray:
        """이미지에 제목 추가"""
        try:
            # PIL로 변환
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            
            # 폰트 설정 (기본 폰트 사용)
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # 제목 추가
            y_offset = 10
            x_offset = 0
            
            for title, width in zip(titles, widths):
                text_x = x_offset + width // 2
                draw.text((text_x, y_offset), title, fill=(255, 255, 255), 
                         font=font, anchor="mt")
                x_offset += width
            
            # OpenCV 형식으로 변환
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
        except Exception:
            return image


class ImageGallery:
    """이미지 갤러리 시스템"""
    
    def __init__(self, gallery_dir: str = "gallery"):
        """갤러리 초기화"""
        self.gallery_dir = gallery_dir
        self.thumbnails_dir = os.path.join(gallery_dir, "thumbnails")
        self.metadata_file = os.path.join(gallery_dir, "gallery_metadata.json")
        
        # 디렉토리 생성
        os.makedirs(gallery_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)
        
        self.image_processor = ImageProcessor(output_dir=gallery_dir)
        self.comparator = ImageComparator()
        
        # 갤러리 아이템 로드
        self.items: Dict[str, GalleryItem] = {}
        self._load_gallery_metadata()
    
    def add_image(self, 
                  image: np.ndarray,
                  name: str,
                  metadata: Optional[ImageMetadata] = None,
                  tags: Optional[List[str]] = None) -> str:
        """갤러리에 이미지 추가"""
        try:
            # 고유 ID 생성
            item_id = f"{name}_{int(time.time())}"
            
            # 이미지 저장
            success, image_path = self.image_processor.save_image(
                image, item_id, ImageFormat.JPEG, QualityLevel.HIGH, metadata
            )
            
            if not success:
                return ""
            
            # 썸네일 생성
            thumbnail_path = self._create_thumbnail(image, item_id)
            
            # 갤러리 아이템 생성
            gallery_item = GalleryItem(
                id=item_id,
                name=name,
                image_path=image_path,
                thumbnail_path=thumbnail_path,
                metadata=metadata,
                tags=tags or [],
                creation_time=datetime.now(),
                last_modified=datetime.now()
            )
            
            # 갤러리에 추가
            self.items[item_id] = gallery_item
            self._save_gallery_metadata()
            
            return item_id
            
        except Exception as e:
            print(f"갤러리 이미지 추가 실패: {e}")
            return ""
    
    def _create_thumbnail(self, image: np.ndarray, item_id: str, 
                         size: Tuple[int, int] = (200, 200)) -> str:
        """썸네일 생성"""
        try:
            # 썸네일 크기로 리사이즈
            h, w = image.shape[:2]
            aspect_ratio = w / h
            
            if aspect_ratio > 1:  # 가로가 더 긴 경우
                new_w = size[0]
                new_h = int(size[0] / aspect_ratio)
            else:  # 세로가 더 긴 경우
                new_h = size[1]
                new_w = int(size[1] * aspect_ratio)
            
            thumbnail = cv2.resize(image, (new_w, new_h))
            
            # 정사각형 배경에 중앙 배치
            background = np.ones((size[1], size[0], 3), dtype=np.uint8) * 128
            
            y_offset = (size[1] - new_h) // 2
            x_offset = (size[0] - new_w) // 2
            
            background[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = thumbnail
            
            # 썸네일 저장
            thumbnail_path = os.path.join(self.thumbnails_dir, f"{item_id}_thumb.jpg")
            cv2.imwrite(thumbnail_path, background)
            
            return thumbnail_path
            
        except Exception as e:
            print(f"썸네일 생성 실패: {e}")
            return ""
    
    def remove_image(self, item_id: str) -> bool:
        """갤러리에서 이미지 제거"""
        try:
            if item_id not in self.items:
                return False
            
            item = self.items[item_id]
            
            # 파일 삭제
            if os.path.exists(item.image_path):
                os.remove(item.image_path)
            if os.path.exists(item.thumbnail_path):
                os.remove(item.thumbnail_path)
            
            # 갤러리에서 제거
            del self.items[item_id]
            self._save_gallery_metadata()
            
            return True
            
        except Exception as e:
            print(f"이미지 제거 실패: {e}")
            return False
    
    def get_image(self, item_id: str) -> Optional[np.ndarray]:
        """이미지 로드"""
        try:
            if item_id not in self.items:
                return None
            
            item = self.items[item_id]
            if os.path.exists(item.image_path):
                return cv2.imread(item.image_path)
            
            return None
            
        except Exception:
            return None
    
    def get_thumbnail(self, item_id: str) -> Optional[np.ndarray]:
        """썸네일 로드"""
        try:
            if item_id not in self.items:
                return None
            
            item = self.items[item_id]
            if os.path.exists(item.thumbnail_path):
                return cv2.imread(item.thumbnail_path)
            
            return None
            
        except Exception:
            return None
    
    def search_images(self, 
                     query: str = "",
                     tags: Optional[List[str]] = None,
                     date_range: Optional[Tuple[datetime, datetime]] = None) -> List[GalleryItem]:
        """이미지 검색"""
        results = []
        
        for item in self.items.values():
            # 이름으로 검색
            if query and query.lower() not in item.name.lower():
                continue
            
            # 태그로 검색
            if tags and not any(tag in item.tags for tag in tags):
                continue
            
            # 날짜 범위로 검색
            if date_range:
                start_date, end_date = date_range
                if not (start_date <= item.creation_time <= end_date):
                    continue
            
            results.append(item)
        
        # 최신순으로 정렬
        results.sort(key=lambda x: x.creation_time, reverse=True)
        return results
    
    def create_comparison(self, 
                         item_id1: str, 
                         item_id2: str,
                         mode: ComparisonMode = ComparisonMode.SIDE_BY_SIDE) -> Optional[ComparisonResult]:
        """이미지 비교 생성"""
        try:
            image1 = self.get_image(item_id1)
            image2 = self.get_image(item_id2)
            
            if image1 is None or image2 is None:
                return None
            
            item1 = self.items[item_id1]
            item2 = self.items[item_id2]
            
            # 유사도 계산
            similarity = self.comparator.calculate_similarity(image1, image2)
            
            # 차이점 영역 찾기
            diff_regions = self.comparator.find_difference_regions(image1, image2)
            
            # 비교 이미지 생성
            if mode == ComparisonMode.SIDE_BY_SIDE:
                comparison_image = self.comparator.create_side_by_side_comparison(
                    image1, image2, item1.name, item2.name
                )
            elif mode == ComparisonMode.OVERLAY:
                comparison_image = self.comparator.create_overlay_comparison(image1, image2)
            elif mode == ComparisonMode.DIFFERENCE:
                comparison_image = self.comparator.create_difference_visualization(image1, image2)
            elif mode == ComparisonMode.SPLIT_VIEW:
                comparison_image = self.comparator.create_split_view(image1, image2)
            else:
                comparison_image = self.comparator.create_side_by_side_comparison(image1, image2)
            
            return ComparisonResult(
                original_path=item1.image_path,
                modified_path=item2.image_path,
                comparison_image=comparison_image,
                similarity_score=similarity,
                difference_regions=diff_regions,
                comparison_mode=mode,
                metadata={
                    "item1": item1.to_dict(),
                    "item2": item2.to_dict(),
                    "comparison_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            print(f"이미지 비교 생성 실패: {e}")
            return None
    
    def create_gallery_view(self, 
                           items: List[GalleryItem],
                           layout: GalleryLayout = GalleryLayout.GRID,
                           cols: int = 4) -> Optional[np.ndarray]:
        """갤러리 뷰 생성"""
        try:
            if not items:
                return None
            
            if layout == GalleryLayout.GRID:
                return self._create_grid_layout(items, cols)
            elif layout == GalleryLayout.LIST:
                return self._create_list_layout(items)
            else:
                return self._create_grid_layout(items, cols)
            
        except Exception as e:
            print(f"갤러리 뷰 생성 실패: {e}")
            return None
    
    def _create_grid_layout(self, items: List[GalleryItem], cols: int) -> np.ndarray:
        """격자 레이아웃 생성"""
        rows = (len(items) + cols - 1) // cols
        
        # 썸네일 크기
        thumb_size = 200
        margin = 10
        
        # 전체 이미지 크기
        total_width = cols * thumb_size + (cols + 1) * margin
        total_height = rows * thumb_size + (rows + 1) * margin + 30  # 제목 공간
        
        # 배경 이미지 생성
        gallery_image = np.ones((total_height, total_width, 3), dtype=np.uint8) * 240
        
        # 썸네일 배치
        for i, item in enumerate(items):
            row = i // cols
            col = i % cols
            
            x = col * (thumb_size + margin) + margin
            y = row * (thumb_size + margin) + margin + 30
            
            # 썸네일 로드
            thumbnail = self.get_thumbnail(item.id)
            if thumbnail is not None:
                # 썸네일 크기 조정
                thumbnail = cv2.resize(thumbnail, (thumb_size, thumb_size))
                gallery_image[y:y+thumb_size, x:x+thumb_size] = thumbnail
                
                # 이름 추가 (간단히 OpenCV 텍스트 사용)
                cv2.putText(gallery_image, item.name[:15], (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        return gallery_image
    
    def _create_list_layout(self, items: List[GalleryItem]) -> np.ndarray:
        """리스트 레이아웃 생성"""
        # 간단한 리스트 뷰 (썸네일 + 정보)
        thumb_size = 100
        item_height = thumb_size + 20
        margin = 10
        
        total_width = 800
        total_height = len(items) * item_height + (len(items) + 1) * margin
        
        list_image = np.ones((total_height, total_width, 3), dtype=np.uint8) * 250
        
        for i, item in enumerate(items):
            y = i * item_height + (i + 1) * margin
            
            # 썸네일
            thumbnail = self.get_thumbnail(item.id)
            if thumbnail is not None:
                thumbnail = cv2.resize(thumbnail, (thumb_size, thumb_size))
                list_image[y:y+thumb_size, margin:margin+thumb_size] = thumbnail
            
            # 정보 텍스트
            text_x = margin + thumb_size + 20
            cv2.putText(list_image, item.name, (text_x, y+30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(list_image, f"Created: {item.creation_time.strftime('%Y-%m-%d')}", 
                       (text_x, y+60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
            cv2.putText(list_image, f"Tags: {', '.join(item.tags[:3])}", 
                       (text_x, y+80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        return list_image
    
    def _load_gallery_metadata(self):
        """갤러리 메타데이터 로드"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item_data in data.get("items", []):
                    item = GalleryItem.from_dict(item_data)
                    self.items[item.id] = item
                    
        except Exception as e:
            print(f"갤러리 메타데이터 로드 실패: {e}")
    
    def _save_gallery_metadata(self):
        """갤러리 메타데이터 저장"""
        try:
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "items": [item.to_dict() for item in self.items.values()]
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"갤러리 메타데이터 저장 실패: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """갤러리 통계 조회"""
        total_items = len(self.items)
        
        # 태그별 통계
        tag_counts = {}
        for item in self.items.values():
            for tag in item.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 날짜별 통계
        dates = [item.creation_time.date() for item in self.items.values()]
        date_counts = {}
        for date in dates:
            date_str = date.isoformat()
            date_counts[date_str] = date_counts.get(date_str, 0) + 1
        
        return {
            "total_items": total_items,
            "tag_statistics": tag_counts,
            "date_statistics": date_counts,
            "most_common_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def export_gallery(self, export_path: str) -> bool:
        """갤러리 내보내기"""
        try:
            export_data = {
                "gallery_metadata": {
                    "version": "1.0",
                    "export_time": datetime.now().isoformat(),
                    "total_items": len(self.items)
                },
                "items": [item.to_dict() for item in self.items.values()]
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"갤러리 내보내기 실패: {e}")
            return False