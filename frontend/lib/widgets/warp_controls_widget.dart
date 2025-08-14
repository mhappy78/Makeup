import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';
import '../services/api_service.dart';

/// 워핑 컨트롤 위젯
class WarpControlsWidget extends StatelessWidget {
  const WarpControlsWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 제목
                Text(
                  '자유 변형 도구',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                
                const SizedBox(height: 16),
                
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
                
                // 영향 반경 슬라이더
                Text(
                  '영향 반경: ${appState.influenceRadius.toInt()}px',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                
                Slider(
                  value: appState.influenceRadius,
                  min: 20,
                  max: 200,
                  divisions: 18,
                  label: '${appState.influenceRadius.toInt()}px',
                  onChanged: appState.currentImage != null
                      ? (value) => appState.setInfluenceRadius(value)
                      : null,
                ),
                
                Text(
                  '변형이 적용될 범위를 설정합니다',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // 변형 강도 슬라이더
                Text(
                  '변형 강도: ${(appState.warpStrength * 100).toInt()}%',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                
                Slider(
                  value: appState.warpStrength,
                  min: 0.1,
                  max: 2.0,
                  divisions: 19,
                  label: '${(appState.warpStrength * 100).toInt()}%',
                  onChanged: appState.currentImage != null
                      ? (value) => appState.setWarpStrength(value)
                      : null,
                ),
                
                Text(
                  '변형의 강도를 조절합니다',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
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
                      const SizedBox(height: 6),
                      Text(
                        '1. 원하는 변형 모드를 선택하세요\n'
                        '2. 영향 반경과 강도를 조절하세요\n'
                        '3. 이미지에서 드래그하여 변형을 적용하세요',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                
                const Spacer(),
                
                // 다운로드 버튼
                if (appState.currentImage != null) ...[
                  const SizedBox(height: 16),
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
          ),
        );
      },
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