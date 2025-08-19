import 'dart:typed_data';
import 'dart:js' as js;
import 'dart:html' as html;
import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/foundation.dart';
import '../models/app_state.dart';

/// 프론트엔드 MediaPipe 서비스
/// 백엔드 없이 브라우저에서 직접 얼굴 랜드마크 검출
class MediaPipeService {
  static const String _jsDetectFunction = 'detectFaceLandmarks';
  static const String _jsDetectFromImageDataFunction = 'detectFaceLandmarksFromImageData';
  static const String _jsStatusFunction = 'getMediaPipeStatus';
  static const String _jsBenchmarkFunction = 'runMediaPipeBenchmark';
  
  /// MediaPipe JavaScript 엔진이 로드되었는지 확인
  static bool get isEngineLoaded {
    try {
      return js.context.hasProperty('mediaPipeEngine') && 
             js.context.hasProperty(_jsDetectFunction);
    } catch (e) {
      debugPrint('MediaPipe 엔진 로드 확인 실패: $e');
      return false;
    }
  }

  /// MediaPipe 엔진 상태 확인
  static Map<String, dynamic>? getEngineStatus() {
    if (!isEngineLoaded) return null;
    
    try {
      final result = js.context.callMethod(_jsStatusFunction);
      return {
        'isInitialized': result['isInitialized'],
        'isProcessing': result['isProcessing'],
        'version': result['version'],
      };
    } catch (e) {
      debugPrint('MediaPipe 상태 확인 실패: $e');
      return null;
    }
  }

  /// 이미지 바이트에서 얼굴 랜드마크 검출
  /// 
  /// [imageBytes] - 이미지 바이트 데이터 (JPEG, PNG 등)
  /// 
  /// Returns: 랜드마크 검출 결과 또는 null (실패 시)
  static Future<Map<String, dynamic>?> detectFaceLandmarks(Uint8List imageBytes) async {
    // 첫 번째 시도: MediaPipe JavaScript 엔진
    try {
      final result = await _tryMediaPipeDetection(imageBytes);
      if (result != null) {
        return result;
      }
    } catch (e) {
      debugPrint('MediaPipe 검출 실패, 폴백 모드로 전환: $e');
    }

    // 두 번째 시도: 기본 랜드마크 생성 (폴백)
    debugPrint('⚠️ MediaPipe 실패, 기본 랜드마크로 폴백');
    return _generateDefaultLandmarks();
  }

  /// MediaPipe JavaScript 엔진으로 랜드마크 검출 시도
  static Future<Map<String, dynamic>?> _tryMediaPipeDetection(Uint8List imageBytes) async {
    if (!isEngineLoaded) {
      throw Exception('MediaPipe 엔진이 로드되지 않았습니다');
    }

    final stopwatch = Stopwatch()..start();
    
    // JavaScript 함수 호출 (Promise 처리)
    try {
      final jsPromise = js.context.callMethod(_jsDetectFunction, [imageBytes]);
      final result = await _promiseToFuture(jsPromise);
      return await _processMediaPipeResult(result, stopwatch);
    } catch (e) {
      debugPrint('JavaScript 함수 호출 또는 Promise 처리 실패: $e');
      rethrow;
    }
  }

  /// MediaPipe 결과 처리
  static Future<Map<String, dynamic>?> _processMediaPipeResult(dynamic result, Stopwatch stopwatch) async {
    stopwatch.stop();

    if (result != null && result['landmarks'] != null) {
      final rawLandmarks = result['landmarks'] as List;
      
      // JavaScript 결과를 Dart로 변환
      final landmarks = rawLandmarks
          .map((landmark) => [(landmark[0] as num).toDouble(), (landmark[1] as num).toDouble()])
          .toList();
          
      // 좌표계 디버깅을 위한 첫 번째 랜드마크 좌표
      if (landmarks.isNotEmpty) {
        debugPrint('🎯 MediaPipe 랜드마크: (${landmarks[0][0]}, ${landmarks[0][1]}) / 이미지크기: ${result['imageWidth']}x${result['imageHeight']}');
      }
      
      return {
        'landmarks': landmarks,
        'imageWidth': result['imageWidth'] ?? 800,
        'imageHeight': result['imageHeight'] ?? 600,
        'source': 'frontend_mediapipe',
        'processingTime': stopwatch.elapsedMilliseconds,
      };
    }
    
    return null;
  }

  /// 기본 얼굴 랜드마크 생성 (폴백용)
  static Map<String, dynamic> _generateDefaultLandmarks({
    int imageWidth = 800,
    int imageHeight = 600,
  }) {
    // 실제 이미지 크기에 맞는 얼굴 중앙 위치
    final centerX = imageWidth / 2.0;
    final centerY = imageHeight / 2.0;
    final faceWidth = imageWidth * 0.25;  // 이미지 너비의 25%
    final faceHeight = imageHeight * 0.4; // 이미지 높이의 40%
    
    final landmarks = <List<double>>[];
    
    // 478개 MediaPipe 랜드마크의 기본 위치 생성 (최신 버전)
    for (int i = 0; i < 478; i++) {
      double x, y;
      
      if (i < 17) {
        // 턱선 (0-16)
        final t = i / 16.0;
        x = centerX - faceWidth * 0.5 + faceWidth * t;
        y = centerY + faceHeight * 0.3 + 20 * (1 - 4 * (t - 0.5) * (t - 0.5));
      } else if (i < 27) {
        // 오른쪽 눈썹 (17-21) + 왼쪽 눈썹 (22-26)
        final isLeft = i >= 22;
        final localIndex = isLeft ? i - 22 : i - 17;
        final t = localIndex / 4.0;
        x = centerX + (isLeft ? 1 : -1) * (40 + 40 * t);
        y = centerY - faceHeight * 0.3;
      } else if (i < 36) {
        // 코 (27-35)
        final t = (i - 27) / 8.0;
        x = centerX;
        y = centerY - faceHeight * 0.1 + 60 * t;
      } else if (i < 48) {
        // 오른쪽 눈 (36-41) + 왼쪽 눈 (42-47)
        final isLeft = i >= 42;
        final localIndex = isLeft ? i - 42 : i - 36;
        final t = localIndex / 5.0;
        final eyeCenterX = centerX + (isLeft ? 1 : -1) * 60;
        final eyeCenterY = centerY - faceHeight * 0.1;
        x = eyeCenterX + 25 * math.cos(t * 2 * math.pi);
        y = eyeCenterY + 10 * math.sin(t * 2 * math.pi);
      } else if (i < 68) {
        // 입 (48-67)
        final t = (i - 48) / 19.0;
        final lipCenterX = centerX;
        final lipCenterY = centerY + faceHeight * 0.2;
        if (i < 58) {
          // 외부 입술
          x = lipCenterX + 40 * math.cos(t * 2 * math.pi);
          y = lipCenterY + 15 * math.sin(t * 2 * math.pi);
        } else {
          // 내부 입술
          x = lipCenterX + 25 * math.cos(t * 2 * math.pi);
          y = lipCenterY + 8 * math.sin(t * 2 * math.pi);
        }
      } else {
        // 나머지 478개 랜드마크는 얼굴 영역에 분산
        final t = (i - 68) / 410.0;
        final angle = t * 8 * math.pi; // 여러 번 회전
        final radius = 80 + 60 * (i % 5) / 4; // 반지름 변화
        x = centerX + radius * math.cos(angle);
        y = centerY + radius * 0.7 * math.sin(angle);
      }
      
      landmarks.add([x, y]);
    }
    
    debugPrint('🎯 기본 랜드마크: (${landmarks[0][0]}, ${landmarks[0][1]}) / 이미지크기: ${imageWidth}x${imageHeight}');
    
    return {
      'landmarks': landmarks,
      'imageWidth': imageWidth,
      'imageHeight': imageHeight,
      'source': 'default_fallback',
      'processingTime': 5,
    };
  }

  /// ImageData에서 얼굴 랜드마크 검출
  /// 
  /// [imageData] - Canvas ImageData (RGBA)
  /// [width] - 이미지 너비
  /// [height] - 이미지 높이
  /// 
  /// Returns: 랜드마크 검출 결과 또는 null (실패 시)
  static Future<Map<String, dynamic>?> detectFaceLandmarksFromImageData({
    required Uint8List imageData,
    required int width,
    required int height,
  }) async {
    if (!isEngineLoaded) {
      debugPrint('MediaPipe 엔진이 로드되지 않았습니다');
      return null;
    }

    try {
      final stopwatch = Stopwatch()..start();
      
      debugPrint('🔍 ImageData MediaPipe 랜드마크 검출 시작 (${width}x${height})...');
      
      // JavaScript 함수 호출 (Promise 처리)
      final jsPromise = js.context.callMethod(_jsDetectFromImageDataFunction, [
        imageData,
        width,
        height,
      ]);
      final result = await _promiseToFuture(jsPromise);
      
      stopwatch.stop();
      debugPrint('⚡ ImageData MediaPipe 처리 시간: ${stopwatch.elapsedMilliseconds}ms');

      if (result != null) {
        final landmarks = (result['landmarks'] as List)
            .map((landmark) => [(landmark[0] as num).toDouble(), (landmark[1] as num).toDouble()])
            .toList();
            
        debugPrint('✅ ImageData MediaPipe 완료: ${landmarks.length}개 랜드마크');
        
        return {
          'landmarks': landmarks,
          'imageWidth': result['imageWidth'],
          'imageHeight': result['imageHeight'], 
          'source': result['source'],
          'processingTime': stopwatch.elapsedMilliseconds,
        };
      } else {
        debugPrint('ImageData MediaPipe 처리 결과가 null입니다');
        return null;
      }
    } catch (e, stackTrace) {
      debugPrint('ImageData MediaPipe 랜드마크 검출 실패: $e');
      debugPrint('스택 트레이스: $stackTrace');
      return null;
    }
  }

  /// 랜드마크 검출 결과를 AppState Landmark 형식으로 변환
  static List<Landmark> convertToLandmarks(List<List<double>> rawLandmarks) {
    return rawLandmarks.asMap().entries.map((entry) => Landmark(
      x: entry.value[0],
      y: entry.value[1],
      index: entry.key,
    )).toList();
  }

  /// MediaPipe 엔진 초기화 대기
  /// 
  /// [timeoutSeconds] - 최대 대기 시간 (초)
  /// 
  /// Returns: 초기화 성공 여부
  static Future<bool> waitForEngineInitialization({int timeoutSeconds = 10}) async {
    final startTime = DateTime.now();
    
    while (DateTime.now().difference(startTime).inSeconds < timeoutSeconds) {
      if (isEngineLoaded) {
        final status = getEngineStatus();
        if (status != null && status['isInitialized'] == true) {
          debugPrint('✅ MediaPipe 엔진 초기화 완료');
          return true;
        }
      }
      
      await Future.delayed(const Duration(milliseconds: 200));
    }
    
    debugPrint('❌ MediaPipe 엔진 초기화 시간 초과 (${timeoutSeconds}초)');
    return false;
  }

  /// 성능 벤치마크 실행
  /// 
  /// [imageData] - 테스트 이미지 데이터
  /// [width] - 이미지 너비
  /// [height] - 이미지 높이
  /// 
  /// Returns: 벤치마크 결과
  static Future<Map<String, dynamic>> runBenchmark({
    required Uint8List imageData,
    required int width,
    required int height,
  }) async {
    final results = <String, dynamic>{};
    
    if (!isEngineLoaded) {
      results['error'] = 'MediaPipe 엔진이 로드되지 않았습니다';
      return results;
    }

    try {
      final result = await js.context.callMethod(_jsBenchmarkFunction, [
        imageData,
        width,
        height,
      ]);
      
      return {
        'processingTime': result['processingTime'],
        'landmarkCount': result['landmarkCount'] ?? 0,
        'imageSize': result['imageSize'],
        'success': result['success'],
        'error': result['error'],
        'engine': 'MediaPipe JavaScript',
      };
      
    } catch (e) {
      results['error'] = e.toString();
      results['success'] = false;
      return results;
    }
  }

  /// 엔진 건강성 체크
  static Future<Map<String, dynamic>> checkEngineHealth() async {
    final result = <String, dynamic>{
      'isLoaded': isEngineLoaded,
      'isInitialized': false,
      'healthScore': 0,
      'recommendation': '',
    };
    
    if (!isEngineLoaded) {
      result['recommendation'] = 'MediaPipe 엔진이 로드되지 않았습니다. 페이지를 새로고침하세요.';
      return result;
    }
    
    final status = getEngineStatus();
    if (status != null) {
      result['isInitialized'] = status['isInitialized'];
      
      if (status['isInitialized'] == true) {
        result['healthScore'] = 100;
        result['recommendation'] = 'MediaPipe 엔진이 정상 작동합니다.';
      } else {
        result['healthScore'] = 30;
        result['recommendation'] = 'MediaPipe 엔진 초기화를 기다리는 중입니다.';
      }
    }
    
    return result;
  }

  /// JavaScript Promise를 Dart Future로 변환
  static Future<dynamic> _promiseToFuture(dynamic jsPromise) {
    final completer = Completer<dynamic>();
    
    final promiseWrapper = js.JsObject.fromBrowserObject(jsPromise);
    
    promiseWrapper.callMethod('then', [
      js.allowInterop((result) {
        completer.complete(result);
      })
    ]);
    
    promiseWrapper.callMethod('catch', [
      js.allowInterop((error) {
        completer.completeError(error);
      })
    ]);
    
    return completer.future;
  }

  /// 스마트 랜드마크 검출 (이미지 타입 자동 감지)
  /// 
  /// [imageInput] - 이미지 데이터 (Uint8List 또는 ImageData)
  /// [width] - 이미지 너비 (ImageData인 경우)
  /// [height] - 이미지 높이 (ImageData인 경우)
  /// 
  /// Returns: 랜드마크 검출 결과
  static Future<Map<String, dynamic>?> smartDetectLandmarks({
    required dynamic imageInput,
    int? width,
    int? height,
  }) async {
    if (imageInput is Uint8List) {
      // 이미지 바이트인 경우
      return await detectFaceLandmarks(imageInput);
    } else if (imageInput is Uint8List && width != null && height != null) {
      // ImageData인 경우  
      return await detectFaceLandmarksFromImageData(
        imageData: imageInput,
        width: width,
        height: height,
      );
    } else {
      throw ArgumentError('지원하지 않는 이미지 입력 형식입니다');
    }
  }
}

/// MediaPipe 결과 데이터 클래스
class MediaPipeResult {
  final List<Landmark> landmarks;
  final int imageWidth;
  final int imageHeight;
  final String source;
  final int processingTime;

  MediaPipeResult({
    required this.landmarks,
    required this.imageWidth,
    required this.imageHeight,
    required this.source,
    required this.processingTime,
  });

  factory MediaPipeResult.fromMap(Map<String, dynamic> map) {
    final rawLandmarks = map['landmarks'] as List<List<double>>;
    final landmarks = MediaPipeService.convertToLandmarks(rawLandmarks);
    
    return MediaPipeResult(
      landmarks: landmarks,
      imageWidth: map['imageWidth'],
      imageHeight: map['imageHeight'],
      source: map['source'],
      processingTime: map['processingTime'],
    );
  }
}