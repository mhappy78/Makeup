import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';
import '../models/face_regions.dart';

/// 얼굴 부위별 표시 컨트롤 위젯
class FaceRegionsWidget extends StatelessWidget {
  const FaceRegionsWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 헤더
              Row(
                children: [
                  Icon(
                    Icons.face,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '부위별 표시',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 16),
              
              // 전체 토글
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Icon(
                        Icons.visibility,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '랜드마크 표시',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      Switch(
                        value: appState.showLandmarks,
                        onChanged: appState.landmarks.isNotEmpty
                            ? (value) => appState.toggleLandmarks()
                            : null,
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // 부위별 리스트
              Expanded(
                child: appState.landmarks.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.face_outlined,
                              size: 64,
                              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.3),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              '이미지를 업로드하면\n부위별 랜드마크가 표시됩니다',
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                              ),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: FaceRegions.regions.length,
                        itemBuilder: (context, index) {
                          final regionKey = FaceRegions.regions.keys.elementAt(index);
                          final regionData = FaceRegions.regions[regionKey]!;
                          final isVisible = appState.regionVisibility.isVisible(regionKey);
                          final hasAnimation = regionData.hasAnimation;
                          final isAnimating = appState.currentAnimatingRegion == regionKey;
                          
                          return Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: Column(
                              children: [
                                ListTile(
                                  leading: Container(
                                    width: 24,
                                    height: 24,
                                    decoration: BoxDecoration(
                                      color: regionData.color,
                                      shape: BoxShape.circle,
                                      border: Border.all(
                                        color: Colors.white,
                                        width: 2,
                                      ),
                                    ),
                                  ),
                                  title: Text(
                                    regionData.name,
                                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  subtitle: Text(
                                    '${regionData.indices.length}개 랜드마크${hasAnimation ? ' • 애니메이션 지원' : ''}',
                                    style: Theme.of(context).textTheme.bodySmall,
                                  ),
                                  trailing: Switch(
                                    value: isVisible && appState.showLandmarks,
                                    onChanged: appState.showLandmarks
                                        ? (value) => appState.toggleRegionVisibility(regionKey)
                                        : null,
                                  ),
                                  onTap: appState.showLandmarks
                                      ? () => appState.toggleRegionVisibility(regionKey)
                                      : null,
                                ),
                                
                                // 애니메이션 버튼 (애니메이션 지원 부위만)
                                if (hasAnimation && isVisible && appState.showLandmarks)
                                  Padding(
                                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                                    child: SizedBox(
                                      width: double.infinity,
                                      child: ElevatedButton.icon(
                                        onPressed: isAnimating 
                                            ? null 
                                            : () => _startAnimation(context, regionKey),
                                        icon: isAnimating 
                                            ? const SizedBox(
                                                width: 16,
                                                height: 16,
                                                child: CircularProgressIndicator(strokeWidth: 2),
                                              )
                                            : const Icon(Icons.play_arrow, size: 20),
                                        label: Text(
                                          isAnimating ? '애니메이션 재생 중...' : '애니메이션 재생',
                                          style: const TextStyle(fontSize: 12),
                                        ),
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: regionData.color.withOpacity(0.1),
                                          foregroundColor: regionData.color,
                                          padding: const EdgeInsets.symmetric(vertical: 8),
                                        ),
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          );
                        },
                      ),
              ),
              
              // 하단 정보
              if (appState.landmarks.isNotEmpty) ...[
                const Divider(),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.info_outline,
                        size: 16,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'MediaPipe 468개 랜드마크를 부위별로 그룹화하여 표시합니다',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
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
  
  void _startAnimation(BuildContext context, String regionKey) async {
    final appState = context.read<AppState>();
    final regionData = FaceRegions.regions[regionKey]!;
    
    if (!regionData.hasAnimation) return;
    
    appState.startRegionAnimation(regionKey);
    
    // 눈썹주변영역 애니메이션 (3초 동안)
    if (regionKey == 'eyebrow_area') {
      const duration = Duration(milliseconds: 3000);
      const steps = 60; // 60 FPS
      const stepDuration = Duration(milliseconds: 50);
      
      for (int i = 0; i <= steps; i++) {
        if (appState.currentAnimatingRegion != regionKey) break;
        
        final progress = i / steps;
        appState.updateAnimationProgress(regionKey, progress);
        
        await Future.delayed(stepDuration);
      }
      
      // 눈썹주변영역 완료 후 눈썹 애니메이션 시작
      if (appState.currentAnimatingRegion == regionKey) {
        await _startEyebrowAnimation(context, appState);
      }
    }
    // 눈썹 단독 애니메이션
    else if (regionKey == 'eyebrows') {
      await _startEyebrowAnimation(context, appState);
    }
    
    appState.stopAnimation();
  }
  
  Future<void> _startEyebrowAnimation(BuildContext context, AppState appState) async {
    const regionKey = 'eyebrows';
    appState.startRegionAnimation(regionKey);
    
    // 눈썹 애니메이션 (2초 동안)
    const duration = Duration(milliseconds: 2000);
    const steps = 40; // 40 FPS
    const stepDuration = Duration(milliseconds: 50);
    
    for (int i = 0; i <= steps; i++) {
      if (appState.currentAnimatingRegion != regionKey) break;
      
      final progress = i / steps;
      appState.updateAnimationProgress(regionKey, progress);
      
      await Future.delayed(stepDuration);
    }
  }
}