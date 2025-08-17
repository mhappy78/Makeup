import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import '../models/app_state.dart';

/// API 서비스 클래스
class ApiService {
  late final Dio _dio;
  static const String baseUrl = 'http://localhost:8080';
  
  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    // 로그 인터셉터 추가 (디버그 모드에서만)
    // _dio.interceptors.add(LogInterceptor(
    //   requestBody: false, // 이미지 데이터가 클 수 있으므로 비활성화
    //   responseBody: false,
    //   logPrint: (obj) => print('API: $obj'),
    // ));
  }
  
  /// 서버 상태 확인
  Future<bool> checkServerStatus() async {
    try {
      final response = await _dio.get('/');
      return response.statusCode == 200;
    } catch (e) {
      print('Server status check failed: $e');
      return false;
    }
  }
  
  /// 이미지 업로드
  Future<ImageUploadResponse> uploadImage(Uint8List imageBytes, String fileName) async {
    try {
      // Multipart form data 생성
      final formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(
          imageBytes,
          filename: fileName,
          contentType: DioMediaType('image', 'jpeg'),
        ),
      });
      
      final response = await _dio.post(
        '/upload-image',
        data: formData,
        options: Options(
          contentType: 'multipart/form-data',
        ),
      );
      
      return ImageUploadResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException('이미지 업로드 실패: ${e.message}');
    }
  }
  
  /// 얼굴 랜드마크 검출
  Future<LandmarkResponse> getFaceLandmarks(String imageId) async {
    try {
      final response = await _dio.get('/landmarks/$imageId');
      return LandmarkResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw ApiException('얼굴을 찾을 수 없습니다');
      }
      throw ApiException('랜드마크 검출 실패: ${e.message}');
    }
  }
  
  /// 이미지 워핑 적용
  Future<WarpResponse> warpImage(WarpRequest request) async {
    try {
      final response = await _dio.post(
        '/warp-image',
        data: request.toJson(),
      );
      
      return WarpResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException('이미지 변형 실패: ${e.message}');
    }
  }
  
  /// 이미지 다운로드
  Future<Uint8List> downloadImage(String imageId) async {
    try {
      final response = await _dio.get(
        '/download-image/$imageId',
        options: Options(responseType: ResponseType.bytes),
      );
      
      return Uint8List.fromList(response.data);
    } on DioException catch (e) {
      throw ApiException('이미지 다운로드 실패: ${e.message}');
    }
  }
  
  /// 프리셋 적용
  Future<PresetResponse> applyPreset(String imageId, String presetType) async {
    try {
      final response = await _dio.post(
        '/apply-preset',
        data: {
          'image_id': imageId,
          'preset_type': presetType,
        },
      );
      
      return PresetResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException('프리셋 적용 실패: ${e.message}');
    }
  }
  
  /// 임시 이미지 삭제
  Future<void> deleteImage(String imageId) async {
    try {
      await _dio.delete('/image/$imageId');
    } on DioException catch (e) {
      // 삭제 실패는 치명적이지 않으므로 로그만 출력
      print('Image deletion failed: ${e.message}');
    }
  }

  /// 뷰티 점수 비교 분석
  Future<BeautyComparisonResult> analyzeBeautyComparison(
    Map<String, dynamic> beforeAnalysis, 
    Map<String, dynamic> afterAnalysis
  ) async {
    try {
      final response = await _dio.post(
        '/analyze-beauty-comparison',
        data: {
          'before_analysis': beforeAnalysis,
          'after_analysis': afterAnalysis,
        },
      );

      return BeautyComparisonResult.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException('뷰티 분석 비교 실패: ${e.message}');
    }
  }

  /// 기초 뷰티스코어 GPT 분석
  Future<InitialBeautyAnalysisResult> analyzeInitialBeautyScore(
    Map<String, dynamic> beautyAnalysis
  ) async {
    try {
      final response = await _dio.post(
        '/analyze-initial-beauty-score',
        data: {
          'beauty_analysis': beautyAnalysis,
        },
      );

      return InitialBeautyAnalysisResult.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException('기초 뷰티스코어 GPT 분석 실패: ${e.message}');
    }
  }
  
}

/// API 응답 모델들
class ImageUploadResponse {
  final String imageId;
  final int width;
  final int height;
  final String message;
  
  ImageUploadResponse({
    required this.imageId,
    required this.width,
    required this.height,
    required this.message,
  });
  
  factory ImageUploadResponse.fromJson(Map<String, dynamic> json) {
    return ImageUploadResponse(
      imageId: json['image_id'],
      width: json['width'],
      height: json['height'],
      message: json['message'],
    );
  }
}

class LandmarkResponse {
  final List<Landmark> landmarks;
  final int imageWidth;
  final int imageHeight;
  
  LandmarkResponse({
    required this.landmarks,
    required this.imageWidth,
    required this.imageHeight,
  });
  
  factory LandmarkResponse.fromJson(Map<String, dynamic> json) {
    final landmarksList = json['landmarks'] as List;
    final landmarks = landmarksList
        .asMap()
        .entries
        .map((entry) => Landmark.fromJson(entry.value, entry.key))
        .toList();
    
    return LandmarkResponse(
      landmarks: landmarks,
      imageWidth: json['image_width'],
      imageHeight: json['image_height'],
    );
  }
}

class WarpRequest {
  final String imageId;
  final double startX;
  final double startY;
  final double endX;
  final double endY;
  final double influenceRadius;
  final double strength;
  final String mode;
  
  WarpRequest({
    required this.imageId,
    required this.startX,
    required this.startY,
    required this.endX,
    required this.endY,
    required this.influenceRadius,
    required this.strength,
    required this.mode,
  });
  
  Map<String, dynamic> toJson() {
    return {
      'image_id': imageId,
      'start_x': startX,
      'start_y': startY,
      'end_x': endX,
      'end_y': endY,
      'influence_radius': influenceRadius,
      'strength': strength,
      'mode': mode,
    };
  }
}

class WarpResponse {
  final String imageId;
  final String imageData; // Base64 encoded
  
  WarpResponse({
    required this.imageId,
    required this.imageData,
  });
  
  factory WarpResponse.fromJson(Map<String, dynamic> json) {
    return WarpResponse(
      imageId: json['image_id'],
      imageData: json['image_data'],
    );
  }
  
  /// Base64 이미지 데이터를 Uint8List로 디코드
  Uint8List get imageBytes {
    return base64Decode(imageData);
  }
}

class PresetResponse {
  final String imageId;
  final String imageData; // Base64 encoded
  final String message;
  
  PresetResponse({
    required this.imageId,
    required this.imageData,
    required this.message,
  });
  
  factory PresetResponse.fromJson(Map<String, dynamic> json) {
    return PresetResponse(
      imageId: json['image_id'],
      imageData: json['image_data'],
      message: json['message'] ?? 'Preset applied successfully',
    );
  }
  
  /// Base64 이미지 데이터를 Uint8List로 디코드
  Uint8List get imageBytes {
    return base64Decode(imageData);
  }
}


/// 뷰티 점수 비교 결과
class BeautyComparisonResult {
  final String overallChange;
  final Map<String, double> scoreChanges;
  final List<String> recommendations;
  final String analysisText;

  BeautyComparisonResult({
    required this.overallChange,
    required this.scoreChanges,
    required this.recommendations,
    required this.analysisText,
  });

  factory BeautyComparisonResult.fromJson(Map<String, dynamic> json) {
    return BeautyComparisonResult(
      overallChange: json['overall_change'] ?? 'similar',
      scoreChanges: Map<String, double>.from(
        (json['score_changes'] as Map<String, dynamic>? ?? {})
            .map((k, v) => MapEntry(k, (v as num).toDouble()))
      ),
      recommendations: List<String>.from(json['recommendations'] ?? []),
      analysisText: json['analysis_text'] ?? '',
    );
  }
}

class InitialBeautyAnalysisResult {
  final String analysisText;
  final List<String> recommendations;
  final List<String> strengths;
  final List<String> improvementAreas;

  InitialBeautyAnalysisResult({
    required this.analysisText,
    required this.recommendations,
    required this.strengths,
    required this.improvementAreas,
  });

  factory InitialBeautyAnalysisResult.fromJson(Map<String, dynamic> json) {
    return InitialBeautyAnalysisResult(
      analysisText: json['analysis_text'] ?? '',
      recommendations: List<String>.from(json['recommendations'] ?? []),
      strengths: List<String>.from(json['strengths'] ?? []),
      improvementAreas: List<String>.from(json['improvement_areas'] ?? []),
    );
  }
}

/// API 예외 클래스
class ApiException implements Exception {
  final String message;
  
  ApiException(this.message);
  
  @override
  String toString() => message;
}