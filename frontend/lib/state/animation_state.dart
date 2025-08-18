import 'package:flutter/foundation.dart';
import '../config/animation_constants.dart';
import '../models/face_regions.dart';
import '../models/image_models.dart';

/// 애니메이션 상태 관리
class AnimationState extends ChangeNotifier {
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

  // Getters
  List<Landmark> get landmarks => _landmarks;
  bool get showLandmarks => _showLandmarks;
  RegionVisibility get regionVisibility => _regionVisibility;
  bool get isAnimationPlaying => _isAnimationPlaying;
  String? get currentAnimatingRegion => _currentAnimatingRegion;
  Map<String, double> get animationProgress => _animationProgress;
  bool get isAutoAnimationMode => _isAutoAnimationMode;
  int get currentAnimationIndex => _currentAnimationIndex;

  // 애니메이션 시퀀스 순서
  static const List<String> _animationSequence = [
    'eyebrow_area',
    'eyebrows',
    'eyes',
    'eyelid_lower_area',
    'nose_bridge',
    'nose_sides',
    'nose_wings',
    'cheek_area',
    'lip_upper',
    'lip_lower',
    'jawline_area',
  ];

  /// 랜드마크 설정
  void setLandmarks(List<Landmark> landmarks, {bool resetAnalysis = true}) {
    _landmarks = landmarks;
    notifyListeners();
  }

  /// 랜드마크 시각화 토글
  void toggleLandmarks() {
    _showLandmarks = !_showLandmarks;
    notifyListeners();
  }

  /// 특정 부위 시각화 토글
  void toggleRegionVisibility(String region) {
    _regionVisibility.toggle(region);
    notifyListeners();
  }

  /// 부위별 애니메이션 시작
  void startRegionAnimation(String regionKey) {
    _isAnimationPlaying = true;
    _currentAnimatingRegion = regionKey;
    _animationProgress[regionKey] = 0.0;
    _regionVisibility.setVisible(regionKey, true);
    notifyListeners();
  }

  /// 애니메이션 진행률 업데이트
  void updateAnimationProgress(String regionKey, double progress) {
    _animationProgress[regionKey] = progress.clamp(0.0, 1.0);
    notifyListeners();
  }

  /// 애니메이션 중지
  void stopAnimation() {
    _isAnimationPlaying = false;
    _currentAnimatingRegion = null;
    notifyListeners();
  }

  /// 자동 애니메이션 시작
  Future<void> startAutoAnimation() async {
    if (_landmarks.isEmpty || _isAutoAnimationMode) return;

    _isAutoAnimationMode = true;
    _isAnimationPlaying = true;
    _currentAnimationIndex = 0;
    notifyListeners();

    await _playAnimationSequence();
    
    _isAutoAnimationMode = false;
    _isAnimationPlaying = false;
    notifyListeners();
  }

  /// 애니메이션 시퀀스 재생
  Future<void> _playAnimationSequence() async {
    for (int i = 0; i < _animationSequence.length; i++) {
      if (!_isAutoAnimationMode) break;
      
      _currentAnimationIndex = i;
      final regionKey = _animationSequence[i];
      await _playRegionAnimation(regionKey);
      
      // 각 애니메이션 사이에 짧은 대기 시간
      await Future.delayed(const Duration(milliseconds: 500));
    }
  }

  /// 개별 부위 애니메이션 재생
  Future<void> _playRegionAnimation(String regionKey) async {
    startRegionAnimation(regionKey);
    
    final duration = AnimationConstants.getDurationForRegion(regionKey);
    const stepDuration = Duration(milliseconds: AnimationConstants.stepDurationMs);
    final steps = duration ~/ AnimationConstants.stepDurationMs;
    
    for (int i = 0; i <= steps; i++) {
      if (!_isAutoAnimationMode || _currentAnimatingRegion != regionKey) break;
      
      final progress = i / steps;
      updateAnimationProgress(regionKey, progress);
      
      await Future.delayed(stepDuration);
    }
  }

  /// 자동 애니메이션 중단
  void stopAutoAnimation() {
    _isAutoAnimationMode = false;
    _isAnimationPlaying = false;
    _currentAnimatingRegion = null;
    notifyListeners();
  }

  /// 모든 애니메이션을 즉시 완료 상태로 만들기
  void completeAllAnimations() {
    if (_landmarks.isEmpty) return;
    
    _isAutoAnimationMode = false;
    _isAnimationPlaying = false;
    _currentAnimatingRegion = null;
    
    // 모든 부위를 완료 상태로 설정
    for (final regionKey in _animationSequence) {
      _animationProgress[regionKey] = 1.0;
      _regionVisibility.setVisible(regionKey, true);
    }
    
    notifyListeners();
  }

  /// 탭 변경 처리
  void handleTabChange(int tabIndex) {
    // 프리셋 탭(1)이나 프리스타일 탭(2)으로 전환 시 애니메이션 관련 시각화 숨기기
    if (tabIndex == 1 || tabIndex == 2) {
      stopAutoAnimation();
      
      // 모든 부위 시각화 숨기기
      for (final regionKey in _regionVisibility.all.keys) {
        _regionVisibility.setVisible(regionKey, false);
      }
    }
    
    // 뷰티스코어 탭(0)으로 돌아올 때 완료된 상태가 있으면 복원
    if (tabIndex == 0 && _landmarks.isNotEmpty) {
      // 모든 부위 시각화 복원
      for (final regionKey in _regionVisibility.all.keys) {
        _animationProgress[regionKey] = 1.0;
        _regionVisibility.setVisible(regionKey, true);
      }
    }
    
    notifyListeners();
  }

  /// 상태 초기화
  void reset() {
    _landmarks = [];
    _showLandmarks = false;
    _regionVisibility.reset();
    _isAnimationPlaying = false;
    _currentAnimatingRegion = null;
    _animationProgress.clear();
    _isAutoAnimationMode = false;
    _currentAnimationIndex = 0;
    notifyListeners();
  }
}