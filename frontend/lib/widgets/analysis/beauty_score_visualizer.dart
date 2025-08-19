import 'package:flutter/material.dart';
import '../../models/app_state.dart';
import 'dart:math' as math;

/// 뷰티 스코어 시각화를 담당하는 클래스
class BeautyScoreVisualizer {
  final List<Landmark> landmarks;
  final int imageWidth;
  final int imageHeight;
  final double animationProgress;
  
  // 랜드마크 인덱스 상수들
  static const List<int> verticalLandmarks = [234, 33, 133, 362, 359, 447];
  static const List<int> horizontalLandmarks = [8, 2, 37, 152];
  
  BeautyScoreVisualizer({
    required this.landmarks,
    required this.imageWidth,
    required this.imageHeight,
    this.animationProgress = 1.0,
  });
  
  /// 전체 뷰티 스코어 시각화 렌더링
  void render(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    if (animationProgress <= 0.0) return;
    
    // 단계별 애니메이션 (0.0 ~ 1.0)
    // 0.0 ~ 0.3: 격자선 표시
    if (animationProgress >= 0.0) {
      final gridProgress = (animationProgress / 0.3).clamp(0.0, 1.0);
      _drawGridLines(canvas, imageOffset, imageDisplaySize, gridProgress);
    }
    
    // 0.3 ~ 0.7: 분석 원들 표시
    if (animationProgress >= 0.3) {
      final circlesProgress = ((animationProgress - 0.3) / 0.4).clamp(0.0, 1.0);
      _drawAnalysisCircles(canvas, imageOffset, imageDisplaySize, circlesProgress);
    }
    
    // 0.7 ~ 1.0: 턱곡률 텍스트 표시
    if (animationProgress >= 0.7) {
      final textProgress = ((animationProgress - 0.7) / 0.3).clamp(0.0, 1.0);
      _drawJawCurvatureText(canvas, imageOffset, imageDisplaySize, textProgress);
    }
  }
  
  /// 격자선 그리기 (수직선 + 수평선)
  void _drawGridLines(Canvas canvas, Offset imageOffset, Size imageDisplaySize, [double progress = 1.0]) {
    if (progress <= 0.0) return;
    
    final linePaint = _createLinePaint();
    linePaint.color = linePaint.color.withOpacity(linePaint.color.opacity * progress);
    
    // H10과 H8의 Y 좌표 구하기 (세로선 범위 제한용)
    final h10Y = _getLandmarkScreenY(10, imageOffset, imageDisplaySize);
    final h8Y = _getLandmarkScreenY(8, imageOffset, imageDisplaySize);
    
    // L234와 L447의 X 좌표 구하기 (수평선 범위 제한용)
    final l234X = _getLandmarkScreenX(234, imageOffset, imageDisplaySize);
    final l447X = _getLandmarkScreenX(447, imageOffset, imageDisplaySize);
    
    // 세로선 그리기 (H10 ~ H8 사이만)
    for (final index in verticalLandmarks) {
      if (index < landmarks.length) {
        final screenX = _getLandmarkScreenX(index, imageOffset, imageDisplaySize);
        final topY = h10Y ?? imageOffset.dy;
        final bottomY = h8Y ?? (imageOffset.dy + imageDisplaySize.height);
        _drawDashedLine(canvas, Offset(screenX, topY), Offset(screenX, bottomY), linePaint);
      }
    }
    
    // 수평선 그리기 (L234 ~ L447 사이만)
    for (final index in horizontalLandmarks) {
      if (index < landmarks.length) {
        final screenY = _getLandmarkScreenY(index, imageOffset, imageDisplaySize);
        final leftX = l234X ?? imageOffset.dx;
        final rightX = l447X ?? (imageOffset.dx + imageDisplaySize.width);
        _drawDashedLine(canvas, Offset(leftX, screenY), Offset(rightX, screenY), linePaint);
      }
    }
  }
  
  /// 분석 원들 그리기 (중앙 5개 + 좌우 각 2개)
  void _drawAnalysisCircles(Canvas canvas, Offset imageOffset, Size imageDisplaySize, [double progress = 1.0]) {
    if (progress <= 0.0) return;
    
    // 원들을 순차적으로 나타나게 함
    final centerProgress = (progress * 3).clamp(0.0, 1.0);
    final rightProgress = ((progress * 3) - 1).clamp(0.0, 1.0);
    final leftProgress = ((progress * 3) - 2).clamp(0.0, 1.0);
    
    if (centerProgress > 0) _drawCenterCircles(canvas, imageOffset, imageDisplaySize, centerProgress);
    if (rightProgress > 0) _drawRightCircles(canvas, imageOffset, imageDisplaySize, rightProgress);
    if (leftProgress > 0) _drawLeftCircles(canvas, imageOffset, imageDisplaySize, leftProgress);
  }
  
  /// 중앙 5개 원 (시안색)
  void _drawCenterCircles(Canvas canvas, Offset imageOffset, Size imageDisplaySize, [double progress = 1.0]) {
    if (10 >= landmarks.length) return;
    
    final h10Y = _getLandmarkScreenY(10, imageOffset, imageDisplaySize);
    final verticalXPositions = verticalLandmarks
        .where((i) => i < landmarks.length)
        .map((i) => _getLandmarkScreenX(i, imageOffset, imageDisplaySize))
        .toList();
    
    if (verticalXPositions.length < 2) return;
    
    final radiuses = <double>[];
    for (int i = 0; i < verticalXPositions.length - 1; i++) {
      radiuses.add((verticalXPositions[i + 1] - verticalXPositions[i]) / 2);
    }
    
    final totalDiameter = radiuses.reduce((a, b) => a + b) * 2;
    
    for (int i = 0; i < radiuses.length; i++) {
      final centerX = (verticalXPositions[i] + verticalXPositions[i + 1]) / 2;
      final radius = radiuses[i];
      final percentage = (((radius * 2) / totalDiameter) * 100).round();
      
      _drawGlowingCircle(canvas, Offset(centerX, h10Y), radius, 
          const Color(0xFF00FFFF), '$percentage%', progress);
    }
  }
  
  /// 오른쪽 2개 원 (라임색)
  void _drawRightCircles(Canvas canvas, Offset imageOffset, Size imageDisplaySize, [double progress = 1.0]) {
    if (447 >= landmarks.length) return;
    
    final l447X = _getLandmarkScreenX(447, imageOffset, imageDisplaySize);
    final yPositions = [8, 2, 152]
        .where((i) => i < landmarks.length)
        .map((i) => _getLandmarkScreenY(i, imageOffset, imageDisplaySize))
        .toList();
    
    if (yPositions.length < 3) return;
    
    final radius1 = (yPositions[1] - yPositions[0]).abs() / 2;
    final radius2 = (yPositions[2] - yPositions[1]).abs() / 2;
    final totalDiameter = (radius1 + radius2) * 2;
    
    final centerY1 = (yPositions[0] + yPositions[1]) / 2;
    final centerY2 = (yPositions[1] + yPositions[2]) / 2;
    final percentage1 = (((radius1 * 2) / totalDiameter) * 100).round();
    final percentage2 = (((radius2 * 2) / totalDiameter) * 100).round();
    
    _drawGlowingCircle(canvas, Offset(l447X, centerY1), radius1, 
        const Color(0xFF00FF00), '$percentage1%', progress);
    _drawGlowingCircle(canvas, Offset(l447X, centerY2), radius2, 
        const Color(0xFF00FF00), '$percentage2%', progress);
  }
  
  /// 왼쪽 2개 원 (황금색)
  void _drawLeftCircles(Canvas canvas, Offset imageOffset, Size imageDisplaySize, [double progress = 1.0]) {
    if (234 >= landmarks.length) return;
    
    final l234X = _getLandmarkScreenX(234, imageOffset, imageDisplaySize);
    final yPositions = [2, 37, 152]
        .where((i) => i < landmarks.length)
        .map((i) => _getLandmarkScreenY(i, imageOffset, imageDisplaySize))
        .toList();
    
    if (yPositions.length < 3) return;
    
    final radius1 = (yPositions[1] - yPositions[0]).abs() / 2;
    final radius2 = (yPositions[2] - yPositions[1]).abs() / 2;
    final totalDiameter = (radius1 + radius2) * 2;
    
    final centerY1 = (yPositions[0] + yPositions[1]) / 2;
    final centerY2 = (yPositions[1] + yPositions[2]) / 2;
    final percentage1 = (((radius1 * 2) / totalDiameter) * 100).round();
    final percentage2 = (((radius2 * 2) / totalDiameter) * 100).round();
    
    _drawGlowingCircle(canvas, Offset(l234X, centerY1), radius1, 
        const Color(0xFFFFD700), '$percentage1%', progress);
    _drawGlowingCircle(canvas, Offset(l234X, centerY2), radius2, 
        const Color(0xFFFFD700), '$percentage2%', progress);
  }

  /// 턱곡률 텍스트 그리기
  void _drawJawCurvatureText(Canvas canvas, Offset imageOffset, Size imageDisplaySize, [double progress = 1.0]) {
    if (progress <= 0.0) return;
    final gonialAngle = _calculateGonialAngle();
    final cervicoMentalAngle = _calculateCervicoMentalAngle();
    
    if (gonialAngle == null || cervicoMentalAngle == null) return;
    
    final liftingScore = _calculateLiftingScore(gonialAngle, cervicoMentalAngle);
    
    if (152 < landmarks.length && 18 < landmarks.length) {
      final jawBottom = landmarks[152];
      final lipBottom = landmarks[18];
      
      final centerX = (jawBottom.x + lipBottom.x) / 2;
      final centerY = (jawBottom.y + lipBottom.y) / 2;
      
      final screenX = imageOffset.dx + (centerX / imageWidth) * imageDisplaySize.width;
      final screenY = imageOffset.dy + (centerY / imageHeight) * imageDisplaySize.height;
      
      // 각도 정보 텍스트만 표시 (애니메이션 적용)
      _drawText(canvas, Offset(screenX, screenY), 
          '하악각${gonialAngle.round()}° 턱목각${cervicoMentalAngle.round()}°', 
          Colors.white.withOpacity(progress), 10);
    }
  }
  
  // =============================================================================
  // 유틸리티 메서드들
  // =============================================================================
  
  /// 랜드마크의 화면 X 좌표 계산
  double _getLandmarkScreenX(int index, Offset imageOffset, Size imageDisplaySize) {
    if (index >= landmarks.length) return 0;
    // MediaPipe에서 픽셀 좌표로 변환됨 - 이미지 표시 영역에 맞게 스케일링
    final normalizedX = landmarks[index].x / imageWidth;  // 0~1 정규화
    return imageOffset.dx + (normalizedX * imageDisplaySize.width);
  }
  
  /// 랜드마크의 화면 Y 좌표 계산  
  double _getLandmarkScreenY(int index, Offset imageOffset, Size imageDisplaySize) {
    if (index >= landmarks.length) return 0;
    // MediaPipe에서 픽셀 좌표로 변환됨 - 이미지 표시 영역에 맞게 스케일링
    final normalizedY = landmarks[index].y / imageHeight;  // 0~1 정규화
    return imageOffset.dy + (normalizedY * imageDisplaySize.height);
  }
  
  /// 선 스타일 페인트 생성
  Paint _createLinePaint() {
    return Paint()
      ..color = Colors.white.withOpacity(0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
  }
  
  /// 발광 원 그리기
  void _drawGlowingCircle(Canvas canvas, Offset center, double radius, Color color, String text, [double progress = 1.0]) {
    if (progress <= 0.0) return;
    // 스케일 애니메이션 효과 (작은 크기에서 시작해서 원래 크기로)
    final scale = 0.3 + (0.7 * progress); // 0.3에서 1.0까지
    final animatedRadius = radius * scale;
    
    // 발광 효과
    final glowPaint = Paint()
      ..color = color.withOpacity(0.7 * progress)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8.0 * scale
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6.0);
    canvas.drawCircle(center, animatedRadius, glowPaint);
    
    // 메인 원
    final circlePaint = Paint()
      ..color = color.withOpacity(progress)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5 * scale;
    canvas.drawCircle(center, animatedRadius, circlePaint);
    
    // 텍스트 (페이드인 효과)
    if (progress > 0.5) { // 텍스트는 원이 어느 정도 나타난 후에 표시
      final textOpacity = ((progress - 0.5) / 0.5).clamp(0.0, 1.0);
      _drawText(canvas, center, text, color.withOpacity(textOpacity), 12);
    }
  }
  
  /// 텍스트 그리기
  void _drawText(Canvas canvas, Offset position, String text, Color color, double fontSize) {
    final textPainter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: color,
          fontSize: fontSize,
          fontWeight: FontWeight.bold,
          shadows: [
            Shadow(
              color: color.withOpacity(0.8),
              blurRadius: 6,
            ),
            Shadow(
              color: Colors.black.withOpacity(0.9),
              blurRadius: 3,
            ),
          ],
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    
    textPainter.layout();
    textPainter.paint(
      canvas,
      Offset(
        position.dx - textPainter.width / 2,
        position.dy - textPainter.height / 2,
      ),
    );
  }
  
  /// 점선 그리기
  void _drawDashedLine(Canvas canvas, Offset start, Offset end, Paint paint) {
    const dashLength = 8.0;
    const gapLength = 4.0;
    
    final distance = (end - start).distance;
    final dashCount = (distance / (dashLength + gapLength)).floor();
    final unitVector = (end - start) / distance;
    
    for (int i = 0; i < dashCount; i++) {
      final dashStart = start + unitVector * (i * (dashLength + gapLength));
      final dashEnd = dashStart + unitVector * dashLength;
      canvas.drawLine(dashStart, dashEnd, paint);
    }
    
    final remainingDistance = distance - (dashCount * (dashLength + gapLength));
    if (remainingDistance > 0) {
      final dashStart = start + unitVector * (dashCount * (dashLength + gapLength));
      final actualDashLength = remainingDistance.clamp(0.0, dashLength);
      final dashEnd = dashStart + unitVector * actualDashLength;
      canvas.drawLine(dashStart, dashEnd, paint);
    }
  }
  
  // =============================================================================
  // 턱곡률 계산 메서드들
  // =============================================================================
  
  double? _calculateGonialAngle() {
    final requiredIndices = [234, 172, 150, 454, 397, 379];
    if (requiredIndices.any((i) => i >= landmarks.length)) return null;
    
    final leftGonial = _calculateJawAngleImproved(landmarks[234], landmarks[172], landmarks[150]);
    final rightGonial = _calculateJawAngleImproved(landmarks[454], landmarks[397], landmarks[379]);
    
    if (leftGonial == null || rightGonial == null) return null;
    return (leftGonial + rightGonial) / 2;
  }
  
  double? _calculateCervicoMentalAngle() {
    if (152 >= landmarks.length || 18 >= landmarks.length) return null;
    
    final chin = landmarks[152];
    final neckFront = landmarks[18];
    final neckBottomX = chin.x;
    final neckBottomY = chin.y + (chin.y - neckFront.y).abs() * 1.5;
    
    return _calculateAngle3Points(
      Offset(neckBottomX, neckBottomY),
      Offset(chin.x, chin.y),
      Offset(neckFront.x, neckFront.y),
    );
  }
  
  double? _calculateJawAngleImproved(Landmark earPoint, Landmark jawCorner, Landmark jawMid) {
    const verticalVector = Offset(0, 1);
    final jawVector = Offset(jawMid.x - jawCorner.x, jawMid.y - jawCorner.y);
    final jawLength = jawVector.distance;
    if (jawLength == 0) return null;
    
    final jawUnit = jawVector / jawLength;
    final dotProduct = verticalVector.dx * jawUnit.dx + verticalVector.dy * jawUnit.dy;
    final cosAngle = dotProduct.clamp(-1.0, 1.0);
    final angleRad = math.acos(cosAngle.abs());
    final angleDeg = angleRad * 180 / math.pi;
    
    return 90 + angleDeg;
  }
  
  double? _calculateAngle3Points(Offset p1, Offset p2, Offset p3) {
    final v1 = p1 - p2;
    final v2 = p3 - p2;
    final len1 = v1.distance;
    final len2 = v2.distance;
    
    if (len1 == 0 || len2 == 0) return null;
    
    final dotProduct = v1.dx * v2.dx + v1.dy * v2.dy;
    final cosAngle = (dotProduct / (len1 * len2)).clamp(-1.0, 1.0);
    final angleRad = math.acos(cosAngle);
    return angleRad * 180 / math.pi;
  }
  
  double _calculateLiftingScore(double gonialAngle, double cervicoMentalAngle) {
    double gonialScore;
    if (gonialAngle <= 90) {
      gonialScore = 100;
    } else if (gonialAngle <= 120) {
      gonialScore = 100 - ((gonialAngle - 90) * 20 / 30);
    } else if (gonialAngle <= 140) {
      gonialScore = 80 - ((gonialAngle - 120) * 60 / 20);
    } else {
      gonialScore = (20 - ((gonialAngle - 140) * 20 / 10)).clamp(0.0, 20.0);
    }
    
    double cervicoScore;
    if (105 <= cervicoMentalAngle && cervicoMentalAngle <= 115) {
      cervicoScore = 100;
    } else if (100 <= cervicoMentalAngle && cervicoMentalAngle <= 120) {
      cervicoScore = 90 - (cervicoMentalAngle - 110).abs() * 2;
    } else if (90 <= cervicoMentalAngle && cervicoMentalAngle <= 130) {
      cervicoScore = 70 - (cervicoMentalAngle - 110).abs() * 1.5;
    } else {
      cervicoScore = (70 - (cervicoMentalAngle - 110).abs() * 2).clamp(40.0, 70.0);
    }
    
    final liftingScore = gonialScore * 0.7 + cervicoScore * 0.3;
    return liftingScore.clamp(0.0, 100.0);
  }
}