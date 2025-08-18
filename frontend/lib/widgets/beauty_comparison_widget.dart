import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
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
                        appState.isReAnalyzing 
                          ? '🤖 AI 전문가가 재진단 결과를 분석 중입니다...'
                          : '🤖 AI 전문가가 진단 결과를 분석 중입니다...',
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
                        _buildRichAnalysisText(context, comparison['analysisText'] as String),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
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
      String changeText = change > 0 ? '+${change.round()}점' : '${change.round()}점';
      
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

  /// AI 전문가 분석 텍스트를 2번 항목까지만 표시
  Widget _buildTruncatedAnalysisText(BuildContext context, String text) {
    // --- 구분선 이전의 내용만 사용 (1, 2번 분석 부분)
    final parts = text.split('---');
    final analysisOnly = parts[0].trim();
    
    return Text(
      analysisOnly,
      style: Theme.of(context).textTheme.bodyMedium,
    );
  }

  /// AI 전문가 분석 텍스트를 리치 텍스트로 변환 (초기 분석과 동일한 스타일)
  Widget _buildRichAnalysisText(BuildContext context, String text) {
    final lines = text.split('\n');
    final List<Widget> widgets = [];
    
    for (String line in lines) {
      line = line.trim();
      if (line.isEmpty) continue;
      
      // ### 1. 전반적인 변화 요약, ### 2. 항목별 상세 분석 형태의 메인 제목
      if (line.startsWith('### 1.') || line.startsWith('### 2.') || line.startsWith('1.') || line.startsWith('2.')) {
        widgets.add(Padding(
          padding: EdgeInsets.only(bottom: 8, top: widgets.isEmpty ? 0 : 16),
          child: _buildRichTextLine(context, line, TextType.mainTitle),
        ));
      }
      // 개선된 점: 형태의 서브 제목 (이모지 및 : 제거)
      else if (line.contains('개선된 점')) {
        String cleanLine = line.replaceAll('🟢', '').replaceAll(':', '').trim();
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6, top: 12),
          child: _buildRichTextLine(context, cleanLine, TextType.subTitle),
        ));
      }
      // 아쉬운 점: 형태의 서브 제목 (이모지 및 : 제거)
      else if (line.contains('아쉬운 점')) {
        String cleanLine = line.replaceAll('🔸', '').replaceAll(':', '').trim();
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6, top: 12),
          child: _buildRichTextLine(context, cleanLine, TextType.subTitle),
        ));
      }
      // - 항목명: 내용 형태의 리스트 아이템
      else if (line.startsWith('-')) {
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6, left: 16),
          child: _buildRichTextLine(context, line, TextType.body),
        ));
      }
      // 일반 본문 텍스트
      else {
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: _buildRichTextLine(context, line, TextType.body),
        ));
      }
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  /// 케어 팁 텍스트를 리치 텍스트로 변환 (초기 분석과 동일한 스타일)
  Widget _buildRichCareTipText(BuildContext context, String text) {
    final lines = text.split('\n');
    final List<Widget> widgets = [];
    
    for (String line in lines) {
      line = line.trim();
      if (line.isEmpty) continue;
      
      // 🎯 **가로 황금비율 개선** 형태의 메인 제목
      if (line.contains('🎯') && line.contains('**')) {
        widgets.add(Padding(
          padding: EdgeInsets.only(bottom: 8, top: widgets.isEmpty ? 0 : 16),
          child: _buildRichTextLine(context, line, TextType.mainTitle),
        ));
      }
      // 💪 **운동/습관**: 형태의 서브 제목
      else if ((line.contains('💪') || line.contains('🏥')) && line.contains('**')) {
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6, top: 12),
          child: _buildRichTextLine(context, line, TextType.subTitle),
        ));
      }
      // 단순히 🎯, 💪, 🏥 아이콘만 있는 라인 (볼드 없음)
      else if (line.contains('🎯') || line.contains('💪') || line.contains('🏥')) {
        widgets.add(Padding(
          padding: EdgeInsets.only(bottom: 6, top: widgets.isEmpty ? 0 : 12),
          child: _buildRichTextLine(context, line, TextType.title),
        ));
      }
      // **볼드** 텍스트만 있는 소제목
      else if (line.contains('**')) {
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 4, top: 8),
          child: _buildRichTextLine(context, line, TextType.subtitle),
        ));
      }
      // 일반 본문 텍스트 (들여쓰기 16px)
      else {
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6, left: 16),
          child: _buildRichTextLine(context, line, TextType.body),
        ));
      }
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  /// URL 클릭 기능이 있는 리치 텍스트 라인 생성
  Widget _buildRichTextLine(BuildContext context, String text, TextType type) {
    // **볼드** 및 ### 마크다운 헤더 제거
    text = text.replaceAll('**', '').replaceAll('###', '').trim();
    
    // URL이 있는지 확인
    if (text.contains('http')) {
      return _buildTextWithLinks(context, text, type);
    } else {
      return SelectableText(
        text,
        style: _getTextStyle(context, type),
      );
    }
  }

  /// URL이 포함된 텍스트 처리
  Widget _buildTextWithLinks(BuildContext context, String text, TextType type) {
    final urlPattern = RegExp(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)');
    final matches = urlPattern.allMatches(text);
    
    if (matches.isEmpty) {
      return SelectableText(text, style: _getTextStyle(context, type));
    }

    List<InlineSpan> spans = [];
    int lastIndex = 0;

    for (final match in matches) {
      // URL 이전 텍스트 추가
      if (match.start > lastIndex) {
        spans.add(TextSpan(
          text: text.substring(lastIndex, match.start),
          style: _getTextStyle(context, type),
        ));
      }

      // 클릭 가능한 URL 추가
      final linkText = match.group(1)!;
      final url = match.group(2)!;
      
      spans.add(TextSpan(
        text: linkText,
        style: _getTextStyle(context, type).copyWith(
          color: Colors.lightGreen.shade700, // 연두색
          decoration: TextDecoration.underline,
        ),
        recognizer: TapGestureRecognizer()
          ..onTap = () async {
            if (await canLaunchUrl(Uri.parse(url))) {
              await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
            }
          },
      ));

      lastIndex = match.end;
    }

    // 마지막 부분 추가
    if (lastIndex < text.length) {
      spans.add(TextSpan(
        text: text.substring(lastIndex),
        style: _getTextStyle(context, type),
      ));
    }

    return SelectableText.rich(
      TextSpan(children: spans),
    );
  }

  /// 텍스트 타입에 따른 스타일 반환
  TextStyle _getTextStyle(BuildContext context, TextType type) {
    switch (type) {
      case TextType.mainTitle:
        return Theme.of(context).textTheme.titleMedium!.copyWith(
          fontWeight: FontWeight.bold,
          color: Colors.green.shade700,
          fontSize: 16,
        );
      case TextType.subTitle:
        return Theme.of(context).textTheme.bodyMedium!.copyWith(
          fontWeight: FontWeight.bold,
          color: Colors.green.shade700,
          fontSize: 14,
        );
      case TextType.title:
        return Theme.of(context).textTheme.bodyMedium!.copyWith(
          fontWeight: FontWeight.bold,
          color: Colors.green.shade700,
          fontSize: 15,
        );
      case TextType.subtitle:
        return Theme.of(context).textTheme.bodyMedium!.copyWith(
          fontWeight: FontWeight.normal,
          color: Colors.grey.shade800,
          fontSize: 14,
        );
      case TextType.body:
        return Theme.of(context).textTheme.bodyMedium!.copyWith(
          fontWeight: FontWeight.normal,
          color: Colors.grey.shade800,
          fontSize: 14,
        );
    }
  }
}

enum TextType { mainTitle, subTitle, title, subtitle, body }