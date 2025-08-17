import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/app_state.dart';
import 'beauty_comparison_widget.dart';
import 'dart:math' as math;

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
        // 종합 점수 카드
        _buildOverallScoreCard(context, analysis),
        const SizedBox(height: 20),
        
        // 세부 분석 그리드
        _buildDetailedAnalysis(context, analysis),
        const SizedBox(height: 20),
        
        // 뷰티 점수 비교 결과 (재진단 시 표시)
        const BeautyComparisonWidget(),
        
        // 개선 제안
        _buildRecommendations(context, analysis),
        const SizedBox(height: 20),
        
        // 분석 날짜 및 정보
        _buildAnalysisInfo(context, analysis),
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
    final List<String> recommendations = [];
    final overallScore = analysis['overallScore']?.toDouble() ?? 75.0;
    
    // 세로 점수 관련 제안
    final verticalScore = analysis['verticalScore']?['score']?.toDouble() ?? 75.0;
    if (verticalScore < 80) {
      recommendations.add('세로 비율 개선을 위해 하이라이터와 쉐딩으로 얼굴 윤곽을 보정해보세요.');
    }
    
    // 가로 점수 관련 제안
    final horizontalScore = analysis['horizontalScore']?['score']?.toDouble() ?? 75.0;
    if (horizontalScore < 80) {
      recommendations.add('가로 비율 밸런스를 위해 눈썹 모양과 아이라인으로 시선을 조정해보세요.');
    }
    
    // 하관 점수 관련 제안
    final lowerFaceScore = analysis['lowerFaceScore']?['score']?.toDouble() ?? 75.0;
    if (lowerFaceScore < 80) {
      recommendations.add('하관 라인 개선을 위해 립라이너와 턱선 컨투어링을 활용해보세요.');
    }
    
    // 대칭성 관련 제안
    final symmetry = analysis['symmetry']?.toDouble() ?? 75.0;
    if (symmetry < 75) {
      recommendations.add('컨투어링으로 얼굴 대칭감을 보완할 수 있어요.');
    }
    
    // 전체적인 제안
    if (overallScore < 70) {
      recommendations.add('전체적인 얼굴 밸런스 개선을 위한 메이크업 테크닉을 연습해보세요.');
    }
    
    // 일반적인 제안들
    if (recommendations.length < 4) {
      recommendations.addAll([
        '수분 관리로 피부 탄력과 광택을 개선해보세요.',
        '자신의 얼굴형에 맞는 헤어스타일로 전체적인 밸런스를 맞춰보세요.',
        '정기적인 페이셜 마사지로 얼굴 라인을 더욱 선명하게 만들어보세요.',
      ]);
    }
    
    return recommendations.take(4).toList();
  }

  String _formatTimestamp(DateTime timestamp) {
    return '${timestamp.year}.${timestamp.month.toString().padLeft(2, '0')}.${timestamp.day.toString().padLeft(2, '0')} '
           '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}';
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
                  '📐 얼굴 가로 비율',
                  analysis['verticalScore']?['percentages']?.cast<double>() ?? [20.0, 20.0, 20.0, 20.0, 20.0],
                  ['왼쪽바깥', '왼쪽눈', '미간', '오른쪽눈', '오른쪽바깥'],
                  List.filled(5, 20.0), // 평균값
                  analysis['verticalScore']?['score']?.toDouble() ?? 75.0,
                ),
                const SizedBox(height: 24),
                _buildMetricChart(
                  context,
                  '📏 얼굴 세로 밸런스',
                  [
                    analysis['horizontalScore']?['upperPercentage']?.toDouble() ?? 50.0,
                    analysis['horizontalScore']?['lowerPercentage']?.toDouble() ?? 50.0,
                  ],
                  ['눈~코', '인중~턱'],
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
                  ['인중', '입술~턱'],
                  [33.0, 67.0], // 평균값
                  analysis['lowerFaceScore']?['score']?.toDouble() ?? 75.0,
                ),
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
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.grey.shade800,
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
          const SizedBox(height: 16),
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

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.9, // 높이를 더 크게 하여 오버플로우 방지
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
              padding: const EdgeInsets.all(16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // 점수 원형 프로그레스
                  Stack(
                    alignment: Alignment.center,
                    children: [
                      SizedBox(
                        width: 60,
                        height: 60,
                        child: CircularProgressIndicator(
                          value: score / 100,
                          strokeWidth: 6,
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
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: isSelected ? Colors.white : gradient[0],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    category['title'] as String,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: isSelected ? Colors.white : Colors.grey.shade800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    category['subtitle'] as String,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 12,
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
                '$type\n${value.toStringAsFixed(1)}%',
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
      textPainter.paint(
        canvas,
        Offset(
          point.dx - textPainter.width / 2,
          point.dy - textPainter.height / 2,
        ),
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
          '${actualValues[i].toStringAsFixed(1)}%',
          Offset(centerX, chartHeight - actualHeight / 2 + 20),
          Colors.white,
        );
      } else { // 막대가 낮으면 위에 표시
        _drawValueText(
          canvas,
          '${actualValues[i].toStringAsFixed(1)}%',
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
      final diffText = '${diff > 0 ? '+' : ''}${diff.toStringAsFixed(1)}%';
      
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
        '${value.toStringAsFixed(0)}%',
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