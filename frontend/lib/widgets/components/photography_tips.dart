import 'package:flutter/material.dart';

/// 사진 촬영 가이드 컴포넌트
class PhotographyTips extends StatelessWidget {
  const PhotographyTips({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.lightbulb_outline,
                size: 20,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(width: 8),
              Text(
                '좋은 분석 결과를 위한 촬영 팁',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: Theme.of(context).colorScheme.primary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          // 메인 포인트 - 정면 사진 강조
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.face,
                  size: 24,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '정면 얼굴 사진 필수!',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '카메라를 똑바로 보고 촬영해주세요',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 12),
          
          // 추가 팁들
          _buildTipRow(context, Icons.person, '혼자 촬영', '한 명만 나오도록 촬영해주세요'),
          const SizedBox(height: 8),
          _buildTipRow(context, Icons.wb_sunny_outlined, '밝은 조명', '자연광이나 밝은 실내에서'),
          const SizedBox(height: 8),
          _buildTipRow(context, Icons.crop_portrait, '얼굴 전체', '이마부터 턱까지 모두 보이도록'),
          const SizedBox(height: 8),
          _buildTipRow(context, Icons.visibility, '선명한 화질', '흔들리지 않게 또렷하게'),
          
          const SizedBox(height: 16),
          
          // 지원 형식 (작게 표시)
          Center(
            child: Text(
              '지원 형식: JPEG, PNG, WebP',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant.withOpacity(0.7),
                fontSize: 11,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 촬영 팁 행을 빌드하는 헬퍼 함수
  Widget _buildTipRow(BuildContext context, IconData icon, String title, String description) {
    return Row(
      children: [
        Icon(
          icon,
          size: 18,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: Theme.of(context).colorScheme.onSurface,
                ),
              ),
              Text(
                description,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}