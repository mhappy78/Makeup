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
        return LayoutBuilder(
          builder: (context, constraints) {
            final isMobile = constraints.maxWidth < 768;
            
            return SingleChildScrollView(
              padding: EdgeInsets.all(isMobile ? 8.0 : 16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 헤더 (모바일에서는 숨김)
                  if (!isMobile) ...[
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
                  ],
                  
                  // 컴팩트 모바일 프리셋
                  if (appState.currentImage != null) ...[
                    _buildCompactPresetItem(context, appState, '🌟 아래턱', 'lower_jaw', '샷', 100, 500, 100, isMobile),
                    SizedBox(height: isMobile ? 4 : 8),
                    _buildCompactPresetItem(context, appState, '🌟 중간턱', 'middle_jaw', '샷', 100, 500, 100, isMobile),
                    SizedBox(height: isMobile ? 4 : 8),
                    _buildCompactPresetItem(context, appState, '🌟 볼', 'cheek', '샷', 100, 500, 100, isMobile),
                    SizedBox(height: isMobile ? 4 : 8),
                    _buildCompactPresetItem(context, appState, '✂️ 앞트임', 'front_protusion', '%', 1, 5, 1, isMobile),
                    SizedBox(height: isMobile ? 4 : 8),
                    _buildCompactPresetItem(context, appState, '✂️ 뒷트임', 'back_slit', '%', 1, 5, 1, isMobile),
                    SizedBox(height: isMobile ? 8 : 16),
                    
                    // 컨트롤 버튼들
                    _buildControlButtons(context, appState, isMobile),
                    
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
                            '• 프리셋은 시뮬레이션 목적입니다\\n'
                            '• 실제 시술과는 차이가 있을 수 있습니다\\n'
                            '• 여러 프리셋을 조합하여 사용 가능합니다\\n'
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
                            '이미지를 업로드하면\\n프리셋을 사용할 수 있습니다',
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
      },
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
    int stepValue,
    bool isMobile
  ) {
    final currentValue = math.max(minValue, math.min(maxValue, appState.presetSettings[presetType] ?? minValue));
    final currentCounter = appState.presetCounters[presetType] ?? 0;
    
    return Container(
      padding: EdgeInsets.all(isMobile ? 6 : 12),
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
            flex: isMobile ? 1 : 2,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    fontSize: isMobile ? 12 : null,
                  ),
                ),
                if (!isMobile)
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
            flex: isMobile ? 2 : 3,
            child: isMobile 
                ? Slider(
                    value: currentValue.toDouble(),
                    min: minValue.toDouble(),
                    max: maxValue.toDouble(),
                    divisions: math.max(1, ((maxValue - minValue) / stepValue).round()),
                    label: '$currentValue$unit',
                    onChanged: (value) {
                      appState.updatePresetSetting(presetType, value.round());
                    },
                  )
                : Column(
                    children: [
                      Slider(
                        value: currentValue.toDouble(),
                        min: minValue.toDouble(),
                        max: maxValue.toDouble(),
                        divisions: math.max(1, ((maxValue - minValue) / stepValue).round()),
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
          
          if (isMobile)
            Text(
              '$currentValue$unit',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
          
          const SizedBox(width: 8),
          
          // 적용 버튼
          SizedBox(
            width: isMobile ? 60 : 80,
            child: ElevatedButton(
              onPressed: appState.loadingPresetType != null 
                  ? null 
                  : () => _applyPresetWithSettings(context, presetType),
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Theme.of(context).colorScheme.onPrimary,
                padding: EdgeInsets.symmetric(vertical: isMobile ? 6 : 8, horizontal: 4),
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
                  : Text('적용', style: TextStyle(fontSize: isMobile ? 10 : 12)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildControlButtons(BuildContext context, AppState appState, bool isMobile) {
    if (isMobile) {
      // 모바일: 2줄 배치로 변경
      return Column(
        children: [
          // 첫 번째 줄: 뒤로, 원본
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: appState.canUndo ? () => appState.undo() : null,
                  icon: const Icon(Icons.undo, size: 16),
                  label: const Text('뒤로', style: TextStyle(fontSize: 11)),
                  style: FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
                    foregroundColor: Theme.of(context).colorScheme.onSecondaryContainer,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: FilledButton.icon(
                  onPressed: appState.originalImage != null 
                      ? () => appState.restoreToOriginal() 
                      : null,
                  icon: const Icon(Icons.restore, size: 16),
                  label: const Text('원본', style: TextStyle(fontSize: 11)),
                  style: FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
                    foregroundColor: Theme.of(context).colorScheme.onSecondaryContainer,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // 두 번째 줄: Before/After, 저장
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: (appState.originalImage != null && appState.currentImage != null)
                      ? () => _showBeforeAfterComparison(context)
                      : null,
                  icon: const Icon(Icons.compare, size: 16),
                  label: const Text('Before/After', style: TextStyle(fontSize: 11)),
                  style: FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Theme.of(context).colorScheme.onPrimary,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: FilledButton.icon(
                  onPressed: appState.currentImage != null 
                      ? () => _downloadImage(context) 
                      : null,
                  icon: const Icon(Icons.download, size: 16),
                  label: const Text('저장', style: TextStyle(fontSize: 11)),
                  style: FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.secondary,
                    foregroundColor: Theme.of(context).colorScheme.onSecondary,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
            ],
          ),
        ],
      );
    } else {
      // 데스크톱: 기존 레이아웃
      return Column(
        children: [
          // 첫 번째 줄: 뒤로가기, 원본복원
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: appState.canUndo ? () => appState.undo() : null,
                  icon: const Icon(Icons.undo, size: 18),
                  label: const Text('뒤로'),
                  style: FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
                    foregroundColor: Theme.of(context).colorScheme.onSecondaryContainer,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton.icon(
                  onPressed: appState.originalImage != null 
                      ? () => appState.restoreToOriginal() 
                      : null,
                  icon: const Icon(Icons.restore, size: 18),
                  label: const Text('원본'),
                  style: FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
                    foregroundColor: Theme.of(context).colorScheme.onSecondaryContainer,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 12),
          
          // 두 번째 줄: Before/After와 저장 (프리스타일 탭 스타일)
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: (appState.originalImage != null && appState.currentImage != null)
                      ? () => _showBeforeAfterComparison(context)
                      : null,
                  icon: const Icon(Icons.compare, size: 18),
                  label: const Text('Before/After'),
                  style: FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Theme.of(context).colorScheme.onPrimary,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton.icon(
                  onPressed: appState.currentImage != null 
                      ? () => _downloadImage(context) 
                      : null,
                  icon: const Icon(Icons.download, size: 18),
                  label: const Text('저장'),
                  style: FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.secondary,
                    foregroundColor: Theme.of(context).colorScheme.onSecondary,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
            ],
          ),
        ],
      );
    }
  }

  Future<void> _applyPresetWithSettings(BuildContext context, String presetType) async {
    final appState = context.read<AppState>();
    final shots = appState.presetSettings[presetType] ?? 100;
    
    // 프리셋 시각화 표시
    appState.showPresetVisualizationFor(presetType);
    
    // 설정된 샷 수만큼 반복 적용
    final baseShots = presetType.contains('protusion') || presetType.contains('slit') ? 1 : 100;
    final iterations = (shots / baseShots).round();
    
    // 레이저 효과 표시 (이터래이션 수 전달)
    appState.activateLaserEffect(presetType, iterations);
    
    for (int i = 0; i < iterations; i++) {
      // 현재 진행 상황 계산
      final currentShots = (i + 1) * baseShots;
      await _applyPresetWithProgress(context, presetType, currentShots);
      if (i < iterations - 1) {
        // 마지막이 아니면 0.5초 대기
        await Future.delayed(const Duration(milliseconds: 500));
      }
    }
    
    // 카운터 업데이트
    appState.incrementPresetCounter(presetType, shots);
  }

  Future<void> _applyPresetWithProgress(BuildContext context, String presetType, int progress) async {
    final appState = context.read<AppState>();
    final apiService = context.read<ApiService>();
    
    if (appState.currentImageId == null) return;
    
    try {
      // 특정 프리셋만 로딩 상태로 설정 + 진행 상황 표시
      appState.setPresetLoading(presetType, progress);
      
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
      
      // 로딩 상태 즉시 해제 (지연 제거)
      appState.setPresetLoading(null);
      
    } catch (e) {
      // 에러 시에도 즉시 로딩 상태 해제
      appState.setPresetLoading(null);
      appState.setError('프리셋 적용 실패: $e');
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