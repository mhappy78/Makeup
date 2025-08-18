import 'package:flutter/material.dart';
<<<<<<< HEAD

/// 로고 위젯 - 앱 전반에서 재사용 가능
class LogoWidget extends StatelessWidget {
  final double width;
  final double height;
  final bool showShadow;

=======
import '../../config/app_constants.dart';

/// BeautyGen 로고 위젯
class LogoWidget extends StatelessWidget {
  final double? width;
  final double? height;
  final bool withShadow;
  
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
  const LogoWidget({
    super.key,
    this.width = 480,
    this.height = 240,
<<<<<<< HEAD
    this.showShadow = true,
=======
    this.withShadow = true,
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
  });

  @override
  Widget build(BuildContext context) {
<<<<<<< HEAD
    final logoWidget = Image.network(
=======
    Widget logoImage = Image.network(
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
      'images/logo_e.png',
      width: width,
      height: height,
      fit: BoxFit.contain,
<<<<<<< HEAD
      errorBuilder: (context, error, stackTrace) {
        // 이미지 로드 실패 시 기본 아이콘 표시
        return Container(
          width: width,
          height: height,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Icon(
            Icons.face,
            size: width * 0.25, // 비례 크기
            color: Theme.of(context).colorScheme.primary,
          ),
        );
      },
    );

    if (!showShadow) {
      return logoWidget;
    }

    return Container(
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
      child: logoWidget,
    );
  }
=======
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
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
}