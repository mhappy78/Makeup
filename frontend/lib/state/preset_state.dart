import 'package:flutter/foundation.dart';
import '../config/animation_constants.dart';
import '../models/image_models.dart';

/// 프리셋 상태 관리
class PresetState extends ChangeNotifier {
  // 프리셋 관련 상태
  Map<String, int> _presetCounters = {
    'lower_jaw': 0,
    'middle_jaw': 0,
    'cheek': 0,
    'front_protusion': 0,
    'back_slit': 0,
  };
  
  Map<String, int> _presetSettings = {
    'lower_jaw': 300,
    'middle_jaw': 300,
    'cheek': 300,
    'front_protusion': 3,
    'back_slit': 3,
  };
  
  // 프리셋 로딩 상태
  String? _loadingPresetType;
  int _currentProgress = 0;
  
  // 레이저 시각화 상태
  bool _showLaserEffect = false;
  String? _currentLaserPreset;
  int _laserIterations = 1;
  int _laserDurationMs = AnimationConstants.minLaserDuration;
  
  // 프리셋 시각화 상태
  bool _showPresetVisualization = false;
  String? _currentPresetType;
  Map<String, dynamic> _presetVisualizationData = {};

  // Getters
  Map<String, int> get presetCounters => _presetCounters;
  Map<String, int> get presetSettings => _presetSettings;
  String? get loadingPresetType => _loadingPresetType;
  int get currentProgress => _currentProgress;
  bool get showLaserEffect => _showLaserEffect;
  String? get currentLaserPreset => _currentLaserPreset;
  int get laserIterations => _laserIterations;
  int get laserDurationMs => _laserDurationMs;
  bool get showPresetVisualization => _showPresetVisualization;
  String? get currentPresetType => _currentPresetType;
  Map<String, dynamic> get presetVisualizationData => _presetVisualizationData;

  /// 특정 프리셋이 로딩 중인지 확인
  bool isPresetLoading(String presetType) => _loadingPresetType == presetType;

  /// 프리셋 로딩 상태 설정
  void setPresetLoading(String? presetType, [int progress = 0]) {
    _loadingPresetType = presetType;
    _currentProgress = progress;
    notifyListeners();
  }

  /// 프리셋 설정 변경
  void updatePresetSetting(String presetType, int value) {
    _presetSettings[presetType] = value;
    notifyListeners();
  }

  /// 프리셋 카운터 증가
  void incrementPresetCounter(String presetType, int shots) {
    _presetCounters[presetType] = (_presetCounters[presetType] ?? 0) + shots;
    notifyListeners();
  }

  /// 레이저 효과 표시
  void activateLaserEffect(String presetType, int iterations) {
    _showLaserEffect = true;
    _currentLaserPreset = presetType;
    _laserIterations = iterations;
    
    // 이터레이션 수에 따른 지속 시간 계산
    _laserDurationMs = (iterations * AnimationConstants.laserIterationDuration)
        .clamp(AnimationConstants.minLaserDuration, AnimationConstants.maxLaserDuration);
    
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

  /// 프리셋 카운터 초기화
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

  /// 프리셋 시각화 활성화
  void showPresetVisualizationFor(String presetType) {
    _currentPresetType = presetType;
    _presetVisualizationData = {}; // 실제 데이터는 랜드마크가 필요하므로 외부에서 설정
    notifyListeners();
    
    // 5초 후 자동으로 숨김
    Future.delayed(const Duration(seconds: 5), () {
      hidePresetVisualization();
    });
  }

  /// 프리셋 시각화 숨김
  void hidePresetVisualization() {
    _showPresetVisualization = false;
    _currentPresetType = null;
    _presetVisualizationData.clear();
    notifyListeners();
  }

  /// 프리셋 시각화 데이터 설정
  void setPresetVisualizationData(Map<String, dynamic> data) {
    _presetVisualizationData = data;
    _showPresetVisualization = true;
    notifyListeners();
  }

  /// 프리셋 상태 초기화
  void reset() {
    resetPresetCounters();
    _loadingPresetType = null;
    _currentProgress = 0;
    _showLaserEffect = false;
    _currentLaserPreset = null;
    _laserIterations = 1;
    _laserDurationMs = AnimationConstants.minLaserDuration;
    hidePresetVisualization();
    notifyListeners();
  }
}