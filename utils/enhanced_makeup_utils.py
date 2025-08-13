"""
향상된 메이크업 유틸리티 - Reference files 완전 호환
utils.py의 모든 기능을 포함하며 추가 개선사항 적용
"""
import numpy as np
import mediapipe as mp
import cv2
from typing import Dict, List, Tuple, Optional


# MediaPipe 기반 정확한 얼굴 랜드마크 포인트 (reference files에서 완전히 복사)
face_points = {
    "BLUSH_LEFT": [50],
    "BLUSH_RIGHT": [280],
    "LEFT_EYE": [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7, 33],
    "RIGHT_EYE": [362, 298, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382, 362],
    "EYELINER_LEFT": [243, 112, 26, 22, 23, 24, 110, 25, 226, 130, 33, 7, 163, 144, 145, 153, 154, 155, 133, 243],
    "EYELINER_RIGHT": [463, 362, 382, 381, 380, 374, 373, 390, 249, 263, 359, 446, 255, 339, 254, 253, 252, 256, 341, 463],
    "EYESHADOW_LEFT": [226, 247, 30, 29, 27, 28, 56, 190, 243, 173, 157, 158, 159, 160, 161, 246, 33, 130, 226],
    "EYESHADOW_RIGHT": [463, 414, 286, 258, 257, 259, 260, 467, 446, 359, 263, 466, 388, 387, 386, 385, 384, 398, 362, 463],
    "FACE": [152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10, 338, 297, 332, 284, 251, 389, 454, 323, 401, 361, 435, 288, 397, 365, 379, 378, 400, 377, 152],
    "LIP_UPPER": [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 308, 415, 310, 312, 13, 82, 81, 80, 191, 78],
    "LIP_LOWER": [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 402, 317, 14, 87, 178, 88, 95, 78, 61],
    "EYEBROW_LEFT": [55, 107, 66, 105, 63, 70, 46, 53, 52, 65, 55],
    "EYEBROW_RIGHT": [285, 336, 296, 334, 293, 300, 276, 283, 295, 285]
}

# MediaPipe 함수 초기화
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils


def show_image(image: np.array, msg: str = "Loaded Image"):
    """
    Reference files의 show_image 함수와 완전히 동일
    cv2 창에 이미지 표시
    
    Args:
        image: 이미지 배열
        msg: cv2 창 이름
    """
    image_copy = image.copy()
    cv2.imshow(msg, image_copy)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def read_landmarks(image: np.array) -> Dict[int, Tuple[int, int]]:
    """
    Reference files의 read_landmarks 함수와 완전히 동일
    MediaPipe를 사용하여 얼굴 랜드마크 추출
    
    Args:
        image: 이미지 배열
        
    Returns:
        랜드마크 인덱스와 (x, y) 좌표의 딕셔너리
    """
    landmark_cordinates = {}
    
    # MediaPipe facemesh 로드 및 얼굴 랜드마크 감지
    # 얼굴 랜드마크는 0부터 477까지의 정규화된 포인트를 반환
    with mp_face_mesh.FaceMesh(refine_landmarks=True) as face_mesh:
        results = face_mesh.process(image)
        
        # 얼굴 랜드마크가 감지되었는지 확인
        if results.multi_face_landmarks is None or len(results.multi_face_landmarks) == 0:
            print("No face detected in the image.")
            return landmark_cordinates
            
        face_landmarks = results.multi_face_landmarks[0].landmark

    # 정규화된 포인트를 이미지 차원에 맞게 변환
    for idx, landmark in enumerate(face_landmarks):
        landmark_px = mp_drawing._normalized_to_pixel_coordinates(
            landmark.x, landmark.y, image.shape[1], image.shape[0]
        )
        # 얼굴 랜드마크와 (x,y) 좌표의 맵 생성
        if landmark_px:
            landmark_cordinates[idx] = landmark_px
    return landmark_cordinates


def add_mask(mask: np.array, idx_to_coordinates: dict, face_connections: list, colors: list) -> np.array:
    """
    Reference files의 add_mask 함수와 완전히 동일
    입력된 얼굴 특징을 기반으로 색상에 맞는 마스크 생성
    
    Args:
        mask: 0으로 채워진 이미지
        idx_to_coordinates: 각 얼굴 랜드마크에 대한 (x,y) 좌표 딕셔너리
        face_connections: 각 얼굴 특징에 대한 (x,y) 좌표 리스트
        colors: 각 특징에 대한 [B,G,R] 색상 리스트
        
    Returns:
        색상이 적용된 마스크
    """
    # 랜드마크가 감지되었는지 확인
    if not idx_to_coordinates:
        print("No facial landmarks detected. Returning empty mask.")
        return mask
        
    for i, connection in enumerate(face_connections):
        # 각 좌표에 대한 (x,y) 이미지 추출
        # 필요한 모든 랜드마크가 사용 가능한지 확인
        if all(idx in idx_to_coordinates for idx in connection):
            points = np.array([idx_to_coordinates[idx] for idx in connection])
            # 마스크에 특징 모양을 만들고 색상 추가
            cv2.fillPoly(mask, [points], colors[i])

    # 이미지 부드럽게 처리
    mask = cv2.GaussianBlur(mask, (7, 7), 4)
    return mask


def add_enhanced_mask(mask: np.array, idx_to_coordinates: dict, face_connections: list, 
                     colors_map: dict, intensity_map: dict, face_elements: list, 
                     blur_strength: int, blur_sigma: int) -> np.array:
    """
    Reference files의 add_enhanced_mask 함수와 완전히 동일
    강화된 마스크 생성 함수
    
    Args:
        mask: 빈 마스크 이미지
        idx_to_coordinates: 랜드마크 좌표 딕셔너리
        face_connections: 얼굴 연결점 리스트
        colors_map: 색상 맵
        intensity_map: 강도 맵
        face_elements: 얼굴 요소 리스트
        blur_strength: 블러 강도
        blur_sigma: 블러 시그마
        
    Returns:
        강화된 마스크
    """
    if not idx_to_coordinates:
        return mask
    
    for i, (connection, element) in enumerate(zip(face_connections, face_elements)):
        if all(idx in idx_to_coordinates for idx in connection):
            points = np.array([idx_to_coordinates[idx] for idx in connection])
            
            # 개별 부위별 마스크 생성
            temp_mask = np.zeros_like(mask)
            color = colors_map[element]
            cv2.fillPoly(temp_mask, [points], color)
            
            # 블러 적용
            temp_mask = cv2.GaussianBlur(temp_mask, (blur_strength, blur_strength), blur_sigma)
            
            # 부위별 강도 적용
            intensity = intensity_map[element]
            temp_mask = (temp_mask * intensity).astype(np.uint8)
            
            # 마스크에 추가
            mask = cv2.add(mask, temp_mask)
    
    return mask


def draw_landmarks(image: np.array, landmarks: dict, color: tuple = (0, 255, 0), radius: int = 2) -> np.array:
    """
    Reference files의 draw_landmarks 함수와 완전히 동일
    얼굴 랜드마크를 이미지에 그리기
    
    Args:
        image: 원본 이미지
        landmarks: 랜드마크 딕셔너리
        color: 랜드마크 색상 (기본: 녹색)
        radius: 랜드마크 반지름
        
    Returns:
        랜드마크가 그려진 이미지
    """
    result = image.copy()
    for idx, point in landmarks.items():
        cv2.circle(result, point, radius, color, -1)
    return result


def apply_makeup(image: np.array, colors_map: dict, intensity_map: dict, mask_alpha: float, 
                blur_strength: int, blur_sigma: int, show_landmarks: bool = False) -> tuple:
    """
    Reference files의 apply_makeup 함수와 완전히 동일
    메이크업을 적용하는 함수
    
    Args:
        image: 원본 이미지
        colors_map: 색상 맵
        intensity_map: 강도 맵
        mask_alpha: 마스크 투명도
        blur_strength: 블러 강도
        blur_sigma: 블러 시그마
        show_landmarks: 랜드마크 표시 여부
        
    Returns:
        (결과 이미지, 마스크, 얼굴 감지 여부)
    """
    # 얼굴 부위 설정
    face_elements = [
        "LIP_LOWER", "LIP_UPPER",
        "EYEBROW_LEFT", "EYEBROW_RIGHT",
        "EYELINER_LEFT", "EYELINER_RIGHT",
        "EYESHADOW_LEFT", "EYESHADOW_RIGHT",
    ]
    
    # 얼굴 연결점 추출
    face_connections = [face_points[idx] for idx in face_elements]
    
    # 빈 마스크 생성
    mask = np.zeros_like(image)
    
    # 얼굴 랜드마크 추출
    face_landmarks = read_landmarks(image=image)
    
    # 향상된 마스크 생성
    mask = add_enhanced_mask(
        mask, face_landmarks, face_connections, 
        colors_map, intensity_map, face_elements,
        blur_strength, blur_sigma
    )
    
    # 이미지와 마스크 결합
    output = cv2.addWeighted(image, 1.0, mask, mask_alpha, 1.0)
    
    # 랜드마크 표시
    if show_landmarks and face_landmarks:
        output = draw_landmarks(output, face_landmarks)
    
    return output, mask, len(face_landmarks) > 0


def get_face_points() -> dict:
    """
    Reference files의 face_points 반환
    
    Returns:
        얼굴 포인트 딕셔너리
    """
    return face_points.copy()


def get_default_colors_map() -> dict:
    """
    Reference files의 기본 색상 맵 반환
    
    Returns:
        기본 색상 맵 (BGR 형식)
    """
    return {
        # 상하 입술
        "LIP_UPPER": [0, 0, 255],  # Red in BGR
        "LIP_LOWER": [0, 0, 255],  # Red in BGR
        # 아이라이너
        "EYELINER_LEFT": [139, 0, 0],  # Dark Blue in BGR
        "EYELINER_RIGHT": [139, 0, 0],  # Dark Blue in BGR
        # 아이섀도
        "EYESHADOW_LEFT": [0, 100, 0],  # Dark Green in BGR
        "EYESHADOW_RIGHT": [0, 100, 0],  # Dark Green in BGR
        # 눈썹
        "EYEBROW_LEFT": [19, 69, 139],  # Dark Brown in BGR
        "EYEBROW_RIGHT": [19, 69, 139],  # Dark Brown in BGR
    }


def get_face_elements() -> list:
    """
    Reference files에서 사용하는 얼굴 요소 리스트 반환
    
    Returns:
        얼굴 요소 리스트
    """
    return [
        "LIP_LOWER",
        "LIP_UPPER", 
        "EYEBROW_LEFT",
        "EYEBROW_RIGHT",
        "EYELINER_LEFT",
        "EYELINER_RIGHT",
        "EYESHADOW_LEFT",
        "EYESHADOW_RIGHT",
    ]


def validate_image_input(image: np.array) -> bool:
    """
    이미지 입력 유효성 검증
    
    Args:
        image: 검증할 이미지
        
    Returns:
        유효성 여부
    """
    if image is None:
        return False
    if len(image.shape) != 3:
        return False
    if image.shape[2] != 3:
        return False
    return True


def convert_rgb_to_bgr_color(rgb_color: str) -> list:
    """
    RGB 색상 문자열을 BGR 리스트로 변환
    
    Args:
        rgb_color: "#RRGGBB" 형식의 색상 문자열
        
    Returns:
        [B, G, R] 형식의 색상 리스트
    """
    # "#RRGGBB"에서 RGB 값 추출
    r, g, b = tuple(int(rgb_color[i:i+2], 16) for i in (1, 3, 5))
    # BGR 형식으로 반환
    return [b, g, r]


def create_intensity_map(lip: float = 1.0, eyeliner: float = 1.0, 
                        eyeshadow: float = 1.0, eyebrow: float = 1.0) -> dict:
    """
    강도 맵 생성 헬퍼 함수
    
    Args:
        lip: 입술 강도
        eyeliner: 아이라이너 강도
        eyeshadow: 아이섀도 강도
        eyebrow: 눈썹 강도
        
    Returns:
        강도 맵 딕셔너리
    """
    return {
        "LIP_UPPER": lip,
        "LIP_LOWER": lip,
        "EYELINER_LEFT": eyeliner,
        "EYELINER_RIGHT": eyeliner,
        "EYESHADOW_LEFT": eyeshadow,
        "EYESHADOW_RIGHT": eyeshadow,
        "EYEBROW_LEFT": eyebrow,
        "EYEBROW_RIGHT": eyebrow,
    }


def apply_simple_makeup_from_reference(image_path: str, colors_map: dict = None) -> np.array:
    """
    Reference files의 main 함수 로직을 완전히 재현
    
    Args:
        image_path: 이미지 경로 또는 이미지 배열
        colors_map: 색상 맵 (선택사항)
        
    Returns:
        메이크업이 적용된 이미지
    """
    # 기본 색상 맵 설정
    if colors_map is None:
        colors_map = get_default_colors_map()
    
    # 적용할 얼굴 특징 추출
    face_elements = get_face_elements()
    
    # 필요한 얼굴 포인트와 색상 추출
    face_connections = [face_points[idx] for idx in face_elements]
    colors = [colors_map[idx] for idx in face_elements]
    
    # 이미지 읽기
    if isinstance(image_path, str):
        image = cv2.imread(image_path)
    else:
        image = image_path
    
    if not validate_image_input(image):
        raise ValueError("유효하지 않은 이미지입니다.")
    
    # 이미지와 같은 크기의 빈 마스크 생성
    mask = np.zeros_like(image)
    
    # 얼굴 랜드마크 추출
    face_landmarks = read_landmarks(image=image)
    
    # 얼굴 특징에 대한 색상 마스크 생성
    mask = add_mask(
        mask,
        idx_to_coordinates=face_landmarks,
        face_connections=face_connections,
        colors=colors
    )
    
    # 이미지와 마스크를 가중치에 따라 결합
    output = cv2.addWeighted(image, 1.0, mask, 0.2, 1.0)
    
    return output


# Reference files와의 완전한 호환성을 위한 별칭
def main_reference_compatible(image_path: str):
    """
    Reference files의 main 함수와 완전히 호환되는 함수
    """
    result = apply_simple_makeup_from_reference(image_path)
    show_image(result)
    return result