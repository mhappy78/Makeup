import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/app_state.dart';

/// Before/After 비교 위젯 (슬라이더로 동시 비교)
class BeforeAfterComparison extends StatefulWidget {
  const BeforeAfterComparison({super.key});

  @override
  State<BeforeAfterComparison> createState() => _BeforeAfterComparisonState();
}

class _BeforeAfterComparisonState extends State<BeforeAfterComparison> {
  double _sliderValue = 0.5; // 0.0 = Before (원본), 1.0 = After (수정)
  
  // 줌과 팬 상태
  double _zoomScale = 1.0;
  Offset _panOffset = Offset.zero;
  
  // 제스처 제어 상태
  bool _isPanMode = false;
  Offset? _lastPanUpdate;
  
  // 회색조 상태
  bool _isGrayscale = true; // 디폴트로 Before 이미지를 회색으로 표시

  // 줌 리셋
  void _resetZoom() {
    setState(() {
      _zoomScale = 1.0;
      _panOffset = Offset.zero;
    });
  }

  // 줌 인
  void _zoomIn() {
    setState(() {
      _zoomScale = (_zoomScale * 1.2).clamp(1.0, 3.0);
      _constrainPanOffset();
    });
  }

  // 줌 아웃
  void _zoomOut() {
    setState(() {
      final newScale = (_zoomScale / 1.2).clamp(1.0, 3.0);
      _zoomScale = newScale;
      
      if (_zoomScale == 1.0) {
        _panOffset = Offset.zero;
      } else {
        _constrainPanOffset();
      }
    });
  }

  // 팬 오프셋을 화면 경계 내로 제한
  void _constrainPanOffset() {
    final maxOffset = 100.0 * _zoomScale;
    
    _panOffset = Offset(
      _panOffset.dx.clamp(-maxOffset, maxOffset),
      _panOffset.dy.clamp(-maxOffset, maxOffset),
    );
  }

  // 슬라이더 라벨 위젯
  Widget _buildSliderLabel(BuildContext context, String text, bool isActive) {
    return Text(
      text,
      style: TextStyle(
        fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
        color: isActive 
            ? Theme.of(context).colorScheme.primary
            : Theme.of(context).colorScheme.onSurface,
      ),
    );
  }

  // 빠른 선택 버튼
  Widget _buildQuickSelectButton({
    required VoidCallback onPressed,
    required IconData icon,
    required String label,
    required bool isSelected,
    required BuildContext context,
  }) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, size: 16),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: isSelected 
            ? Theme.of(context).colorScheme.primary
            : Theme.of(context).colorScheme.surface,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (appState.originalImage == null || appState.currentImage == null) {
          return const Center(
            child: Text('비교할 이미지가 없습니다.'),
          );
        }

        return Stack(
          children: [
            Column(
              children: [
                // 이미지 비교 영역
                Container(
                  height: MediaQuery.of(context).size.height * 0.75,
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      return Stack(
                        children: [
                          // After 이미지 (전체, 배경)
                          GestureDetector(
                            onDoubleTap: _resetZoom,
                            onPanStart: (details) {
                              if (_zoomScale > 1.0) {
                                setState(() {
                                  _isPanMode = true;
                                  _lastPanUpdate = details.localPosition;
                                });
                              }
                            },
                            onPanEnd: (details) {
                              setState(() {
                                _isPanMode = false;
                                _lastPanUpdate = null;
                              });
                            },
                            onPanUpdate: (details) {
                              if (_isPanMode && _lastPanUpdate != null && _zoomScale > 1.0) {
                                final delta = details.localPosition - _lastPanUpdate!;
                                setState(() {
                                  _panOffset += delta;
                                  _constrainPanOffset();
                                  _lastPanUpdate = details.localPosition;
                                });
                              }
                            },
                            child: ClipRect(
                              child: Transform.translate(
                                offset: _panOffset,
                                child: Transform.scale(
                                  scale: _zoomScale,
                                  child: Image.memory(
                                    appState.currentImage!,
                                    fit: BoxFit.contain,
                                    alignment: Alignment.center,
                                    width: constraints.maxWidth,
                                    height: constraints.maxHeight,
                                  ),
                                ),
                              ),
                            ),
                          ),
                          
                          // Before 이미지 (화면 좌표계 기준으로 클립)
                          ClipRect(
                            clipper: _ScreenClipper(constraints.maxWidth * _sliderValue),
                            child: GestureDetector(
                              onDoubleTap: _resetZoom,
                              onPanStart: (details) {
                                if (_zoomScale > 1.0) {
                                  setState(() {
                                    _isPanMode = true;
                                    _lastPanUpdate = details.localPosition;
                                  });
                                }
                              },
                              onPanEnd: (details) {
                                setState(() {
                                  _isPanMode = false;
                                  _lastPanUpdate = null;
                                });
                              },
                              onPanUpdate: (details) {
                                if (_isPanMode && _lastPanUpdate != null && _zoomScale > 1.0) {
                                  final delta = details.localPosition - _lastPanUpdate!;
                                  setState(() {
                                    _panOffset += delta;
                                    _constrainPanOffset();
                                    _lastPanUpdate = details.localPosition;
                                  });
                                }
                              },
                              child: Transform.translate(
                                offset: _panOffset,
                                child: Transform.scale(
                                  scale: _zoomScale,
                                  child: ColorFiltered(
                                    colorFilter: _isGrayscale 
                                        ? const ColorFilter.matrix([
                                            0.2126, 0.7152, 0.0722, 0, 0,
                                            0.2126, 0.7152, 0.0722, 0, 0,
                                            0.2126, 0.7152, 0.0722, 0, 0,
                                            0, 0, 0, 1, 0,
                                          ])
                                        : const ColorFilter.matrix([
                                            1, 0, 0, 0, 0,
                                            0, 1, 0, 0, 0,
                                            0, 0, 1, 0, 0,
                                            0, 0, 0, 1, 0,
                                          ]),
                                    child: Image.memory(
                                      appState.originalImage!,
                                      fit: BoxFit.contain,
                                      alignment: Alignment.center,
                                      width: constraints.maxWidth,
                                      height: constraints.maxHeight,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                          
                          // 구분선 (화면 좌표계, 항상 슬라이더 위치)
                          Positioned(
                            left: constraints.maxWidth * _sliderValue - 1,
                            top: 0,
                            bottom: 0,
                            width: 2,
                            child: Container(
                              color: Colors.white,
                              child: Container(
                                margin: const EdgeInsets.symmetric(vertical: 10),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.3),
                                      blurRadius: 2,
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                          
                          // 드래그 핸들
                          Positioned(
                            left: constraints.maxWidth * _sliderValue - 16,
                            bottom: 20,
                            child: GestureDetector(
                              onPanUpdate: (details) {
                                final globalPosition = details.globalPosition;
                                final localPosition = (context.findRenderObject() as RenderBox)
                                    .globalToLocal(globalPosition);
                                final newValue = (localPosition.dx / constraints.maxWidth).clamp(0.0, 1.0);
                                setState(() {
                                  _sliderValue = newValue;
                                });
                              },
                              child: Container(
                                width: 32,
                                height: 48,
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(color: Colors.blue, width: 2),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.3),
                                      blurRadius: 4,
                                      offset: const Offset(0, 2),
                                    ),
                                  ],
                                ),
                                child: const Icon(
                                  Icons.drag_handle,
                                  color: Colors.blue,
                                  size: 20,
                                ),
                              ),
                            ),
                          ),
                          
                          // Before/After 라벨
                          Positioned(
                            left: constraints.maxWidth * _sliderValue - 70,
                            bottom: 30,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: _isGrayscale ? Colors.grey.withOpacity(0.8) : Colors.black.withOpacity(0.7),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text(
                                'Before',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                          
                          Positioned(
                            left: constraints.maxWidth * _sliderValue + 34,
                            bottom: 30,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.blue.withOpacity(0.8),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text(
                                'After',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                        ],
                      );
                    },
                  ),
                ),
                
                // 슬라이더 컨트롤
                Container(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      // 라벨
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _buildSliderLabel(context, 'Before (원본)', _sliderValue < 0.5),
                          _buildSliderLabel(context, 'After (수정)', _sliderValue >= 0.5),
                        ],
                      ),
                      
                      // 슬라이더
                      Slider(
                        value: _sliderValue,
                        min: 0.0,
                        max: 1.0,
                        divisions: 20,
                        onChanged: (value) {
                          setState(() {
                            _sliderValue = value;
                          });
                        },
                      ),
                      
                      // 빠른 선택 버튼들
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildQuickSelectButton(
                            onPressed: () => setState(() => _sliderValue = 0.0),
                            icon: Icons.photo,
                            label: '원본',
                            isSelected: _sliderValue == 0.0,
                            context: context,
                          ),
                          _buildQuickSelectButton(
                            onPressed: () => setState(() => _sliderValue = 0.5),
                            icon: Icons.compare,
                            label: '50/50',
                            isSelected: false,
                            context: context,
                          ),
                          _buildQuickSelectButton(
                            onPressed: () => setState(() => _sliderValue = 1.0),
                            icon: Icons.auto_fix_high,
                            label: '수정',
                            isSelected: _sliderValue == 1.0,
                            context: context,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            
            // X 닫기 버튼 (우측 상단)
            Positioned(
              top: 20,
              right: 16,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.7),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close, color: Colors.white, size: 24),
                  constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                  padding: EdgeInsets.zero,
                ),
              ),
            ),
            
            // 줌 컨트롤 (왼쪽 상단)
            Positioned(
              top: 20,
              left: 16,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.7),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '${(_zoomScale * 100).toInt()}%',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      onPressed: _zoomOut,
                      icon: const Icon(Icons.zoom_out, color: Colors.white, size: 20),
                      constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                      padding: EdgeInsets.zero,
                    ),
                    IconButton(
                      onPressed: _resetZoom,
                      icon: const Icon(Icons.center_focus_strong, color: Colors.white, size: 20),
                      constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                      padding: EdgeInsets.zero,
                    ),
                    IconButton(
                      onPressed: _zoomIn,
                      icon: const Icon(Icons.zoom_in, color: Colors.white, size: 20),
                      constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                      padding: EdgeInsets.zero,
                    ),
                  ],
                ),
              ),
            ),
            
            // 회색조 토글 버튼 (이미지 좌측 하단)
            Positioned(
              top: MediaQuery.of(context).size.height * 0.75 - 80,
              left: 30,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.7),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: IconButton(
                  onPressed: () {
                    setState(() {
                      _isGrayscale = !_isGrayscale;
                    });
                  },
                  icon: Icon(
                    _isGrayscale ? Icons.filter_b_and_w : Icons.color_lens,
                    color: _isGrayscale ? Colors.grey : Colors.white,
                    size: 20,
                  ),
                  constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                  padding: EdgeInsets.zero,
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

/// 화면 좌표계 기준 클리퍼 (슬라이더 위치까지만 표시)
class _ScreenClipper extends CustomClipper<Rect> {
  final double screenSplitX;

  _ScreenClipper(this.screenSplitX);

  @override
  Rect getClip(Size size) {
    return Rect.fromLTRB(0, 0, screenSplitX, size.height);
  }

  @override
  bool shouldReclip(_ScreenClipper oldClipper) {
    return oldClipper.screenSplitX != screenSplitX;
  }
}