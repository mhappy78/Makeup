import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// 앱 전체 설정 및 테마 관리 클래스
class AppConfig {
  // 앱 기본 정보
  static const String appName = 'BeautyGen';
  static const String version = '1.0.0';
  
  // 색상 테마
  static const Color primaryColor = Color(0xFF6366F1); // 인디고 색상
  static const String fontFamily = 'Malgun Gothic';
  
  /// 라이트 테마 생성
  static ThemeData get lightTheme {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryColor,
        brightness: Brightness.light,
      ),
      useMaterial3: true,
      fontFamily: fontFamily,
      textTheme: GoogleFonts.notoSansKrTextTheme().copyWith(
        // 시스템 폰트를 fallback으로 설정
      ),
    );
  }
  
  /// 다크 테마 생성
  static ThemeData get darkTheme {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryColor,
        brightness: Brightness.dark,
      ),
      useMaterial3: true,
      fontFamily: fontFamily,
      textTheme: GoogleFonts.notoSansKrTextTheme(ThemeData.dark().textTheme).copyWith(
        // 시스템 폰트를 fallback으로 설정
      ),
    );
  }
}