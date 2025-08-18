import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_constants.dart';

/// BeautyGen 앱 테마 설정
class AppTheme {
  /// 라이트 테마
  static ThemeData get lightTheme {
    return _buildTheme(Brightness.light);
  }
  
  /// 다크 테마
  static ThemeData get darkTheme {
    return _buildTheme(Brightness.dark);
  }
  
  /// 공통 테마 빌더
  static ThemeData _buildTheme(Brightness brightness) {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppConstants.primaryColor,
      brightness: brightness,
    );
    
    final textTheme = brightness == Brightness.light
        ? GoogleFonts.notoSansKrTextTheme()
        : GoogleFonts.notoSansKrTextTheme(ThemeData.dark().textTheme);
    
    return ThemeData(
      colorScheme: colorScheme,
      useMaterial3: true,
      textTheme: textTheme,
      
      // 공통 컴포넌트 테마
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
          ),
          padding: AppConstants.defaultPadding,
        ),
      ),
      
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
          ),
          padding: AppConstants.defaultPadding,
        ),
      ),
      
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
          ),
          padding: AppConstants.defaultPadding,
        ),
      ),
      
      cardTheme: CardTheme(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
        ),
        margin: AppConstants.smallPadding,
      ),
      
      dialogTheme: DialogTheme(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppConstants.largeBorderRadius),
        ),
      ),
    );
  }
}