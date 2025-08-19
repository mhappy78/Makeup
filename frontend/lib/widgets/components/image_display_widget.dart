import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'dart:math' as math;
import '../../models/app_state.dart' show AppState, Landmark, WarpMode;
import '../../models/face_regions.dart';
import '../../services/mediapipe_service.dart';
import '../../services/warp_fallback_manager.dart';
import '../../services/warp_coordinator.dart';
import '../analysis/beauty_score_visualizer.dart';

// 시각화 상수들
class VisualizationConstants {
  // 기본 크기
  static const double landmarkRadius = 5.0;
  static const double arrowLength = 7.5;
  static const double arrowHeadSize = 15.0;
  static const double influenceRadius = 50.0;
  static const double dashWidth = 5.0;
  static const double dashGap = 5.0;
  
  // 애니메이션 관련
  static const double pulseBaseRadius = 15.0;
  static const double pulseAmplitude = 8.0;
  static const double scanAreaHeight = 50.0;
  static const double scanOffset = 20.0;
  static const double blurRadius = 15.0;
  
  // 색상
  static const Color startPointColor = Colors.red;
  static const Color endPointColor = Colors.blue;
  static const Color arrowColor = Colors.orange;
  static const Color influenceCircleColor = Colors.yellow;
}

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
  
  @override
  void initState() {
    super.initState();
    // WarpCoordinator에 등록하여 frontend warping 활성화
    WarpCoordinator.registerImageDisplayWidget(this);
  }

  @override
  void dispose() {
    // WarpCoordinator에서 등록 해제
    WarpCoordinator.unregisterImageDisplayWidget();
    super.dispose();
  }
  
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
                  onTapDown: (details) {
                    // 뷰티스코어 탭에서 애니메이션 중일 때 이미지 클릭 시 애니메이션 즉시 완료
                    if (appState.currentTabIndex == 0 && (appState.isAnimationPlaying || appState.isAutoAnimationMode)) {
                      appState.completeAllAnimations();
                      return;
                    }
                    
                    // 확대/축소 모드에서 단일 클릭 처리
                    if (appState.currentTabIndex == 2 && 
                        (appState.warpMode == WarpMode.expand || appState.warpMode == WarpMode.shrink)) {
                      debugPrint('확대/축소 클릭 감지됨');
                      final localPosition = details.localPosition;
                      if (_isPointInImageBounds(localPosition, constraints, appState)) {
                        setState(() {
                          _startPoint = localPosition;
                          _currentPoint = localPosition;
                          _isDragging = false;
                        });
                        _performWarp(constraints, appState);
                        setState(() {
                          _startPoint = null;
                          _currentPoint = null;
                          _isDragging = false;
                        });
                      }
                    }
                  },
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
                  
                  // 프리스타일 탭에서 단일 터치인 경우 워핑 시작점 설정 (팬 모드가 아닐 때만)
                  if (appState.currentTabIndex == 2 && details.pointerCount == 1 && !_isPanMode) {
                    final localPosition = details.localFocalPoint;
                    if (_isPointInImageBounds(localPosition, constraints, appState)) {
                      setState(() {
                        _startPoint = localPosition;
                        _currentPoint = localPosition;
                        _isDragging = false;
                      });
                      
                      // 확대/축소 모드일 때는 클릭 즉시 워핑 실행
                      if (appState.warpMode == WarpMode.expand || appState.warpMode == WarpMode.shrink) {
                        _performWarp(constraints, appState);
                        setState(() {
                          _startPoint = null;
                          _currentPoint = null;
                          _isDragging = false;
                        });
                      }
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
                        // 워핑 모드: 워핑 도구 (확대/축소 모드가 아닐 때만)
                        if (_startPoint != null && appState.warpMode != WarpMode.expand && appState.warpMode != WarpMode.shrink) {
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
                  
                  // 전문가 탭에서 워핑 완료 처리 (팬 모드가 아니고, 확대/축소 모드가 아닐 때만)
                  if (appState.currentTabIndex == 2 && !_isPanMode && _startPoint != null && _currentPoint != null && _isDragging && 
                      appState.warpMode != WarpMode.expand && appState.warpMode != WarpMode.shrink) {
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
                        child: AnimatedSwitcher(
                          duration: const Duration(milliseconds: 150), // 부드러운 전환
                          switchInCurve: Curves.easeIn,
                          switchOutCurve: Curves.easeOut,
                          child: Transform.translate(
                            key: ValueKey(appState.currentImageId), // 키를 AnimatedSwitcher 자식으로 이동
                            offset: appState.panOffset,
                            child: Transform.scale(
                              scale: appState.zoomScale,
                              child: Image.memory(
                                appState.displayImage!,
                                fit: BoxFit.contain,
                                alignment: Alignment.center,
                                gaplessPlayback: true, // 이미지 전환 시 깜빡임 방지
                                filterQuality: FilterQuality.medium, // 필터 품질 최적화
                                isAntiAlias: true, // 안티 앨리어싱으로 부드러운 렌더링
                              ),
                            ),
                          ),
                        ),
                      ),
                    
                    // 이미지 영역 내 고정 위치 로딩 메시지 (AnimatedSwitcher로 깜빡임 방지)
                    Positioned(
                      bottom: 20, // 이미지 하단에서 20px 위
                      left: 0,
                      right: 0,
                      child: IgnorePointer(
                        child: Center(
                          child: AnimatedSwitcher(
                            duration: const Duration(milliseconds: 100), // 매우 빠른 페이드 인/아웃
                            switchInCurve: Curves.easeIn,
                            switchOutCurve: Curves.easeOut,
                            child: (appState.loadingPresetType != null || appState.isWarpLoading)
                                ? Container(
                                    key: ValueKey('loading_${appState.loadingPresetType ?? 'warp'}'), // 프리셋별 고유 키
                                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                    margin: const EdgeInsets.symmetric(horizontal: 20),
                                    decoration: BoxDecoration(
                                      color: Colors.black.withOpacity(0.8),
                                      borderRadius: BorderRadius.circular(25),
                                      boxShadow: [
                                        BoxShadow(
                                          color: Colors.black.withOpacity(0.3),
                                          blurRadius: 8,
                                          offset: const Offset(0, 4),
                                        ),
                                      ],
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        SizedBox(
                                          width: 18,
                                          height: 18,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2.5,
                                            valueColor: AlwaysStoppedAnimation<Color>(Colors.cyan.shade300),
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        Text(
                                          _getPresetMessage(appState.loadingPresetType, appState.currentProgress),
                                          style: TextStyle(
                                            color: Colors.cyan.shade300,
                                            fontSize: 14,
                                            fontWeight: FontWeight.w500,
                                            letterSpacing: 0.5,
                                            shadows: [
                                              Shadow(
                                                color: Colors.cyan.withOpacity(0.6),
                                                blurRadius: 4.0,
                                              ),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                  )
                                : const SizedBox.shrink(key: ValueKey('empty_loading')), // 빈 상태
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
                    
                    // 레이저 시각화 효과 (프리셋 탭에서만)
                    if (appState.currentTabIndex == 1 && appState.showLaserEffect && appState.currentLaserPreset != null)
                      Positioned(
                        left: imageOffset.dx,
                        top: imageOffset.dy,
                        width: imageDisplaySize.width,
                        height: imageDisplaySize.height,
                        child: CustomPaint(
                          painter: LaserEffectPainter(
                            presetType: appState.currentLaserPreset!,
                            landmarks: appState.landmarks,
                            imageWidth: appState.imageWidth,
                            imageHeight: appState.imageHeight,
                            containerSize: imageDisplaySize,
                            iterations: appState.laserIterations,
                            durationMs: appState.laserDurationMs,
                            zoomScale: appState.zoomScale,
                            panOffset: appState.panOffset,
                            originalContainerSize: constraints.biggest,
                          ),
                        ),
                      ),
                    
                    // 프리셋 시각화 (프리셋 탭에서만)
                    if (appState.currentTabIndex == 1 && appState.showPresetVisualization && appState.presetVisualizationData.isNotEmpty)
                      Positioned(
                        left: imageOffset.dx,
                        top: imageOffset.dy,
                        width: imageDisplaySize.width,
                        height: imageDisplaySize.height,
                        child: CustomPaint(
                          painter: PresetVisualizationPainter(
                            visualizationData: appState.presetVisualizationData,
                            imageWidth: appState.imageWidth,
                            imageHeight: appState.imageHeight,
                            containerSize: imageDisplaySize,
                            zoomScale: appState.zoomScale,
                            panOffset: appState.panOffset,
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
                            heroTag: "zoom_in_button",
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
                            heroTag: "zoom_out_button",
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
    
    // 재진단 중이면 워핑 비활성화
    if (appState.isReAnalyzing) {
      return;
    }
    
    if (_startPoint == null || _currentPoint == null) {
      debugPrint('시작점 또는 현재점이 null');
      return;
    }
    
    // 확대/축소 모드가 아니면서 드래그하지 않은 경우 리턴
    if ((appState.warpMode != WarpMode.expand && appState.warpMode != WarpMode.shrink) && !_isDragging) {
      debugPrint('드래그 모드이지만 드래그하지 않음');
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
      // 프론트엔드 워핑 시스템 사용
      await _applyWarp(appState, imageCoordinates);
    } catch (e) {
      appState.setError('변형 적용 실패: $e');
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
    if (appState.currentImage == null) return;
    
    // 워핑 작업 전에 히스토리 저장
    appState.saveToHistory();
    
    // 워핑 로딩 상태 시작
    appState.setWarpLoading(true);
    
    try {
      // 프론트엔드 워핑 시스템 사용
      final warpParams = WarpParameters(
        startX: coordinates['startX']!,
        startY: coordinates['startY']!,
        endX: coordinates['endX']!,
        endY: coordinates['endY']!,
        influenceRadius: appState.getInfluenceRadiusPixels(),
        strength: appState.warpStrength,
        mode: appState.warpMode,
      );
      
      final warpResult = await WarpFallbackManager.smartApplyWarp(
        imageBytes: appState.currentImage!,
        warpParams: warpParams,
      );
      
      if (warpResult.success && warpResult.resultBytes != null) {
        // 클라이언트에서 처리된 결과 - 이미지만 업데이트
        appState.updateCurrentImage(warpResult.resultBytes!);
        
        // 랜드마크 다시 검출 (프론트엔드 MediaPipe 사용)
        if (appState.currentImage != null) {
          try {
            final landmarkResult = await MediaPipeService.detectFaceLandmarks(appState.currentImage!);
            if (landmarkResult != null && landmarkResult['landmarks'] != null) {
              final rawLandmarks = landmarkResult['landmarks'] as List<List<double>>;
              final landmarks = MediaPipeService.convertToLandmarks(rawLandmarks);
              final source = landmarkResult['source'] ?? 'frontend_mediapipe';
              appState.setLandmarks(landmarks, resetAnalysis: false, source: source);
            }
          } catch (e) {
            debugPrint('랜드마크 검출 실패: $e');
            // 랜드마크 검출 실패는 무시하고 워핑 결과만 적용
          }
        }
        
      } else {
        throw Exception(warpResult.error ?? '프론트엔드 워핑 실패');
      }
      
    } catch (e) {
      appState.setError('변형 적용 실패: $e');
    } finally {
      // 워핑 로딩 상태 종료
      appState.setWarpLoading(false);
    }
  }
  
  // 프리셋별 메시지 반환 (진행 상황 포함)
  String _getPresetMessage(String? presetType, [int progress = 0]) {
    if (presetType == null) return '워핑 적용 중..';
    
    String baseMessage;
    String unit;
    
    switch (presetType) {
      case 'lower_jaw':
        baseMessage = '아래턱선 날렵하게 커스터마이징 중';
        unit = '샷';
        break;
      case 'middle_jaw':
        baseMessage = '중간턱 라인 자연스럽게 다듬는 중';
        unit = '샷';
        break;
      case 'cheek':
        baseMessage = '볼살 슬림하게 개선하는 중';
        unit = '샷';
        break;
      case 'front_protusion':
        baseMessage = '앞트임으로 더 큰 눈매 만드는 중';
        unit = '%';
        break;
      case 'back_slit':
        baseMessage = '뒷트임으로 시원한 눈매 연출 중';
        unit = '%';
        break;
      default:
        baseMessage = '프리셋 적용 중';
        unit = '';
        break;
    }
    
    // 진행 상황이 있으면 표시
    if (progress > 0) {
      return '$baseMessage.. $progress$unit';
    } else {
      return '$baseMessage..';
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
            // MediaPipe에서 이미 픽셀 좌표로 변환됨 - 화면 표시용으로 스케일링
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
            
            // MediaPipe에서 이미 픽셀 좌표로 변환됨 - 화면 표시용으로 스케일링
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
            // MediaPipe에서 이미 픽셀 좌표로 변환됨 - 화면 표시용으로 스케일링
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
        // MediaPipe에서 이미 픽셀 좌표로 변환됨 - 화면 표시용으로 스케일링
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
    canvas.drawCircle(position, VisualizationConstants.landmarkRadius, innerGlowPaint);
    
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
      ..color = VisualizationConstants.endPointColor.withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    
    canvas.drawCircle(startPoint, influenceRadius, radiusPaint);
    
    // 시작점
    final startPaint = Paint()
      ..color = VisualizationConstants.startPointColor
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
    const arrowLength = VisualizationConstants.arrowLength; // 2배 작게
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
    final scanAreaHeight = VisualizationConstants.scanAreaHeight;
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
        debugPrint('텍스트 애니메이션 에러: $e');
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
      ..color = VisualizationConstants.endPointColor.withOpacity(0.8)
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

/// 레이저 효과 페인터
class LaserEffectPainter extends CustomPainter {
  final String presetType;
  final List<Landmark> landmarks;
  final int imageWidth;
  final int imageHeight;
  final Size containerSize;
  final int iterations;
  final int durationMs;
  final double zoomScale;
  final Offset panOffset;
  final Size originalContainerSize;

  LaserEffectPainter({
    required this.presetType,
    required this.landmarks,
    required this.imageWidth,
    required this.imageHeight,
    required this.containerSize,
    required this.iterations,
    required this.durationMs,
    required this.zoomScale,
    required this.panOffset,
    required this.originalContainerSize,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (landmarks.isEmpty) return;

    final currentTime = DateTime.now().millisecondsSinceEpoch;
    // 전체 애니메이션 지속 시간에 맞춘 진행률 (0.0~1.0)
    final totalProgress = ((currentTime / 50) % (durationMs / 50)) / (durationMs / 50);
    // 각 이터레이션의 진행률
    final iterationProgress = (totalProgress * iterations) % 1.0;
    final animationProgress = iterationProgress;
    
    // 프리셋별 타겟 랜드마크 정의
    List<int> targetLandmarks = [];
    String treatmentArea = '';
    
    switch (presetType) {
      case 'lower_jaw':
        targetLandmarks = [150, 379, 172, 397, 169, 175, 176, 400, 379, 365, 397, 379];
        treatmentArea = '아래턱선';
        break;
      case 'middle_jaw':
        targetLandmarks = [172, 397, 216, 436, 135, 364, 150, 379];
        treatmentArea = '중간턱';
        break;
      case 'cheek':
        targetLandmarks = [
          215, 435, // 메인 볼 랜드마크
          132, 147, 187, 207, 192, 138, 214, // 왼쪽 볼 주변
          361, 376, 411, 427, 434, 367, 416  // 오른쪽 볼 주변
        ];
        treatmentArea = '볼';
        break;
      case 'front_protusion':
        targetLandmarks = [243, 463, 56, 190, 414, 286]; // 168, 6 삭제
        treatmentArea = '앞트임';
        break;
      case 'back_slit':
        targetLandmarks = [
          33, 359, // 메인 외안각
          124, 35, 111, 143, 353, 265, 340, 372 // 새로 추가된 랜드마크
        ];
        treatmentArea = '뒷트임';
        break;
    }
    
    if (targetLandmarks.isEmpty) return;
    
    // 레이저 빔 그리기
    for (int i = 0; i < targetLandmarks.length; i++) {
      final landmarkIndex = targetLandmarks[i];
      if (landmarkIndex >= landmarks.length) continue;
      
      final landmark = landmarks[landmarkIndex];
      
      // 이미지 좌표를 화면 좌표로 변환 (줌과 팬 고려)
      final normalizedX = landmark.x / imageWidth;
      final normalizedY = landmark.y / imageHeight;
      
      // 기본 이미지 영역에서의 좌표
      final baseX = normalizedX * containerSize.width;
      final baseY = normalizedY * containerSize.height;
      
      // 이미지 중심점 계산
      final imageCenter = Offset(containerSize.width / 2, containerSize.height / 2);
      
      // 이미지 중심 기준으로 좌표 변환
      final offsetFromCenter = Offset(baseX - imageCenter.dx, baseY - imageCenter.dy);
      
      // 줌 적용
      final scaledOffset = offsetFromCenter * zoomScale;
      
      // 실제 좌표 (중심점 + 줌된 오프셋 + 팬 오프셋)
      final landmarkX = imageCenter.dx + scaledOffset.dx + panOffset.dx;
      final landmarkY = imageCenter.dy + scaledOffset.dy + panOffset.dy;
      
      // 개별 레이저 포인트의 애니메이션 오프셋
      final pointAnimationOffset = (i * 0.1) % 1.0;
      final pointProgress = (animationProgress + pointAnimationOffset) % 1.0;
      
      // 레이저 빔 중심점
      final centerPoint = Offset(landmarkX, landmarkY);
      
      // 펄스 효과
      final pulseRadius = VisualizationConstants.pulseBaseRadius + (math.sin(pointProgress * math.pi * 4) * VisualizationConstants.pulseAmplitude);
      final pulseOpacity = (0.3 + (math.sin(pointProgress * math.pi * 2) * 0.4)).clamp(0.0, 1.0);
      
      // 외부 발광 링
      final outerGlowPaint = Paint()
        ..color = VisualizationConstants.startPointColor.withOpacity(pulseOpacity * 0.2)
        ..style = PaintingStyle.fill
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, VisualizationConstants.blurRadius);
      canvas.drawCircle(centerPoint, pulseRadius * 2, outerGlowPaint);
      
      // 중간 발광 링
      final middleGlowPaint = Paint()
        ..color = VisualizationConstants.startPointColor.withOpacity(pulseOpacity * 0.5)
        ..style = PaintingStyle.fill
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8.0);
      canvas.drawCircle(centerPoint, pulseRadius, middleGlowPaint);
      
      // 핵심 레이저 점
      final corePaint = Paint()
        ..color = VisualizationConstants.startPointColor.withOpacity(pulseOpacity)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(centerPoint, 4.0, corePaint);
      
      // 하이라이트
      final highlightPaint = Paint()
        ..color = Colors.white.withOpacity(pulseOpacity * 0.8)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(centerPoint, 2.0, highlightPaint);
      
      // 레이저 크로스헤어
      final crossPaint = Paint()
        ..color = VisualizationConstants.startPointColor.withOpacity(pulseOpacity * 0.6)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.0;
      
      // 수직선
      canvas.drawLine(
        Offset(landmarkX, landmarkY - 12),
        Offset(landmarkX, landmarkY + 12),
        crossPaint,
      );
      
      // 수평선
      canvas.drawLine(
        Offset(landmarkX - 12, landmarkY),
        Offset(landmarkX + 12, landmarkY),
        crossPaint,
      );
      
      // 스캐닝 라인 (위아래로 움직임)
      final scanOffset = math.sin(pointProgress * math.pi * 6) * VisualizationConstants.scanOffset;
      final scanPaint = Paint()
        ..color = Colors.cyan.withOpacity(pulseOpacity * 0.7)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;
      
      canvas.drawLine(
        Offset(landmarkX - 25, landmarkY + scanOffset),
        Offset(landmarkX + 25, landmarkY + scanOffset),
        scanPaint,
      );
    }
    
    // 레이저 애니메이션에서는 텍스트 표시하지 않음 (로딩 오버레이에서 처리)
  }

  @override
  bool shouldRepaint(LaserEffectPainter oldDelegate) {
    return true; // 항상 다시 그리기 (애니메이션을 위해)
  }
}

/// 프리셋 시각화를 그리는 CustomPainter
class PresetVisualizationPainter extends CustomPainter {
  final Map<String, dynamic> visualizationData;
  final int imageWidth;
  final int imageHeight;
  final Size containerSize;
  final double zoomScale;
  final Offset panOffset;

  PresetVisualizationPainter({
    required this.visualizationData,
    required this.imageWidth,
    required this.imageHeight,
    required this.containerSize,
    required this.zoomScale,
    required this.panOffset,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (visualizationData.isEmpty || !visualizationData.containsKey('transformations')) {
      return;
    }

    final transformations = visualizationData['transformations'] as List<Map<String, dynamic>>;
    
    for (final transformation in transformations) {
      _drawTransformation(canvas, transformation);
    }
  }

  void _drawTransformation(Canvas canvas, Map<String, dynamic> transformation) {
    final startX = transformation['startX'] as double;
    final startY = transformation['startY'] as double;
    final endX = transformation['endX'] as double;
    final endY = transformation['endY'] as double;
    final influenceRadius = transformation['influenceRadius'] as double;
    final ellipseRatio = transformation['ellipseRatio'] as double?;

    // 화면 좌표로 변환
    final startPoint = _transformToScreenCoords(startX, startY);
    final endPoint = _transformToScreenCoords(endX, endY);
    final radiusInScreen = influenceRadius * (containerSize.width / imageWidth) * zoomScale;

    // 1. 영향 반경 (타원 또는 원)
    final radiusPaint = Paint()
      ..color = VisualizationConstants.influenceCircleColor.withOpacity(0.2)
      ..style = PaintingStyle.fill;
    
    final radiusBorderPaint = Paint()
      ..color = VisualizationConstants.influenceCircleColor.withOpacity(0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    if (ellipseRatio != null) {
      // 타원형 영향반경
      final ellipseWidth = radiusInScreen * 2;
      final ellipseHeight = radiusInScreen * 2 * ellipseRatio;
      
      final ellipseRect = Rect.fromCenter(
        center: startPoint,
        width: ellipseWidth,
        height: ellipseHeight,
      );
      
      canvas.drawOval(ellipseRect, radiusPaint);
      _drawDashedOval(canvas, ellipseRect, radiusBorderPaint);
    } else {
      // 원형 영향반경 (기존 방식)
      canvas.drawCircle(startPoint, radiusInScreen, radiusPaint);
      _drawDashedCircle(canvas, startPoint, radiusInScreen, radiusBorderPaint);
    }

    // 3. 출발점 (빨간색 원)
    final startPaint = Paint()
      ..color = VisualizationConstants.startPointColor
      ..style = PaintingStyle.fill;
    canvas.drawCircle(startPoint, 4.0, startPaint);

    // 4. 끝점 (파란색 원)
    final endPaint = Paint()
      ..color = VisualizationConstants.endPointColor
      ..style = PaintingStyle.fill;
    canvas.drawCircle(endPoint, 4.0, endPaint);

    // 5. 화살표 (주황색)
    final arrowPaint = Paint()
      ..color = VisualizationConstants.arrowColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0
      ..strokeCap = StrokeCap.round;
    
    // 화살표 선
    canvas.drawLine(startPoint, endPoint, arrowPaint);
    
    // 화살표 머리
    _drawArrowHead(canvas, startPoint, endPoint, arrowPaint);

    // 6. 정보 라벨 (거리와 강도)
    final distance = transformation['distance'] as double;
    final strength = transformation['strength'] as double;
    final pullDistance = transformation['pullDistance'] as double;
    
    _drawInfoLabel(canvas, startPoint, distance, strength, pullDistance);
  }

  Offset _transformToScreenCoords(double x, double y) {
    // 정규화된 좌표로 변환
    final normalizedX = x / imageWidth;
    final normalizedY = y / imageHeight;
    
    // 기본 이미지 영역에서의 좌표
    final baseX = normalizedX * containerSize.width;
    final baseY = normalizedY * containerSize.height;
    
    // 이미지 중심점 계산
    final imageCenter = Offset(containerSize.width / 2, containerSize.height / 2);
    
    // 이미지 중심 기준으로 좌표 변환
    final offsetFromCenter = Offset(baseX - imageCenter.dx, baseY - imageCenter.dy);
    
    // 줌 적용
    final scaledOffset = offsetFromCenter * zoomScale;
    
    // 실제 좌표 (중심점 + 줌된 오프셋 + 팬 오프셋)
    return Offset(
      imageCenter.dx + scaledOffset.dx + panOffset.dx,
      imageCenter.dy + scaledOffset.dy + panOffset.dy,
    );
  }

  void _drawDashedCircle(Canvas canvas, Offset center, double radius, Paint paint) {
    const dashWidth = VisualizationConstants.dashWidth;
    const dashSpace = 3.0;
    final circumference = 2 * math.pi * radius;
    final dashCount = (circumference / (dashWidth + dashSpace)).floor();
    
    for (int i = 0; i < dashCount; i++) {
      final startAngle = (i * 2 * math.pi) / dashCount;
      final endAngle = startAngle + (dashWidth / circumference) * 2 * math.pi;
      
      final path = Path();
      path.addArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        endAngle - startAngle,
      );
      canvas.drawPath(path, paint);
    }
  }

  void _drawArrowHead(Canvas canvas, Offset start, Offset end, Paint paint) {
    final direction = end - start;
    final length = direction.distance;
    
    if (length == 0) return;
    
    final unitVector = direction / length;
    final arrowLength = math.min(VisualizationConstants.arrowHeadSize, length * 0.3);
    
    // 화살표 각도 (30도)
    const arrowAngle = math.pi / 6;
    
    // 화살표 왼쪽 날개
    final leftWing = Offset(
      end.dx - arrowLength * (unitVector.dx * math.cos(arrowAngle) + unitVector.dy * math.sin(arrowAngle)),
      end.dy - arrowLength * (unitVector.dy * math.cos(arrowAngle) - unitVector.dx * math.sin(arrowAngle)),
    );
    
    // 화살표 오른쪽 날개  
    final rightWing = Offset(
      end.dx - arrowLength * (unitVector.dx * math.cos(-arrowAngle) + unitVector.dy * math.sin(-arrowAngle)),
      end.dy - arrowLength * (unitVector.dy * math.cos(-arrowAngle) - unitVector.dx * math.sin(-arrowAngle)),
    );
    
    canvas.drawLine(end, leftWing, paint);
    canvas.drawLine(end, rightWing, paint);
  }

  void _drawInfoLabel(Canvas canvas, Offset position, double distance, double strength, double pullDistance) {
    final textStyle = TextStyle(
      color: Colors.white,
      fontSize: 10,
      fontWeight: FontWeight.w600,
      shadows: [
        Shadow(
          offset: const Offset(1, 1),
          blurRadius: 2,
          color: Colors.black.withOpacity(0.8),
        ),
      ],
    );

    final text = 'D:${distance.toStringAsFixed(0)}px\nS:${strength.toStringAsFixed(1)}\nP:${pullDistance.toStringAsFixed(0)}px';
    final textPainter = TextPainter(
      text: TextSpan(text: text, style: textStyle),
      textDirection: TextDirection.ltr,
    );
    
    textPainter.layout();
    
    // 라벨 위치 (출발점 오른쪽 위)
    final labelOffset = Offset(position.dx + 10, position.dy - 20);
    
    // 배경 그리기
    final backgroundPaint = Paint()
      ..color = Colors.black.withOpacity(0.7);
    
    final backgroundRect = Rect.fromLTWH(
      labelOffset.dx - 2,
      labelOffset.dy - 2,
      textPainter.width + 4,
      textPainter.height + 4,
    );
    
    canvas.drawRRect(
      RRect.fromRectAndRadius(backgroundRect, const Radius.circular(4)),
      backgroundPaint,
    );
    
    // 텍스트 그리기
    textPainter.paint(canvas, labelOffset);
  }

  void _drawDashedOval(Canvas canvas, Rect rect, Paint paint) {
    // 타원 점선 그리기 (간단한 구현)
    const dashWidth = VisualizationConstants.dashWidth;
    const dashSpace = 3.0;
    
    final path = Path()..addOval(rect);
    final pathMetrics = path.computeMetrics();
    
    for (final metric in pathMetrics) {
      double distance = 0.0;
      bool draw = true;
      
      while (distance < metric.length) {
        final nextDistance = distance + (draw ? dashWidth : dashSpace);
        if (nextDistance > metric.length) {
          if (draw) {
            final extractPath = metric.extractPath(distance, metric.length);
            canvas.drawPath(extractPath, paint);
          }
          break;
        } else {
          if (draw) {
            final extractPath = metric.extractPath(distance, nextDistance);
            canvas.drawPath(extractPath, paint);
          }
          distance = nextDistance;
          draw = !draw;
        }
      }
    }
  }

  @override
  bool shouldRepaint(PresetVisualizationPainter oldDelegate) {
    return visualizationData != oldDelegate.visualizationData ||
           zoomScale != oldDelegate.zoomScale ||
           panOffset != oldDelegate.panOffset;
  }
}