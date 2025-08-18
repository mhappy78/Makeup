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
}