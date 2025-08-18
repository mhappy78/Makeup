<<<<<<< HEAD
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
=======
import 'package:flutter/material.dart';

/// BeautyGen 앱 상수 정의
class AppConstants {
  // 색상 테마
  static const Color primaryColor = Color(0xFF6366F1);
  
  // 앱 정보
  static const String appName = 'BeautyGen';
  static const String appDescription = 'AI 기반 뷰티 분석 & 시뮬레이터';
  
  // API 설정
  static const String apiBaseUrl = 'http://localhost:8080';
  
  // 이미지 설정
  static const int maxImageSizeMB = 10;
  static const List<String> supportedImageFormats = ['jpg', 'jpeg', 'png', 'webp'];
  
  // 애니메이션 설정
  static const Duration defaultAnimationDuration = Duration(milliseconds: 300);
  static const Duration longAnimationDuration = Duration(milliseconds: 500);
  
  // UI 설정
  static const double defaultBorderRadius = 12.0;
  static const double smallBorderRadius = 8.0;
  static const double largeBorderRadius = 16.0;
  
  static const EdgeInsets defaultPadding = EdgeInsets.all(16.0);
  static const EdgeInsets smallPadding = EdgeInsets.all(8.0);
  static const EdgeInsets largePadding = EdgeInsets.all(24.0);
  
  // 반응형 breakpoints
  static const double mobileBreakpoint = 768.0;
  static const double tabletBreakpoint = 1024.0;
  
  // 레이아웃 설정
  static const double desktopControlPanelWidth = 500.0;
  static const double tabBarHeight = 42.0;
  static const double minMobileImageHeight = 600.0;
  static const double floatingButtonTopOffset = 8.0;
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
}