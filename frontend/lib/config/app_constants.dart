/// 앱 전반에 사용되는 상수들
class AppConstants {
  // 워핑 기본값
  static const double defaultInfluenceRadiusPercent = 20.0;
  static const double defaultWarpStrength = 0.1;
  static const double minInfluenceRadius = 0.1;
  static const double maxInfluenceRadius = 50.0;
  
  // 줌 제한
  static const double minZoomScale = 0.5;
  static const double maxZoomScale = 3.0;
  static const double defaultZoomScale = 1.0;
  
  // 프리셋 기본값
  static const Map<String, int> presetDefaultCounters = {
    'lower_jaw': 0,
    'middle_jaw': 0,
    'cheek': 0,
    'front_protusion': 0,
    'back_slit': 0,
  };
  
  static const Map<String, int> presetDefaultSettings = {
    'lower_jaw': 300,      // 100~500샷 (기본값 300)
    'middle_jaw': 300,
    'cheek': 300,
    'front_protusion': 3,  // 1~5%
    'back_slit': 3,        // 1~5%
  };
  
  // 파일 제한
  static const int maxFileSize = 10 * 1024 * 1024; // 10MB
  static const List<String> allowedImageExtensions = ['jpg', 'jpeg', 'png', 'webp'];
  
  // UI 상수
  static const double defaultBorderRadius = 12.0;
  static const double defaultPadding = 16.0;
  static const double defaultMargin = 8.0;
  
  // API 기본값
  static const String defaultBaseUrl = 'http://localhost:8080';
  
  // 탭 인덱스
  static const int beautyScoreTabIndex = 0;
  static const int presetTabIndex = 1;
  static const int freestyleTabIndex = 2;
}