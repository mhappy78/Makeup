import 'package:flutter/foundation.dart';
import 'dart:typed_data';
import 'dart:async';
import 'warp_service.dart';
import '../models/app_state.dart';

/// 클라이언트 전용 워핑 관리자 - 100% 프론트엔드 독립
class WarpFallbackManager {
  static const int _maxRetries = 2;
  static const Duration _retryDelay = Duration(milliseconds: 500);
  static const int _clientSideTimeoutMs = 10000; // 10초 타임아웃
  
  // 통계 데이터 (클라이언트 전용)
  static int _clientSuccessCount = 0;
  static int _clientFailureCount = 0;
  static int _totalAttempts = 0;
  
  /// 클라이언트 전용 워핑 적용 - 재시도 로직 포함
  /// 
  /// [imageBytes] - 이미지 데이터
  /// [warpParams] - 워핑 파라미터
  /// 
  /// Returns: WarpAttemptResult (클라이언트 전용)
  static Future<WarpAttemptResult> smartApplyWarp({
    required Uint8List imageBytes,
    required WarpParameters warpParams,
  }) async {
    _totalAttempts++;
    
    // 클라이언트 워핑 시도 (재시도 로직 포함)
    for (int attempt = 1; attempt <= _maxRetries; attempt++) {
      final result = await _attemptClientSideWarp(imageBytes, warpParams);
      
      if (result.success) {
        _clientSuccessCount++;
        return result;
      }
      
      // 마지막 시도가 아니면 잠시 대기 후 재시도
      if (attempt < _maxRetries) {
        await Future.delayed(_retryDelay);
        debugPrint('🔄 클라이언트 워핑 재시도 ($attempt/$_maxRetries): ${result.error}');
      }
    }
    
    _clientFailureCount++;
    return WarpAttemptResult.failure(
      source: 'client',
      error: '클라이언트 워핑 최대 재시도 실패',
      attempts: _maxRetries,
    );
  }

  /// 클라이언트 전용 프리셋 적용
  static Future<WarpAttemptResult> smartApplyPreset({
    required Uint8List imageBytes,
    required List<Landmark> landmarks,
    required String presetType,
  }) async {
    _totalAttempts++;
    
    // 클라이언트 프리셋 시도 (재시도 로직 포함)
    for (int attempt = 1; attempt <= _maxRetries; attempt++) {
      final result = await _attemptClientSidePreset(imageBytes, landmarks, presetType);
      
      if (result.success) {
        _clientSuccessCount++;
        return result;
      }
      
      // 마지막 시도가 아니면 잠시 대기 후 재시도
      if (attempt < _maxRetries) {
        await Future.delayed(_retryDelay);
        debugPrint('🔄 클라이언트 프리셋 재시도 ($attempt/$_maxRetries): ${result.error}');
      }
    }
    
    _clientFailureCount++;
    return WarpAttemptResult.failure(
      source: 'client',
      error: '클라이언트 프리셋 최대 재시도 실패',
      attempts: _maxRetries,
    );
  }

  /// 클라이언트 사이드 워핑 시도
  static Future<WarpAttemptResult> _attemptClientSideWarp(
    Uint8List imageBytes,
    WarpParameters params,
  ) async {
    if (!WarpService.isEngineLoaded) {
      return WarpAttemptResult.failure(
        source: 'client',
        error: '워핑 엔진이 로드되지 않음 - 페이지를 새로고침하세요',
      );
    }

    final stopwatch = Stopwatch()..start();
    
    try {
      // 이미지 데이터 추출
      final imageDataMap = await WarpService.extractImageData(imageBytes)
          .timeout(Duration(milliseconds: _clientSideTimeoutMs ~/ 2));
      
      if (imageDataMap == null) {
        throw Exception('이미지 데이터 추출 실패');
      }

      final imageData = imageDataMap['data'] as Uint8List;
      final width = imageDataMap['width'] as int;
      final height = imageDataMap['height'] as int;

      // 워핑 적용
      final result = await WarpService.applyWarp(
        imageBytes: imageData,
        width: width,
        height: height,
        startX: params.startX,
        startY: params.startY,
        endX: params.endX,
        endY: params.endY,
        influenceRadius: params.influenceRadius,
        strength: params.strength,
        mode: params.mode,
      ).timeout(Duration(milliseconds: _clientSideTimeoutMs));

      if (result == null) {
        throw Exception('워핑 처리 결과가 null');
      }

      stopwatch.stop();

      return WarpAttemptResult.success(
        source: 'client',
        resultBytes: result,
        processingTime: stopwatch.elapsedMilliseconds,
      );

    } catch (e) {
      stopwatch.stop();
      return WarpAttemptResult.failure(
        source: 'client',
        error: e.toString(),
        processingTime: stopwatch.elapsedMilliseconds,
      );
    }
  }

  /// 클라이언트 사이드 프리셋 시도
  static Future<WarpAttemptResult> _attemptClientSidePreset(
    Uint8List imageBytes,
    List<Landmark> landmarks,
    String presetType,
  ) async {
    if (!WarpService.isEngineLoaded) {
      return WarpAttemptResult.failure(
        source: 'client',
        error: '워핑 엔진이 로드되지 않음 - 페이지를 새로고침하세요',
      );
    }

    final stopwatch = Stopwatch()..start();
    
    try {
      final imageDataMap = await WarpService.extractImageData(imageBytes)
          .timeout(Duration(milliseconds: _clientSideTimeoutMs ~/ 2));
      
      if (imageDataMap == null) {
        throw Exception('이미지 데이터 추출 실패');
      }

      final imageData = imageDataMap['data'] as Uint8List;
      final width = imageDataMap['width'] as int;
      final height = imageDataMap['height'] as int;

      final result = await WarpService.applyPreset(
        imageBytes: imageData,
        width: width,
        height: height,
        landmarks: landmarks,
        presetType: presetType,
      ).timeout(Duration(milliseconds: _clientSideTimeoutMs));

      if (result == null) {
        throw Exception('프리셋 처리 결과가 null');
      }

      stopwatch.stop();

      return WarpAttemptResult.success(
        source: 'client',
        resultBytes: result,
        processingTime: stopwatch.elapsedMilliseconds,
      );

    } catch (e) {
      stopwatch.stop();
      return WarpAttemptResult.failure(
        source: 'client',
        error: e.toString(),
        processingTime: stopwatch.elapsedMilliseconds,
      );
    }
  }

  /// 통계 정보 조회 (클라이언트 전용)
  static WarpStatistics getStatistics() {
    return WarpStatistics(
      totalAttempts: _totalAttempts,
      clientSuccessCount: _clientSuccessCount,
      clientFailureCount: _clientFailureCount,
      clientSuccessRate: _totalAttempts > 0 ? _clientSuccessCount / _totalAttempts : 0,
    );
  }

  /// 통계 초기화
  static void resetStatistics() {
    _clientSuccessCount = 0;
    _clientFailureCount = 0;
    _totalAttempts = 0;
  }

  /// 클라이언트 엔진 건강성 체크
  static Future<EngineHealthResult> checkEngineHealth() async {
    final result = EngineHealthResult();
    
    try {
      // 1. 엔진 로드 상태
      result.isLoaded = WarpService.isEngineLoaded;
      
      if (!result.isLoaded) {
        result.healthScore = 0;
        result.recommendation = '워핑 엔진이 로드되지 않았습니다. 페이지를 새로고침하세요.';
        return result;
      }

      // 2. 기본 기능 테스트 (더미 데이터 사용)
      final testImageData = Uint8List.fromList(List.filled(100 * 100 * 4, 128)); // 100x100 회색 이미지
      
      final testResult = await WarpService.applyWarp(
        imageBytes: testImageData,
        width: 100,
        height: 100,
        startX: 50,
        startY: 50,
        endX: 60,
        endY: 60,
        influenceRadius: 20,
        strength: 0.5,
        mode: WarpMode.pull,
      ).timeout(const Duration(seconds: 5));

      if (testResult != null) {
        result.basicFunctionWorking = true;
        result.healthScore = 100;
        result.recommendation = '워핑 엔진이 정상 작동합니다.';
      } else {
        result.basicFunctionWorking = false;
        result.healthScore = 30;
        result.recommendation = '워핑 엔진에 문제가 있습니다. 페이지를 새로고침하세요.';
      }

    } catch (e) {
      result.basicFunctionWorking = false;
      result.healthScore = 10;
      result.recommendation = '워핑 엔진 테스트 실패: $e';
    }

    return result;
  }

  /// 자동 최적화 추천 (클라이언트 전용)
  static OptimizationRecommendation getOptimizationRecommendation() {
    final stats = getStatistics();
    final recommendation = OptimizationRecommendation();
    
    if (stats.totalAttempts < 5) {
      recommendation.message = '데이터가 부족합니다. 더 많은 워핑을 시도해보세요.';
      recommendation.priority = RecommendationPriority.low;
      return recommendation;
    }

    if (stats.clientSuccessRate < 0.7) {
      recommendation.message = '클라이언트 워핑 성공률이 낮습니다 (${(stats.clientSuccessRate * 100).toStringAsFixed(1)}%). 브라우저 성능을 확인하거나 이미지 크기를 줄여보세요.';
      recommendation.priority = RecommendationPriority.high;
    } else if (stats.clientSuccessRate < 0.9) {
      recommendation.message = '클라이언트 워핑이 가끔 실패합니다 (${(stats.clientSuccessRate * 100).toStringAsFixed(1)}%). 영향 반경을 작게 설정하거나 강도를 낮춰보세요.';
      recommendation.priority = RecommendationPriority.medium;
    } else {
      recommendation.message = '워핑 성능이 우수합니다 (${(stats.clientSuccessRate * 100).toStringAsFixed(1)}% 성공률). 현재 설정을 유지하세요.';
      recommendation.priority = RecommendationPriority.low;
    }

    return recommendation;
  }
}

/// 워핑 파라미터 클래스
class WarpParameters {
  final double startX;
  final double startY;
  final double endX;
  final double endY;
  final double influenceRadius;
  final double strength;
  final WarpMode mode;

  WarpParameters({
    required this.startX,
    required this.startY,
    required this.endX,
    required this.endY,
    required this.influenceRadius,
    required this.strength,
    required this.mode,
  });
}

/// 워핑 시도 결과
class WarpAttemptResult {
  final bool success;
  final String source; // 'client' 전용
  final Uint8List? resultBytes;
  final int processingTime;
  final String? error;
  final int attempts;

  WarpAttemptResult({
    required this.success,
    required this.source,
    this.resultBytes,
    this.processingTime = 0,
    this.error,
    this.attempts = 1,
  });

  factory WarpAttemptResult.success({
    required String source,
    required Uint8List resultBytes,
    int processingTime = 0,
    int attempts = 1,
  }) {
    return WarpAttemptResult(
      success: true,
      source: source,
      resultBytes: resultBytes,
      processingTime: processingTime,
      attempts: attempts,
    );
  }

  factory WarpAttemptResult.failure({
    required String source,
    required String error,
    int processingTime = 0,
    int attempts = 1,
  }) {
    return WarpAttemptResult(
      success: false,
      source: source,
      error: error,
      processingTime: processingTime,
      attempts: attempts,
    );
  }
}

/// 워핑 통계 (클라이언트 전용)
class WarpStatistics {
  final int totalAttempts;
  final int clientSuccessCount;
  final int clientFailureCount;
  final double clientSuccessRate;

  WarpStatistics({
    required this.totalAttempts,
    required this.clientSuccessCount,
    required this.clientFailureCount,
    required this.clientSuccessRate,
  });

  Map<String, dynamic> toJson() {
    return {
      'totalAttempts': totalAttempts,
      'clientSuccessCount': clientSuccessCount,
      'clientFailureCount': clientFailureCount,
      'clientSuccessRate': clientSuccessRate,
    };
  }
}

/// 엔진 건강성 결과
class EngineHealthResult {
  bool isLoaded = false;
  bool basicFunctionWorking = false;
  int healthScore = 0; // 0-100
  String recommendation = '';

  Map<String, dynamic> toJson() {
    return {
      'isLoaded': isLoaded,
      'basicFunctionWorking': basicFunctionWorking,
      'healthScore': healthScore,
      'recommendation': recommendation,
    };
  }
}

/// 최적화 추천
class OptimizationRecommendation {
  String message = '';
  RecommendationPriority priority = RecommendationPriority.low;

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      'priority': priority.name,
    };
  }
}

enum RecommendationPriority { low, medium, high }