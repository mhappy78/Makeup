import 'package:flutter/foundation.dart';
import 'dart:typed_data';
import 'dart:async';
import 'warp_service.dart';
import 'api_service.dart';
import '../models/app_state.dart';

/// 워핑 폴백 관리자 - 클라이언트 실패 시 백엔드로 자동 전환
class WarpFallbackManager {
  static const int _maxRetries = 2;
  static const Duration _retryDelay = Duration(milliseconds: 500);
  static const int _clientSideTimeoutMs = 10000; // 10초 타임아웃
  
  // 통계 데이터
  static int _clientSuccessCount = 0;
  static int _clientFailureCount = 0;
  static int _backendFallbackCount = 0;
  static int _totalAttempts = 0;
  
  /// 스마트 워핑 적용 - 클라이언트 우선, 실패 시 백엔드 폴백
  /// 
  /// [imageBytes] - 이미지 데이터
  /// [imageId] - 백엔드 이미지 ID (폴백용)
  /// [warpParams] - 워핑 파라미터
  /// 
  /// Returns: {success: bool, result: WarpResult?, source: 'client'|'backend', error: String?}
  static Future<WarpAttemptResult> smartApplyWarp({
    required Uint8List imageBytes,
    required String imageId,
    required WarpParameters warpParams,
    required ApiService apiService,
  }) async {
    _totalAttempts++;
    
    
    // 1. 클라이언트 사이드 시도
    final clientResult = await _attemptClientSideWarp(imageBytes, warpParams);
    
    if (clientResult.success) {
      _clientSuccessCount++;
      return clientResult;
    }
    
    _clientFailureCount++;
    
    // 2. 백엔드 폴백
    _backendFallbackCount++;
    final backendResult = await _attemptBackendWarp(imageId, warpParams, apiService);
    
    if (backendResult.success) {
      debugPrint('✅ 백엔드 폴백 성공 (${backendResult.processingTime}ms)');
    } else {
      debugPrint('❌ 백엔드 폴백도 실패: ${backendResult.error}');
    }
    
    return backendResult;
  }

  /// 스마트 프리셋 적용
  static Future<WarpAttemptResult> smartApplyPreset({
    required Uint8List imageBytes,
    required String imageId,
    required List<Landmark> landmarks,
    required String presetType,
    required ApiService apiService,
  }) async {
    _totalAttempts++;
    
    
    // 1. 클라이언트 사이드 시도
    final clientResult = await _attemptClientSidePreset(imageBytes, landmarks, presetType);
    
    if (clientResult.success) {
      _clientSuccessCount++;
      return clientResult;
    }
    
    _clientFailureCount++;
    
    // 2. 백엔드 폴백
    _backendFallbackCount++;
    final backendResult = await _attemptBackendPreset(imageId, presetType, apiService);
    
    if (backendResult.success) {
    } else {
    }
    
    return backendResult;
  }

  /// 클라이언트 사이드 워핑 시도
  static Future<WarpAttemptResult> _attemptClientSideWarp(
    Uint8List imageBytes,
    WarpParameters params,
  ) async {
    if (!WarpService.isEngineLoaded) {
      return WarpAttemptResult.failure(
        source: 'client',
        error: '워핑 엔진이 로드되지 않음',
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

      // JavaScript에서 이미 JPEG로 변환된 바이트를 받음
      final convertedImage = result;
      
      stopwatch.stop();

      return WarpAttemptResult.success(
        source: 'client',
        resultBytes: convertedImage,
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
        error: '워핑 엔진이 로드되지 않음',
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

      // JavaScript에서 이미 JPEG로 변환된 바이트를 받음
      final convertedImage = result;
      
      stopwatch.stop();

      return WarpAttemptResult.success(
        source: 'client',
        resultBytes: convertedImage,
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

  /// 백엔드 워핑 시도 (재시도 로직 포함)
  static Future<WarpAttemptResult> _attemptBackendWarp(
    String imageId,
    WarpParameters params,
    ApiService apiService,
  ) async {
    for (int attempt = 1; attempt <= _maxRetries; attempt++) {
      final stopwatch = Stopwatch()..start();
      
      try {
        final request = WarpRequest(
          imageId: imageId,
          startX: params.startX,
          startY: params.startY,
          endX: params.endX,
          endY: params.endY,
          influenceRadius: params.influenceRadius,
          strength: params.strength,
          mode: params.mode.value,
        );
        
        final response = await apiService.warpImage(request);

        stopwatch.stop();

        return WarpAttemptResult.success(
          source: 'backend',
          resultBytes: response.imageBytes,
          resultImageId: response.imageId,
          processingTime: stopwatch.elapsedMilliseconds,
          attempts: attempt,
        );

      } catch (e) {
        stopwatch.stop();
        
        if (attempt < _maxRetries) {
          await Future.delayed(_retryDelay);
          continue;
        }
        
        return WarpAttemptResult.failure(
          source: 'backend',
          error: e.toString(),
          processingTime: stopwatch.elapsedMilliseconds,
          attempts: attempt,
        );
      }
    }

    return WarpAttemptResult.failure(
      source: 'backend',
      error: '최대 재시도 횟수 초과',
    );
  }

  /// 백엔드 프리셋 시도 (재시도 로직 포함)
  static Future<WarpAttemptResult> _attemptBackendPreset(
    String imageId,
    String presetType,
    ApiService apiService,
  ) async {
    for (int attempt = 1; attempt <= _maxRetries; attempt++) {
      final stopwatch = Stopwatch()..start();
      
      try {
        final response = await apiService.applyPreset(imageId, presetType);
        stopwatch.stop();

        return WarpAttemptResult.success(
          source: 'backend',
          resultBytes: response.imageBytes,
          resultImageId: response.imageId,
          processingTime: stopwatch.elapsedMilliseconds,
          attempts: attempt,
        );

      } catch (e) {
        stopwatch.stop();
        
        if (attempt < _maxRetries) {
          await Future.delayed(_retryDelay);
          continue;
        }
        
        return WarpAttemptResult.failure(
          source: 'backend',
          error: e.toString(),
          processingTime: stopwatch.elapsedMilliseconds,
          attempts: attempt,
        );
      }
    }

    return WarpAttemptResult.failure(
      source: 'backend',
      error: '최대 재시도 횟수 초과',
    );
  }

  /// 통계 정보 조회
  static WarpStatistics getStatistics() {
    return WarpStatistics(
      totalAttempts: _totalAttempts,
      clientSuccessCount: _clientSuccessCount,
      clientFailureCount: _clientFailureCount,
      backendFallbackCount: _backendFallbackCount,
      clientSuccessRate: _totalAttempts > 0 ? _clientSuccessCount / _totalAttempts : 0,
      fallbackRate: _totalAttempts > 0 ? _backendFallbackCount / _totalAttempts : 0,
    );
  }

  /// 통계 초기화
  static void resetStatistics() {
    _clientSuccessCount = 0;
    _clientFailureCount = 0;
    _backendFallbackCount = 0;
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
        result.recommendation = '워핑 엔진에 문제가 있습니다. 백엔드 워핑 사용을 권장합니다.';
      }

    } catch (e) {
      result.basicFunctionWorking = false;
      result.healthScore = 10;
      result.recommendation = '워핑 엔진 테스트 실패: $e';
    }

    return result;
  }

  /// 자동 최적화 추천
  static OptimizationRecommendation getOptimizationRecommendation() {
    final stats = getStatistics();
    final recommendation = OptimizationRecommendation();
    
    if (stats.totalAttempts < 5) {
      recommendation.message = '데이터가 부족합니다. 더 많은 워핑을 시도해보세요.';
      recommendation.priority = RecommendationPriority.low;
      return recommendation;
    }

    if (stats.clientSuccessRate < 0.5) {
      recommendation.message = '클라이언트 워핑 성공률이 낮습니다 (${(stats.clientSuccessRate * 100).toStringAsFixed(1)}%). 브라우저 성능을 확인하거나 백엔드 워핑을 우선 사용하세요.';
      recommendation.priority = RecommendationPriority.high;
      recommendation.suggestBackendFirst = true;
    } else if (stats.clientSuccessRate < 0.8) {
      recommendation.message = '클라이언트 워핑이 가끔 실패합니다 (${(stats.clientSuccessRate * 100).toStringAsFixed(1)}%). 이미지 크기를 줄이거나 영향 반경을 작게 설정해보세요.';
      recommendation.priority = RecommendationPriority.medium;
    } else {
      recommendation.message = '워핑 성능이 양호합니다 (${(stats.clientSuccessRate * 100).toStringAsFixed(1)}% 성공률). 현재 설정을 유지하세요.';
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
  final String source; // 'client' 또는 'backend'
  final Uint8List? resultBytes;
  final String? resultImageId;
  final int processingTime;
  final String? error;
  final int attempts;

  WarpAttemptResult({
    required this.success,
    required this.source,
    this.resultBytes,
    this.resultImageId,
    this.processingTime = 0,
    this.error,
    this.attempts = 1,
  });

  factory WarpAttemptResult.success({
    required String source,
    required Uint8List resultBytes,
    String? resultImageId,
    int processingTime = 0,
    int attempts = 1,
  }) {
    return WarpAttemptResult(
      success: true,
      source: source,
      resultBytes: resultBytes,
      resultImageId: resultImageId,
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

/// 워핑 통계
class WarpStatistics {
  final int totalAttempts;
  final int clientSuccessCount;
  final int clientFailureCount;
  final int backendFallbackCount;
  final double clientSuccessRate;
  final double fallbackRate;

  WarpStatistics({
    required this.totalAttempts,
    required this.clientSuccessCount,
    required this.clientFailureCount,
    required this.backendFallbackCount,
    required this.clientSuccessRate,
    required this.fallbackRate,
  });

  Map<String, dynamic> toJson() {
    return {
      'totalAttempts': totalAttempts,
      'clientSuccessCount': clientSuccessCount,
      'clientFailureCount': clientFailureCount,
      'backendFallbackCount': backendFallbackCount,
      'clientSuccessRate': clientSuccessRate,
      'fallbackRate': fallbackRate,
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
  bool suggestBackendFirst = false;

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      'priority': priority.name,
      'suggestBackendFirst': suggestBackendFirst,
    };
  }
}

enum RecommendationPriority { low, medium, high }