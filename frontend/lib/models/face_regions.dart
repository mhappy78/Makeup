import 'dart:ui';

/// 얼굴 부위별 랜드마크 정의
class FaceRegions {
  /// 부위별 랜드마크 인덱스와 색상 정의
  static final Map<String, RegionData> regions = {
    // 눈 영역
    'eyes': RegionData(
      name: '눈',
      indices: [
        33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, // 왼쪽 눈
        362, 382, 381, 380, 374, 373, 390, 249, 359, 263, 466, 388, 387, 386, 385, 384, 398 // 오른쪽 눈
      ],
      color: const Color(0xFF00FF00), // 녹색
      lines: [
        // 왼쪽 눈 윤곽
        [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 33],
        // 오른쪽 눈 윤곽
        [362, 382, 381, 380, 374, 373, 390, 249, 359, 263, 466, 388, 387, 386, 385, 384, 398, 362],
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '왼쪽눈',
          points: [133, 173, 157, 158, 159, 160, 161, 246, 33, 7, 163, 144, 145, 153, 154, 155, 133],
          fillArea: true,
        ),
        AnimationSequence(
          name: '오른쪽눈',
          points: [362, 398, 384, 385, 386, 387, 388, 466, 263, 359, 249, 390, 373, 374, 380, 381, 382, 362],
          fillArea: true,
          simultaneousStart: true,
        ),
      ],
    ),
    
    // 하주변영역 (눈 아래 영역)
    'eyelid_lower_area': RegionData(
      name: '하주변영역',
      indices: [
        226, 25, 110, 24, 23, 22, 26, 112, 243, // 왼쪽 하꺼풀
        463, 341, 256, 252, 253, 254, 339, 255, 446, // 오른쪽 하꺼풀
        35, 31, 228, 229, 230, 231, 232, 233, 244, // 왼쪽 하주변
        465, 453, 452, 451, 450, 449, 448, 261, 265 // 오른쪽 하주변
      ],
      color: const Color(0xFF66CCFF), // 밝은 청록색
      lines: [
        // 왼쪽 하꺼풀 라인
        [226, 25, 110, 24, 23, 22, 26, 112, 243],
        // 오른쪽 하꺼풀 라인
        [463, 341, 256, 252, 253, 254, 339, 255, 446],
        // 왼쪽 하주변 라인
        [35, 31, 228, 229, 230, 231, 232, 233, 244],
        // 오른쪽 하주변 라인
        [465, 453, 452, 451, 450, 449, 448, 261, 265],
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '왼쪽하주변',
          points: [243, 112, 26, 22, 23, 24, 110, 25, 226, 35, 31, 228, 229, 230, 231, 232, 233, 244, 243],
          fillArea: true,
        ),
        AnimationSequence(
          name: '오른쪽하주변',
          points: [463, 341, 256, 252, 253, 254, 339, 255, 446, 265, 261, 448, 449, 450, 451, 452, 453, 465, 463],
          fillArea: true,
          simultaneousStart: true,
        ),
      ],
    ),
    
    // 코 기둥
    'nose_bridge': RegionData(
      name: '코기둥',
      indices: [4, 5, 6, 19, 94, 168, 195, 197],
      color: const Color(0xFFFF4400), // 주황빨강
      lines: [
        [19, 94, 168, 195, 197, 6, 5, 4], // 코기둥 라인
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '코기둥',
          points: [168, 6, 197, 195, 5, 4, 19, 94],
          fillArea: false,
        ),
      ],
    ),
    
    // 콧볼
    'nose_wings': RegionData(
      name: '콧볼',
      indices: [45, 129, 64, 98, 97, 115, 220, 275, 278, 294, 326, 327, 344, 440],
      color: const Color(0xFFFF8800), // 주황색
      lines: [
        // 왼쪽 콧볼
        [45, 129, 64, 98, 97, 115, 220],
        // 오른쪽 콧볼
        [275, 278, 294, 326, 327, 344, 440],
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '콧볼',
          points: [4, 275, 440, 344, 278, 294, 327, 326, 97, 98, 64, 129, 115, 220, 45, 4],
          fillArea: true,
        ),
      ],
    ),
    
    // 코 측면
    'nose_sides': RegionData(
      name: '코측면',
      indices: [
        193, 122, 196, 236, 198, 209, 49, // 왼쪽 코 측면
        417, 351, 419, 456, 420, 360, 279 // 오른쪽 코 측면
      ],
      color: const Color(0xFFFF9900), // 주황색
      lines: [
        // 왼쪽 코 측면 라인
        [193, 122, 196, 236, 198, 209, 49],
        // 오른쪽 코 측면 라인
        [417, 351, 419, 456, 420, 360, 279],
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '왼쪽코측면',
          points: [122, 196, 236, 198, 209, 49],
          fillArea: false,
        ),
        AnimationSequence(
          name: '오른쪽코측면',
          points: [351, 419, 456, 420, 360, 279],
          fillArea: false,
          simultaneousStart: true,
        ),
      ],
    ),
    
    // 윗입술
    'lip_upper': RegionData(
      name: '윗입술',
      indices: [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 308, 415, 310, 312, 13, 82, 81, 80, 191, 78],
      color: const Color(0xFFFF3300), // 밝은 빨간색
      lines: [
        [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291], // 윗입술 상단
        [61, 78, 191, 80, 81, 82, 13, 312, 310, 415, 308, 291], // 윗입술 하단
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '윗입술',
          points: [0, 267, 269, 270, 409, 291, 308, 310, 312, 13, 82, 81, 80, 191, 78, 61, 185, 40, 39, 37, 0],
          fillArea: true,
        ),
      ],
    ),
    
    // 아래입술
    'lip_lower': RegionData(
      name: '아래입술',
      indices: [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 402, 317, 14, 87, 178, 88, 95, 78],
      color: const Color(0xFFFF6600), // 주황색
      lines: [
        [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291], // 아래입술 하단
        [61, 78, 95, 88, 178, 87, 14, 317, 402, 324, 308, 291], // 아래입술 상단
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '아래입술',
          points: [17, 314, 405, 321, 375, 291, 308, 324, 402, 317, 14, 87, 178, 88, 95, 78, 61, 146, 91, 181, 84, 17],
          fillArea: true,
        ),
      ],
    ),
    
    // 턱선영역
    'jawline_area': RegionData(
      name: '턱선영역',
      indices: [
        172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 58, 132, 137, // 기존 턱선
        123, 50, 207, 212, 202, 204, 194, 201, 200, 421, 418, 424, 422, 432, 427, 280, 352 // 추가 랜드마크
      ],
      color: const Color(0xFF0088FF), // 밝은 파란색
      lines: [
        // 턱선 메인 라인
        [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323],
        // 턱선 보조 라인
        [123, 50, 207, 212, 202, 204, 194, 201, 200, 421, 418, 424, 422, 432, 427, 280, 352],
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '턱선영역',
          points: [200, 421, 418, 424, 422, 432, 427, 280, 352, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 137, 123, 50, 207, 212, 202, 204, 194, 201, 200],
          fillArea: true,
        ),
      ],
    ),
    
    // 눈썹주변영역 (눈썹 제외)
    'eyebrow_area': RegionData(
      name: '눈썹주변영역',
      indices: [151, 337, 299, 333, 298, 301, 383, 353, 260, 259, 257, 258, 286, 413, 417, 168, 193, 189, 56, 28, 27, 29, 30, 156, 139, 71, 68, 104, 69, 108],
      color: const Color(0xFF9900FF), // 보라색
      lines: [
        // 눈썹주변영역 애니메이션 순서
        [151, 337, 299, 333, 298, 301, 383, 353, 260, 259, 257, 258, 286, 413, 417, 168, 193, 189, 56, 28, 27, 29, 30, 156, 139, 71, 68, 104, 69, 108, 151],
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '눈썹주변영역',
          points: [151, 337, 299, 333, 298, 301, 383, 353, 260, 259, 257, 258, 286, 413, 417, 168, 193, 189, 56, 28, 27, 29, 30, 156, 139, 71, 68, 104, 69, 108, 151],
          fillArea: true,
        ),
      ],
    ),
    
    // 눈썹 (별도 영역)
    'eyebrows': RegionData(
      name: '눈썹',
      indices: [
        55, 107, 66, 105, 63, 70, 46, 53, 52, 65, // 왼쪽 눈썹
        285, 336, 296, 334, 293, 300, 276, 283, 282, 295 // 오른쪽 눈썹
      ],
      color: const Color(0xFF7700CC), // 더 진한 보라색
      lines: [
        // 왼쪽 눈썹
        [107, 66, 105, 63, 70, 46, 53, 52, 65, 55, 107],
        // 오른쪽 눈썹
        [336, 296, 334, 293, 300, 276, 283, 282, 295, 285, 336],
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '왼쪽눈썹',
          points: [107, 66, 105, 63, 70, 46, 53, 52, 65, 55, 107],
          fillArea: true,
        ),
        AnimationSequence(
          name: '오른쪽눈썹',
          points: [336, 296, 334, 293, 300, 276, 283, 282, 295, 285, 336],
          fillArea: true,
          simultaneousStart: true, // 왼쪽과 동시 시작
        ),
      ],
    ),
    
    // 볼영역
    'cheek_area': RegionData(
      name: '볼영역',
      indices: [
        116, 117, 118, 119, 120, 121, 126, 142, 36, 205, 147, 187, 123, 50, // 왼쪽 볼
        345, 346, 347, 348, 349, 350, 355, 371, 266, 425, 376, 411, 352, 280 // 오른쪽 볼
      ],
      color: const Color(0xFFFF6699), // 밝은 분홍색
      lines: [
        // 왼쪽 볼 영역
        [116, 117, 118, 119, 120, 121, 126, 142, 36, 205, 147, 187, 123, 50],
        // 오른쪽 볼 영역
        [345, 346, 347, 348, 349, 350, 355, 371, 266, 425, 376, 411, 352, 280],
      ],
      hasAnimation: true,
      animationSequences: [
        AnimationSequence(
          name: '왼쪽볼',
          points: [121, 120, 119, 118, 117, 116, 123, 147, 187, 205, 36, 142, 126, 121],
          fillArea: true,
        ),
        AnimationSequence(
          name: '오른쪽볼',
          points: [350, 349, 348, 347, 346, 345, 352, 376, 411, 425, 266, 371, 355, 350],
          fillArea: true,
          simultaneousStart: true,
        ),
      ],
    ),
  };
}

/// 얼굴 부위 데이터
class RegionData {
  final String name;
  final List<int> indices;
  final Color color;
  final List<List<int>> lines;
  final bool hasAnimation;
  final List<AnimationSequence> animationSequences;
  
  const RegionData({
    required this.name,
    required this.indices,
    required this.color,
    required this.lines,
    this.hasAnimation = false,
    this.animationSequences = const [],
  });
}

/// 애니메이션 시퀀스 데이터
class AnimationSequence {
  final String name;
  final List<int> points;
  final bool fillArea;
  final bool simultaneousStart;
  
  const AnimationSequence({
    required this.name,
    required this.points,
    this.fillArea = false,
    this.simultaneousStart = false,
  });
}

/// 부위별 가시성 상태
class RegionVisibility {
  final Map<String, bool> _visibility = {};
  
  RegionVisibility() {
    // 기본적으로 모든 부위 표시
    for (final key in FaceRegions.regions.keys) {
      _visibility[key] = true;
    }
  }
  
  bool isVisible(String region) => _visibility[region] ?? false;
  
  void setVisible(String region, bool visible) {
    _visibility[region] = visible;
  }
  
  void toggleVisibility(String region) {
    _visibility[region] = !(_visibility[region] ?? false);
  }
  
  Map<String, bool> get all => Map.unmodifiable(_visibility);
}