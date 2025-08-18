import 'package:flutter/material.dart';

/// 이미지 업로드 버튼들 - 갤러리 및 카메라
class UploadButtons extends StatelessWidget {
  final VoidCallback onGalleryPressed;
  final VoidCallback onCameraPressed;
  final bool isLoading;

  const UploadButtons({
    super.key,
    required this.onGalleryPressed,
    required this.onCameraPressed,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // 이미지 선택 버튼
        Expanded(
          child: SizedBox(
            height: 56,
            child: FilledButton.icon(
              onPressed: isLoading ? null : onGalleryPressed,
              icon: isLoading 
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.upload),
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
              onPressed: isLoading ? null : onCameraPressed,
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
    );
  }
}