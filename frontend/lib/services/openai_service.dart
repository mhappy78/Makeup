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

      final prompt = _buildComparisonPrompt(beforeAnalysis, afterAnalysis, scoreChanges);
      
      final response = await _callGptApi(prompt);
      
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

      final prompt = _buildInitialAnalysisPrompt(beautyAnalysis);
      
      final response = await _callGptApi(prompt);
      
      debugPrint('✅ GPT 기초 뷰티스코어 분석 완료');
      
      return _parseGptResponse(response);
      
    } catch (e) {
      debugPrint('❌ GPT 기초 뷰티스코어 분석 실패: $e');
      rethrow;
    }
  }

  /// GPT API 호출
  static Future<String> _callGptApi(String prompt) async {
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
            'content': '당신은 뷰티 분석 전문가입니다. 정확하고 전문적인 분석을 제공하며, JSON 형식으로 응답합니다.',
          },
          {
            'role': 'user',
            'content': prompt,
          }
        ],
        'temperature': 0.7,
        'max_tokens': 1000,
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

  /// 비교 분석용 프롬프트 생성
  static String _buildComparisonPrompt(
    Map<String, dynamic> before,
    Map<String, dynamic> after,
    Map<String, double> changes,
  ) {
    return '''
뷰티 점수 변화 분석을 수행해주세요.

**변형 전 점수:**
- 전체 점수: ${before['overallScore']?.toStringAsFixed(1) ?? 'N/A'}
- 가로 황금비율: ${_getScoreFromAnalysis(before['verticalScore'])}
- 세로 대칭성: ${_getScoreFromAnalysis(before['horizontalScore'])}
- 하관 조화: ${_getScoreFromAnalysis(before['lowerFaceScore'])}
- 기본 대칭성: ${before['symmetry']?.toStringAsFixed(1) ?? 'N/A'}

**변형 후 점수:**
- 전체 점수: ${after['overallScore']?.toStringAsFixed(1) ?? 'N/A'}
- 가로 황금비율: ${_getScoreFromAnalysis(after['verticalScore'])}
- 세로 대칭성: ${_getScoreFromAnalysis(after['horizontalScore'])}
- 하관 조화: ${_getScoreFromAnalysis(after['lowerFaceScore'])}
- 기본 대칭성: ${after['symmetry']?.toStringAsFixed(1) ?? 'N/A'}

**점수 변화:**
${changes.entries.map((e) => '- ${e.key}: ${(e.value as num).toStringAsFixed(1)}').join('\n')}

다음 JSON 형식으로 응답해주세요:
{
  "analysis": "변화에 대한 상세 분석 (2-3문장)",
  "recommendations": [
    "구체적인 추천사항 1",
    "구체적인 추천사항 2", 
    "구체적인 추천사항 3"
  ]
}''';
  }

  /// 기초 분석용 프롬프트 생성
  static String _buildInitialAnalysisPrompt(Map<String, dynamic> analysis) {
    return '''
뷰티 점수 분석을 수행해주세요.

**현재 점수:**
- 전체 점수: ${analysis['overallScore']?.toStringAsFixed(1) ?? 'N/A'}
- 가로 황금비율: ${_getScoreFromAnalysis(analysis['verticalScore'])}
- 세로 대칭성: ${_getScoreFromAnalysis(analysis['horizontalScore'])}
- 하관 조화: ${_getScoreFromAnalysis(analysis['lowerFaceScore'])}
- 기본 대칭성: ${analysis['symmetry']?.toStringAsFixed(1) ?? 'N/A'}
- 눈 점수: ${_getScoreFromAnalysis(analysis['eyeScore'])}
- 코 점수: ${_getScoreFromAnalysis(analysis['noseScore'])}
- 입술 점수: ${_getScoreFromAnalysis(analysis['lipScore'])}

다음 JSON 형식으로 응답해주세요:
{
  "analysis": "전반적인 뷰티 특징 분석 (3-4문장)",
  "recommendations": [
    "개선을 위한 추천사항 1",
    "개선을 위한 추천사항 2",
    "개선을 위한 추천사항 3"
  ]
}''';
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

  /// GPT 응답 파싱
  static Map<String, dynamic> _parseGptResponse(String response) {
    try {
      // JSON 부분만 추출 (```json과 ``` 제거)
      String jsonString = response.trim();
      
      // 마크다운 코드 블록 제거
      if (jsonString.startsWith('```json')) {
        jsonString = jsonString.substring(7);
      }
      if (jsonString.startsWith('```')) {
        jsonString = jsonString.substring(3);
      }
      if (jsonString.endsWith('```')) {
        jsonString = jsonString.substring(0, jsonString.length - 3);
      }
      
      final parsed = jsonDecode(jsonString.trim());
      
      return {
        'analysis': parsed['analysis'] ?? '분석 결과를 파싱할 수 없습니다.',
        'recommendations': List<String>.from(parsed['recommendations'] ?? []),
      };
    } catch (e) {
      debugPrint('GPT 응답 파싱 실패: $e');
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