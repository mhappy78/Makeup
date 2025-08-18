import 'package:flutter/foundation.dart';

/// UI 관련 상태 관리
class UiState extends ChangeNotifier {
  // UI 상태
  bool _isLoading = false;
  String? _errorMessage;
  int _currentTabIndex = 0;

  // Getters
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  int get currentTabIndex => _currentTabIndex;

  /// 로딩 상태 설정
  void setLoading(bool loading) {
    _isLoading = loading;
    if (loading) {
      _errorMessage = null;
    }
    notifyListeners();
  }

  /// 에러 설정
  void setError(String error) {
    _errorMessage = error;
    _isLoading = false;
    notifyListeners();
  }

  /// 에러 클리어
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  /// 현재 탭 인덱스 설정
  void setCurrentTabIndex(int index) {
    _currentTabIndex = index;
    notifyListeners();
  }

  /// UI 상태 초기화
  void reset() {
    _isLoading = false;
    _errorMessage = null;
    _currentTabIndex = 0;
    notifyListeners();
  }
}