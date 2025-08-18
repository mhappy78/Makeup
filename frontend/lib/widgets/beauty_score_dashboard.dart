import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/app_state.dart';
import 'beauty_comparison_widget.dart';
import 'dart:math' as math;
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/gestures.dart';

/// 텍스트 타입 enum
enum TextType { mainTitle, subTitle, title, subtitle, body }

/// 뷰티 스코어 분석 대시보드 위젯
class BeautyScoreDashboard extends StatefulWidget {
  const BeautyScoreDashboard({super.key});

  @override
  State<BeautyScoreDashboard> createState() => _BeautyScoreDashboardState();
}

class _BeautyScoreDashboardState extends State<BeautyScoreDashboard>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  String? _selectedCategory;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (appState.landmarks.isEmpty || !appState.showBeautyScore) {
          return _buildEmptyState(context, appState);
        }
        
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 헤더
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [Colors.pink.shade400, Colors.purple.shade500],
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.auto_awesome,
                      color: Colors.white,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '뷰티 스코어',
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Colors.purple.shade700,
                        ),
                      ),
                      Text(
                        'AI 기반 얼굴 분석 리포트',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              
              const SizedBox(height: 20),
              
              // 메인 컨텐츠
              _buildBeautyAnalysisContent(context, appState),
            ],
          ),
        );
      },
    );
  }

  Widget _buildEmptyState(BuildContext context, AppState appState) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.pink.shade200, Colors.purple.shade300],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.face_retouching_natural,
              size: 60,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 24),
          Text(
            appState.isAutoAnimationMode
                ? '얼굴을 분석하고 있어요...'
                : '이미지를 업로드하면\nAI가 당신의 뷰티 스코어를\n전문적으로 분석해드려요',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Colors.grey.shade600,
              height: 1.5,
            ),
          ),
          if (appState.isAutoAnimationMode) ...[
            const SizedBox(height: 20),
            SizedBox(
              width: 40,
              height: 40,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.purple.shade400),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBeautyAnalysisContent(BuildContext context, AppState appState) {
    final analysis = appState.beautyAnalysis;
    if (analysis.isEmpty) return _buildEmptyState(context, appState);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 종합 뷰티 분석 (중복 내용 통합)
        _buildGptAnalysisWidget(context, analysis),
        
        // 비교 결과 (재진단 시 표시)
        const BeautyComparisonWidget(),
        
        // 인터랙티브 세부 분석
        _buildInteractiveDetailedAnalysis(context, analysis),
        const SizedBox(height: 20),
        
        // 재분석 실천 가능한 케어 팁 (세부 분석 바로 아래)
        _buildReAnalysisCareTips(context, analysis),
        
        // 초기 분석 실천 가능한 케어 팁 (세부 분석 다음에 위치)
        _buildActionableCareTips(context, analysis),
        const SizedBox(height: 20),
        
        // 진행 상황 추적
        _buildProgressTracking(context, analysis),
      ],
    );
  }

  Widget _buildOverallScoreCard(BuildContext context, Map<String, dynamic> analysis) {
    final score = analysis['overallScore']?.toDouble() ?? 75.0;
    
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.pink.shade50, Colors.purple.shade50],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.purple.shade100),
      ),
      child: Column(
        children: [
          Text(
            '종합 뷰티 스코어',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Colors.purple.shade700,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 120,
                height: 120,
                child: CircularProgressIndicator(
                  value: score / 100,
                  strokeWidth: 12,
                  backgroundColor: Colors.purple.shade100,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    score >= 80 ? Colors.green : score >= 60 ? Colors.orange : Colors.red,
                  ),
                ),
              ),
              Column(
                children: [
                  Text(
                    '${score.round()}',
                    style: Theme.of(context).textTheme.displayMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.purple.shade700,
                    ),
                  ),
                  Text(
                    '점',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Colors.purple.shade600,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            _getScoreDescription(score),
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.purple.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailedAnalysis(BuildContext context, Map<String, dynamic> analysis) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 섹션 헤더
        Text(
          '🧬 정밀 분석 리포트',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
            color: Colors.purple.shade700,
          ),
        ),
        const SizedBox(height: 16),
        
        // 메인 분석 차트
        _buildAnalysisChart(context, analysis),
        const SizedBox(height: 20),
        
        // 정량적 측정 데이터 (항상 표시)
        _buildDetailedMetrics(context, analysis),
        const SizedBox(height: 20),
        
        // 인터랙티브 카테고리
        _buildInteractiveCategories(context, analysis),
      ],
    );
  }

  Widget _buildRecommendations(BuildContext context, Map<String, dynamic> analysis) {
    final recommendations = _generateRecommendations(analysis);
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.amber.shade50, Colors.orange.shade50],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.orange.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: Colors.orange.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  Icons.lightbulb,
                  color: Colors.orange.shade600,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '개인 맞춤 뷰티 제안',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Colors.orange.shade800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...recommendations.map((recommendation) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 6,
                  height: 6,
                  margin: const EdgeInsets.only(top: 6, right: 12),
                  decoration: BoxDecoration(
                    color: Colors.orange.shade400,
                    shape: BoxShape.circle,
                  ),
                ),
                Expanded(
                  child: Text(
                    recommendation,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.orange.shade700,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildAnalysisInfo(BuildContext context, Map<String, dynamic> analysis) {
    final timestampStr = analysis['analysisTimestamp'] as String?;
    final timestamp = timestampStr != null ? DateTime.tryParse(timestampStr) : null;
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.analytics,
                color: Colors.purple.shade600,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                '분석 정보',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Colors.purple.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            '• AI 기반 MediaPipe 468개 랜드마크 분석\n'
            '• 황금비율 및 얼굴 대칭성 측정\n'
            '• 개인 맞춤형 뷰티 개선 제안\n'
            '${timestamp != null ? '• 분석일시: ${_formatTimestamp(timestamp)}' : ''}',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.grey.shade600,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.purple.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.purple.shade200),
            ),
            child: Text(
              '💡 이 분석 결과는 AI 기반 추정치이며, 개인의 주관적 아름다움과 다를 수 있습니다.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.purple.shade700,
                fontStyle: FontStyle.italic,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getScoreDescription(double score) {
    if (score >= 90) return '완벽한 아름다움! 모든 비율이 이상적입니다.';
    if (score >= 80) return '매우 아름다운 얼굴! 뛰어난 균형감을 가지고 있어요.';
    if (score >= 70) return '아름다운 얼굴이에요! 몇 가지 포인트만 개선하면 완벽해요.';
    if (score >= 60) return '매력적인 얼굴입니다. 개선 포인트를 참고해보세요.';
    return '독특하고 개성 있는 매력을 가지고 있어요!';
  }

  List<String> _generateRecommendations(Map<String, dynamic> analysis) {
    // 먼저 Backend GPT 분석에서 추천사항 확인
    final gptAnalysis = analysis['gptAnalysis'] as Map<String, dynamic>?;
    print('🔍 케어 팁 생성 - gptAnalysis: $gptAnalysis');
    
    if (gptAnalysis != null && gptAnalysis['recommendations'] != null) {
      final gptRecommendations = List<String>.from(gptAnalysis['recommendations']);
      print('🔍 GPT recommendations 발견: $gptRecommendations');
      if (gptRecommendations.isNotEmpty) {
        print('🔍 GPT recommendations 사용함 (${gptRecommendations.length}개)');
        return gptRecommendations.take(3).toList();
      }
    }
    
    print('🔍 GPT recommendations 없음 - 폴백 케어 팁 사용');
    
    // GPT 추천사항이 없을 경우에만 폴백 케어 팁 생성
    final List<String> careTips = [];
    final overallScore = analysis['overallScore']?.toDouble() ?? 75.0;
    
    // 기본 케어 팁 1: 수분 관리
    careTips.add('충분한 수분 섭취 (하루 2L 이상)와 보습 크림 사용으로 피부 탄력 유지하기');
    
    // 점수에 따른 맞춤 케어 팁 2
    if (overallScore >= 85) {
      careTips.add('현재 상태 유지를 위한 정기적인 페이셜 마사지와 자외선 차단제 필수 사용');
    } else if (overallScore >= 70) {
      careTips.add('안면 근육 운동(입술 운동, 볼 마사지)으로 혈액 순환 개선하기');
    } else {
      careTips.add('균형 잡힌 식단과 충분한 수면(7-8시간)으로 피부 재생 도움');
    }
    
    // 케어 팁 3: 생활습관 개선
    final verticalPercentages = analysis['verticalScore']?['percentages'] as List<double>?;
    final gonialAngle = analysis['jawScore']?['gonialAngle']?.toDouble();
    
    if (gonialAngle != null && gonialAngle > 120) {
      careTips.add('턱 마사지와 목 스트레칭으로 턱선 정리하고 올바른 자세 유지하기');
    } else if (verticalPercentages != null) {
      bool hasImbalance = verticalPercentages.any((pct) => (pct - 20.0).abs() > 3.0);
      if (hasImbalance) {
        careTips.add('얼굴 요가와 림프 마사지로 얼굴 근육 균형 개선하기');
      } else {
        careTips.add('주 2-3회 얼굴 팩과 정기적인 각질 제거로 피부 컨디션 관리하기');
      }
    } else {
      careTips.add('스트레스 관리와 금연, 금주로 피부 건강 전반적으로 개선하기');
    }
    
    return careTips.take(3).toList(); // 정확히 3개 반환
  }

  String _formatTimestamp(DateTime timestamp) {
    return '${timestamp.year}.${timestamp.month.toString().padLeft(2, '0')}.${timestamp.day.toString().padLeft(2, '0')} '
           '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}';
  }

  /// 케어 팁 텍스트를 리치 텍스트로 변환 (제목/본문 스타일링, URL 클릭 기능)
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
      // 일반 본문 텍스트 (들여쓰기 16px = 스페이스 4번)
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
    // **볼드** 제거
    text = text.replaceAll('**', '');
    
    // URL 패턴 찾기
    final urlPattern = RegExp(r'\(https?://[^\s\)]+\)');
    final linkTextPattern = RegExp(r'\[[^\]]+\]');
    
    // URL이 있는지 확인
    if (text.contains('http')) {
      return _buildTextWithLinks(context, text, type);
    } else {
      // URL이 없으면 일반 텍스트
      return SelectableText(
        text,
        style: _getTextStyle(context, type),
      );
    }
  }

  /// URL 링크가 포함된 텍스트 생성
  Widget _buildTextWithLinks(BuildContext context, String text, TextType type) {
    final List<TextSpan> spans = [];
    
    // [링크텍스트](URL) 패턴 처리
    final combinedPattern = RegExp(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)');
    final matches = combinedPattern.allMatches(text);
    
    int lastIndex = 0;
    
    for (final match in matches) {
      // 링크 이전 텍스트 추가
      if (match.start > lastIndex) {
        final beforeText = text.substring(lastIndex, match.start);
        if (beforeText.isNotEmpty) {
          spans.add(TextSpan(
            text: beforeText,
            style: _getTextStyle(context, type),
          ));
        }
      }
      
      // 링크 텍스트와 URL 추출
      final linkText = match.group(1) ?? '';
      final url = match.group(2) ?? '';
      
      // 링크 스판 추가 (연두색)
      spans.add(TextSpan(
        text: linkText,
        style: _getTextStyle(context, type).copyWith(
          color: Colors.lightGreen.shade600,
          decoration: TextDecoration.underline,
        ),
        recognizer: TapGestureRecognizer()
          ..onTap = () => _launchURL(url),
      ));
      
      lastIndex = match.end;
    }
    
    // 마지막 남은 텍스트 추가
    if (lastIndex < text.length) {
      final remainingText = text.substring(lastIndex);
      if (remainingText.isNotEmpty) {
        spans.add(TextSpan(
          text: remainingText,
          style: _getTextStyle(context, type),
        ));
      }
    }
    
    return SelectableText.rich(
      TextSpan(children: spans),
    );
  }

  /// URL 실행 함수
  Future<void> _launchURL(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  /// 텍스트 타입에 따른 스타일 반환 (케어 팁 전용 스타일)
  TextStyle _getTextStyle(BuildContext context, TextType type) {
    switch (type) {
      case TextType.mainTitle:
        // 🎯 가로 황금비율 개선 - 녹색 제목
        return Theme.of(context).textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.bold,
          color: Colors.green.shade700,
          height: 1.4,
          fontSize: 16,
        ) ?? const TextStyle();
      case TextType.subTitle:
        // 💪 운동/습관, 🏥 전문관리 - 검은색 내용
        return Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.normal,
          color: Colors.black87,
          height: 1.4,
          fontSize: 15,
        ) ?? const TextStyle();
      case TextType.title:
        // 일반 제목 - 녹색
        return Theme.of(context).textTheme.titleSmall?.copyWith(
          fontWeight: FontWeight.bold,
          color: Colors.green.shade700,
          height: 1.4,
          fontSize: 16,
        ) ?? const TextStyle();
      case TextType.subtitle:
        // 소제목 - 검은색
        return Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.normal,
          color: Colors.black87,
          height: 1.4,
          fontSize: 15,
        ) ?? const TextStyle();
      case TextType.body:
        // 본문 - 검은색, 볼드 제외
        return Theme.of(context).textTheme.bodyMedium?.copyWith(
          height: 1.6,
          color: Colors.black87,
          fontSize: 15,
          fontWeight: FontWeight.normal,
        ) ?? const TextStyle();
    }
  }

  /// 아이콘과 텍스트를 스타일링하여 표시 (케어 팁용)
  Widget _buildStyledIconText(BuildContext context, String text, {
    bool isMainTitle = false,
    bool isSubTitle = false,
    bool isTitle = false, 
    bool isSubtitle = false, 
    bool isBody = false
  }) {
    // **볼드** 텍스트 처리
    text = text.replaceAll('**', '');
    
    TextStyle style;
    if (isMainTitle) {
      // 🎯 **가로 황금비율 개선** - 가장 큰 제목
      style = Theme.of(context).textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.bold,
        color: Colors.indigo.shade700,
        height: 1.4,
        fontSize: 17,
      ) ?? const TextStyle();
    } else if (isSubTitle) {
      // 💪 **운동/습관**: - 중간 제목
      style = Theme.of(context).textTheme.titleSmall?.copyWith(
        fontWeight: FontWeight.w600,
        color: Colors.indigo.shade600,
        height: 1.4,
        fontSize: 15,
      ) ?? const TextStyle();
    } else if (isTitle) {
      // 단순 아이콘 제목
      style = Theme.of(context).textTheme.titleSmall?.copyWith(
        fontWeight: FontWeight.bold,
        color: Colors.indigo.shade700,
        height: 1.4,
      ) ?? const TextStyle();
    } else if (isSubtitle) {
      // **볼드** 소제목
      style = Theme.of(context).textTheme.bodyMedium?.copyWith(
        fontWeight: FontWeight.w600,
        color: Colors.indigo.shade600,
        height: 1.4,
      ) ?? const TextStyle();
    } else {
      // 본문: 일반 글씨 + 기본 색깔
      style = Theme.of(context).textTheme.bodyMedium?.copyWith(
        color: Colors.grey.shade800,
        height: 1.5,
        fontWeight: FontWeight.normal,
        fontSize: 14,
      ) ?? const TextStyle();
    }
    
    return Text(
      text,
      style: style,
    );
  }

  /// AI 분석 텍스트를 리치 텍스트로 변환 (3번까지만 표시)
  Widget _buildRichAnalysisText(BuildContext context, String text) {
    print('🔍 _buildRichAnalysisText 호출됨');
    print('🔍 입력 텍스트 길이: ${text.length}');
    print('🔍 입력 텍스트 전체: $text');
    
    // --- 구분선 이전의 내용만 사용 (1, 2, 3번 분석 부분)
    final parts = text.split('---');
    final analysisOnly = parts[0].trim();
    
    print('🔍 --- 분리 후 analysisOnly: $analysisOnly');
    
    final lines = analysisOnly.split('\n');
    final List<Widget> widgets = [];
    bool reachedEnd = false;
    
    print('🔍 총 라인 수: ${lines.length}');
    
    for (int i = 0; i < lines.length; i++) {
      String line = lines[i].trim();
      if (line.isEmpty) continue;
      
      print('🔍 처리 중인 라인 $i: $line');
      
      // ### 마크다운 헤더 처리
      if (line.startsWith('###')) {
        // 실천 방법 관련 ### 헤더면 중단
        if (line.contains('실천 방법') || line.contains('개선 방법') || line.contains('구체적 실천')) {
          print('🔍 실천 방법 ### 헤더 발견, 중단: $line');
          reachedEnd = true;
          break;
        } else {
          // 분석 섹션의 ### 헤더는 마크다운 제거 후 메인 제목 체크
          final cleanedLine = line.replaceAll('###', '').trim();
          print('🔍 분석 ### 헤더 발견: $cleanedLine');
          
          // 메인 섹션 제목인지 체크
          if (_isMainSectionTitle(cleanedLine)) {
            print('🔍 메인 제목으로 처리: $cleanedLine');
            widgets.add(Padding(
              padding: EdgeInsets.only(bottom: 12, top: widgets.isEmpty ? 0 : 24),
              child: _buildAnalysisTitle(context, cleanedLine),
            ));
          } else {
            print('🔍 서브 제목으로 처리: $cleanedLine');
            widgets.add(_buildRichTextLine(context, cleanedLine, TextType.subTitle));
          }
          continue;
        }
      }
      
      // 실천 방법 관련 키워드가 나오면 중단 (### 제외)
      if (line.contains('🎯') || line.contains('💪') || line.contains('🏥') ||
          line.contains('가로 황금비율 개선') || line.contains('턱선 개선')) {
        print('🔍 실천 방법 키워드 발견, 중단: $line');
        reachedEnd = true;
        break;
      }
      
      if (reachedEnd) break;
      // 주요 섹션 제목 인식 (더 엄격하고 안전한 패턴)
      else if (_isMainSectionTitle(line)) {
        print('🔍 메인 제목 섹션 추가: $line');
        widgets.add(Padding(
          padding: EdgeInsets.only(bottom: 12, top: widgets.isEmpty ? 0 : 24),
          child: _buildAnalysisTitle(context, line),
        ));
      }
      // **볼드** 텍스트는 소제목
      else if (line.contains('**')) {
        print('🔍 볼드 소제목 추가: $line');
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6, top: 8),
          child: _buildAnalysisSubtitle(context, line),
        ));
      }
      // 일반 본문
      else {
        print('🔍 일반 본문 추가: $line');
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: _buildAnalysisBody(context, line),
        ));
      }
    }
    
    print('🔍 최종 위젯 개수: ${widgets.length}');
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  Widget _buildAnalysisTitle(BuildContext context, String text) {
    // **볼드** 제거
    text = text.replaceAll('**', '');
    
    // 번호 섹션(1., 2., 3.)은 녹색+볼드 제목 스타일
    return Text(
      text,
      style: Theme.of(context).textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.bold,
        color: Colors.green.shade700,  // 녹색+볼드
        height: 1.4,
        fontSize: 16,
      ),
    );
  }

  Widget _buildAnalysisSubtitle(BuildContext context, String text) {
    text = text.replaceAll('**', '');
    
    // **볼드** 소제목은 검은색+볼드 제거
    return Padding(
      padding: const EdgeInsets.only(left: 16),  // 들여쓰기
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.normal,  // 볼드 제거
          color: Colors.grey.shade800,    // 검은색
          height: 1.4,
        ),
      ),
    );
  }

  Widget _buildAnalysisBody(BuildContext context, String text) {
    // 케어 팁과 동일한 검은색 본문 스타일 (볼드 제거)
    return Padding(
      padding: const EdgeInsets.only(left: 16),  // 케어 팁과 동일한 들여쓰기
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          height: 1.6,
          color: Colors.grey.shade800,
          fontSize: 15,
          fontWeight: FontWeight.normal,  // 볼드 제거
        ),
      ),
    );
  }

  /// 메인 섹션 제목 여부를 엄격하게 판단하는 헬퍼 함수
  bool _isMainSectionTitle(String line) {
    // 1. 숫자로 시작하는 패턴 (1., 2., 3.)은 메인 제목에서만 허용
    if (RegExp(r'^\d+\.').hasMatch(line)) {
      // "개선이 필요한 부분" 아래의 세부 항목들은 메인 제목이 아님
      if (line.contains('-') || line.contains('개선') || line.contains('조정') || 
          line.contains('보완') || line.contains('관리') || line.contains('운동') ||
          line.contains('마사지') || line.contains('케어') || line.contains('시술') ||
          line.contains('치료') || line.contains('교정') || line.contains('수술')) {
        return false;
      }
      // 숫자로만 시작하고 위 키워드가 없으면 메인 제목으로 처리
      return true;
    }
    
    // 2. 특정 이모지를 포함하는 완전한 제목 패턴만 인식
    final mainTitlePatterns = [
      '🌟', '내 얼굴의 좋은 점', '좋은 점',
      '📊', '개선이 필요한 부분', '개선이 필요', 
      '💡', '개선 후 기대효과', '기대효과'
    ];
    
    // 3. 라인이 특정 패턴을 포함하고, 다른 내용(점수, 비율 등)을 포함하지 않는 경우만 제목으로 인식
    for (final pattern in mainTitlePatterns) {
      if (line.contains(pattern)) {
        // 제목에 점수나 비율이 포함되어 있으면 제목이 아님
        if (line.contains('점') || line.contains('%') || line.contains('°')) {
          continue;
        }
        // 제목에 ':' 이나 '-' 가 많이 포함되어 있으면 본문일 가능성 높음
        if (line.split(':').length > 2 || line.split('-').length > 3) {
          continue;
        }
        return true;
      }
    }
    
    return false;
  }

  // =============================================================================
  // 새로운 인터랙티브 UI 컴포넌트들
  // =============================================================================

  /// 메인 분석 차트 (레이더 차트 스타일)
  Widget _buildAnalysisChart(BuildContext context, Map<String, dynamic> analysis) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: Container(
        height: 200,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.indigo.shade50, Colors.purple.shade50],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.purple.shade200),
        ),
        child: CustomPaint(
          size: Size.infinite,
          painter: _RadarChartPainter(analysis),
        ),
      ),
    );
  }

  /// 상세 메트릭 차트
  Widget _buildDetailedMetrics(BuildContext context, Map<String, dynamic> analysis) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
              ),
            ),
            child: Row(
              children: [
                Icon(Icons.analytics, color: Colors.purple.shade600, size: 20),
                const SizedBox(width: 8),
                Text(
                  '정량적 측정 데이터',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.purple.shade700,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                _buildMetricChart(
                  context,
                  '🎭 가로 황금비율',
                  analysis['verticalScore']?['percentages']?.cast<double>() ?? [20.0, 20.0, 20.0, 20.0, 20.0],
                  ['왼쪽바깥', '왼쪽눈', '미간', '오른쪽눈', '오른쪽바깥'],
                  List.filled(5, 20.0), // 평균값
                  analysis['verticalScore']?['score']?.toDouble() ?? 75.0,
                ),
                const SizedBox(height: 24),
                _buildMetricChart(
                  context,
                  '⚖️ 세로 대칭성',
                  [
                    analysis['horizontalScore']?['upperPercentage']?.toDouble() ?? 50.0,
                    analysis['horizontalScore']?['lowerPercentage']?.toDouble() ?? 50.0,
                  ],
                  ['눈~코', '코~턱'],
                  [50.0, 50.0], // 평균값
                  analysis['horizontalScore']?['score']?.toDouble() ?? 75.0,
                ),
                const SizedBox(height: 24),
                _buildMetricChart(
                  context,
                  '🎭 하관 조화도',
                  [
                    analysis['lowerFaceScore']?['upperPercentage']?.toDouble() ?? 33.0,
                    analysis['lowerFaceScore']?['lowerPercentage']?.toDouble() ?? 67.0,
                  ],
                  ['인중', '입~턱'],
                  [33.0, 67.0], // 평균값
                  analysis['lowerFaceScore']?['score']?.toDouble() ?? 75.0,
                ),
                const SizedBox(height: 24),
                _buildJawAngleAnalysis(context, analysis),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 개별 메트릭 차트 위젯
  Widget _buildMetricChart(
    BuildContext context, 
    String title, 
    List<double> actualValues, 
    List<String> labels,
    List<double> idealValues,
    double score,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.grey.shade50, Colors.white],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey.shade800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _getMetricDescription(title),
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                        height: 1.3,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getScoreColor(score).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${score.round()}점',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: _getScoreColor(score),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 200,
            child: _buildFlChart(actualValues, idealValues, labels),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildLegendItem('이상값', Colors.grey.shade400),
              _buildLegendItem('실제값', Colors.indigo.shade400),
            ],
          ),
          const SizedBox(height: 12),
          _buildMetricDetailAnalysis(title, actualValues, labels, idealValues),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }

  /// 인터랙티브 카테고리 그리드
  Widget _buildInteractiveCategories(BuildContext context, Map<String, dynamic> analysis) {
    final categories = [
      {
        'id': 'vertical',
        'title': '가로 황금비율',
        'subtitle': '5구간 균등 분석',
        'score': analysis['verticalScore']?['score']?.toDouble() ?? 75.0,
        'color': Colors.indigo,
        'gradient': [Colors.indigo.shade400, Colors.purple.shade300],
      },
      {
        'id': 'horizontal',
        'title': '세로 대칭성',
        'subtitle': '상하 균형 분석',
        'score': analysis['horizontalScore']?['score']?.toDouble() ?? 75.0,
        'color': Colors.teal,
        'gradient': [Colors.teal.shade400, Colors.green.shade300],
      },
      {
        'id': 'lowerface',
        'title': '하관 조화',
        'subtitle': '인중-턱 비율 분석',
        'score': analysis['lowerFaceScore']?['score']?.toDouble() ?? 75.0,
        'color': Colors.amber,
        'gradient': [Colors.amber.shade400, Colors.orange.shade300],
      },
      {
        'id': 'jawline',
        'title': '턱 곡률',
        'subtitle': '턱선 각도 분석',
        'score': analysis['jawline']?['score']?.toDouble() ?? 75.0,
        'color': Colors.pink,
        'gradient': [Colors.pink.shade400, Colors.red.shade300],
      },
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        // 화면 크기에 따라 동적으로 childAspectRatio 조정
        double aspectRatio;
        if (constraints.maxWidth > 600) {
          // 넓은 화면: 카드 높이를 더 낮게 (aspectRatio 더 증가)
          aspectRatio = 2.8; // 2.3에서 2.8로 증가
        } else {
          // 좁은 화면: 높이를 적당히 줄임
          aspectRatio = 2.2; // 2.8에서 2.2로 감소 (너무 높지 않게)
        }
        
        return GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(), // 스크롤 비활성화
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 8,
              mainAxisSpacing: 8,
              childAspectRatio: aspectRatio,
            ),
            itemCount: categories.length,
            itemBuilder: (context, index) {
        final category = categories[index];
        final isSelected = _selectedCategory == category['id'];
        final score = category['score'] as double;
        final gradient = category['gradient'] as List<Color>;
        
        return GestureDetector(
          onTap: () {
            setState(() {
              _selectedCategory = isSelected ? null : category['id'] as String;
            });
          },
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: isSelected 
                    ? gradient 
                    : [Colors.white, Colors.grey.shade50],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: isSelected ? gradient[0] : Colors.grey.shade200,
                width: isSelected ? 2 : 1,
              ),
              boxShadow: [
                BoxShadow(
                  color: isSelected 
                      ? gradient[0].withOpacity(0.3) 
                      : Colors.black.withOpacity(0.05),
                  blurRadius: isSelected ? 15 : 5,
                  offset: Offset(0, isSelected ? 8 : 2),
                ),
              ],
            ),
            child: Padding(
              padding: const EdgeInsets.all(4), // 8에서 4로 줄임
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // 점수 원형 프로그레스
                  Stack(
                    alignment: Alignment.center,
                    children: [
                      SizedBox(
                        width: 45, // 60에서 45로 줄임
                        height: 45, // 60에서 45로 줄임
                        child: CircularProgressIndicator(
                          value: score / 100,
                          strokeWidth: 4, // 6에서 4로 줄임
                          backgroundColor: isSelected 
                              ? Colors.white.withOpacity(0.3)
                              : Colors.grey.shade200,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            isSelected ? Colors.white : gradient[0],
                          ),
                        ),
                      ),
                      Text(
                        score.round().toString(),
                        style: TextStyle(
                          fontSize: 14, // 16에서 14로 줄임
                          fontWeight: FontWeight.bold,
                          color: isSelected ? Colors.white : gradient[0],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 3), // 6에서 3으로 줄임
                  Text(
                    category['title'] as String,
                    textAlign: TextAlign.center,
                    maxLines: 1, // 2에서 1로 줄임
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 11, // 13에서 11로 줄임
                      fontWeight: FontWeight.bold,
                      color: isSelected ? Colors.white : Colors.grey.shade800,
                    ),
                  ),
                  const SizedBox(height: 1), // 2에서 1로 줄임
                  Text(
                    category['subtitle'] as String,
                    textAlign: TextAlign.center,
                    maxLines: 1, // 2에서 1로 줄임
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 9, // 11에서 9로 줄임
                      color: isSelected 
                          ? Colors.white.withOpacity(0.9) 
                          : Colors.grey.shade600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
        );
      },
    );
  }

  /// fl_chart를 사용한 아름다운 바 차트
  Widget _buildFlChart(List<double> actualValues, List<double> idealValues, List<String> labels) {
    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: math.max(actualValues.reduce(math.max), idealValues.reduce(math.max)) * 1.2,
        barTouchData: BarTouchData(
          touchTooltipData: BarTouchTooltipData(
            getTooltipColor: (group) => Colors.black87,
            tooltipRoundedRadius: 8,
            getTooltipItem: (group, groupIndex, rod, rodIndex) {
              final isIdeal = rodIndex == 0;
              final value = isIdeal ? idealValues[groupIndex] : actualValues[groupIndex];
              final type = isIdeal ? '이상값' : '실제값';
              return BarTooltipItem(
                '$type\n${value.round()}%',
                const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              );
            },
          ),
        ),
        titlesData: FlTitlesData(
          show: true,
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (double value, TitleMeta meta) {
                if (value.toInt() < labels.length) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      labels[value.toInt()],
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontWeight: FontWeight.w500,
                        fontSize: 10,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  );
                }
                return const Text('');
              },
              reservedSize: 40,
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              interval: 10,
              getTitlesWidget: (double value, TitleMeta meta) {
                return Text(
                  '${value.toInt()}%',
                  style: TextStyle(
                    color: Colors.grey.shade600,
                    fontWeight: FontWeight.w400,
                    fontSize: 10,
                  ),
                );
              },
              reservedSize: 35,
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          horizontalInterval: 10,
          getDrawingHorizontalLine: (value) => FlLine(
            color: Colors.grey.shade300,
            strokeWidth: 0.5,
          ),
        ),
        barGroups: List.generate(
          actualValues.length,
          (index) => BarChartGroupData(
            x: index,
            groupVertically: false,
            barRods: [
              // 이상값 막대 (회색)
              BarChartRodData(
                toY: idealValues[index],
                color: Colors.grey.shade400,
                width: 16,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(6),
                  topRight: Radius.circular(6),
                ),
                backDrawRodData: BackgroundBarChartRodData(
                  show: true,
                  toY: math.max(actualValues.reduce(math.max), idealValues.reduce(math.max)) * 1.2,
                  color: Colors.grey.shade100,
                ),
              ),
              // 실제값 막대 (파란색)
              BarChartRodData(
                toY: actualValues[index],
                color: Colors.indigo.shade400,
                width: 16,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(6),
                  topRight: Radius.circular(6),
                ),
                rodStackItems: [
                  BarChartRodStackItem(0, actualValues[index], Colors.indigo.shade400),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// 각 메트릭의 의미를 설명하는 메서드
  String _getMetricDescription(String title) {
    switch (title) {
      case '🎭 가로 황금비율':
        return '얼굴을 가로로 5등분했을 때의 균형도를 분석합니다. 이상적인 비율은 각 구간이 20%씩 균등한 상태입니다.';
      case '⚖️ 세로 대칭성':
        return '얼굴을 세로로 2등분(눈~코, 코~턱)했을 때의 균형도를 측정합니다. 이상적인 비율은 50:50입니다.';
      case '🎭 하관 조화도':
        return '하관(인중~턱) 영역의 조화를 분석합니다. 인중 33%, 입술~턱 67%가 이상적인 황금비율입니다.';
      default:
        return '얼굴의 전반적인 비율과 균형도를 측정합니다.';
    }
  }

  /// 메트릭별 상세 분석 정보를 제공하는 위젯
  Widget _buildMetricDetailAnalysis(String title, List<double> actualValues, List<String> labels, List<double> idealValues) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue.shade200, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.analytics, size: 16, color: Colors.blue.shade600),
              const SizedBox(width: 6),
              Text(
                '상세 분석',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.blue.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...List.generate(actualValues.length, (index) {
            final actual = actualValues[index];
            final ideal = idealValues[index];
            final label = labels[index];
            final difference = actual - ideal;
            final isGood = difference.abs() <= 2.0; // 2% 이내면 좋은 수치
            
            return Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: Text(
                      label,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade700,
                      ),
                    ),
                  ),
                  Expanded(
                    flex: 2,
                    child: Text(
                      '${actual.round()}%',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: isGood ? Colors.green.shade600 : Colors.orange.shade600,
                      ),
                    ),
                  ),
                  Expanded(
                    flex: 3,
                    child: Text(
                      _getAnalysisText(difference, title, label),
                      style: TextStyle(
                        fontSize: 11,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  /// 분석 결과에 따른 설명 텍스트
  String _getAnalysisText(double difference, String title, String label) {
    if (difference.abs() <= 2.0) {
      return '✅ 이상적';
    } else if (difference > 0) {
      return '📈 ${difference.round()}% 높음';
    } else {
      return '📉 ${difference.abs().round()}% 낮음';
    }
  }

  /// 턱 각도 분석 위젯 (각도 정보 포함)
  Widget _buildJawAngleAnalysis(BuildContext context, Map<String, dynamic> analysis) {
    // 디버깅: jawScore 데이터 구조 확인
    // print('🔍 jawScore 데이터 구조: ${analysis['jawScore']}');
    
    final jawScore = analysis['jawScore']?['score']?.toDouble() ?? 75.0;
    final gonialAngle = analysis['jawScore']?['gonialAngle']?.toDouble();
    final cervicoMentalAngle = analysis['jawScore']?['cervicoMentalAngle']?.toDouble();
    
    // 디버깅: 추출된 값들 확인
    // print('🔍 턱 곡률 값들: jawScore=$jawScore, gonialAngle=$gonialAngle, cervicoMentalAngle=$cervicoMentalAngle');
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.grey.shade50, Colors.white],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '📐 턱 곡률 분석',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey.shade800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '하악각과 턱목각을 측정하여 얼굴 라인의 리프팅 효과와 곡률을 분석합니다.',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                        height: 1.3,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getScoreColor(jawScore).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${jawScore.round()}점',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: _getScoreColor(jawScore),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          if (gonialAngle != null && cervicoMentalAngle != null) ...[
            Row(
              children: [
                Expanded(
                  child: _buildAngleCard(
                    '하악각 (Gonial Angle)',
                    gonialAngle,
                    90.0, 
                    120.0,
                    '턱선의 각진 정도를 나타냅니다.\n90-120°가 이상적 범위입니다.',
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildAngleCard(
                    '턱목각 (Cervico-Mental)',
                    cervicoMentalAngle,
                    105.0,
                    115.0,
                    '턱과 목의 경계선 각도입니다.\n105-115°가 이상적 범위입니다.',
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.amber.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.amber.shade200, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.lightbulb_outline, size: 16, color: Colors.amber.shade600),
                      const SizedBox(width: 6),
                      Text(
                        '턱 곡률 해석',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.amber.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _getJawAnalysisText(gonialAngle, cervicoMentalAngle),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade700,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
          ] else ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                '턱 각도 측정 데이터를 불러오는 중입니다...',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// 각도 카드 위젯
  Widget _buildAngleCard(String title, double angle, double minIdeal, double maxIdeal, String description) {
    final isIdeal = angle >= minIdeal && angle <= maxIdeal;
    final color = isIdeal ? Colors.green : Colors.orange;
    
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.shade200, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: color.shade700,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                '${angle.round()}°',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: color.shade800,
                ),
              ),
              const SizedBox(width: 8),
              Icon(
                isIdeal ? Icons.check_circle : Icons.info,
                size: 16,
                color: color.shade600,
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            description,
            style: TextStyle(
              fontSize: 10,
              color: Colors.grey.shade600,
              height: 1.3,
            ),
          ),
        ],
      ),
    );
  }

  /// 턱 분석 텍스트 생성
  String _getJawAnalysisText(double gonialAngle, double cervicoMentalAngle) {
    String gonialText = '';
    String cervicoText = '';
    
    if (gonialAngle <= 90) {
      gonialText = '매우 각진 턱선으로 강인한 인상을 줍니다.';
    } else if (gonialAngle <= 120) {
      gonialText = '이상적인 턱선 각도로 균형잡힌 얼굴형입니다.';
    } else if (gonialAngle <= 140) {
      gonialText = '부드러운 턱선으로 온화한 인상을 줍니다.';
    } else {
      gonialText = '매우 둥근 턱선으로 부드러운 인상이 강합니다.';
    }
    
    if (cervicoMentalAngle >= 105 && cervicoMentalAngle <= 115) {
      cervicoText = '턱과 목의 경계가 뚜렷하여 리프팅 효과가 뛰어납니다.';
    } else if (cervicoMentalAngle < 105) {
      cervicoText = '턱목 각도가 예각으로 갸름한 얼굴형 특징을 보입니다.';
    } else {
      cervicoText = '턱목 경계가 부드러워 자연스러운 곡선을 형성합니다.';
    }
    
    return '$gonialText $cervicoText';
  }

  Color _getScoreColor(double score) {
    if (score >= 85) return Colors.green;
    if (score >= 70) return Colors.orange;
    return Colors.red;
  }
}

/// 레이더 차트 페인터
class _RadarChartPainter extends CustomPainter {
  final Map<String, dynamic> analysis;

  _RadarChartPainter(this.analysis);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 3;

    // 배경 격자
    _drawGrid(canvas, center, radius);
    
    // 데이터 차트
    _drawDataChart(canvas, center, radius);
    
    // 라벨
    _drawLabels(canvas, center, radius);
  }

  void _drawGrid(Canvas canvas, Offset center, double radius) {
    final paint = Paint()
      ..color = Colors.purple.withOpacity(0.1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // 동심원 그리기
    for (int i = 1; i <= 5; i++) {
      canvas.drawCircle(center, radius * i / 5, paint);
    }

    // 방사선 그리기
    const angles = [0, math.pi / 2, math.pi, 3 * math.pi / 2];
    for (final angle in angles) {
      final endPoint = Offset(
        center.dx + math.cos(angle) * radius,
        center.dy + math.sin(angle) * radius,
      );
      canvas.drawLine(center, endPoint, paint);
    }
  }

  void _drawDataChart(Canvas canvas, Offset center, double radius) {
    final scores = [
      analysis['verticalScore']?['score']?.toDouble() ?? 75.0,
      analysis['horizontalScore']?['score']?.toDouble() ?? 75.0,
      analysis['lowerFaceScore']?['score']?.toDouble() ?? 75.0,
      analysis['jawline']?['score']?.toDouble() ?? 75.0,
    ];

    final path = Path();
    const angles = [0, math.pi / 2, math.pi, 3 * math.pi / 2];

    for (int i = 0; i < scores.length; i++) {
      final score = scores[i];
      final angle = angles[i] - math.pi / 2; // 12시 방향부터 시작
      final distance = radius * (score / 100);
      final point = Offset(
        center.dx + math.cos(angle) * distance,
        center.dy + math.sin(angle) * distance,
      );

      if (i == 0) {
        path.moveTo(point.dx, point.dy);
      } else {
        path.lineTo(point.dx, point.dy);
      }
    }
    path.close();

    // 채우기
    final fillPaint = Paint()
      ..color = Colors.purple.withOpacity(0.3)
      ..style = PaintingStyle.fill;
    canvas.drawPath(path, fillPaint);

    // 테두리
    final strokePaint = Paint()
      ..color = Colors.purple.shade400
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawPath(path, strokePaint);

    // 점 그리기
    for (int i = 0; i < scores.length; i++) {
      final score = scores[i];
      final angle = angles[i] - math.pi / 2;
      final distance = radius * (score / 100);
      final point = Offset(
        center.dx + math.cos(angle) * distance,
        center.dy + math.sin(angle) * distance,
      );

      final pointPaint = Paint()
        ..color = Colors.purple.shade600
        ..style = PaintingStyle.fill;
      canvas.drawCircle(point, 4, pointPaint);
    }
  }

  void _drawLabels(Canvas canvas, Offset center, double radius) {
    final labels = ['가로 황금비율', '세로 대칭성', '하관 조화', '턱 곡률'];
    const angles = [0, math.pi / 2, math.pi, 3 * math.pi / 2];

    for (int i = 0; i < labels.length; i++) {
      final angle = angles[i] - math.pi / 2;
      final labelRadius = radius + 20;
      final point = Offset(
        center.dx + math.cos(angle) * labelRadius,
        center.dy + math.sin(angle) * labelRadius,
      );

      final textPainter = TextPainter(
        text: TextSpan(
          text: labels[i],
          style: TextStyle(
            color: Colors.purple.shade700,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
        textDirection: TextDirection.ltr,
      );

      textPainter.layout();
      
      // 라벨별 위치 조정
      double offsetX = point.dx - textPainter.width / 2;
      double offsetY = point.dy - textPainter.height / 2;
      
      if (labels[i] == '세로 대칭성') {
        // 세로 대칭성을 더 오른쪽으로 이동
        offsetX += 25;
      } else if (labels[i] == '턱 곡률') {
        // 턱 곡률을 왼쪽으로 이동
        offsetX -= 15;
      }
      
      textPainter.paint(
        canvas,
        Offset(offsetX, offsetY),
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

/// 메트릭 차트 페인터 (막대 그래프)
class _MetricChartPainter extends CustomPainter {
  final List<double> actualValues;
  final List<double> idealValues;
  final List<String> labels;

  _MetricChartPainter({
    required this.actualValues,
    required this.idealValues,
    required this.labels,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (actualValues.isEmpty || labels.isEmpty) return;

    final barWidth = size.width / (actualValues.length * 2.5);
    final maxValue = math.max(
      actualValues.reduce(math.max),
      idealValues.reduce(math.max),
    );
    final chartHeight = size.height - 60; // 여백을 위한 공간
    
    // 배경 그리드 그리기
    _drawGrid(canvas, size, chartHeight, maxValue);
    
    // 막대 그래프 그리기
    for (int i = 0; i < actualValues.length; i++) {
      final centerX = (i + 0.5) * (size.width / actualValues.length);
      
      // 이상값 막대 (회색)
      final idealHeight = (idealValues[i] / maxValue) * chartHeight;
      final idealBarRect = Rect.fromLTWH(
        centerX - barWidth,
        chartHeight - idealHeight + 20,
        barWidth * 0.8,
        idealHeight,
      );
      
      final idealPaint = Paint()
        ..color = Colors.grey.shade400
        ..style = PaintingStyle.fill;
      canvas.drawRRect(
        RRect.fromRectAndRadius(idealBarRect, const Radius.circular(4)),
        idealPaint,
      );
      
      // 실제값 막대 (파란색)
      final actualHeight = (actualValues[i] / maxValue) * chartHeight;
      final actualBarRect = Rect.fromLTWH(
        centerX - barWidth * 0.2,
        chartHeight - actualHeight + 20,
        barWidth * 0.8,
        actualHeight,
      );
      
      final actualPaint = Paint()
        ..color = Colors.indigo.shade400
        ..style = PaintingStyle.fill;
      canvas.drawRRect(
        RRect.fromRectAndRadius(actualBarRect, const Radius.circular(4)),
        actualPaint,
      );
      
      // 값 텍스트 표시 (막대 내부에 표시)
      if (actualHeight > 25) { // 막대가 충분히 클 때만 내부에 표시
        _drawValueText(
          canvas,
          '${actualValues[i].round()}%',
          Offset(centerX, chartHeight - actualHeight / 2 + 20),
          Colors.white,
        );
      } else { // 막대가 낮으면 위에 표시
        _drawValueText(
          canvas,
          '${actualValues[i].round()}%',
          Offset(centerX, chartHeight - actualHeight + 5),
          Colors.indigo.shade700,
        );
      }
      
      // 라벨 텍스트
      _drawLabelText(
        canvas,
        labels[i],
        Offset(centerX, chartHeight + 35),
      );
      
      // 차이값 표시 (실제값 - 이상값)
      final diff = actualValues[i] - idealValues[i];
      final diffColor = diff > 0 ? Colors.red.shade600 : Colors.green.shade600;
      final diffText = '${diff > 0 ? '+' : ''}${diff.round()}%';
      
      _drawValueText(
        canvas,
        diffText,
        Offset(centerX, 5),
        diffColor,
      );
    }
  }

  void _drawGrid(Canvas canvas, Size size, double chartHeight, double maxValue) {
    final gridPaint = Paint()
      ..color = Colors.grey.shade300
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.5;

    // 수평 그리드 라인 (5개)
    for (int i = 0; i <= 4; i++) {
      final y = chartHeight * i / 4 + 20;
      canvas.drawLine(
        Offset(0, y),
        Offset(size.width, y),
        gridPaint,
      );
      
      // Y축 값 텍스트
      final value = maxValue * (4 - i) / 4;
      _drawValueText(
        canvas,
        '${value.round()}%',
        Offset(-10, y),
        Colors.grey.shade600,
      );
    }
  }

  void _drawValueText(Canvas canvas, String text, Offset position, Color color) {
    final textPainter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w600,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();
    textPainter.paint(
      canvas,
      Offset(
        position.dx - textPainter.width / 2,
        position.dy - textPainter.height / 2,
      ),
    );
  }

  void _drawLabelText(Canvas canvas, String text, Offset position) {
    final textPainter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: Colors.grey.shade700,
          fontSize: 11,
          fontWeight: FontWeight.w500,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();
    textPainter.paint(
      canvas,
      Offset(
        position.dx - textPainter.width / 2,
        position.dy - textPainter.height / 2,
      ),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

extension on _BeautyScoreDashboardState {
  /// GPT 기초 뷰티스코어 분석 결과 위젯
  Widget _buildGptAnalysisWidget(BuildContext context, Map<String, dynamic> analysis) {
    final gptAnalysis = analysis['gptAnalysis'] as Map<String, dynamic>?;
    final hasComparison = analysis.containsKey('comparison');
    
    // 디버깅: 전체 analysis 구조 확인
    print('🔍 Frontend analysis keys: ${analysis.keys.toList()}');
    print('🔍 Frontend gptAnalysis: ${gptAnalysis != null ? gptAnalysis.keys.toList() : 'null'}');
    
    // 재진단 비교가 있으면 GPT 기초 분석 대신 비교 결과만 표시
    if (hasComparison) {
      return const SizedBox.shrink();
    }
    
    // GPT 분석이 없으면 표시하지 않음
    if (gptAnalysis == null) {
      print('🔍 Frontend: GPT 분석이 null이므로 표시하지 않음');
      return const SizedBox.shrink();
    }

    return Consumer<AppState>(
      builder: (context, appState, child) {
        print('🔍 GPT 위젯 렌더링 - isGptAnalyzing: ${appState.isGptAnalyzing}');
        print('🔍 GPT 위젯 렌더링 - gptAnalysis keys: ${gptAnalysis?.keys.toList()}');
        
        // GPT 분석 중일 때 로딩 표시
        if (appState.isGptAnalyzing) {
          return Container(
            margin: const EdgeInsets.only(bottom: 20),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Colors.indigo.shade50,
                  Colors.purple.shade50,
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.indigo.shade100),
            ),
            child: Row(
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.indigo.shade600),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    '🤖 AI 전문가가 맞춤형 뷰티 분석을 진행 중입니다...',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.indigo.shade700,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          );
        }

        print('🔍 GPT 위젯 실제 렌더링 시작');
        print('🔍 analysisText 존재: ${gptAnalysis['analysisText'] != null}');
        print('🔍 analysisText 길이: ${(gptAnalysis['analysisText'] as String?)?.length ?? 0}');

        return Column(
          children: [
            // 종합 뷰티 점수 카드
            _buildOverallScoreCard(context, analysis),
            const SizedBox(height: 20),
            
            // AI 전문가 분석 - 항상 표시
            Container(
              margin: const EdgeInsets.only(bottom: 20),
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Colors.indigo.shade50,
                    Colors.purple.shade50,
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.indigo.shade100),
                boxShadow: [
                  BoxShadow(
                    color: Colors.indigo.shade100.withOpacity(0.3),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 헤더 - 항상 표시
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Colors.indigo.shade400, Colors.purple.shade500],
                          ),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(
                          Icons.psychology,
                          color: Colors.white,
                          size: 20,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          '🤖 AI 전문가 맞춤 분석',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.indigo.shade700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // GPT 분석 텍스트 또는 기본 메시지
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.indigo.shade100),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.grey.shade100,
                          blurRadius: 5,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: (gptAnalysis['analysisText'] != null && 
                           (gptAnalysis['analysisText'] as String).isNotEmpty)
                        ? _buildRichAnalysisText(context, gptAnalysis['analysisText'] as String)
                        : Text(
                            'AI 분석을 준비 중입니다...',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.grey.shade600,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }


  // 🎯 새로운 UI/UX 개선 컴포넌트들

  /// 1단계: 개인화된 환영 메시지 - 감정적 연결
  Widget _buildPersonalizedWelcome(BuildContext context, Map<String, dynamic> analysis) {
    final score = analysis['overallScore']?.toDouble() ?? 75.0;
    final gptAnalysis = analysis['gptAnalysis'] as Map<String, dynamic>?;
    
    // 점수에 따른 개인화된 메시지
    String welcomeMessage;
    String motivationalText;
    IconData welcomeIcon;
    List<Color> gradientColors;
    
    if (score >= 85) {
      welcomeMessage = "✨ 놀라운 결과예요!";
      motivationalText = "당신은 이미 완벽에 가까운 조화로운 아름다움을 가지고 계시네요";
      welcomeIcon = Icons.auto_awesome;
      gradientColors = [Colors.amber.shade100, Colors.orange.shade100];
    } else if (score >= 75) {
      welcomeMessage = "🌟 멋진 분석 결과!";
      motivationalText = "균형잡힌 아름다운 특징들이 돋보이는 결과입니다";
      welcomeIcon = Icons.favorite;
      gradientColors = [Colors.pink.shade100, Colors.purple.shade100];
    } else if (score >= 65) {
      welcomeMessage = "💫 좋은 기본기!";
      motivationalText = "고유한 매력을 가진 특별한 아름다움을 발견했어요";
      welcomeIcon = Icons.star;
      gradientColors = [Colors.blue.shade100, Colors.indigo.shade100];
    } else {
      welcomeMessage = "🎯 성장 가능성!";
      motivationalText = "모든 사람은 고유한 아름다움을 가지고 있어요. 함께 발견해볼까요?";
      welcomeIcon = Icons.trending_up;
      gradientColors = [Colors.green.shade100, Colors.teal.shade100];
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: gradientColors,
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: gradientColors[0].withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.9),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(
              welcomeIcon,
              size: 28,
              color: gradientColors[1].withOpacity(0.8),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  welcomeMessage,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Colors.grey.shade800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  motivationalText,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey.shade700,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 2단계: 스토리텔링 방식의 종합 점수 카드
  Widget _buildStorytellingScoreCard(BuildContext context, Map<String, dynamic> analysis) {
    final score = analysis['overallScore']?.toDouble() ?? 75.0;
    
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.white,
            Colors.purple.shade50.withOpacity(0.3),
          ],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.purple.shade100, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.purple.shade100.withOpacity(0.5),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        children: [
          // 헤더 섹션
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.purple.shade600, Colors.indigo.shade600],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(24),
                topRight: Radius.circular(24),
              ),
            ),
            child: Column(
              children: [
                Text(
                  '🎯 종합 뷰티 분석',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'AI 기반 전문 얼굴 분석 결과',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.white.withOpacity(0.9),
                  ),
                ),
              ],
            ),
          ),
          
          // 점수 섹션
          Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              children: [
                // 중앙 원형 점수 표시
                Stack(
                  alignment: Alignment.center,
                  children: [
                    SizedBox(
                      width: 150,
                      height: 150,
                      child: CircularProgressIndicator(
                        value: score / 100,
                        strokeWidth: 8,
                        backgroundColor: Colors.grey.shade200,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          _getScoreColor(score),
                        ),
                      ),
                    ),
                    Column(
                      children: [
                        Text(
                          '${score.round()}',
                          style: Theme.of(context).textTheme.displayLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: _getScoreColor(score),
                          ),
                        ),
                        Text(
                          '점',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: _getScoreColor(score),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                
                const SizedBox(height: 24),
                
                // 점수 설명
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  decoration: BoxDecoration(
                    color: _getScoreColor(score).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: _getScoreColor(score).withOpacity(0.3),
                    ),
                  ),
                  child: Text(
                    _getDetailedScoreDescription(score),
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: _getScoreColor(score).withOpacity(0.8),
                      fontWeight: FontWeight.w600,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 5단계: 인터랙티브 세부 분석 (Expandable)
  Widget _buildInteractiveDetailedAnalysis(BuildContext context, Map<String, dynamic> analysis) {
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.grey.shade200),
          boxShadow: [
            BoxShadow(
              color: Colors.grey.shade100,
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          title: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.indigo.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  Icons.analytics,
                  color: Colors.indigo.shade600,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '📊 세부 분석 보기',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          subtitle: Text(
            '각 항목별 상세 점수와 분석 결과를 확인하세요',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.grey.shade600,
            ),
          ),
          children: [
            Padding(
              padding: const EdgeInsets.all(20),
              child: _buildDetailedAnalysis(context, analysis),
            ),
          ],
        ),
      ),
    );
  }

  /// 6단계: 실천 가능한 케어 팁 (세부 분석 다음에 위치)
  Widget _buildActionableCareTips(BuildContext context, Map<String, dynamic> analysis) {
    final gptAnalysis = analysis['gptAnalysis'] as Map<String, dynamic>?;
    final recommendations = gptAnalysis?['recommendations'] as List<String>? ?? [];
    
    // GPT 추천사항이 없으면 표시하지 않음
    if (recommendations.isEmpty) {
      return const SizedBox.shrink();
    }
    
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.green.shade50, Colors.teal.shade50],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.green.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.green.shade100.withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 헤더
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Colors.green.shade600, Colors.teal.shade600],
                  ),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(
                  Icons.spa,
                  color: Colors.white,
                  size: 22,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '🌿 실천 가능한 케어 팁',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Colors.green.shade700,
                      ),
                    ),
                    Text(
                      'AI가 추천하는 일상 뷰티 관리법',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.green.shade600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 18),
          
          // 케어 팁 목록
          ...recommendations.asMap().entries.map((entry) {
            final index = entry.key;
            final tip = entry.value;
            
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.green.shade100),
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.shade100,
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 케어 팁 텍스트 (리치 텍스트 적용, 번호 제거)
                  _buildRichCareTipText(context, tip),
                ],
              ),
            );
          }),
          
          // 푸터 메시지
          Container(
            margin: const EdgeInsets.only(top: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.shade100.withOpacity(0.5),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.favorite,
                  color: Colors.green.shade600,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '꾸준한 관리가 자연스러운 아름다움의 비결이에요',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.green.shade700,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 재분석 실천 가능한 케어 팁 (세부 분석 바로 아래)
  Widget _buildReAnalysisCareTips(BuildContext context, Map<String, dynamic> analysis) {
    final comparison = analysis['comparison'] as Map<String, dynamic>?;
    final recommendations = comparison?['recommendations'] as List<String>? ?? [];
    
    // 재분석 추천사항이 없거나 재분석이 아니면 표시하지 않음
    if (recommendations.isEmpty || comparison?['isReAnalysis'] != true) {
      return const SizedBox.shrink();
    }
    
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.green.shade50, Colors.blue.shade50],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.green.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.shade100,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 헤더
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.green.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  Icons.lightbulb,
                  color: Colors.green.shade700,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '💡 맞춤형 케어 팁',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Colors.green.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          // 케어 팁 내용
          _buildRichCareTipText(context, recommendations[0]),
          
          // 푸터 메시지
          Container(
            margin: const EdgeInsets.only(top: 16),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.shade100.withOpacity(0.5),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.psychology,
                  color: Colors.green.shade600,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '변화된 결과를 바탕으로 한 맞춤형 관리법이에요',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.green.shade700,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 7단계: 진행 상황 추적
  Widget _buildProgressTracking(BuildContext context, Map<String, dynamic> analysis) {
    final timestamp = analysis['analysisTimestamp'] as String?;
    final hasComparison = analysis.containsKey('comparison');
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.timeline,
                color: Colors.grey.shade600,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                '📈 분석 히스토리',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: Colors.grey.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Icon(
                Icons.access_time,
                size: 16,
                color: Colors.grey.shade500,
              ),
              const SizedBox(width: 8),
              Text(
                timestamp != null 
                    ? '분석 완료: ${_formatTimestamp(timestamp)}'
                    : '최초 분석 완료',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey.shade600,
                ),
              ),
            ],
          ),
          if (hasComparison) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(
                  Icons.compare_arrows,
                  size: 16,
                  color: Colors.green.shade600,
                ),
                const SizedBox(width: 8),
                Text(
                  '재진단 비교 분석 완료',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.green.shade600,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  // 헬퍼 함수들
  Color _getScoreColor(double score) {
    if (score >= 85) return Colors.amber.shade600;
    if (score >= 75) return Colors.green.shade600;
    if (score >= 65) return Colors.blue.shade600;
    return Colors.orange.shade600;
  }

  String _getDetailedScoreDescription(double score) {
    if (score >= 85) {
      return "뛰어난 얼굴 조화도를 보여주는 결과입니다\n자연스럽고 균형잡힌 아름다움이 돋보여요";
    } else if (score >= 75) {
      return "매우 좋은 얼굴 균형을 가지고 계시네요\n조화로운 비율이 인상적입니다";
    } else if (score >= 65) {
      return "좋은 기본기를 가진 매력적인 얼굴입니다\n고유한 특색이 있는 아름다움이에요";
    } else {
      return "모든 사람은 고유한 아름다움을 가지고 있어요\n당신만의 특별한 매력을 발견해보세요";
    }
  }

  String _formatTimestamp(String timestamp) {
    try {
      final dateTime = DateTime.parse(timestamp);
      final now = DateTime.now();
      final difference = now.difference(dateTime);
      
      if (difference.inMinutes < 1) {
        return '방금 전';
      } else if (difference.inHours < 1) {
        return '${difference.inMinutes}분 전';
      } else if (difference.inDays < 1) {
        return '${difference.inHours}시간 전';
      } else {
        return '${difference.inDays}일 전';
      }
    } catch (e) {
      return '방금 전';
    }
  }
}