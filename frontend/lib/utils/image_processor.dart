import 'dart:typed_data';
import 'package:image/image.dart' as img;
import 'dart:math' as math;

/// BeautyGen 이미지 처리 유틸리티 클래스
class ImageProcessor {
  
  /// 얼굴 감지 결과를 기반으로 3:4 비율로 크롭하고 밝기 보정
  static Future<Uint8List> processImageWithFaceDetection(
    Uint8List imageBytes, 
    List<dynamic>? landmarks
  ) async {
    final originalImage = img.decodeImage(imageBytes);
    if (originalImage == null) return imageBytes;

    img.Image processedImage = originalImage;

    // 1. 얼굴 기반 크롭 (랜드마크가 있는 경우)
    if (landmarks != null && landmarks.isNotEmpty) {
      processedImage = _cropImageAroundFace(processedImage, landmarks);
    } else {
      // 랜드마크가 없으면 중앙 기준으로 3:4 크롭
      processedImage = _cropImageTo3x4(processedImage);
    }

    // 2. 이미지가 너무 작으면 적당한 크기로 확대
    processedImage = _ensureMinimumSize(processedImage);

    // 3. JPEG로 인코딩 (품질 90%)
    final processedBytes = img.encodeJpg(processedImage, quality: 90);
    return Uint8List.fromList(processedBytes);
  }

  /// 얼굴 랜드마크를 기반으로 얼굴 중심 3:4 크롭
  static img.Image _cropImageAroundFace(img.Image image, List<dynamic> landmarks) {
    // 얼굴 경계 박스 계산
    double minX = double.infinity;
    double maxX = double.negativeInfinity;
    double minY = double.infinity;
    double maxY = double.negativeInfinity;

    for (final landmark in landmarks) {
      double x, y;
      if (landmark is Map<String, dynamic>) {
        x = (landmark['x'] as num).toDouble();
        y = (landmark['y'] as num).toDouble();
      } else {
        // Landmark 객체인 경우
        final landmarkObj = landmark as dynamic;
        x = landmarkObj.x.toDouble();
        y = landmarkObj.y.toDouble();
      }
      
      minX = math.min(minX, x);
      maxX = math.max(maxX, x);
      minY = math.min(minY, y);
      maxY = math.max(maxY, y);
    }

    // 얼굴 크기 계산
    final faceWidth = maxX - minX;
    final faceHeight = maxY - minY;
    final faceCenterX = (minX + maxX) / 2;
    final faceCenterY = (minY + maxY) / 2;

    // 얼굴보다 20% 더 넓은 영역으로 크롭 범위 계산
    final padding = math.max(faceWidth, faceHeight) * 0.6; // 60% 패딩
    final cropWidth = math.max(faceWidth + padding, faceHeight * 0.75); // 최소 3:4 비율 유지
    final cropHeight = cropWidth * 4 / 3; // 3:4 비율

    // 크롭 영역 계산 (얼굴 중심 기준)
    final cropX = math.max(0, (faceCenterX - cropWidth / 2).round());
    final cropY = math.max(0, (faceCenterY - cropHeight / 2).round());
    final finalCropWidth = math.min(cropWidth.round(), image.width - cropX);
    final finalCropHeight = math.min(cropHeight.round(), image.height - cropY);

    // 이미지 크롭
    return img.copyCrop(
      image,
      x: cropX,
      y: cropY,
      width: finalCropWidth,
      height: finalCropHeight,
    );
  }

  /// 중앙 기준 3:4 크롭 (랜드마크가 없는 경우)
  static img.Image _cropImageTo3x4(img.Image image) {
    final originalWidth = image.width;
    final originalHeight = image.height;

    // 3:4 비율 계산
    final targetAspectRatio = 3.0 / 4.0;
    final currentAspectRatio = originalWidth / originalHeight;

    int cropWidth, cropHeight;
    int cropX, cropY;

    if (currentAspectRatio > targetAspectRatio) {
      // 이미지가 더 넓음 - 좌우를 크롭
      cropHeight = originalHeight;
      cropWidth = (originalHeight * targetAspectRatio).round();
      cropX = (originalWidth - cropWidth) ~/ 2;
      cropY = 0;
    } else {
      // 이미지가 더 높음 - 상하를 크롭
      cropWidth = originalWidth;
      cropHeight = (originalWidth / targetAspectRatio).round();
      cropX = 0;
      cropY = (originalHeight - cropHeight) ~/ 2;
    }

    return img.copyCrop(
      image,
      x: cropX,
      y: cropY,
      width: cropWidth,
      height: cropHeight,
    );
  }


  /// 단순 3:4 크롭 (카메라용)
  static Future<Uint8List> cropImageTo3x4(Uint8List imageBytes) async {
    final originalImage = img.decodeImage(imageBytes);
    if (originalImage == null) return imageBytes;

    final croppedImage = _cropImageTo3x4(originalImage);
    final croppedBytes = img.encodeJpg(croppedImage, quality: 90);
    return Uint8List.fromList(croppedBytes);
  }

  /// 이미지가 너무 작으면 최소 크기로 확대
  static img.Image _ensureMinimumSize(img.Image image) {
    // 최소 권장 크기 (3:4 비율 유지)
    const int minWidth = 600;  // 최소 너비
    const int minHeight = 800; // 최소 높이 (3:4 비율)
    
    // 현재 이미지가 이미 충분히 크면 그대로 반환
    if (image.width >= minWidth && image.height >= minHeight) {
      return image;
    }
    
    // 3:4 비율을 유지하면서 확대할 스케일 계산
    final scaleByWidth = minWidth / image.width;
    final scaleByHeight = minHeight / image.height;
    final scale = math.max(scaleByWidth, scaleByHeight);
    
    // 새로운 크기 계산
    final newWidth = (image.width * scale).round();
    final newHeight = (image.height * scale).round();
    
    // 이미지 리사이즈 (고품질 보간법 사용)
    return img.copyResize(
      image,
      width: newWidth,
      height: newHeight,
      interpolation: img.Interpolation.cubic, // 부드러운 확대를 위한 cubic 보간
    );
  }
}