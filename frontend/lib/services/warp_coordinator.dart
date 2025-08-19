import 'package:flutter/foundation.dart';
import '../widgets/components/smart_warp_widget.dart';
import '../widgets/components/image_display_widget.dart';

/// 스마트 워핑 위젯과 다른 컴포넌트 간의 조정자
class WarpCoordinator {
  static SmartWarpWidgetState? _smartWarpWidget;
  static dynamic _imageDisplayWidget; // ImageDisplayWidget state
  
  /// SmartWarpWidget 등록
  static void registerSmartWarpWidget(SmartWarpWidgetState widget) {
    _smartWarpWidget = widget;
  }
  
  /// SmartWarpWidget 등록 해제
  static void unregisterSmartWarpWidget() {
    _smartWarpWidget = null;
  }
  
  /// ImageDisplayWidget 등록
  static void registerImageDisplayWidget(dynamic widget) {
    _imageDisplayWidget = widget;
  }
  
  /// ImageDisplayWidget 등록 해제
  static void unregisterImageDisplayWidget() {
    _imageDisplayWidget = null;
  }
  
  /// 프리셋 적용
  static Future<bool> applyPreset(String presetType) async {
    if (_smartWarpWidget == null) {
      return false;
    }
    
    try {
      await _smartWarpWidget!.applySmartPreset(presetType);
      return true;
    } catch (e) {
      debugPrint('❌ 프리셋 적용 실패: $e');
      return false;
    }
  }
  
  /// SmartWarpWidget이 등록되어 있는지 확인
  static bool get isSmartWarpAvailable => _smartWarpWidget != null;
}