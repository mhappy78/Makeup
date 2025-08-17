import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';

/// 뷰티 점수 비교 결과 표시 위젯
class BeautyComparisonWidget extends StatelessWidget {
  const BeautyComparisonWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        final comparison = appState.beautyAnalysis['comparison'] as Map<String, dynamic>?;
        
        // GPT 분석 중일 때 로딩 인디케이터 표시
        if (appState.isGptAnalyzing) {
          return Container(
            margin: const EdgeInsets.all(16),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
                  Theme.of(context).colorScheme.secondaryContainer.withOpacity(0.3),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                width: 2,
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          Theme.of(context).colorScheme.primary,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Flexible(
                      child: Text(
                        '🤖 AI 전문가가 재진단 결과를 분석 중입니다...',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        overflow: TextOverflow.ellipsis,
                        maxLines: 2,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  '변화된 뷰티 점수를 바탕으로 맞춤형 분석과 추천사항을 준비하고 있어요.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.grey.shade600,
                  ),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 3,
                ),
              ],
            ),
          );
        }
        
        if (comparison == null || comparison['isReAnalysis'] != true) {
          return const SizedBox.shrink();
        }

        return Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
                Theme.of(context).colorScheme.secondaryContainer.withOpacity(0.3),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
              width: 2,
            ),
          ),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 헤더
                Row(
                  children: [
                    Icon(
                      Icons.analytics,
                      color: Theme.of(context).colorScheme.primary,
                      size: 24,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '🔄 재진단 결과 비교',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    ),
                    const Spacer(),
                    Flexible(
                      child: _buildOverallChangeChip(context, comparison['overallChange'] as String),
                    ),
                  ],
                ),
                
                const SizedBox(height: 16),
                
                // 점수 변화 표시
                _buildScoreChanges(context, comparison['scoreChanges'] as Map<String, double>),
                
                const SizedBox(height: 16),
                
                // GPT 분석 텍스트
                if (comparison['analysisText'] != null && (comparison['analysisText'] as String).isNotEmpty) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surface.withOpacity(0.8),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              Icons.psychology,
                              size: 20,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'AI 전문가 분석',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          comparison['analysisText'] as String,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                
                // 추천사항
                if (comparison['recommendations'] != null) ...[
                  Text(
                    '💡 맞춤 추천사항',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...((comparison['recommendations'] as List<String>).map((rec) => 
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('• ', style: TextStyle(
                            color: Theme.of(context).colorScheme.primary,
                            fontWeight: FontWeight.bold,
                          )),
                          Expanded(child: Text(rec, style: Theme.of(context).textTheme.bodyMedium)),
                        ],
                      ),
                    ),
                  )),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildOverallChangeChip(BuildContext context, String overallChange) {
    Color chipColor;
    String chipText;
    IconData chipIcon;

    switch (overallChange) {
      case 'improved':
        chipColor = Colors.green;
        chipText = '개선됨';
        chipIcon = Icons.trending_up;
        break;
      case 'declined':
        chipColor = Colors.red;
        chipText = '변화필요';
        chipIcon = Icons.trending_down;
        break;
      default:
        chipColor = Colors.orange;
        chipText = '유지';
        chipIcon = Icons.trending_flat;
    }

    return Chip(
      avatar: Icon(chipIcon, size: 16, color: Colors.white),
      label: Text(
        chipText,
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
      ),
      backgroundColor: chipColor,
    );
  }

  Widget _buildScoreChanges(BuildContext context, Map<String, double> scoreChanges) {
    if (scoreChanges.isEmpty) return const SizedBox.shrink();

    final scoreItems = <Widget>[];
    
    scoreChanges.forEach((key, change) {
      if (key == 'overall') return; // 전체 점수는 별도 표시
      
      String displayName = _getDisplayName(key);
      Color changeColor = change > 0 ? Colors.green : (change < 0 ? Colors.red : Colors.grey);
      String changeText = change > 0 ? '+${change.toStringAsFixed(1)}' : change.toStringAsFixed(1);
      
      scoreItems.add(
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 2),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(child: Text(displayName)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: changeColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: changeColor.withOpacity(0.3)),
                ),
                child: Text(
                  changeText,
                  style: TextStyle(
                    color: changeColor,
                    fontWeight: FontWeight.w600,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📊 항목별 점수 변화',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface.withOpacity(0.8),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(children: scoreItems),
        ),
      ],
    );
  }

  String _getDisplayName(String key) {
    switch (key) {
      case 'verticalScore':
        return '가로 황금비율';
      case 'horizontalScore':
        return '세로 대칭성';
      case 'lowerFaceScore':
        return '하관 조화';
      case 'symmetry':
        return '전체 대칭성';
      case 'eyeScore':
        return '눈';
      case 'noseScore':
        return '코';
      case 'lipScore':
        return '입술';
      case 'jawScore':
        return '턱 곡률';
      default:
        return key;
    }
  }
}