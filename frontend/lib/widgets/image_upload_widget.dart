import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:typed_data';
import '../models/app_state.dart';
import '../services/api_service.dart';
import '../utils/image_processor.dart';
import 'camera_capture_widget.dart';

/// 이미지 업로드 위젯
class ImageUploadWidget extends StatelessWidget {
  const ImageUploadWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 600),
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 업로드 아이콘
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(60),
              ),
              child: Icon(
                Icons.face,
                size: 60,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
            
            const SizedBox(height: 32),
            
            // 제목
            Text(
              'BeautyGen',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
            
            const SizedBox(height: 16),
            
            // 설명
            Text(
              'AI 기반 뷰티 분석과 자유 스타일링을 시작하세요',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
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
            
            // 지원 형식 안내
            Text(
              '지원 형식: JPEG, PNG, WebP',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
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
    final apiService = context.read<ApiService>();

    appState.setLoading(true);

    try {
      // 1. 이미지 업로드
      final uploadResponse = await apiService.uploadImage(imageBytes, 'camera_capture.jpg');
      
      // 2. 얼굴 랜드마크 자동 검출
      final landmarkResponse = await apiService.getFaceLandmarks(uploadResponse.imageId);
      
      // 3. 얼굴 기반 이미지 처리 (크롭 + 밝기 보정)
      final processedBytes = await ImageProcessor.processImageWithFaceDetection(
        imageBytes, 
        landmarkResponse.landmarks.cast<dynamic>(),
      );
      
      // 4. 처리된 이미지로 다시 업로드
      final processedUploadResponse = await apiService.uploadImage(processedBytes, 'processed_camera_capture.jpg');
      
      // 5. 앱 상태 업데이트
      appState.setImage(
        processedBytes,
        processedUploadResponse.imageId,
        processedUploadResponse.width,
        processedUploadResponse.height,
      );

      // 6. 랜드마크 다시 검출 (처리된 이미지 기준)
      final finalLandmarkResponse = await apiService.getFaceLandmarks(processedUploadResponse.imageId);
      appState.setLandmarks(finalLandmarkResponse.landmarks);

      appState.setLoading(false);
      
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
    final apiService = context.read<ApiService>();

    appState.setLoading(true);

    try {
      // 1. 이미지 업로드
      final uploadResponse = await apiService.uploadImage(imageBytes, fileName);
      
      // 2. 얼굴 랜드마크 자동 검출
      final landmarkResponse = await apiService.getFaceLandmarks(uploadResponse.imageId);
      
      // 3. 얼굴 기반 이미지 처리 (크롭 + 밝기 보정)
      final processedBytes = await ImageProcessor.processImageWithFaceDetection(
        imageBytes, 
        landmarkResponse.landmarks.cast<dynamic>(),
      );
      
      // 4. 처리된 이미지로 다시 업로드
      final processedUploadResponse = await apiService.uploadImage(processedBytes, 'processed_$fileName');
      
      // 5. 앱 상태 업데이트
      appState.setImage(
        processedBytes,
        processedUploadResponse.imageId,
        processedUploadResponse.width,
        processedUploadResponse.height,
      );

      // 6. 랜드마크 다시 검출 (처리된 이미지 기준)
      final finalLandmarkResponse = await apiService.getFaceLandmarks(processedUploadResponse.imageId);
      appState.setLandmarks(finalLandmarkResponse.landmarks);

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
}