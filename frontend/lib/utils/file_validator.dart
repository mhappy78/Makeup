<<<<<<< HEAD
=======
import 'dart:typed_data';
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
import '../config/app_constants.dart';

/// 파일 검증 유틸리티
class FileValidator {
<<<<<<< HEAD
  /// 파일이 유효한지 검증하고 에러 메시지 반환
  static String? getValidationErrorMessage(String fileName, int fileSize) {
    // 파일 크기 검증
    if (fileSize > AppConstants.maxFileSize) {
      return '파일 크기는 ${AppConstants.maxFileSize ~/ (1024 * 1024)}MB 이하여야 합니다.';
    }

    // 파일 형식 검증
    if (!isValidImageFormat(fileName)) {
      return '지원하지 않는 이미지 형식입니다. ${AppConstants.allowedImageExtensions.join(', ').toUpperCase()} 파일을 선택해주세요.';
    }

    return null; // 유효함
  }

  /// 이미지 형식이 유효한지 확인
  static bool isValidImageFormat(String fileName) {
    final extension = fileName.toLowerCase().split('.').last;
    return AppConstants.allowedImageExtensions.contains(extension);
  }

  /// 파일 크기를 읽기 쉬운 형식으로 변환
  static String formatFileSize(int bytes) {
    if (bytes >= 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    } else if (bytes >= 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    } else {
      return '$bytes B';
    }
=======
  /// 이미지 형식 검증
  static bool isValidImageFormat(String fileName) {
    final extension = fileName.toLowerCase().split('.').last;
    return AppConstants.supportedImageFormats.contains(extension);
  }
  
  /// 파일 크기 검증 (바이트 단위)
  static bool isValidFileSize(Uint8List fileBytes) {
    final maxSizeBytes = AppConstants.maxImageSizeMB * 1024 * 1024;
    return fileBytes.length <= maxSizeBytes;
  }
  
  /// 파일 크기 검증 (길이 단위)
  static bool isValidFileSizeFromLength(int length) {
    final maxSizeBytes = AppConstants.maxImageSizeMB * 1024 * 1024;
    return length <= maxSizeBytes;
  }
  
  /// 검증 결과 메시지 생성
  static String? getValidationErrorMessage(String fileName, int fileSize) {
    if (!isValidImageFormat(fileName)) {
      final supportedFormats = AppConstants.supportedImageFormats
          .map((f) => f.toUpperCase())
          .join(', ');
      return '지원하지 않는 이미지 형식입니다. $supportedFormats 파일을 선택해주세요.';
    }
    
    if (!isValidFileSizeFromLength(fileSize)) {
      return '파일 크기는 ${AppConstants.maxImageSizeMB}MB 이하여야 합니다.';
    }
    
    return null;
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
  }
}