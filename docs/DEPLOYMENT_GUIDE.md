# 배포 가이드

## 개요

자연스러운 메이크업 & 성형 시뮬레이션 시스템의 배포 가이드입니다. 이 문서는 시스템을 다양한 환경에 배포하는 방법을 설명합니다.

## 배포 준비

### 1. 시스템 요구사항

#### 최소 요구사항
- **운영체제**: Windows 10, macOS 10.14, Ubuntu 18.04 이상
- **Python**: 3.8 이상
- **메모리**: 4GB RAM 이상
- **저장공간**: 2GB 이상
- **네트워크**: 인터넷 연결 (초기 설치 시)

#### 권장 요구사항
- **운영체제**: Windows 11, macOS 12, Ubuntu 20.04 이상
- **Python**: 3.9 이상
- **메모리**: 8GB RAM 이상
- **저장공간**: 5GB 이상
- **GPU**: CUDA 지원 GPU (성능 향상)
- **카메라**: 웹캠 (실시간 기능 사용시)

### 2. 배포 패키지 생성

#### 자동 배포 패키지 생성
```bash
python deployment_package.py
```

#### 사용자 정의 배포 패키지 생성
```bash
python deployment_package.py --output custom_dist --project-root .
```

#### 생성되는 파일들
- `natural-makeup-surgery-simulation-v1.0.0.zip`: 배포 패키지
- `deployment_report.json`: 배포 보고서
- `package_info.json`: 패키지 정보

## 배포 방법

### 1. 로컬 설치 배포

#### Windows
1. ZIP 파일 압축 해제
2. `start.bat` 실행
3. 또는 `python launch.py` 실행

#### Linux/Mac
1. ZIP 파일 압축 해제
2. `chmod +x start.sh` (권한 부여)
3. `./start.sh` 실행
4. 또는 `python3 launch.py` 실행

### 2. Python 패키지 설치

#### pip를 통한 설치
```bash
# 로컬 패키지 설치
pip install -e .

# 또는 setup.py 사용
python setup.py install
```

#### 개발 모드 설치
```bash
pip install -e . --user
```

### 3. Docker 배포 (선택사항)

#### Dockerfile 생성
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# 포트 노출
EXPOSE 8501

# 실행 명령
CMD ["streamlit", "run", "ui/main_interface.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Docker 이미지 빌드 및 실행
```bash
# 이미지 빌드
docker build -t natural-beauty-sim .

# 컨테이너 실행
docker run -p 8501:8501 natural-beauty-sim
```

### 4. 웹 서버 배포

#### Streamlit Cloud 배포
1. GitHub 저장소에 코드 업로드
2. Streamlit Cloud에서 앱 연결
3. 자동 배포 및 URL 생성

#### Heroku 배포
```bash
# Heroku CLI 설치 후
heroku create natural-beauty-sim
git push heroku main
```

## 배포 검증

### 1. 자동 검증 실행
```bash
python final_integration_test.py
```

### 2. 품질 보증 테스트
```bash
python quality_assurance_runner.py
```

### 3. 수동 검증 체크리스트

#### 기능 검증
- [ ] 애플리케이션 정상 시작
- [ ] 이미지 업로드 기능
- [ ] 실시간 카메라 기능
- [ ] 얼굴 감지 및 랜드마크 추출
- [ ] 메이크업 효과 적용
- [ ] 성형 시뮬레이션 적용
- [ ] 이미지 저장 기능
- [ ] 갤러리 기능

#### 성능 검증
- [ ] 얼굴 감지 속도 (< 100ms)
- [ ] 메이크업 적용 속도 (< 500ms)
- [ ] 성형 시뮬레이션 속도 (< 1000ms)
- [ ] 메모리 사용량 (< 500MB)
- [ ] CPU 사용률 (< 80%)

#### 호환성 검증
- [ ] Windows 10/11 호환성
- [ ] macOS 호환성
- [ ] Ubuntu/Linux 호환성
- [ ] 다양한 이미지 형식 지원
- [ ] 다양한 해상도 지원

## 문제 해결

### 일반적인 배포 문제

#### 1. Python 버전 호환성
```bash
# Python 버전 확인
python --version

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### 2. 의존성 설치 실패
```bash
# pip 업그레이드
pip install --upgrade pip

# 캐시 없이 설치
pip install -r requirements.txt --no-cache-dir

# 개별 패키지 설치
pip install opencv-python mediapipe pillow numpy streamlit
```

#### 3. OpenCV 설치 문제
```bash
# 시스템별 OpenCV 설치
# Ubuntu/Debian
sudo apt-get install python3-opencv

# macOS (Homebrew)
brew install opencv

# Windows
pip install opencv-python-headless
```

#### 4. MediaPipe 설치 문제
```bash
# MediaPipe 재설치
pip uninstall mediapipe
pip install mediapipe --no-deps
pip install opencv-python numpy pillow
```

#### 5. 카메라 접근 권한
- **Windows**: 설정 > 개인정보 > 카메라 권한 확인
- **macOS**: 시스템 환경설정 > 보안 및 개인정보 > 카메라 권한 확인
- **Linux**: 사용자를 video 그룹에 추가
  ```bash
  sudo usermod -a -G video $USER
  ```

#### 6. 포트 충돌 (Streamlit)
```bash
# 다른 포트 사용
streamlit run ui/main_interface.py --server.port 8502
```

### 성능 최적화

#### 1. GPU 가속 활성화
```bash
# CUDA 설치 확인
nvidia-smi

# GPU 버전 OpenCV 설치
pip install opencv-contrib-python
```

#### 2. 메모리 최적화
- 이미지 해상도 조정
- 프레임 스킵 설정 증가
- 불필요한 효과 비활성화

#### 3. CPU 최적화
- 멀티스레딩 활성화
- 프로세스 우선순위 조정

## 모니터링 및 유지보수

### 1. 로그 모니터링
```bash
# 애플리케이션 로그 확인
tail -f application.log

# 시스템 리소스 모니터링
htop  # Linux/Mac
```

### 2. 자동 업데이트
```bash
# Git을 통한 업데이트
git pull origin main
pip install -r requirements.txt --upgrade
```

### 3. 백업 및 복구
```bash
# 설정 백업
cp -r ~/.streamlit backup/
cp -r gallery/ backup/

# 복구
cp -r backup/.streamlit ~/
cp -r backup/gallery/ .
```

## 보안 고려사항

### 1. 네트워크 보안
- HTTPS 사용 (프로덕션 환경)
- 방화벽 설정
- 접근 제어 구현

### 2. 데이터 보안
- 사용자 이미지 암호화
- 임시 파일 자동 삭제
- 개인정보 보호 정책 준수

### 3. 애플리케이션 보안
- 입력 검증 강화
- 오류 메시지 최소화
- 정기적인 보안 업데이트

## 라이선스 및 법적 고려사항

### 1. 오픈소스 라이선스
- MIT 라이선스 적용
- 의존성 라이브러리 라이선스 확인
- 상업적 사용 시 라이선스 검토

### 2. 개인정보 보호
- GDPR 준수 (유럽 사용자)
- 개인정보 처리 방침 작성
- 사용자 동의 절차 구현

### 3. 의료기기 규제
- 의료 목적 사용 시 규제 확인
- 면책 조항 포함
- 전문의 상담 권고

## 지원 및 문의

### 기술 지원
- **이메일**: support@naturalbeauty.ai
- **GitHub Issues**: https://github.com/naturalbeauty/issues
- **문서**: https://docs.naturalbeauty.ai

### 커뮤니티
- **Discord**: https://discord.gg/naturalbeauty
- **Reddit**: r/NaturalBeautyAI
- **Stack Overflow**: #natural-beauty-simulation

## 버전 관리

### 현재 버전: 1.0.0
- 초기 릴리스
- 기본 메이크업 및 성형 시뮬레이션 기능
- Streamlit 기반 웹 인터페이스

### 향후 계획
- **1.1.0**: 모바일 지원 추가
- **1.2.0**: AI 추천 시스템
- **2.0.0**: 3D 렌더링 지원

---

이 가이드는 지속적으로 업데이트됩니다. 최신 버전은 공식 문서를 참조하세요.