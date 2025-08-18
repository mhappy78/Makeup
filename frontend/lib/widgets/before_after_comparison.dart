import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';

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

  // 줌 인 (최대 3배까지만 허용하여 UI 접근성 보장)
  void _zoomIn() {
    setState(() {
      _zoomScale = (_zoomScale * 1.2).clamp(1.0, 3.0);
      _constrainPanOffset();
    });
  }

  // 줌 아웃 (원본 크기 이하로 축소 방지)
  void _zoomOut() {
    setState(() {
      final newScale = (_zoomScale / 1.2).clamp(1.0, 3.0);
      _zoomScale = newScale;
      
      // 원본 크기(1.0)로 돌아가면 중앙 정렬
      if (_zoomScale == 1.0) {
        _panOffset = Offset.zero;
      } else {
        _constrainPanOffset();
      }
    });
  }

  // 팬 오프셋을 화면 경계 내로 제한
  void _constrainPanOffset() {
    // 현재 위젯의 크기 기준으로 최대 이동 거리 계산
    final maxOffset = 100.0 * _zoomScale; // 줌 레벨에 따라 이동 허용 범위 조정
    
    _panOffset = Offset(
      _panOffset.dx.clamp(-maxOffset, maxOffset),
      _panOffset.dy.clamp(-maxOffset, maxOffset),
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
                // 이미지 비교 영역 (프리셋 탭과 동일한 크기)
                Container(
                  height: MediaQuery.of(context).size.height * 0.75, // 프리셋 탭과 동일한 비율
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      return GestureDetector(
                        onDoubleTap: _resetZoom,
                        onPanStart: (details) {
                          // 줌이 1.0보다 클 때만 팬 모드 활성화 (즉시 드래그 가능)
                          if (_zoomScale > 1.0) {
                            setState(() {
                              _isPanMode = true;
                              _lastPanUpdate = details.localPosition;
                            });
                          }
                        },
                        onPanEnd: (details) {
                          // 팬 모드 종료
                          setState(() {
                            _isPanMode = false;
                            _lastPanUpdate = null;
                          });
                        },
                        onPanUpdate: (details) {
                          if (_isPanMode && _lastPanUpdate != null && _zoomScale > 1.0) {
                            // 팬 모드에서는 이미지 이동 (경계 제한 적용, 줌 > 1.0일 때만)
                            final delta = details.localPosition - _lastPanUpdate!;
                            setState(() {
                              _panOffset += delta;
                              _constrainPanOffset();
                              _lastPanUpdate = details.localPosition;
                            });
                          }
                          // 이미지 영역 드래그로는 슬라이더 조작하지 않음 (핸들만 드래그 가능)
                        },
                        child: Stack(
                          children: [
                            // 줌과 팬이 적용된 이미지 컨테이너 (클립으로 경계 제한)
                            Positioned.fill(
                              child: ClipRect(
                                child: Transform.translate(
                                  offset: _panOffset,
                                  child: Transform.scale(
                                    scale: _zoomScale,
                                    child: Stack(
                                      children: [
                                        // After 이미지 (배경)
                                        Positioned.fill(
                                          child: Image.memory(
                                            appState.currentImage!,
                                            fit: BoxFit.contain,
                                            alignment: Alignment.center,
                                          ),
                                        ),
                                        
                                        // Before 이미지 (클립으로 일부만 표시, 회색조 옵션)
                                        Positioned.fill(
                                          child: ClipRect(
                                            clipper: _VerticalClipper(_sliderValue),
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
                                              ),
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            
                            // 구분선
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
                            
                            // 드래그 핸들 (더 아래로 이동)
                            Positioned(
                              left: constraints.maxWidth * _sliderValue - 16,
                              bottom: 20, // 더 아래로 이동
                              child: GestureDetector(
                                onPanStart: (details) {
                                  // 핸들 드래그 시작
                                  _lastPanUpdate = details.localPosition;
                                },
                                onPanUpdate: (details) {
                                  // 핸들만 드래그하여 슬라이더 조작
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
                            
                            // Before 라벨 (손잡이 왼쪽)
                            Positioned(
                              left: constraints.maxWidth * _sliderValue - 70,
                              bottom: 30,
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: _isGrayscale ? Colors.grey.withOpacity(0.8) : Colors.black.withOpacity(0.7),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  'Before',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 10,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                            
                            // After 라벨 (손잡이 오른쪽)
                            Positioned(
                              left: constraints.maxWidth * _sliderValue + 34,
                              bottom: 30,
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Colors.blue.withOpacity(0.8),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
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
                        ),
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
                          Text(
                            'Before (원본)',
                            style: TextStyle(
                              fontWeight: _sliderValue < 0.5 ? FontWeight.bold : FontWeight.normal,
                              color: _sliderValue < 0.5 
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).colorScheme.onSurface,
                            ),
                          ),
                          Text(
                            'After (수정)',
                            style: TextStyle(
                              fontWeight: _sliderValue >= 0.5 ? FontWeight.bold : FontWeight.normal,
                              color: _sliderValue >= 0.5 
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).colorScheme.onSurface,
                            ),
                          ),
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
                          ElevatedButton.icon(
                            onPressed: () {
                              setState(() {
                                _sliderValue = 0.0;
                              });
                            },
                            icon: const Icon(Icons.photo, size: 16),
                            label: const Text('원본'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _sliderValue == 0.0 
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).colorScheme.surface,
                            ),
                          ),
                          ElevatedButton.icon(
                            onPressed: () {
                              setState(() {
                                _sliderValue = 0.5;
                              });
                            },
                            icon: const Icon(Icons.compare, size: 16),
                            label: const Text('50/50'),
                          ),
                          ElevatedButton.icon(
                            onPressed: () {
                              setState(() {
                                _sliderValue = 1.0;
                              });
                            },
                            icon: const Icon(Icons.auto_fix_high, size: 16),
                            label: const Text('수정'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _sliderValue == 1.0 
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).colorScheme.surface,
                            ),
                          ),
                        ],
                      ),
                      
                      // 줌 사용법 안내 삭제
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
              top: MediaQuery.of(context).size.height * 0.75 - 80, // 이미지 영역 하단에서 80px 위
              left: 30, // 이미지 영역 내 좌측
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

/// 세로 클리핑을 위한 커스텀 클리퍼
class _VerticalClipper extends CustomClipper<Rect> {
  final double splitRatio;

  _VerticalClipper(this.splitRatio);

  @override
  Rect getClip(Size size) {
    return Rect.fromLTRB(0, 0, size.width * splitRatio, size.height);
  }

  @override
  bool shouldReclip(_VerticalClipper oldClipper) {
    return oldClipper.splitRatio != splitRatio;
  }
}