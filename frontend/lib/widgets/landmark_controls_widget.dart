import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';
import '../services/api_service.dart';
import 'dart:html' as html;
import 'dart:math' as math;
import 'before_after_comparison.dart';

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
              
              const SizedBox(height: 8),
              
              // 컴팩트 모바일 프리셋
              if (appState.currentImage != null) ...[
                _buildCompactPresetItem(context, appState, '💉 아래턱', 'lower_jaw', '샷', 100, 500, 100),
                const SizedBox(height: 8),
                _buildCompactPresetItem(context, appState, '💉 중간턱', 'middle_jaw', '샷', 100, 500, 100),
                const SizedBox(height: 8),
                _buildCompactPresetItem(context, appState, '💉 볼', 'cheek', '샷', 100, 500, 100),
                const SizedBox(height: 8),
                _buildCompactPresetItem(context, appState, '💉 앞트임', 'front_protusion', '%', 1, 10, 1),
                const SizedBox(height: 8),
                _buildCompactPresetItem(context, appState, '💉 뒷트임', 'back_slit', '%', 1, 10, 1),
                const SizedBox(height: 16), // 컴팩트 레이아웃 완료
                /*
                  [
                    _PresetItemWithSlider(
                      title: '💉 아래턱',
                      description: '아래턱선을 날렵하게 정리',
                      presetType: 'lower_jaw',
                      unit: '샷',
                      minValue: 100,
                      maxValue: 500,
                      stepValue: 100,
                      onTap: () => _applyPresetWithSettings(context, 'lower_jaw'),
                    ),
                    _PresetItemWithSlider(
                      title: '💉 중간턱',
                      description: '중간턱 라인을 자연스럽게 개선',
                      presetType: 'middle_jaw',
                      unit: '샷',
                      minValue: 100,
                      maxValue: 500,
                      stepValue: 100,
                      onTap: () => _applyPresetWithSettings(context, 'middle_jaw'),
                    ),
                  ],
                ),
                
                const SizedBox(height: 20),
                
                _buildPresetSectionWithSlider(
                  context,
                  appState,
                  '🔹 볼륨 조절',
                  [
                    _PresetItemWithSlider(
                      title: '💉 볼',
                      description: '볼살을 자연스럽게 정리',
                      presetType: 'cheek',
                      unit: '샷',
                      minValue: 100,
                      maxValue: 500,
                      stepValue: 100,
                      onTap: () => _applyPresetWithSettings(context, 'cheek'),
                    ),
                  ],
                ),
                
                const SizedBox(height: 20),
                
                _buildPresetSectionWithSlider(
                  context,
                  appState,
                  '🔹 눈매 개선',
                  [
                    _PresetItemWithSlider(
                      title: '💉 앞트임',
                      description: '눈의 앞쪽을 자연스럽게 확장',
                      presetType: 'front_protusion',
                      unit: '번',
                      minValue: 10,
                      maxValue: 100,
                      stepValue: 10,
                      onTap: () => _applyPresetWithSettings(context, 'front_protusion'),
                    ),
                    _PresetItemWithSlider(
                      title: '💉 뒷트임',
                      description: '눈의 뒤쪽을 자연스럽게 확장',
                      presetType: 'back_slit',
                      unit: '번',
                      minValue: 10,
                      maxValue: 100,
                      stepValue: 10,
                      onTap: () => _applyPresetWithSettings(context, 'back_slit'),
                    ),
                  ],
                */ // 이전 코드 끝
                
                const SizedBox(height: 16),
                
                // 총 누적 통계
                _buildTotalCounters(context, appState),
                
                const SizedBox(height: 24),
                
                // 컨트롤 버튼들
                _buildControlButtons(context, appState),
                
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
              onPressed: appState.loadingPresetType != null ? null : item.onTap,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
                alignment: Alignment.centerLeft,
                elevation: 2,
                backgroundColor: Theme.of(context).colorScheme.surface,
                foregroundColor: Theme.of(context).colorScheme.onSurface,
              ),
              child: Row(
                children: [
                  Expanded(
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
                  // 해당 프리셋이 로딩 중일 때만 스피너 표시
                  if (appState.isPresetLoading(item.presetType))
                    Container(
                      margin: const EdgeInsets.only(left: 12),
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Theme.of(context).colorScheme.primary,
                        ),
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

  Widget _buildPresetSectionWithSlider(
    BuildContext context,
    AppState appState,
    String title,
    List<_PresetItemWithSlider> items,
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
        ...items.map((item) => _buildPresetItemWithSlider(context, appState, item)),
      ],
    );
  }

  Widget _buildPresetItemWithSlider(
    BuildContext context,
    AppState appState,
    _PresetItemWithSlider item,
  ) {
    final currentValue = appState.presetSettings[item.presetType] ?? item.minValue;
    final currentCounter = appState.presetCounters[item.presetType] ?? 0;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 헤더 (제목 + 현재 누적)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.title,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    item.description,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '총 $currentCounter${item.unit}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 12),
          
          // 슬라이더
          Row(
            children: [
              Text(
                '${item.minValue}${item.unit}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              Expanded(
                child: Slider(
                  value: currentValue.toDouble(),
                  min: item.minValue.toDouble(),
                  max: item.maxValue.toDouble(),
                  divisions: ((item.maxValue - item.minValue) / item.stepValue).round(),
                  label: '$currentValue${item.unit}',
                  onChanged: (value) {
                    appState.updatePresetSetting(item.presetType, value.round());
                  },
                ),
              ),
              Text(
                '${item.maxValue}${item.unit}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
          
          const SizedBox(height: 8),
          
          // 적용 버튼
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: appState.loadingPresetType != null ? null : item.onTap,
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Theme.of(context).colorScheme.onPrimary,
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (appState.isPresetLoading(item.presetType))
                    Container(
                      margin: const EdgeInsets.only(right: 8),
                      child: SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Theme.of(context).colorScheme.onPrimary,
                        ),
                      ),
                    ),
                  Text('$currentValue${item.unit} 적용'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCompactPresetItem(
    BuildContext context,
    AppState appState, 
    String title, 
    String presetType, 
    String unit, 
    int minValue, 
    int maxValue, 
    int stepValue
  ) {
    final currentValue = appState.presetSettings[presetType] ?? minValue;
    final currentCounter = appState.presetCounters[presetType] ?? 0;
    
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
        ),
      ),
      child: Row(
        children: [
          // 레이블 및 카운터
          Expanded(
            flex: 2,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  '총 $currentCounter$unit',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          
          // 슬라이더
          Expanded(
            flex: 3,
            child: Column(
              children: [
                Slider(
                  value: currentValue.toDouble(),
                  min: minValue.toDouble(),
                  max: maxValue.toDouble(),
                  divisions: ((maxValue - minValue) / stepValue).round(),
                  label: '$currentValue$unit',
                  onChanged: (value) {
                    appState.updatePresetSetting(presetType, value.round());
                  },
                ),
                Text(
                  '$currentValue$unit',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          
          // 적용 버튼
          SizedBox(
            width: 80,
            child: ElevatedButton(
              onPressed: appState.loadingPresetType != null 
                  ? null 
                  : () => _applyPresetWithSettings(context, presetType),
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Theme.of(context).colorScheme.onPrimary,
                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
              ),
              child: appState.isPresetLoading(presetType)
                  ? SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Theme.of(context).colorScheme.onPrimary,
                      ),
                    )
                  : const Text('적용', style: TextStyle(fontSize: 12)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTotalCounters(BuildContext context, AppState appState) {
    final totalShots = (appState.presetCounters['lower_jaw'] ?? 0) +
                     (appState.presetCounters['middle_jaw'] ?? 0) +
                     (appState.presetCounters['cheek'] ?? 0);
    
    final totalTreatments = (appState.presetCounters['front_protusion'] ?? 0) +
                           (appState.presetCounters['back_slit'] ?? 0);
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.secondaryContainer.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          Column(
            children: [
              Text(
                '총 누적 샷',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
              Text(
                '$totalShots샷',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
            ],
          ),
          Container(
            width: 1,
            height: 40,
            color: Theme.of(context).colorScheme.outline.withOpacity(0.3),
          ),
          Column(
            children: [
              Text(
                '총 트임 %',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
              Text(
                '$totalTreatments%',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildControlButtons(BuildContext context, AppState appState) {
    return Column(
      children: [
        // 첫 번째 줄: 뒤로가기, 원본복원
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: appState.canUndo ? () => appState.undo() : null,
                icon: const Icon(Icons.undo, size: 18),
                label: const Text('뒤로가기'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: appState.originalImage != null 
                    ? () => appState.restoreToOriginal() 
                    : null,
                icon: const Icon(Icons.restore, size: 18),
                label: const Text('원본복원'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
        
        const SizedBox(height: 12),
        
        // 두 번째 줄: Before/After, 저장하기
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: (appState.originalImage != null && appState.currentImage != null)
                    ? () => _showBeforeAfterComparison(context)
                    : null,
                icon: const Icon(Icons.compare, size: 18),
                label: const Text('Before/After'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: appState.currentImage != null 
                    ? () => _downloadImage(context) 
                    : null,
                icon: const Icon(Icons.download, size: 18),
                label: const Text('저장하기'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  foregroundColor: Theme.of(context).colorScheme.onPrimary,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _applyPresetWithSettings(BuildContext context, String presetType) async {
    final appState = context.read<AppState>();
    final shots = appState.presetSettings[presetType] ?? 100;
    
    // 설정된 샷 수만큼 반복 적용
    final baseShots = presetType.contains('protusion') || presetType.contains('slit') ? 1 : 100;
    final iterations = (shots / baseShots).round();
    
    // 레이저 효과 표시 (이터래이션 수 전달)
    appState.activateLaserEffect(presetType, iterations);
    
    for (int i = 0; i < iterations; i++) {
      await _applyPreset(context, presetType);
      if (i < iterations - 1) {
        // 마지막이 아니면 0.5초 대기
        await Future.delayed(const Duration(milliseconds: 500));
      }
    }
    
    // 카운터 업데이트
    appState.incrementPresetCounter(presetType, shots);
  }

  Future<void> _applyPreset(BuildContext context, String presetType) async {
    final appState = context.read<AppState>();
    final apiService = context.read<ApiService>();
    
    if (appState.currentImageId == null) return;
    
    try {
      // 특정 프리셋만 로딩 상태로 설정 (전체 화면 로딩 X)
      appState.setPresetLoading(presetType);
      
      // API를 통해 프리셋 적용
      final response = await apiService.applyPreset(
        appState.currentImageId!,
        presetType,
      );
      
      // 상태 업데이트 (부드러운 전환을 위해 프리셋 전용 메서드 사용)
      appState.updateImageFromPreset(
        response.imageBytes,
        response.imageId,
      );
      
      // 로딩 상태 해제
      appState.setPresetLoading(null);
      // 스냅샷 제거 - 깜빡임 방지
      
    } catch (e) {
      // 로딩 상태 해제
      appState.setPresetLoading(null);
      appState.setError('프리셋 적용 실패: $e');
      // 에러 스냅샷도 제거 - 깜빡임 방지
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

  void _showBeforeAfterComparison(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => Scaffold(
          appBar: AppBar(
            title: const Text('Before / After 비교'),
            centerTitle: true,
          ),
          body: const BeforeAfterComparison(),
        ),
      ),
    );
  }

  Future<void> _downloadImage(BuildContext context) async {
    final appState = context.read<AppState>();
    
    if (appState.currentImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('다운로드할 이미지가 없습니다'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }
    
    try {
      // 웹에서 다운로드 기능 구현
      final blob = html.Blob([appState.currentImage!]);
      final url = html.Url.createObjectUrlFromBlob(blob);
      final anchor = html.document.createElement('a') as html.AnchorElement
        ..href = url
        ..style.display = 'none'
        ..download = 'beautyGen_result_${DateTime.now().millisecondsSinceEpoch}.jpg';
      html.document.body?.children.add(anchor);
      
      anchor.click();
      
      html.document.body?.children.remove(anchor);
      html.Url.revokeObjectUrl(url);
      
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('이미지 다운로드 시작됨'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('다운로드 실패: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}

class _PresetItem {
  final String title;
  final String description;
  final String presetType;
  final VoidCallback onTap;

  _PresetItem({
    required this.title,
    required this.description,
    required this.presetType,
    required this.onTap,
  });
}

class _PresetItemWithSlider {
  final String title;
  final String description;
  final String presetType;
  final String unit;
  final int minValue;
  final int maxValue;
  final int stepValue;
  final VoidCallback onTap;

  _PresetItemWithSlider({
    required this.title,
    required this.description,
    required this.presetType,
    required this.unit,
    required this.minValue,
    required this.maxValue,
    required this.stepValue,
    required this.onTap,
  });
}