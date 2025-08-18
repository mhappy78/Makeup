import '../models/image_models.dart';

/// 뷰티 분석 관련 비즈니스 로직
class BeautyAnalysisService {
  /// 뷰티 스코어를 등급으로 변환
  static String getScoreGrade(double score) {
    if (score >= 90) return 'S';
    if (score >= 80) return 'A';
    if (score >= 70) return 'B';
    if (score >= 60) return 'C';
    if (score >= 50) return 'D';
    return 'F';
  }

  /// 뷰티 스코어 색상 반환
  static String getScoreColor(double score) {
    if (score >= 90) return '#9C27B0'; // Purple
    if (score >= 80) return '#4CAF50'; // Green
    if (score >= 70) return '#FF9800'; // Orange
    if (score >= 60) return '#FFC107'; // Amber
    if (score >= 50) return '#FF5722'; // Deep Orange
    return '#F44336'; // Red
  }

  /// 점수별 메시지 반환
  static String getScoreMessage(double score) {
    if (score >= 90) return '완벽한 비율입니다!';
    if (score >= 80) return '매우 좋은 비율입니다!';
    if (score >= 70) return '좋은 비율입니다!';
    if (score >= 60) return '평균적인 비율입니다.';
    if (score >= 50) return '개선의 여지가 있습니다.';
    return '많은 개선이 필요합니다.';
  }

  /// 개선 제안 생성
  static List<String> generateImprovementSuggestions(Map<String, dynamic> analysis) {
    final suggestions = <String>[];
    
    // 각 항목별 점수 확인하여 개선안 제안
    final overallScore = analysis['overallScore'] ?? 75.0;
    final verticalScore = analysis['verticalScore']?['score'] ?? 75.0;
    final horizontalScore = analysis['horizontalScore']?['score'] ?? 75.0;
    final lowerFaceScore = analysis['lowerFaceScore']?['score'] ?? 75.0;
    final symmetry = analysis['symmetry'] ?? 75.0;

    if (verticalScore < 70) {
      suggestions.add('가로 황금비율 개선을 위해 얼굴 윤곽 관리를 고려해보세요');
    }
    
    if (horizontalScore < 70) {
      suggestions.add('세로 대칭성 개선을 위해 이마-코, 코-턱 비율 조정을 고려해보세요');
    }
    
    if (lowerFaceScore < 70) {
      suggestions.add('하관 조화 개선을 위해 입술-턱 비율 조정을 고려해보세요');
    }
    
    if (symmetry < 70) {
      suggestions.add('얼굴 대칭성 개선을 위해 좌우 균형을 맞춰보세요');
    }

    if (suggestions.isEmpty) {
      suggestions.add('전반적으로 균형잡힌 얼굴형입니다!');
    }

    return suggestions;
  }

  /// 분석 결과 요약 생성
  static Map<String, dynamic> generateAnalysisSummary(Map<String, dynamic> analysis) {
    final overallScore = analysis['overallScore'] ?? 75.0;
    final grade = getScoreGrade(overallScore);
    final message = getScoreMessage(overallScore);
    final suggestions = generateImprovementSuggestions(analysis);

    return {
      'score': overallScore,
      'grade': grade,
      'message': message,
      'suggestions': suggestions,
      'color': getScoreColor(overallScore),
    };
  }

  /// 점수 변화량 계산
  static double calculateScoreChange(double originalScore, double newScore) {
    return newScore - originalScore;
  }

  /// 점수 변화 메시지 생성
  static String getScoreChangeMessage(double change) {
    if (change > 5) return '크게 개선되었습니다!';
    if (change > 2) return '개선되었습니다!';
    if (change > -2) return '거의 변화가 없습니다.';
    if (change > -5) return '약간 감소했습니다.';
    return '많이 감소했습니다.';
  }

  /// 추천 프리셋 제안
  static List<String> getRecommendedPresets(Map<String, dynamic> analysis) {
    final recommendations = <String>[];
    
    final jawScore = analysis['jawScore']?['score'] ?? 75.0;
    final symmetry = analysis['symmetry'] ?? 75.0;
    final lowerFaceScore = analysis['lowerFaceScore']?['score'] ?? 75.0;

    if (jawScore < 70) {
      recommendations.addAll(['lower_jaw', 'middle_jaw']);
    }
    
    if (lowerFaceScore < 70) {
      recommendations.add('cheek');
    }
    
    if (symmetry < 70) {
      recommendations.addAll(['front_protusion', 'back_slit']);
    }

    return recommendations;
  }
}