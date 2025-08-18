import 'package:flutter/foundation.dart';
import '../config/animation_constants.dart';
import '../services/beauty_analysis_service.dart';
import '../services/api_service.dart';
import '../models/image_models.dart';

/// 뷰티 분석 상태 관리
class BeautyAnalysisState extends ChangeNotifier {
  // 뷰티 스코어 관련 상태
  bool _showBeautyScore = false;
  double _beautyScoreAnimationProgress = 0.0;
  Map<String, dynamic> _beautyAnalysis = {};
  bool _beautyAnalysisCompleted = false;
  
  // 재진단 관련 상태
  Map<String, dynamic>? _originalBeautyAnalysis;
  bool _isReAnalyzing = false;
  bool _isGptAnalyzing = false;

  // Getters
  bool get showBeautyScore => _showBeautyScore;
  double get beautyScoreAnimationProgress => _beautyScoreAnimationProgress;
  Map<String, dynamic> get beautyAnalysis => _beautyAnalysis;
  bool get beautyAnalysisCompleted => _beautyAnalysisCompleted;
  Map<String, dynamic>? get originalBeautyAnalysis => _originalBeautyAnalysis;
  bool get isReAnalyzing => _isReAnalyzing;
  bool get isGptAnalyzing => _isGptAnalyzing;

  /// 뷰티 분석 계산 및 설정
  void calculateBeautyAnalysis(List<Landmark> landmarks, {bool isReAnalysis = false}) {
    if (landmarks.isEmpty) return;
    
    // 워핑 중이거나 재진단 중이 아닌 경우 뷰티 분석 건너뜀
    if (_originalBeautyAnalysis != null && !_isReAnalyzing) {
      return;
    }

    _beautyAnalysis = BeautyAnalysisService.calculateBeautyAnalysis(landmarks);
    
    // 최초 분석일 경우 원본으로 저장
    if (_originalBeautyAnalysis == null) {
      _originalBeautyAnalysis = Map<String, dynamic>.from(_beautyAnalysis);
    }
    
    // 완료 상태 설정
    _beautyAnalysisCompleted = true;
    notifyListeners();
    
    // GPT 분석 시작
    if (!isReAnalysis) {
      _performInitialGptAnalysis();
    } else {
      _performGptAnalysis();
    }
  }

  /// 재진단 시작
  Future<void> startReAnalysis(String? imageId) async {
    if (imageId == null) return;
    
    _isReAnalyzing = true;
    _beautyAnalysisCompleted = false;
    notifyListeners();
  }

  /// 재진단 완료
  void completeReAnalysis() {
    _isReAnalyzing = false;
    _showBeautyScore = true;
    _beautyScoreAnimationProgress = 1.0;
    _beautyAnalysisCompleted = true;
    notifyListeners();
  }

  /// 기초 뷰티스코어에 대한 GPT 분석 수행
  Future<void> _performInitialGptAnalysis() async {
    if (_beautyAnalysis.isEmpty || _isGptAnalyzing) return;
    
    try {
      _isGptAnalyzing = true;
      notifyListeners();
      
      final apiService = ApiService();
      final analysisResult = await apiService.analyzeInitialBeautyScore(_beautyAnalysis);
      
      if (_isGptAnalyzing) {
        _beautyAnalysis['gptAnalysis'] = {
          'analysisText': analysisResult.analysisText,
          'recommendations': analysisResult.recommendations,
          'isInitialAnalysis': true,
        };
        notifyListeners();
      }
    } catch (e) {
      // GPT 분석 실패해도 기본 분석은 유지
    } finally {
      _isGptAnalyzing = false;
      notifyListeners();
    }
  }

  /// 재진단 GPT 분석
  Future<void> _performGptAnalysis() async {
    if (_originalBeautyAnalysis == null || _beautyAnalysis.isEmpty) return;
    
    try {
      _isGptAnalyzing = true;
      notifyListeners();
      
      final apiService = ApiService();
      final comparisonResult = await apiService.analyzeBeautyComparison(
        _originalBeautyAnalysis!,
        _beautyAnalysis,
      );
      
      if (_isGptAnalyzing) {
        _beautyAnalysis['gptAnalysis'] = {
          'analysisText': comparisonResult.analysisText,
          'recommendations': comparisonResult.recommendations,
          'overallChange': comparisonResult.overallChange,
          'scoreChanges': comparisonResult.scoreChanges,
          'isComparison': true,
        };
        notifyListeners();
      }
    } catch (e) {
      // GPT 분석 실패해도 기본 분석은 유지
    } finally {
      _isGptAnalyzing = false;
      notifyListeners();
    }
  }

  /// 뷰티 분석 완료 (애니메이션 완료 후 호출)
  void completeBeautyAnalysis(List<Landmark> landmarks) {
    if (landmarks.isEmpty) return;
    
    calculateBeautyAnalysis(landmarks);
    _beautyAnalysisCompleted = true;
    _showBeautyScore = true;
    _beautyScoreAnimationProgress = 1.0;
    notifyListeners();
  }

  /// 뷰티 스코어 표시 설정
  void setShowBeautyScore(bool show) {
    _showBeautyScore = show;
    notifyListeners();
  }

  /// 뷰티 스코어 애니메이션 진행률 설정
  void setBeautyScoreAnimationProgress(double progress) {
    _beautyScoreAnimationProgress = progress.clamp(0.0, 1.0);
    notifyListeners();
  }

  /// 탭 변경 처리
  void handleTabChange(int tabIndex) {
    // 현재는 특별한 처리가 필요 없음
  }

  /// 새 이미지 업로드 시 초기화
  void resetForNewImage() {
    _beautyAnalysis.clear();
    _originalBeautyAnalysis = null;
    _showBeautyScore = false;
    _beautyScoreAnimationProgress = 0.0;
    _beautyAnalysisCompleted = false;
    _isReAnalyzing = false;
    _isGptAnalyzing = false;
    notifyListeners();
  }

  /// 전체 상태 초기화
  void reset() {
    resetForNewImage();
  }
}