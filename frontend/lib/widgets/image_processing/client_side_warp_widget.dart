import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:typed_data';
import 'dart:async';
import '../../models/app_state.dart';
import '../../services/warp_service.dart';

/// 클라이언트 사이드 워핑을 지원하는 이미지 디스플레이 위젯
class ClientSideWarpWidget extends StatefulWidget {
  final double? width;
  final double? height;
  final bool enableWarp;
  final Function(String)? onError;

  const ClientSideWarpWidget({
    super.key,
    this.width,
    this.height,
    this.enableWarp = true,
    this.onError,
  });

  @override
  State<ClientSideWarpWidget> createState() => _ClientSideWarpWidgetState();
}

class _ClientSideWarpWidgetState extends State<ClientSideWarpWidget> {
  bool _isProcessing = false;
  String? _processingStatus;
  Timer? _statusTimer;

  @override
  void initState() {
    super.initState();
    _initializeWarpEngine();
  }

  @override
  void dispose() {
    _statusTimer?.cancel();
    super.dispose();
  }

  /// 워핑 엔진 초기화
  Future<void> _initializeWarpEngine() async {
    if (!widget.enableWarp) return;

    setState(() {
      _processingStatus = '워핑 엔진 초기화 중...';
    });

    final isLoaded = await WarpService.waitForEngineLoad(timeoutSeconds: 10);
    
    if (mounted) {
      setState(() {
        _processingStatus = isLoaded ? null : '워핑 엔진 로드 실패';
      });

      if (!isLoaded) {
        widget.onError?.call('JavaScript 워핑 엔진을 로드할 수 없습니다. 백엔드 워핑으로 폴백됩니다.');
      }
    }
  }

  /// 워핑 변형 적용 (클라이언트 사이드)
  Future<void> _applyWarp(
    double localX,
    double localY,
    double endLocalX,
    double endLocalY,
  ) async {
    final appState = context.read<AppState>();
    
    if (appState.currentImage == null || !widget.enableWarp) {
      return;
    }

    if (_isProcessing) {
      debugPrint('워핑 처리 중... 요청 무시');
      return;
    }

    if (!WarpService.isEngineLoaded) {
      widget.onError?.call('워핑 엔진이 준비되지 않았습니다');
      return;
    }

    setState(() {
      _isProcessing = true;
      _processingStatus = '워핑 처리 중...';
    });

    try {
      // 이미지 데이터 추출
      final imageDataMap = await WarpService.extractImageData(appState.currentImage!);
      
      if (imageDataMap == null) {
        throw Exception('이미지 데이터 추출 실패');
      }

      final imageData = imageDataMap['data'] as Uint8List;
      final imageWidth = imageDataMap['width'] as int;
      final imageHeight = imageDataMap['height'] as int;

      // 화면 좌표를 이미지 좌표로 변환
      final Size? widgetSize = _getWidgetSize();
      if (widgetSize == null) {
        throw Exception('위젯 크기를 측정할 수 없습니다');
      }

      final imageCoords = _screenToImageCoordinates(
        localX, localY, widgetSize, imageWidth, imageHeight);
      final imageEndCoords = _screenToImageCoordinates(
        endLocalX, endLocalY, widgetSize, imageWidth, imageHeight);

      // 영향 반경을 이미지 크기에 맞게 계산
      final influenceRadius = appState.getInfluenceRadiusPixels();

      setState(() {
        _processingStatus = '변형 계산 중...';
      });

      // JavaScript 워핑 엔진 호출
      final result = await WarpService.applyWarp(
        imageBytes: imageData,
        width: imageWidth,
        height: imageHeight,
        startX: imageCoords.dx,
        startY: imageCoords.dy,
        endX: imageEndCoords.dx,
        endY: imageEndCoords.dy,
        influenceRadius: influenceRadius,
        strength: appState.warpStrength,
        mode: appState.warpMode,
      );

      if (result == null) {
        throw Exception('워핑 처리 실패');
      }

      setState(() {
        _processingStatus = '이미지 변환 중...';
      });

      // 결과를 Flutter 이미지 형식으로 변환
      final convertedImage = await WarpService.imageDataToBytes(
        imageData: result,
        width: imageWidth,
        height: imageHeight,
        format: 'image/jpeg',
        quality: 0.95,
      );

      if (convertedImage == null) {
        throw Exception('이미지 변환 실패');
      }

      // 히스토리 저장 후 이미지 업데이트
      appState.saveToHistory();
      appState.setCurrentImage(convertedImage);

      setState(() {
        _processingStatus = '완료';
      });

      // 성공 메시지를 잠시 표시 후 제거
      _statusTimer?.cancel();
      _statusTimer = Timer(const Duration(milliseconds: 800), () {
        if (mounted) {
          setState(() {
            _processingStatus = null;
          });
        }
      });

    } catch (e) {
      debugPrint('클라이언트 사이드 워핑 실패: $e');
      widget.onError?.call('워핑 처리 실패: $e');
      
      setState(() {
        _processingStatus = null;
      });
    } finally {
      setState(() {
        _isProcessing = false;
      });
    }
  }

  /// 프리셋 적용 (클라이언트 사이드)
  Future<void> _applyPreset(String presetType) async {
    final appState = context.read<AppState>();
    
    if (appState.currentImage == null || 
        appState.landmarks.isEmpty ||
        !widget.enableWarp) {
      return;
    }

    if (_isProcessing) {
      debugPrint('워핑 처리 중... 프리셋 요청 무시');
      return;
    }

    if (!WarpService.isEngineLoaded) {
      widget.onError?.call('워핑 엔진이 준비되지 않았습니다');
      return;
    }

    setState(() {
      _isProcessing = true;
      _processingStatus = '프리셋 적용 중...';
    });

    try {
      final imageDataMap = await WarpService.extractImageData(appState.currentImage!);
      
      if (imageDataMap == null) {
        throw Exception('이미지 데이터 추출 실패');
      }

      final imageData = imageDataMap['data'] as Uint8List;
      final imageWidth = imageDataMap['width'] as int;
      final imageHeight = imageDataMap['height'] as int;

      setState(() {
        _processingStatus = '프리셋 계산 중...';
      });

      // JavaScript 프리셋 엔진 호출
      final result = await WarpService.applyPreset(
        imageBytes: imageData,
        width: imageWidth,
        height: imageHeight,
        landmarks: appState.landmarks,
        presetType: presetType,
      );

      if (result == null) {
        throw Exception('프리셋 적용 실패');
      }

      setState(() {
        _processingStatus = '이미지 변환 중...';
      });

      final convertedImage = await WarpService.imageDataToBytes(
        imageData: result,
        width: imageWidth,
        height: imageHeight,
        format: 'image/jpeg',
        quality: 0.95,
      );

      if (convertedImage == null) {
        throw Exception('이미지 변환 실패');
      }

      // 히스토리 저장 및 상태 업데이트
      appState.saveToHistory();
      appState.setCurrentImage(convertedImage);

      setState(() {
        _processingStatus = '프리셋 적용 완료';
      });

      _statusTimer?.cancel();
      _statusTimer = Timer(const Duration(milliseconds: 1000), () {
        if (mounted) {
          setState(() {
            _processingStatus = null;
          });
        }
      });

    } catch (e) {
      debugPrint('클라이언트 사이드 프리셋 실패: $e');
      widget.onError?.call('프리셋 적용 실패: $e');
      
      setState(() {
        _processingStatus = null;
      });
    } finally {
      setState(() {
        _isProcessing = false;
      });
    }
  }

  /// 화면 좌표를 이미지 좌표로 변환
  Offset _screenToImageCoordinates(
    double screenX,
    double screenY,
    Size widgetSize,
    int imageWidth,
    int imageHeight,
  ) {
    // 이미지 종횡비와 위젯 종횡비 계산
    final imageAspectRatio = imageWidth / imageHeight;
    final widgetAspectRatio = widgetSize.width / widgetSize.height;
    
    double imageDisplayWidth, imageDisplayHeight;
    double offsetX = 0, offsetY = 0;
    
    if (imageAspectRatio > widgetAspectRatio) {
      // 이미지가 위젯보다 넓음 - 위젯 너비에 맞춤
      imageDisplayWidth = widgetSize.width;
      imageDisplayHeight = widgetSize.width / imageAspectRatio;
      offsetY = (widgetSize.height - imageDisplayHeight) / 2;
    } else {
      // 이미지가 위젯보다 높음 - 위젯 높이에 맞춤
      imageDisplayHeight = widgetSize.height;
      imageDisplayWidth = widgetSize.height * imageAspectRatio;
      offsetX = (widgetSize.width - imageDisplayWidth) / 2;
    }
    
    // 상대적 좌표를 이미지 좌표로 변환
    final relativeX = (screenX - offsetX) / imageDisplayWidth;
    final relativeY = (screenY - offsetY) / imageDisplayHeight;
    
    final imageX = (relativeX * imageWidth).clamp(0.0, imageWidth.toDouble() - 1);
    final imageY = (relativeY * imageHeight).clamp(0.0, imageHeight.toDouble() - 1);
    
    return Offset(imageX, imageY);
  }

  /// 위젯 크기 측정
  Size? _getWidgetSize() {
    final context = this.context;
    final renderBox = context.findRenderObject() as RenderBox?;
    return renderBox?.size;
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return Stack(
          children: [
            // 기본 이미지 디스플레이
            if (appState.currentImage != null)
              GestureDetector(
                onPanStart: !widget.enableWarp || _isProcessing ? null : (details) {
                  // 워핑 시작점 기록은 상위 위젯에서 처리
                },
                onPanEnd: !widget.enableWarp || _isProcessing ? null : (details) {
                  // 워핑 적용은 상위 위젯에서 처리
                },
                child: Container(
                  width: widget.width,
                  height: widget.height,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.memory(
                      appState.currentImage!,
                      fit: BoxFit.contain,
                      width: widget.width,
                      height: widget.height,
                    ),
                  ),
                ),
              ),

            // 처리 상태 오버레이
            if (_processingStatus != null)
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
                        if (_isProcessing)
                          const CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 3,
                          ),
                        const SizedBox(height: 12),
                        Text(
                          _processingStatus!,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        if (_isProcessing)
                          const Padding(
                            padding: EdgeInsets.only(top: 8.0),
                            child: Text(
                              '클라이언트 사이드 처리',
                              style: TextStyle(
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

            // 엔진 상태 표시 (개발용)
            if (kDebugMode && widget.enableWarp)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: WarpService.isEngineLoaded 
                        ? Colors.green.withOpacity(0.8)
                        : Colors.red.withOpacity(0.8),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    WarpService.isEngineLoaded ? 'JS Ready' : 'JS Loading',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }

  /// 외부에서 호출할 수 있는 워핑 메서드
  Future<void> applyWarpFromCoordinates({
    required double startX,
    required double startY,
    required double endX,
    required double endY,
  }) async {
    await _applyWarp(startX, startY, endX, endY);
  }

  /// 외부에서 호출할 수 있는 프리셋 메서드
  Future<void> applyPresetTransformation(String presetType) async {
    await _applyPreset(presetType);
  }
}

/// 클라이언트 사이드 워핑 성능 모니터링 위젯
class WarpPerformanceMonitor extends StatelessWidget {
  final VoidCallback? onRunBenchmark;

  const WarpPerformanceMonitor({
    super.key,
    this.onRunBenchmark,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (!kDebugMode || appState.currentImage == null) {
          return const SizedBox.shrink();
        }

        return Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.8),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Icon(
                    WarpService.isEngineLoaded 
                        ? Icons.check_circle 
                        : Icons.error,
                    color: WarpService.isEngineLoaded 
                        ? Colors.green 
                        : Colors.red,
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    'JavaScript 워핑 엔진',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                WarpService.isEngineLoaded 
                    ? '✓ 클라이언트 사이드 워핑 사용 가능'
                    : '⚠ 백엔드 워핑으로 폴백',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 10,
                ),
              ),
              if (onRunBenchmark != null) ...[
                const SizedBox(height: 8),
                ElevatedButton(
                  onPressed: onRunBenchmark,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  ),
                  child: const Text(
                    '성능 벤치마크',
                    style: TextStyle(fontSize: 10),
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}