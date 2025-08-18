<<<<<<< HEAD
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
=======
import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../models/image_models.dart';

/// 뷰티 분석 서비스
class BeautyAnalysisService {
  /// 뷰티 분석 계산
  static Map<String, dynamic> calculateBeautyAnalysis(List<Landmark> landmarks) {
    if (landmarks.isEmpty) return {};
    
    try {
      // 시각화 기반 정밀 점수 계산
      final verticalAnalysis = _calculateVerticalScoreFromVisualization(landmarks);
      final horizontalAnalysis = _calculateHorizontalScoreFromVisualization(landmarks);
      final lowerFaceAnalysis = _calculateLowerFaceScoreFromVisualization(landmarks);
      
      // 기본 분석들
      final facialSymmetry = _calculateFacialSymmetry(landmarks);
      final eyeAnalysis = _calculateEyeAnalysis(landmarks);
      final noseAnalysis = _calculateNoseAnalysis(landmarks);
      final lipAnalysis = _calculateLipAnalysis(landmarks);
      final jawlineAnalysis = _calculateJawlineAnalysis(landmarks);

      // 종합 점수 계산
      final overallScore = _calculateOverallBeautyScoreFromVisualization(
        verticalScore: verticalAnalysis['score'] ?? 75.0,
        horizontalScore: horizontalAnalysis['score'] ?? 75.0,
        lowerFaceScore: lowerFaceAnalysis['score'] ?? 75.0,
        symmetry: facialSymmetry,
        eyeScore: eyeAnalysis['score'] ?? 70.0,
        noseScore: noseAnalysis['score'] ?? 70.0,
        lipScore: lipAnalysis['score'] ?? 70.0,
        jawScore: jawlineAnalysis['score'] ?? 70.0,
      );

      return {
        'overallScore': overallScore,
        'verticalScore': verticalAnalysis,
        'horizontalScore': horizontalAnalysis,
        'lowerFaceScore': lowerFaceAnalysis,
        'symmetry': facialSymmetry,
        'eyeScore': eyeAnalysis,
        'noseScore': noseAnalysis,
        'lipScore': lipAnalysis,
        'jawScore': jawlineAnalysis,
        'analysisTimestamp': DateTime.now().toIso8601String(),
      };
    } catch (e) {
      return {
        'overallScore': 75.0,
        'error': 'Analysis calculation failed: $e',
      };
    }
  }

  /// 세로 점수 계산 (중앙 5개 원 비율 기반)
  static Map<String, dynamic> _calculateVerticalScoreFromVisualization(List<Landmark> landmarks) {
    try {
      final verticalLandmarks = [234, 33, 133, 362, 359, 447];
      if (verticalLandmarks.any((i) => i >= landmarks.length) || 10 >= landmarks.length) {
        return {'score': 75.0};
      }

      final verticalXPositions = verticalLandmarks.map((i) => landmarks[i].x).toList();
      final radiuses = <double>[];
      
      for (int i = 0; i < verticalXPositions.length - 1; i++) {
        radiuses.add((verticalXPositions[i + 1] - verticalXPositions[i]).abs() / 2);
      }

      final totalDiameter = radiuses.reduce((a, b) => a + b) * 2;
      final percentages = radiuses.map((r) => ((r * 2) / totalDiameter) * 100).toList();

      // 황금비율과의 차이 계산 (이상적인 비율 20% 씩)
      const idealRatio = 20.0;
      double totalDeviation = 0.0;
      for (final percentage in percentages) {
        totalDeviation += (percentage - idealRatio).abs();
      }

      final score = (100 - (totalDeviation * 2)).clamp(50.0, 100.0);
      
      return {
        'score': score,
        'percentages': percentages,
        'totalDeviation': totalDeviation,
        'sections': percentages.length,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 가로 점수 계산 (오른쪽 2개 원 비율 기반)
  static Map<String, dynamic> _calculateHorizontalScoreFromVisualization(List<Landmark> landmarks) {
    try {
      final yPositions = [8, 2, 152]
          .where((i) => i < landmarks.length)
          .map((i) => landmarks[i].y)
          .toList();

      if (yPositions.length < 3) {
        return {'score': 75.0};
      }

      final radius1 = (yPositions[1] - yPositions[0]).abs() / 2;
      final radius2 = (yPositions[2] - yPositions[1]).abs() / 2;
      final totalDiameter = (radius1 + radius2) * 2;

      final percentage1 = ((radius1 * 2) / totalDiameter) * 100;
      final percentage2 = ((radius2 * 2) / totalDiameter) * 100;

      // 이상적인 비율은 50:50
      const idealRatio = 50.0;
      final deviation1 = (percentage1 - idealRatio).abs();
      final deviation2 = (percentage2 - idealRatio).abs();
      final totalDeviation = deviation1 + deviation2;

      final score = (100 - (totalDeviation * 1.5)).clamp(50.0, 100.0);

      return {
        'score': score,
        'upperPercentage': percentage1,
        'lowerPercentage': percentage2,
        'deviation': totalDeviation,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 하관 점수 계산
  static Map<String, dynamic> _calculateLowerFaceScoreFromVisualization(List<Landmark> landmarks) {
    try {
      final yPositions = [2, 37, 152]
          .where((i) => i < landmarks.length)
          .map((i) => landmarks[i].y)
          .toList();

      if (yPositions.length < 3) {
        return {'score': 75.0};
      }

      final radius1 = (yPositions[1] - yPositions[0]).abs() / 2;
      final radius2 = (yPositions[2] - yPositions[1]).abs() / 2;
      final totalDiameter = (radius1 + radius2) * 2;

      final percentage1 = ((radius1 * 2) / totalDiameter) * 100;
      final percentage2 = ((radius2 * 2) / totalDiameter) * 100;

      // 황금비율 기준: 상단 33%, 하단 67%가 이상적
      const idealUpper = 33.0;
      const idealLower = 67.0;
      final deviation1 = (percentage1 - idealUpper).abs();
      final deviation2 = (percentage2 - idealLower).abs();
      final totalDeviation = deviation1 + deviation2;

      final score = (100 - (totalDeviation * 1.2)).clamp(50.0, 100.0);

      return {
        'score': score,
        'upperPercentage': percentage1,
        'lowerPercentage': percentage2,
        'deviation': totalDeviation,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 얼굴 대칭성 계산
  static double _calculateFacialSymmetry(List<Landmark> landmarks) {
    if (landmarks.length < 468) return 75.0;

    try {
      final leftEye = landmarks[33];
      final rightEye = landmarks[362];
      final leftMouth = landmarks[61];
      final rightMouth = landmarks[291];
      
      final centerX = (leftEye.x + rightEye.x) / 2;
      final faceWidth = (rightEye.x - leftEye.x).abs();
      
      final eyeSymmetry = 1.0 - ((leftEye.x - centerX).abs() - (centerX - rightEye.x).abs()).abs() / faceWidth;
      final mouthSymmetry = 1.0 - ((leftMouth.x - centerX).abs() - (centerX - rightMouth.x).abs()).abs() / faceWidth;
      
      final symmetryScore = (eyeSymmetry + mouthSymmetry) / 2 * 100;
      return symmetryScore.clamp(50.0, 100.0);
    } catch (e) {
      return 75.0;
    }
  }

  /// 눈 분석
  static Map<String, dynamic> _calculateEyeAnalysis(List<Landmark> landmarks) {
    if (landmarks.length < 468) return {'score': 75.0};

    try {
      final leftEyeWidth = (landmarks[33].x - landmarks[133].x).abs();
      final rightEyeWidth = (landmarks[362].x - landmarks[263].x).abs();
      final eyeDistance = (landmarks[362].x - landmarks[33].x).abs();
      
      final avgEyeWidth = (leftEyeWidth + rightEyeWidth) / 2;
      final idealRatio = eyeDistance / avgEyeWidth;
      
      final eyeScore = 100 - ((idealRatio - 1.0).abs() * 30);
      
      return {
        'score': eyeScore.clamp(50.0, 100.0),
        'leftWidth': leftEyeWidth,
        'rightWidth': rightEyeWidth,
        'distance': eyeDistance,
        'symmetry': 1.0 - (leftEyeWidth - rightEyeWidth).abs() / avgEyeWidth,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 코 분석
  static Map<String, dynamic> _calculateNoseAnalysis(List<Landmark> landmarks) {
    if (landmarks.length < 468) return {'score': 75.0};

    try {
      final noseTip = landmarks[2];
      final noseLeft = landmarks[31];
      final noseRight = landmarks[35];
      final noseBridge = landmarks[9];
      
      final noseWidth = (noseRight.x - noseLeft.x).abs();
      final noseHeight = (noseTip.y - noseBridge.y).abs();
      final noseRatio = noseHeight / noseWidth;
      
      final noseScore = 100 - ((noseRatio - 1.2).abs() * 40);
      
      return {
        'score': noseScore.clamp(50.0, 100.0),
        'width': noseWidth,
        'height': noseHeight,
        'ratio': noseRatio,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 입술 분석
  static Map<String, dynamic> _calculateLipAnalysis(List<Landmark> landmarks) {
    if (landmarks.length < 468) return {'score': 75.0};

    try {
      final upperLip = landmarks[13];
      final lowerLip = landmarks[18];
      final leftMouth = landmarks[61];
      final rightMouth = landmarks[291];
      
      final lipWidth = (rightMouth.x - leftMouth.x).abs();
      final lipHeight = (lowerLip.y - upperLip.y).abs();
      final lipRatio = lipWidth / lipHeight;
      
      final lipScore = 100 - ((lipRatio - 3.0).abs() * 20);
      
      return {
        'score': lipScore.clamp(50.0, 100.0),
        'width': lipWidth,
        'height': lipHeight,
        'ratio': lipRatio,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 턱선 분석
  static Map<String, dynamic> _calculateJawlineAnalysis(List<Landmark> landmarks) {
    if (landmarks.length < 468) return {'score': 75.0};

    try {
      final gonialAngle = _calculateGonialAngle(landmarks);
      final cervicoMentalAngle = _calculateCervicoMentalAngle(landmarks);
      
      if (gonialAngle == null || cervicoMentalAngle == null) {
        return {'score': 75.0};
      }
      
      final liftingScore = _calculateLiftingScore(gonialAngle, cervicoMentalAngle);
      
      return {
        'score': liftingScore.clamp(50.0, 100.0),
        'gonialAngle': gonialAngle,
        'cervicoMentalAngle': cervicoMentalAngle,
        'liftingScore': liftingScore,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 시각화 기반 종합 점수 계산
  static double _calculateOverallBeautyScoreFromVisualization({
    required double verticalScore,
    required double horizontalScore,
    required double lowerFaceScore,
    required double symmetry,
    required double eyeScore,
    required double noseScore,
    required double lipScore,
    required double jawScore,
  }) {
    return (
      (verticalScore * 0.25) +
      (horizontalScore * 0.20) +
      (lowerFaceScore * 0.15) +
      (symmetry * 0.15) +
      (eyeScore * 0.10) +
      (noseScore * 0.08) +
      (lipScore * 0.05) +
      (jawScore * 0.02)
    ).clamp(50.0, 100.0);
  }

  /// 하악각 계산
  static double? _calculateGonialAngle(List<Landmark> landmarks) {
    final requiredIndices = [234, 172, 150, 454, 397, 379];
    if (requiredIndices.any((i) => i >= landmarks.length)) return null;
    
    final leftGonial = _calculateJawAngle(landmarks[234], landmarks[172], landmarks[150]);
    final rightGonial = _calculateJawAngle(landmarks[454], landmarks[397], landmarks[379]);
    
    if (leftGonial == null || rightGonial == null) return null;
    return (leftGonial + rightGonial) / 2;
  }

  /// 턱목각 계산
  static double? _calculateCervicoMentalAngle(List<Landmark> landmarks) {
    if (152 >= landmarks.length || 18 >= landmarks.length) return null;
    
    final chin = landmarks[152];
    final neckFront = landmarks[18];
    final neckBottomX = chin.x;
    final neckBottomY = chin.y + (chin.y - neckFront.y).abs() * 1.5;
    
    return _calculateAngle3Points(
      Offset(neckBottomX, neckBottomY),
      Offset(chin.x, chin.y),
      Offset(neckFront.x, neckFront.y),
    );
  }

  /// 턱 각도 계산
  static double? _calculateJawAngle(Landmark earPoint, Landmark jawCorner, Landmark jawMid) {
    const verticalVector = Offset(0, 1);
    final jawVector = Offset(jawMid.x - jawCorner.x, jawMid.y - jawCorner.y);
    final jawLength = jawVector.distance;
    if (jawLength == 0) return null;
    
    final jawUnit = jawVector / jawLength;
    final dotProduct = verticalVector.dx * jawUnit.dx + verticalVector.dy * jawUnit.dy;
    final cosAngle = dotProduct.clamp(-1.0, 1.0);
    final angleRad = math.acos(cosAngle.abs());
    final angleDeg = angleRad * 180 / math.pi;
    
    return 90 + angleDeg;
  }

  /// 3점 각도 계산
  static double? _calculateAngle3Points(Offset p1, Offset p2, Offset p3) {
    final v1 = p1 - p2;
    final v2 = p3 - p2;
    final len1 = v1.distance;
    final len2 = v2.distance;
    
    if (len1 == 0 || len2 == 0) return null;
    
    final dotProduct = v1.dx * v2.dx + v1.dy * v2.dy;
    final cosAngle = (dotProduct / (len1 * len2)).clamp(-1.0, 1.0);
    final angleRad = math.acos(cosAngle);
    return angleRad * 180 / math.pi;
  }

  /// 리프팅 점수 계산
  static double _calculateLiftingScore(double gonialAngle, double cervicoMentalAngle) {
    double gonialScore;
    if (gonialAngle <= 90) {
      gonialScore = 100;
    } else if (gonialAngle <= 120) {
      gonialScore = 100 - ((gonialAngle - 90) * 20 / 30);
    } else if (gonialAngle <= 140) {
      gonialScore = 80 - ((gonialAngle - 120) * 60 / 20);
    } else {
      gonialScore = (20 - ((gonialAngle - 140) * 20 / 10)).clamp(0.0, 20.0);
    }
    
    double cervicoScore;
    if (105 <= cervicoMentalAngle && cervicoMentalAngle <= 115) {
      cervicoScore = 100;
    } else if (100 <= cervicoMentalAngle && cervicoMentalAngle <= 120) {
      cervicoScore = 90 - (cervicoMentalAngle - 110).abs() * 2;
    } else if (90 <= cervicoMentalAngle && cervicoMentalAngle <= 130) {
      cervicoScore = 70 - (cervicoMentalAngle - 110).abs() * 1.5;
    } else {
      cervicoScore = (70 - (cervicoMentalAngle - 110).abs() * 2).clamp(40.0, 70.0);
    }
    
    final liftingScore = gonialScore * 0.7 + cervicoScore * 0.3;
    return liftingScore.clamp(0.0, 100.0);
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
  }
}