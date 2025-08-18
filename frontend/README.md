# Face Simulator Frontend

Flutter로 개발된 AI 기반 얼굴 분석 및 뷰티 시뮬레이터 웹 프론트엔드입니다.

## 🎯 주요 기능

### 📊 전문적 뷰티 분석
- **실시간 얼굴 랜드마크 검출**: MediaPipe 기반 468개 포인트 정밀 분석
- **종합 뷰티 스코어**: 가중평균 기반 정밀 점수 계산 시스템
- **인터랙티브 애니메이션**: 11개 얼굴 영역별 순차 애니메이션
- **AI 기반 개인 맞춤 추천**: GPT 연동 뷰티 분석 및 조언

### ⚡ 프리셋 가상 시술
- **5가지 시술 타입**: 턱선(3), 앞트임, 뒷트임
- **샷 기반 진행도**: 실제 시술과 유사한 100-500샷 시스템
- **실시간 레이저 효과**: 시술 과정 시각화
- **전후 비교**: Before/After 슬라이더 비교

### 🎨 프리스타일 편집
- **고급 이미지 워핑**: Pull/Push/Expand/Shrink 4모드
- **정밀 제어**: 퍼센트 기반 영향 반경 (0.5%-50%)
- **히스토리 관리**: 최대 20단계 Undo/Redo
- **실시간 프리뷰**: 마우스 호버 시 변형 미리보기

### 📸 스마트 카메라 시스템
- **크로스 플랫폼**: 데스크톱 웹캠, 모바일 전면 카메라
- **3:4 비율 실시간 프리뷰**: 최적 얼굴 촬영 가이드
- **자동 얼굴 크로핑**: 지능형 60% 패딩 처리
- **다중 얼굴 감지**: 자동 최대 얼굴 선택

## 🏗️ 아키텍처

### 프로젝트 구조
```
lib/
├── main.dart                    # 앱 진입점
├── config/                      # 설정 파일
│   ├── animation_constants.dart # 애니메이션 상수
│   ├── app_constants.dart       # 앱 상수
│   └── app_theme.dart          # 테마 설정
├── models/                      # 데이터 모델
│   ├── app_state.dart          # 전역 상태 관리
│   ├── face_regions.dart       # 얼굴 영역 정의
│   └── image_models.dart       # 이미지 관련 모델
├── screens/                     # 화면 컴포넌트
│   └── home_screen.dart        # 메인 홈 화면
├── services/                    # 서비스 레이어
│   ├── api_service.dart        # FastAPI 백엔드 통신
│   └── beauty_analysis_service.dart # 뷰티 분석 로직
├── utils/                       # 유틸리티
│   ├── file_validator.dart     # 파일 검증
│   ├── image_processor.dart    # 이미지 처리
│   └── ui_helpers.dart         # UI 헬퍼
└── widgets/                     # UI 컴포넌트
    ├── beauty_comparison_widget.dart     # 뷰티 비교
    ├── beauty_score_dashboard.dart      # 뷰티 대시보드
    ├── beauty_score_visualizer.dart     # 실시간 시각화
    ├── before_after_comparison.dart     # 전후 비교
    ├── camera_capture_widget.dart       # 카메라 통합
    ├── face_regions_widget.dart         # 얼굴 영역 위젯
    ├── image_display_widget.dart        # 이미지 표시
    ├── image_upload_widget.dart         # 이미지 업로드
    ├── landmark_controls_widget.dart    # 프리셋 컨트롤
    ├── warp_controls_widget.dart        # 워핑 컨트롤
    └── components/                       # 재사용 컴포넌트
        ├── image_container.dart         # 이미지 컨테이너
        ├── logo_widget.dart            # 브랜딩
        ├── photography_tips.dart        # 촬영 가이드
        └── upload_buttons.dart          # 업로드 버튼
```

### 상태 관리
- **Provider 패턴**: 전역 상태 관리
- **AppState 클래스**: 중앙집중식 상태 관리
- **실시간 반응형 UI**: ChangeNotifier 기반

## 🛠️ 기술 스택

**Frontend Framework:**
- Flutter 3.10+ (Cross-platform web application)
- Provider (State management pattern)
- Material Design 3 (UI system)

**Image Processing:**
- MediaPipe (468-point facial landmark detection)
- Image package (Client-side processing)
- Camera package (Webcam/mobile integration)

**Network & APIs:**
- Dio 5.3.2 (HTTP client)
- JSON serialization
- Base64 encoding

## 🚀 개발 및 실행

### Prerequisites
- Flutter SDK 3.10+
- Chrome browser
- Dart SDK (Flutter 포함)

### 개발 환경 설정
```bash
# 의존성 설치
flutter pub get

# 웹 개발 서버 실행
flutter run -d chrome --web-port=3000

# 프로덕션 빌드
flutter build web
```

### 코드 품질 관리
```bash
# 정적 분석
flutter analyze

# 코드 포맷팅
dart format .

# 테스트 실행
flutter test

# 빌드 캐시 정리
flutter clean
```

## 📐 핵심 알고리즘

### 이미지 워핑 공식
```dart
e = ((pow_r - dd) * (pow_r - dd)) / 
    ((pow_r - dd + d_pull * d_pull) * (pow_r - dd + d_pull * d_pull))
```

### 뷰티 스코어 가중치
```dart
final weightedScore = 
    (verticalScore * 0.25) +      // 가로 황금비율 25%
    (horizontalScore * 0.20) +    // 세로 대칭성 20%
    (lowerFaceScore * 0.15) +     // 하관 조화 15%
    (symmetry * 0.15) +           // 기본 대칭성 15%
    (eyeScore * 0.10) +           // 눈 10%
    (noseScore * 0.08) +          // 코 8%
    (lipScore * 0.05) +           // 입술 5%
    (jawScore * 0.02);            // 턱 곡률 2%
```

## 🎨 사용자 인터페이스

### 탭 네비게이션 시스템
- **📊 뷰티스코어**: 전문 분석 대시보드
- **⚡ 프리셋**: 빠른 변형 및 레이저 효과
- **🎨 프리스타일**: 고급 편집 도구

### 반응형 디자인
- 모바일 우선 접근법
- 브라우저별 최적화
- 터치 친화적 인터페이스
- 480x240 로고 브랜딩

## 🔧 성능 최적화

### 상태 관리
- Provider 패턴 기반 중앙집중식 관리
- 메모리 누수 방지 (proper dispose)
- 단일 책임 원칙 준수

### 이미지 처리
- 클라이언트 사이드 3:4 비율 처리
- 최소 600x800 크기 보장
- Base64 인코딩/디코딩 최적화
- 히스토리 관리 (최대 20단계)

### 애니메이션
- 60 FPS 부드러운 애니메이션
- 지능형 시퀀스 관리
- 메모리 효율적인 프레임 제어

## 📱 브라우저 호환성

- ✅ Chrome (권장)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- 📱 모바일 브라우저 지원

## 🤝 개발 가이드라인

### 코딩 규칙
- Material Design 3 가이드라인 준수
- Provider 패턴 활용
- 재사용 가능한 컴포넌트 설계
- 명확한 파일명 및 구조

### 파일 구조 규칙
- 기능별 폴더 분리 (config, models, services, utils, widgets)
- components/ 폴더에 재사용 컴포넌트 배치
- 단일 책임 원칙에 따른 파일 분할
- 명확한 import 경로 설정

### 성능 고려사항
- 불필요한 rebuild 최소화
- 메모리 누수 방지
- 효율적인 애니메이션 관리
- 최적화된 이미지 처리

## 📄 라이선스

이 프로젝트는 교육 및 시연 목적으로 개발되었습니다.