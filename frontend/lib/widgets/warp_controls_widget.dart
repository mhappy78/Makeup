import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';
import '../services/api_service.dart';
import 'before_after_comparison.dart';

/// 워핑 컨트롤 위젯
class WarpControlsWidget extends StatelessWidget {
  const WarpControlsWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 영향 반경 (한 줄에 텍스트와 슬라이더)
              Row(
                children: [
                  SizedBox(
                    width: 100,
                    child: Text(
                      '영향 반경: ${appState.influenceRadiusPercent.toStringAsFixed(1)}%',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Slider(
                      value: appState.influenceRadiusPercent,
                      min: 0.5,
                      max: 50.0,
                      divisions: 99,
                      label: '${appState.influenceRadiusPercent.toStringAsFixed(1)}%',
                      onChanged: appState.currentImage != null
                          ? (value) => appState.setInfluenceRadiusPercent(value)
                          : null,
                    ),
                  ),
                ],
              ),
              
              // 변형 강도 (한 줄에 텍스트와 슬라이더)
              Row(
                children: [
                  SizedBox(
                    width: 100,
                    child: Text(
                      '변형 강도: ${(appState.warpStrength * 100).toInt()}%',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Slider(
                      value: appState.warpStrength,
                      min: 0.05, // 5%
                      max: 1.0, // 100%
                      divisions: 19, // 5%씩 이동 (5%, 10%, 15%, ..., 100%)
                      label: '${(appState.warpStrength * 100).toInt()}%',
                      onChanged: appState.currentImage != null
                          ? (value) => appState.setWarpStrength(value)
                          : null,
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 20),
              
              // 히스토리 관리 버튼들
              Row(
                children: [
                  Expanded(
                    child: FilledButton.tonal(
                      onPressed: appState.canUndo 
                          ? () => appState.undo()
                          : null,
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.undo, size: 18),
                          SizedBox(width: 4),
                          Text('뒤로가기'),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: FilledButton.tonal(
                      onPressed: appState.originalImage != null 
                          ? () => appState.restoreToOriginal()
                          : null,
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.restore, size: 18),
                          SizedBox(width: 4),
                          Text('원본복원'),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 20),
              
              // 워핑 모드 선택
              Text(
                '변형 모드',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              
              const SizedBox(height: 8),
              
              // 모드 버튼들
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: WarpMode.values.map((mode) {
                  final isSelected = appState.warpMode == mode;
                  return FilterChip(
                    label: Text(mode.displayName),
                    selected: isSelected,
                    onSelected: appState.currentImage != null 
                        ? (selected) {
                            if (selected) {
                              appState.setWarpMode(mode);
                            }
                          }
                        : null,
                    tooltip: mode.description,
                  );
                }).toList(),
              ),
              
              const SizedBox(height: 16),
              
              // 현재 모드 설명
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      _getModeIcon(appState.warpMode),
                      size: 20,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        appState.warpMode.description,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 20),
              
              // 사용법 안내
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.info_outline,
                          size: 16,
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          '사용법',
                          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '1. 원하는 변형 모드를 선택하세요\n'
                      '2. 영향 반경(%)과 강도를 조절하세요\n'
                      '3. 좌측 하단 버튼으로 줌인하세요\n'
                      '4. 길게 누르고 드래그: 이미지 이동 (팬)\n'
                      '5. 짧게 클릭/터치 드래그: 워핑 적용\n'
                      '6. 뒤로가기/원본복원으로 실수를 되돌리세요',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 20),
              
              // Before/After 비교 버튼
              if (appState.originalImage != null && appState.currentImage != null) ...[
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => _showBeforeAfterComparison(context),
                    icon: const Icon(Icons.compare),
                    label: const Text('Before / After 비교'),
                  ),
                ),
                const SizedBox(height: 12),
              ],
              
              // 다운로드 버튼
              if (appState.currentImage != null) ...[
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => _downloadImage(context),
                    icon: const Icon(Icons.download),
                    label: const Text('결과 저장'),
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  void _showBeforeAfterComparison(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => Scaffold(
          appBar: AppBar(
            title: const Text('Before / After 비교'),
            leading: IconButton(
              icon: const Icon(Icons.close),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          body: const BeforeAfterComparison(),
        ),
      ),
    );
  }

  IconData _getModeIcon(WarpMode mode) {
    switch (mode) {
      case WarpMode.pull:
        return Icons.open_with;
      case WarpMode.push:
        return Icons.push_pin;
      case WarpMode.expand:
        return Icons.zoom_out_map;
      case WarpMode.shrink:
        return Icons.center_focus_weak;
    }
  }

  Future<void> _downloadImage(BuildContext context) async {
    final appState = context.read<AppState>();
    final apiService = context.read<ApiService>();
    
    if (appState.currentImageId == null) return;
    
    try {
      appState.setLoading(true);
      
      final imageBytes = await apiService.downloadImage(appState.currentImageId!);
      
      // 웹에서는 브라우저 다운로드 트리거
      // 실제 구현에서는 html 패키지를 사용해야 함
      
      appState.setLoading(false);
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('이미지 다운로드 준비 완료!'),
            backgroundColor: Colors.green,
          ),
        );
      }
      
    } catch (e) {
      appState.setError('다운로드 실패: $e');
    }
  }
}