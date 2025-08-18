import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'dart:typed_data';
import '../models/image_models.dart';

/// 이미지 관련 상태 관리
class ImageState extends ChangeNotifier {
  // 이미지 데이터
  Uint8List? _currentImage;
  Uint8List? _originalImage;
  String? _currentImageId;
  String? _originalImageId;
  int _imageWidth = 0;
  int _imageHeight = 0;
  
  // 히스토리 관리
  final List<ImageHistoryItem> _imageHistory = [];
  static const int _maxHistorySize = 20;
  
  // 줌 및 팬 상태
  double _zoomScale = 1.0;
  Offset _panOffset = Offset.zero;
  bool _showOriginalImage = false;

  // Getters
  Uint8List? get currentImage => _currentImage;
  Uint8List? get originalImage => _originalImage;
  String? get currentImageId => _currentImageId;
  String? get originalImageId => _originalImageId;
  int get imageWidth => _imageWidth;
  int get imageHeight => _imageHeight;
  bool get canUndo => _imageHistory.isNotEmpty;
  double get zoomScale => _zoomScale;
  Offset get panOffset => _panOffset;
  bool get showOriginalImage => _showOriginalImage;
  
  /// 표시할 이미지 (Before/After 비교용)
  Uint8List? get displayImage => _showOriginalImage ? _originalImage : _currentImage;
  
  /// 새 이미지 설정 (업로드 시)
  void setImage(Uint8List imageData, String imageId, int width, int height) {
    _currentImage = imageData;
    _originalImage = Uint8List.fromList(imageData);
    _currentImageId = imageId;
    _originalImageId = imageId;
    _imageWidth = width;
    _imageHeight = height;
    _imageHistory.clear();
    _resetZoomAndPan();
    notifyListeners();
  }
  
  /// 현재 이미지만 업데이트 (워핑 후)
  void updateCurrentImage(Uint8List imageData, [String? newImageId]) {
    _addToHistory();
    _currentImage = imageData;
    if (newImageId != null) {
      _currentImageId = newImageId;
    }
    notifyListeners();
  }
  
  /// 카메라에서 촬영한 이미지 임시 설정
  void setCurrentImage(Uint8List imageData) {
    _currentImage = imageData;
    notifyListeners();
  }
  
  /// 히스토리에 현재 이미지 추가
  void _addToHistory() {
    if (_currentImage != null && _currentImageId != null) {
      _imageHistory.add(ImageHistoryItem(
        imageData: Uint8List.fromList(_currentImage!),
        imageId: _currentImageId!,
      ));
      
      if (_imageHistory.length > _maxHistorySize) {
        _imageHistory.removeAt(0);
      }
    }
  }
  
  /// 이전 상태로 되돌리기
  void undo() {
    if (_imageHistory.isNotEmpty) {
      final historyItem = _imageHistory.removeLast();
      _currentImage = Uint8List.fromList(historyItem.imageData);
      _currentImageId = historyItem.imageId;
      notifyListeners();
    }
  }
  
  /// 현재 상태를 히스토리에 저장
  void saveToHistory() {
    if (_currentImage != null && _currentImageId != null) {
      final historyItem = ImageHistoryItem(
        imageData: Uint8List.fromList(_currentImage!),
        imageId: _currentImageId!,
      );
      
      _imageHistory.add(historyItem);
      
      // 최대 히스토리 크기 제한
      if (_imageHistory.length > _maxHistorySize) {
        _imageHistory.removeAt(0);
      }
      
      notifyListeners();
    }
  }
  
  /// 원본 이미지로 복원
  Future<void> restoreToOriginal() async {
    if (_originalImage != null) {
      saveToHistory();
      _currentImage = Uint8List.fromList(_originalImage!);
      notifyListeners();
    }
  }
  
  /// 줌 스케일 설정
  void setZoomScale(double scale) {
    _zoomScale = scale.clamp(0.5, 3.0);
    notifyListeners();
  }
  
  /// 팬 오프셋 설정
  void setPanOffset(Offset offset) {
    _panOffset = offset;
    notifyListeners();
  }
  
  /// 팬 오프셋 추가
  void addPanOffset(Offset delta) {
    final newOffset = _panOffset + delta;
    
    if (_zoomScale > 1.0) {
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
  
  /// 줌 리셋
  void resetZoom() {
    _resetZoomAndPan();
    notifyListeners();
  }
  
  /// Before/After 토글
  void toggleOriginalImage() {
    _showOriginalImage = !_showOriginalImage;
    notifyListeners();
  }
  
  /// Before/After 상태 설정
  void setShowOriginalImage(bool show) {
    _showOriginalImage = show;
    notifyListeners();
  }
  
  /// 줌과 팬 초기화
  void _resetZoomAndPan() {
    _zoomScale = 1.0;
    _panOffset = Offset.zero;
  }
  
  /// 상태 초기화
  void reset() {
    _currentImage = null;
    _originalImage = null;
    _currentImageId = null;
    _originalImageId = null;
    _imageWidth = 0;
    _imageHeight = 0;
    _imageHistory.clear();
    _resetZoomAndPan();
    _showOriginalImage = false;
    notifyListeners();
  }
}