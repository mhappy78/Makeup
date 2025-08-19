import 'dart:convert';
import 'dart:html' as html;
import 'dart:async';
import 'package:flutter/foundation.dart';

/// OpenAI GPT API 서비스
/// 환경변수로 주입된 API 키를 사용하여 프론트엔드에서 직접 GPT 분석 수행
class OpenAIService {
  // 빌드 시 환경변수에서 주입되는 API 키
  static const String _apiKey = String.fromEnvironment('OPENAI_API_KEY', defaultValue: '');
  static const String _baseUrl = 'https://api.openai.com/v1';
  static const String _model = 'gpt-4o-mini';

  /// API 키가 설정되었는지 확인
  static bool get hasApiKey => _apiKey.isNotEmpty;

  /// 뷰티 점수 변화 분석
  /// 
  /// [beforeAnalysis] - 변형 전 뷰티 분석 결과
  /// [afterAnalysis] - 변형 후 뷰티 분석 결과
  /// [scoreChanges] - 점수 변화량
  /// 
  /// Returns: GPT 분석 결과
  static Future<Map<String, dynamic>> analyzeBeautyComparison({
    required Map<String, dynamic> beforeAnalysis,
    required Map<String, dynamic> afterAnalysis,
    required Map<String, double> scoreChanges,
  }) async {
    if (!hasApiKey) {
      throw Exception('OpenAI API 키가 설정되지 않았습니다');
    }

    try {
      debugPrint('🤖 GPT 뷰티 비교 분석 시작...');

      final systemPrompt = _getComparisonSystemPrompt();
      final userPrompt = _buildComparisonPrompt(beforeAnalysis, afterAnalysis, scoreChanges);
      
      final response = await _callGptApi({
        'system': systemPrompt,
        'user': userPrompt,
        'isComparison': true,
      });
      
      debugPrint('✅ GPT 뷰티 비교 분석 완료');
      
      return _parseGptResponse(response);
      
    } catch (e) {
      debugPrint('❌ GPT 뷰티 비교 분석 실패: $e');
      rethrow;
    }
  }

  /// 기초 뷰티스코어 분석
  /// 
  /// [beautyAnalysis] - 뷰티 분석 결과
  /// 
  /// Returns: GPT 분석 결과
  static Future<Map<String, dynamic>> analyzeInitialBeautyScore({
    required Map<String, dynamic> beautyAnalysis,
  }) async {
    if (!hasApiKey) {
      throw Exception('OpenAI API 키가 설정되지 않았습니다');
    }

    try {
      debugPrint('🤖 GPT 기초 뷰티스코어 분석 시작...');

      final systemPrompt = _getInitialAnalysisSystemPrompt();
      final userPrompt = _buildInitialAnalysisPrompt(beautyAnalysis);
      
      final response = await _callGptApi({
        'system': systemPrompt,
        'user': userPrompt,
        'isComparison': false,
      });
      
      debugPrint('✅ GPT 기초 뷰티스코어 분석 완료');
      
      return _parseGptResponse(response);
      
    } catch (e) {
      debugPrint('❌ GPT 기초 뷰티스코어 분석 실패: $e');
      rethrow;
    }
  }

  /// GPT API 호출
  static Future<String> _callGptApi(Map<String, dynamic> prompt) async {
    final request = html.HttpRequest();
    
    try {
      request.open('POST', '$_baseUrl/chat/completions');
      request.setRequestHeader('Content-Type', 'application/json');
      request.setRequestHeader('Authorization', 'Bearer $_apiKey');
      
      final body = jsonEncode({
        'model': _model,
        'messages': [
          {
            'role': 'system',
            'content': prompt['system'] ?? '',
          },
          {
            'role': 'user',
            'content': prompt['user'] ?? '',
          }
        ],
        'temperature': 0.7,
        'max_tokens': prompt['isComparison'] == true ? 1000 : 1200,
      });

      final completer = Completer<String>();
      
      request.onLoad.listen((_) {
        if (request.status == 200) {
          final responseData = jsonDecode(request.responseText!);
          final content = responseData['choices'][0]['message']['content'] as String;
          completer.complete(content);
        } else {
          completer.completeError(
            Exception('OpenAI API 오류: ${request.status} - ${request.responseText}')
          );
        }
      });

      request.onError.listen((e) {
        completer.completeError(Exception('네트워크 오류: $e'));
      });

      request.send(body);
      
      return await completer.future;
      
    } catch (e) {
      throw Exception('GPT API 호출 실패: $e');
    }
  }

  /// 비교 분석용 시스템 프롬프트 생성 (백엔드와 동일)
  static String _getComparisonSystemPrompt() {
    return '''
당신은 전문적인 뷰티 컨설턴트이자 성형외과 상담 전문가입니다. 
얼굴 변형 전후의 뷰티 점수를 분석하고, 개선사항과 추천사항을 제공해주세요.

분석 기준:
- 가로 황금비율 (verticalScore): 얼굴의 가로 비율 균형
- 세로 대칭성 (horizontalScore): 얼굴의 세로 대칭성
- 하관 조화 (lowerFaceScore): 하관부 조화로움
- 전체 대칭성 (symmetry): 좌우 대칭성
- 턱 곡률 (jawScore): 턱선의 각도와 곡률

전문관리 추천 가이드라인:
- 필러는 절대 추천하지 마세요
- 레이저 리프팅을 우선 추천하고, 보톡스, 실리프팅, 고주파, 울쎄라 등을 대안으로 제시
- 비용은 반드시 "30만원", "50만원" 형태로만 표기 (300,000원, 30만원대 등 금지)
- 구체적 시술정보(샷수, 용량, 기간 등)를 반드시 포함

응답은 반드시 한국어로, 친근하면서도 전문적인 톤으로 작성해주세요.
''';
  }

  /// 비교 분석용 사용자 프롬프트 생성 (백엔드와 동일)
  static String _buildComparisonPrompt(
    Map<String, dynamic> before,
    Map<String, dynamic> after,
    Map<String, double> changes,
  ) {
    // 안전한 점수 추출 함수
    double getScore(Map<String, dynamic> analysis, String key, [double defaultValue = 0]) {
      final value = analysis[key];
      if (value is Map && value['score'] != null) {
        return (value['score'] as num).toDouble();
      }
      if (value is num) {
        return value.toDouble();
      }
      return defaultValue;
    }

    // 점수 변화 요약
    final changesSummary = <String>[];
    changes.forEach((key, change) {
      if (change.abs() > 0.5) { // 0.5점 이상 변화만 포함
        final direction = change > 0 ? "상승" : "하락";
        changesSummary.add("$key: ${change.round()}점 $direction");
      }
    });

    return '''
뷰티 시술 전후 분석 결과:

【시술 전 점수】
- 종합점수: ${getScore(before, 'overallScore').round()}점
- 가로 황금비율: ${getScore(before, 'verticalScore').round()}점
- 세로 대칭성: ${getScore(before, 'horizontalScore').round()}점
- 하관 조화: ${getScore(before, 'lowerFaceScore').round()}점
- 전체 대칭성: ${getScore(before, 'symmetry').round()}점
- 턱 곡률: ${getScore(before, 'jawScore').round()}점

【시술 후 점수】
- 종합점수: ${getScore(after, 'overallScore').round()}점
- 가로 황금비율: ${getScore(after, 'verticalScore').round()}점
- 세로 대칭성: ${getScore(after, 'horizontalScore').round()}점
- 하관 조화: ${getScore(after, 'lowerFaceScore').round()}점
- 전체 대칭성: ${getScore(after, 'symmetry').round()}점
- 턱 곡률: ${getScore(after, 'jawScore').round()}점

【주요 변화】
${changesSummary.isNotEmpty ? changesSummary.join(', ') : '큰 변화 없음'}

다음 형식으로 분석해주세요:

1. 전반적인 변화 요약 (2-3문장)

2. 항목별 상세 분석
**🟢 개선된 점:**
- [항목명]: [구체적 개선 내용과 의미]

**🔸 아쉬운 점:**
- [항목명]: [부족한 부분과 의미]

---

위 분석에서 "아쉬운 점"에 언급된 항목들에 대해서만 구체적인 개선 방법을 제시해주세요:

🎯 **[아쉬운 항목명]** 개선
💪 **운동/습관**: 매일 [시간]분 [구체적 방법]
추천 사이트: [실제 사용 가능한 사이트명](https://www.실제URL.com)

🏥 **전문 관리**: [시술명] ([숫자]만원, [시술정보])
- 우선 추천: 레이저 리프팅 (턱선, 안면거상 효과가 필요한 경우)
- 대안: 보톡스, 실리프팅, 고주파 등 (필러 제외, 해당 부위에 적합한 시술)
- 비용 예시: 30만원, 50만원, 80만원 등 (숫자+만원 형태로만 표기)
- 시술정보 예시: 레이저 300-500샷, 보톡스 20-30cc, 실리프팅 3-5개월 지속
효과: [구체적 효과 설명]
추천 병원: [실제 병원명](https://www.실제병원URL.com)

친근하고 전문적인 톤으로 작성해주세요.
''';
  }

  /// 기초 분석용 시스템 프롬프트 생성 (백엔드와 동일)
  static String _getInitialAnalysisSystemPrompt() {
    return '''
당신은 뷰티 분석과 구체적 실천 방법 전문가입니다. 

**목표**: 분석한 수치적 결과를 바탕으로 구체적이고 실천 가능한 개선 방법을 제시

**응답 구조**:
1. **간단한 분석 요약** (2-3줄)
2. **분석 결과** (주요 강점과 개선점을 수치와 함께)
3. **구체적 실천 방법 3가지** (분석에서 언급한 개선점과 연결)

**실천 방법 형식** (각 항목마다):
- 🎯 **개선 목표**: [분석에서 언급한 구체적 수치] → [목표 수치]
- 💪 **운동/습관**: 매일 [시간]분 [구체적 방법]
추천 사이트: [실제 사용 가능한 사이트명](https://www.실제URL.com)
- 🏥 **전문 관리**: [시술명] ([숫자]만원, [시술정보])
  - 우선 추천: 레이저 리프팅 (턱선, 안면거상, 리프팅 효과가 필요한 경우)
  - 대안: 보톡스, 실리프팅, 고주파, 울쎄라 등 (필러 제외, 해당 부위에 적합한 시술)
  - 비용 표기: 30만원, 50만원, 80만원 등 (반드시 숫자+만원 형태로만 표기)
  - 시술정보 예시: 레이저 300-500샷, 보톡스 20-30cc, 실리프팅 3-5개월 지속, 울쎄라 1-2회 시술
  효과: [구체적 효과 설명]
추천 병원: [실제 병원명](https://www.실제병원URL.com)

**중요**: 추천하는 모든 사이트와 병원 URL은 실제로 존재하고 접속 가능한 곳만 포함하세요.
- 운동/습관: YouTube 채널, 피트니스 앱, 건강 정보 사이트 등 실제 이용 가능한 곳
- 전문 관리: 실제 성형외과, 피부과, 에스테틱 클리닉 등 공식 홈페이지

**필수 요구사항**:
- 분석에서 언급한 정확한 수치를 반드시 포함
- 각 개선점마다 운동+전문관리 모두 제시
- 구체적 시간, 비용, 시술정보(샷수/용량/기간) 명시
- 비용은 반드시 "30만원", "50만원" 형태로만 표기 (300,000원, 30만원대 등 금지)
- 전문관리에서 필러는 절대 추천하지 말고, 레이저/보톡스/실리프팅/고주파 등 권장
''';
  }

  /// 기초 분석용 사용자 프롬프트 생성 (백엔드와 동일)
  static String _buildInitialAnalysisPrompt(Map<String, dynamic> beautyAnalysis) {
    // 안전한 점수 추출 함수
    double getScore(Map<String, dynamic> analysis, String key, [double defaultValue = 0]) {
      final value = analysis[key];
      if (value is Map && value['score'] != null) {
        return (value['score'] as num).toDouble();
      }
      if (value is num) {
        return value.toDouble();
      }
      return defaultValue;
    }

    // 상세 정보 추출
    Map<String, dynamic> getDetailedInfo(String key) {
      final value = beautyAnalysis[key];
      if (value is Map<String, dynamic>) {
        return value;
      }
      return <String, dynamic>{};
    }

    final mainScores = {
      'overall': getScore(beautyAnalysis, 'overallScore'),
      'vertical': getScore(beautyAnalysis, 'verticalScore'),
      'horizontal': getScore(beautyAnalysis, 'horizontalScore'),
      'lowerFace': getScore(beautyAnalysis, 'lowerFaceScore'),
      'symmetry': getScore(beautyAnalysis, 'symmetry'),
      'jaw': getScore(beautyAnalysis, 'jawScore'),
    };

    // 강점과 개선 영역 분류
    final strengths = <String>[];
    final improvementAreas = <String>[];
    
    final scoreNames = {
      'vertical': '가로 황금비율',
      'horizontal': '세로 대칭성',
      'lowerFace': '하관 조화',
      'symmetry': '전체 대칭성',
      'jaw': '턱 곡률'
    };
    
    mainScores.forEach((key, score) {
      if (key == 'overall') return;
      final name = scoreNames[key] ?? key;
      if (score >= 80) {
        strengths.add('$name (${score.round()}점)');
      } else if (score < 70) {
        improvementAreas.add('$name (${score.round()}점)');
      }
    });

    // 상세 분석 정보 구성
    final detailedAnalysis = <String>[];
    final verticalInfo = getDetailedInfo('verticalScore');
    final horizontalInfo = getDetailedInfo('horizontalScore');
    final lowerFaceInfo = getDetailedInfo('lowerFaceScore');
    final jawInfo = getDetailedInfo('jawScore');

    // 가로 황금비율 (5구간 퍼센트)
    if (mainScores['vertical']! >= 10) {
      var analysisText = '가로 황금비율: ${mainScores['vertical']!.round()}점';
      if (verticalInfo['percentages'] != null) {
        final percentages = verticalInfo['percentages'] as List;
        final sections = ['왼쪽바깥', '왼쪽눈', '미간', '오른쪽눈', '오른쪽바깥'];
        final percentDetails = <String>[];
        for (int i = 0; i < percentages.length && i < 5; i++) {
          percentDetails.add('${sections[i]} ${(percentages[i] as num).round()}%');
        }
        analysisText += ' (구간별: ${percentDetails.join(', ')})';
      }
      detailedAnalysis.add(analysisText);
    }

    // 세로 대칭성 (2구간 퍼센트)
    if (mainScores['horizontal']! >= 10) {
      var analysisText = '세로 대칭성: ${mainScores['horizontal']!.round()}점';
      if (horizontalInfo['upperPercentage'] != null && horizontalInfo['lowerPercentage'] != null) {
        final upper = (horizontalInfo['upperPercentage'] as num).round();
        final lower = (horizontalInfo['lowerPercentage'] as num).round();
        analysisText += ' (눈~코 $upper%, 코~턱 $lower%)';
      }
      detailedAnalysis.add(analysisText);
    }

    // 하관 조화 (2구간 퍼센트)
    if (mainScores['lowerFace']! >= 10) {
      var analysisText = '하관 조화: ${mainScores['lowerFace']!.round()}점';
      if (lowerFaceInfo['upperPercentage'] != null && lowerFaceInfo['lowerPercentage'] != null) {
        final upper = (lowerFaceInfo['upperPercentage'] as num).round();
        final lower = (lowerFaceInfo['lowerPercentage'] as num).round();
        analysisText += ' (인중 $upper%, 입~턱 $lower%)';
      }
      detailedAnalysis.add(analysisText);
    }

    // 전체 대칭성
    if (mainScores['symmetry']! >= 10) {
      detailedAnalysis.add('전체 대칭성: ${mainScores['symmetry']!.round()}점');
    }

    // 턱 곡률 (각도 정보)
    if (mainScores['jaw']! >= 10) {
      var analysisText = '턱 곡률: ${mainScores['jaw']!.round()}점';
      if (jawInfo['gonialAngle'] != null && jawInfo['cervicoMentalAngle'] != null) {
        final gonial = (jawInfo['gonialAngle'] as num).round();
        final cervico = (jawInfo['cervicoMentalAngle'] as num).round();
        analysisText += ' (하악각 ${gonial}°, 턱목각 ${cervico}°)';
      }
      detailedAnalysis.add(analysisText);
    }

    // 개선 포인트 추출
    final improvementPoints = <String>[];
    
    // 가로 황금비율 체크 (20%에서 3% 이상 벗어난 경우)
    if (verticalInfo['percentages'] != null) {
      final percentages = verticalInfo['percentages'] as List;
      final sections = ['왼쪽바깥', '왼쪽눈', '미간', '오른쪽눈', '오른쪽바깥'];
      for (int i = 0; i < percentages.length && i < 5; i++) {
        final pct = (percentages[i] as num).toDouble();
        final diff = (pct - 20.0).abs();
        if (diff > 3.0) {
          improvementPoints.add('${sections[i]} ${pct.round()}% (이상적 20%)');
        }
      }
    }

    // 세로 대칭성 체크 (50:50에서 3% 이상 벗어난 경우)
    if (horizontalInfo['upperPercentage'] != null) {
      final upper = (horizontalInfo['upperPercentage'] as num).toDouble();
      if ((upper - 50.0).abs() > 3.0) {
        improvementPoints.add('상안면 ${upper.round()}% (이상적 50%)');
      }
    }

    // 하관 조화 체크 (33:67에서 벗어난 경우)
    if (lowerFaceInfo['upperPercentage'] != null) {
      final upper = (lowerFaceInfo['upperPercentage'] as num).toDouble();
      if ((upper - 33.0).abs() > 3.0) {
        improvementPoints.add('인중 ${upper.round()}% (이상적 33%)');
      }
    }

    // 턱 곡률 체크 (90-120도 범위 벗어난 경우)
    if (jawInfo['gonialAngle'] != null) {
      final gonial = (jawInfo['gonialAngle'] as num).toDouble();
      if (gonial < 90 || gonial > 120) {
        improvementPoints.add('하악각 ${gonial.round()}° (이상적 90-120°)');
      }
    }

    return '''
측정 결과: 종합 ${mainScores['overall']!.round()}점

강점 항목: ${strengths.isNotEmpty ? strengths.join(', ') : '균형 잡힌 전체적 비율'}
개선 항목: ${improvementAreas.isNotEmpty ? improvementAreas.join(', ') : '없음'}

특징적 측정값:
${improvementPoints.isNotEmpty ? improvementPoints.map((point) => '- $point').join('\n') : '- 전체적으로 이상적인 비율 유지'}

다음 3개 항목으로 분석해주세요:

1. 🌟 내 얼굴의 좋은 점
측정 결과 중 이상적인 범위에 있거나 매력적인 부분을 구체적 수치와 함께 설명해주세요.

2. 📊 개선이 필요한 부분  
이상적 범위에서 벗어난 부분을 구체적 수치와 함께 쉽게 설명해주세요.
(예: "하악각이 133°로 이상적 범위 90-120°보다 커서 턱선이 부드러운 편이에요")

3. 💡 개선 후 기대효과
개선되면 어떤 매력적인 변화가 있을지 희망적으로 설명해주세요.

---

위 2번에서 언급한 개선 필요 부분을 정확히 참조하여 구체적 실천 방법을 제시해주세요.

각 개선점마다 다음 형식으로:
🎯 **[2번에서 언급한 구체적 문제]** 개선
💪 **운동/습관**: 매일 [시간]분 [구체적 방법] + 추천 사이트
🏥 **전문 관리**: [시술명] [예상비용] [효과]

반드시 2번 분석의 구체적 수치와 문제점을 참조해서 연결해주세요.
''';
  }

  /// 분석 결과에서 점수 추출
  static String _getScoreFromAnalysis(dynamic analysis) {
    if (analysis is Map && analysis['score'] != null) {
      return analysis['score'].toStringAsFixed(1);
    } else if (analysis is num) {
      return analysis.toStringAsFixed(1);
    }
    return 'N/A';
  }

  /// GPT 응답 파싱 (백엔드와 동일한 방식)
  static Map<String, dynamic> _parseGptResponse(String response) {
    try {
      debugPrint('🤖 GPT 원본 응답: ${response.substring(0, response.length > 500 ? 500 : response.length)}...');
      
      // 분석 텍스트와 실천 방법 분리 (백엔드와 동일)
      final recommendations = <String>[];
      var cleanAnalysisText = response;
      
      final firstSeparatorIndex = response.indexOf('---');
      
      if (firstSeparatorIndex != -1) {
        // --- 이전 부분만 분석 텍스트로 사용
        cleanAnalysisText = response.substring(0, firstSeparatorIndex).trim();
        
        // --- 이후 부분을 실천 방법으로 사용
        final practiceSection = response.substring(firstSeparatorIndex + 3).trim();
        
        // 실제 내용이 있으면 전체를 하나의 추천사항으로 추가
        if (practiceSection.isNotEmpty && practiceSection.length > 10) {
          recommendations.add(practiceSection);
        }
      }
      
      return {
        'analysis': cleanAnalysisText.isNotEmpty ? cleanAnalysisText : '뷰티 분석이 완료되었습니다.',
        'recommendations': recommendations.isNotEmpty ? recommendations : [
          '균형잡힌 얼굴 비율 유지',
          '자연스러운 대칭성 개선', 
          '전반적인 조화 추구'
        ],
      };
    } catch (e) {
      debugPrint('❌ GPT 응답 파싱 실패: $e');
      debugPrint('원본 응답: $response');
      
      // 파싱 실패 시 기본 응답
      return {
        'analysis': '뷰티 분석이 완료되었습니다. 더 자세한 분석을 위해 다시 시도해보세요.',
        'recommendations': [
          '균형잡힌 얼굴 비율 유지',
          '자연스러운 대칭성 개선', 
          '전반적인 조화 추구'
        ],
      };
    }
  }

  /// API 키 상태 확인
  static Map<String, dynamic> getApiStatus() {
    return {
      'hasApiKey': hasApiKey,
      'apiKeyLength': hasApiKey ? _apiKey.length : 0,
      'model': _model,
      'isConfigured': hasApiKey,
    };
  }

  /// 서비스 건강성 체크
  static Future<Map<String, dynamic>> checkServiceHealth() async {
    final result = {
      'hasApiKey': hasApiKey,
      'isConfigured': hasApiKey,
      'healthScore': hasApiKey ? 100 : 0,
      'recommendation': '',
    };

    if (!hasApiKey) {
      result['recommendation'] = 'OpenAI API 키가 설정되지 않았습니다. 환경변수를 확인하세요.';
    } else {
      result['recommendation'] = 'OpenAI API 서비스가 정상적으로 설정되었습니다.';
    }

    return result;
  }
}

/// GPT 분석 결과 데이터 클래스
class GptAnalysisResult {
  final String analysis;
  final List<String> recommendations;

  GptAnalysisResult({
    required this.analysis,
    required this.recommendations,
  });

  factory GptAnalysisResult.fromMap(Map<String, dynamic> map) {
    return GptAnalysisResult(
      analysis: map['analysis'] ?? '',
      recommendations: List<String>.from(map['recommendations'] ?? []),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'analysis': analysis,
      'recommendations': recommendations,
    };
  }
}