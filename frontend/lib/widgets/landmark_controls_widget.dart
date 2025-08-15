import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';
import '../services/api_service.dart';

/// 프리셋 컨트롤 위젯
class LandmarkControlsWidget extends StatelessWidget {
  const LandmarkControlsWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 헤더
              Row(
                children: [
                  Icon(
                    Icons.auto_fix_high,
                    size: 24,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '⚡ 빠른 프리셋',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 16),
              
              // 설명
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '원터치로 적용할 수 있는 전문적인 성형 효과입니다. '
                  '각 프리셋은 실제 시술 결과를 시뮬레이션합니다.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
              ),
              
              const SizedBox(height: 24),
              
              // 프리셋 버튼들
              if (appState.currentImage != null) ...[
                _buildPresetSection(
                  context,
                  appState,
                  '🔹 턱선 조각',
                  [
                    _PresetItem(
                      title: '💉 아래턱 100샷+',
                      description: '아래턱선을 날렵하게 정리',
                      onTap: () => _applyPreset(context, 'lower_jaw'),
                    ),
                    _PresetItem(
                      title: '💉 중간턱 100샷+',
                      description: '중간턱 라인을 자연스럽게 개선',
                      onTap: () => _applyPreset(context, 'middle_jaw'),
                    ),
                  ],
                ),
                
                const SizedBox(height: 20),
                
                _buildPresetSection(
                  context,
                  appState,
                  '🔹 볼륨 조절',
                  [
                    _PresetItem(
                      title: '💉 볼 100샷+',
                      description: '볼살을 자연스럽게 정리',
                      onTap: () => _applyPreset(context, 'cheek'),
                    ),
                  ],
                ),
                
                const SizedBox(height: 20),
                
                _buildPresetSection(
                  context,
                  appState,
                  '🔹 눈매 개선',
                  [
                    _PresetItem(
                      title: '💉 앞트임+',
                      description: '눈의 앞쪽을 자연스럽게 확장',
                      onTap: () => _applyPreset(context, 'front_protusion'),
                    ),
                    _PresetItem(
                      title: '💉 뒷트임+',
                      description: '눈의 뒤쪽을 자연스럽게 확장',
                      onTap: () => _applyPreset(context, 'back_slit'),
                    ),
                  ],
                ),
                
                const SizedBox(height: 32),
                
                // 주의사항
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.errorContainer.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: Theme.of(context).colorScheme.error.withOpacity(0.3),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.info_outline,
                            size: 16,
                            color: Theme.of(context).colorScheme.error,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '주의사항',
                            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: Theme.of(context).colorScheme.error,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '• 프리셋은 시뮬레이션 목적입니다\n'
                        '• 실제 시술과는 차이가 있을 수 있습니다\n'
                        '• 여러 프리셋을 조합하여 사용 가능합니다\n'
                        '• 뒤로가기로 언제든 되돌릴 수 있습니다',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onErrorContainer,
                        ),
                      ),
                    ],
                  ),
                ),
              ] else ...[
                // 이미지 없을 때 안내
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.photo_camera_outlined,
                        size: 48,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        '이미지를 업로드하면\n프리셋을 사용할 수 있습니다',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildPresetSection(
    BuildContext context,
    AppState appState,
    String title,
    List<_PresetItem> items,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        ...items.map((item) => Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: appState.isLoading ? null : item.onTap,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
                alignment: Alignment.centerLeft,
                elevation: 2,
                backgroundColor: Theme.of(context).colorScheme.surface,
                foregroundColor: Theme.of(context).colorScheme.onSurface,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.title,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    item.description,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ),
        )),
      ],
    );
  }

  Future<void> _applyPreset(BuildContext context, String presetType) async {
    final appState = context.read<AppState>();
    final apiService = context.read<ApiService>();
    
    if (appState.currentImageId == null) return;
    
    try {
      appState.setLoading(true);
      
      // API를 통해 프리셋 적용
      final response = await apiService.applyPreset(
        appState.currentImageId!,
        presetType,
      );
      
      // 상태 업데이트
      appState.setImage(
        response.imageBytes,
        response.imageId,
        appState.imageWidth,
        appState.imageHeight,
      );
      
      appState.setLoading(false);
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${_getPresetName(presetType)} 적용 완료!'),
            backgroundColor: Colors.green,
          ),
        );
      }
      
    } catch (e) {
      appState.setError('프리셋 적용 실패: $e');
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('프리셋 적용 실패: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  String _getPresetName(String presetType) {
    switch (presetType) {
      case 'lower_jaw':
        return '아래턱 100샷+';
      case 'middle_jaw':
        return '중간턱 100샷+';
      case 'cheek':
        return '볼 100샷+';
      case 'front_protusion':
        return '앞트임+';
      case 'back_slit':
        return '뒷트임+';
      default:
        return '프리셋';
    }
  }
}

class _PresetItem {
  final String title;
  final String description;
  final VoidCallback onTap;

  _PresetItem({
    required this.title,
    required this.description,
    required this.onTap,
  });
}