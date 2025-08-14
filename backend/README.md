# Face Simulator Backend API

FastAPI 기반 얼굴 성형 시뮬레이터 백엔드 API

## 주요 기능

- **이미지 업로드**: 얼굴 이미지 업로드 및 임시 저장
- **얼굴 랜드마크 검출**: MediaPipe를 사용한 468개 얼굴 랜드마크 검출
- **자유 변형**: Pull/Push/Expand/Shrink 워핑 기능
- **이미지 다운로드**: 변형된 이미지 다운로드
- **CORS 지원**: Flutter 웹/앱에서 접근 가능

## 설치 및 실행

### 1. 의존성 설치
```bash
cd backend
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
python run.py
```

### 3. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### 기본
- `GET /`: 서버 상태 확인

### 이미지 처리
- `POST /upload-image`: 이미지 업로드
- `GET /landmarks/{image_id}`: 얼굴 랜드마크 검출
- `POST /warp-image`: 이미지 워핑 적용
- `GET /download-image/{image_id}`: 이미지 다운로드
- `DELETE /image/{image_id}`: 임시 이미지 삭제

## 요청/응답 예시

### 이미지 업로드
```bash
curl -X POST "http://localhost:8000/upload-image" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@face.jpg"
```

### 워핑 적용
```json
{
  "image_id": "uuid-string",
  "start_x": 100.0,
  "start_y": 200.0,
  "end_x": 120.0,
  "end_y": 180.0,
  "influence_radius": 80.0,
  "strength": 1.0,
  "mode": "pull"
}
```

## 워핑 모드
- `pull`: 당기기
- `push`: 밀어내기  
- `expand`: 확대
- `shrink`: 축소

## 기술 스택
- **FastAPI**: 웹 프레임워크
- **MediaPipe**: 얼굴 랜드마크 검출
- **OpenCV**: 이미지 처리 및 워핑
- **PIL/Pillow**: 이미지 변환
- **NumPy**: 수치 연산