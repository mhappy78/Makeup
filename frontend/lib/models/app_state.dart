import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'dart:typed_data';
import 'dart:math' as math;
import 'face_regions.dart';
import '../services/api_service.dart';

// 애니메이션 상수들
class AnimationConstants {
  // 애니메이션 지속 시간 (밀리초)
  static const int eyebrowAreaDuration = 3000;
  static const int eyebrowsDuration = 2000;
  static const int eyesAreaDuration = 2500;
  static const int eyelidLowerAreaDuration = 2500;
  static const int cheekAreaDuration = 2500;
  static const int noseBridgeDuration = 1500;
  static const int noseSidesDuration = 1500;
  static const int noseWingsDuration = 2000;
  static const int lipUpperDuration = 2000;
  static const int lipLowerDuration = 2000;
  static const int jawlineAreaDuration = 3500;
  static const int defaultDuration = 2000;
  
  // 레이저 효과
  static const int minLaserDuration = 1500;
  static const int maxLaserDuration = 15000;
  static const int laserIterationDuration = 1000;
  
  // 뷰티 스코어 애니메이션
  static const int beautyScoreAnimationDuration = 2000;
  static const int beautyScoreAnimationSteps = 60;
  static const int beautyScoreStepDuration = 33;
  
  // 공통 스텝 설정
  static const int stepDurationMs = 50;
}

/// 앱의 전역 상태 관리
class AppState extends ChangeNotifier {
  // 이미지 관련 상태
  Uint8List? _currentImage;
  Uint8List? _originalImage;  // 원본 이미지 저장
  String? _currentImageId;
  String? _originalImageId;  // 원본 이미지 ID (Backend 보존용)
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
  double _influenceRadiusPercent = 20.0; // 이미지 크기 대비 퍼센트 (기본 20%)
  double _warpStrength = 0.1; // 기본 10% (0.1)
  
  // 줌 및 팬 상태
  double _zoomScale = 1.0;
  Offset _panOffset = Offset.zero;
  bool _showOriginalImage = false; // Before/After 비교를 위한 상태
  
  // 히스토리 관리
  final List<ImageHistoryItem> _imageHistory = [];
  static const int _maxHistorySize = 20;
  
  // UI 상태
  bool _isLoading = false;
  String? _errorMessage;
  bool _showBeautyScore = false;
  double _beautyScoreAnimationProgress = 0.0;
  int _currentTabIndex = 0; // 현재 탭 인덱스 (0: 분석, 1: 수정, 2: 전문가)
  
  // 컨텍스트 저장 (오버레이 사용을 위해)
  BuildContext? _context;
  
  // 프리셋 로딩 상태
  String? _loadingPresetType; // 현재 로딩 중인 프리셋 타입
  int _currentProgress = 0; // 현재 진행된 샷/퍼센트 수
  
  // 워핑 로딩 상태
  bool _isWarpLoading = false; // 워핑 처리 중 여부
  
  // 프리셋 관련 상태
  Map<String, int> _presetCounters = {
    'lower_jaw': 0,
    'middle_jaw': 0,
    'cheek': 0,
    'front_protusion': 0,
    'back_slit': 0,
  };
  
  Map<String, int> _presetSettings = {
    'lower_jaw': 100,    // 100~500샷
    'middle_jaw': 100,
    'cheek': 100,
    'front_protusion': 3,  // 1~5%
    'back_slit': 3,        // 1~5%
  };
  
  // 레이저 시각화 상태
  bool _showLaserEffect = false;
  String? _currentLaserPreset;
  int _laserIterations = 1;
  int _laserDurationMs = 1500;
  
  // 뷰티 스코어 분석 결과
  Map<String, dynamic> _beautyAnalysis = {};
  
  // 프리셋 시각화 상태
  bool _showPresetVisualization = false;
  String? _currentPresetType;
  Map<String, dynamic> _presetVisualizationData = {};
  
  
  // Getters
  Uint8List? get currentImage => _currentImage;
  Uint8List? get originalImage => _originalImage;
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
  double get influenceRadiusPercent => _influenceRadiusPercent;
  double get warpStrength => _warpStrength;
  bool get canUndo => _imageHistory.isNotEmpty;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get showBeautyScore => _showBeautyScore;
  double get beautyScoreAnimationProgress => _beautyScoreAnimationProgress;
  Map<String, dynamic> get beautyAnalysis => _beautyAnalysis;
  int get currentTabIndex => _currentTabIndex;
  double get zoomScale => _zoomScale;
  Offset get panOffset => _panOffset;
  bool get showOriginalImage => _showOriginalImage;
  String? get loadingPresetType => _loadingPresetType;
  int get currentProgress => _currentProgress;
  bool get isWarpLoading => _isWarpLoading;
  Map<String, int> get presetCounters => _presetCounters;
  Map<String, int> get presetSettings => _presetSettings;
  bool get showLaserEffect => _showLaserEffect;
  String? get currentLaserPreset => _currentLaserPreset;
  int get laserIterations => _laserIterations;
  int get laserDurationMs => _laserDurationMs;
  bool get showPresetVisualization => _showPresetVisualization;
  String? get currentPresetType => _currentPresetType;
  Map<String, dynamic> get presetVisualizationData => _presetVisualizationData;
  
  // Before/After 비교를 위한 표시 이미지 getter
  Uint8List? get displayImage => _showOriginalImage ? _originalImage : _currentImage;
  
  // 특정 프리셋이 로딩 중인지 확인
  bool isPresetLoading(String presetType) => _loadingPresetType == presetType;
  
  // 이미지 설정 (새 이미지 업로드 시)
  void setImage(Uint8List imageData, String imageId, int width, int height) {
    _currentImage = imageData;
    _originalImage = Uint8List.fromList(imageData); // 원본 이미지 복사 저장
    _currentImageId = imageId;
    _originalImageId = imageId; // 원본 ID도 저장
    _imageWidth = width;
    _imageHeight = height;
    _landmarks.clear();
    _showBeautyScore = false; // 새 이미지 시 뷰티 스코어 숨기기
    _beautyScoreAnimationProgress = 0.0;
    _beautyAnalysis.clear();
    _imageHistory.clear(); // 히스토리 초기화
    clearError();
    notifyListeners();
  }
  
  // 워핑 결과 이미지로 현재 이미지만 업데이트 (원본은 유지)
  void updateCurrentImage(Uint8List imageData) {
    _currentImage = imageData;
    notifyListeners();
  }
  
  // 프리셋 적용용 이미지 업데이트 (히스토리 보존)
  void updateImageFromPreset(Uint8List imageData, String imageId) {
    // 현재 이미지를 히스토리에 저장
    if (_currentImage != null && _currentImageId != null) {
      _imageHistory.add(ImageHistoryItem(
        imageData: Uint8List.fromList(_currentImage!),
        imageId: _currentImageId!,
      ));
      
      // 히스토리 크기 제한
      if (_imageHistory.length > _maxHistorySize) {
        _imageHistory.removeAt(0);
      }
    }
    
    // 새 이미지로 업데이트 (원본은 유지)
    _currentImage = imageData;
    _currentImageId = imageId;
    
    notifyListeners();
  }
  
  // 워핑 결과 이미지와 새로운 ID로 현재 이미지 업데이트
  void updateCurrentImageWithId(Uint8List imageData, String newImageId) {
    _currentImage = imageData;
    _currentImageId = newImageId;
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
    
    // 분석 탭(index 0)에서만 자동 애니메이션 시작
    if (landmarks.isNotEmpty && _currentTabIndex == 0) {
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
    _calculateBeautyAnalysis();
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
        duration = AnimationConstants.eyebrowAreaDuration; // 3초
        break;
      case 'eyebrows':
        duration = AnimationConstants.eyebrowsDuration; // 2초
        break;
      case 'eyes':
      case 'eyelid_lower_area':
      case 'cheek_area':
        duration = AnimationConstants.eyesAreaDuration; // 2.5초
        break;
      case 'nose_bridge':
      case 'nose_sides':
        duration = AnimationConstants.noseBridgeDuration; // 1.5초
        break;
      case 'nose_wings':
      case 'lip_upper':
      case 'lip_lower':
        duration = AnimationConstants.noseWingsDuration; // 2초
        break;
      case 'jawline_area':
        duration = AnimationConstants.jawlineAreaDuration; // 3.5초
        break;
      default:
        duration = AnimationConstants.defaultDuration;
    }
    
    const stepDuration = Duration(milliseconds: AnimationConstants.stepDurationMs);
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
  
  // 영향 반경 변경 (퍼센트 기반)
  void setInfluenceRadiusPercent(double percent) {
    _influenceRadiusPercent = percent.clamp(0.1, 50.0); // 0.1%~50% 범위 제한
    notifyListeners();
  }
  
  // 워핑 강도 변경
  void setWarpStrength(double strength) {
    _warpStrength = strength;
    notifyListeners();
  }
  
  // 줌 스케일 설정
  void setZoomScale(double scale) {
    _zoomScale = math.max(0.5, math.min(3.0, scale)); // 0.5x ~ 3.0x 제한
    notifyListeners();
  }
  
  // 팬 오프셋 설정
  void setPanOffset(Offset offset) {
    _panOffset = offset;
    notifyListeners();
  }
  
  // 팬 오프셋 추가 (상대적 이동) - 경계 제한 포함
  void addPanOffset(Offset delta) {
    final newOffset = _panOffset + delta;
    
    // 줌된 상태에서만 팬 경계 제한
    if (_zoomScale > 1.0) {
      // 대략적인 경계 계산 (화면 크기의 절반)
      final maxOffset = 200.0 * (_zoomScale - 1.0);
      _panOffset = Offset(
        newOffset.dx.clamp(-maxOffset, maxOffset),
        newOffset.dy.clamp(-maxOffset, maxOffset),
      );
    } else {
      _panOffset = newOffset;
    }
    
    notifyListeners();
  }
  
  // 줌 리셋
  void resetZoom() {
    _zoomScale = 1.0;
    _panOffset = Offset.zero;
    notifyListeners();
  }
  
  // Before/After 토글
  void toggleOriginalImage() {
    _showOriginalImage = !_showOriginalImage;
    notifyListeners();
  }
  
  // Before/After 상태 설정
  void setShowOriginalImage(bool show) {
    _showOriginalImage = show;
    notifyListeners();
  }
  
  // 퍼센트를 픽셀로 변환 (백엔드 전송용 - 실제 이미지 크기)
  double getInfluenceRadiusPixels() {
    if (_currentImage == null || _imageWidth == 0 || _imageHeight == 0) {
      return 80.0; // 기본값
    }
    
    // 이미지의 더 작은 차원을 기준으로 백분율 계산 (정사각형에 가깝게)
    final baseSize = math.min(_imageWidth, _imageHeight);
    return baseSize * (_influenceRadiusPercent / 100.0);
  }
  
  // 화면 표시용 영향반경 계산 (화면 크기에 맞게 스케일링)
  double getInfluenceRadiusForDisplay(Size containerSize) {
    if (_currentImage == null || _imageWidth == 0 || _imageHeight == 0) {
      return 20.0; // 기본값
    }
    
    // 이미지 표시 크기 계산
    final imageAspectRatio = _imageWidth / _imageHeight;
    final containerAspectRatio = containerSize.width / containerSize.height;
    
    late Size imageDisplaySize;
    
    if (imageAspectRatio > containerAspectRatio) {
      imageDisplaySize = Size(containerSize.width, containerSize.width / imageAspectRatio);
    } else {
      imageDisplaySize = Size(containerSize.height * imageAspectRatio, containerSize.height);
    }
    
    // 화면 표시 크기의 더 작은 차원을 기준으로 백분율 계산
    final baseDisplaySize = math.min(imageDisplaySize.width, imageDisplaySize.height);
    return baseDisplaySize * (_influenceRadiusPercent / 100.0);
  }
  
  // 히스토리에 현재 이미지와 ID 저장
  void saveToHistory() {
    if (_currentImage != null && _currentImageId != null) {
      _imageHistory.add(ImageHistoryItem(
        imageData: Uint8List.fromList(_currentImage!),
        imageId: _currentImageId!,
      ));
      
      // 최대 히스토리 크기 유지
      if (_imageHistory.length > _maxHistorySize) {
        _imageHistory.removeAt(0);
      }
      
      print('히스토리 저장: ${_imageHistory.length}개 항목 (ID: $_currentImageId)');
      notifyListeners();
    }
  }
  
  // 이전 상태로 되돌리기 (이미지 데이터 + ID)
  void undo() {
    if (_imageHistory.isNotEmpty) {
      final historyItem = _imageHistory.removeLast();
      _currentImage = Uint8List.fromList(historyItem.imageData);
      _currentImageId = historyItem.imageId; // ✅ ID도 함께 되돌리기
      
      print('뒤로가기: 남은 히스토리 ${_imageHistory.length}개 항목, 복원된 ID: ${historyItem.imageId}');
      
      // 뒤로가기 후에는 현재 이미지 상태만 업데이트하고 setImage는 호출하지 않음
      notifyListeners();
    }
  }
  
  // 원본 이미지로 완전 복원
  Future<void> restoreToOriginal() async {
    if (_originalImage != null) {
      try {
        // 히스토리 저장 후 원본 복원
        saveToHistory();
        _currentImage = Uint8List.fromList(_originalImage!);
        
        // 원본 이미지를 Backend에 새 ID로 업로드
        final apiService = ApiService();
        final uploadResponse = await apiService.uploadImage(_originalImage!, 'restored_original.jpg');
        _currentImageId = uploadResponse.imageId;
        
        print('원본 복원: 새 ID로 업로드 완료 - ${_currentImageId}');
        
        notifyListeners();
      } catch (e) {
        print('원본 복원 실패: $e');
        // 실패해도 Frontend 이미지는 원본으로 복원
        notifyListeners();
      }
    } else {
      print('원본 복원 실패: 원본 이미지가 없습니다');
    }
  }
  
  // 로딩 상태 설정
  void setLoading(bool loading) {
    _isLoading = loading;
    if (loading) {
      _errorMessage = null;
    }
    notifyListeners();
  }
  
  // 컨텍스트 설정 (앱 시작 시 호출)
  void setContext(BuildContext context) {
    _context = context;
  }
  
  // 프리셋 로딩 상태 설정
  void setPresetLoading(String? presetType, [int progress = 0]) {
    _loadingPresetType = presetType;
    _currentProgress = progress;
    if (presetType != null) {
      _errorMessage = null;
    }
    notifyListeners(); // 간단하게 상태만 업데이트
  }
  
  // 워핑 로딩 상태 설정
  void setWarpLoading(bool loading) {
    _isWarpLoading = loading;
    if (loading) {
      _errorMessage = null;
    }
    notifyListeners(); // 간단하게 상태만 업데이트
  }
  
  // 프리셋 설정 변경
  void updatePresetSetting(String presetType, int value) {
    _presetSettings[presetType] = value;
    notifyListeners();
  }
  
  // 프리셋 카운터 증가
  void incrementPresetCounter(String presetType, int shots) {
    _presetCounters[presetType] = (_presetCounters[presetType] ?? 0) + shots;
    notifyListeners();
  }
  
  // 레이저 효과 표시 (이터래이션 수에 따른 지속 시간)
  void activateLaserEffect(String presetType, int iterations) {
    _showLaserEffect = true;
    _currentLaserPreset = presetType;
    _laserIterations = iterations;
    
    // 이터래이션 수에 따른 지속 시간 계산 (각 이터래이션당 1초 + 0.5초 대기)
    _laserDurationMs = (iterations * AnimationConstants.laserIterationDuration).clamp(AnimationConstants.minLaserDuration, AnimationConstants.maxLaserDuration); // 최소 1.5초, 최대 15초
    
    notifyListeners();
    
    // 계산된 시간 후 자동으로 숨김
    Future.delayed(Duration(milliseconds: _laserDurationMs), () {
      _showLaserEffect = false;
      _currentLaserPreset = null;
      _laserIterations = 1;
      _laserDurationMs = AnimationConstants.minLaserDuration;
      notifyListeners();
    });
  }
  
  // 프리셋 카운터 초기화
  void resetPresetCounters() {
    _presetCounters = {
      'lower_jaw': 0,
      'middle_jaw': 0,
      'cheek': 0,
      'front_protusion': 0,
      'back_slit': 0,
    };
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
  
  // 프리셋 시각화 활성화 (현재 임시로 비활성화)
  void showPresetVisualizationFor(String presetType) {
    if (_landmarks.isEmpty) return;
    
    _currentPresetType = presetType;
    _presetVisualizationData = _generatePresetVisualizationData(presetType);
    // _showPresetVisualization = true; // 임시로 주석 처리
    notifyListeners();
    
    // 5초 후 자동으로 숨김
    Future.delayed(const Duration(seconds: 5), () {
      hidePresetVisualization();
    });
  }
  
  // 프리셋 시각화 숨김
  void hidePresetVisualization() {
    _showPresetVisualization = false;
    _currentPresetType = null;
    _presetVisualizationData.clear();
    notifyListeners();
  }
  
  // 프리셋별 시각화 데이터 생성
  Map<String, dynamic> _generatePresetVisualizationData(String presetType) {
    if (_landmarks.isEmpty) return {};
    
    // 얼굴 크기 계산 (백엔드와 동일한 로직)
    final faceLeft = _landmarks[234];
    final faceRight = _landmarks[447];
    final faceWidth = (faceRight.x - faceLeft.x).abs();
    
    List<Map<String, dynamic>> transformations = [];
    
    switch (presetType) {
      case 'lower_jaw':
        transformations = _getLowerJawTransformations(faceWidth);
        break;
      case 'middle_jaw':
        transformations = _getMiddleJawTransformations(faceWidth);
        break;
      case 'cheek':
        transformations = _getCheekTransformations(faceWidth);
        break;
      case 'front_protusion':
        transformations = _getFrontProtusionTransformations(faceWidth);
        break;
      case 'back_slit':
        transformations = _getBackSlitTransformations(faceWidth);
        break;
    }
    
    return {
      'transformations': transformations,
      'presetType': presetType,
      'faceWidth': faceWidth,
    };
  }
  
  // 아래턱 변형 데이터
  List<Map<String, dynamic>> _getLowerJawTransformations(double faceWidth) {
    final leftLandmark = _landmarks[150];
    final rightLandmark = _landmarks[379];
    final targetLandmark = _landmarks[4];
    final influenceRadius = faceWidth * 0.4;
    
    return [
      _createTransformationData(leftLandmark, targetLandmark, influenceRadius, 0.05, 0.1),
      _createTransformationData(rightLandmark, targetLandmark, influenceRadius, 0.05, 0.1),
    ];
  }
  
  // 중간턱 변형 데이터
  List<Map<String, dynamic>> _getMiddleJawTransformations(double faceWidth) {
    final leftLandmark = _landmarks[172];
    final rightLandmark = _landmarks[397];
    final targetLandmark = _landmarks[4];
    final influenceRadius = faceWidth * 0.65;
    
    return [
      _createTransformationData(leftLandmark, targetLandmark, influenceRadius, 0.05, 0.1),
      _createTransformationData(rightLandmark, targetLandmark, influenceRadius, 0.05, 0.1),
    ];
  }
  
  // 볼 변형 데이터
  List<Map<String, dynamic>> _getCheekTransformations(double faceWidth) {
    final leftLandmark = _landmarks[215];
    final rightLandmark = _landmarks[435];
    final targetLandmark = _landmarks[4];
    final influenceRadius = faceWidth * 0.65;
    
    return [
      _createTransformationData(leftLandmark, targetLandmark, influenceRadius, 0.05, 0.1),
      _createTransformationData(rightLandmark, targetLandmark, influenceRadius, 0.05, 0.1),
    ];
  }
  
  // 앞트임 변형 데이터
  List<Map<String, dynamic>> _getFrontProtusionTransformations(double faceWidth) {
    final landmark243 = _landmarks[243];
    final landmark463 = _landmarks[463];
    final influenceRadius = faceWidth * 0.1; // 예전 방식: 10%
    
    // 중간점들 계산
    final mid56190 = Landmark(
      x: (_landmarks[56].x + _landmarks[190].x) / 2,
      y: (_landmarks[56].y + _landmarks[190].y) / 2,
      index: -1,
    );
    final mid414286 = Landmark(
      x: (_landmarks[414].x + _landmarks[286].x) / 2,
      y: (_landmarks[414].y + _landmarks[286].y) / 2,
      index: -1,
    );
    
    // 타겟 중간점 (예전 방식: 코 중심)
    final targetMid = Landmark(
      x: (_landmarks[168].x + _landmarks[6].x) / 2,
      y: (_landmarks[168].y + _landmarks[6].y) / 2,
      index: -1,
    );
    
    return [
      _createTransformationData(landmark243, targetMid, influenceRadius, 0.3, 0.1, ellipseRatio: 1.3),
      _createTransformationData(landmark463, targetMid, influenceRadius, 0.3, 0.1, ellipseRatio: 1.3),
      _createTransformationData(mid56190, targetMid, influenceRadius, 0.3, 0.1, ellipseRatio: 1.3),
      _createTransformationData(mid414286, targetMid, influenceRadius, 0.3, 0.1, ellipseRatio: 1.3),
    ];
  }
  
  // 뒷트임 변형 데이터
  List<Map<String, dynamic>> _getBackSlitTransformations(double faceWidth) {
    final landmark33 = _landmarks[33];
    final landmark359 = _landmarks[359];
    final influenceRadius = faceWidth * 0.1; // 예전 방식: 10%
    
    // 타겟 중간점들
    final mid34162 = Landmark(
      x: (_landmarks[34].x + _landmarks[162].x) / 2,
      y: (_landmarks[34].y + _landmarks[162].y) / 2,
      index: -1,
    );
    final mid368264 = Landmark(
      x: (_landmarks[368].x + _landmarks[264].x) / 2,
      y: (_landmarks[368].y + _landmarks[264].y) / 2,
      index: -1,
    );
    
    return [
      _createTransformationData(landmark33, mid34162, influenceRadius, 0.5, 0.1),
      _createTransformationData(landmark359, mid368264, influenceRadius, 0.5, 0.1),
    ];
  }
  
  // 변형 데이터 생성 헬퍼
  Map<String, dynamic> _createTransformationData(
    Landmark startLandmark, 
    Landmark targetLandmark, 
    double influenceRadius, 
    double strength, 
    double pullRatio,
    {double? ellipseRatio}
  ) {
    final distance = math.sqrt(
      math.pow(startLandmark.x - targetLandmark.x, 2) + 
      math.pow(startLandmark.y - targetLandmark.y, 2)
    );
    final pullDistance = distance * pullRatio;
    
    // 방향 벡터 계산
    final dx = targetLandmark.x - startLandmark.x;
    final dy = targetLandmark.y - startLandmark.y;
    final norm = math.sqrt(dx * dx + dy * dy);
    
    final endX = norm > 0 ? startLandmark.x + (dx / norm) * pullDistance : startLandmark.x;
    final endY = norm > 0 ? startLandmark.y + (dy / norm) * pullDistance : startLandmark.y;
    
    return {
      'startX': startLandmark.x,
      'startY': startLandmark.y,
      'endX': endX,
      'endY': endY,
      'influenceRadius': influenceRadius,
      'strength': strength,
      'pullDistance': pullDistance,
      'distance': distance,
      'ellipseRatio': ellipseRatio,
    };
  }
  
  // 자동 애니메이션 중단
  void stopAutoAnimation() {
    _isAutoAnimationMode = false;
    _isAnimationPlaying = false;
    _currentAnimatingRegion = null;
    notifyListeners();
  }

  // 현재 탭 인덱스 설정
  void setCurrentTabIndex(int index) {
    _currentTabIndex = index;
    
    // 프리셋 탭(1)이나 프리스타일 탭(2)으로 전환 시 뷰티스코어 시각화 숨김
    if (index == 1 || index == 2) {
      _showBeautyScore = false;
      _isAutoAnimationMode = false;
      _isAnimationPlaying = false;
      _currentAnimatingRegion = null;
      _beautyScoreAnimationProgress = 0.0;
      _showLandmarks = false; // 랜드마크 시각화 숨기기
      _beautyAnalysis.clear(); // 뷰티 분석 데이터 클리어
      
      // 모든 부위 시각화 숨기기
      for (final regionKey in _regionVisibility.all.keys) {
        _regionVisibility.setVisible(regionKey, false);
      }
      
      // 랜드마크 애니메이션 진행률 초기화
      _animationProgress.clear();
      
      stopAutoAnimation(); // 진행 중인 애니메이션 중단
    }
    
    notifyListeners();
  }

  // 원본 이미지로 복원 (전문가 탭 전용)
  void restoreOriginalImage() {
    if (_originalImage != null) {
      _currentImage = Uint8List.fromList(_originalImage!);
      _showBeautyScore = false; // 뷰티 스코어 숨기기
      _beautyScoreAnimationProgress = 0.0;
      _beautyAnalysis.clear();
      _showLandmarks = false; // 랜드마크 시각화 숨기기
      
      // 모든 부위 시각화 숨기기
      for (final regionKey in _regionVisibility.all.keys) {
        _regionVisibility.setVisible(regionKey, false);
      }
      
      stopAutoAnimation(); // 진행 중인 애니메이션 중단
      notifyListeners();
    }
  }

  // 뷰티 스코어 애니메이션 시작
  Future<void> _startBeautyScoreAnimation() async {
    _beautyScoreAnimationProgress = 0.0;
    notifyListeners();
    
    const duration = Duration(milliseconds: AnimationConstants.beautyScoreAnimationDuration); // 2초 동안 애니메이션
    const steps = AnimationConstants.beautyScoreAnimationSteps; // 60 프레임
    const stepDuration = Duration(milliseconds: AnimationConstants.beautyScoreStepDuration); // ~60 FPS
    
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

  // 뷰티 분석 계산
  void _calculateBeautyAnalysis() {
    if (_landmarks.isEmpty) return;

    try {
      // 시각화 기반 정밀 점수 계산
      final verticalAnalysis = _calculateVerticalScoreFromVisualization();
      final horizontalAnalysis = _calculateHorizontalScoreFromVisualization();
      final lowerFaceAnalysis = _calculateLowerFaceScoreFromVisualization();
      
      // 기본 분석들
      final facialSymmetry = _calculateFacialSymmetry();
      final eyeAnalysis = _calculateEyeAnalysis();
      final noseAnalysis = _calculateNoseAnalysis();
      final lipAnalysis = _calculateLipAnalysis();
      final jawlineAnalysis = _calculateJawlineAnalysis();

      // 종합 점수 계산 (시각화 기반)
      final overallScore = _calculateOverallBeautyScoreFromVisualization(
        verticalScore: verticalAnalysis['score'] ?? 75.0,
        horizontalScore: horizontalAnalysis['score'] ?? 75.0,
        lowerFaceScore: lowerFaceAnalysis['score'] ?? 75.0,
        symmetry: facialSymmetry,
        eyeScore: eyeAnalysis['score'] ?? 70.0,
        noseScore: noseAnalysis['score'] ?? 70.0,
        lipScore: lipAnalysis['score'] ?? 70.0,
        jawScore: jawlineAnalysis['score'] ?? 70.0,
      );

      _beautyAnalysis = {
        'overallScore': overallScore,
        'verticalScore': verticalAnalysis,
        'horizontalScore': horizontalAnalysis, 
        'lowerFaceScore': lowerFaceAnalysis,
        'symmetry': facialSymmetry,
        'eyes': eyeAnalysis,
        'nose': noseAnalysis,
        'lips': lipAnalysis,
        'jawline': jawlineAnalysis,
        'analysisTimestamp': DateTime.now(),
      };
    } catch (e) {
      // 오류 발생 시 기본값 설정
      _beautyAnalysis = {
        'overallScore': 75.0,
        'error': 'Analysis calculation failed',
      };
    }
  }

  // 얼굴 비율 계산
  double _calculateFaceProportions() {
    if (_landmarks.length < 468) return 75.0;

    try {
      // 얼굴 길이/너비 비율 (1.618이 황금비율)
      final faceWidth = (_landmarks[454].x - _landmarks[234].x).abs();
      final faceHeight = (_landmarks[10].y - _landmarks[152].y).abs();
      final ratio = faceHeight / faceWidth;
      
      // 황금비율(1.618)에 가까울수록 높은 점수
      final score = 100 - ((ratio - 1.618).abs() * 50);
      return score.clamp(50.0, 100.0);
    } catch (e) {
      return 75.0;
    }
  }

  // 얼굴 대칭성 계산
  double _calculateFacialSymmetry() {
    if (_landmarks.length < 468) return 75.0;

    try {
      // 주요 대칭점들 비교
      final leftEye = _landmarks[33];
      final rightEye = _landmarks[362];
      final noseTip = _landmarks[1];
      final leftMouth = _landmarks[61];
      final rightMouth = _landmarks[291];
      
      // 얼굴 중심선 계산
      final centerX = (leftEye.x + rightEye.x) / 2;
      final faceWidth = (rightEye.x - leftEye.x).abs();
      
      // 대칭성 점수 계산
      final eyeSymmetry = 1.0 - ((leftEye.x - centerX).abs() - (centerX - rightEye.x).abs()).abs() / faceWidth;
      final mouthSymmetry = 1.0 - ((leftMouth.x - centerX).abs() - (centerX - rightMouth.x).abs()).abs() / faceWidth;
      
      final symmetryScore = (eyeSymmetry + mouthSymmetry) / 2 * 100;
      return symmetryScore.clamp(50.0, 100.0);
    } catch (e) {
      return 75.0;
    }
  }

  // 황금비율 분석
  double _calculateGoldenRatio() {
    if (_landmarks.length < 468) return 75.0;

    try {
      // 얼굴의 1/3 비율 분석
      final hairline = _landmarks[10];
      final eyebrow = _landmarks[9];
      final noseTip = _landmarks[2];
      final chin = _landmarks[152];
      
      final upperThird = (eyebrow.y - hairline.y).abs();
      final middleThird = (noseTip.y - eyebrow.y).abs();
      final lowerThird = (chin.y - noseTip.y).abs();
      
      final total = upperThird + middleThird + lowerThird;
      final idealRatio = total / 3;
      
      // 각 부분이 1/3에 얼마나 가까운지 계산
      final upperScore = 1.0 - (upperThird - idealRatio).abs() / idealRatio;
      final middleScore = 1.0 - (middleThird - idealRatio).abs() / idealRatio;
      final lowerScore = 1.0 - (lowerThird - idealRatio).abs() / idealRatio;
      
      final goldenScore = (upperScore + middleScore + lowerScore) / 3 * 100;
      return goldenScore.clamp(50.0, 100.0);
    } catch (e) {
      return 75.0;
    }
  }

  // 눈 분석
  Map<String, dynamic> _calculateEyeAnalysis() {
    if (_landmarks.length < 468) return {'score': 75.0};

    try {
      // 눈 크기와 모양 분석
      final leftEyeWidth = (_landmarks[33].x - _landmarks[133].x).abs();
      final rightEyeWidth = (_landmarks[362].x - _landmarks[263].x).abs();
      final eyeDistance = (_landmarks[362].x - _landmarks[33].x).abs();
      
      // 이상적인 비율 (눈 간격이 한 눈 크기와 비슷해야 함)
      final avgEyeWidth = (leftEyeWidth + rightEyeWidth) / 2;
      final idealRatio = eyeDistance / avgEyeWidth;
      
      final eyeScore = 100 - ((idealRatio - 1.0).abs() * 30);
      
      return {
        'score': eyeScore.clamp(50.0, 100.0),
        'leftWidth': leftEyeWidth,
        'rightWidth': rightEyeWidth,
        'distance': eyeDistance,
        'symmetry': 1.0 - (leftEyeWidth - rightEyeWidth).abs() / avgEyeWidth,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  // 코 분석
  Map<String, dynamic> _calculateNoseAnalysis() {
    if (_landmarks.length < 468) return {'score': 75.0};

    try {
      final noseTip = _landmarks[2];
      final noseLeft = _landmarks[31];
      final noseRight = _landmarks[35];
      final noseBridge = _landmarks[9];
      
      final noseWidth = (noseRight.x - noseLeft.x).abs();
      final noseHeight = (noseTip.y - noseBridge.y).abs();
      final noseRatio = noseHeight / noseWidth;
      
      // 이상적인 코 비율 분석
      final noseScore = 100 - ((noseRatio - 1.2).abs() * 40);
      
      return {
        'score': noseScore.clamp(50.0, 100.0),
        'width': noseWidth,
        'height': noseHeight,
        'ratio': noseRatio,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  // 입술 분석
  Map<String, dynamic> _calculateLipAnalysis() {
    if (_landmarks.length < 468) return {'score': 75.0};

    try {
      final upperLip = _landmarks[13];
      final lowerLip = _landmarks[18];
      final leftMouth = _landmarks[61];
      final rightMouth = _landmarks[291];
      
      final lipWidth = (rightMouth.x - leftMouth.x).abs();
      final lipHeight = (lowerLip.y - upperLip.y).abs();
      final lipRatio = lipWidth / lipHeight;
      
      // 이상적인 입술 비율
      final lipScore = 100 - ((lipRatio - 3.0).abs() * 20);
      
      return {
        'score': lipScore.clamp(50.0, 100.0),
        'width': lipWidth,
        'height': lipHeight,
        'ratio': lipRatio,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  // 턱선 분석
  Map<String, dynamic> _calculateJawlineAnalysis() {
    if (_landmarks.length < 468) return {'score': 75.0};

    try {
      // 기존 턱곡률 계산 로직 활용
      final gonialAngle = _calculateGonialAngleValue();
      final cervicoMentalAngle = _calculateCervicoMentalAngleValue();
      
      if (gonialAngle == null || cervicoMentalAngle == null) {
        return {'score': 75.0};
      }
      
      final liftingScore = _calculateLiftingScoreValue(gonialAngle, cervicoMentalAngle);
      
      return {
        'score': liftingScore.clamp(50.0, 100.0),
        'gonialAngle': gonialAngle,
        'cervicoMentalAngle': cervicoMentalAngle,
        'liftingScore': liftingScore,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  // 종합 점수 계산
  double _calculateOverallBeautyScore({
    required double faceProportions,
    required double symmetry,
    required double goldenRatio,
    required double eyeScore,
    required double noseScore,
    required double lipScore,
    required double jawScore,
  }) {
    // 가중평균 계산 (각 요소별 중요도 반영)
    final weightedScore = 
        (faceProportions * 0.20) +  // 얼굴 비율 20%
        (symmetry * 0.25) +         // 대칭성 25%
        (goldenRatio * 0.15) +      // 황금비율 15%
        (eyeScore * 0.15) +         // 눈 15%
        (noseScore * 0.10) +        // 코 10%
        (lipScore * 0.10) +         // 입술 10%
        (jawScore * 0.05);          // 턱선 5%
    
    return weightedScore.clamp(50.0, 100.0);
  }

  // 기존 턱곡률 계산 메서드들을 재사용하기 위한 헬퍼 메서드들
  double? _calculateGonialAngleValue() {
    final requiredIndices = [234, 172, 150, 454, 397, 379];
    if (requiredIndices.any((i) => i >= _landmarks.length)) return null;
    
    final leftGonial = _calculateJawAngleImprovedValue(_landmarks[234], _landmarks[172], _landmarks[150]);
    final rightGonial = _calculateJawAngleImprovedValue(_landmarks[454], _landmarks[397], _landmarks[379]);
    
    if (leftGonial == null || rightGonial == null) return null;
    return (leftGonial + rightGonial) / 2;
  }

  double? _calculateCervicoMentalAngleValue() {
    if (152 >= _landmarks.length || 18 >= _landmarks.length) return null;
    
    final chin = _landmarks[152];
    final neckFront = _landmarks[18];
    final neckBottomX = chin.x;
    final neckBottomY = chin.y + (chin.y - neckFront.y).abs() * 1.5;
    
    return _calculateAngle3PointsValue(
      Offset(neckBottomX, neckBottomY),
      Offset(chin.x, chin.y),
      Offset(neckFront.x, neckFront.y),
    );
  }

  double? _calculateJawAngleImprovedValue(Landmark earPoint, Landmark jawCorner, Landmark jawMid) {
    const verticalVector = Offset(0, 1);
    final jawVector = Offset(jawMid.x - jawCorner.x, jawMid.y - jawCorner.y);
    final jawLength = jawVector.distance;
    if (jawLength == 0) return null;
    
    final jawUnit = jawVector / jawLength;
    final dotProduct = verticalVector.dx * jawUnit.dx + verticalVector.dy * jawUnit.dy;
    final cosAngle = dotProduct.clamp(-1.0, 1.0);
    final angleRad = math.acos(cosAngle.abs());
    final angleDeg = angleRad * 180 / math.pi;
    
    return 90 + angleDeg;
  }

  double? _calculateAngle3PointsValue(Offset p1, Offset p2, Offset p3) {
    final v1 = p1 - p2;
    final v2 = p3 - p2;
    final len1 = v1.distance;
    final len2 = v2.distance;
    
    if (len1 == 0 || len2 == 0) return null;
    
    final dotProduct = v1.dx * v2.dx + v1.dy * v2.dy;
    final cosAngle = (dotProduct / (len1 * len2)).clamp(-1.0, 1.0);
    final angleRad = math.acos(cosAngle);
    return angleRad * 180 / math.pi;
  }

  double _calculateLiftingScoreValue(double gonialAngle, double cervicoMentalAngle) {
    double gonialScore;
    if (gonialAngle <= 90) {
      gonialScore = 100;
    } else if (gonialAngle <= 120) {
      gonialScore = 100 - ((gonialAngle - 90) * 20 / 30);
    } else if (gonialAngle <= 140) {
      gonialScore = 80 - ((gonialAngle - 120) * 60 / 20);
    } else {
      gonialScore = (20 - ((gonialAngle - 140) * 20 / 10)).clamp(0.0, 20.0);
    }
    
    double cervicoScore;
    if (105 <= cervicoMentalAngle && cervicoMentalAngle <= 115) {
      cervicoScore = 100;
    } else if (100 <= cervicoMentalAngle && cervicoMentalAngle <= 120) {
      cervicoScore = 90 - (cervicoMentalAngle - 110).abs() * 2;
    } else if (90 <= cervicoMentalAngle && cervicoMentalAngle <= 130) {
      cervicoScore = 70 - (cervicoMentalAngle - 110).abs() * 1.5;
    } else {
      cervicoScore = (70 - (cervicoMentalAngle - 110).abs() * 2).clamp(40.0, 70.0);
    }
    
    final liftingScore = gonialScore * 0.7 + cervicoScore * 0.3;
    return liftingScore.clamp(0.0, 100.0);
  }

  // =============================================================================
  // 시각화 기반 정밀 점수 계산 메서드들
  // =============================================================================

  /// 세로 점수 계산 (중앙 5개 원 비율 기반)
  Map<String, dynamic> _calculateVerticalScoreFromVisualization() {
    try {
      // 시각화에서 사용하는 랜드마크들
      final verticalLandmarks = [234, 33, 133, 362, 359, 447];
      if (verticalLandmarks.any((i) => i >= _landmarks.length) || 10 >= _landmarks.length) {
        return {'score': 75.0};
      }

      final verticalXPositions = verticalLandmarks
          .map((i) => _landmarks[i].x)
          .toList();

      final radiuses = <double>[];
      for (int i = 0; i < verticalXPositions.length - 1; i++) {
        radiuses.add((verticalXPositions[i + 1] - verticalXPositions[i]).abs() / 2);
      }

      final totalDiameter = radiuses.reduce((a, b) => a + b) * 2;
      final percentages = radiuses.map((r) => ((r * 2) / totalDiameter) * 100).toList();

      // 황금비율과의 차이 계산 (이상적인 비율 20% 씩)
      final idealRatio = 20.0;
      double totalDeviation = 0.0;
      for (final percentage in percentages) {
        totalDeviation += (percentage - idealRatio).abs();
      }

      final score = (100 - (totalDeviation * 2)).clamp(50.0, 100.0);

      return {
        'score': score,
        'percentages': percentages,
        'totalDeviation': totalDeviation,
        'sections': percentages.length,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 가로 점수 계산 (오른쪽 2개 원 비율 기반)
  Map<String, dynamic> _calculateHorizontalScoreFromVisualization() {
    try {
      final yPositions = [8, 2, 152]
          .where((i) => i < _landmarks.length)
          .map((i) => _landmarks[i].y)
          .toList();

      if (yPositions.length < 3) {
        return {'score': 75.0};
      }

      final radius1 = (yPositions[1] - yPositions[0]).abs() / 2;
      final radius2 = (yPositions[2] - yPositions[1]).abs() / 2;
      final totalDiameter = (radius1 + radius2) * 2;

      final percentage1 = ((radius1 * 2) / totalDiameter) * 100;
      final percentage2 = ((radius2 * 2) / totalDiameter) * 100;

      // 이상적인 비율은 50:50
      final idealRatio = 50.0;
      final deviation1 = (percentage1 - idealRatio).abs();
      final deviation2 = (percentage2 - idealRatio).abs();
      final totalDeviation = deviation1 + deviation2;

      final score = (100 - (totalDeviation * 1.5)).clamp(50.0, 100.0);

      return {
        'score': score,
        'upperPercentage': percentage1,
        'lowerPercentage': percentage2,
        'deviation': totalDeviation,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 하관 점수 계산 (왼쪽 2개 원 비율 기반)
  Map<String, dynamic> _calculateLowerFaceScoreFromVisualization() {
    try {
      final yPositions = [2, 37, 152]
          .where((i) => i < _landmarks.length)
          .map((i) => _landmarks[i].y)
          .toList();

      if (yPositions.length < 3) {
        return {'score': 75.0};
      }

      final radius1 = (yPositions[1] - yPositions[0]).abs() / 2;
      final radius2 = (yPositions[2] - yPositions[1]).abs() / 2;
      final totalDiameter = (radius1 + radius2) * 2;

      final percentage1 = ((radius1 * 2) / totalDiameter) * 100;
      final percentage2 = ((radius2 * 2) / totalDiameter) * 100;

      // 황금비율 기준: 상단 33%, 하단 67%가 이상적
      final idealUpper = 33.0;
      final idealLower = 67.0;
      final deviation1 = (percentage1 - idealUpper).abs();
      final deviation2 = (percentage2 - idealLower).abs();
      final totalDeviation = deviation1 + deviation2;

      final score = (100 - (totalDeviation * 1.2)).clamp(50.0, 100.0);

      return {
        'score': score,
        'upperPercentage': percentage1,
        'lowerPercentage': percentage2,
        'deviation': totalDeviation,
      };
    } catch (e) {
      return {'score': 75.0};
    }
  }

  /// 시각화 기반 종합 점수 계산
  double _calculateOverallBeautyScoreFromVisualization({
    required double verticalScore,
    required double horizontalScore,
    required double lowerFaceScore,
    required double symmetry,
    required double eyeScore,
    required double noseScore,
    required double lipScore,
    required double jawScore,
  }) {
    // 가중평균 계산 (시각화 기반 비율 점수를 높게 반영)
    final weightedScore = 
        (verticalScore * 0.25) +    // 세로 비율 25%
        (horizontalScore * 0.20) +  // 가로 비율 20%
        (lowerFaceScore * 0.15) +   // 하관 비율 15%
        (symmetry * 0.15) +         // 대칭성 15%
        (eyeScore * 0.10) +         // 눈 10%
        (noseScore * 0.08) +        // 코 8%
        (lipScore * 0.05) +         // 입술 5%
        (jawScore * 0.02);          // 턱선 2%
    
    return weightedScore.clamp(50.0, 100.0);
  }

  
  // 상태 리셋
  void reset() {
    stopAutoAnimation(); // 애니메이션 중단
    _currentImage = null;
    _originalImage = null;
    _currentImageId = null;
    _imageWidth = 0;
    _imageHeight = 0;
    _landmarks.clear();
    _showLandmarks = false;
    _showBeautyScore = false;
    _beautyScoreAnimationProgress = 0.0;
    _beautyAnalysis.clear();
    _animationProgress.clear();
    _currentAnimationIndex = 0;
    _currentTabIndex = 0; // 분석 탭으로 초기화
    _warpMode = WarpMode.pull;
    _influenceRadiusPercent = 5.0;
    _warpStrength = 1.0;
    _imageHistory.clear(); // 히스토리 초기화
    _isLoading = false;
    _errorMessage = null;
    notifyListeners();
  }
}

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
}

/// 워핑 모드 열거형
enum WarpMode {
  pull('pull', '당기기', '선택한 점을 드래그 방향으로 당김'),
  push('push', '밀어내기', '선택한 점을 드래그 방향으로 밀어냄'),
  expand('expand', '축소', '선택한 점 주변을 방사형으로 축소'),
  shrink('shrink', '확대', '선택한 점 주변을 방사형으로 확대');
  
  const WarpMode(this.value, this.displayName, this.description);
  
  final String value;
  final String displayName;
  final String description;
}