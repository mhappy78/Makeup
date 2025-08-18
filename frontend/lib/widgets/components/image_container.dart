import 'package:flutter/material.dart';
<<<<<<< HEAD
import 'dart:typed_data';

/// 이미지 표시용 컨테이너 - 다양한 상황에서 재사용 가능
class ImageContainer extends StatelessWidget {
  final Uint8List? imageData;
  final double? width;
  final double? height;
  final BoxFit fit;
  final BorderRadius? borderRadius;
  final Widget? placeholder;
  final Widget? errorWidget;
  final List<BoxShadow>? boxShadow;

  const ImageContainer({
    super.key,
    this.imageData,
    this.width,
    this.height,
    this.fit = BoxFit.contain,
    this.borderRadius,
    this.placeholder,
    this.errorWidget,
    this.boxShadow,
=======
import '../../config/app_constants.dart';
import '../image_display_widget.dart';

/// 이미지 표시 컨테이너
class ImageContainer extends StatelessWidget {
  final EdgeInsets? margin;
  final double? height;
  
  const ImageContainer({
    super.key,
    this.margin,
    this.height,
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
  });

  @override
  Widget build(BuildContext context) {
<<<<<<< HEAD
    Widget child;

    if (imageData != null) {
      child = Image.memory(
        imageData!,
        width: width,
        height: height,
        fit: fit,
        errorBuilder: (context, error, stackTrace) {
          return errorWidget ?? _buildErrorWidget(context);
        },
      );
    } else {
      child = placeholder ?? _buildPlaceholderWidget(context);
    }

    if (borderRadius != null) {
      child = ClipRRect(
        borderRadius: borderRadius!,
        child: child,
      );
    }

    if (boxShadow != null) {
      child = Container(
        decoration: BoxDecoration(
          borderRadius: borderRadius,
          boxShadow: boxShadow,
        ),
        child: child,
      );
    }

    return child;
  }

  Widget _buildPlaceholderWidget(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant,
        borderRadius: borderRadius,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.image_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: 8),
          Text(
            '이미지가 없습니다',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorWidget(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.errorContainer,
        borderRadius: borderRadius,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline,
            size: 48,
            color: Theme.of(context).colorScheme.onErrorContainer,
          ),
          const SizedBox(height: 8),
          Text(
            '이미지 로드 실패',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onErrorContainer,
            ),
          ),
        ],
=======
    return Container(
      height: height,
      margin: margin ?? AppConstants.smallPadding,
      decoration: BoxDecoration(
        border: Border.all(
          color: Theme.of(context).colorScheme.outline,
        ),
        borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
        child: const ImageDisplayWidget(),
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
      ),
    );
  }
}