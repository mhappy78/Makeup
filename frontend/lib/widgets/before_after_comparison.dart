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
                  const Text(
                    '💡 이미지를 클릭하거나 드래그하여 비교해보세요',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
            
            // 이미지 비교 영역
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  return GestureDetector(
                    onTapDown: (details) {
                      final newValue = (details.localPosition.dx / constraints.maxWidth).clamp(0.0, 1.0);
                      setState(() {
                        _sliderValue = newValue;
                      });
                    },
                    onPanUpdate: (details) {
                      final newValue = (details.localPosition.dx / constraints.maxWidth).clamp(0.0, 1.0);
                      setState(() {
                        _sliderValue = newValue;
                      });
                    },
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
                        
                        // 드래그 핸들 (중앙)
                        Positioned(
                          left: constraints.maxWidth * _sliderValue - 16,
                          top: constraints.maxHeight * 0.5 - 24,
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