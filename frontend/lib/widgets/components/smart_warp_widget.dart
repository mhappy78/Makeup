import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:provider/provider.dart';
import 'dart:math' as math;
import '../../models/app_state.dart';
import '../../models/face_regions.dart';
import '../../services/warp_fallback_manager.dart';
import '../../services/api_service.dart';
import '../../services/warp_coordinator.dart';
import '../analysis/beauty_score_visualizer.dart';

/// 스마트 워핑 위젯 - 자동 폴백 지원
class SmartWarpWidget extends StatefulWidget {
  final double? width;
  final double? height;

  const SmartWarpWidget({
    super.key,
    this.width,
    this.height,
  });

  @override
  State<SmartWarpWidget> createState() => SmartWarpWidgetState();
}

// State 클래스를 public으로 변경하여 외부에서 접근 가능하게 함

class SmartWarpWidgetState extends State<SmartWarpWidget> 
    with TickerProviderStateMixin {
  
  // 제스처 상태
  Offset? _startPoint;
  Offset? _currentPoint;
  Offset? _hoverPoint;
  bool _isDragging = false;
  bool _isHovering = false;
  bool _isPanMode = false;
  
  // 처리 상태
  bool _isProcessing = false;
  String? _processingSource;
  String? _statusMessage;
  
  // 애니메이션
  late AnimationController _rippleController;
  late Animation<double> _rippleAnimation;
  
  @override
  void initState() {
    super.initState();
    
    _rippleController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _rippleAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _rippleController, curve: Curves.easeOut),
    );
    
    // WarpCoordinator에 등록
    WarpCoordinator.registerSmartWarpWidget(this);
  }

  @override
  void dispose() {
    // WarpCoordinator에서 등록 해제
    WarpCoordinator.unregisterSmartWarpWidget();
    _rippleController.dispose();
    super.dispose();
  }

  /// 스마트 워핑 적용
  Future<void> _applySmartWarp(Offset start, Offset end) async {
    final appState = context.read<AppState>();
    final apiService = context.read<ApiService>();
    
    if (appState.currentImage == null || appState.currentImageId == null) {
      return;
    }

    setState(() {
      _isProcessing = true;
      _processingSource = null;
      _statusMessage = '최적 처리 방법 선택 중...';
    });

    try {
      // 화면 좌표를 이미지 좌표로 변환
      final Size? containerSize = _getContainerSize();
      if (containerSize == null) {
        throw Exception('위젯 크기를 측정할 수 없습니다');
      }

      final imageCoords = _screenToImageCoordinates(start, containerSize, appState);
      final imageEndCoords = _screenToImageCoordinates(end, containerSize, appState);

      // 워핑 파라미터 생성
      final warpParams = WarpParameters(
        startX: imageCoords.dx,
        startY: imageCoords.dy,
        endX: imageEndCoords.dx,
        endY: imageEndCoords.dy,
        influenceRadius: appState.getInfluenceRadiusPixels(),
        strength: appState.warpStrength,
        mode: appState.warpMode,
      );

      // 히스토리 저장
      appState.saveToHistory();

      // 스마트 워핑 실행
      final result = await WarpFallbackManager.smartApplyWarp(
        imageBytes: appState.currentImage!,
        imageId: appState.currentImageId!,
        warpParams: warpParams,
        apiService: apiService,
      );

      setState(() {
        _processingSource = result.source;
        _statusMessage = result.source == 'client' 
            ? '클라이언트 처리 완료' 
            : '백엔드 처리 완료';
      });

      if (result.success) {
        // 성공 시 상태 업데이트
        if (result.source == 'client') {
          appState.setCurrentImage(result.resultBytes!);
        } else {
          appState.updateImageFromWarp(
            result.resultBytes!,
            result.resultImageId!,
          );
        }

        // 성공 애니메이션
        _rippleController.forward().then((_) {
          _rippleController.reset();
        });

        // 상태 메시지 자동 제거
        Future.delayed(const Duration(milliseconds: 1500), () {
          if (mounted) {
            setState(() {
              _statusMessage = null;
            });
          }
        });

      } else {
        throw Exception(result.error ?? '워핑 처리 실패');
      }

    } catch (e) {
      setState(() {
        _statusMessage = '오류: $e';
      });
      
      appState.setError('워핑 실패: $e');
      
      // 에러 메시지 자동 제거
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          setState(() {
            _statusMessage = null;
          });
        }
      });
    } finally {
      setState(() {
        _isProcessing = false;
      });
    }
  }

  /// 스마트 프리셋 적용
  Future<void> applySmartPreset(String presetType) async {
    final appState = context.read<AppState>();
    final apiService = context.read<ApiService>();
    
    if (appState.currentImage == null || 
        appState.currentImageId == null ||
        appState.landmarks.isEmpty) {
      return;
    }

    setState(() {
      _isProcessing = true;
      _processingSource = null;
      _statusMessage = '프리셋 처리 중...';
    });

    try {
      appState.saveToHistory();

      final result = await WarpFallbackManager.smartApplyPreset(
        imageBytes: appState.currentImage!,
        imageId: appState.currentImageId!,
        landmarks: appState.landmarks,
        presetType: presetType,
        apiService: apiService,
      );

      setState(() {
        _processingSource = result.source;
        _statusMessage = '${_getPresetDisplayName(presetType)} 적용 완료';
      });

      if (result.success) {
        if (result.source == 'client') {
          appState.setCurrentImage(result.resultBytes!);
        } else {
          appState.updateImageFromPreset(
            result.resultBytes!,
            result.resultImageId!,
          );
        }

        _rippleController.forward().then((_) {
          _rippleController.reset();
        });

        Future.delayed(const Duration(milliseconds: 2000), () {
          if (mounted) {
            setState(() {
              _statusMessage = null;
            });
          }
        });

      } else {
        throw Exception(result.error ?? '프리셋 적용 실패');
      }

    } catch (e) {
      setState(() {
        _statusMessage = '프리셋 오류: $e';
      });
      
      appState.setError('프리셋 적용 실패: $e');
      
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          setState(() {
            _statusMessage = null;
          });
        }
      });
    } finally {
      setState(() {
        _isProcessing = false;
      });
    }
  }

  /// 제스처 처리
  void _handlePanStart(DragStartDetails details) {
    if (_isProcessing) return;
    
    final appState = context.read<AppState>();
    // 뷰티스코어 탭(0번)에서는 워핑 비활성화
    if (appState.currentTabIndex == 0) return;

    setState(() {
      _startPoint = details.localPosition;
      _currentPoint = details.localPosition;
      _isDragging = true;
      _isPanMode = false;
    });
  }

  void _handlePanUpdate(DragUpdateDetails details) {
    if (_isProcessing) return;
    
    final appState = context.read<AppState>();
    // 뷰티스코어 탭(0번)에서는 워핑 비활성화
    if (appState.currentTabIndex == 0) return;

    setState(() {
      _currentPoint = details.localPosition;
    });
  }

  void _handlePanEnd(DragEndDetails details) async {
    if (_isProcessing || _isPanMode) {
      setState(() {
        _startPoint = null;
        _currentPoint = null;
        _isDragging = false;
      });
      return;
    }
    
    final appState = context.read<AppState>();
    
    // 뷰티스코어 탭(0번)에서는 강제 분석 실행
    if (appState.currentTabIndex == 0) {
      setState(() {
        _startPoint = null;
        _currentPoint = null;
        _isDragging = false;
      });
      
      // 클릭(거리가 짧으면) 강제 분석 시작
      if (_startPoint != null && _currentPoint != null) {
        final distance = (_currentPoint! - _startPoint!).distance;
        if (distance < 10.0) {
          debugPrint('🎯 뷰티스코어 강제 분석 시작');
          appState.completeAllAnimations();
        }
      }
      return;
    }

    if (_startPoint != null && _currentPoint != null) {
      final distance = (_currentPoint! - _startPoint!).distance;
      
      if (distance > 10.0) {
        await _applySmartWarp(_startPoint!, _currentPoint!);
      }
    }

    setState(() {
      _startPoint = null;
      _currentPoint = null;
      _isDragging = false;
    });
  }

  void _handleLongPressStart(LongPressStartDetails details) {
    if (_isProcessing) return;

    setState(() {
      _isPanMode = true;
      _startPoint = details.localPosition;
    });
  }

  void _handleLongPressMoveUpdate(LongPressMoveUpdateDetails details) {
    if (_isPanMode && _startPoint != null) {
      final appState = context.read<AppState>();
      final delta = details.localPosition - _startPoint!;
      appState.addPanOffset(delta);
      
      setState(() {
        _startPoint = details.localPosition;
      });
    }
  }

  /// 좌표 변환
  Offset _screenToImageCoordinates(Offset screenPoint, Size containerSize, AppState appState) {
    final adjustedX = (screenPoint.dx - appState.panOffset.dx) / appState.zoomScale;
    final adjustedY = (screenPoint.dy - appState.panOffset.dy) / appState.zoomScale;
    
    final imageAspectRatio = appState.imageWidth / appState.imageHeight;
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
    
    final relativeX = (adjustedX - imageOffset.dx) / imageDisplaySize.width;
    final relativeY = (adjustedY - imageOffset.dy) / imageDisplaySize.height;
    
    final imageX = (relativeX * appState.imageWidth).clamp(0.0, appState.imageWidth.toDouble() - 1);
    final imageY = (relativeY * appState.imageHeight).clamp(0.0, appState.imageHeight.toDouble() - 1);
    
    return Offset(imageX, imageY);
  }

  Size? _getContainerSize() {
    final context = this.context;
    final renderBox = context.findRenderObject() as RenderBox?;
    return renderBox?.size;
  }

  String _getPresetDisplayName(String presetType) {
    switch (presetType) {
      case 'lower_jaw': return '아래턱';
      case 'middle_jaw': return '중간턱';
      case 'cheek': return '볼';
      case 'front_protusion': return '앞트임';
      case 'back_slit': return '뒷트임';
      default: return presetType;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return Stack(
          children: [
            // 메인 이미지
            if (appState.currentImage != null)
              MouseRegion(
                onHover: (event) {
                  setState(() {
                    _hoverPoint = event.localPosition;
                    _isHovering = true;
                  });
                },
                onExit: (event) {
                  setState(() {
                    _isHovering = false;
                  });
                },
                child: GestureDetector(
                  onPanStart: _handlePanStart,
                  onPanUpdate: _handlePanUpdate,
                  onPanEnd: _handlePanEnd,
                  onLongPressStart: _handleLongPressStart,
                  onLongPressMoveUpdate: _handleLongPressMoveUpdate,
                  child: Container(
                    width: widget.width,
                    height: widget.height,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Transform.translate(
                        offset: appState.panOffset,
                        child: Transform.scale(
                          scale: appState.zoomScale,
                          child: Image.memory(
                            appState.currentImage!,
                            fit: BoxFit.contain,
                            width: widget.width,
                            height: widget.height,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),

            // 랜드마크 오버레이 (기존 ImageDisplayWidget에서 가져온 애니메이션)
            if (appState.showLandmarks && appState.landmarks.isNotEmpty)
              Positioned.fill(
                child: CustomPaint(
                  painter: _AnimatedFaceRegionsPainter(
                    landmarks: appState.landmarks,
                    imageWidth: appState.imageWidth,
                    imageHeight: appState.imageHeight,
                    containerSize: Size(widget.width ?? 400, widget.height ?? 600),
                    regionVisibility: appState.regionVisibility,
                    animationProgress: appState.animationProgress,
                    currentAnimatingRegion: appState.currentAnimatingRegion,
                    showSpecialLandmarks: appState.showBeautyScore,
                    beautyScoreAnimationProgress: appState.beautyScoreAnimationProgress,
                  ),
                ),
              ),
            
            // 얼굴 스캔 애니메이션 오버레이 (자동 애니메이션 모드일 때)
            if (appState.isAutoAnimationMode)
              Positioned.fill(
                child: CustomPaint(
                  painter: _FaceScanAnimationPainter(
                    containerSize: Size(widget.width ?? 400, widget.height ?? 600),
                    imageWidth: appState.imageWidth,
                    imageHeight: appState.imageHeight,
                  ),
                ),
              ),
            
            // 분석 텍스트 오버레이 (자동 애니메이션 모드일 때)
            if (appState.isAutoAnimationMode)
              Positioned(
                top: 20,
                left: 0,
                right: 0,
                child: _AnalysisTextOverlay(),
              ),

            // 뷰티 스코어 시각화
            if (appState.showBeautyScore && appState.landmarks.isNotEmpty)
              Positioned.fill(
                child: CustomPaint(
                  painter: _BeautyScorePainter(
                    landmarks: appState.landmarks,
                    imageWidth: appState.imageWidth,
                    imageHeight: appState.imageHeight,
                    animationProgress: appState.beautyScoreAnimationProgress,
                  ),
                ),
              ),

            // 워핑 시각화
            if (_isDragging && _startPoint != null && _currentPoint != null)
              Positioned.fill(
                child: CustomPaint(
                  painter: _WarpVisualizationPainter(
                    startPoint: _startPoint!,
                    currentPoint: _currentPoint!,
                    influenceRadius: appState.getInfluenceRadiusForDisplay(
                      _getContainerSize() ?? const Size(100, 100)
                    ),
                    warpMode: appState.warpMode,
                  ),
                ),
              ),

            // 호버 효과 (뷰티스코어 탭에서는 비활성화)
            if (_isHovering && _hoverPoint != null && !_isDragging && !_isProcessing && appState.currentTabIndex != 0)
              Positioned.fill(
                child: CustomPaint(
                  painter: _HoverEffectPainter(
                    hoverPoint: _hoverPoint!,
                    influenceRadius: appState.getInfluenceRadiusForDisplay(
                      _getContainerSize() ?? const Size(100, 100)
                    ),
                  ),
                ),
              ),

            // 성공 리플 효과
            if (_rippleController.isAnimating)
              Positioned.fill(
                child: AnimatedBuilder(
                  animation: _rippleAnimation,
                  builder: (context, child) {
                    return CustomPaint(
                      painter: _SuccessRipplePainter(
                        animation: _rippleAnimation.value,
                        center: _startPoint ?? Offset.zero,
                      ),
                    );
                  },
                ),
              ),

            // 처리 상태 오버레이
            if (_isProcessing)
              Positioned.fill(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 3,
                        ),
                        const SizedBox(height: 12),
                        if (_statusMessage != null)
                          Text(
                            _statusMessage!,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        if (_processingSource != null)
                          Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(
                              _processingSource == 'client' ? '클라이언트 처리' : '서버 처리',
                              style: const TextStyle(
                                color: Colors.white70,
                                fontSize: 12,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),

            // 상태 메시지 (처리 완료 후)
            if (!_isProcessing && _statusMessage != null)
              Positioned(
                bottom: 16,
                left: 16,
                right: 16,
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: _getStatusColor().withOpacity(0.9),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _getStatusIcon(),
                        color: Colors.white,
                        size: 16,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _statusMessage!,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      if (_processingSource != null)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            _processingSource == 'client' ? 'JS' : 'API',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),

            // 워핑 모드 표시
            Positioned(
              top: 16,
              left: 16,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.7),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _getWarpModeIcon(appState.warpMode),
                      color: Colors.white,
                      size: 16,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      appState.warpMode.displayName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // 통계 표시 (디버그 모드)
            if (kDebugMode)
              Positioned(
                top: 16,
                right: 16,
                child: _buildDebugStats(),
              ),
          ],
        );
      },
    );
  }

  Widget _buildDebugStats() {
    final stats = WarpFallbackManager.getStatistics();
    
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '스마트 워핑 통계',
            style: TextStyle(
              color: Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '총 시도: ${stats.totalAttempts}',
            style: TextStyle(color: Colors.white, fontSize: 9),
          ),
          Text(
            '클라이언트 성공률: ${(stats.clientSuccessRate * 100).toStringAsFixed(1)}%',
            style: TextStyle(color: Colors.white, fontSize: 9),
          ),
          Text(
            '백엔드 폴백률: ${(stats.fallbackRate * 100).toStringAsFixed(1)}%',
            style: TextStyle(color: Colors.white, fontSize: 9),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor() {
    if (_statusMessage?.contains('완료') == true) {
      return Colors.green;
    } else if (_statusMessage?.contains('오류') == true) {
      return Colors.red;
    } else {
      return Colors.blue;
    }
  }

  IconData _getStatusIcon() {
    if (_statusMessage?.contains('완료') == true) {
      return Icons.check_circle;
    } else if (_statusMessage?.contains('오류') == true) {
      return Icons.error;
    } else {
      return Icons.info;
    }
  }

  IconData _getWarpModeIcon(WarpMode mode) {
    switch (mode) {
      case WarpMode.pull:
        return Icons.open_with;
      case WarpMode.push:
        return Icons.push_pin;
      case WarpMode.expand:
        return Icons.zoom_out_map;
      case WarpMode.shrink:
        return Icons.center_focus_weak;
    }
  }
}

// 커스텀 페인터들 (기존과 동일)
class _WarpVisualizationPainter extends CustomPainter {
  final Offset startPoint;
  final Offset currentPoint;
  final double influenceRadius;
  final WarpMode warpMode;

  _WarpVisualizationPainter({
    required this.startPoint,
    required this.currentPoint,
    required this.influenceRadius,
    required this.warpMode,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    // 영향 범위 원
    paint.color = Colors.yellow.withOpacity(0.6);
    canvas.drawCircle(startPoint, influenceRadius, paint);

    // 드래그 화살표
    paint.color = Colors.orange;
    paint.strokeWidth = 3;
    _drawArrow(canvas, startPoint, currentPoint, paint);

    // 시작점과 끝점
    paint.style = PaintingStyle.fill;
    paint.color = Colors.red;
    canvas.drawCircle(startPoint, 6, paint);
    
    paint.color = Colors.blue;
    canvas.drawCircle(currentPoint, 6, paint);
  }

  void _drawArrow(Canvas canvas, Offset start, Offset end, Paint paint) {
    canvas.drawLine(start, end, paint);
    
    final direction = (end - start);
    final length = direction.distance;
    if (length < 20) return;
    
    final normalizedDirection = direction / length;
    final arrowHead1 = end - normalizedDirection * 15 + 
        Offset(-normalizedDirection.dy, normalizedDirection.dx) * 8;
    final arrowHead2 = end - normalizedDirection * 15 + 
        Offset(normalizedDirection.dy, -normalizedDirection.dx) * 8;
    
    canvas.drawLine(end, arrowHead1, paint);
    canvas.drawLine(end, arrowHead2, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _HoverEffectPainter extends CustomPainter {
  final Offset hoverPoint;
  final double influenceRadius;

  _HoverEffectPainter({
    required this.hoverPoint,
    required this.influenceRadius,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..color = Colors.white.withOpacity(0.5);

    canvas.drawCircle(hoverPoint, influenceRadius, paint);
    
    paint.style = PaintingStyle.fill;
    paint.color = Colors.white.withOpacity(0.8);
    canvas.drawCircle(hoverPoint, 3, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _SuccessRipplePainter extends CustomPainter {
  final double animation;
  final Offset center;

  _SuccessRipplePainter({
    required this.animation,
    required this.center,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..color = Colors.green.withOpacity(1 - animation);

    final radius = animation * 100;
    canvas.drawCircle(center, radius, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _BeautyScorePainter extends CustomPainter {
  final List<Landmark> landmarks;
  final int imageWidth;
  final int imageHeight;
  final double animationProgress;

  _BeautyScorePainter({
    required this.landmarks,
    required this.imageWidth,
    required this.imageHeight,
    required this.animationProgress,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (landmarks.isEmpty) {
      debugPrint('🔍 BeautyScorePainter: 랜드마크 없음');
      return;
    }

    debugPrint('🎨 BeautyScorePainter: 애니메이션 진행도 ${(animationProgress * 100).toStringAsFixed(1)}%');

    final visualizer = BeautyScoreVisualizer(
      landmarks: landmarks,
      imageWidth: imageWidth,
      imageHeight: imageHeight,
      animationProgress: animationProgress,
    );

    // Calculate image display parameters
    final imageAspectRatio = imageWidth / imageHeight;
    final containerAspectRatio = size.width / size.height;
    
    late Size imageDisplaySize;
    late Offset imageOffset;
    
    if (imageAspectRatio > containerAspectRatio) {
      imageDisplaySize = Size(size.width, size.width / imageAspectRatio);
      imageOffset = Offset(0, (size.height - imageDisplaySize.height) / 2);
    } else {
      imageDisplaySize = Size(size.height * imageAspectRatio, size.height);
      imageOffset = Offset((size.width - imageDisplaySize.width) / 2, 0);
    }

    debugPrint('🖼️ 이미지 표시 크기: ${imageDisplaySize.width}x${imageDisplaySize.height}');
    visualizer.render(canvas, imageOffset, imageDisplaySize);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

// 기존 ImageDisplayWidget에서 가져온 애니메이션 클래스들

/// 애니메이션이 있는 얼굴 부위별 페인터
class _AnimatedFaceRegionsPainter extends CustomPainter {
  final List<Landmark> landmarks;
  final int imageWidth;
  final int imageHeight;
  final Size containerSize;
  final RegionVisibility regionVisibility;
  final Map<String, double> animationProgress;
  final String? currentAnimatingRegion;
  final bool showSpecialLandmarks;
  final double beautyScoreAnimationProgress;

  _AnimatedFaceRegionsPainter({
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

      // 애니메이션이 있는 부위인지 확인
      if (regionData.hasAnimation && animationProgress.containsKey(regionKey)) {
        _drawAnimatedRegion(
          canvas, 
          regionData, 
          regionKey, 
          imageOffset, 
          imageDisplaySize,
          linePaint,
        );
      } else if (!regionData.hasAnimation || (currentAnimatingRegion == null && animationProgress.isEmpty)) {
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
            
            for (final index in line) {
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
            
            if (pathStarted) {
              canvas.drawPath(path, linePaint);
            }
          }
        }
      }
    }
  }

  void _drawAnimatedRegion(
    Canvas canvas,
    RegionData regionData,
    String regionKey,
    Offset imageOffset,
    Size imageDisplaySize,
    Paint linePaint,
  ) {
    final progress = animationProgress[regionKey] ?? 0.0;
    
    // 현재 애니메이션 진행률에 따라 그릴 점과 선의 수 계산
    final totalPoints = regionData.indices.length;
    final pointsToShow = (totalPoints * progress).ceil();
    
    // 점 그리기
    for (int i = 0; i < pointsToShow; i++) {
      if (i < regionData.indices.length) {
        final index = regionData.indices[i];
        if (index < landmarks.length) {
          final landmark = landmarks[index];
          final screenX = imageOffset.dx + (landmark.x / imageWidth) * imageDisplaySize.width;
          final screenY = imageOffset.dy + (landmark.y / imageHeight) * imageDisplaySize.height;
          
          final pointPaint = Paint()
            ..color = regionData.color.withOpacity(0.8)
            ..style = PaintingStyle.fill;
          
          canvas.drawCircle(
            Offset(screenX, screenY),
            3.0,
            pointPaint,
          );
        }
      }
    }
    
    // 선 그리기
    for (final line in regionData.lines) {
      if (line.length >= 2) {
        final path = Path();
        bool pathStarted = false;
        
        for (final index in line) {
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
        
        if (pathStarted) {
          canvas.drawPath(path, linePaint);
        }
      }
    }
  }

  @override
  bool shouldRepaint(_AnimatedFaceRegionsPainter oldDelegate) {
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

/// 얼굴 스캔 애니메이션 페인터
class _FaceScanAnimationPainter extends CustomPainter {
  final Size containerSize;
  final int imageWidth;
  final int imageHeight;

  _FaceScanAnimationPainter({
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
  }

  @override
  bool shouldRepaint(_FaceScanAnimationPainter oldDelegate) {
    return true; // 항상 다시 그리기 (애니메이션을 위해)
  }
}

/// 분석 텍스트 오버레이 위젯
class _AnalysisTextOverlay extends StatefulWidget {
  const _AnalysisTextOverlay();

  @override
  State<_AnalysisTextOverlay> createState() => _AnalysisTextOverlayState();
}

class _AnalysisTextOverlayState extends State<_AnalysisTextOverlay>
    with TickerProviderStateMixin {
  late AnimationController _textController;
  late AnimationController _dotsController;
  late Animation<double> _fadeAnimation;
  
  int _currentTextIndex = 0;
  
  final List<String> _analysisTexts = [
    '얼굴 랜드마크 감지 중...',
    '얼굴 비율 분석 중...',
    '대칭성 계산 중...',
    '황금비율 측정 중...',
    '뷰티 스코어 계산 중...',
  ];

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
    
    _dotsController.repeat();
    _startTextAnimation();
  }

  void _startTextAnimation() async {
    for (int i = 0; i < _analysisTexts.length; i++) {
      setState(() {
        _currentTextIndex = i;
      });
      
      _textController.forward();
      await Future.delayed(const Duration(milliseconds: 2500));
      _textController.reverse();
      await Future.delayed(const Duration(milliseconds: 500));
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
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.7),
          borderRadius: BorderRadius.circular(25),
          border: Border.all(
            color: const Color(0xFF00FFFF).withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 스캔 아이콘
            SizedBox(
              width: 24,
              height: 24,
              child: AnimatedBuilder(
                animation: _dotsController,
                builder: (context, child) {
                  return Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: const Color(0xFF00FFFF),
                        width: 2,
                      ),
                    ),
                    child: Center(
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
                    ),
                  );
                },
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
                    style: const TextStyle(
                      color: Color(0xFF00FFFF),
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.5,
                    ),
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