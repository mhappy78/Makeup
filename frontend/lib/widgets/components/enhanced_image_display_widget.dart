import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:provider/provider.dart';
import '../../models/app_state.dart';
import '../../services/warp_service.dart';
import '../../services/api_service.dart';
import '../image_processing/client_side_warp_widget.dart';
import '../analysis/beauty_score_visualizer.dart';

/// 클라이언트 사이드 워핑을 지원하는 향상된 이미지 디스플레이 위젯
class EnhancedImageDisplayWidget extends StatefulWidget {
  final double? width;
  final double? height;
  final bool enableClientSideWarp;

  const EnhancedImageDisplayWidget({
    super.key,
    this.width,
    this.height,
    this.enableClientSideWarp = true,
  });

  @override
  State<EnhancedImageDisplayWidget> createState() => _EnhancedImageDisplayWidgetState();
}

class _EnhancedImageDisplayWidgetState extends State<EnhancedImageDisplayWidget> {
  final GlobalKey<_ClientSideWarpWidgetState> _warpWidgetKey = 
      GlobalKey<_ClientSideWarpWidgetState>();
  
  Offset? _startPoint;
  Offset? _currentPoint;
  Offset? _hoverPoint;
  bool _isDragging = false;
  bool _isHovering = false;
  bool _isPanMode = false;
  bool _useClientSideWarp = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _checkClientSideSupport();
  }

  /// 클라이언트 사이드 워핑 지원 여부 확인
  Future<void> _checkClientSideSupport() async {
    if (!widget.enableClientSideWarp) {
      setState(() {
        _useClientSideWarp = false;
      });
      return;
    }

    final isSupported = await WarpService.waitForEngineLoad(timeoutSeconds: 3);
    if (mounted) {
      setState(() {
        _useClientSideWarp = isSupported;
      });
      
      if (!isSupported && kDebugMode) {
        debugPrint('클라이언트 사이드 워핑 미지원 - 백엔드 워핑 사용');
      }
    }
  }

  /// 워핑 모드별 실제 처리 로직
  Future<void> _processWarp(Offset start, Offset end) async {
    final appState = context.read<AppState>();
    
    if (appState.currentImage == null) return;

    // 클라이언트 사이드 워핑 시도
    if (_useClientSideWarp && WarpService.isEngineLoaded) {
      try {
        await _warpWidgetKey.currentState?.applyWarpFromCoordinates(
          startX: start.dx,
          startY: start.dy,
          endX: end.dx,
          endY: end.dy,
        );
        return; // 성공하면 백엔드 호출 스킵
      } catch (e) {
        debugPrint('클라이언트 사이드 워핑 실패, 백엔드로 폴백: $e');
        setState(() {
          _errorMessage = '클라이언트 워핑 실패, 백엔드 처리중...';
        });
      }
    }

    // 백엔드 워핑 폴백
    await _applyBackendWarp(start, end);
  }

  /// 백엔드 워핑 처리 (기존 로직)
  Future<void> _applyBackendWarp(Offset start, Offset end) async {
    final appState = context.read<AppState>();
    final apiService = context.read<ApiService>();
    
    if (appState.currentImageId == null) return;

    try {
      appState.setWarpLoading(true);

      // 화면 좌표를 이미지 좌표로 변환
      final Size? containerSize = _getImageContainerSize();
      if (containerSize == null) return;

      final imageCoords = _screenToImageCoordinates(start, containerSize);
      final imageEndCoords = _screenToImageCoordinates(end, containerSize);

      // 히스토리 저장
      appState.saveToHistory();

      // API 호출
      final response = await apiService.applyWarp(
        appState.currentImageId!,
        imageCoords.dx,
        imageCoords.dy,
        imageEndCoords.dx,
        imageEndCoords.dy,
        appState.getInfluenceRadiusPixels(),
        appState.warpStrength,
        appState.warpMode.value,
      );

      // 상태 업데이트
      appState.updateImageFromWarp(
        response.imageBytes,
        response.imageId,
      );

      setState(() {
        _errorMessage = null;
      });

    } catch (e) {
      appState.setError('워핑 적용 실패: $e');
      setState(() {
        _errorMessage = '워핑 실패: $e';
      });
    } finally {
      appState.setWarpLoading(false);
    }
  }

  /// 프리셋 적용 처리
  Future<void> _applyPreset(String presetType) async {
    // 클라이언트 사이드 프리셋 시도
    if (_useClientSideWarp && WarpService.isEngineLoaded) {
      try {
        await _warpWidgetKey.currentState?.applyPresetTransformation(presetType);
        return;
      } catch (e) {
        debugPrint('클라이언트 사이드 프리셋 실패, 백엔드로 폴백: $e');
      }
    }

    // 백엔드 프리셋 폴백은 기존 로직 사용
    // (landmark_controls_widget.dart의 _applyPresetWithSettings 로직)
  }

  /// 화면 좌표를 이미지 좌표로 변환
  Offset _screenToImageCoordinates(Offset screenPoint, Size containerSize) {
    final appState = context.read<AppState>();
    
    // 줌과 팬 오프셋 적용
    final adjustedX = (screenPoint.dx - appState.panOffset.dx) / appState.zoomScale;
    final adjustedY = (screenPoint.dy - appState.panOffset.dy) / appState.zoomScale;
    
    // 이미지 표시 영역 계산
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
    
    // 상대적 좌표를 이미지 좌표로 변환
    final relativeX = (adjustedX - imageOffset.dx) / imageDisplaySize.width;
    final relativeY = (adjustedY - imageOffset.dy) / imageDisplaySize.height;
    
    final imageX = (relativeX * appState.imageWidth).clamp(0.0, appState.imageWidth.toDouble() - 1);
    final imageY = (relativeY * appState.imageHeight).clamp(0.0, appState.imageHeight.toDouble() - 1);
    
    return Offset(imageX, imageY);
  }

  /// 이미지 컨테이너 크기 측정
  Size? _getImageContainerSize() {
    final context = this.context;
    final renderBox = context.findRenderObject() as RenderBox?;
    return renderBox?.size;
  }

  /// 제스처 처리
  void _handlePanStart(DragStartDetails details) {
    setState(() {
      _startPoint = details.localPosition;
      _currentPoint = details.localPosition;
      _isDragging = true;
      _isPanMode = false;
    });
  }

  void _handlePanUpdate(DragUpdateDetails details) {
    setState(() {
      _currentPoint = details.localPosition;
    });
  }

  void _handlePanEnd(DragEndDetails details) async {
    if (_startPoint != null && _currentPoint != null && !_isPanMode) {
      final distance = (_currentPoint! - _startPoint!).distance;
      
      // 최소 거리 체크 (의도치 않은 터치 방지)
      if (distance > 10.0) {
        await _processWarp(_startPoint!, _currentPoint!);
      }
    }

    setState(() {
      _startPoint = null;
      _currentPoint = null;
      _isDragging = false;
      _isPanMode = false;
    });
  }

  void _handleLongPressStart(LongPressStartDetails details) {
    setState(() {
      _isPanMode = true;
      _startPoint = details.localPosition;
    });
  }

  void _handleLongPressMoveUpdate(LongPressMoveUpdateDetails details) {
    if (_isPanMode) {
      final appState = context.read<AppState>();
      final delta = details.localPosition - _startPoint!;
      appState.addPanOffset(delta);
      
      setState(() {
        _startPoint = details.localPosition;
      });
    }
  }

  /// 에러 메시지 처리
  void _handleError(String error) {
    setState(() {
      _errorMessage = error;
    });
    
    // 에러 메시지 자동 제거
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        setState(() {
          _errorMessage = null;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return Stack(
          children: [
            // 클라이언트 사이드 워핑 위젯
            ClientSideWarpWidget(
              key: _warpWidgetKey,
              width: widget.width,
              height: widget.height,
              enableWarp: _useClientSideWarp,
              onError: _handleError,
            ),
            
            // 제스처 감지 오버레이
            Positioned.fill(
              child: GestureDetector(
                onPanStart: _handlePanStart,
                onPanUpdate: _handlePanUpdate,
                onPanEnd: _handlePanEnd,
                onLongPressStart: _handleLongPressStart,
                onLongPressMoveUpdate: _handleLongPressMoveUpdate,
                onPointerHover: (event) {
                  setState(() {
                    _hoverPoint = event.localPosition;
                    _isHovering = true;
                  });
                },
                onPointerExit: (event) {
                  setState(() {
                    _isHovering = false;
                  });
                },
                child: Container(
                  color: Colors.transparent,
                ),
              ),
            ),

            // 시각적 피드백 오버레이
            if (_isDragging && _startPoint != null && _currentPoint != null)
              Positioned.fill(
                child: CustomPaint(
                  painter: _WarpVisualizationPainter(
                    startPoint: _startPoint!,
                    currentPoint: _currentPoint!,
                    influenceRadius: appState.getInfluenceRadiusForDisplay(
                      _getImageContainerSize() ?? const Size(100, 100)
                    ),
                    warpMode: appState.warpMode,
                  ),
                ),
              ),

            // 호버 효과
            if (_isHovering && _hoverPoint != null && !_isDragging)
              Positioned.fill(
                child: CustomPaint(
                  painter: _HoverEffectPainter(
                    hoverPoint: _hoverPoint!,
                    influenceRadius: appState.getInfluenceRadiusForDisplay(
                      _getImageContainerSize() ?? const Size(100, 100)
                    ),
                  ),
                ),
              ),

            // 뷰티 스코어 시각화
            if (appState.showBeautyScore)
              Positioned.fill(
                child: BeautyScoreVisualizer(),
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
                    if (_useClientSideWarp) ...[
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                        decoration: BoxDecoration(
                          color: Colors.green,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          'JS',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 8,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            // 에러 메시지
            if (_errorMessage != null)
              Positioned(
                bottom: 16,
                left: 16,
                right: 16,
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red.withOpacity(0.9),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),

            // 성능 모니터 (디버그 모드)
            if (kDebugMode)
              Positioned(
                bottom: 16,
                right: 16,
                child: _WarpPerformanceIndicator(
                  useClientSide: _useClientSideWarp,
                  onToggleMode: () async {
                    if (!_useClientSideWarp) {
                      final isLoaded = await WarpService.waitForEngineLoad(timeoutSeconds: 5);
                      setState(() {
                        _useClientSideWarp = isLoaded;
                      });
                    } else {
                      setState(() {
                        _useClientSideWarp = false;
                      });
                    }
                  },
                ),
              ),
          ],
        );
      },
    );
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

/// 워핑 시각화 페인터
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

/// 호버 효과 페인터
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

/// 성능 지표 위젯
class _WarpPerformanceIndicator extends StatelessWidget {
  final bool useClientSide;
  final VoidCallback onToggleMode;

  const _WarpPerformanceIndicator({
    required this.useClientSide,
    required this.onToggleMode,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onToggleMode,
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.8),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              useClientSide ? Icons.flash_on : Icons.cloud,
              color: useClientSide ? Colors.green : Colors.orange,
              size: 20,
            ),
            const SizedBox(height: 4),
            Text(
              useClientSide ? 'Client' : 'Server',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}