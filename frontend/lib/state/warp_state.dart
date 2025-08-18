import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../models/image_models.dart';

/// 워핑 도구 상태 관리
class WarpState extends ChangeNotifier {
  WarpMode _warpMode = WarpMode.pull;
  double _influenceRadiusPercent = 20.0;
  double _warpStrength = 0.1;
  bool _isWarpLoading = false;

  // Getters
  WarpMode get warpMode => _warpMode;
  double get influenceRadiusPercent => _influenceRadiusPercent;
  double get warpStrength => _warpStrength;
  bool get isWarpLoading => _isWarpLoading;

  /// 워핑 모드 변경
  void setWarpMode(WarpMode mode) {
    _warpMode = mode;
    notifyListeners();
  }

  /// 영향 반경 변경 (퍼센트 기반)
  void setInfluenceRadiusPercent(double percent) {
    _influenceRadiusPercent = percent.clamp(0.1, 50.0);
    notifyListeners();
  }

  /// 워핑 강도 변경
  void setWarpStrength(double strength) {
    _warpStrength = strength.clamp(0.1, 2.0);
    notifyListeners();
  }

  /// 워핑 로딩 상태 설정
  void setWarpLoading(bool loading) {
    _isWarpLoading = loading;
    notifyListeners();
  }

  /// 퍼센트를 픽셀로 변환 (백엔드 전송용)
  double getInfluenceRadiusPixels(int imageWidth, int imageHeight) {
    if (imageWidth == 0 || imageHeight == 0) return 80.0;
    
    final baseSize = math.min(imageWidth, imageHeight);
    return baseSize * (_influenceRadiusPercent / 100.0);
  }

  /// 화면 표시용 영향반경 계산
  double getInfluenceRadiusForDisplay(Size containerSize, int imageWidth, int imageHeight) {
    if (containerSize.width == 0 || containerSize.height == 0 || imageWidth == 0 || imageHeight == 0) {
      return 50.0;
    }
    
    final scaleX = containerSize.width / imageWidth;
    final scaleY = containerSize.height / imageHeight;
    final scale = math.min(scaleX, scaleY);
    
    final baseSize = math.min(imageWidth, imageHeight);
    final pixelRadius = baseSize * (_influenceRadiusPercent / 100.0);
    
    return pixelRadius * scale;
  }
  
  /// 상태 초기화
  void reset() {
    _warpMode = WarpMode.pull;
    _influenceRadiusPercent = 20.0;
    _warpStrength = 0.1;
    _isWarpLoading = false;
    notifyListeners();
  }
}