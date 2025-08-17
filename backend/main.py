from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict, Any
import io
import cv2
import numpy as np
from PIL import Image
import mediapipe as mp
import base64
import uuid
import os
import math
from datetime import datetime
import openai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 앱 초기화
app = FastAPI(
    title="Face Simulator API",
    description="얼굴 성형 시뮬레이터 백엔드 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Flutter 웹/앱에서 접근 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MediaPipe 초기화
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# 전역 변수
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# 임시 파일 저장 디렉토리
TEMP_DIR = "temp_images"
os.makedirs(TEMP_DIR, exist_ok=True)

# Pydantic 모델들
class WarpRequest(BaseModel):
    image_id: str
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    influence_radius: float = 80.0
    strength: float = 1.0
    mode: str = "pull"  # pull, push, expand, shrink

class PresetRequest(BaseModel):
    image_id: str
    preset_type: str  # lower_jaw, middle_jaw, cheek, front_protusion, back_slit

class LandmarkResponse(BaseModel):
    landmarks: List[Tuple[float, float]]
    image_width: int
    image_height: int

class ImageResponse(BaseModel):
    image_id: str
    image_data: str  # base64 encoded

class BeautyComparisonRequest(BaseModel):
    before_analysis: Dict[str, Any]  # 이전 뷰티 분석 결과
    after_analysis: Dict[str, Any]   # 현재 뷰티 분석 결과

class BeautyComparisonResponse(BaseModel):
    overall_change: str  # 전반적 변화 ("improved", "declined", "similar")
    score_changes: Dict[str, float]  # 각 항목별 점수 변화
    recommendations: List[str]  # GPT 추천사항
    analysis_text: str  # 상세 분석 텍스트

class InitialBeautyAnalysisRequest(BaseModel):
    beauty_analysis: Dict[str, Any]  # 뷰티 분석 결과

class InitialBeautyAnalysisResponse(BaseModel):
    analysis_text: str  # 상세 분석 텍스트
    recommendations: List[str]  # GPT 추천사항
    strengths: List[str]  # 강점 분석
    improvement_areas: List[str]  # 개선 영역

    
@app.get("/")
async def root():
    return {"message": "Face Simulator API", "status": "running"}

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """이미지 업로드 및 ID 반환"""
    try:
        # 파일 검증
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다")
        
        # 이미지 ID 생성
        image_id = str(uuid.uuid4())
        
        # 파일 읽기 및 저장
        contents = await file.read()
        
        # OpenCV로 이미지 읽기
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="유효하지 않은 이미지 파일입니다")
        
        # RGB로 변환
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 임시 파일로 저장
        temp_path = os.path.join(TEMP_DIR, f"{image_id}.jpg")
        cv2.imwrite(temp_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
        
        # 이미지 크기 정보
        height, width = image_rgb.shape[:2]
        
        return {
            "image_id": image_id,
            "width": width,
            "height": height,
            "message": "이미지 업로드 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 업로드 실패: {str(e)}")

@app.get("/landmarks/{image_id}")
async def get_face_landmarks(image_id: str):
    """얼굴 랜드마크 검출"""
    try:
        temp_path = os.path.join(TEMP_DIR, f"{image_id}.jpg")
        
        if not os.path.exists(temp_path):
            raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
        
        # 이미지 로드
        image = cv2.imread(temp_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]
        
        # MediaPipe로 얼굴 랜드마크 검출
        results = face_mesh.process(image_rgb)
        
        if not results.multi_face_landmarks:
            raise HTTPException(status_code=404, detail="얼굴을 찾을 수 없습니다")
        
        # 랜드마크 좌표 추출
        landmarks = []
        face_landmarks = results.multi_face_landmarks[0]
        
        for landmark in face_landmarks.landmark:
            x = landmark.x * width
            y = landmark.y * height
            landmarks.append((x, y))
        
        return LandmarkResponse(
            landmarks=landmarks,
            image_width=width,
            image_height=height
        )
        
    except Exception as e:
        if "이미지를 찾을 수 없습니다" in str(e) or "얼굴을 찾을 수 없습니다" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"랜드마크 검출 실패: {str(e)}")

@app.post("/warp-image")
async def warp_image(request: WarpRequest):
    """이미지 워핑(자유변형) 적용"""
    try:
        temp_path = os.path.join(TEMP_DIR, f"{request.image_id}.jpg")
        
        if not os.path.exists(temp_path):
            raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
        
        # 이미지 로드
        image = cv2.imread(temp_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 워핑 적용
        warped_image = apply_warp(
            image_rgb,
            start_x=request.start_x,
            start_y=request.start_y,
            end_x=request.end_x,
            end_y=request.end_y,
            influence_radius=request.influence_radius,
            strength=request.strength,
            mode=request.mode
        )
        
        # 새로운 UUID로 결과 이미지 저장 (원본 보존)
        import uuid
        new_image_id = str(uuid.uuid4())
        new_temp_path = os.path.join(TEMP_DIR, f"{new_image_id}.jpg")
        cv2.imwrite(new_temp_path, cv2.cvtColor(warped_image, cv2.COLOR_RGB2BGR))
        
        # Base64로 인코딩하여 반환
        pil_image = Image.fromarray(warped_image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=95)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return ImageResponse(
            image_id=new_image_id,
            image_data=img_base64
        )
        
    except Exception as e:
        if "이미지를 찾을 수 없습니다" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"이미지 워핑 실패: {str(e)}")

@app.get("/download-image/{image_id}")
async def download_image(image_id: str):
    """이미지 다운로드"""
    try:
        temp_path = os.path.join(TEMP_DIR, f"{image_id}.jpg")
        
        if not os.path.exists(temp_path):
            raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
        
        # 파일 스트리밍 응답
        def iterfile(file_path: str):
            with open(file_path, mode="rb") as file_like:
                yield from file_like
        
        return StreamingResponse(
            iterfile(temp_path),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"attachment; filename=face_simulator_result_{image_id[:8]}.jpg"}
        )
        
    except Exception as e:
        if "이미지를 찾을 수 없습니다" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"이미지 다운로드 실패: {str(e)}")

@app.post("/apply-preset")
async def apply_preset(request: PresetRequest):
    """프리셋 적용"""
    try:
        temp_path = os.path.join(TEMP_DIR, f"{request.image_id}.jpg")
        
        if not os.path.exists(temp_path):
            raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
        
        # 이미지 로드
        image = cv2.imread(temp_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 얼굴 랜드마크 검출
        results = face_mesh.process(image_rgb)
        
        if not results.multi_face_landmarks:
            raise HTTPException(status_code=404, detail="얼굴을 찾을 수 없습니다")
        
        # 랜드마크 좌표 추출
        height, width = image_rgb.shape[:2]
        landmarks = []
        face_landmarks = results.multi_face_landmarks[0]
        
        for landmark in face_landmarks.landmark:
            x = landmark.x * width
            y = landmark.y * height
            landmarks.append((x, y))
        
        # 프리셋 적용
        result_image = apply_preset_transformation(image_rgb, landmarks, request.preset_type)
        
        # 새로운 UUID로 결과 이미지 저장
        new_image_id = str(uuid.uuid4())
        new_temp_path = os.path.join(TEMP_DIR, f"{new_image_id}.jpg")
        cv2.imwrite(new_temp_path, cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))
        
        # Base64로 인코딩하여 반환
        pil_image = Image.fromarray(result_image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=95)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return ImageResponse(
            image_id=new_image_id,
            image_data=img_base64
        )
        
    except Exception as e:
        if "이미지를 찾을 수 없습니다" in str(e) or "얼굴을 찾을 수 없습니다" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"프리셋 적용 실패: {str(e)}")

@app.delete("/image/{image_id}")
async def delete_image(image_id: str):
    """임시 이미지 삭제"""
    try:
        temp_path = os.path.join(TEMP_DIR, f"{image_id}.jpg")
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            return {"message": "이미지 삭제 성공"}
        else:
            return {"message": "이미지가 이미 삭제되었거나 존재하지 않습니다"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 삭제 실패: {str(e)}")

@app.post("/analyze-beauty-comparison")
async def analyze_beauty_comparison(request: BeautyComparisonRequest):
    """뷰티 점수 변화 분석 및 GPT 추천"""
    try:
        before = request.before_analysis
        after = request.after_analysis
        
        # 점수 변화 계산
        score_changes = {}
        if 'overallScore' in before and 'overallScore' in after:
            score_changes['overall'] = after['overallScore'] - before['overallScore']
        
        # 세부 항목별 변화
        detail_items = ['verticalScore', 'horizontalScore', 'lowerFaceScore', 'symmetry', 'eyeScore', 'noseScore', 'lipScore', 'jawScore']
        for item in detail_items:
            if item in before and item in after:
                # 딕셔너리 타입인 경우 'score' 키에서 값 추출
                if isinstance(before[item], dict) and isinstance(after[item], dict):
                    before_score = before[item].get('score', 0)
                    after_score = after[item].get('score', 0)
                    score_changes[item] = after_score - before_score
                else:
                    # 숫자 타입인 경우 직접 계산
                    score_changes[item] = after[item] - before[item]
        
        # 전반적 변화 판단
        overall_change = "similar"
        if score_changes.get('overall', 0) > 2:
            overall_change = "improved"
        elif score_changes.get('overall', 0) < -2:
            overall_change = "declined"
        
        # GPT-4o mini를 사용한 분석
        analysis_result = await get_gpt_beauty_analysis(before, after, score_changes)
        
        return BeautyComparisonResponse(
            overall_change=overall_change,
            score_changes=score_changes,
            recommendations=analysis_result["recommendations"],
            analysis_text=analysis_result["analysis"]
        )
        
    except Exception as e:
        print(f"뷰티 분석 비교 에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"뷰티 분석 비교 실패: {str(e)}")

@app.post("/analyze-initial-beauty-score")
async def analyze_initial_beauty_score(request: InitialBeautyAnalysisRequest):
    """기초 뷰티스코어 GPT 분석"""
    try:
        beauty_analysis = request.beauty_analysis
        
        # GPT-4o mini를 사용한 기초 뷰티스코어 분석
        analysis_result = await get_gpt_initial_beauty_analysis(beauty_analysis)
        
        return InitialBeautyAnalysisResponse(
            analysis_text=analysis_result["analysis"],
            recommendations=analysis_result["recommendations"],
            strengths=analysis_result["strengths"],
            improvement_areas=analysis_result["improvement_areas"]
        )
        
    except Exception as e:
        print(f"기초 뷰티스코어 GPT 분석 에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"기초 뷰티스코어 GPT 분석 실패: {str(e)}")


def apply_warp(image: np.ndarray, start_x: float, start_y: float, 
               end_x: float, end_y: float, influence_radius: float, 
               strength: float, mode: str) -> np.ndarray:
    """워핑 변형 적용 함수"""
    img_height, img_width = image.shape[:2]
    
    # 좌표 경계 검사
    start_x = max(0, min(start_x, img_width - 1))
    start_y = max(0, min(start_y, img_height - 1))
    end_x = max(0, min(end_x, img_width - 1))
    end_y = max(0, min(end_y, img_height - 1))
    
    print(f"워핑 모드: {mode}")
    if mode == "pull":
        return apply_pull_warp(image, start_x, start_y, end_x, end_y, influence_radius, strength)
    elif mode == "push":
        return apply_push_warp(image, start_x, start_y, end_x, end_y, influence_radius, strength)
    elif mode == "expand":
        print("확대 모드 실행 - expand=True")
        return apply_radial_warp(image, start_x, start_y, influence_radius, strength, expand=True)
    elif mode == "shrink":
        print("축소 모드 실행 - expand=False")
        return apply_radial_warp(image, start_x, start_y, influence_radius, strength, expand=False)
    else:
        print(f"알 수 없는 모드: {mode}")
        return image

def apply_pull_warp(image: np.ndarray, start_x: float, start_y: float,
                   end_x: float, end_y: float, influence_radius: float, strength: float, ellipse_ratio: float = None) -> np.ndarray:
    """당기기 워핑"""
    img_height, img_width = image.shape[:2]
    
    # 드래그 벡터 (예전 방식: 반대 방향)
    dx = start_x - end_x
    dy = start_y - end_y
    
    # 변형 맵 생성
    map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
    map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
    map_x = np.repeat(map_x, img_height, axis=0)
    map_y = np.repeat(map_y, img_width, axis=1)
    
    # 각 픽셀에서 시작점까지의 거리 계산
    pixel_dx = map_x - start_x
    pixel_dy = map_y - start_y
    pixel_dist = np.sqrt(pixel_dx*pixel_dx + pixel_dy*pixel_dy)
    
    # 영향받는 영역 마스크
    mask = pixel_dist < influence_radius
    
    # 변형 강도 계산
    strength_map = np.zeros_like(pixel_dist)
    valid_dist = pixel_dist[mask]
    
    if len(valid_dist) > 0:
        strength_map[mask] = (1 - valid_dist / influence_radius) ** 2
        strength_map[mask] *= strength
        
        # 변형 적용
        map_x[mask] += dx * strength_map[mask]
        map_y[mask] += dy * strength_map[mask]
    
    # 경계 클리핑
    map_x = np.clip(map_x, 0, img_width - 1)
    map_y = np.clip(map_y, 0, img_height - 1)
    
    # 리맵핑 적용
    return cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def apply_push_warp(image: np.ndarray, start_x: float, start_y: float,
                   end_x: float, end_y: float, influence_radius: float, strength: float) -> np.ndarray:
    """밀어내기 워핑"""
    img_height, img_width = image.shape[:2]
    
    # 드래그 벡터
    dx = end_x - start_x
    dy = end_y - start_y
    
    # 변형 맵 생성
    map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
    map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
    map_x = np.repeat(map_x, img_height, axis=0)
    map_y = np.repeat(map_y, img_width, axis=1)
    
    # 각 픽셀에서 시작점까지의 거리 계산
    pixel_dx = map_x - start_x
    pixel_dy = map_y - start_y
    pixel_dist = np.sqrt(pixel_dx*pixel_dx + pixel_dy*pixel_dy)
    
    # 영향받는 영역 마스크
    mask = pixel_dist < influence_radius
    
    # 변형 강도 계산
    strength_map = np.zeros_like(pixel_dist)
    valid_dist = pixel_dist[mask]
    
    if len(valid_dist) > 0:
        strength_map[mask] = (1 - valid_dist / influence_radius) ** 2
        strength_map[mask] *= strength
        
        # 변형 적용
        map_x[mask] += dx * strength_map[mask]
        map_y[mask] += dy * strength_map[mask]
    
    # 경계 클리핑
    map_x = np.clip(map_x, 0, img_width - 1)
    map_y = np.clip(map_y, 0, img_height - 1)
    
    # 리맵핑 적용
    return cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def apply_radial_warp(image: np.ndarray, center_x: float, center_y: float,
                     influence_radius: float, strength: float, expand: bool = True) -> np.ndarray:
    """방사형 워핑 (확대/축소)"""
    img_height, img_width = image.shape[:2]
    
    # 변형 맵 생성
    map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
    map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
    map_x = np.repeat(map_x, img_height, axis=0)
    map_y = np.repeat(map_y, img_width, axis=1)
    
    # 중심점으로부터의 거리와 각도
    dx = map_x - center_x
    dy = map_y - center_y
    distance = np.sqrt(dx*dx + dy*dy)
    
    # 영향받는 영역
    mask = distance < influence_radius
    
    # 변형 계수 계산
    strength_factor = strength * 0.3
    
    if expand:
        # 확대: 중심으로 가까워지게 (팽창 효과)
        scale_factor = 1 - strength_factor * (1 - distance / influence_radius)
    else:
        # 축소: 중심에서 멀어지게 (수축 효과)
        scale_factor = 1 + strength_factor * (1 - distance / influence_radius)
    
    scale_factor = np.maximum(scale_factor, 0.1)  # 최소 스케일 제한
    
    # 새로운 좌표 계산
    new_x = center_x + dx * scale_factor
    new_y = center_y + dy * scale_factor
    
    # 영향받는 영역만 업데이트
    map_x = np.where(mask, new_x, map_x)
    map_y = np.where(mask, new_y, map_y)
    
    # 경계 클리핑
    map_x = np.clip(map_x, 0, img_width - 1)
    map_y = np.clip(map_y, 0, img_height - 1)
    
    # 리맵핑 적용
    return cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def apply_preset_transformation(image: np.ndarray, landmarks: List[Tuple[float, float]], preset_type: str) -> np.ndarray:
    """프리셋 변형 적용"""
    print(f"\n=== PRESET DEBUG: {preset_type} ===")
    print(f"Image shape: {image.shape}")
    print(f"Total landmarks: {len(landmarks)}")
    
    # 프리셋 상수들 (face_simulator.py에서 가져옴)
    PRESET_CONFIGS = {
        'lower_jaw': {
            'strength': 0.05,
            'influence_ratio': 0.4,
            'pull_ratio': 0.1,
            'face_size_landmarks': (234, 447),
            'target_landmarks': (150, 379, 4)
        },
        'middle_jaw': {
            'strength': 0.05,
            'influence_ratio': 0.65,
            'pull_ratio': 0.1,
            'face_size_landmarks': (234, 447),
            'target_landmarks': (172, 397, 4)
        },
        'cheek': {
            'strength': 0.05,
            'influence_ratio': 0.65,
            'pull_ratio': 0.1,
            'face_size_landmarks': (234, 447),
            'target_landmarks': (215, 435, 4)
        },
        'front_protusion': {
            'strength': 0.3,
            'influence_ratio': 0.1,
            'pull_ratio': 0.1,
            'face_size_landmarks': (234, 447),
            'target_landmarks': (243, 463, (56, 190), (414, 286), 168, 6),
            'ellipse_ratio': 1.3
        },
        'back_slit': {
            'strength': 0.5,
            'influence_ratio': 0.1,
            'pull_ratio': 0.1,
            'face_size_landmarks': (234, 447),
            'target_landmarks': (33, 359, (34, 162), (368, 264))
        }
    }
    
    if preset_type not in PRESET_CONFIGS:
        raise ValueError(f"Unknown preset type: {preset_type}")
    
    config = PRESET_CONFIGS[preset_type]
    
    # 얼굴 크기 계산
    face_size_left = landmarks[config['face_size_landmarks'][0]]
    face_size_right = landmarks[config['face_size_landmarks'][1]]
    face_width = abs(face_size_right[0] - face_size_left[0])
    
    print(f"Face landmarks: left={face_size_left}, right={face_size_right}")
    print(f"Face width: {face_width}px")
    
    # 영향 반경 계산
    influence_radius = face_width * config['influence_ratio']
    print(f"Influence radius: {influence_radius}px (ratio: {config['influence_ratio']})")
    print(f"Config: {config}")
    
    result_image = image.copy()
    
    if preset_type in ['lower_jaw', 'middle_jaw', 'cheek']:
        # 기본 턱선 프리셋 (좌우 대칭)
        left_landmark = landmarks[config['target_landmarks'][0]]
        right_landmark = landmarks[config['target_landmarks'][1]]
        target_landmark = landmarks[config['target_landmarks'][2]]
        
        # 좌측 변형
        distance_left = math.sqrt((left_landmark[0] - target_landmark[0])**2 + 
                                (left_landmark[1] - target_landmark[1])**2)
        pull_distance_left = distance_left * config['pull_ratio']
        
        dx_left = target_landmark[0] - left_landmark[0]
        dy_left = target_landmark[1] - left_landmark[1]
        norm_left = math.sqrt(dx_left**2 + dy_left**2)
        
        if norm_left > 0:
            dx_left = (dx_left / norm_left) * pull_distance_left
            dy_left = (dy_left / norm_left) * pull_distance_left
            
            target_x_left = left_landmark[0] + dx_left
            target_y_left = left_landmark[1] + dy_left
            
            result_image = apply_pull_warp(
                result_image,
                left_landmark[0], left_landmark[1],
                target_x_left, target_y_left,
                influence_radius, config['strength']
            )
        
        # 우측 변형
        distance_right = math.sqrt((right_landmark[0] - target_landmark[0])**2 + 
                                 (right_landmark[1] - target_landmark[1])**2)
        pull_distance_right = distance_right * config['pull_ratio']
        
        dx_right = target_landmark[0] - right_landmark[0]
        dy_right = target_landmark[1] - right_landmark[1]
        norm_right = math.sqrt(dx_right**2 + dy_right**2)
        
        if norm_right > 0:
            dx_right = (dx_right / norm_right) * pull_distance_right
            dy_right = (dy_right / norm_right) * pull_distance_right
            
            target_x_right = right_landmark[0] + dx_right
            target_y_right = right_landmark[1] + dy_right
            
            result_image = apply_pull_warp(
                result_image,
                right_landmark[0], right_landmark[1],
                target_x_right, target_y_right,
                influence_radius, config['strength']
            )
    
    elif preset_type == 'front_protusion':
        # 앞트임 프리셋 (4개 포인트)
        landmark_243 = landmarks[243]
        landmark_463 = landmarks[463]
        
        print(f"\n--- FRONT PROTUSION DEBUG ---")
        print(f"Landmark 243 (left inner): {landmark_243}")
        print(f"Landmark 463 (right inner): {landmark_463}")
        
        # 중간점들 계산
        mid_56_190 = ((landmarks[56][0] + landmarks[190][0]) / 2,
                      (landmarks[56][1] + landmarks[190][1]) / 2)
        mid_414_286 = ((landmarks[414][0] + landmarks[286][0]) / 2,
                       (landmarks[414][1] + landmarks[286][1]) / 2)
        
        print(f"Mid 56_190: {mid_56_190}")
        print(f"Mid 414_286: {mid_414_286}")
        
        # 앞트임: 예전 방식 - 코 중심으로 당기기
        # 타겟 중간점 계산 (168 + 6의 중간점)
        target_mid = ((landmarks[168][0] + landmarks[6][0]) / 2,
                      (landmarks[168][1] + landmarks[6][1]) / 2)
        
        print(f"Target mid (nose center): {target_mid}")
        
        # 각 포인트에 변형 적용 (코 중심으로)
        for i, (source_landmark, target_point) in enumerate([
            (landmark_243, target_mid),
            (landmark_463, target_mid),
            (mid_56_190, target_mid),
            (mid_414_286, target_mid)
        ]):
            distance = math.sqrt((source_landmark[0] - target_point[0])**2 + 
                               (source_landmark[1] - target_point[1])**2)
            pull_distance = distance * config['pull_ratio']
            
            dx = target_point[0] - source_landmark[0]
            dy = target_point[1] - source_landmark[1]
            norm = math.sqrt(dx**2 + dy**2)
            
            print(f"\nPoint {i+1}: {source_landmark} -> {target_point}")
            print(f"Distance: {distance:.2f}px")
            print(f"Pull ratio: {config['pull_ratio']}")
            print(f"Pull distance: {pull_distance:.2f}px")
            print(f"Direction vector: ({dx:.2f}, {dy:.2f})")
            
            if norm > 0:
                dx = (dx / norm) * pull_distance
                dy = (dy / norm) * pull_distance
                
                target_x = source_landmark[0] + dx
                target_y = source_landmark[1] + dy
                
                print(f"Normalized direction: ({dx:.2f}, {dy:.2f})")
                print(f"Final target: ({target_x:.2f}, {target_y:.2f})")
                print(f"Actual movement: ({dx:.2f}, {dy:.2f})")
                print(f"Strength: {config['strength']}")
                print(f"Influence radius: {influence_radius:.2f}px")
                print(f"Ellipse ratio: {config.get('ellipse_ratio')}")
                
                result_image = apply_pull_warp(
                    result_image,
                    source_landmark[0], source_landmark[1],
                    target_x, target_y,
                    influence_radius, config['strength'],
                    config.get('ellipse_ratio')
                )
    
    elif preset_type == 'back_slit':
        # 뒷트임 프리셋
        landmark_33 = landmarks[33]
        landmark_359 = landmarks[359]
        
        # 타겟 중간점들
        mid_34_162 = ((landmarks[34][0] + landmarks[162][0]) / 2,
                      (landmarks[34][1] + landmarks[162][1]) / 2)
        mid_368_264 = ((landmarks[368][0] + landmarks[264][0]) / 2,
                       (landmarks[368][1] + landmarks[264][1]) / 2)
        
        # 변형 적용
        for source_landmark, target_point in [
            (landmark_33, mid_34_162),
            (landmark_359, mid_368_264)
        ]:
            distance = math.sqrt((source_landmark[0] - target_point[0])**2 + 
                               (source_landmark[1] - target_point[1])**2)
            pull_distance = distance * config['pull_ratio']
            
            dx = target_point[0] - source_landmark[0]
            dy = target_point[1] - source_landmark[1]
            norm = math.sqrt(dx**2 + dy**2)
            
            if norm > 0:
                dx = (dx / norm) * pull_distance
                dy = (dy / norm) * pull_distance
                
                target_x = source_landmark[0] + dx
                target_y = source_landmark[1] + dy
                
                result_image = apply_pull_warp(
                    result_image,
                    source_landmark[0], source_landmark[1],
                    target_x, target_y,
                    influence_radius, config['strength'],
                    config.get('ellipse_ratio')
                )
    
    return result_image


async def get_gpt_beauty_analysis(before_analysis: Dict[str, Any], after_analysis: Dict[str, Any], score_changes: Dict[str, float]) -> Dict[str, Any]:
    """GPT-4o mini를 사용한 뷰티 분석 비교"""
    try:
        # 시스템 프롬프트 정의
        system_prompt = """
당신은 전문적인 뷰티 컨설턴트이자 성형외과 상담 전문가입니다. 
얼굴 변형 전후의 뷰티 점수를 분석하고, 개선사항과 추천사항을 제공해주세요.

분석 기준:
- 가로 황금비율 (verticalScore): 얼굴의 가로 비율 균형
- 세로 대칭성 (horizontalScore): 얼굴의 세로 대칭성
- 하관 조화 (lowerFaceScore): 하관부 조화로움
- 전체 대칭성 (symmetry): 좌우 대칭성
- 눈 (eyeScore): 눈의 형태와 위치
- 코 (noseScore): 코의 형태와 비율
- 입술 (lipScore): 입술의 형태와 비율
- 턱 곡률 (jawScore): 턱선의 각도와 곡률

응답은 반드시 한국어로, 친근하면서도 전문적인 톤으로 작성해주세요.
"""

        # 점수 변화 요약
        changes_summary = []
        for key, change in score_changes.items():
            if abs(change) > 0.5:  # 0.5점 이상 변화만 포함
                direction = "상승" if change > 0 else "하락"
                changes_summary.append(f"{key}: {change:.1f}점 {direction}")

        # 안전한 점수 추출 함수
        def get_score(analysis, key, default=0):
            value = analysis.get(key, default)
            if isinstance(value, dict):
                return value.get('score', default)
            return value if isinstance(value, (int, float)) else default

        user_prompt = f"""
뷰티 시술 전후 분석 결과:

【시술 전 점수】
- 종합점수: {get_score(before_analysis, 'overallScore'):.1f}점
- 가로 황금비율: {get_score(before_analysis, 'verticalScore'):.1f}점
- 세로 대칭성: {get_score(before_analysis, 'horizontalScore'):.1f}점
- 하관 조화: {get_score(before_analysis, 'lowerFaceScore'):.1f}점
- 전체 대칭성: {get_score(before_analysis, 'symmetry'):.1f}점
- 눈: {get_score(before_analysis, 'eyeScore'):.1f}점
- 코: {get_score(before_analysis, 'noseScore'):.1f}점
- 입술: {get_score(before_analysis, 'lipScore'):.1f}점
- 턱 곡률: {get_score(before_analysis, 'jawScore'):.1f}점

【시술 후 점수】
- 종합점수: {get_score(after_analysis, 'overallScore'):.1f}점
- 가로 황금비율: {get_score(after_analysis, 'verticalScore'):.1f}점
- 세로 대칭성: {get_score(after_analysis, 'horizontalScore'):.1f}점
- 하관 조화: {get_score(after_analysis, 'lowerFaceScore'):.1f}점
- 전체 대칭성: {get_score(after_analysis, 'symmetry'):.1f}점
- 눈: {get_score(after_analysis, 'eyeScore'):.1f}점
- 코: {get_score(after_analysis, 'noseScore'):.1f}점
- 입술: {get_score(after_analysis, 'lipScore'):.1f}점
- 턱 곡률: {get_score(after_analysis, 'jawScore'):.1f}점

【주요 변화】
{', '.join(changes_summary) if changes_summary else '큰 변화 없음'}

다음 형식으로 분석해주세요:

1. 전반적인 변화 요약 (2-3문장)
2. 항목별 상세 분석 (개선된 부분, 아쉬운 부분)
3. 추가 개선 추천사항 (3-4개의 구체적인 제안)

친근하고 격려적인 톤으로, 하지만 전문적인 조언을 포함해서 작성해주세요.
"""

        # GPT-4o mini 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        analysis_text = response.choices[0].message.content or "분석 중 오류가 발생했습니다."

        # 추천사항 추출 (간단한 파싱)
        recommendations = []
        if "추천사항" in analysis_text or "제안" in analysis_text:
            lines = analysis_text.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ["추천", "제안", "권장", "고려"]):
                    clean_line = line.strip().lstrip('-').lstrip('*').lstrip('•').strip()
                    if len(clean_line) > 10:  # 의미있는 길이의 추천사항만
                        recommendations.append(clean_line)

        # 기본 추천사항이 없으면 생성
        if not recommendations:
            if score_changes.get('overall', 0) > 0:
                recommendations = [
                    "현재 개선이 잘 되고 있습니다. 이 방향으로 계속 진행하시는 것을 추천합니다.",
                    "다른 부위와의 조화를 고려한 추가적인 미세 조정을 고려해보세요.",
                    "정기적인 재측정을 통해 변화 과정을 모니터링하세요."
                ]
            else:
                recommendations = [
                    "현재 설정을 재검토하고 다른 접근 방식을 시도해보세요.",
                    "전문가와 상담하여 맞춤형 개선 방안을 찾아보시기 바랍니다.",
                    "단계적인 접근으로 자연스러운 변화를 추구하세요."
                ]

        return {
            "analysis": analysis_text,
            "recommendations": recommendations[:4]  # 최대 4개까지
        }

    except Exception as e:
        print(f"GPT 분석 오류: {e}")
        # 폴백 응답
        return {
            "analysis": "시술 전후 분석이 완료되었습니다. 전문적인 분석을 위해 잠시 후 다시 시도해주세요.",
            "recommendations": [
                "변화된 부분을 꼼꼼히 관찰해보세요.",
                "만족스러운 결과라면 현재 상태를 유지하시고, 추가 개선이 필요하다면 단계적으로 접근하세요.",
                "정기적인 재진단을 통해 지속적인 개선을 추구하세요."
            ]
        }


async def get_gpt_initial_beauty_analysis(beauty_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """GPT-4o mini를 사용한 기초 뷰티스코어 분석"""
    print(f"🔍 GPT 분석 함수 호출됨")
    try:
        # 시스템 프롬프트 정의 - 분석과 구체적 실천 방법 연결
        system_prompt = """
당신은 뷰티 분석과 구체적 실천 방법 전문가입니다. 

**목표**: 분석한 수치적 결과를 바탕으로 구체적이고 실천 가능한 개선 방법을 제시

**응답 구조**:
1. **간단한 분석 요약** (2-3줄)
2. **분석 결과** (주요 강점과 개선점을 수치와 함께)
3. **구체적 실천 방법 3가지** (분석에서 언급한 개선점과 연결)

**실천 방법 형식** (각 항목마다):
- 🎯 **개선 목표**: [분석에서 언급한 구체적 수치] → [목표 수치]
- 💪 **운동/습관**: 매일 [시간]분 [구체적 방법]
추천 사이트: [실제 사용 가능한 사이트명](https://www.실제URL.com)
- 🏥 **전문 관리**: [시술명] [예상비용] [효과 설명]  
추천 병원: [실제 병원명](https://www.실제병원URL.com)

**중요**: 추천하는 모든 사이트와 병원 URL은 실제로 존재하고 접속 가능한 곳만 포함하세요.
- 운동/습관: YouTube 채널, 피트니스 앱, 건강 정보 사이트 등 실제 이용 가능한 곳
- 전문 관리: 실제 성형외과, 피부과, 에스테틱 클리닉 등 공식 홈페이지

**필수 요구사항**:
- 분석에서 언급한 정확한 수치를 반드시 포함
- 각 개선점마다 운동+전문관리 모두 제시
- 구체적 시간, 비용, 방법 명시
"""

        # 안전한 점수 추출 함수
        def get_score(analysis, key, default=0):
            value = analysis.get(key, default)
            if isinstance(value, dict):
                return value.get('score', default)
            return value if isinstance(value, (int, float)) else default

        # 실제 측정된 주요 얼굴 비율 분석만 포함 (눈/코/입술 제외)
        main_scores = {
            'overall': get_score(beauty_analysis, 'overallScore'),
            'vertical': get_score(beauty_analysis, 'verticalScore'),
            'horizontal': get_score(beauty_analysis, 'horizontalScore'),
            'lowerFace': get_score(beauty_analysis, 'lowerFaceScore'),
            'symmetry': get_score(beauty_analysis, 'symmetry'),
            'jaw': get_score(beauty_analysis, 'jawScore'),
        }

        # 강점 항목 (80점 이상)
        strengths = []
        # 개선 영역 (70점 미만)
        improvement_areas = []
        
        score_names = {
            'vertical': '가로 황금비율',
            'horizontal': '세로 대칭성', 
            'lowerFace': '하관 조화',
            'symmetry': '전체 대칭성',
            'jaw': '턱 곡률'
        }
        
        for key, score in main_scores.items():
            if key == 'overall':
                continue
            name = score_names.get(key, key)
            if score >= 80:
                strengths.append(f"{name} ({score:.1f}점)")
            elif score < 70:
                improvement_areas.append(f"{name} ({score:.1f}점)")

        # 상세 분석 정보 추출
        def get_detailed_info(key):
            value = beauty_analysis.get(key, {})
            if isinstance(value, dict):
                return value
            return {}

        vertical_info = get_detailed_info('verticalScore')
        horizontal_info = get_detailed_info('horizontalScore') 
        lowerface_info = get_detailed_info('lowerFaceScore')
        jaw_info = get_detailed_info('jawScore')

        # 상세 점수와 비율 정보 구성
        detailed_analysis = []
        
        # 가로 황금비율 (5구간 퍼센트)
        if main_scores['vertical'] >= 10:
            analysis_text = f"가로 황금비율: {main_scores['vertical']:.1f}점"
            if 'percentages' in vertical_info and vertical_info['percentages']:
                percentages = vertical_info['percentages']
                sections = ['왼쪽바깥', '왼쪽눈', '미간', '오른쪽눈', '오른쪽바깥']
                percent_details = []
                for i, pct in enumerate(percentages[:5]):
                    percent_details.append(f"{sections[i]} {pct:.1f}%")
                analysis_text += f" (구간별: {', '.join(percent_details)})"
            detailed_analysis.append(analysis_text)
        
        # 세로 대칭성 (2구간 퍼센트)
        if main_scores['horizontal'] >= 10:
            analysis_text = f"세로 대칭성: {main_scores['horizontal']:.1f}점"
            if 'upperPercentage' in horizontal_info and 'lowerPercentage' in horizontal_info:
                upper = horizontal_info['upperPercentage']
                lower = horizontal_info['lowerPercentage']
                analysis_text += f" (눈~코 {upper:.1f}%, 코~턱 {lower:.1f}%)"
            detailed_analysis.append(analysis_text)
        
        # 하관 조화 (2구간 퍼센트)
        if main_scores['lowerFace'] >= 10:
            analysis_text = f"하관 조화: {main_scores['lowerFace']:.1f}점"
            if 'upperPercentage' in lowerface_info and 'lowerPercentage' in lowerface_info:
                upper = lowerface_info['upperPercentage']
                lower = lowerface_info['lowerPercentage']
                analysis_text += f" (인중 {upper:.1f}%, 입~턱 {lower:.1f}%)"
            detailed_analysis.append(analysis_text)
        
        # 전체 대칭성
        if main_scores['symmetry'] >= 10:
            detailed_analysis.append(f"전체 대칭성: {main_scores['symmetry']:.1f}점")
        
        # 턱 곡률 (각도 정보)
        if main_scores['jaw'] >= 10:
            analysis_text = f"턱 곡률: {main_scores['jaw']:.1f}점"
            if 'gonialAngle' in jaw_info and 'cervicoMentalAngle' in jaw_info:
                gonial = jaw_info['gonialAngle']
                cervico = jaw_info['cervicoMentalAngle']
                analysis_text += f" (하악각 {gonial:.1f}°, 턱목각 {cervico:.1f}°)"
            detailed_analysis.append(analysis_text)
        
        # 개선 포인트만 추출 (이상적 범위에서 벗어난 특징적인 부분)
        improvement_points = []
        
        # 가로 황금비율 체크 (20%에서 3% 이상 벗어난 경우)
        if 'percentages' in vertical_info and vertical_info['percentages']:
            percentages = vertical_info['percentages']
            sections = ['왼쪽바깥', '왼쪽눈', '미간', '오른쪽눈', '오른쪽바깥']
            for i, pct in enumerate(percentages[:5]):
                diff = abs(pct - 20.0)
                if diff > 3.0:
                    improvement_points.append(f"{sections[i]} {pct:.1f}% (이상 20%)")
        
        # 세로 대칭성 체크 (50:50에서 3% 이상 벗어난 경우)
        if 'upperPercentage' in horizontal_info and 'lowerPercentage' in horizontal_info:
            upper = horizontal_info['upperPercentage']
            lower = horizontal_info['lowerPercentage']
            if abs(upper - 50.0) > 3.0:
                improvement_points.append(f"상안면 {upper:.1f}% (이상 50%)")
        
        # 하관 조화 체크 (33:67에서 벗어난 경우)
        if 'upperPercentage' in lowerface_info and 'lowerPercentage' in lowerface_info:
            upper = lowerface_info['upperPercentage']
            lower = lowerface_info['lowerPercentage']
            if abs(upper - 33.0) > 3.0:
                improvement_points.append(f"인중 {upper:.1f}% (이상 33%)")
        
        # 턱 곡률 체크 (90-120도 범위 벗어난 경우)
        if 'gonialAngle' in jaw_info:
            gonial = jaw_info['gonialAngle']
            if gonial < 90 or gonial > 120:
                improvement_points.append(f"하악각 {gonial:.1f}° (이상 90-120°)")

        user_prompt = f"""
측정 결과: 종합 {main_scores['overall']:.1f}점

강점 항목: {', '.join(strengths) if strengths else '균형 잡힌 전체적 비율'}
개선 항목: {', '.join(improvement_areas) if improvement_areas else '없음'}

특징적 측정값:
{chr(10).join(f"- {point}" for point in improvement_points) if improvement_points else "- 전체적으로 이상적인 비율 유지"}

다음 3개 항목으로 분석해주세요:

1. 🌟 내 얼굴의 좋은 점
측정 결과 중 이상적인 범위에 있거나 매력적인 부분을 구체적 수치와 함께 설명해주세요.

2. 📊 개선이 필요한 부분  
이상적 범위에서 벗어난 부분을 구체적 수치와 함께 쉽게 설명해주세요.
(예: "하악각이 133°로 이상적 범위 90-120°보다 커서 턱선이 부드러운 편이에요")

3. 💡 개선 후 기대효과
개선되면 어떤 매력적인 변화가 있을지 희망적으로 설명해주세요.

---

위 2번에서 언급한 개선 필요 부분을 정확히 참조하여 구체적 실천 방법을 제시해주세요.

각 개선점마다 다음 형식으로:
🎯 **[2번에서 언급한 구체적 문제]** 개선
💪 **운동/습관**: 매일 [시간]분 [구체적 방법] + 추천 사이트
🏥 **전문 관리**: [시술명] [예상비용] [효과]

반드시 2번 분석의 구체적 수치와 문제점을 참조해서 연결해주세요.
"""

        # GPT-4o mini 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1200,
            temperature=0.7
        )

        analysis_text = response.choices[0].message.content or "분석 중 오류가 발생했습니다."

        # 추천사항, 강점, 개선영역 추출
        recommendations = []
        strengths_list = []
        improvement_list = []

        # GPT 텍스트에서 실천 방법 부분만 추출 (--- 이후 전체 내용)
        text_parts = analysis_text.split('---')
        
        if len(text_parts) >= 2:
            # --- 이후의 모든 내용을 실천 방법으로 사용
            practice_section = text_parts[1].strip()
            
            # "### 구체적 실천 방법" 제거하고 실제 내용만 추출
            practice_lines = practice_section.split('\n')
            cleaned_lines = []
            
            for line in practice_lines:
                line = line.strip()
                if not line:
                    cleaned_lines.append('')  # 빈 줄도 유지
                    continue
                    
                # 안내 문구나 형식 설명 건너뛰기 (### 제목은 제거)
                if any(skip_text in line for skip_text in [
                    "위 2번에서 언급한", "각 개선점마다", "다음 형식으로", 
                    "반드시 2번 분석", "정확히 참조"
                ]) or line.startswith('### 구체적 실천 방법'):
                    continue
                
                # 실제 내용만 포함 (모든 🎯, 💪, 🏥 내용과 일반 텍스트)
                cleaned_lines.append(line)
            
            # 실천 방법 전체를 하나의 문자열로 합치기 (Frontend에서 그대로 표시)
            if cleaned_lines:
                full_practice_content = '\n'.join(cleaned_lines).strip()
                recommendations = [full_practice_content]  # 전체 내용을 하나의 요소로
                
            print(f"🔍 Backend recommendations 길이: {len(recommendations[0]) if recommendations else 0}자")
            print(f"🔍 Backend recommendations 샘플: {recommendations[0][:100] if recommendations else 'None'}...")
        else:
            print(f"🔍 Backend GPT 응답에 --- 구분자 없음: {analysis_text[:200]}...")
        
        # 기존 분석 내용 추출 (1, 2, 3번 섹션에서)
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 섹션 구분
            if any(keyword in line for keyword in ["🌟", "좋은 점", "강점"]):
                current_section = "strengths"
                continue
            elif any(keyword in line for keyword in ["📊", "개선이 필요한", "개선 필요"]):
                current_section = "improvements"
                continue
            elif "💡" in line or "기대효과" in line:
                current_section = "effects"
                continue
            elif "---" in line:
                # 실천 방법 섹션 시작하면 분석 파싱 종료
                break
            
            # 각 섹션 내용 추출
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*') or 
                        any(char.isdigit() for char in line[:3])):
                clean_line = line.lstrip('-').lstrip('*').lstrip('•').strip()
                # 번호 제거 (1., 2., 3. 등)
                if clean_line and clean_line[0].isdigit() and '.' in clean_line[:5]:
                    clean_line = clean_line.split('.', 1)[1].strip()
                
                if current_section == "strengths" and len(clean_line) > 10:
                    strengths_list.append(clean_line)
                elif current_section == "improvements" and len(clean_line) > 10:
                    improvement_list.append(clean_line)

        # 기본값 설정
        if not recommendations:
            if main_scores['overall'] >= 80:
                recommendations = [
                    "현재 매우 균형잡힌 아름다운 얼굴을 가지고 계시네요.",
                    "자연스러운 메이크업으로 본인의 매력을 더욱 부각시켜보세요.",
                    "건강한 라이프스타일을 유지하시면 자연스러운 아름다움이 지속될 것입니다."
                ]
            elif main_scores['overall'] >= 70:
                recommendations = [
                    "이미 좋은 기본기를 가지고 계시니 자신감을 가지세요.",
                    "포인트 메이크업으로 개성을 표현해보시는 것을 추천합니다.",
                    "규칙적인 스킨케어로 피부 상태를 개선해보세요."
                ]
            else:
                recommendations = [
                    "모든 사람은 고유한 아름다움을 가지고 있습니다.",
                    "자신만의 매력적인 스타일을 찾아보세요.",
                    "단계적인 관리를 통해 점진적인 개선을 추구하시면 좋을 것 같습니다."
                ]

        if not strengths_list:
            strengths_list = [item for item in strengths] if strengths else ["고유한 개성과 매력"]

        if not improvement_list:
            improvement_list = [item for item in improvement_areas] if improvement_areas else []

        result = {
            "analysis": analysis_text,
            "recommendations": recommendations[:4],
            "strengths": strengths_list[:3],
            "improvement_areas": improvement_list[:3]
        }
        print(f"🔍 Backend GPT 응답: {result}")
        return result

    except Exception as e:
        print(f"기초 뷰티스코어 GPT 분석 오류: {e}")
        # 폴백 응답
        return {
            "analysis": "뷰티 분석이 완료되었습니다. 여러분만의 고유한 매력을 발견하고 자신감을 가지세요!",
            "recommendations": [
                "자신만의 매력을 찾아 표현해보세요.",
                "건강한 라이프스타일을 유지하시면 자연스러운 아름다움이 빛날 것입니다.",
                "정기적인 관리로 꾸준한 개선을 추구해보세요."
            ],
            "strengths": ["고유한 개성"],
            "improvement_areas": []
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)