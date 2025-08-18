import 'package:flutter/material.dart';
<<<<<<< HEAD

/// 이미지 업로드 버튼들 - 갤러리 및 카메라
class UploadButtons extends StatelessWidget {
  final VoidCallback onGalleryPressed;
  final VoidCallback onCameraPressed;
  final bool isLoading;

=======
import '../../config/app_constants.dart';

/// 이미지 업로드 버튼들
class UploadButtons extends StatelessWidget {
  final VoidCallback onGalleryPressed;
  final VoidCallback onCameraPressed;
  
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
  const UploadButtons({
    super.key,
    required this.onGalleryPressed,
    required this.onCameraPressed,
<<<<<<< HEAD
    this.isLoading = false,
=======
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
<<<<<<< HEAD
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
=======
        // 갤러리 버튼
        Expanded(
          child: _UploadButton(
            onPressed: onGalleryPressed,
            icon: Icons.upload,
            label: '갤러리',
            isPrimary: true,
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
          ),
        ),
        
        const SizedBox(width: 16),
        
<<<<<<< HEAD
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
=======
        // 카메라 버튼
        Expanded(
          child: _UploadButton(
            onPressed: onCameraPressed,
            icon: Icons.camera_alt,
            label: '카메라',
            isPrimary: false,
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
          ),
        ),
      ],
    );
  }
<<<<<<< HEAD
=======
}

/// 개별 업로드 버튼
class _UploadButton extends StatelessWidget {
  final VoidCallback onPressed;
  final IconData icon;
  final String label;
  final bool isPrimary;
  
  const _UploadButton({
    required this.onPressed,
    required this.icon,
    required this.label,
    required this.isPrimary,
  });

  @override
  Widget build(BuildContext context) {
    const buttonHeight = 56.0;
    const textStyle = TextStyle(
      fontSize: 16,
      fontWeight: FontWeight.w600,
    );
    
    return SizedBox(
      height: buttonHeight,
      child: isPrimary
          ? FilledButton.icon(
              onPressed: onPressed,
              icon: Icon(icon),
              label: Text(label),
              style: FilledButton.styleFrom(textStyle: textStyle),
            )
          : OutlinedButton.icon(
              onPressed: onPressed,
              icon: Icon(icon),
              label: Text(label),
              style: OutlinedButton.styleFrom(textStyle: textStyle),
            ),
    );
  }
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
}