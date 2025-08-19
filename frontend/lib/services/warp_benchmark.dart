import 'package:flutter/foundation.dart';
import 'dart:typed_data';
import 'dart:math' as math;
import 'warp_service.dart';
import '../models/app_state.dart';

/// 워핑 성능 벤치마크 서비스
class WarpBenchmark {
  static const int _defaultIterations = 10;
  static const List<WarpMode> _testModes = WarpMode.values;
  
  /// 벤치마크 결과 모델
  static const List<String> _testPresets = [
    'lower_jaw',
    'middle_jaw', 
    'cheek',
    'front_protusion',
    'back_slit'
  ];

  /// 종합 성능 벤치마크 실행
  /// 
  /// [imageBytes] - 테스트 이미지 (JPEG/PNG 형식)
  /// [iterations] - 각 테스트 반복 횟수
  /// 
  /// Returns: 상세 벤치마크 결과
  static Future<BenchmarkReport> runComprehensiveBenchmark({
    required Uint8List imageBytes,
    int iterations = _defaultIterations,
  }) async {
    final report = BenchmarkReport();
    
    debugPrint('=== BeautyGen 워핑 성능 벤치마크 시작 ===');
    debugPrint('이미지 크기: ${imageBytes.length} bytes');
    debugPrint('반복 횟수: $iterations');
    
    try {
      // 1. 엔진 로드 테스트
      report.engineLoadTime = await _measureEngineLoadTime();
      
      // 2. 이미지 데이터 추출 성능
      final imageDataResult = await _measureImageDataExtraction(imageBytes);
      report.imageExtractionTime = imageDataResult.extractionTime;
      
      if (imageDataResult.imageData == null) {
        report.addError('이미지 데이터 추출 실패');
        return report;
      }
      
      final imageData = imageDataResult.imageData!;
      final width = imageDataResult.width;
      final height = imageDataResult.height;
      
      debugPrint('추출된 이미지: ${width}x${height}');
      
      // 3. 워핑 모드별 성능 테스트
      for (final mode in _testModes) {
        final modeResult = await _measureWarpModePerformance(
          imageData: imageData,
          width: width,
          height: height,
          mode: mode,
          iterations: iterations,
        );
        report.warpModeResults[mode] = modeResult;
      }
      
      // 4. 프리셋 성능 테스트 (랜드마크가 필요하므로 더미 데이터 사용)
      final dummyLandmarks = _generateDummyLandmarks(width, height);
      for (final preset in _testPresets) {
        final presetResult = await _measurePresetPerformance(
          imageData: imageData,
          width: width,
          height: height,
          landmarks: dummyLandmarks,
          presetType: preset,
          iterations: math.min(iterations, 3), // 프리셋은 더 적은 반복
        );
        report.presetResults[preset] = presetResult;
      }
      
      // 5. 메모리 사용량 추정
      report.memoryUsage = _estimateMemoryUsage(width, height);
      
      // 6. 종합 점수 계산
      report.calculateOverallScore();
      
    } catch (e, stackTrace) {
      report.addError('벤치마크 실행 실패: $e');
      debugPrint('벤치마크 에러: $e');
      debugPrint('스택 트레이스: $stackTrace');
    }
    
    debugPrint('=== 벤치마크 완료 ===');
    debugPrint('전체 소요 시간: ${report.totalTime}ms');
    debugPrint('종합 점수: ${report.overallScore}/100');
    
    return report;
  }

  /// 엔진 로드 시간 측정
  static Future<int> _measureEngineLoadTime() async {
    final stopwatch = Stopwatch()..start();
    
    if (WarpService.isEngineLoaded) {
      stopwatch.stop();
      return stopwatch.elapsedMilliseconds;
    }
    
    final isLoaded = await WarpService.waitForEngineLoad(timeoutSeconds: 10);
    stopwatch.stop();
    
    if (!isLoaded) {
      throw Exception('워핑 엔진 로드 실패');
    }
    
    return stopwatch.elapsedMilliseconds;
  }

  /// 이미지 데이터 추출 성능 측정
  static Future<_ImageDataResult> _measureImageDataExtraction(Uint8List imageBytes) async {
    final stopwatch = Stopwatch()..start();
    
    try {
      final result = await WarpService.extractImageData(imageBytes);
      stopwatch.stop();
      
      if (result == null) {
        return _ImageDataResult(
          extractionTime: stopwatch.elapsedMilliseconds,
          imageData: null,
          width: 0,
          height: 0,
        );
      }
      
      return _ImageDataResult(
        extractionTime: stopwatch.elapsedMilliseconds,
        imageData: result['data'] as Uint8List,
        width: result['width'] as int,
        height: result['height'] as int,
      );
    } catch (e) {
      stopwatch.stop();
      return _ImageDataResult(
        extractionTime: stopwatch.elapsedMilliseconds,
        imageData: null,
        width: 0,
        height: 0,
      );
    }
  }

  /// 워핑 모드별 성능 측정
  static Future<WarpModeResult> _measureWarpModePerformance({
    required Uint8List imageData,
    required int width,
    required int height,
    required WarpMode mode,
    required int iterations,
  }) async {
    final result = WarpModeResult(mode: mode);
    final times = <int>[];
    
    // 테스트 좌표 생성 (이미지 중앙 근처)
    final centerX = width * 0.5;
    final centerY = height * 0.5;
    final radius = math.min(width, height) * 0.2;
    
    for (int i = 0; i < iterations; i++) {
      try {
        // 랜덤 시작/끝 점 생성
        final angle = (i / iterations) * 2 * math.pi;
        final startX = centerX + math.cos(angle) * radius * 0.5;
        final startY = centerY + math.sin(angle) * radius * 0.5;
        final endX = centerX + math.cos(angle) * radius;
        final endY = centerY + math.sin(angle) * radius;
        
        final stopwatch = Stopwatch()..start();
        
        final warpResult = await WarpService.applyWarp(
          imageBytes: imageData,
          width: width,
          height: height,
          startX: startX,
          startY: startY,
          endX: endX,
          endY: endY,
          influenceRadius: radius,
          strength: 0.5,
          mode: mode,
        );
        
        stopwatch.stop();
        times.add(stopwatch.elapsedMilliseconds);
        
        if (warpResult == null) {
          result.failureCount++;
        } else {
          result.successCount++;
        }
        
      } catch (e) {
        result.failureCount++;
        result.errors.add('반복 ${i + 1}: $e');
      }
    }
    
    if (times.isNotEmpty) {
      result.averageTime = times.reduce((a, b) => a + b) / times.length;
      result.minTime = times.reduce(math.min);
      result.maxTime = times.reduce(math.max);
      result.medianTime = _calculateMedian(times);
    }
    
    return result;
  }

  /// 프리셋 성능 측정
  static Future<PresetResult> _measurePresetPerformance({
    required Uint8List imageData,
    required int width,
    required int height,
    required List<Landmark> landmarks,
    required String presetType,
    required int iterations,
  }) async {
    final result = PresetResult(presetType: presetType);
    final times = <int>[];
    
    for (int i = 0; i < iterations; i++) {
      try {
        final stopwatch = Stopwatch()..start();
        
        final presetResult = await WarpService.applyPreset(
          imageBytes: imageData,
          width: width,
          height: height,
          landmarks: landmarks,
          presetType: presetType,
        );
        
        stopwatch.stop();
        times.add(stopwatch.elapsedMilliseconds);
        
        if (presetResult == null) {
          result.failureCount++;
        } else {
          result.successCount++;
        }
        
      } catch (e) {
        result.failureCount++;
        result.errors.add('반복 ${i + 1}: $e');
      }
    }
    
    if (times.isNotEmpty) {
      result.averageTime = times.reduce((a, b) => a + b) / times.length;
      result.minTime = times.reduce(math.min);
      result.maxTime = times.reduce(math.max);
    }
    
    return result;
  }

  /// 더미 랜드마크 생성 (468개)
  static List<Landmark> _generateDummyLandmarks(int width, int height) {
    final landmarks = <Landmark>[];
    
    for (int i = 0; i < 468; i++) {
      // 얼굴 영역 내에 랜덤 좌표 생성
      final x = width * (0.3 + 0.4 * math.Random().nextDouble());
      final y = height * (0.2 + 0.6 * math.Random().nextDouble());
      
      landmarks.add(Landmark(x: x, y: y, index: i));
    }
    
    return landmarks;
  }

  /// 메모리 사용량 추정
  static MemoryUsage _estimateMemoryUsage(int width, int height) {
    final pixelCount = width * height;
    final rgbaBytes = pixelCount * 4; // RGBA
    final processingOverhead = rgbaBytes * 2; // 처리용 임시 버퍼
    
    return MemoryUsage(
      imageDataSize: rgbaBytes,
      processingOverhead: processingOverhead,
      totalEstimated: rgbaBytes + processingOverhead,
    );
  }

  /// 중앙값 계산
  static double _calculateMedian(List<int> values) {
    final sorted = List<int>.from(values)..sort();
    final length = sorted.length;
    
    if (length % 2 == 0) {
      return (sorted[length ~/ 2 - 1] + sorted[length ~/ 2]) / 2.0;
    } else {
      return sorted[length ~/ 2].toDouble();
    }
  }

  /// 빠른 성능 체크 (간단한 테스트)
  static Future<QuickBenchmarkResult> runQuickBenchmark({
    required Uint8List imageBytes,
  }) async {
    final result = QuickBenchmarkResult();
    
    try {
      // 엔진 로드 확인
      result.engineLoaded = WarpService.isEngineLoaded;
      if (!result.engineLoaded) {
        result.engineLoaded = await WarpService.waitForEngineLoad(timeoutSeconds: 3);
      }
      
      if (!result.engineLoaded) {
        result.recommendation = '워핑 엔진이 로드되지 않았습니다. 백엔드 워핑을 사용하세요.';
        return result;
      }
      
      // 이미지 데이터 추출 테스트
      final extractionResult = await _measureImageDataExtraction(imageBytes);
      result.imageExtractionTime = extractionResult.extractionTime;
      
      if (extractionResult.imageData == null) {
        result.recommendation = '이미지 처리 실패. 백엔드 워핑을 사용하세요.';
        return result;
      }
      
      // 단일 워핑 테스트
      final testResult = await _measureWarpModePerformance(
        imageData: extractionResult.imageData!,
        width: extractionResult.width,
        height: extractionResult.height,
        mode: WarpMode.pull,
        iterations: 1,
      );
      
      result.singleWarpTime = testResult.averageTime;
      result.warpSuccess = testResult.successCount > 0;
      
      // 추천사항 생성
      result.recommendation = _generateRecommendation(result);
      
    } catch (e) {
      result.recommendation = '테스트 실패: $e';
    }
    
    return result;
  }

  /// 성능 기반 추천사항 생성
  static String _generateRecommendation(QuickBenchmarkResult result) {
    if (!result.engineLoaded || !result.warpSuccess) {
      return '클라이언트 워핑 불가. 백엔드 워핑 사용 권장.';
    }
    
    if (result.singleWarpTime < 100) {
      return '⚡ 매우 빠름! 클라이언트 워핑 강력 권장.';
    } else if (result.singleWarpTime < 300) {
      return '✅ 양호함. 클라이언트 워핑 권장.';
    } else if (result.singleWarpTime < 1000) {
      return '⚠ 느림. 작은 이미지에서만 클라이언트 워핑 권장.';
    } else {
      return '🐌 매우 느림. 백엔드 워핑 권장.';
    }
  }
}

/// 이미지 데이터 추출 결과
class _ImageDataResult {
  final int extractionTime;
  final Uint8List? imageData;
  final int width;
  final int height;

  _ImageDataResult({
    required this.extractionTime,
    required this.imageData,
    required this.width,
    required this.height,
  });
}

/// 종합 벤치마크 결과
class BenchmarkReport {
  int engineLoadTime = 0;
  int imageExtractionTime = 0;
  final Map<WarpMode, WarpModeResult> warpModeResults = {};
  final Map<String, PresetResult> presetResults = {};
  MemoryUsage? memoryUsage;
  final List<String> errors = [];
  double overallScore = 0;

  int get totalTime {
    int total = engineLoadTime + imageExtractionTime;
    for (final result in warpModeResults.values) {
      total += (result.averageTime * result.successCount).round();
    }
    for (final result in presetResults.values) {
      total += (result.averageTime * result.successCount).round();
    }
    return total;
  }

  void addError(String error) {
    errors.add(error);
  }

  void calculateOverallScore() {
    if (errors.isNotEmpty) {
      overallScore = 0;
      return;
    }

    double score = 100;
    
    // 엔진 로드 시간 점수 (0-10점)
    if (engineLoadTime > 5000) score -= 10;
    else if (engineLoadTime > 2000) score -= 5;
    else if (engineLoadTime > 1000) score -= 2;
    
    // 워핑 성능 점수 (0-50점)
    double avgWarpTime = 0;
    int successfulModes = 0;
    for (final result in warpModeResults.values) {
      if (result.successCount > 0) {
        avgWarpTime += result.averageTime;
        successfulModes++;
      }
    }
    
    if (successfulModes > 0) {
      avgWarpTime /= successfulModes;
      if (avgWarpTime > 1000) score -= 30;
      else if (avgWarpTime > 500) score -= 20;
      else if (avgWarpTime > 200) score -= 10;
      else if (avgWarpTime > 100) score -= 5;
    } else {
      score -= 50; // 모든 워핑 실패
    }
    
    // 프리셋 성능 점수 (0-30점)
    double avgPresetTime = 0;
    int successfulPresets = 0;
    for (final result in presetResults.values) {
      if (result.successCount > 0) {
        avgPresetTime += result.averageTime;
        successfulPresets++;
      }
    }
    
    if (successfulPresets > 0) {
      avgPresetTime /= successfulPresets;
      if (avgPresetTime > 2000) score -= 30;
      else if (avgPresetTime > 1000) score -= 20;
      else if (avgPresetTime > 500) score -= 10;
      else if (avgPresetTime > 200) score -= 5;
    } else {
      score -= 30; // 모든 프리셋 실패
    }
    
    // 메모리 효율성 (0-10점)
    if (memoryUsage != null && memoryUsage!.totalEstimated > 50 * 1024 * 1024) {
      score -= 10; // 50MB 초과 시 감점
    }
    
    overallScore = math.max(0, score);
  }

  Map<String, dynamic> toJson() {
    return {
      'engineLoadTime': engineLoadTime,
      'imageExtractionTime': imageExtractionTime,
      'warpModeResults': warpModeResults.map((k, v) => MapEntry(k.value, v.toJson())),
      'presetResults': presetResults.map((k, v) => MapEntry(k, v.toJson())),
      'memoryUsage': memoryUsage?.toJson(),
      'errors': errors,
      'overallScore': overallScore,
      'totalTime': totalTime,
    };
  }
}

/// 워핑 모드별 결과
class WarpModeResult {
  final WarpMode mode;
  double averageTime = 0;
  int minTime = 0;
  int maxTime = 0;
  double medianTime = 0;
  int successCount = 0;
  int failureCount = 0;
  final List<String> errors = [];

  WarpModeResult({required this.mode});

  double get successRate => 
      (successCount + failureCount) > 0 ? successCount / (successCount + failureCount) : 0;

  Map<String, dynamic> toJson() {
    return {
      'mode': mode.value,
      'averageTime': averageTime,
      'minTime': minTime,
      'maxTime': maxTime,
      'medianTime': medianTime,
      'successCount': successCount,
      'failureCount': failureCount,
      'successRate': successRate,
      'errors': errors,
    };
  }
}

/// 프리셋 결과
class PresetResult {
  final String presetType;
  double averageTime = 0;
  int minTime = 0;
  int maxTime = 0;
  int successCount = 0;
  int failureCount = 0;
  final List<String> errors = [];

  PresetResult({required this.presetType});

  double get successRate => 
      (successCount + failureCount) > 0 ? successCount / (successCount + failureCount) : 0;

  Map<String, dynamic> toJson() {
    return {
      'presetType': presetType,
      'averageTime': averageTime,
      'minTime': minTime,
      'maxTime': maxTime,
      'successCount': successCount,
      'failureCount': failureCount,
      'successRate': successRate,
      'errors': errors,
    };
  }
}

/// 메모리 사용량
class MemoryUsage {
  final int imageDataSize;
  final int processingOverhead;
  final int totalEstimated;

  MemoryUsage({
    required this.imageDataSize,
    required this.processingOverhead,
    required this.totalEstimated,
  });

  String get imageDataSizeMB => (imageDataSize / 1024 / 1024).toStringAsFixed(2);
  String get totalEstimatedMB => (totalEstimated / 1024 / 1024).toStringAsFixed(2);

  Map<String, dynamic> toJson() {
    return {
      'imageDataSize': imageDataSize,
      'processingOverhead': processingOverhead,
      'totalEstimated': totalEstimated,
      'imageDataSizeMB': imageDataSizeMB,
      'totalEstimatedMB': totalEstimatedMB,
    };
  }
}

/// 빠른 벤치마크 결과
class QuickBenchmarkResult {
  bool engineLoaded = false;
  int imageExtractionTime = 0;
  double singleWarpTime = 0;
  bool warpSuccess = false;
  String recommendation = '';

  Map<String, dynamic> toJson() {
    return {
      'engineLoaded': engineLoaded,
      'imageExtractionTime': imageExtractionTime,
      'singleWarpTime': singleWarpTime,
      'warpSuccess': warpSuccess,
      'recommendation': recommendation,
    };
  }
}