# Face Simulator Frontend

Flutter로 개발된 얼굴 성형 시뮬레이터 웹 프론트엔드입니다.

## 주요 기능

- **이미지 업로드**: 드래그 앤 드롭 또는 파일 선택으로 얼굴 사진 업로드
- **자동 얼굴 인식**: MediaPipe 기반 468개 얼굴 랜드마크 자동 검출
- **실시간 변형**: 4가지 모드(당기기/밀어내기/확대/축소)로 실시간 얼굴 변형
- **직관적 UI**: Material Design 3 기반 현대적이고 반응형 인터페이스

## 기술 스택

- **Flutter 3.x**: 크로스 플랫폼 UI 프레임워크
- **Provider**: 상태 관리
- **Dio**: HTTP 클라이언트
- **Material Design 3**: 디자인 시스템

## 프로젝트 구조

```
lib/
├── main.dart                 # 앱 진입점
├── models/                   # 데이터 모델
│   └── app_state.dart       # 앱 전역 상태
├── services/                 # 서비스 레이어
│   └── api_service.dart     # FastAPI 백엔드 통신
├── screens/                  # 화면 컴포넌트
│   └── home_screen.dart     # 메인 홈 화면
└── widgets/                  # 재사용 가능한 위젯
    ├── image_upload_widget.dart      # 이미지 업로드
    ├── image_display_widget.dart     # 이미지 표시 및 상호작용
    ├── landmark_controls_widget.dart # 랜드마크 컨트롤
    └── warp_controls_widget.dart     # 워핑 도구 컨트롤
```

## 설치 및 실행

### 1. Flutter 설치
[Flutter 공식 문서](https://flutter.dev/docs/get-started/install) 참조

### 2. 의존성 설치
```bash
cd frontend
flutter pub get
```

### 3. 웹 서버 실행
```bash
flutter run -d web-server --web-port 3000
```

### 4. 개발 모드 실행 (Hot Reload)
```bash
flutter run -d chrome
```

## API 연동

FastAPI 백엔드와 통신하여 다음 기능을 제공합니다:

### 엔드포인트
- `POST /upload-image`: 이미지 업로드
- `GET /landmarks/{id}`: 얼굴 랜드마크 검출
- `POST /warp-image`: 이미지 워핑 적용
- `GET /download-image/{id}`: 변형된 이미지 다운로드

### 설정
기본적으로 `http://localhost:8080`으로 백엔드에 연결합니다.
다른 주소를 사용할 경우 `lib/services/api_service.dart`에서 `baseUrl`을 수정하세요.

## 주요 컴포넌트

### AppState
- 앱의 전역 상태 관리
- 이미지, 랜드마크, 워핑 설정 등의 상태 보관
- Provider 패턴으로 상태 변경 알림

### ImageDisplayWidget
- 이미지 표시 및 터치/마우스 상호작용 처리
- 랜드마크 오버레이 렌더링
- 워핑 도구 시각화 (영향 반경, 드래그 벡터 등)

### WarpControlsWidget
- 4가지 워핑 모드 선택
- 영향 반경 및 변형 강도 조절
- 실시간 매개변수 업데이트

## 빌드

### 웹 배포용 빌드
```bash
flutter build web
```

빌드된 파일은 `build/web/` 디렉토리에 생성됩니다.

### 개발 설정
```bash
# 코드 분석
flutter analyze

# 테스트 실행
flutter test

# 의존성 업데이트
flutter pub upgrade
```

## 사용법

1. **이미지 업로드**: "이미지 선택" 버튼을 클릭하거나 파일을 드래그하여 얼굴 사진을 업로드합니다.

2. **랜드마크 확인**: 업로드 후 자동으로 얼굴 랜드마크가 검출되며, 토글을 통해 표시/숨김이 가능합니다.

3. **변형 적용**: 
   - 원하는 변형 모드(당기기/밀어내기/확대/축소)를 선택
   - 영향 반경과 강도를 조절
   - 이미지에서 마우스로 드래그하여 변형 적용

4. **결과 저장**: "결과 저장" 버튼을 클릭하여 변형된 이미지를 다운로드합니다.

## 브라우저 지원

- Chrome (권장)
- Firefox
- Safari
- Edge

모든 주요 모던 브라우저에서 동작하며, 웹 표준을 준수합니다.