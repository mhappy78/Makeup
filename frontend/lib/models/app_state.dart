import 'package:flutter/foundation.dart';
import 'dart:typed_data';
import 'face_regions.dart';
import '../services/api_service.dart';

/// 앱의 전역 상태 관리
class AppState extends ChangeNotifier {
  // 이미지 관련 상태
  Uint8List? _currentImage;
  String? _currentImageId;
  int _imageWidth = 0;
  int _imageHeight = 0;
  
  // 랜드마크 관련 상태
  List<Landmark> _landmarks = [];
  bool _showLandmarks = false;
  final RegionVisibility _regionVisibility = RegionVisibility();
  
  // 애니메이션 상태
  bool _isAnimationPlaying = false;
  String? _currentAnimatingRegion;
  Map<String, double> _animationProgress = {};
  bool _isAutoAnimationMode = false;
  int _currentAnimationIndex = 0;
  
  // 워핑 도구 상태
  WarpMode _warpMode = WarpMode.pull;
  double _influenceRadius = 80.0;
  double _warpStrength = 1.0;
  
  // UI 상태
  bool _isLoading = false;
  String? _errorMessage;
  bool _showBeautyScore = false;
  double _beautyScoreAnimationProgress = 0.0;
  
  
  // Getters
  Uint8List? get currentImage => _currentImage;
  String? get currentImageId => _currentImageId;
  int get imageWidth => _imageWidth;
  int get imageHeight => _imageHeight;
  List<Landmark> get landmarks => _landmarks;
  bool get showLandmarks => _showLandmarks;
  RegionVisibility get regionVisibility => _regionVisibility;
  bool get isAnimationPlaying => _isAnimationPlaying;
  String? get currentAnimatingRegion => _currentAnimatingRegion;
  Map<String, double> get animationProgress => _animationProgress;
  bool get isAutoAnimationMode => _isAutoAnimationMode;
  WarpMode get warpMode => _warpMode;
  double get influenceRadius => _influenceRadius;
  double get warpStrength => _warpStrength;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get showBeautyScore => _showBeautyScore;
  double get beautyScoreAnimationProgress => _beautyScoreAnimationProgress;
  
  // 이미지 설정
  void setImage(Uint8List imageData, String imageId, int width, int height) {
    _currentImage = imageData;
    _currentImageId = imageId;
    _imageWidth = width;
    _imageHeight = height;
    _landmarks.clear();
    _showBeautyScore = false; // 새 이미지 시 뷰티 스코어 숨기기
    _beautyScoreAnimationProgress = 0.0;
    clearError();
    notifyListeners();
  }
  
  // 애니메이션 시퀀스 순서 정의
  static const List<String> _animationSequence = [
    'eyebrow_area',    // 1. 눈썹주변영역
    'eyebrows',        // 2. 눈썹
    'eyes',            // 3. 눈
    'eyelid_lower_area', // 4. 하주변영역
    'nose_bridge',     // 5. 코기둥
    'nose_sides',      // 6. 코측면
    'nose_wings',      // 7. 콧볼
    'cheek_area',      // 8. 볼영역
    'lip_upper',       // 9. 윗입술
    'lip_lower',       // 10. 아래입술
    'jawline_area',    // 11. 턱선영역
  ];

  // 랜드마크 설정 및 자동 애니메이션 시작
  void setLandmarks(List<Landmark> landmarks) {
    _landmarks = landmarks;
    notifyListeners();
    
    // 이미지 업로드 시 자동으로 애니메이션 시작
    if (landmarks.isNotEmpty) {
      _startAutoAnimation();
    }
  }
  
  // 랜드마크 표시 토글
  void toggleLandmarks() {
    _showLandmarks = !_showLandmarks;
    notifyListeners();
  }
  
  // 부위별 가시성 토글
  void toggleRegionVisibility(String region) {
    _regionVisibility.toggleVisibility(region);
    notifyListeners();
  }
  
  // 애니메이션 시작
  void startRegionAnimation(String regionKey) {
    _isAnimationPlaying = true;
    _currentAnimatingRegion = regionKey;
    _animationProgress[regionKey] = 0.0;
    notifyListeners();
  }
  
  // 애니메이션 진행률 업데이트
  void updateAnimationProgress(String regionKey, double progress) {
    _animationProgress[regionKey] = progress;
    notifyListeners();
  }
  
  // 애니메이션 종료
  void stopAnimation() {
    _isAnimationPlaying = false;
    _currentAnimatingRegion = null;
    notifyListeners();
  }
  
  // 자동 애니메이션 시작
  Future<void> _startAutoAnimation() async {
    _isAutoAnimationMode = true;
    _currentAnimationIndex = 0;
    _showLandmarks = true; // 자동으로 랜드마크 표시 켜기
    
    // 모든 부위를 표시 상태로 설정
    for (final regionKey in _animationSequence) {
      _regionVisibility.setVisible(regionKey, true);
    }
    
    // 애니메이션 진행률 초기화
    _animationProgress.clear();
    
    notifyListeners();
    
    // 시퀀스 애니메이션 시작
    await _playAnimationSequence();
    
    // 애니메이션 종료 후 뷰티 스코어 계산 및 표시
    _showBeautyScore = true;
    _startBeautyScoreAnimation();
    
    _isAutoAnimationMode = false;
    notifyListeners();
  }
  
  // 애니메이션 시퀀스 재생
  Future<void> _playAnimationSequence() async {
    for (int i = 0; i < _animationSequence.length; i++) {
      if (!_isAutoAnimationMode) break;
      
      _currentAnimationIndex = i;
      final regionKey = _animationSequence[i];
      // 애니메이션이 있는 모든 부위 재생
      await _playRegionAnimation(regionKey);
      
      // 각 애니메이션 사이에 짧은 대기 시간
      await Future.delayed(const Duration(milliseconds: 500));
    }
  }
  
  // 개별 부위 애니메이션 재생
  Future<void> _playRegionAnimation(String regionKey) async {
    startRegionAnimation(regionKey);
    
    // 애니메이션 지속시간 설정
    int duration;
    switch (regionKey) {
      case 'eyebrow_area':
        duration = 3000; // 3초
        break;
      case 'eyebrows':
        duration = 2000; // 2초
        break;
      case 'eyes':
      case 'eyelid_lower_area':
      case 'cheek_area':
        duration = 2500; // 2.5초
        break;
      case 'nose_bridge':
      case 'nose_sides':
        duration = 1500; // 1.5초
        break;
      case 'nose_wings':
      case 'lip_upper':
      case 'lip_lower':
        duration = 2000; // 2초
        break;
      case 'jawline_area':
        duration = 3500; // 3.5초
        break;
      default:
        duration = 2000;
    }
    
    const stepDuration = Duration(milliseconds: 50);
    final steps = duration ~/ 50;
    
    for (int i = 0; i <= steps; i++) {
      if (!_isAutoAnimationMode || _currentAnimatingRegion != regionKey) break;
      
      final progress = i / steps;
      updateAnimationProgress(regionKey, progress);
      
      await Future.delayed(stepDuration);
    }
  }
  
  // 워핑 모드 변경
  void setWarpMode(WarpMode mode) {
    _warpMode = mode;
    notifyListeners();
  }
  
  // 영향 반경 변경
  void setInfluenceRadius(double radius) {
    _influenceRadius = radius;
    notifyListeners();
  }
  
  // 워핑 강도 변경
  void setWarpStrength(double strength) {
    _warpStrength = strength;
    notifyListeners();
  }
  
  // 로딩 상태 설정
  void setLoading(bool loading) {
    _isLoading = loading;
    if (loading) {
      _errorMessage = null;
    }
    notifyListeners();
  }
  
  // 에러 설정
  void setError(String error) {
    _errorMessage = error;
    _isLoading = false;
    notifyListeners();
  }
  
  // 에러 클리어
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
  
  // 자동 애니메이션 중단
  void stopAutoAnimation() {
    _isAutoAnimationMode = false;
    _isAnimationPlaying = false;
    _currentAnimatingRegion = null;
    notifyListeners();
  }

  // 뷰티 스코어 애니메이션 시작
  Future<void> _startBeautyScoreAnimation() async {
    _beautyScoreAnimationProgress = 0.0;
    notifyListeners();
    
    const duration = Duration(milliseconds: 2000); // 2초 동안 애니메이션
    const steps = 60; // 60 프레임
    const stepDuration = Duration(milliseconds: 33); // ~60 FPS
    
    for (int i = 0; i <= steps; i++) {
      if (!_showBeautyScore) break; // 중단 조건
      
      final progress = i / steps;
      // 부드러운 이징 곡선 적용 (ease-out)
      _beautyScoreAnimationProgress = 1 - (1 - progress) * (1 - progress);
      
      notifyListeners();
      await Future.delayed(stepDuration);
    }
    
    _beautyScoreAnimationProgress = 1.0;
    notifyListeners();
  }

  
  // 상태 리셋
  void reset() {
    stopAutoAnimation(); // 애니메이션 중단
    _currentImage = null;
    _currentImageId = null;
    _imageWidth = 0;
    _imageHeight = 0;
    _landmarks.clear();
    _showLandmarks = false;
    _showBeautyScore = false;
    _beautyScoreAnimationProgress = 0.0;
    _animationProgress.clear();
    _currentAnimationIndex = 0;
    _warpMode = WarpMode.pull;
    _influenceRadius = 80.0;
    _warpStrength = 1.0;
    _isLoading = false;
    _errorMessage = null;
    notifyListeners();
  }
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
}

/// 워핑 모드 열거형
enum WarpMode {
  pull('pull', '당기기', '선택한 점을 드래그 방향으로 당김'),
  push('push', '밀어내기', '선택한 점을 드래그 방향으로 밀어냄'),
  expand('expand', '확대', '선택한 점 주변을 방사형으로 확대'),
  shrink('shrink', '축소', '선택한 점 주변을 방사형으로 축소');
  
  const WarpMode(this.value, this.displayName, this.description);
  
  final String value;
  final String displayName;
  final String description;
}