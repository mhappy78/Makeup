import 'dart:typed_data';

/// 이미지 히스토리 아이템 (이미지 데이터 + ID)
class ImageHistoryItem {
  final Uint8List imageData;
  final String imageId;
  
  const ImageHistoryItem({
    required this.imageData,
    required this.imageId,
  });
}

/// 얼굴 랜드마크 모델
class Landmark {
  final double x;
  final double y;
  final int index;
  
  const Landmark({
    required this.x,
    required this.y,
    required this.index,
  });
  
  factory Landmark.fromJson(List<dynamic> json, int index) {
    return Landmark(
      x: json[0].toDouble(),
      y: json[1].toDouble(),
      index: index,
    );
  }
  
<<<<<<< HEAD
  Map<String, dynamic> toJson() {
    return {
      'x': x,
      'y': y,
      'index': index,
    };
  }
=======
  @override
  String toString() => 'Landmark(x: $x, y: $y, index: $index)';
  
  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Landmark &&
        other.x == x &&
        other.y == y &&
        other.index == index;
  }
  
  @override
  int get hashCode => Object.hash(x, y, index);
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
}

/// 워핑 모드 열거형
enum WarpMode {
  pull('pull', '당기기', '선택한 점을 드래그 방향으로 당김'),
  push('push', '밀어내기', '선택한 점을 드래그 방향으로 밀어냄'),
  expand('expand', '확대', '선택한 점 주변을 방사형으로 축소'),
  shrink('shrink', '축소', '선택한 점 주변을 방사형으로 확대');
  
  const WarpMode(this.value, this.displayName, this.description);
  
  final String value;
  final String displayName;
  final String description;
}

<<<<<<< HEAD
/// API 응답 모델들
class UploadResponse {
  final String imageId;
  final int width;
  final int height;
  final String message;

  UploadResponse({
    required this.imageId,
    required this.width,
    required this.height,
    required this.message,
  });

  factory UploadResponse.fromJson(Map<String, dynamic> json) {
    return UploadResponse(
      imageId: json['image_id'],
      width: json['width'],
      height: json['height'],
      message: json['message'],
    );
  }
}

class LandmarkResponse {
  final List<Landmark> landmarks;
  final String? warningMessage;

  LandmarkResponse({
    required this.landmarks,
    this.warningMessage,
  });

  factory LandmarkResponse.fromJson(Map<String, dynamic> json) {
    final landmarksData = json['landmarks'] as List;
    final landmarks = landmarksData
        .asMap()
        .entries
        .map((entry) => Landmark.fromJson(entry.value, entry.key))
        .toList();

    return LandmarkResponse(
      landmarks: landmarks,
      warningMessage: json['warning_message'],
    );
  }
}

class WarpResponse {
  final String imageId;
  final String message;

  WarpResponse({
    required this.imageId,
    required this.message,
  });

  factory WarpResponse.fromJson(Map<String, dynamic> json) {
    return WarpResponse(
      imageId: json['image_id'],
      message: json['message'],
    );
  }
}

class PresetResponse {
  final String imageId;
  final String message;

  PresetResponse({
    required this.imageId,
    required this.message,
  });

  factory PresetResponse.fromJson(Map<String, dynamic> json) {
    return PresetResponse(
      imageId: json['image_id'],
      message: json['message'],
    );
  }
}

class BeautyAnalysisResponse {
  final Map<String, dynamic> analysis;
  final String message;

  BeautyAnalysisResponse({
    required this.analysis,
    required this.message,
  });

  factory BeautyAnalysisResponse.fromJson(Map<String, dynamic> json) {
    return BeautyAnalysisResponse(
      analysis: json['analysis'],
      message: json['message'],
    );
  }
}

class GptAnalysisResponse {
  final String analysisText;
  final List<String> recommendations;
  final double overallChange;
  final Map<String, dynamic> scoreChanges;

  GptAnalysisResponse({
    required this.analysisText,
    required this.recommendations,
    required this.overallChange,
    required this.scoreChanges,
  });

  factory GptAnalysisResponse.fromJson(Map<String, dynamic> json) {
    return GptAnalysisResponse(
      analysisText: json['analysis_text'] ?? '',
      recommendations: List<String>.from(json['recommendations'] ?? []),
      overallChange: json['overall_change']?.toDouble() ?? 0.0,
      scoreChanges: json['score_changes'] ?? {},
=======
/// 프리셋 타입 열거형
enum PresetType {
  lowerJaw('lower_jaw', '아래턱'),
  middleJaw('middle_jaw', '중간턱'), 
  cheek('cheek', '볼'),
  frontProtusion('front_protusion', '앞트임'),
  backSlit('back_slit', '뒷트임');
  
  const PresetType(this.value, this.displayName);
  
  final String value;
  final String displayName;
  
  static PresetType fromValue(String value) {
    return PresetType.values.firstWhere(
      (preset) => preset.value == value,
      orElse: () => PresetType.lowerJaw,
>>>>>>> f435d49af910aaf9ed939c9da05f44ebe54ec140
    );
  }
}