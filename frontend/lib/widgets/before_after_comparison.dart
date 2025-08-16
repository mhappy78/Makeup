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

        return Column(
          children: [
            // 비교 제목 및 안내
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              color: Colors.black87,
              child: Column(
                children: [
                  Text(
                    _sliderValue < 0.5 
                        ? 'Before (원본) ${((1 - _sliderValue) * 100).toInt()}%'
                        : 'After (수정) ${(_sliderValue * 100).toInt()}%',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          (_isPanMode && _zoomScale > 1.0) 
                              ? '🖐️ 팬 모드: 이미지를 드래그하여 이동하세요'
                              : '💡 이미지를 클릭하거나 드래그하여 비교해보세요',
                          style: TextStyle(
                            color: (_isPanMode && _zoomScale > 1.0) ? Colors.yellow : Colors.white70,
                            fontSize: 12,
                          ),
                        ),
                      ),
                      // 줌 컨트롤 (항상 접근 가능하도록 고정)
                      Container(
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
                    ],
                  ),
                ],
              ),
            ),
            
            // 이미지 비교 영역
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  return GestureDetector(
                    // 이미지 영역 클릭 시에는 슬라이더 조작하지 않음 (핸들만 드래그 가능)
                    // onTapDown 제거하여 클릭 시 슬라이더 이동 방지
                    onDoubleTap: _resetZoom,
                    onLongPressStart: (details) {
                      // 줌이 1.0보다 클 때만 팬 모드 활성화
                      if (_zoomScale > 1.0) {
                        setState(() {
                          _isPanMode = true;
                          _lastPanUpdate = details.localPosition;
                        });
                      }
                    },
                    onLongPressEnd: (details) {
                      // 팬 모드 종료
                      setState(() {
                        _isPanMode = false;
                        _lastPanUpdate = null;
                      });
                    },
                    onLongPressMoveUpdate: (details) {
                      // 팬 모드에서 이미지 이동 (경계 제한 적용, 줌 > 1.0일 때만)
                      if (_isPanMode && _lastPanUpdate != null && _zoomScale > 1.0) {
                        final delta = details.localPosition - _lastPanUpdate!;
                        setState(() {
                          _panOffset += delta;
                          _constrainPanOffset();
                          _lastPanUpdate = details.localPosition;
                        });
                      }
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
                                    
                                    // Before 이미지 (클립으로 일부만 표시)
                                    Positioned.fill(
                                      child: ClipRect(
                                        clipper: _VerticalClipper(_sliderValue),
                                        child: Image.memory(
                                          appState.originalImage!,
                                          fit: BoxFit.contain,
                                          alignment: Alignment.center,
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
                        
                        // 드래그 핸들 (하단으로 이동)
                        Positioned(
                          left: constraints.maxWidth * _sliderValue - 16,
                          bottom: 80, // 하단에 위치 (슬라이더 컨트롤 영역 위)
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
                        
                        // Before 라벨 (경계선 왼쪽 상단으로 이동)
                        if (_sliderValue > 0.15) // 충분한 공간이 있을 때만 표시
                          Positioned(
                            left: constraints.maxWidth * _sliderValue - 80,
                            top: 20,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.7),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: Colors.white.withOpacity(0.5)),
                              ),
                              child: Text(
                                'Before',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  shadows: [
                                    Shadow(
                                      color: Colors.black.withOpacity(0.8),
                                      blurRadius: 2,
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        
                        // After 라벨 (경계선 오른쪽 상단으로 이동)
                        if (_sliderValue < 0.85) // 충분한 공간이 있을 때만 표시
                          Positioned(
                            left: constraints.maxWidth * _sliderValue + 20,
                            top: 20,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.7),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: Colors.white.withOpacity(0.5)),
                              ),
                              child: Text(
                                'After',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  shadows: [
                                    Shadow(
                                      color: Colors.black.withOpacity(0.8),
                                      blurRadius: 2,
                                    ),
                                  ],
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
                  
                  const SizedBox(height: 12),
                  
                  // 줌 사용법 안내
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.5),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '🔍 줌 & 팬 사용법',
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '• 더블탭: 줌 리셋\n• 길게 누르기: 팬 모드 활성화 (줌 > 100%일 때만)\n• 상단 버튼: 줌 인/아웃 조절 (100%-300%)\n• 줌아웃 시 자동 중앙정렬\n• 팬 모드: 이미지 경계 내에서만 이동 가능',
                          style: TextStyle(
                            fontSize: 12,
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
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