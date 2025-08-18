import 'package:flutter/material.dart';
import '../../config/app_constants.dart';

/// BeautyGen 로고 위젯
class LogoWidget extends StatelessWidget {
  final double? width;
  final double? height;
  final bool withShadow;
  
  const LogoWidget({
    super.key,
    this.width = 480,
    this.height = 240,
    this.withShadow = true,
  });

  @override
  Widget build(BuildContext context) {
    Widget logoImage = Image.network(
      'images/logo_e.png',
      width: width,
      height: height,
      fit: BoxFit.contain,
      errorBuilder: (context, error, stackTrace) => _buildFallbackLogo(context),
    );
    
    if (!withShadow) return logoImage;
    
    return Container(
      decoration: BoxDecoration(
        boxShadow: _buildShadows(),
      ),
      child: logoImage,
    );
  }
  
  /// 로고 로드 실패 시 대체 위젯
  Widget _buildFallbackLogo(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(AppConstants.largeBorderRadius),
      ),
      child: Icon(
        Icons.face,
        size: 120,
        color: Theme.of(context).colorScheme.primary,
      ),
    );
  }
  
  /// 그림자 효과 정의
  List<BoxShadow> _buildShadows() {
    return [
      BoxShadow(
        color: Colors.black.withOpacity(0.15),
        blurRadius: 20,
        offset: const Offset(8, 8),
        spreadRadius: 0,
      ),
      BoxShadow(
        color: Colors.black.withOpacity(0.08),
        blurRadius: 40,
        offset: const Offset(12, 12),
        spreadRadius: -4,
      ),
    ];
  }
}