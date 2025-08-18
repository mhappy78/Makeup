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
    );
  }
}