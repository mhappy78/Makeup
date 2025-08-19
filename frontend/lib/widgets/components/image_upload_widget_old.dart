import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:typed_data';
import '../../models/app_state.dart';
import '../../services/mediapipe_service.dart';
import '../../utils/image_processor.dart';
import 'camera_capture_widget.dart';

/// 이미지 업로드 위젯
class ImageUploadWidget extends StatelessWidget {
  const ImageUploadWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: ConstrainedBox(
        constraints: BoxConstraints(
          minHeight: MediaQuery.of(context).size.height,
        ),
        child: Center(
          child: Container(
            constraints: const BoxConstraints(maxWidth: 600),
            padding: const EdgeInsets.fromLTRB(32, 16, 32, 32), // 상단 패딩만 16px로 줄임
            child: Column(
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                // 로고 이미지
                Container(
                  decoration: BoxDecoration(
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.15),
                        blurRadius: 20,
                        offset: const Offset(8, 8), // 오른쪽 아래 방향
                        spreadRadius: 0,
                      ),
                      BoxShadow(
                        color: Colors.black.withOpacity(0.08),
                        blurRadius: 40,
                        offset: const Offset(12, 12), // 더 멀리 오른쪽 아래
                        spreadRadius: -4,
                      ),
                    ],
                  ),
                  child: Image.network(
                    'images/logo_e.png',
                    width: 480,
                    height: 240,
                    fit: BoxFit.contain,
                    errorBuilder: (context, error, stackTrace) {
                      // 이미지 로드 실패 시 기본 아이콘 표시
                      return Container(
                        width: 480,
                        height: 240,
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primaryContainer,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Icon(
                          Icons.face,
                          size: 120,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                      );
                    },
                  ),
                ),
                
                const SizedBox(height: 48),
                
                // 업로드 버튼들
                Row(
                  children: [
                    // 이미지 선택 버튼
                    Expanded(
                      child: SizedBox(
                        height: 56,
                        child: FilledButton.icon(
                          onPressed: () => _pickAndUploadImage(context),
                          icon: const Icon(Icons.upload),
                          label: const Text('갤러리'),
                          style: FilledButton.styleFrom(
                            textStyle: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ),
                    
                    const SizedBox(width: 16),
                    
                    // 카메라 촬영 버튼
                    Expanded(
                      child: SizedBox(
                        height: 56,
                        child: OutlinedButton.icon(
                          onPressed: () => _openCamera(context),
                          icon: const Icon(Icons.camera_alt),
                          label: const Text('카메라'),
                          style: OutlinedButton.styleFrom(
                            textStyle: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 32),
                
                // 사진 촬영 가이드
                Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.lightbulb_outline,
                        size: 20,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '좋은 분석 결과를 위한 촬영 팁',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          color: Theme.of(context).colorScheme.primary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  
                  // 메인 포인트 - 정면 사진 강조
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.face,
                          size: 24,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '정면 얼굴 사진 필수!',
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '카메라를 똑바로 보고 촬영해주세요',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 12),
                  
                  // 추가 팁들
                  _buildTipRow(context, Icons.person, '혼자 촬영', '한 명만 나오도록 촬영해주세요'),
                  const SizedBox(height: 8),
                  _buildTipRow(context, Icons.wb_sunny_outlined, '밝은 조명', '자연광이나 밝은 실내에서'),
                  const SizedBox(height: 8),
                  _buildTipRow(context, Icons.crop_portrait, '얼굴 전체', '이마부터 턱까지 모두 보이도록'),
                  const SizedBox(height: 8),
                  _buildTipRow(context, Icons.visibility, '선명한 화질', '흔들리지 않게 또렷하게'),
                  
                  const SizedBox(height: 16),
                  
                  // 지원 형식 (작게 표시)
                  Center(
                    child: Text(
                      '지원 형식: JPEG, PNG, WebP',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant.withOpacity(0.7),
                        fontSize: 11,
                      ),
                    ),
                  ),
                ],
              ),
            ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _openCamera(BuildContext context) async {
    try {
      // 카메라 화면으로 이동
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => const CameraCaptureWidget(),
          fullscreenDialog: true,
        ),
      );
      
      // 카메라에서 돌아온 후 이미지가 설정되었다면 처리
      final appState = context.read<AppState>();
      if (appState.currentImage != null) {
        await _processCameraImage(context, appState.currentImage!);
      }
    } catch (e) {
      _showError(context, '카메라 오류: $e');
    }
  }

  Future<void> _processCameraImage(BuildContext context, Uint8List imageBytes) async {
    final appState = context.read<AppState>();

    appState.setLoading(true);

    try {
      debugPrint('🔍 프론트엔드에서 카메라 이미지 처리 시작...');
      
      // 1. 프론트엔드 MediaPipe로 얼굴 랜드마크 검출
      final landmarkResult = await MediaPipeService.detectFaceLandmarks(imageBytes);
      
      if (landmarkResult == null || landmarkResult['landmarks'] == null) {
        throw Exception('얼굴을 찾을 수 없습니다. 얼굴이 명확히 보이는 사진을 사용해주세요.');
      }

      final rawLandmarks = landmarkResult['landmarks'] as List<List<double>>;
      final landmarks = MediaPipeService.convertToLandmarks(rawLandmarks);
      
      debugPrint('✅ 프론트엔드에서 ${landmarks.length}개 랜드마크 검출 완료');
      
      // 2. 얼굴 기반 이미지 처리 (크롭 + 밝기 보정)
      final processedBytes = await ImageProcessor.processImageWithFaceDetection(
        imageBytes, 
        rawLandmarks.cast<dynamic>(),
      );
      
      // 3. 로컬 이미지 ID 생성 (백엔드 업로드 없음)
      final imageId = 'frontend_camera_${DateTime.now().millisecondsSinceEpoch}';
      
      // 4. 앱 상태 업데이트
      appState.setImage(
        processedBytes,
        imageId,
        landmarkResult['imageWidth'] ?? 800,
        landmarkResult['imageHeight'] ?? 600,
      );

      // 5. 처리된 이미지에서 랜드마크 재검출
      final finalLandmarkResult = await MediaPipeService.detectFaceLandmarks(processedBytes);
      
      if (finalLandmarkResult != null && finalLandmarkResult['landmarks'] != null) {
        final finalRawLandmarks = finalLandmarkResult['landmarks'] as List<List<double>>;
        final finalLandmarks = MediaPipeService.convertToLandmarks(finalRawLandmarks);
        final source = finalLandmarkResult['source'] ?? 'unknown';
        appState.setLandmarks(finalLandmarks, source: source);
        debugPrint('✅ 처리된 이미지에서 ${finalLandmarks.length}개 랜드마크 재검출 완료 (소스: $source)');
      } else {
        // 재검출 실패 시 원래 랜드마크 사용
        final source = landmarkResult['source'] ?? 'unknown';
        appState.setLandmarks(landmarks, source: source);
        debugPrint('⚠️ 처리된 이미지 재검출 실패, 원래 랜드마크 사용 (소스: $source)');
      }

      appState.setLoading(false);
      debugPrint('✅ 프론트엔드 카메라 이미지 처리 완료');
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('카메라 촬영 및 얼굴 인식 완료!'),
            backgroundColor: Colors.green,
          ),
        );
      }
      
    } catch (e) {
      appState.setError('카메라 이미지 처리 실패: $e');
      
      if (context.mounted) {
        _showError(context, e.toString());
      }
    }
  }

  Future<void> _pickAndUploadImage(BuildContext context) async {
    try {
      // 파일 선택
      final result = await FilePicker.platform.pickFiles(
        type: FileType.image,
        allowMultiple: false,
        withData: true,
      );

      if (result == null || result.files.isEmpty) {
        return;
      }

      final file = result.files.first;
      final fileName = file.name;
      final fileBytes = file.bytes;

      if (fileBytes == null) {
        _showError(context, '파일을 읽을 수 없습니다.');
        return;
      }

      // 파일 크기 검증 (10MB 제한)
      if (fileBytes.length > 10 * 1024 * 1024) {
        _showError(context, '파일 크기는 10MB 이하여야 합니다.');
        return;
      }

      // 이미지 형식 검증
      if (!_isValidImageFormat(fileName)) {
        _showError(context, '지원하지 않는 이미지 형식입니다. JPEG, PNG, WebP 파일을 선택해주세요.');
        return;
      }

      await _processImage(context, fileBytes, fileName);
      
    } catch (e) {
      _showError(context, '파일 선택 중 오류가 발생했습니다: $e');
    }
  }

  Future<void> _processImage(BuildContext context, Uint8List imageBytes, String fileName) async {
    final appState = context.read<AppState>();

    appState.setLoading(true);

    try {
      debugPrint('🔍 프론트엔드에서 파일 이미지 처리 시작...');
      
      // 1. 프론트엔드 MediaPipe로 얼굴 랜드마크 검출
      final landmarkResult = await MediaPipeService.detectFaceLandmarks(imageBytes);
      
      if (landmarkResult == null || landmarkResult['landmarks'] == null) {
        throw Exception('얼굴을 찾을 수 없습니다. 얼굴이 명확히 보이는 사진을 사용해주세요.');
      }

      final rawLandmarks = landmarkResult['landmarks'] as List<List<double>>;
      final landmarks = MediaPipeService.convertToLandmarks(rawLandmarks);
      
      debugPrint('✅ 프론트엔드에서 ${landmarks.length}개 랜드마크 검출 완료');
      
      // 2. 얼굴 기반 이미지 처리 (크롭 + 밝기 보정)
      final processedBytes = await ImageProcessor.processImageWithFaceDetection(
        imageBytes, 
        rawLandmarks.cast<dynamic>(),
      );
      
      // 3. 로컬 이미지 ID 생성 (백엔드 업로드 없음)
      final imageId = 'frontend_upload_${DateTime.now().millisecondsSinceEpoch}';
      
      // 4. 앱 상태 업데이트
      appState.setImage(
        processedBytes,
        imageId,
        landmarkResult['imageWidth'] ?? 800,
        landmarkResult['imageHeight'] ?? 600,
      );

      // 5. 처리된 이미지에서 랜드마크 재검출
      final finalLandmarkResult = await MediaPipeService.detectFaceLandmarks(processedBytes);
      
      if (finalLandmarkResult != null && finalLandmarkResult['landmarks'] != null) {
        final finalRawLandmarks = finalLandmarkResult['landmarks'] as List<List<double>>;
        final finalLandmarks = MediaPipeService.convertToLandmarks(finalRawLandmarks);
        final source = finalLandmarkResult['source'] ?? 'unknown';
        appState.setLandmarks(finalLandmarks, source: source);
        debugPrint('✅ 처리된 이미지에서 ${finalLandmarks.length}개 랜드마크 재검출 완료 (소스: $source)');
      } else {
        // 재검출 실패 시 원래 랜드마크 사용
        final source = landmarkResult['source'] ?? 'unknown';
        appState.setLandmarks(landmarks, source: source);
        debugPrint('⚠️ 처리된 이미지 재검출 실패, 원래 랜드마크 사용 (소스: $source)');
      }

      appState.setLoading(false);
      debugPrint('✅ 프론트엔드 파일 이미지 처리 완료');
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('이미지 업로드 및 얼굴 인식 완료!'),
            backgroundColor: Colors.green,
          ),
        );
      }
      
    } catch (e) {
      appState.setError('업로드 실패: $e');
      
      if (context.mounted) {
        _showError(context, e.toString());
      }
    }
  }

  bool _isValidImageFormat(String fileName) {
    final extension = fileName.toLowerCase().split('.').last;
    return ['jpg', 'jpeg', 'png', 'webp'].contains(extension);
  }

  void _showError(BuildContext context, String message) {
    if (!context.mounted) return;
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Theme.of(context).colorScheme.error,
        action: SnackBarAction(
          label: '확인',
          textColor: Theme.of(context).colorScheme.onError,
          onPressed: () {
            ScaffoldMessenger.of(context).hideCurrentSnackBar();
          },
        ),
      ),
    );
  }

  /// 촬영 팁 행을 빌드하는 헬퍼 함수
  Widget _buildTipRow(BuildContext context, IconData icon, String title, String description) {
    return Row(
      children: [
        Icon(
          icon,
          size: 18,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: Theme.of(context).colorScheme.onSurface,
                ),
              ),
              Text(
                description,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// 여러 얼굴 경고 메시지 표시
  void _showMultipleFacesWarning(BuildContext context, String warningMessage) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          icon: Icon(
            Icons.groups,
            color: Theme.of(context).colorScheme.primary,
            size: 32,
          ),
          title: const Text('여러 얼굴이 감지되었습니다'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                warningMessage,
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.lightbulb_outline,
                      size: 20,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '더 정확한 분석을 위해 한 명만 나온 사진을 다시 업로드해보세요',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('확인'),
            ),
          ],
        );
      },
    );
  }
}