#!/usr/bin/env python3
"""
코 마스크 디버깅
"""

import numpy as np
import cv2
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.core import Point3D, Color
from engines.makeup_engine import RealtimeMakeupEngine


def create_test_image(width=400, height=400):
    """테스트용 얼굴 이미지 생성"""
    # 기본 피부색 배경
    image = np.full((height, width, 3), [180, 150, 120], dtype=np.uint8)  # BGR 형식
    
    # 얼굴 타원 그리기
    center = (width // 2, height // 2)
    axes = (width // 3, int(height * 0.4))
    cv2.ellipse(image, center, axes, 0, 0, 360, [200, 170, 140], -1)
    
    return image


def create_test_landmarks(width=400, height=400):
    """테스트용 얼굴 랜드마크 생성"""
    landmarks = []
    
    # 나머지 랜드마크를 충분히 생성 (총 468개까지)
    while len(landmarks) < 468:
        x = np.random.randint(50, width - 50)
        y = np.random.randint(50, height - 50)
        landmarks.append(Point3D(x, y, 0))
    
    return landmarks


def debug_nose_mask():
    """코 마스크 디버깅"""
    print("=== 코 마스크 디버깅 ===")
    
    # 테스트 데이터 준비
    image = create_test_image()
    landmarks = create_test_landmarks()
    engine = RealtimeMakeupEngine()
    
    # 코 마스크 생성
    nose_mask = engine._get_cheek_mask(image, landmarks, "nose")
    
    print(f"마스크 크기: {nose_mask.shape}")
    print(f"마스크 최대값: {nose_mask.max()}")
    print(f"마스크 최소값: {nose_mask.min()}")
    print(f"0이 아닌 픽셀 수: {np.sum(nose_mask > 0)}")
    
    # 마스크 시각화
    cv2.imwrite('debug_nose_mask.jpg', nose_mask)
    print("마스크 이미지 저장: debug_nose_mask.jpg")
    
    # 원본 이미지에 마스크 오버레이
    overlay = image.copy()
    overlay[nose_mask > 0] = [0, 255, 0]  # 녹색으로 표시
    result = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
    cv2.imwrite('debug_nose_overlay.jpg', result)
    print("오버레이 이미지 저장: debug_nose_overlay.jpg")


if __name__ == "__main__":
    debug_nose_mask()