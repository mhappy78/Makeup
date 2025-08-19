import 'dart:typed_data';
import 'dart:js' as js;
import 'dart:html' as html;
import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../models/app_state.dart';

/// JavaScript 워핑 엔진과의 안전한 인터페이스
class WarpService {
  static const String _jsWarpFunction = 'applyWarpTransformation';
  static const String _jsPresetFunction = 'applyPresetTransformation';
  
  /// JavaScript 워핑 엔진이 로드되었는지 확인
  static bool get isEngineLoaded {
    try {
      return js.context.hasProperty('warpEngine') && 
             js.context.hasProperty(_jsWarpFunction);
    } catch (e) {
      debugPrint('워핑 엔진 로드 확인 실패: $e');
      return false;
    }
  }

  /// 워핑 변형 적용
  /// 
  /// [imageBytes] - 원본 이미지 바이트 (RGBA 형식)
  /// [width] - 이미지 너비
  /// [height] - 이미지 높이  
  /// [startX] - 시작 X 좌표
  /// [startY] - 시작 Y 좌표
  /// [endX] - 끝 X 좌표
  /// [endY] - 끝 Y 좌표
  /// [influenceRadius] - 영향 반경 (픽셀)
  /// [strength] - 변형 강도 (0.0 ~ 1.0)
  /// [mode] - 워핑 모드 ('pull', 'push', 'expand', 'shrink')
  /// 
  /// Returns: 변형된 이미지 바이트 또는 null (실패 시)
  static Future<Uint8List?> applyWarp({
    required Uint8List imageBytes,
    required int width,
    required int height,
    required double startX,
    required double startY,
    required double endX,
    required double endY,
    required double influenceRadius,
    required double strength,
    required WarpMode mode,
  }) async {
    if (!isEngineLoaded) {
      debugPrint('워핑 엔진이 로드되지 않았습니다');
      return null;
    }

    try {
      // Dart WarpMode enum을 JavaScript 문자열로 변환
      final modeString = _warpModeToString(mode);
      
      // 성능 측정 시작
      final stopwatch = Stopwatch()..start();
      
      // JavaScript 함수 호출
      final result = js.context.callMethod(_jsWarpFunction, [
        imageBytes,           // Uint8List -> JavaScript Array
        width,
        height,
        startX,
        startY,
        endX,
        endY,
        influenceRadius,
        strength,
        modeString,
      ]);

      stopwatch.stop();

      // JavaScript 결과를 Dart Uint8List로 변환
      if (result != null) {
        final List<dynamic> resultList = result;
        final jpegBytes = Uint8List.fromList(resultList.cast<int>());
        return jpegBytes;
      } else {
        debugPrint('워핑 처리 결과가 null입니다');
        return null;
      }
    } catch (e, stackTrace) {
      debugPrint('워핑 적용 실패: $e');
      debugPrint('스택 트레이스: $stackTrace');
      return null;
    }
  }

  /// 프리셋 변형 적용
  /// 
  /// [imageBytes] - 원본 이미지 바이트
  /// [width] - 이미지 너비
  /// [height] - 이미지 높이
  /// [landmarks] - 468개 얼굴 랜드마크 리스트
  /// [presetType] - 프리셋 타입
  /// 
  /// Returns: 변형된 이미지 바이트 또는 null (실패 시)
  static Future<Uint8List?> applyPreset({
    required Uint8List imageBytes,
    required int width,
    required int height,
    required List<Landmark> landmarks,
    required String presetType,
  }) async {
    if (!isEngineLoaded) {
      debugPrint('워핑 엔진이 로드되지 않았습니다');
      return null;
    }

    try {
      // 랜드마크를 JavaScript 배열 형식으로 변환
      final landmarkArray = landmarks.map((landmark) => [landmark.x, landmark.y]).toList();
      
      
      // JavaScript Array로 명시적으로 변환
      final jsLandmarkArray = js.JsArray.from(
        landmarkArray.map((landmark) => js.JsArray.from(landmark)).toList()
      );
      
      final stopwatch = Stopwatch()..start();
      
      final result = js.context.callMethod(_jsPresetFunction, [
        imageBytes,
        width,
        height,
        jsLandmarkArray,
        presetType,
      ]);

      stopwatch.stop();

      if (result != null) {
        final List<dynamic> resultList = result;
        return Uint8List.fromList(resultList.cast<int>());
      } else {
        debugPrint('프리셋 처리 결과가 null입니다');
        return null;
      }
    } catch (e, stackTrace) {
      debugPrint('프리셋 적용 실패: $e');
      debugPrint('스택 트레이스: $stackTrace');
      return null;
    }
  }

  /// Canvas에서 ImageData 추출
  /// 
  /// [imageBytes] - Flutter Image 위젯의 이미지 바이트
  /// 
  /// Returns: {data: Uint8List, width: int, height: int} 또는 null
  static Future<Map<String, dynamic>?> extractImageData(Uint8List imageBytes) async {
    try {
      // HTML Image 요소 생성
      final img = html.ImageElement();
      final blob = html.Blob([imageBytes]);
      final url = html.Url.createObjectUrlFromBlob(blob);
      
      // 이미지 로드 완료를 기다림
      final completer = Completer<Map<String, dynamic>?>();
      
      img.onLoad.listen((_) {
        try {
          // Canvas에 이미지 그리기
          final canvas = html.CanvasElement();
          final ctx = canvas.getContext('2d') as html.CanvasRenderingContext2D;
          
          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
          ctx.drawImage(img, 0, 0);
          
          // ImageData 추출
          final imageData = ctx.getImageData(0, 0, canvas.width!, canvas.height!);
          final uint8Data = Uint8List.fromList(imageData.data);
          
          // URL 해제
          html.Url.revokeObjectUrl(url);
          
          completer.complete({
            'data': uint8Data,
            'width': canvas.width!,
            'height': canvas.height!,
          });
        } catch (e) {
          debugPrint('ImageData 추출 실패: $e');
          html.Url.revokeObjectUrl(url);
          completer.complete(null);
        }
      });
      
      img.onError.listen((_) {
        debugPrint('이미지 로드 실패');
        html.Url.revokeObjectUrl(url);
        completer.complete(null);
      });
      
      img.src = url;
      return await completer.future;
    } catch (e) {
      debugPrint('extractImageData 실패: $e');
      return null;
    }
  }

  /// ImageData를 Uint8List로 변환 (JPEG/PNG 형식)
  /// 
  /// [imageData] - RGBA 이미지 데이터
  /// [width] - 이미지 너비
  /// [height] - 이미지 높이
  /// [format] - 출력 형식 ('image/jpeg' 또는 'image/png')
  /// [quality] - JPEG 품질 (0.0 ~ 1.0, JPEG만 해당)
  /// 
  /// Returns: 인코딩된 이미지 바이트
  static Future<Uint8List?> imageDataToBytes({
    required Uint8List imageData,
    required int width,
    required int height,
    String format = 'image/jpeg',
    double quality = 0.95,
  }) async {
    // 이 함수는 더 이상 사용되지 않음
    // JavaScript에서 직접 JPEG로 변환하여 반환
    debugPrint('⚠️ imageDataToBytes는 더 이상 사용되지 않습니다');
    return imageData;
  }

  /// WarpMode enum을 JavaScript 문자열로 변환
  static String _warpModeToString(WarpMode mode) {
    switch (mode) {
      case WarpMode.pull:
        return 'pull';
      case WarpMode.push:
        return 'push';
      case WarpMode.expand:
        return 'expand';
      case WarpMode.shrink:
        return 'shrink';
    }
  }

  /// 워핑 엔진 초기화 상태 확인 및 대기
  /// 
  /// [timeoutSeconds] - 최대 대기 시간 (초)
  /// 
  /// Returns: 초기화 성공 여부
  static Future<bool> waitForEngineLoad({int timeoutSeconds = 5}) async {
    final startTime = DateTime.now();
    
    while (DateTime.now().difference(startTime).inSeconds < timeoutSeconds) {
      if (isEngineLoaded) {
        return true;
      }
      
      await Future.delayed(const Duration(milliseconds: 100));
    }
    
    debugPrint('워핑 엔진 로드 시간 초과 (${timeoutSeconds}초)');
    return false;
  }

  /// 성능 벤치마크 실행
  /// 
  /// [imageBytes] - 테스트 이미지
  /// [width] - 이미지 너비
  /// [height] - 이미지 높이
  /// 
  /// Returns: 벤치마크 결과 맵
  static Future<Map<String, dynamic>> runBenchmark({
    required Uint8List imageBytes,
    required int width,
    required int height,
  }) async {
    final results = <String, dynamic>{};
    
    if (!isEngineLoaded) {
      results['error'] = '워핑 엔진이 로드되지 않았습니다';
      return results;
    }

    try {
      // 워핑 모드별 성능 측정
      for (final mode in WarpMode.values) {
        final stopwatch = Stopwatch()..start();
        
        final result = await applyWarp(
          imageBytes: imageBytes,
          width: width,
          height: height,
          startX: width * 0.3,
          startY: height * 0.3,
          endX: width * 0.7,
          endY: height * 0.7,
          influenceRadius: width * 0.1,
          strength: 0.5,
          mode: mode,
        );
        
        stopwatch.stop();
        
        results['${mode.value}_ms'] = stopwatch.elapsedMilliseconds;
        results['${mode.value}_success'] = result != null;
      }
      
      // 프리셋 성능 측정 (랜드마크가 필요하므로 스킵)
      results['total_modes'] = WarpMode.values.length;
      results['engine_loaded'] = true;
      
    } catch (e) {
      results['error'] = e.toString();
    }
    
    return results;
  }
}

/// 데이터 변환 유틸리티
class ImageDataConverter {
  /// Flutter Image.memory에서 RGBA 데이터 추출
  static Future<Map<String, dynamic>?> fromFlutterImage(Uint8List imageBytes) async {
    return await WarpService.extractImageData(imageBytes);
  }
  
  /// RGBA 데이터를 Flutter에서 사용할 수 있는 형식으로 변환
  static Future<Uint8List?> toFlutterImage({
    required Uint8List rgbaData,
    required int width,
    required int height,
  }) async {
    return await WarpService.imageDataToBytes(
      imageData: rgbaData,
      width: width,
      height: height,
      format: 'image/jpeg',
      quality: 0.95,
    );
  }
}