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
        return LayoutBuilder(
          builder: (context, constraints) {
            // 브라우저 화면 크기 기준 반응형 (프리셋 탭과 동일한 로직)
            final screenWidth = MediaQuery.of(context).size.width;
            final isMobile = screenWidth <= 768;
            
            return SingleChildScrollView(
              padding: EdgeInsets.all(isMobile ? 8.0 : 16.0),
              child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 영향 반경과 변형 강도
              if (isMobile) ...[
                // 모바일: 한 줄에 텍스트와 슬라이더
                Row(
                  children: [
                    SizedBox(
                      width: 70,
                      child: Text(
                        '반경:${appState.influenceRadiusPercent.toStringAsFixed(1)}%',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
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
                
                Row(
                  children: [
                    SizedBox(
                      width: 70,
                      child: Text(
                        '강도:${(appState.warpStrength * 100).toInt()}%',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
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
              ] else ...[
                // 데스크톱: 텍스트 위, 슬라이더 아래
                Text(
                  '영향 반경: ${appState.influenceRadiusPercent.toStringAsFixed(1)}%',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                Slider(
                  value: appState.influenceRadiusPercent,
                  min: 0.5,
                  max: 50.0,
                  divisions: 99,
                  label: '${appState.influenceRadiusPercent.toStringAsFixed(1)}%',
                  onChanged: appState.currentImage != null
                      ? (value) => appState.setInfluenceRadiusPercent(value)
                      : null,
                ),
                
                const SizedBox(height: 20),
                
                Text(
                  '변형 강도: ${(appState.warpStrength * 100).toInt()}%',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                Slider(
                  value: appState.warpStrength,
                  min: 0.05, // 5%
                  max: 1.0, // 100%
                  divisions: 19, // 5%씩 이동 (5%, 10%, 15%, ..., 100%)
                  label: '${(appState.warpStrength * 100).toInt()}%',
                  onChanged: appState.currentImage != null
                      ? (value) => appState.setWarpStrength(value)
                      : null,
                ),
              ],
              
              SizedBox(height: isMobile ? 8 : 30),
              
              // 히스토리 관리 버튼들
              Row(
                children: [
                  Expanded(
                    child: FilledButton.tonal(
                      onPressed: appState.canUndo 
                          ? () => appState.undo()
                          : null,
                      style: FilledButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: isMobile ? 8 : 12),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.undo, size: isMobile ? 16 : 18),
                          SizedBox(width: isMobile ? 2 : 4),
                          Text(
                            isMobile ? '뒤로' : '뒤로가기',
                            style: TextStyle(fontSize: isMobile ? 12 : null),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(width: isMobile ? 4 : 8),
                  Expanded(
                    child: FilledButton.tonal(
                      onPressed: appState.originalImage != null 
                          ? () => appState.restoreToOriginal()
                          : null,
                      style: FilledButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: isMobile ? 8 : 12),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.restore, size: isMobile ? 16 : 18),
                          SizedBox(width: isMobile ? 2 : 4),
                          Text(
                            isMobile ? '원본' : '원본복원',
                            style: TextStyle(fontSize: isMobile ? 12 : null),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              
              SizedBox(height: isMobile ? 8 : 30),
              
              // 변형 모드와 버튼들을 한 줄에 (모바일에서)
              if (isMobile) ...[
                Row(
                  children: [
                    SizedBox(
                      width: 45,
                      child: Text(
                        '변형\n모드',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                          height: 1.1,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Row(
                        children: [WarpMode.pull, WarpMode.push, WarpMode.expand, WarpMode.shrink].asMap().entries.map((entry) {
                          final index = entry.key;
                          final mode = entry.value;
                          final isSelected = appState.warpMode == mode;
                          final isLast = index == 3; // 4개 버튼 중 마지막
                          
                          return Expanded(
                            child: Container(
                              height: 32,
                              margin: EdgeInsets.only(right: isLast ? 0 : 4),
                              child: FilledButton(
                                onPressed: appState.currentImage != null 
                                    ? () => appState.setWarpMode(mode)
                                    : null,
                                style: FilledButton.styleFrom(
                                  backgroundColor: isSelected 
                                      ? Theme.of(context).colorScheme.primary
                                      : Theme.of(context).colorScheme.surface,
                                  foregroundColor: isSelected 
                                      ? Theme.of(context).colorScheme.onPrimary
                                      : Theme.of(context).colorScheme.onSurface,
                                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(6),
                                    side: BorderSide(
                                      color: isSelected 
                                          ? Theme.of(context).colorScheme.primary
                                          : Theme.of(context).colorScheme.outline.withOpacity(0.3),
                                      width: 1,
                                    ),
                                  ),
                                  elevation: isSelected ? 2 : 0,
                                  minimumSize: const Size(0, 32),
                                ),
                                child: FittedBox(
                                  fit: BoxFit.scaleDown,
                                  child: Text(
                                    mode.displayName,
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  ],
                ),
              ] else ...[
                // 데스크톱: 3줄 레이아웃
                // 첫 번째 줄: 제목
                Text(
                  '변형 모드',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // 두 번째 줄: 당기기, 밀어내기
                Row(
                  children: [
                    Expanded(
                      child: _buildDesktopModeButton(context, appState, WarpMode.pull),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _buildDesktopModeButton(context, appState, WarpMode.push),
                    ),
                  ],
                ),
                
                const SizedBox(height: 16),
                
                // 세 번째 줄: 축소, 확대 
                Row(
                  children: [
                    Expanded(
                      child: _buildDesktopModeButton(context, appState, WarpMode.expand),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _buildDesktopModeButton(context, appState, WarpMode.shrink),
                    ),
                  ],
                ),
                
                const SizedBox(height: 20),
                
                // 현재 모드 설명 (데스크톱에서만)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _getModeIcon(appState.warpMode),
                        size: 24,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          appState.warpMode.description,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              
              SizedBox(height: isMobile ? 8 : 30),
              
              // Before/After와 결과저장 버튼
              if (appState.originalImage != null && appState.currentImage != null) ...[
                if (isMobile) ...[
                  // 모바일: 한 줄에
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: () => _showBeforeAfterComparison(context),
                          icon: Icon(Icons.compare, size: 16),
                          label: Text(
                            'Before/After',
                            style: TextStyle(fontSize: 12),
                          ),
                          style: FilledButton.styleFrom(
                            padding: EdgeInsets.symmetric(vertical: 8),
                          ),
                        ),
                      ),
                      SizedBox(width: 8),
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: () => _downloadImage(context),
                          icon: Icon(Icons.download, size: 16),
                          label: Text(
                            '저장',
                            style: TextStyle(fontSize: 12),
                          ),
                          style: FilledButton.styleFrom(
                            backgroundColor: Colors.white,
                            foregroundColor: Colors.black87,
                            padding: EdgeInsets.symmetric(vertical: 8),
                            side: BorderSide(color: Colors.grey.shade400, width: 1),
                          ),
                        ),
                      ),
                    ],
                  ),
                ] else ...[
                  // 데스크톱: 각각 한 줄씩
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: () => _showBeforeAfterComparison(context),
                      icon: Icon(Icons.compare, size: 24),
                      label: Text(
                        'Before/After',
                        style: TextStyle(fontSize: 16),
                      ),
                      style: FilledButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: () => _downloadImage(context),
                      icon: Icon(Icons.download, size: 24),
                      label: Text(
                        '결과 저장',
                        style: TextStyle(fontSize: 16),
                      ),
                      style: FilledButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black87,
                        padding: EdgeInsets.symmetric(vertical: 16),
                        side: BorderSide(color: Colors.grey.shade400, width: 1),
                      ),
                    ),
                  ),
                ],
                SizedBox(height: isMobile ? 8 : 16),
                
                // 재진단 버튼 (Before/After와 저장 버튼 아래)
                _buildReAnalysisButton(context, appState, isMobile),
                
                SizedBox(height: isMobile ? 8 : 30),
              ] else if (appState.currentImage != null) ...[
                // 이미지는 있지만 원본이 없는 경우 저장만 표시
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => _downloadImage(context),
                    icon: const Icon(Icons.download),
                    label: const Text('결과 저장'),
                    style: FilledButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.black87,
                      side: BorderSide(color: Colors.grey.shade400, width: 1),
                    ),
                  ),
                ),
                SizedBox(height: isMobile ? 8 : 20),
              ],
              
              // 사용법 안내 (가장 아래로)
              Container(
                padding: EdgeInsets.all(isMobile ? 8 : 12),
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
                            fontSize: isMobile ? 12 : null,
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: isMobile ? 4 : 8),
                    Text(
                      isMobile 
                          ? '1. 변형모드 선택\n2. 반경/강도 조절\n3. 짧게 터치&드래그로 워핑\n4. 길게 누르고 드래그로 이동'
                          : '1. 원하는 변형 모드를 선택하세요\n'
                            '2. 영향 반경(%)과 강도를 조절하세요\n'
                            '3. 좌측 하단 버튼으로 줌인하세요\n'
                            '4. 길게 누르고 드래그: 이미지 이동 (팬)\n'
                            '5. 짧게 클릭/터치 드래그: 워핑 적용\n'
                            '6. 뒤로가기/원본복원으로 실수를 되돌리세요',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                        fontSize: isMobile ? 10 : null,
                      ),
                    ),
                  ],
                ),
              ),
            ],
              ),
            );
          },
        );
      },
    );
  }

  void _showBeforeAfterComparison(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => const Scaffold(
          body: BeforeAfterComparison(),
        ),
      ),
    );
  }

  Widget _buildDesktopModeButton(BuildContext context, AppState appState, WarpMode mode) {
    final isSelected = appState.warpMode == mode;
    return SizedBox(
      height: 60,
      child: FilledButton.icon(
        onPressed: appState.currentImage != null 
            ? () => appState.setWarpMode(mode)
            : null,
        icon: Icon(
          _getModeIcon(mode),
          size: 24,
        ),
        label: Text(
          mode.displayName,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        style: FilledButton.styleFrom(
          backgroundColor: isSelected 
              ? Theme.of(context).colorScheme.primary
              : Theme.of(context).colorScheme.surfaceVariant,
          foregroundColor: isSelected 
              ? Theme.of(context).colorScheme.onPrimary
              : Theme.of(context).colorScheme.onSurfaceVariant,
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(
              color: isSelected 
                  ? Theme.of(context).colorScheme.primary
                  : Theme.of(context).colorScheme.outline.withOpacity(0.3),
              width: 2,
            ),
          ),
          elevation: isSelected ? 4 : 1,
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

  Widget _buildReAnalysisButton(BuildContext context, AppState appState, bool isMobile) {
    // 원본 분석이 있고 재진단 중이 아닐 때만 표시
    if (appState.originalBeautyAnalysis == null) {
      return const SizedBox.shrink();
    }

    return Container(
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: appState.currentImage != null && !appState.isReAnalyzing
            ? () => appState.startReAnalysis()
            : null,
        icon: appState.isReAnalyzing 
            ? SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Theme.of(context).colorScheme.onPrimary,
                ),
              )
            : Icon(Icons.analytics, size: isMobile ? 16 : 18),
        label: Text(
          appState.isReAnalyzing ? '재진단 중...' : '🔄 뷰티 점수 다시 진단',
          style: TextStyle(
            fontSize: isMobile ? 12 : 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        style: FilledButton.styleFrom(
          backgroundColor: Theme.of(context).colorScheme.tertiary,
          foregroundColor: Theme.of(context).colorScheme.onTertiary,
          padding: EdgeInsets.symmetric(vertical: isMobile ? 12 : 16),
        ),
      ),
    );
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