import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:typed_data';

import '../config/app_constants.dart';
import '../models/app_state.dart';
import '../services/api_service.dart';
import '../utils/image_processor.dart';
import '../utils/file_validator.dart';
import '../utils/ui_helpers.dart';
import 'camera_capture_widget.dart';
import 'components/logo_widget.dart';
import 'components/upload_buttons.dart';
import 'components/photography_tips.dart';

/// BeautyGen 이미지 업로드 위젯
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
            padding: const EdgeInsets.fromLTRB(32, 16, 32, 32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                // 로고 이미지
                const LogoWidget(),
                
                const SizedBox(height: 48),
                
                // 업로드 버튼들
                UploadButtons(
                  onGalleryPressed: () => _pickAndUploadImage(context),
                  onCameraPressed: () => _openCamera(context),
                ),
                
                const SizedBox(height: 32),
                
                // 사진 촬영 가이드
                const PhotographyTips(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// 카메라 촬영 열기
  Future<void> _openCamera(BuildContext context) async {
    try {
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => const CameraCaptureWidget(),
          fullscreenDialog: true,
        ),
      );
      
      final appState = context.read<AppState>();
      if (appState.currentImage != null) {
        await _processImage(context, appState.currentImage!, 'camera_capture.jpg');
      }
    } catch (e) {
      UiHelpers.showErrorSnackBar(context, '카메라 오류: $e');
    }
  }

  /// 통합 이미지 처리 메서드
  Future<void> _processImage(BuildContext context, Uint8List imageBytes, String fileName) async {
    final appState = context.read<AppState>();
    final apiService = context.read<ApiService>();

    appState.setLoading(true);

    try {
      // 1. 이미지 업로드
      final uploadResponse = await apiService.uploadImage(imageBytes, fileName);
      
      // 2. 얼굴 랜드마크 검출
      final landmarkResponse = await apiService.getFaceLandmarks(uploadResponse.imageId);
      
      // 여러 얼굴 경고 메시지 표시
      if (landmarkResponse.warningMessage != null && context.mounted) {
        UiHelpers.showMultipleFacesWarningDialog(context, landmarkResponse.warningMessage!);
      }
      
      // 3. 얼굴 기반 이미지 처리
      final processedBytes = await ImageProcessor.processImageWithFaceDetection(
        imageBytes, 
        landmarkResponse.landmarks.cast<dynamic>(),
      );
      
      // 4. 처리된 이미지 재업로드
      final processedUploadResponse = await apiService.uploadImage(
        processedBytes, 
        'processed_$fileName',
      );
      
      // 5. 앱 상태 업데이트
      appState.setImage(
        processedBytes,
        processedUploadResponse.imageId,
        processedUploadResponse.width,
        processedUploadResponse.height,
      );

      // 6. 최종 랜드마크 검출
      final finalLandmarkResponse = await apiService.getFaceLandmarks(processedUploadResponse.imageId);
      appState.setLandmarks(finalLandmarkResponse.landmarks);

      appState.setLoading(false);
      
      if (context.mounted) {
        final message = fileName.contains('camera') 
            ? '카메라 촬영 및 얼굴 인식 완료!' 
            : '이미지 업로드 및 얼굴 인식 완료!';
        UiHelpers.showSuccessSnackBar(context, message);
      }
      
    } catch (e) {
      appState.setError('이미지 처리 실패: $e');
      
      if (context.mounted) {
        UiHelpers.showErrorSnackBar(context, e.toString());
      }
    }
  }

  /// 갤러리에서 이미지 선택 및 업로드
  Future<void> _pickAndUploadImage(BuildContext context) async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.image,
        allowMultiple: false,
        withData: true,
      );

      if (result == null || result.files.isEmpty) return;

      final file = result.files.first;
      final fileBytes = file.bytes;

      if (fileBytes == null) {
        UiHelpers.showErrorSnackBar(context, '파일을 읽을 수 없습니다.');
        return;
      }

      // 파일 검증
      final errorMessage = FileValidator.getValidationErrorMessage(
        file.name, 
        fileBytes.length,
      );
      
      if (errorMessage != null) {
        UiHelpers.showErrorSnackBar(context, errorMessage);
        return;
      }

      await _processImage(context, fileBytes, file.name);
      
    } catch (e) {
      UiHelpers.showErrorSnackBar(context, '파일 선택 중 오류가 발생했습니다: $e');
    }
  }

}