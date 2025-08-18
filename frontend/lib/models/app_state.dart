import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../state/image_state.dart';
import '../state/warp_state.dart';
import '../state/animation_state.dart';
import '../state/preset_state.dart';
import '../state/beauty_analysis_state.dart';
import '../state/ui_state.dart';
import '../services/api_service.dart';
import 'image_models.dart';

/// BeautyGen 앱의 전역 상태 관리 (리팩토링된 버전)
class AppState extends ChangeNotifier {
  // 분리된 상태들
  final ImageState _imageState = ImageState();
  final WarpState _warpState = WarpState();
  final AnimationState _animationState = AnimationState();
  final PresetState _presetState = PresetState();
  final BeautyAnalysisState _beautyAnalysisState = BeautyAnalysisState();
  final UiState _uiState = UiState();
  

  AppState() {
    // 상태 변경 리스너 등록
    _imageState.addListener(_onStateChanged);
    _warpState.addListener(_onStateChanged);
    _animationState.addListener(_onStateChanged);
    _presetState.addListener(_onStateChanged);
    _beautyAnalysisState.addListener(_onStateChanged);
    _uiState.addListener(_onStateChanged);
  }

  @override
  void dispose() {
    _imageState.removeListener(_onStateChanged);
    _warpState.removeListener(_onStateChanged);
    _animationState.removeListener(_onStateChanged);
    _presetState.removeListener(_onStateChanged);
    _beautyAnalysisState.removeListener(_onStateChanged);
    _uiState.removeListener(_onStateChanged);
    
    _imageState.dispose();
    _warpState.dispose();
    _animationState.dispose();
    _presetState.dispose();
    _beautyAnalysisState.dispose();
    _uiState.dispose();
    
    super.dispose();
  }

  /// 하위 상태 변경 시 알림
  void _onStateChanged() {
    notifyListeners();
  }

  // === 이미지 상태 위임 ===
  Uint8List? get currentImage => _imageState.currentImage;
  Uint8List? get originalImage => _imageState.originalImage;
  String? get currentImageId => _imageState.currentImageId;
  int get imageWidth => _imageState.imageWidth;
  int get imageHeight => _imageState.imageHeight;
  bool get canUndo => _imageState.canUndo;
  double get zoomScale => _imageState.zoomScale;
  Offset get panOffset => _imageState.panOffset;
  bool get showOriginalImage => _imageState.showOriginalImage;
  Uint8List? get displayImage => _imageState.displayImage;

  void setImage(Uint8List imageData, String imageId, int width, int height) {
    _imageState.setImage(imageData, imageId, width, height);
    _animationState.reset(); // 애니메이션 초기화
    _beautyAnalysisState.resetForNewImage(); // 뷰티 분석 초기화
  }

  void updateCurrentImage(Uint8List imageData) => _imageState.updateCurrentImage(imageData);
  void updateCurrentImageWithId(Uint8List imageData, String newImageId) => 
      _imageState.updateCurrentImage(imageData, newImageId);
  void setCurrentImage(Uint8List imageData) => _imageState.setCurrentImage(imageData);
  void updateImageFromPreset(Uint8List imageData, String imageId) => 
      _imageState.updateCurrentImage(imageData, imageId);
  
  void undo() => _imageState.undo();
  void saveToHistory() => _imageState.saveToHistory();
  Future<void> restoreToOriginal() => _imageState.restoreToOriginal();
  void setZoomScale(double scale) => _imageState.setZoomScale(scale);
  void setPanOffset(Offset offset) => _imageState.setPanOffset(offset);
  void addPanOffset(Offset delta) => _imageState.addPanOffset(delta);
  void resetZoom() => _imageState.resetZoom();
  void toggleOriginalImage() => _imageState.toggleOriginalImage();
  void setShowOriginalImage(bool show) => _imageState.setShowOriginalImage(show);

  // === 워핑 상태 위임 ===
  WarpMode get warpMode => _warpState.warpMode;
  double get influenceRadiusPercent => _warpState.influenceRadiusPercent;
  double get warpStrength => _warpState.warpStrength;
  bool get isWarpLoading => _warpState.isWarpLoading;

  void setWarpMode(WarpMode mode) => _warpState.setWarpMode(mode);
  void setInfluenceRadiusPercent(double percent) => _warpState.setInfluenceRadiusPercent(percent);
  void setWarpStrength(double strength) => _warpState.setWarpStrength(strength);
  void setWarpLoading(bool loading) => _warpState.setWarpLoading(loading);
  double getInfluenceRadiusPixels() => _warpState.getInfluenceRadiusPixels(imageWidth, imageHeight);
  double getInfluenceRadiusForDisplay(Size containerSize) => 
      _warpState.getInfluenceRadiusForDisplay(containerSize, imageWidth, imageHeight);

  // === 애니메이션 상태 위임 ===
  List<Landmark> get landmarks => _animationState.landmarks;
  bool get showLandmarks => _animationState.showLandmarks;
  get regionVisibility => _animationState.regionVisibility;
  bool get isAnimationPlaying => _animationState.isAnimationPlaying;
  String? get currentAnimatingRegion => _animationState.currentAnimatingRegion;
  Map<String, double> get animationProgress => _animationState.animationProgress;
  bool get isAutoAnimationMode => _animationState.isAutoAnimationMode;

  void setLandmarks(List<Landmark> landmarks, {bool resetAnalysis = true}) {
    _animationState.setLandmarks(landmarks, resetAnalysis: resetAnalysis);
    
    // 분석 탭(index 0)에서만 자동 애니메이션 시작
    if (landmarks.isNotEmpty && (_uiState.currentTabIndex == 0 || _beautyAnalysisState.isReAnalyzing) && resetAnalysis) {
      _animationState.startAutoAnimation().then((_) {
        // 애니메이션 완료 후 뷰티 분석 시작
        _beautyAnalysisState.calculateBeautyAnalysis(landmarks);
        _beautyAnalysisState.setShowBeautyScore(true);
      });
    }
  }

  void toggleLandmarks() => _animationState.toggleLandmarks();
  void toggleRegionVisibility(String region) => _animationState.toggleRegionVisibility(region);
  void startRegionAnimation(String regionKey) => _animationState.startRegionAnimation(regionKey);
  void updateAnimationProgress(String regionKey, double progress) => 
      _animationState.updateAnimationProgress(regionKey, progress);
  void stopAnimation() => _animationState.stopAnimation();
  void stopAutoAnimation() => _animationState.stopAutoAnimation();
  void completeAllAnimations() {
    _animationState.completeAllAnimations();
    if (landmarks.isNotEmpty) {
      _beautyAnalysisState.completeBeautyAnalysis(landmarks);
    }
  }

  // === 프리셋 상태 위임 ===
  Map<String, int> get presetCounters => _presetState.presetCounters;
  Map<String, int> get presetSettings => _presetState.presetSettings;
  String? get loadingPresetType => _presetState.loadingPresetType;
  int get currentProgress => _presetState.currentProgress;
  bool get showLaserEffect => _presetState.showLaserEffect;
  String? get currentLaserPreset => _presetState.currentLaserPreset;
  int get laserIterations => _presetState.laserIterations;
  int get laserDurationMs => _presetState.laserDurationMs;
  bool get showPresetVisualization => _presetState.showPresetVisualization;
  String? get currentPresetType => _presetState.currentPresetType;
  Map<String, dynamic> get presetVisualizationData => _presetState.presetVisualizationData;

  bool isPresetLoading(String presetType) => _presetState.isPresetLoading(presetType);
  void setPresetLoading(String? presetType, [int progress = 0]) => 
      _presetState.setPresetLoading(presetType, progress);
  void updatePresetSetting(String presetType, int value) => 
      _presetState.updatePresetSetting(presetType, value);
  void incrementPresetCounter(String presetType, int shots) => 
      _presetState.incrementPresetCounter(presetType, shots);
  void activateLaserEffect(String presetType, int iterations) => 
      _presetState.activateLaserEffect(presetType, iterations);
  void resetPresetCounters() => _presetState.resetPresetCounters();
  void showPresetVisualizationFor(String presetType) => 
      _presetState.showPresetVisualizationFor(presetType);
  void hidePresetVisualization() => _presetState.hidePresetVisualization();

  // === 뷰티 분석 상태 위임 ===
  bool get showBeautyScore => _beautyAnalysisState.showBeautyScore;
  double get beautyScoreAnimationProgress => _beautyAnalysisState.beautyScoreAnimationProgress;
  Map<String, dynamic> get beautyAnalysis => _beautyAnalysisState.beautyAnalysis;
  bool get beautyAnalysisCompleted => _beautyAnalysisState.beautyAnalysisCompleted;
  Map<String, dynamic>? get originalBeautyAnalysis => _beautyAnalysisState.originalBeautyAnalysis;
  bool get isReAnalyzing => _beautyAnalysisState.isReAnalyzing;
  bool get isGptAnalyzing => _beautyAnalysisState.isGptAnalyzing;

  Future<void> startReAnalysis() async {
    await _beautyAnalysisState.startReAnalysis(currentImageId);
    
    // 뷰티스코어 탭으로 이동
    setCurrentTabIndex(0);
    
    // 랜드마크 재검출 및 분석 시작
    if (currentImageId != null) {
      try {
        setLoading(true);
        final apiService = ApiService();
        final landmarkResponse = await apiService.getFaceLandmarks(currentImageId!);
        setLandmarks(landmarkResponse.landmarks, resetAnalysis: true);
        setLoading(false);
      } catch (e) {
        setError('재진단 실패: $e');
      }
    }
  }

  // === UI 상태 위임 ===
  bool get isLoading => _uiState.isLoading;
  String? get errorMessage => _uiState.errorMessage;
  int get currentTabIndex => _uiState.currentTabIndex;

  void setLoading(bool loading) => _uiState.setLoading(loading);
  void setError(String error) => _uiState.setError(error);
  void clearError() => _uiState.clearError();
  
  void setCurrentTabIndex(int index) {
    // 재진단 중일 때 다른 탭으로 전환하면 재진단 취소
    if (_beautyAnalysisState.isReAnalyzing && index != 0) {
      _beautyAnalysisState.completeReAnalysis();
      completeAllAnimations();
    }
    
    // 뷰티스코어 탭에서 다른 탭으로 전환 시 애니메이션 즉시 완료
    if (_uiState.currentTabIndex == 0 && index != 0 && 
        (_animationState.isAnimationPlaying || _animationState.isAutoAnimationMode)) {
      completeAllAnimations();
    }
    
    _uiState.setCurrentTabIndex(index);
    _beautyAnalysisState.handleTabChange(index);
    _animationState.handleTabChange(index);
  }

  // === 추가 메서드들 ===

  /// 원본 이미지로 복원 (전문가 탭 전용)
  void restoreOriginalImage() {
    if (_imageState.originalImage != null) {
      _imageState.updateCurrentImage(_imageState.originalImage!);
      _beautyAnalysisState.resetForNewImage();
      _animationState.reset();
    }
  }

  /// 전체 상태 리셋
  void reset() {
    _imageState.reset();
    _warpState.reset();
    _animationState.reset();
    _presetState.reset();
    _beautyAnalysisState.reset();
    _uiState.reset();
  }
}