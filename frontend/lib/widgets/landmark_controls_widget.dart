import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';

/// 랜드마크 컨트롤 위젯
class LandmarkControlsWidget extends StatelessWidget {
  const LandmarkControlsWidget({super.key});

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
                  '얼굴 랜드마크',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // 랜드마크 정보
                if (appState.landmarks.isNotEmpty) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surfaceVariant,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.face,
                          size: 20,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '${appState.landmarks.length}개 랜드마크 검출됨',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 12),
                ],
                
                // 랜드마크 표시 토글
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('랜드마크 표시'),
                  subtitle: Text(
                    appState.landmarks.isEmpty 
                        ? '이미지를 업로드하면 자동으로 검출됩니다'
                        : '얼굴의 주요 특징점을 표시합니다',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  value: appState.showLandmarks,
                  onChanged: appState.landmarks.isNotEmpty 
                      ? (value) => appState.toggleLandmarks()
                      : null,
                ),
                
                const SizedBox(height: 8),
                
                // 랜드마크 정보 텍스트
                if (appState.landmarks.isNotEmpty)
                  Text(
                    'MediaPipe Face Mesh를 사용하여 468개의 3D 얼굴 랜드마크를 검출합니다. '
                    '이 점들은 얼굴의 주요 특징(눈, 코, 입, 윤곽 등)을 정확하게 표현합니다.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}