import 'package:flutter/material.dart';
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
  });

  @override
  Widget build(BuildContext context) {
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
      ),
    );
  }
}