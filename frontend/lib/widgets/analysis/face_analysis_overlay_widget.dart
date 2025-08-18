import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/app_state.dart';
import 'dart:math' as math;

/// face_simulator.py 정확한 구현을 따른 얼굴 분석 오버레이 위젯
class FaceAnalysisOverlayWidget extends StatefulWidget {
  const FaceAnalysisOverlayWidget({super.key});

  @override
  State<FaceAnalysisOverlayWidget> createState() => _FaceAnalysisOverlayWidgetState();
}

class _FaceAnalysisOverlayWidgetState extends State<FaceAnalysisOverlayWidget>
    with TickerProviderStateMixin {
  late AnimationController _fadeController;
  late AnimationController _circleController;
  late Animation<double> _fadeAnimation;
  late Animation<double> _circleAnimation;

  @override
  void initState() {
    super.initState();
    
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    
    _circleController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeInOut,
    ));
    
    _circleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _circleController,
      curve: Curves.elasticOut,
    ));
    
    // 애니메이션 시작
    _fadeController.forward().then((_) {
      _circleController.forward();
    });
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _circleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (!appState.showBeautyScore || 
            appState.beautyScores == null || 
            appState.overallBeautyScore == null ||
            appState.currentImage == null) {
          return const SizedBox.shrink();
        }

        return Container(
          color: Colors.black.withOpacity(0.85),
          child: Stack(
            children: [
              // 닫기 버튼
              Positioned(
                top: 40,
                right: 20,
                child: IconButton(
                  onPressed: () => appState.hideBeautyScore(),
                  icon: const Icon(
                    Icons.close,
                    color: Colors.white,
                    size: 28,
                  ),
                ),
              ),
              
              // 메인 분석 오버레이
              FadeTransition(
                opacity: _fadeAnimation,
                child: Center(
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      return CustomPaint(
                        size: constraints.biggest,
                        painter: FaceAnalysisOverlayPainter(
                          beautyScores: appState.beautyScores!,
                          overallScore: appState.overallBeautyScore!,
                          circleAnimation: _circleAnimation.value,
                          landmarks: appState.landmarks,
                          imageWidth: appState.imageWidth,
                          imageHeight: appState.imageHeight,
                          containerSize: constraints.biggest,
                        ),
                      );
                    },
                  ),
                ),
              ),
              
              // 하단 정보 패널
              Positioned(
                bottom: 30,
                left: 20,
                right: 20,
                child: FadeTransition(
                  opacity: _fadeAnimation,
                  child: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.95),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.grey[300]!),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '얼굴 황금비율 분석 결과',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          '종합 점수: ${appState.overallBeautyScore!.toStringAsFixed(1)}점',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: _getScoreColor(appState.overallBeautyScore!),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _getScoreDescription(appState.overallBeautyScore!),
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Colors.grey[600],
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Color _getScoreColor(double score) {
    if (score >= 90) return const Color(0xFF4CAF50);
    if (score >= 80) return const Color(0xFF2196F3);
    if (score >= 70) return const Color(0xFFFF9800);
    if (score >= 60) return const Color(0xFFFF5722);
    return const Color(0xFFF44336);
  }

  String _getScoreDescription(double score) {
    if (score >= 90) return '완벽한 황금비율을 가진 아름다운 얼굴입니다';
    if (score >= 80) return '매우 아름다운 비율의 얼굴입니다';
    if (score >= 70) return '아름다운 비율의 얼굴입니다';
    if (score >= 60) return '균형잡힌 비율의 얼굴입니다';
    return '개선 가능한 비율의 얼굴입니다';
  }
}

/// face_simulator.py 스타일의 분석 오버레이 페인터
class FaceAnalysisOverlayPainter extends CustomPainter {
  final Map<String, double> beautyScores;
  final double overallScore;
  final double circleAnimation;
  final List<dynamic> landmarks;
  final int imageWidth;
  final int imageHeight;
  final Size containerSize;

  FaceAnalysisOverlayPainter({
    required this.beautyScores,
    required this.overallScore,
    required this.circleAnimation,
    required this.landmarks,
    required this.imageWidth,
    required this.imageHeight,
    required this.containerSize,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (landmarks.isEmpty || imageWidth == 0 || imageHeight == 0) {
      return;
    }

    // 이미지의 실제 표시 영역 계산
    final imageAspectRatio = imageWidth / imageHeight;
    final containerAspectRatio = containerSize.width / containerSize.height;
    
    late Size imageDisplaySize;
    late Offset imageOffset;
    
    if (imageAspectRatio > containerAspectRatio) {
      imageDisplaySize = Size(containerSize.width, containerSize.width / imageAspectRatio);
      imageOffset = Offset(0, (containerSize.height - imageDisplaySize.height) / 2);
    } else {
      imageDisplaySize = Size(containerSize.height * imageAspectRatio, containerSize.height);
      imageOffset = Offset((containerSize.width - imageDisplaySize.width) / 2, 0);
    }

    // 비율선 그리기
    _drawProportionLines(canvas, imageOffset, imageDisplaySize);
    
    // 교차점 원들 그리기
    _drawIntersectionCircles(canvas, imageOffset, imageDisplaySize);
    
    // 원형 점수 지시기 그리기
    _drawBeautyScoreIndicators(canvas, imageOffset, imageDisplaySize);
  }

  void _drawProportionLines(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    if (landmarks.isEmpty || imageWidth == 0 || imageHeight == 0) return;

    // face_simulator.py 정확한 구현 따라하기
    
    // 1. 1/5 세로 비례선 (특정 랜드마크 기준)
    _drawFifthProportionLines(canvas, imageOffset, imageDisplaySize);
    
    // 2. 1/3 가로 비례선 (특정 랜드마크 기준)
    _drawThirdProportionLines(canvas, imageOffset, imageDisplaySize);
    
    // 3. 랜드마크 37을 지나는 수평선
    _drawLandmark37Line(canvas, imageOffset, imageDisplaySize);
  }
  
  void _drawFifthProportionLines(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    // face_simulator.py의 정확한 랜드마크들
    final landmark33 = _getLandmarkCoords(33);   // 1/5: 왼쪽 눈 바깥쪽
    final landmark133 = _getLandmarkCoords(133); // 2/5: 왼쪽 눈 안쪽
    final landmark362 = _getLandmarkCoords(362); // 3/5: 오른쪽 눈 안쪽
    final landmark359 = _getLandmarkCoords(359); // 4/5: 오른쪽 눈 바깥쪽
    final landmark447 = _getLandmarkCoords(447); // 5/5: 오른쪽 테두리
    final landmark234 = _getLandmarkCoords(234); // 0/5: 왼쪽 테두리
    
    final landmarks = [landmark234, landmark33, landmark133, landmark362, landmark359, landmark447];
    
    final linePaint = Paint()
      ..color = Colors.white.withOpacity(0.5)
      ..strokeWidth = 0.5
      ..style = PaintingStyle.stroke;
    
    // 얼굴 상하단 계산
    final faceTop = _getLandmarkCoords(10);
    final faceBottom = _getLandmarkCoords(152);
    
    if (faceTop == null || faceBottom == null) return;
    
    for (int i = 0; i < landmarks.length; i++) {
      final landmark = landmarks[i];
      if (landmark == null) continue;
      
      final x = _convertToScreenX(landmark.dx, imageOffset, imageDisplaySize);
      final topY = _convertToScreenY(faceTop.dy, imageOffset, imageDisplaySize);
      final bottomY = _convertToScreenY(faceBottom.dy, imageOffset, imageDisplaySize);
      
      _drawDashedLine(canvas,
        Offset(x, topY),
        Offset(x, bottomY),
        linePaint
      );
    }
  }
  
  void _drawThirdProportionLines(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    // face_simulator.py의 정확한 랜드마크들
    final landmark8 = _getLandmarkCoords(8);   // 1/3: 이마-눈썹 경계
    final landmark2 = _getLandmarkCoords(2);   // 2/3: 코 끝
    final landmark152 = _getLandmarkCoords(152); // 3/3: 턱 끝
    
    final horizontalLandmarks = [landmark8, landmark2, landmark152];
    
    final linePaint = Paint()
      ..color = Colors.white.withOpacity(0.5)
      ..strokeWidth = 0.5
      ..style = PaintingStyle.stroke;
    
    // 얼굴 좌우 계산
    final faceLeft = _getLandmarkCoords(234);
    final faceRight = _getLandmarkCoords(454);
    
    if (faceLeft == null || faceRight == null) return;
    
    for (final landmark in horizontalLandmarks) {
      if (landmark == null) continue;
      
      final y = _convertToScreenY(landmark.dy, imageOffset, imageDisplaySize);
      final leftX = _convertToScreenX(faceLeft.dx, imageOffset, imageDisplaySize);
      final rightX = _convertToScreenX(faceRight.dx, imageOffset, imageDisplaySize);
      
      _drawDashedLine(canvas,
        Offset(leftX, y),
        Offset(rightX, y),
        linePaint
      );
    }
  }
  
  void _drawLandmark37Line(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    final landmark37 = _getLandmarkCoords(37); // 하안검 라인
    final faceLeft = _getLandmarkCoords(234);
    final faceRight = _getLandmarkCoords(454);
    
    if (landmark37 == null || faceLeft == null || faceRight == null) return;
    
    final linePaint = Paint()
      ..color = const Color(0xFF9370DB)
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;
    
    final y = _convertToScreenY(landmark37.dy, imageOffset, imageDisplaySize);
    final leftX = _convertToScreenX(faceLeft.dx, imageOffset, imageDisplaySize);
    final rightX = _convertToScreenX(faceRight.dx, imageOffset, imageDisplaySize);
    
    _drawDashedLine(canvas,
      Offset(leftX, y),
      Offset(rightX, y),
      linePaint
    );
  }

  void _drawDashedLine(Canvas canvas, Offset start, Offset end, Paint paint) {
    const dashWidth = 8.0;
    const dashSpace = 4.0;
    
    final distance = (end - start).distance;
    final dashCount = (distance / (dashWidth + dashSpace)).floor();
    
    for (int i = 0; i < dashCount; i++) {
      final startRatio = (i * (dashWidth + dashSpace)) / distance;
      final endRatio = ((i * (dashWidth + dashSpace)) + dashWidth) / distance;
      
      final dashStart = Offset.lerp(start, end, startRatio)!;
      final dashEnd = Offset.lerp(start, end, endRatio)!;
      
      canvas.drawLine(dashStart, dashEnd, paint);
    }
  }

  void _drawIntersectionCircles(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    // face_simulator.py의 정확한 교차점 원들 구현
    
    // 1. 첫 번째 교차점 원 (빨간색): 1/3선과 2/3선이 5/5선과 만나는 점
    _drawFirstIntersectionCircle(canvas, imageOffset, imageDisplaySize);
    
    // 2. 두 번째 교차점 원 (빨간색): 2/3선과 3/3선이 5/5선과 만나는 점
    _drawSecondIntersectionCircle(canvas, imageOffset, imageDisplaySize);
    
    // 3. 좌상 교차점 원 (파란색): 왼쪽 테두리와 2/3선, 37선 교차점
    _drawLeftUpperIntersectionCircle(canvas, imageOffset, imageDisplaySize);
    
    // 4. 좌하 교차점 원 (파란색): 왼쪽 테두리와 하단, 37선 교차점
    _drawLeftLowerIntersectionCircle(canvas, imageOffset, imageDisplaySize);
    
    // 5. 상단 테두리 5개 원들 (빨간색)
    _drawTopBorderCircles(canvas, imageOffset, imageDisplaySize);
  }
  
  void _drawFirstIntersectionCircle(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    final landmark8 = _getLandmarkCoords(8);   // 1/3 이마선
    final landmark2 = _getLandmarkCoords(2);   // 2/3 코선
    final landmark447 = _getLandmarkCoords(447); // 5/5선
    
    if (landmark8 == null || landmark2 == null || landmark447 == null) return;
    
    final rightVerticalX = _convertToScreenX(landmark447.dx, imageOffset, imageDisplaySize);
    final point1Y = _convertToScreenY(landmark8.dy, imageOffset, imageDisplaySize);
    final point2Y = _convertToScreenY(landmark2.dy, imageOffset, imageDisplaySize);
    
    final center = Offset(rightVerticalX, (point1Y + point2Y) / 2);
    final radius = (point2Y - point1Y).abs() / 2 * circleAnimation;
    
    final circlePaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;
    
    if (radius > 0) {
      canvas.drawCircle(center, radius, circlePaint);
    }
  }
  
  void _drawSecondIntersectionCircle(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    final landmark2 = _getLandmarkCoords(2);   // 2/3 코선
    final landmark152 = _getLandmarkCoords(152); // 3/3 턱선
    final landmark447 = _getLandmarkCoords(447); // 5/5선
    
    if (landmark2 == null || landmark152 == null || landmark447 == null) return;
    
    final rightVerticalX = _convertToScreenX(landmark447.dx, imageOffset, imageDisplaySize);
    final point1Y = _convertToScreenY(landmark2.dy, imageOffset, imageDisplaySize);
    final point2Y = _convertToScreenY(landmark152.dy, imageOffset, imageDisplaySize);
    
    final center = Offset(rightVerticalX, (point1Y + point2Y) / 2);
    final radius = (point2Y - point1Y).abs() / 2 * circleAnimation;
    
    final circlePaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;
    
    if (radius > 0) {
      canvas.drawCircle(center, radius, circlePaint);
    }
  }
  
  void _drawLeftUpperIntersectionCircle(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    final landmark234 = _getLandmarkCoords(234); // 왼쪽 테두리
    final landmark2 = _getLandmarkCoords(2);     // 2/3 코선
    final landmark37 = _getLandmarkCoords(37);   // 37선
    
    if (landmark234 == null || landmark2 == null || landmark37 == null) return;
    
    final leftVerticalX = _convertToScreenX(landmark234.dx, imageOffset, imageDisplaySize);
    final point1Y = _convertToScreenY(landmark2.dy, imageOffset, imageDisplaySize);
    final point2Y = _convertToScreenY(landmark37.dy, imageOffset, imageDisplaySize);
    
    final center = Offset(leftVerticalX, (point1Y + point2Y) / 2);
    final radius = (point2Y - point1Y).abs() / 2 * circleAnimation;
    
    final circlePaint = Paint()
      ..color = Colors.blue
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;
    
    if (radius > 0) {
      canvas.drawCircle(center, radius, circlePaint);
    }
  }
  
  void _drawLeftLowerIntersectionCircle(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    final landmark234 = _getLandmarkCoords(234); // 왼쪽 테두리
    final landmark152 = _getLandmarkCoords(152); // 하단 테두리
    final landmark37 = _getLandmarkCoords(37);   // 37선
    
    if (landmark234 == null || landmark152 == null || landmark37 == null) return;
    
    final leftVerticalX = _convertToScreenX(landmark234.dx, imageOffset, imageDisplaySize);
    final point1Y = _convertToScreenY(landmark152.dy, imageOffset, imageDisplaySize);
    final point2Y = _convertToScreenY(landmark37.dy, imageOffset, imageDisplaySize);
    
    final center = Offset(leftVerticalX, (point1Y + point2Y) / 2);
    final radius = (point2Y - point1Y).abs() / 2 * circleAnimation;
    
    final circlePaint = Paint()
      ..color = Colors.blue
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;
    
    if (radius > 0) {
      canvas.drawCircle(center, radius, circlePaint);
    }
  }
  
  void _drawTopBorderCircles(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    // 상단 테두리에 5개의 원 (각 수직선 구간별)
    final faceTop = _getLandmarkCoords(10);
    final landmark234 = _getLandmarkCoords(234); // 0/5
    final landmark33 = _getLandmarkCoords(33);   // 1/5
    final landmark133 = _getLandmarkCoords(133); // 2/5
    final landmark362 = _getLandmarkCoords(362); // 3/5
    final landmark359 = _getLandmarkCoords(359); // 4/5
    final landmark447 = _getLandmarkCoords(447); // 5/5
    
    if (faceTop == null) return;
    
    final verticalLines = [landmark234, landmark33, landmark133, landmark362, landmark359, landmark447];
    final topY = _convertToScreenY(faceTop.dy, imageOffset, imageDisplaySize);
    
    final circlePaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;
    
    // 5개 구간의 원들
    for (int i = 0; i < 5; i++) {
      final leftLandmark = verticalLines[i];
      final rightLandmark = verticalLines[i + 1];
      
      if (leftLandmark == null || rightLandmark == null) continue;
      
      final leftX = _convertToScreenX(leftLandmark.dx, imageOffset, imageDisplaySize);
      final rightX = _convertToScreenX(rightLandmark.dx, imageOffset, imageDisplaySize);
      
      final center = Offset((leftX + rightX) / 2, topY);
      final radius = (rightX - leftX).abs() / 4 * circleAnimation; // 구간 너비의 1/4
      
      if (radius > 0) {
        canvas.drawCircle(center, radius, circlePaint);
      }
    }
  }

  void _drawBeautyScoreIndicators(Canvas canvas, Offset imageOffset, Size imageDisplaySize) {
    // face_simulator.py의 정확한 구현: 랜드마크 2(코)와 172(턱)에만 원형 지시기
    
    final landmark2 = _getLandmarkCoords(2);   // 코 끝
    final landmark172 = _getLandmarkCoords(172); // 턱 끝
    
    if (landmark2 != null && circleAnimation > 0) {
      final nosePosition = Offset(
        _convertToScreenX(landmark2.dx, imageOffset, imageDisplaySize) + 30,
        _convertToScreenY(landmark2.dy, imageOffset, imageDisplaySize)
      );
      
      _drawCircularIndicator(
        canvas,
        nosePosition,
        beautyScores['코길이'] ?? 79.0,
        '코',
        const Color(0xFF96CEB4),
      );
    }
    
    if (landmark172 != null && circleAnimation > 0) {
      final jawPosition = Offset(
        _convertToScreenX(landmark172.dx, imageOffset, imageDisplaySize),
        _convertToScreenY(landmark172.dy, imageOffset, imageDisplaySize) + 30
      );
      
      _drawCircularIndicator(
        canvas,
        jawPosition,
        beautyScores['턱라인'] ?? 81.0,
        '턱곡률',
        const Color(0xFFDDA0DD),
      );
    }
  }

  void _drawCircularIndicator(Canvas canvas, Offset position, double score, String label, Color color) {
    final radius = 25.0 * circleAnimation;
    
    // 외부 원 (테두리)
    final circlePaint = Paint()
      ..color = color
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke;
    
    canvas.drawCircle(position, radius, circlePaint);
    
    // 내부 채우기 (점수에 따라)
    final fillPaint = Paint()
      ..color = color.withOpacity(0.2)
      ..style = PaintingStyle.fill;
    
    canvas.drawCircle(position, radius * 0.8, fillPaint);
    
    // 점수 텍스트
    final textPainter = TextPainter(
      text: TextSpan(
        text: '${score.toStringAsFixed(1)}%',
        style: TextStyle(
          color: Colors.white,
          fontSize: 12 * circleAnimation,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(
      canvas,
      position - Offset(textPainter.width / 2, textPainter.height / 2),
    );
    
    // 라벨 텍스트 (원 아래)
    final labelPainter = TextPainter(
      text: TextSpan(
        text: label,
        style: TextStyle(
          color: color,
          fontSize: 11 * circleAnimation,
          fontWeight: FontWeight.w600,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    labelPainter.layout();
    labelPainter.paint(
      canvas,
      position + Offset(-labelPainter.width / 2, radius + 8),
    );
  }

  // 헬퍼 메서드들
  Offset? _getLandmarkCoords(int index) {
    try {
      if (landmarks.isEmpty || index >= landmarks.length) return null;
      final landmark = landmarks[index];
      // Landmark 객체의 x, y 속성 사용
      return Offset(landmark.x / imageWidth, landmark.y / imageHeight);
    } catch (e) {
      return null;
    }
  }
  
  double _convertToScreenX(double normalizedX, Offset imageOffset, Size imageDisplaySize) {
    return imageOffset.dx + (normalizedX * imageDisplaySize.width);
  }
  
  double _convertToScreenY(double normalizedY, Offset imageOffset, Size imageDisplaySize) {
    return imageOffset.dy + (normalizedY * imageDisplaySize.height);
  }

  @override
  bool shouldRepaint(FaceAnalysisOverlayPainter oldDelegate) {
    return circleAnimation != oldDelegate.circleAnimation ||
           beautyScores != oldDelegate.beautyScores;
  }
}