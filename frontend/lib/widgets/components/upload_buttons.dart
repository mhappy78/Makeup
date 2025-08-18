import 'package:flutter/material.dart';
import '../../config/app_constants.dart';

/// 이미지 업로드 버튼들
class UploadButtons extends StatelessWidget {
  final VoidCallback onGalleryPressed;
  final VoidCallback onCameraPressed;
  
  const UploadButtons({
    super.key,
    required this.onGalleryPressed,
    required this.onCameraPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // 갤러리 버튼
        Expanded(
          child: _UploadButton(
            onPressed: onGalleryPressed,
            icon: Icons.upload,
            label: '갤러리',
            isPrimary: true,
          ),
        ),
        
        const SizedBox(width: 16),
        
        // 카메라 버튼
        Expanded(
          child: _UploadButton(
            onPressed: onCameraPressed,
            icon: Icons.camera_alt,
            label: '카메라',
            isPrimary: false,
          ),
        ),
      ],
    );
  }
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
}