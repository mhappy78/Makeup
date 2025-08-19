import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import '../../models/app_state.dart';
import '../../services/mediapipe_service.dart';
import '../../utils/image_processor.dart';
import 'camera_capture_widget.dart';

/// 이미지 업로드 위젯 - 파일 선택과 카메라 촬영 지원
class ImageUploadWidget extends StatefulWidget {
  const ImageUploadWidget({super.key});

  @override
  State<ImageUploadWidget> createState() => _ImageUploadWidgetState();
}

class _ImageUploadWidgetState extends State<ImageUploadWidget> {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 600),
          child: SingleChildScrollView(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // 헤더 아이콘과 제목
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.photo_camera,
                    size: 60,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                
                const SizedBox(height: 32),
                
                Text(
                  '사진 업로드',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.onBackground,
                  ),
                ),
                
                const SizedBox(height: 16),
                
                Text(
                  '갤러리에서 사진을 선택하거나 카메라로 촬영해주세요',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                  textAlign: TextAlign.center,
                ),
                
                const SizedBox(height: 48),
                
                // 업로드 버튼들
                Row(
                  children: [
                    // 갤러리 버튼
                    Expanded(
                      child: Container(
                        height: 64,
                        child: ElevatedButton.icon(
                          onPressed: () => _pickImageFromGallery(context),
                          icon: const Icon(Icons.photo_library),
                          label: const Text('갤러리'),
                          style: ElevatedButton.styleFrom(
                            textStyle: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ),
                    
                    const SizedBox(width: 16),
                    
                    // 카메라 버튼
                    Expanded(
                      child: Container(
                        height: 64,
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
      
      // 1. 프론트엔드 MediaPipe로 얼굴 랜드마크 검출
      final landmarkResult = await MediaPipeService.detectFaceLandmarks(imageBytes);
      
      if (landmarkResult == null || landmarkResult['landmarks'] == null) {
        throw Exception('얼굴을 찾을 수 없습니다. 얼굴이 명확히 보이는 사진을 사용해주세요.');
      }

      final rawLandmarks = landmarkResult['landmarks'] as List<List<double>>;
      final landmarks = MediaPipeService.convertToLandmarks(rawLandmarks);
      
      
      // 2. 얼굴 기반 이미지 처리 (크롭 + 밝기 보정)
      final processedBytes = await ImageProcessor.processImageWithFaceDetection(
        imageBytes, 
        rawLandmarks.cast<dynamic>(),
      );
      
      // 3. 로컬 이미지 ID 생성 (백엔드 업로드 없음)
      final imageId = 'frontend_camera_${DateTime.now().millisecondsSinceEpoch}';
      
      // 4. 처리된 이미지에서 랜드마크 재검출 (올바른 이미지 크기로)
      final finalLandmarkResult = await MediaPipeService.detectFaceLandmarks(processedBytes);
      
      if (finalLandmarkResult != null && finalLandmarkResult['landmarks'] != null) {
        final finalRawLandmarks = finalLandmarkResult['landmarks'] as List<List<double>>;
        final finalLandmarks = MediaPipeService.convertToLandmarks(finalRawLandmarks);
        final source = finalLandmarkResult['source'] ?? 'unknown';
        
        // 5. 앱 상태 업데이트 (처리된 이미지 크기 사용)
        appState.setImage(
          processedBytes,
          imageId,
          finalLandmarkResult['imageWidth'] ?? 800,  // 처리된 이미지 크기
          finalLandmarkResult['imageHeight'] ?? 600, // 처리된 이미지 크기
        );
        
        appState.setLandmarks(finalLandmarks, source: source);
      } else {
        // 재검출 실패 시 원래 이미지 크기와 랜드마크 사용
        appState.setImage(
          processedBytes,
          imageId,
          landmarkResult['imageWidth'] ?? 800,
          landmarkResult['imageHeight'] ?? 600,
        );
        
        final source = landmarkResult['source'] ?? 'unknown';
        appState.setLandmarks(landmarks, source: source);
      }

      appState.setLoading(false);
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('사진 촬영 및 얼굴 인식 완료!'),
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

  Future<void> _pickImageFromGallery(BuildContext context) async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.image,
        allowMultiple: false,
        withData: true,
      );

      if (result != null && result.files.single.bytes != null) {
        final fileBytes = result.files.single.bytes!;
        final fileName = result.files.single.name;
        
        if (!_isValidImageFormat(fileName)) {
          _showError(context, '지원하지 않는 이미지 형식입니다. JPEG, PNG, WebP 파일을 선택해주세요.');
          return;
        }

        await _processImage(context, fileBytes, fileName);
      }
      
    } catch (e) {
      _showError(context, '파일 선택 중 오류가 발생했습니다: $e');
    }
  }

  Future<void> _processImage(BuildContext context, Uint8List imageBytes, String fileName) async {
    final appState = context.read<AppState>();

    appState.setLoading(true);

    try {
      
      // 1. 프론트엔드 MediaPipe로 얼굴 랜드마크 검출
      final landmarkResult = await MediaPipeService.detectFaceLandmarks(imageBytes);
      
      if (landmarkResult == null || landmarkResult['landmarks'] == null) {
        throw Exception('얼굴을 찾을 수 없습니다. 얼굴이 명확히 보이는 사진을 사용해주세요.');
      }

      final rawLandmarks = landmarkResult['landmarks'] as List<List<double>>;
      final landmarks = MediaPipeService.convertToLandmarks(rawLandmarks);
      
      
      // 2. 얼굴 기반 이미지 처리 (크롭 + 밝기 보정)
      final processedBytes = await ImageProcessor.processImageWithFaceDetection(
        imageBytes, 
        rawLandmarks.cast<dynamic>(),
      );
      
      // 3. 로컬 이미지 ID 생성 (백엔드 업로드 없음)
      final imageId = 'frontend_upload_${DateTime.now().millisecondsSinceEpoch}';
      
      // 4. 처리된 이미지에서 랜드마크 재검출 (올바른 이미지 크기로)
      final finalLandmarkResult = await MediaPipeService.detectFaceLandmarks(processedBytes);
      
      if (finalLandmarkResult != null && finalLandmarkResult['landmarks'] != null) {
        final finalRawLandmarks = finalLandmarkResult['landmarks'] as List<List<double>>;
        final finalLandmarks = MediaPipeService.convertToLandmarks(finalRawLandmarks);
        final source = finalLandmarkResult['source'] ?? 'unknown';
        
        // 5. 앱 상태 업데이트 (처리된 이미지 크기 사용)
        appState.setImage(
          processedBytes,
          imageId,
          finalLandmarkResult['imageWidth'] ?? 800,  // 처리된 이미지 크기
          finalLandmarkResult['imageHeight'] ?? 600, // 처리된 이미지 크기
        );
        
        appState.setLandmarks(finalLandmarks, source: source);
      } else {
        // 재검출 실패 시 원래 이미지 크기와 랜드마크 사용
        appState.setImage(
          processedBytes,
          imageId,
          landmarkResult['imageWidth'] ?? 800,
          landmarkResult['imageHeight'] ?? 600,
        );
        
        final source = landmarkResult['source'] ?? 'unknown';
        appState.setLandmarks(landmarks, source: source);
      }

      appState.setLoading(false);
      
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

  Widget _buildTipRow(BuildContext context, IconData icon, String title, String description) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: RichText(
            text: TextSpan(
              children: [
                TextSpan(
                  text: '$title: ',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
                TextSpan(
                  text: description,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant.withOpacity(0.8),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  void _showError(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
      ),
    );
  }
}