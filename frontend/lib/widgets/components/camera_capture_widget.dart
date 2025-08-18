import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:provider/provider.dart';
import 'dart:typed_data';
import '../../models/app_state.dart';
import '../../utils/image_processor.dart';
import '../../services/api_service.dart';

/// 얼굴 가이드라인이 있는 카메라 촬영 위젯
class CameraCaptureWidget extends StatefulWidget {
  const CameraCaptureWidget({super.key});

  @override
  State<CameraCaptureWidget> createState() => _CameraCaptureWidgetState();
}

class _CameraCaptureWidgetState extends State<CameraCaptureWidget>
    with TickerProviderStateMixin {
  CameraController? _controller;
  bool _isInitialized = false;
  bool _isCapturing = false;
  int _countdown = 0;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    
    // 펄스 애니메이션 컨트롤러
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(
      begin: 1.0,
      end: 1.1,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));
    _pulseController.repeat(reverse: true);
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        debugPrint('카메라를 찾을 수 없습니다.');
        return;
      }

      // 전면 카메라 우선 선택
      CameraDescription? frontCamera;
      for (final camera in cameras) {
        if (camera.lensDirection == CameraLensDirection.front) {
          frontCamera = camera;
          break;
        }
      }

      final selectedCamera = frontCamera ?? cameras.first;

      _controller = CameraController(
        selectedCamera,
        ResolutionPreset.high,
        enableAudio: false,
      );

      await _controller!.initialize();
      
      if (mounted) {
        setState(() {
          _isInitialized = true;
        });
      }
    } catch (e) {
      debugPrint('카메라 초기화 오류: $e');
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _capturePhoto() async {
    if (!_isInitialized || _controller == null || _isCapturing) return;

    setState(() {
      _isCapturing = true;
      _countdown = 3;
    });

    // 3초 카운트다운
    for (int i = 3; i > 0; i--) {
      setState(() {
        _countdown = i;
      });
      await Future.delayed(const Duration(seconds: 1));
    }

    try {
      final image = await _controller!.takePicture();
      final bytes = await image.readAsBytes();
      
      // AppState와 ApiService 가져오기
      final appState = context.read<AppState>();
      final apiService = ApiService();
      
      // 로딩 상태 표시
      if (mounted) {
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => const Center(
            child: CircularProgressIndicator(),
          ),
        );
      }
      
      try {
        // 1. 임시 이미지 업로드
        final uploadResponse = await apiService.uploadImage(bytes, 'camera_capture.jpg');
        
        // 2. 얼굴 랜드마크 자동 검출
        final landmarkResponse = await apiService.getFaceLandmarks(uploadResponse.imageId);
        
        // 3. 얼굴 기반 이미지 처리 (크롭)
        final processedBytes = await ImageProcessor.processImageWithFaceDetection(
          bytes, 
          landmarkResponse.landmarks.cast<dynamic>(),
        );
        
        // 4. AppState에 처리된 이미지 설정
        appState.setCurrentImage(processedBytes);
        
        // 로딩 다이얼로그 닫기
        if (mounted) {
          Navigator.of(context).pop();
        }
        
        // 카메라 화면 닫기
        if (mounted) {
          Navigator.of(context).pop();
        }
      } catch (e) {
        debugPrint('얼굴 기반 처리 실패, 기본 크롭 적용: $e');
        
        // 얼굴 감지 실패 시 기본 3:4 크롭 적용
        final croppedBytes = await ImageProcessor.cropImageTo3x4(bytes);
        appState.setCurrentImage(croppedBytes);
        
        // 로딩 다이얼로그 닫기
        if (mounted) {
          Navigator.of(context).pop();
        }
        
        // 카메라 화면 닫기
        if (mounted) {
          Navigator.of(context).pop();
        }
      }
    } catch (e) {
      debugPrint('사진 촬영 오류: $e');
    } finally {
      setState(() {
        _isCapturing = false;
        _countdown = 0;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text(
          '얼굴 촬영',
          style: TextStyle(color: Colors.white),
        ),
      ),
      body: !_isInitialized
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Colors.white),
                  SizedBox(height: 16),
                  Text(
                    '카메라를 준비하고 있습니다...',
                    style: TextStyle(color: Colors.white),
                  ),
                ],
              ),
            )
          : Stack(
              children: [
                // 카메라 프리뷰 (3:4 비율로 크롭)
                Positioned.fill(
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      final screenWidth = constraints.maxWidth;
                      final screenHeight = constraints.maxHeight;
                      
                      // 화면을 3:4 비율로 계산
                      final targetWidth = screenWidth;
                      final targetHeight = screenWidth * 4 / 3;
                      
                      // 카메라 원본 비율
                      final cameraAspectRatio = _controller!.value.aspectRatio;
                      
                      // 카메라 프리뷰 크기 계산 (3:4 영역을 꽉 채우도록)
                      double cameraWidth, cameraHeight;
                      if (cameraAspectRatio > (3/4)) {
                        // 카메라가 더 넓음 - 높이 기준으로 맞추고 좌우 크롭
                        cameraHeight = targetHeight;
                        cameraWidth = cameraHeight * cameraAspectRatio;
                      } else {
                        // 카메라가 더 높음 - 너비 기준으로 맞추고 상하 크롭
                        cameraWidth = targetWidth;
                        cameraHeight = cameraWidth / cameraAspectRatio;
                      }
                      
                      return Center(
                        child: SizedBox(
                          width: targetWidth,
                          height: targetHeight,
                          child: ClipRect(
                            child: OverflowBox(
                              child: SizedBox(
                                width: cameraWidth,
                                height: cameraHeight,
                                child: CameraPreview(_controller!),
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
                
                // 얼굴 가이드라인 오버레이 (카메라 화면에 맞춤)
                Positioned.fill(
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      final screenWidth = constraints.maxWidth;
                      
                      // 카메라 화면과 동일한 3:4 비율 계산
                      final targetWidth = screenWidth;
                      final targetHeight = screenWidth * 4 / 3;
                      
                      return Center(
                        child: SizedBox(
                          width: targetWidth,
                          height: targetHeight,
                          child: AnimatedBuilder(
                            animation: _pulseAnimation,
                            builder: (context, child) {
                              return Transform.scale(
                                scale: _isCapturing ? 1.0 : _pulseAnimation.value * 0.05 + 0.95,
                                child: ColorFiltered(
                                  colorFilter: ColorFilter.mode(
                                    _isCapturing ? Colors.green.withOpacity(0.8) : Colors.yellow.withOpacity(0.8),
                                    BlendMode.srcATop,
                                  ),
                                  child: Image.asset(
                                    'assets/images/face_guide.png',
                                    width: targetWidth,
                                    height: targetHeight,
                                    fit: BoxFit.fill, // 가이드라인을 카메라 영역에 정확히 맞춤
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      );
                    },
                  ),
                ),
                
                // 카운트다운 표시
                if (_countdown > 0)
                  Center(
                    child: Container(
                      width: 120,
                      height: 120,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.9),
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          '$_countdown',
                          style: const TextStyle(
                            fontSize: 48,
                            fontWeight: FontWeight.bold,
                            color: Colors.black,
                          ),
                        ),
                      ),
                    ),
                  ),
                
                // 촬영 버튼
                Positioned(
                  bottom: 50,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: GestureDetector(
                      onTap: _capturePhoto,
                      child: AnimatedBuilder(
                        animation: _pulseAnimation,
                        builder: (context, child) {
                          return Transform.scale(
                            scale: _pulseAnimation.value,
                            child: Container(
                              width: 80,
                              height: 80,
                              decoration: BoxDecoration(
                                color: Colors.white,
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: Colors.grey.shade300,
                                  width: 4,
                                ),
                              ),
                              child: const Icon(
                                Icons.camera_alt,
                                size: 32,
                                color: Colors.black,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                ),
                
                // 안내 텍스트
                Positioned(
                  top: 100,
                  left: 20,
                  right: 20,
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.7),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Column(
                      children: [
                        Text(
                          '얼굴을 가이드라인에 맞춰 주세요',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        SizedBox(height: 8),
                        Text(
                          '• 얼굴이 가이드라인 안에 들어오도록 조정하세요\n• 조명이 밝은 곳에서 촬영하세요\n• 정면을 바라보고 촬영하세요',
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}
