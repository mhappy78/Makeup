from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Tuple
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

class LandmarkResponse(BaseModel):
    landmarks: List[Tuple[float, float]]
    image_width: int
    image_height: int

class ImageResponse(BaseModel):
    image_id: str
    image_data: str  # base64 encoded

    
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
    
    if mode == "pull":
        return apply_pull_warp(image, start_x, start_y, end_x, end_y, influence_radius, strength)
    elif mode == "push":
        return apply_push_warp(image, start_x, start_y, end_x, end_y, influence_radius, strength)
    elif mode == "expand":
        return apply_radial_warp(image, start_x, start_y, influence_radius, strength, expand=True)
    elif mode == "shrink":
        return apply_radial_warp(image, start_x, start_y, influence_radius, strength, expand=False)
    else:
        return image

def apply_pull_warp(image: np.ndarray, start_x: float, start_y: float,
                   end_x: float, end_y: float, influence_radius: float, strength: float) -> np.ndarray:
    """당기기 워핑"""
    img_height, img_width = image.shape[:2]
    
    # 드래그 벡터 (반대 방향)
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
        # 확대: 중심에서 멀어지게
        scale_factor = 1 + strength_factor * (1 - distance / influence_radius)
    else:
        # 축소: 중심으로 가까워지게
        scale_factor = 1 - strength_factor * (1 - distance / influence_radius)
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)