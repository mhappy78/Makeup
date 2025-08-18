import 'package:flutter/material.dart';

/// 로고 위젯 - 앱 전반에서 재사용 가능
class LogoWidget extends StatelessWidget {
  final double width;
  final double height;
  final bool showShadow;

  const LogoWidget({
    super.key,
    this.width = 480,
    this.height = 240,
    this.showShadow = true,
  });

  @override
  Widget build(BuildContext context) {
    final logoWidget = Image.network(
      'images/logo_e.png',
      width: width,
      height: height,
      fit: BoxFit.contain,
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
}