import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';
import '../models/face_regions.dart';
import '../services/api_service.dart';
import 'dart:math' as math;
import 'beauty_score_visualizer.dart';

/// 이미지 표시 및 상호작용 위젯
class ImageDisplayWidget extends StatefulWidget {
  const ImageDisplayWidget({super.key});

  @override
  State<ImageDisplayWidget> createState() => _ImageDisplayWidgetState();
}

class _ImageDisplayWidgetState extends State<ImageDisplayWidget> {
  Offset? _startPoint;
  Offset? _currentPoint;
  bool _isDragging = false;
  
  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (appState.currentImage == null) {
          return const Center(child: Text('이미지가 없습니다.'));
        }

        return LayoutBuilder(
          builder: (context, constraints) {
            return GestureDetector(
              onPanStart: (details) => _onPanStart(details, constraints, appState),
              onPanUpdate: (details) => _onPanUpdate(details, constraints, appState),
              onPanEnd: (details) => _onPanEnd(details, constraints, appState),
              child: Container(
                width: double.infinity,
                height: double.infinity,
                color: Colors.grey[100],
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    // 이미지
                    Image.memory(
                      appState.currentImage!,
                      fit: BoxFit.contain,
                    ),
                    
                    // 랜드마크 오버레이
                    if (appState.showLandmarks)
                      CustomPaint(
                        painter: AnimatedFaceRegionsPainter(
                          landmarks: appState.landmarks,
                          imageWidth: appState.imageWidth,
                          imageHeight: appState.imageHeight,
                          containerSize: constraints.biggest,
                          regionVisibility: appState.regionVisibility,
                          animationProgress: appState.animationProgress,
                          currentAnimatingRegion: appState.currentAnimatingRegion,
                          showSpecialLandmarks: appState.showBeautyScore, // 애니메이션 완료 후에만 표시
                          beautyScoreAnimationProgress: appState.beautyScoreAnimationProgress,
                        ),
                      ),
                    
                    // 얼굴 스캔 애니메이션 오버레이
                    if (appState.isAutoAnimationMode)
                      CustomPaint(
                        painter: FaceScanAnimationPainter(
                          containerSize: constraints.biggest,
                          imageWidth: appState.imageWidth,
                          imageHeight: appState.imageHeight,
                        ),
                      ),
                    
                    // 분석 텍스트 오버레이
                    if (appState.isAutoAnimationMode)
                      Positioned(
                        top: 20,
                        left: 0,
                        right: 0,
                        child: const AnalysisTextOverlay(),
                      ),
                    
                    // 워핑 도구 오버레이
                    if (_startPoint != null)
                      CustomPaint(
                        painter: WarpToolPainter(
                          startPoint: _startPoint!,
                          currentPoint: _currentPoint ?? _startPoint!,
                          influenceRadius: appState.influenceRadius,
                          warpMode: appState.warpMode,
                          isDragging: _isDragging,
                        ),
                      ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  void _onPanStart(details, BoxConstraints constraints, AppState appState) {
    final localPosition = details.localPosition;
    
    // 이미지 영역 내에서만 동작하도록 제한
    if (_isPointInImageBounds(localPosition, constraints, appState)) {
      setState(() {
        _startPoint = localPosition;
        _currentPoint = localPosition;
        _isDragging = false;
      });
    }
  }

  void _onPanUpdate(details, BoxConstraints constraints, AppState appState) {
    if (_startPoint == null) return;
    
    setState(() {
      _currentPoint = details.localPosition;
      _isDragging = true;
    });
  }

  void _onPanEnd(details, BoxConstraints constraints, AppState appState) async {
    if (_startPoint == null || _currentPoint == null || !_isDragging) {
      setState(() {
        _startPoint = null;
        _currentPoint = null;
        _isDragging = false;
      });
      return;
    }

    // 이미지 좌표로 변환
    final imageCoordinates = _convertToImageCoordinates(
      _startPoint!,
      _currentPoint!,
      constraints,
      appState,
    );

    if (imageCoordinates == null) {
      setState(() {
        _startPoint = null;
        _currentPoint = null;
        _isDragging = false;
      });
      return;
    }

    // 워핑 적용
    await _applyWarp(appState, imageCoordinates);

    setState(() {
      _startPoint = null;
      _currentPoint = null;
      _isDragging = false;
    });
  }

  bool _isPointInImageBounds(Offset point, BoxConstraints constraints, AppState appState) {
    // 이미지의 실제 표시 영역 계산
    final imageAspectRatio = appState.imageWidth / appState.imageHeight;
    final containerAspectRatio = constraints.maxWidth / constraints.maxHeight;
    
    late Size imageDisplaySize;
    late Offset imageOffset;
    
    if (imageAspectRatio > containerAspectRatio) {
      // 이미지가 더 넓음 - 너비에 맞춤
      imageDisplaySize = Size(constraints.maxWidth, constraints.maxWidth / imageAspectRatio);
      imageOffset = Offset(0, (constraints.maxHeight - imageDisplaySize.height) / 2);
    } else {
      // 이미지가 더 높음 - 높이에 맞춤
      imageDisplaySize = Size(constraints.maxHeight * imageAspectRatio, constraints.maxHeight);
      imageOffset = Offset((constraints.maxWidth - imageDisplaySize.width) / 2, 0);
    }
    
    final imageRect = imageOffset & imageDisplaySize;
    return imageRect.contains(point);
  }

  Map<String, double>? _convertToImageCoordinates(
    Offset startPoint,
    Offset endPoint,
    BoxConstraints constraints,
    AppState appState,
  ) {
    // 이미지의 실제 표시 영역 계산
    final imageAspectRatio = appState.imageWidth / appState.imageHeight;
    final containerAspectRatio = constraints.maxWidth / constraints.maxHeight;
    
    late Size imageDisplaySize;
    late Offset imageOffset;
    
    if (imageAspectRatio > containerAspectRatio) {
      imageDisplaySize = Size(constraints.maxWidth, constraints.maxWidth / imageAspectRatio);
      imageOffset = Offset(0, (constraints.maxHeight - imageDisplaySize.height) / 2);
    } else {
      imageDisplaySize = Size(constraints.maxHeight * imageAspectRatio, constraints.maxHeight);
      imageOffset = Offset((constraints.maxWidth - imageDisplaySize.width) / 2, 0);
    }
    
    // 상대 좌표를 이미지 좌표로 변환
    final relativeStart = Offset(
      (startPoint.dx - imageOffset.dx) / imageDisplaySize.width,
      (startPoint.dy - imageOffset.dy) / imageDisplaySize.height,
    );
    
    final relativeEnd = Offset(
      (endPoint.dx - imageOffset.dx) / imageDisplaySize.width,
      (endPoint.dy - imageOffset.dy) / imageDisplaySize.height,
    );
    
    // 범위 검증
    if (relativeStart.dx < 0 || relativeStart.dx > 1 ||
        relativeStart.dy < 0 || relativeStart.dy > 1 ||
        relativeEnd.dx < 0 || relativeEnd.dx > 1 ||
        relativeEnd.dy < 0 || relativeEnd.dy > 1) {
      return null;
    }
    
    return {
      'startX': relativeStart.dx * appState.imageWidth,
      'startY': relativeStart.dy * appState.imageHeight,
      'endX': relativeEnd.dx * appState.imageWidth,
      'endY': relativeEnd.dy * appState.imageHeight,
    };
  }

  Future<void> _applyWarp(AppState appState, Map<String, double> coordinates) async {
    if (appState.currentImageId == null) return;
    
    appState.setLoading(true);
    
    try {
      final apiService = context.read<ApiService>();
      final warpRequest = WarpRequest(
        imageId: appState.currentImageId!,
        startX: coordinates['startX']!,
        startY: coordinates['startY']!,
        endX: coordinates['endX']!,
        endY: coordinates['endY']!,
        influenceRadius: appState.influenceRadius,
        strength: appState.warpStrength,
        mode: appState.warpMode.value,
      );
      
      final warpResponse = await apiService.warpImage(warpRequest);
      final imageBytes = warpResponse.imageBytes;
      
      // 변형된 이미지로 업데이트
      appState.setImage(
        imageBytes,
        appState.currentImageId!,
        appState.imageWidth,
        appState.imageHeight,
      );
      
      // 랜드마크 다시 검출
      final landmarkResponse = await apiService.getFaceLandmarks(appState.currentImageId!);
      appState.setLandmarks(landmarkResponse.landmarks);
      
      appState.setLoading(false);
      
    } catch (e) {
      appState.setError('변형 적용 실패: $e');
    }
  }
}

/// 애니메이션을 포함한 부위별 얼굴 랜드마크를 그리는 CustomPainter  
class AnimatedFaceRegionsPainter extends CustomPainter {
  final List<Landmark> landmarks;
  final int imageWidth;
  final int imageHeight;
  final Size containerSize;
  final RegionVisibility regionVisibility;
  final Map<String, double> animationProgress;
  final String? currentAnimatingRegion;
  final bool showSpecialLandmarks;
  final double beautyScoreAnimationProgress;


  AnimatedFaceRegionsPainter({
    required this.landmarks,
    required this.imageWidth,
    required this.imageHeight,
    required this.containerSize,
    required this.regionVisibility,
    required this.animationProgress,
    this.currentAnimatingRegion,
    this.showSpecialLandmarks = false,
    this.beautyScoreAnimationProgress = 1.0,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (landmarks.isEmpty) return;

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

    // 각 부위별로 랜드마크와 선 그리기
    for (final entry in FaceRegions.regions.entries) {
      final regionKey = entry.key;
      final regionData = entry.value;
      
      if (!regionVisibility.isVisible(regionKey)) continue;

      final pointPaint = Paint()
        ..color = regionData.color.withOpacity(0.8)
        ..style = PaintingStyle.fill;

      final linePaint = Paint()
        ..color = regionData.color.withOpacity(0.7)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.8
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round;

      final fillPaint = Paint()
        ..color = regionData.color.withOpacity(0.2)
        ..style = PaintingStyle.fill;

      // 애니메이션이 있는 부위인지 확인
      if (regionData.hasAnimation && animationProgress.containsKey(regionKey)) {
        // 애니메이션이 진행 중인 부위만 그리기
        _drawAnimatedRegion(
          canvas, 
          regionData, 
          regionKey, 
          imageOffset, 
          imageDisplaySize,
          linePaint,
          fillPaint,
        );
      } else if (!regionData.hasAnimation || (currentAnimatingRegion == null && animationProgress.isEmpty)) {
        // 애니메이션이 없는 부위이거나, 현재 애니메이션이 진행 중이지 않고 진행률도 비어있을 때만 정적 렌더링
        // 일반 랜드마크 점 그리기
        for (final index in regionData.indices) {
          if (index < landmarks.length) {
            final landmark = landmarks[index];
            final screenX = imageOffset.dx + (landmark.x / imageWidth) * imageDisplaySize.width;
            final screenY = imageOffset.dy + (landmark.y / imageHeight) * imageDisplaySize.height;
            
            canvas.drawCircle(
              Offset(screenX, screenY),
              3.0,
              pointPaint,
            );
          }
        }

        // 일반 연결선 그리기
        for (final line in regionData.lines) {
          if (line.length >= 2) {
            final path = Path();
            bool pathStarted = false;
            
            for (int i = 0; i < line.length; i++) {
              final index = line[i];
              if (index < landmarks.length) {
                final landmark = landmarks[index];
                final screenX = imageOffset.dx + (landmark.x / imageWidth) * imageDisplaySize.width;
                final screenY = imageOffset.dy + (landmark.y / imageHeight) * imageDisplaySize.height;
                
                if (!pathStarted) {
                  path.moveTo(screenX, screenY);
                  pathStarted = true;
                } else {
                  path.lineTo(screenX, screenY);
                }
              }
            }
            
            canvas.drawPath(path, linePaint);
          }
        }
      }
      // 애니메이션이 있는 부위지만 현재 애니메이션 진행 중이고 해당 부위가 아닌 경우 아무것도 그리지 않음
    }
    
    // 뷰티 스코어 시각화 렌더링
    if (showSpecialLandmarks) {
      final beautyVisualizer = BeautyScoreVisualizer(
        landmarks: landmarks,
        imageWidth: imageWidth,
        imageHeight: imageHeight,
        animationProgress: beautyScoreAnimationProgress,
      );
      beautyVisualizer.render(canvas, imageOffset, imageDisplaySize);
    }
  }
  
  void _drawAnimatedRegion(
    Canvas canvas,
    RegionData regionData,
    String regionKey,
    Offset imageOffset,
    Size imageDisplaySize,
    Paint linePaint,
    Paint fillPaint,
  ) {
    final progress = animationProgress[regionKey] ?? 0.0;
    
    // 부드러운 애니메이션 선을 위한 페인트 설정
    final smoothLinePaint = Paint()
      ..color = regionData.color.withOpacity(0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.8
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    
    // 발광 효과를 위한 외곽 페인트
    final glowPaint = Paint()
      ..color = regionData.color.withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2.0);
    
    for (final animSeq in regionData.animationSequences) {
      final points = animSeq.points;
      if (points.length < 2) continue;
      
      // 현재 진행률에 따라 그릴 점들의 개수 계산
      final totalPoints = points.length;
      final currentPointIndex = (progress * totalPoints).floor();
      final segmentProgress = (progress * totalPoints) - currentPointIndex;
      
      if (currentPointIndex >= totalPoints - 1) {
        // 애니메이션 완료 - 전체 경로와 채우기
        final path = _createSmoothPath(points, imageOffset, imageDisplaySize);
        
        // 닫힌 경로면 채우기
        if (animSeq.fillArea) {
          final closedPath = Path.from(path);
          closedPath.close();
          canvas.drawPath(closedPath, fillPaint);
        }
        
        // 발광 효과 외곽선
        canvas.drawPath(path, glowPaint);
        
        // 메인 외곽선 그리기
        canvas.drawPath(path, smoothLinePaint);
        
      } else if (currentPointIndex >= 0) {
        // 애니메이션 진행 중 - 부분적 그리기
        final visiblePoints = <int>[];
        
        // 완성된 점들 추가
        for (int i = 0; i <= currentPointIndex; i++) {
          visiblePoints.add(points[i]);
        }
        
        // 현재 진행 중인 보간된 점 추가
        if (currentPointIndex + 1 < points.length && segmentProgress > 0) {
          final currentIndex = points[currentPointIndex];
          final nextIndex = points[currentPointIndex + 1];
          
          if (currentIndex < landmarks.length && nextIndex < landmarks.length) {
            final currentLandmark = landmarks[currentIndex];
            final nextLandmark = landmarks[nextIndex];
            
            final currentX = imageOffset.dx + (currentLandmark.x / imageWidth) * imageDisplaySize.width;
            final currentY = imageOffset.dy + (currentLandmark.y / imageHeight) * imageDisplaySize.height;
            final nextX = imageOffset.dx + (nextLandmark.x / imageWidth) * imageDisplaySize.width;
            final nextY = imageOffset.dy + (nextLandmark.y / imageHeight) * imageDisplaySize.height;
            
            // 보간된 중간 지점 계산
            final interpolatedX = currentX + (nextX - currentX) * segmentProgress;
            final interpolatedY = currentY + (nextY - currentY) * segmentProgress;
            
            // 현재 애니메이션 지점에서 발광하는 랜드마크 그리기
            _drawGlowingLandmark(canvas, Offset(interpolatedX, interpolatedY), regionData.color);
          }
        }
        
        if (visiblePoints.length >= 2) {
          final partialPath = _createSmoothPath(visiblePoints, imageOffset, imageDisplaySize);
          
          // 발광 효과 외곽선
          canvas.drawPath(partialPath, glowPaint);
          
          // 메인 외곽선 그리기
          canvas.drawPath(partialPath, smoothLinePaint);
        }
        
        // 이미 그려진 랜드마크들을 발광 효과로 표시
        for (int i = 0; i <= currentPointIndex; i++) {
          final index = points[i];
          if (index < landmarks.length) {
            final landmark = landmarks[index];
            final screenX = imageOffset.dx + (landmark.x / imageWidth) * imageDisplaySize.width;
            final screenY = imageOffset.dy + (landmark.y / imageHeight) * imageDisplaySize.height;
            
            _drawGlowingLandmark(canvas, Offset(screenX, screenY), regionData.color, intensity: 0.5);
          }
        }
      }
    }
  }
  
  Path _createSmoothPath(List<int> points, Offset imageOffset, Size imageDisplaySize) {
    final path = Path();
    if (points.isEmpty) return path;
    
    final screenPoints = <Offset>[];
    
    // 모든 점들을 화면 좌표로 변환
    for (final index in points) {
      if (index < landmarks.length) {
        final landmark = landmarks[index];
        final screenX = imageOffset.dx + (landmark.x / imageWidth) * imageDisplaySize.width;
        final screenY = imageOffset.dy + (landmark.y / imageHeight) * imageDisplaySize.height;
        screenPoints.add(Offset(screenX, screenY));
      }
    }
    
    if (screenPoints.isEmpty) return path;
    
    // 첫 번째 점으로 이동
    path.moveTo(screenPoints[0].dx, screenPoints[0].dy);
    
    if (screenPoints.length == 1) return path;
    
    // 부드러운 곡선으로 연결 (Catmull-Rom 스플라인 사용)
    for (int i = 1; i < screenPoints.length; i++) {
      if (i == 1) {
        // 첫 번째 세그먼트는 직선
        path.lineTo(screenPoints[i].dx, screenPoints[i].dy);
      } else {
        // 이전 점, 현재 점, 다음 점을 고려한 부드러운 곡선
        final p0 = screenPoints[i - 2];
        final p1 = screenPoints[i - 1];
        final p2 = screenPoints[i];
        final p3 = i + 1 < screenPoints.length ? screenPoints[i + 1] : screenPoints[i];
        
        // 컨트롤 포인트 계산
        final cp1x = p1.dx + (p2.dx - p0.dx) / 6;
        final cp1y = p1.dy + (p2.dy - p0.dy) / 6;
        final cp2x = p2.dx - (p3.dx - p1.dx) / 6;
        final cp2y = p2.dy - (p3.dy - p1.dy) / 6;
        
        path.cubicTo(cp1x, cp1y, cp2x, cp2y, p2.dx, p2.dy);
      }
    }
    
    return path;
  }
  
  void _drawGlowingLandmark(Canvas canvas, Offset position, Color color, {double intensity = 1.0}) {
    // 외부 발광 효과 (가장 큰 원)
    final outerGlowPaint = Paint()
      ..color = color.withOpacity(0.1 * intensity)
      ..style = PaintingStyle.fill
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8.0);
    canvas.drawCircle(position, 12.0, outerGlowPaint);
    
    // 중간 발광 효과
    final middleGlowPaint = Paint()
      ..color = color.withOpacity(0.3 * intensity)
      ..style = PaintingStyle.fill
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4.0);
    canvas.drawCircle(position, 8.0, middleGlowPaint);
    
    // 내부 발광 효과
    final innerGlowPaint = Paint()
      ..color = color.withOpacity(0.6 * intensity)
      ..style = PaintingStyle.fill
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2.0);
    canvas.drawCircle(position, 5.0, innerGlowPaint);
    
    // 중심 랜드마크 점
    final corePaint = Paint()
      ..color = color.withOpacity(0.9 * intensity)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(position, 3.0, corePaint);
    
    // 하이라이트
    final highlightPaint = Paint()
      ..color = Colors.white.withOpacity(0.8 * intensity)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(position, 1.5, highlightPaint);
  }
  
  
  
  
  
  @override
  bool shouldRepaint(AnimatedFaceRegionsPainter oldDelegate) {
    return landmarks != oldDelegate.landmarks ||
           imageWidth != oldDelegate.imageWidth ||
           imageHeight != oldDelegate.imageHeight ||
           containerSize != oldDelegate.containerSize ||
           regionVisibility != oldDelegate.regionVisibility ||
           animationProgress != oldDelegate.animationProgress ||
           currentAnimatingRegion != oldDelegate.currentAnimatingRegion ||
           showSpecialLandmarks != oldDelegate.showSpecialLandmarks ||
           beautyScoreAnimationProgress != oldDelegate.beautyScoreAnimationProgress;
  }
}

/// 워핑 도구를 그리는 CustomPainter
class WarpToolPainter extends CustomPainter {
  final Offset startPoint;
  final Offset currentPoint;
  final double influenceRadius;
  final WarpMode warpMode;
  final bool isDragging;

  WarpToolPainter({
    required this.startPoint,
    required this.currentPoint,
    required this.influenceRadius,
    required this.warpMode,
    required this.isDragging,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // 영향 반경 원
    final radiusPaint = Paint()
      ..color = Colors.blue.withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    
    canvas.drawCircle(startPoint, influenceRadius * 0.5, radiusPaint);
    
    // 시작점
    final startPaint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.fill;
    
    canvas.drawCircle(startPoint, 6.0, startPaint);
    
    if (isDragging) {
      // 드래그 벡터
      final vectorPaint = Paint()
        ..color = Colors.green
        ..strokeWidth = 3.0
        ..style = PaintingStyle.stroke;
      
      canvas.drawLine(startPoint, currentPoint, vectorPaint);
      
      // 끝점
      final endPaint = Paint()
        ..color = Colors.green
        ..style = PaintingStyle.fill;
      
      canvas.drawCircle(currentPoint, 4.0, endPaint);
      
      // 화살표
      _drawArrow(canvas, startPoint, currentPoint, vectorPaint);
    }
  }
  
  void _drawArrow(Canvas canvas, Offset start, Offset end, Paint paint) {
    const arrowLength = 15.0;
    const arrowAngle = 0.5;
    
    final direction = (end - start).direction;
    final arrowPoint1 = end + Offset.fromDirection(direction + arrowAngle + 3.14159, arrowLength);
    final arrowPoint2 = end + Offset.fromDirection(direction - arrowAngle + 3.14159, arrowLength);
    
    canvas.drawLine(end, arrowPoint1, paint);
    canvas.drawLine(end, arrowPoint2, paint);
  }

  @override
  bool shouldRepaint(WarpToolPainter oldDelegate) {
    return startPoint != oldDelegate.startPoint ||
           currentPoint != oldDelegate.currentPoint ||
           influenceRadius != oldDelegate.influenceRadius ||
           warpMode != oldDelegate.warpMode ||
           isDragging != oldDelegate.isDragging;
  }
}

/// 얼굴 스캔 애니메이션 페인터
class FaceScanAnimationPainter extends CustomPainter {
  final Size containerSize;
  final int imageWidth;
  final int imageHeight;

  FaceScanAnimationPainter({
    required this.containerSize,
    required this.imageWidth,
    required this.imageHeight,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (imageWidth == 0 || imageHeight == 0) return;

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

    final currentTime = DateTime.now().millisecondsSinceEpoch;
    final cyclePhase = (currentTime / 3000) % 1; // 3초 주기
    
    // 상하 복반 운동 계산 (sin 원리 사용)
    final scanProgress = 0.5 + 0.5 * math.sin(cyclePhase * 2 * math.pi);
    final scanY = imageOffset.dy + (imageDisplaySize.height * scanProgress);
    
    // 혜성꿀리 효과를 위한 거리 계산
    final tailLength = 60.0;
    final numTailSegments = 8;
    
    // 혜성꿀리 그리기
    for (int i = 1; i <= numTailSegments; i++) {
      final tailOffset = (i.toDouble() / numTailSegments) * tailLength;
      final tailY = scanY - tailOffset * (cyclePhase < 0.5 ? 1 : -1); // 방향에 따라 꿀리 방향 변경
      
      if (tailY >= imageOffset.dy && tailY <= imageOffset.dy + imageDisplaySize.height) {
        final opacity = (1.0 - i / numTailSegments) * 0.3;
        final tailPaint = Paint()
          ..color = const Color(0xFF00FFFF).withOpacity(opacity)
          ..strokeWidth = 2.0 - (i * 0.2)
          ..style = PaintingStyle.stroke;
        
        canvas.drawLine(
          Offset(imageOffset.dx, tailY),
          Offset(imageOffset.dx + imageDisplaySize.width, tailY),
          tailPaint,
        );
      }
    }
    
    // 메인 스캔 라인 그리기
    final scanLinePaint = Paint()
      ..color = const Color(0xFF00FFFF).withOpacity(0.9)
      ..strokeWidth = 4.0
      ..style = PaintingStyle.stroke;
    
    final glowPaint = Paint()
      ..color = const Color(0xFF00FFFF).withOpacity(0.4)
      ..strokeWidth = 12.0
      ..style = PaintingStyle.stroke
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6.0);
    
    // 발광 효과
    canvas.drawLine(
      Offset(imageOffset.dx, scanY),
      Offset(imageOffset.dx + imageDisplaySize.width, scanY),
      glowPaint,
    );
    
    // 메인 스캔 라인
    canvas.drawLine(
      Offset(imageOffset.dx, scanY),
      Offset(imageOffset.dx + imageDisplaySize.width, scanY),
      scanLinePaint,
    );
    
    // 스캔 영역 표시 (그라데이션 없어도 되는 방식)
    final scanAreaHeight = 50.0;
    final scanRect = Rect.fromLTWH(
      imageOffset.dx,
      scanY - scanAreaHeight / 2,
      imageDisplaySize.width,
      scanAreaHeight,
    );
    
    final gradient = LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [
        const Color(0xFF00FFFF).withOpacity(0.0),
        const Color(0xFF00FFFF).withOpacity(0.15),
        const Color(0xFF00FFFF).withOpacity(0.0),
      ],
    );
    
    final scanAreaPaint = Paint()
      ..shader = gradient.createShader(scanRect);
    
    canvas.drawRect(scanRect, scanAreaPaint);
    
    // 예측 라인들 (스캔 방향 표시)
    final predictLinePaint = Paint()
      ..color = const Color(0xFF00FFFF).withOpacity(0.3)
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;
    
    final direction = cyclePhase < 0.5 ? 1 : -1; // 아래로 갈 때 1, 위로 갈 때 -1
    for (double i = 1; i <= 2; i++) {
      final predictY = scanY + (i * 25 * direction);
      if (predictY >= imageOffset.dy && predictY <= imageOffset.dy + imageDisplaySize.height) {
        canvas.drawLine(
          Offset(imageOffset.dx, predictY),
          Offset(imageOffset.dx + imageDisplaySize.width, predictY),
          predictLinePaint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(FaceScanAnimationPainter oldDelegate) {
    return true; // 항상 다시 그리기 (애니메이션을 위해)
  }
}

/// 분석 텍스트 오버레이 위젯
class AnalysisTextOverlay extends StatefulWidget {
  const AnalysisTextOverlay({super.key});

  @override
  State<AnalysisTextOverlay> createState() => _AnalysisTextOverlayState();
}

class _AnalysisTextOverlayState extends State<AnalysisTextOverlay>
    with TickerProviderStateMixin {
  late AnimationController _textController;
  late AnimationController _dotsController;
  late Animation<double> _fadeAnimation;
  
  final List<String> _analysisTexts = [
    '얼굴 랜드마크 검출 중',
    '얼굴 비율 분석 중',
    '얼굴 대칭성 반영 중',
    '황금비율 비교 중',
    '뷰티 스코어 계산 중',
  ];
  
  int _currentTextIndex = 0;

  @override
  void initState() {
    super.initState();
    
    _textController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );
    
    _dotsController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _textController,
      curve: Curves.easeInOut,
    ));
    
    _startTextAnimation();
    _dotsController.repeat();
  }

  void _startTextAnimation() async {
    while (mounted) {
      try {
        if (!mounted) break;
        await _textController.forward();
        if (!mounted) break;
        await Future.delayed(const Duration(milliseconds: 1500));
        if (!mounted) break;
        await _textController.reverse();
        
        if (mounted) {
          setState(() {
            _currentTextIndex = (_currentTextIndex + 1) % _analysisTexts.length;
          });
        }
      } catch (e) {
        print('텍스트 애니메이션 에러: $e');
        break;
      }
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    _dotsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.8),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: const Color(0xFF00FFFF).withOpacity(0.5),
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF00FFFF).withOpacity(0.3),
              blurRadius: 10,
              spreadRadius: 2,
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 스캐닝 아이콘
            Container(
              width: 24,
              height: 24,
              child: Stack(
                children: [
                  Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: const Color(0xFF00FFFF),
                        width: 2,
                      ),
                    ),
                  ),
                  AnimatedBuilder(
                    animation: _dotsController,
                    builder: (context, child) {
                      return Positioned(
                        top: 2 + (_dotsController.value * 16),
                        left: 10,
                        child: Container(
                          width: 4,
                          height: 4,
                          decoration: BoxDecoration(
                            color: const Color(0xFF00FFFF),
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF00FFFF),
                                blurRadius: 4,
                                spreadRadius: 1,
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
            
            const SizedBox(width: 12),
            
            // 분석 텍스트
            AnimatedBuilder(
              animation: _fadeAnimation,
              builder: (context, child) {
                return Opacity(
                  opacity: _fadeAnimation.value,
                  child: Text(
                    _analysisTexts[_currentTextIndex],
                    style: TextStyle(
                      color: const Color(0xFF00FFFF),
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      shadows: [
                        Shadow(
                          color: const Color(0xFF00FFFF).withOpacity(0.5),
                          blurRadius: 8,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
            
            // 도트 애니메이션
            AnimatedBuilder(
              animation: _dotsController,
              builder: (context, child) {
                final dotCount = (_dotsController.value * 4).floor() % 4;
                return SizedBox(
                  width: 30,
                  child: Text(
                    '.' * dotCount,
                    style: TextStyle(
                      color: const Color(0xFF00FFFF),
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.left,
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}