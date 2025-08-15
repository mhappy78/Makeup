import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';
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
  Offset? _hoverPoint; // 마우스 호버 위치
  bool _isDragging = false;
  bool _isHovering = false; // 호버 상태
  double _baseScaleValue = 1.0; // 스케일 제스처의 기준값
  bool _isPanMode = false; // 팬 모드 여부
  bool _isShiftPressed = false; // Shift 키 눌림 상태
  
  // 공통 이미지 표시 영역 계산 메서드
  Map<String, dynamic> _getImageDisplayInfo(BoxConstraints constraints, AppState appState) {
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
    
    return {
      'imageDisplaySize': imageDisplaySize,
      'imageOffset': imageOffset,
    };
  }
  
  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (appState.currentImage == null) {
          return const Center(child: Text('이미지가 없습니다.'));
        }

        return LayoutBuilder(
          builder: (context, constraints) {
            final imageDisplayInfo = _getImageDisplayInfo(constraints, appState);
            final imageDisplaySize = imageDisplayInfo['imageDisplaySize'] as Size;
            final imageOffset = imageDisplayInfo['imageOffset'] as Offset;
            
            return MouseRegion(
                onEnter: (_) => setState(() => _isHovering = true),
                onExit: (_) => setState(() {
                  _isHovering = false;
                  _hoverPoint = null;
                }),
                onHover: (event) {
                // 전문가 탭에서만 호버 시각화 (이미지 영역 내에서만)
                if (appState.currentTabIndex == 2) {
                  final localPos = event.localPosition;
                  // 이미지 영역 내부인지 확인
                  if (_isPointInImageBounds(localPos, constraints, appState)) {
                    setState(() {
                      _hoverPoint = localPos;
                    });
                  } else {
                    setState(() {
                      _hoverPoint = null;
                    });
                  }
                }
              },
              child: GestureDetector(
                  onDoubleTap: () {
                    // 더블클릭으로 줌 리셋
                    appState.resetZoom();
                  },
                  onLongPressStart: (details) {
                    // 길게 누르기 시작: 팬 모드 활성화 (전문가 탭에서만)
                    if (appState.currentTabIndex == 2) {
                      setState(() {
                        _isPanMode = true;
                        _startPoint = details.localPosition; // 팬 시작점 저장
                      });
                    }
                  },
                  onLongPressMoveUpdate: (details) {
                    // 길게 누르면서 드래그: 팬 동작
                    if (appState.currentTabIndex == 2 && _isPanMode && _startPoint != null && appState.zoomScale > 1.0) {
                      final delta = details.localPosition - _startPoint!;
                      appState.addPanOffset(delta);
                      setState(() {
                        _startPoint = details.localPosition; // 연속적인 팬을 위해 시작점 업데이트
                      });
                    }
                  },
                  onLongPressEnd: (details) {
                    // 길게 누르기 종료: 팬 모드 비활성화
                    if (appState.currentTabIndex == 2) {
                      setState(() {
                        _isPanMode = false;
                        _startPoint = null;
                      });
                    }
                  },
                onScaleStart: (details) {
                  // 스케일 제스처 시작 - 현재 스케일을 기준으로 설정
                  _baseScaleValue = appState.zoomScale;
                  
                  // 전문가 탭에서 단일 터치인 경우 워핑 시작점 설정 (팬 모드가 아닐 때만)
                  if (appState.currentTabIndex == 2 && details.pointerCount == 1 && !_isPanMode) {
                    final localPosition = details.localFocalPoint;
                    if (_isPointInImageBounds(localPosition, constraints, appState)) {
                      setState(() {
                        _startPoint = localPosition;
                        _currentPoint = localPosition;
                        _isDragging = false;
                      });
                    }
                  }
                },
                onScaleUpdate: (details) {
                  // 멀티터치 줌 (두 손가락 이상)
                  if (details.pointerCount > 1 && details.scale != 1.0) {
                    final newScale = (_baseScaleValue * details.scale).clamp(0.5, 3.0);
                    appState.setZoomScale(newScale);
                  }
                  
                  // 단일 터치 처리
                  if (details.pointerCount == 1) {
                    if (appState.currentTabIndex == 2) {
                      // 전문가 탭: 팬 모드인지 확인
                      if (_isPanMode && appState.zoomScale > 1.0) {
                        // 팬 모드: 이미지 이동
                        appState.addPanOffset(details.focalPointDelta * 0.5);
                      } else {
                        // 워핑 모드: 워핑 도구
                        if (_startPoint != null) {
                          setState(() {
                            _currentPoint = details.localFocalPoint;
                            _isDragging = true;
                          });
                        }
                      }
                    } else {
                      // 다른 탭: 팬 (줌된 상태에서만)
                      if (appState.zoomScale > 1.0) {
                        appState.addPanOffset(details.focalPointDelta * 0.5);
                      }
                    }
                  }
                  
                  // 멀티터치 팬
                  if (details.pointerCount > 1 && appState.zoomScale > 1.0 && appState.currentTabIndex != 2) {
                    appState.addPanOffset(details.focalPointDelta * 0.3);
                  }
                },
                onScaleEnd: (details) {
                  // 스케일 제스처 완료
                  _baseScaleValue = appState.zoomScale;
                  
                  // 전문가 탭에서 워핑 완료 처리 (팬 모드가 아닐 때만)
                  if (appState.currentTabIndex == 2 && !_isPanMode && _startPoint != null && _currentPoint != null && _isDragging) {
                    _performWarp(constraints, appState);
                  }
                  
                  setState(() {
                    _startPoint = null;
                    _currentPoint = null;
                    _isDragging = false;
                  });
                },
              child: Container(
                width: double.infinity,
                height: double.infinity,
                color: Colors.grey[100],
                child: Stack(
                    alignment: Alignment.center, // Stack 중앙 정렬
                    children: [
                      // 이미지 (중앙 정렬, 줌과 팬 적용)
                      RepaintBoundary(
                        child: Transform.translate(
                          offset: appState.panOffset,
                          child: Transform.scale(
                            scale: appState.zoomScale,
                            child: Image.memory(
                              appState.displayImage!,
                              key: ValueKey(appState.currentImageId), // 이미지 식별을 위한 키
                              fit: BoxFit.contain,
                              alignment: Alignment.center,
                              gaplessPlayback: true, // 이미지 전환 시 깜빡임 방지
                              filterQuality: FilterQuality.medium, // 필터 품질 최적화
                              isAntiAlias: true, // 안티 앨리어싱으로 부드러운 렌더링
                            ),
                          ),
                        ),
                      ),
                    
                    // 프리셋 처리 중 오버레이
                    if (appState.loadingPresetType != null)
                      Container(
                        color: Colors.black.withOpacity(0.1),
                        child: Center(
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.9),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Theme.of(context).colorScheme.primary,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  '프리셋 적용 중...',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    
                    // 랜드마크 오버레이 (정확한 이미지 위치 기준)
                    if (appState.showLandmarks)
                      Positioned(
                        left: imageOffset.dx,
                        top: imageOffset.dy,
                        width: imageDisplaySize.width,
                        height: imageDisplaySize.height,
                        child: CustomPaint(
                          painter: AnimatedFaceRegionsPainter(
                            landmarks: appState.landmarks,
                            imageWidth: appState.imageWidth,
                            imageHeight: appState.imageHeight,
                            containerSize: imageDisplaySize, // 이미지 표시 크기 사용
                            regionVisibility: appState.regionVisibility,
                            animationProgress: appState.animationProgress,
                            currentAnimatingRegion: appState.currentAnimatingRegion,
                            showSpecialLandmarks: appState.showBeautyScore, // 애니메이션 완료 후에만 표시
                            beautyScoreAnimationProgress: appState.beautyScoreAnimationProgress,
                          ),
                        ),
                      ),
                    
                    // 얼굴 스캔 애니메이션 오버레이 (정확한 이미지 위치 기준)
                    if (appState.isAutoAnimationMode)
                      Positioned(
                        left: imageOffset.dx,
                        top: imageOffset.dy,
                        width: imageDisplaySize.width,
                        height: imageDisplaySize.height,
                        child: CustomPaint(
                          painter: FaceScanAnimationPainter(
                            containerSize: imageDisplaySize, // 이미지 표시 크기 사용
                            imageWidth: appState.imageWidth,
                            imageHeight: appState.imageHeight,
                          ),
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
                    
                    // 워핑 도구 오버레이 (이미지 영역 내)
                    if (_startPoint != null)
                      Positioned(
                        left: imageOffset.dx,
                        top: imageOffset.dy,
                        width: imageDisplaySize.width,
                        height: imageDisplaySize.height,
                        child: CustomPaint(
                          painter: WarpToolPainter(
                            startPoint: Offset(
                              (_startPoint!.dx - imageOffset.dx),
                              (_startPoint!.dy - imageOffset.dy)
                            ),
                            currentPoint: Offset(
                              ((_currentPoint ?? _startPoint!).dx - imageOffset.dx),
                              ((_currentPoint ?? _startPoint!).dy - imageOffset.dy)
                            ),
                            influenceRadius: appState.getInfluenceRadiusForDisplay(imageDisplaySize),
                            warpMode: appState.warpMode,
                            isDragging: _isDragging,
                          ),
                        ),
                      ),
                    
                    // 호버 시각화 (전문가 탭에서만, 이미지 영역 내)
                    if (appState.currentTabIndex == 2 && _hoverPoint != null && !_isDragging)
                      Positioned(
                        left: imageOffset.dx,
                        top: imageOffset.dy,
                        width: imageDisplaySize.width,
                        height: imageDisplaySize.height,
                        child: CustomPaint(
                          painter: HoverPreviewPainter(
                            hoverPoint: Offset(
                              (_hoverPoint!.dx - imageOffset.dx),
                              (_hoverPoint!.dy - imageOffset.dy)
                            ),
                            influenceRadius: appState.getInfluenceRadiusForDisplay(imageDisplaySize),
                            strength: appState.warpStrength,
                            warpMode: appState.warpMode,
                          ),
                        ),
                      ),
                    
                    // 플로팅 줌 컨트롤 (이미지 좌측 하단 세로)
                    Positioned(
                      left: 20,
                      bottom: 20,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // 줌인 버튼
                          FloatingActionButton.small(
                            onPressed: () {
                              final newScale = (appState.zoomScale * 1.2).clamp(0.5, 3.0);
                              appState.setZoomScale(newScale);
                            },
                            backgroundColor: Colors.white,
                            foregroundColor: Colors.black87,
                            child: const Icon(Icons.add, size: 18),
                          ),
                          const SizedBox(height: 8),
                          // 줌 비율 표시
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.black87,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '${(appState.zoomScale * 100).toInt()}%',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                          const SizedBox(height: 8),
                          // 줌아웃 버튼
                          FloatingActionButton.small(
                            onPressed: () {
                              final newScale = (appState.zoomScale / 1.2).clamp(0.5, 3.0);
                              appState.setZoomScale(newScale);
                            },
                            backgroundColor: Colors.white,
                            foregroundColor: Colors.black87,
                            child: const Icon(Icons.remove, size: 18),
                          ),
                        ],
                      ),
                    ),
                    
                    // 팬 모드 표시 (전문가 탭에서만)
                    if (appState.currentTabIndex == 2 && _isPanMode)
                      Positioned(
                        top: 20,
                        right: 20,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.9),
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.2),
                                blurRadius: 4,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.pan_tool,
                                color: Colors.white,
                                size: 16,
                              ),
                              SizedBox(width: 4),
                              Text(
                                '팬 모드',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            );
          },
        );
      },
    );
  }

  // 워핑 수행 메서드 (기존 _onPanEnd 로직)
  Future<void> _performWarp(BoxConstraints constraints, AppState appState) async {
    if (_startPoint == null || _currentPoint == null || !_isDragging) {
      return;
    }

    // 이미지 좌표로 변환
    final imageCoordinates = _convertToImageCoordinates(
      _startPoint!,
      _currentPoint!,
      constraints,
      appState,
    );

    if (imageCoordinates == null) return;

    try {
      appState.setLoading(true);
      final apiService = context.read<ApiService>();

      final warpRequest = WarpRequest(
        imageId: appState.currentImageId!,
        startX: imageCoordinates['startX']!,
        startY: imageCoordinates['startY']!,
        endX: imageCoordinates['endX']!,
        endY: imageCoordinates['endY']!,
        influenceRadius: appState.getInfluenceRadiusPixels(),
        strength: appState.warpStrength,
        mode: appState.warpMode.name,
      );

      final response = await apiService.warpImage(warpRequest);
      
      // 히스토리에 현재 상태 저장
      appState.saveToHistory();
      
      // 새 이미지로 업데이트
      appState.updateCurrentImageWithId(response.imageBytes, response.imageId);
      
    } catch (e) {
      appState.setError('워핑 실패: $e');
    } finally {
      appState.setLoading(false);
    }
  }


  bool _isPointInImageBounds(Offset point, BoxConstraints constraints, AppState appState) {
    // 줌과 팬을 고려한 이미지 영역 계산
    final imageAspectRatio = appState.imageWidth / appState.imageHeight;
    final containerAspectRatio = constraints.maxWidth / constraints.maxHeight;
    
    late Size baseImageDisplaySize;
    late Offset baseImageOffset;
    
    if (imageAspectRatio > containerAspectRatio) {
      baseImageDisplaySize = Size(constraints.maxWidth, constraints.maxWidth / imageAspectRatio);
      baseImageOffset = Offset(0, (constraints.maxHeight - baseImageDisplaySize.height) / 2);
    } else {
      baseImageDisplaySize = Size(constraints.maxHeight * imageAspectRatio, constraints.maxHeight);
      baseImageOffset = Offset((constraints.maxWidth - baseImageDisplaySize.width) / 2, 0);
    }
    
    // 줌과 팬을 적용한 실제 이미지 영역 계산
    final containerCenter = Offset(constraints.maxWidth / 2, constraints.maxHeight / 2);
    final scaledSize = Size(
      baseImageDisplaySize.width * appState.zoomScale,
      baseImageDisplaySize.height * appState.zoomScale,
    );
    
    // 줌된 이미지의 중심점 (팬 오프셋 포함)
    final scaledImageCenter = containerCenter + appState.panOffset;
    
    // 줌된 이미지의 실제 표시 영역
    final scaledImageOffset = Offset(
      scaledImageCenter.dx - scaledSize.width / 2,
      scaledImageCenter.dy - scaledSize.height / 2,
    );
    
    final scaledImageRect = scaledImageOffset & scaledSize;
    return scaledImageRect.contains(point);
  }

  Map<String, double>? _convertToImageCoordinates(
    Offset startPoint,
    Offset endPoint,
    BoxConstraints constraints,
    AppState appState,
  ) {
    // 이미지의 실제 표시 영역 계산 (줌 전 기본 크기)
    final imageAspectRatio = appState.imageWidth / appState.imageHeight;
    final containerAspectRatio = constraints.maxWidth / constraints.maxHeight;
    
    late Size baseImageDisplaySize;
    late Offset baseImageOffset;
    
    if (imageAspectRatio > containerAspectRatio) {
      baseImageDisplaySize = Size(constraints.maxWidth, constraints.maxWidth / imageAspectRatio);
      baseImageOffset = Offset(0, (constraints.maxHeight - baseImageDisplaySize.height) / 2);
    } else {
      baseImageDisplaySize = Size(constraints.maxHeight * imageAspectRatio, constraints.maxHeight);
      baseImageOffset = Offset((constraints.maxWidth - baseImageDisplaySize.width) / 2, 0);
    }
    
    // 컨테이너 중심점 계산
    final containerCenter = Offset(constraints.maxWidth / 2, constraints.maxHeight / 2);
    
    // 줌과 팬을 고려한 역변환
    // 1. 컨테이너 중심 기준 좌표로 변환
    final startFromCenter = startPoint - containerCenter;
    final endFromCenter = endPoint - containerCenter;
    
    // 2. 팬 오프셋 제거
    final startAfterPan = startFromCenter - appState.panOffset;
    final endAfterPan = endFromCenter - appState.panOffset;
    
    // 3. 줌 스케일 제거
    final startAfterZoom = startAfterPan / appState.zoomScale;
    final endAfterZoom = endAfterPan / appState.zoomScale;
    
    // 4. 다시 컨테이너 좌표로 변환
    final adjustedStart = startAfterZoom + containerCenter;
    final adjustedEnd = endAfterZoom + containerCenter;
    
    // 5. 이미지 좌표로 변환
    final relativeStart = Offset(
      (adjustedStart.dx - baseImageOffset.dx) / baseImageDisplaySize.width,
      (adjustedStart.dy - baseImageOffset.dy) / baseImageDisplaySize.height,
    );
    
    final relativeEnd = Offset(
      (adjustedEnd.dx - baseImageOffset.dx) / baseImageDisplaySize.width,
      (adjustedEnd.dy - baseImageOffset.dy) / baseImageDisplaySize.height,
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
    
    // 워핑 작업 전에 히스토리 저장
    appState.saveToHistory();
    
    appState.setLoading(true);
    
    try {
      final apiService = context.read<ApiService>();
      final warpRequest = WarpRequest(
        imageId: appState.currentImageId!,
        startX: coordinates['startX']!,
        startY: coordinates['startY']!,
        endX: coordinates['endX']!,
        endY: coordinates['endY']!,
        influenceRadius: appState.getInfluenceRadiusPixels(),
        strength: appState.warpStrength,
        mode: appState.warpMode.value,
      );
      
      final warpResponse = await apiService.warpImage(warpRequest);
      final imageBytes = warpResponse.imageBytes;
      
      // 변형된 이미지로 현재 이미지와 ID 업데이트 (새로운 이미지 ID 사용)
      appState.updateCurrentImageWithId(imageBytes, warpResponse.imageId);
      
      // 새로운 이미지 ID로 랜드마크 다시 검출
      final landmarkResponse = await apiService.getFaceLandmarks(warpResponse.imageId);
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
    
    canvas.drawCircle(startPoint, influenceRadius, radiusPaint);
    
    // 시작점
    final startPaint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.fill;
    
    canvas.drawCircle(startPoint, 3.0, startPaint); // 반으로 줄임 (6.0 → 3.0)
    
    if (isDragging) {
      // 드래그 벡터 (2배 가늘게)
      final vectorPaint = Paint()
        ..color = Colors.green
        ..strokeWidth = 1.5
        ..style = PaintingStyle.stroke;
      
      canvas.drawLine(startPoint, currentPoint, vectorPaint);
      
      // 끝점
      final endPaint = Paint()
        ..color = Colors.green
        ..style = PaintingStyle.fill;
      
      canvas.drawCircle(currentPoint, 2.0, endPaint); // 반으로 줄임 (4.0 → 2.0)
      
      // 화살표
      _drawArrow(canvas, startPoint, currentPoint, vectorPaint);
    }
  }
  
  void _drawArrow(Canvas canvas, Offset start, Offset end, Paint paint) {
    const arrowLength = 7.5; // 2배 작게 (15.0 → 7.5)
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

/// 호버 미리보기 페인터
class HoverPreviewPainter extends CustomPainter {
  final Offset hoverPoint;
  final double influenceRadius;
  final double strength;
  final WarpMode warpMode;

  HoverPreviewPainter({
    required this.hoverPoint,
    required this.influenceRadius,
    required this.strength,
    required this.warpMode,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // 영향 반경 원 (점선 테두리, 내부 투명)
    final radiusStrokePaint = Paint()
      ..color = Colors.blue.withOpacity(0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    
    // 강도에 따른 내부 원 (강도 시각화)
    final strengthRadius = influenceRadius * (strength.clamp(0.1, 1.0));
    final strengthStrokePaint = Paint()
      ..color = _getModeColor().withOpacity(0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    
    // 영향 반경 원을 점선으로 그리기
    _drawDashedCircle(canvas, hoverPoint, influenceRadius, radiusStrokePaint);
    
    // 강도 원 그리기 (점선)
    if (strength > 0.1) {
      _drawDashedCircle(canvas, hoverPoint, strengthRadius, strengthStrokePaint);
    }
    
    // 중심점 표시
    final centerPaint = Paint()
      ..color = _getModeColor()
      ..style = PaintingStyle.fill;
    
    canvas.drawCircle(hoverPoint, 3.0, centerPaint);
    
    // 모드별 아이콘 또는 표시
    _drawModeIndicator(canvas, hoverPoint);
  }
  
  Color _getModeColor() {
    switch (warpMode) {
      case WarpMode.pull:
        return Colors.green;
      case WarpMode.push:
        return Colors.red;
      case WarpMode.expand:
        return Colors.orange;
      case WarpMode.shrink:
        return Colors.purple;
    }
  }
  
  void _drawModeIndicator(Canvas canvas, Offset center) {
    final paint = Paint()
      ..color = _getModeColor()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    
    switch (warpMode) {
      case WarpMode.pull:
        // 화살표 4방향 안쪽
        _drawArrowIcon(canvas, center, paint, true);
        break;
      case WarpMode.push:
        // 화살표 4방향 바깥쪽
        _drawArrowIcon(canvas, center, paint, false);
        break;
      case WarpMode.expand:
        // + 모양
        canvas.drawLine(
          Offset(center.dx - 8, center.dy),
          Offset(center.dx + 8, center.dy),
          paint,
        );
        canvas.drawLine(
          Offset(center.dx, center.dy - 8),
          Offset(center.dx, center.dy + 8),
          paint,
        );
        break;
      case WarpMode.shrink:
        // - 모양
        canvas.drawLine(
          Offset(center.dx - 6, center.dy),
          Offset(center.dx + 6, center.dy),
          paint,
        );
        break;
    }
  }
  
  void _drawArrowIcon(Canvas canvas, Offset center, Paint paint, bool inward) {
    final size = 6.0;
    final directions = [0.0, 1.5708, 3.14159, 4.71239]; // 0°, 90°, 180°, 270°
    
    for (final direction in directions) {
      final startOffset = inward ? size : -size;
      final endOffset = inward ? -size : size;
      
      final start = center + Offset.fromDirection(direction, startOffset);
      final end = center + Offset.fromDirection(direction, endOffset);
      
      canvas.drawLine(start, end, paint);
      
      // 화살표 머리
      final arrowLength = 3.0;
      final arrowAngle = 0.5;
      final arrowDirection = inward ? direction + 3.14159 : direction;
      
      final arrowPoint1 = end + Offset.fromDirection(arrowDirection + arrowAngle, arrowLength);
      final arrowPoint2 = end + Offset.fromDirection(arrowDirection - arrowAngle, arrowLength);
      
      canvas.drawLine(end, arrowPoint1, paint);
      canvas.drawLine(end, arrowPoint2, paint);
    }
  }

  // 점선 원 그리기 헬퍼 메서드
  void _drawDashedCircle(Canvas canvas, Offset center, double radius, Paint paint) {
    const double dashLength = 8.0;
    const double gapLength = 4.0;
    const double totalDashUnit = dashLength + gapLength;
    
    final circumference = 2 * math.pi * radius;
    final dashCount = (circumference / totalDashUnit).floor();
    
    for (int i = 0; i < dashCount; i++) {
      final startAngle = (i * totalDashUnit / radius);
      final endAngle = startAngle + (dashLength / radius);
      
      final startX = center.dx + radius * math.cos(startAngle);
      final startY = center.dy + radius * math.sin(startAngle);
      final endX = center.dx + radius * math.cos(endAngle);
      final endY = center.dy + radius * math.sin(endAngle);
      
      // 짧은 호 그리기
      final path = Path();
      path.addArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        endAngle - startAngle,
      );
      canvas.drawPath(path, paint);
    }
  }

  @override
  bool shouldRepaint(HoverPreviewPainter oldDelegate) {
    return hoverPoint != oldDelegate.hoverPoint ||
           influenceRadius != oldDelegate.influenceRadius ||
           strength != oldDelegate.strength ||
           warpMode != oldDelegate.warpMode;
  }
}