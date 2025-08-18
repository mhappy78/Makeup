import 'package:flutter/material.dart';
import '../../config/app_constants.dart';

/// 사진 촬영 팁 위젯
class PhotographyTips extends StatelessWidget {
  const PhotographyTips({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(context),
          const SizedBox(height: 16),
          _buildMainTip(context),
          const SizedBox(height: 12),
          ..._buildTipsList(context),
          const SizedBox(height: 16),
          _buildSupportedFormats(context),
        ],
      ),
    );
  }
  
  /// 헤더 타이틀
  Widget _buildHeader(BuildContext context) {
    return Row(
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
    );
  }
  
  /// 메인 팁 (정면 사진 강조)
  Widget _buildMainTip(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppConstants.smallBorderRadius),
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
    );
  }
  
  /// 추가 팁 목록
  List<Widget> _buildTipsList(BuildContext context) {
    final tips = [
      _TipData(Icons.person, '혼자 촬영', '한 명만 나오도록 촬영해주세요'),
      _TipData(Icons.wb_sunny_outlined, '밝은 조명', '자연광이나 밝은 실내에서'),
      _TipData(Icons.crop_portrait, '얼굴 전체', '이마부터 턱까지 모두 보이도록'),
      _TipData(Icons.visibility, '선명한 화질', '흔들리지 않게 또렷하게'),
    ];
    
    return tips.map((tip) => Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: _buildTipRow(context, tip),
    )).toList();
  }
  
  /// 개별 팁 행
  Widget _buildTipRow(BuildContext context, _TipData tip) {
    return Row(
      children: [
        Icon(
          tip.icon,
          size: 18,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                tip.title,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: Theme.of(context).colorScheme.onSurface,
                ),
              ),
              Text(
                tip.description,
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
  
  /// 지원 형식 표시
  Widget _buildSupportedFormats(BuildContext context) {
    return Center(
      child: Text(
        '지원 형식: ${AppConstants.supportedImageFormats.map((f) => f.toUpperCase()).join(', ')}',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant.withOpacity(0.7),
          fontSize: 11,
        ),
      ),
    );
  }
}

/// 팁 데이터 클래스
class _TipData {
  final IconData icon;
  final String title;
  final String description;
  
  const _TipData(this.icon, this.title, this.description);
}