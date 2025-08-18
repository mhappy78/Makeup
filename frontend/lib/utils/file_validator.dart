import 'dart:typed_data';
import '../config/app_constants.dart';

/// 파일 검증 유틸리티
class FileValidator {
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
  }
}