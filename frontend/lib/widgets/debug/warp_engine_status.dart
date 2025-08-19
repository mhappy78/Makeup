import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../../services/warp_service.dart';
import '../../models/app_state.dart';

/// JavaScript 워핑 엔진 상태 표시 위젯 (디버그 전용)
class WarpEngineStatusWidget extends StatefulWidget {
  const WarpEngineStatusWidget({super.key});

  @override
  State<WarpEngineStatusWidget> createState() => _WarpEngineStatusWidgetState();
}

class _WarpEngineStatusWidgetState extends State<WarpEngineStatusWidget> {
  bool _isLoaded = false;
  String _status = '확인 중...';
  
  @override
  void initState() {
    super.initState();
    _checkEngineStatus();
  }

  Future<void> _checkEngineStatus() async {
    if (!kDebugMode) return;
    
    setState(() {
      _status = '엔진 로드 확인 중...';
    });

    // 잠시 대기 후 확인
    await Future.delayed(const Duration(milliseconds: 100));
    
    final isLoaded = WarpService.isEngineLoaded;
    
    setState(() {
      _isLoaded = isLoaded;
      _status = isLoaded ? '✅ 로드됨' : '❌ 로드 실패';
    });

    if (!isLoaded) {
      // 추가 대기 후 재확인
      setState(() {
        _status = '⏳ 로드 대기 중...';
      });
      
      final loaded = await WarpService.waitForEngineLoad(timeoutSeconds: 5);
      
      setState(() {
        _isLoaded = loaded;
        _status = loaded ? '✅ 로드 완료' : '❌ 타임아웃';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!kDebugMode) {
      return const SizedBox.shrink();
    }

    return Container(
      margin: const EdgeInsets.all(8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _isLoaded ? Colors.green.withOpacity(0.8) : Colors.red.withOpacity(0.8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Icon(
                _isLoaded ? Icons.check_circle : Icons.error,
                color: Colors.white,
                size: 16,
              ),
              const SizedBox(width: 6),
              Text(
                'JavaScript 워핑 엔진',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            _status,
            style: TextStyle(
              color: Colors.white,
              fontSize: 10,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Flexible(
                child: ElevatedButton(
                  onPressed: _checkEngineStatus,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white.withOpacity(0.2),
                    padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                  ),
                  child: const Text(
                    '재확인',
                    style: TextStyle(color: Colors.white, fontSize: 10),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Flexible(
                child: ElevatedButton(
                  onPressed: _testEngine,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white.withOpacity(0.2),
                    padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                  ),
                  child: const Text(
                    '테스트',
                    style: TextStyle(color: Colors.white, fontSize: 10),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _testEngine() async {
    if (!WarpService.isEngineLoaded) {
      setState(() {
        _status = '❌ 엔진이 로드되지 않음';
      });
      return;
    }

    setState(() {
      _status = '🧪 테스트 실행 중...';
    });

    try {
      // 더미 이미지 데이터로 테스트
      final testImageData = Uint8List.fromList(List.filled(100 * 100 * 4, 128));
      
      final result = await WarpService.applyWarp(
        imageBytes: testImageData,
        width: 100,
        height: 100,
        startX: 50,
        startY: 50,
        endX: 60,
        endY: 60,
        influenceRadius: 20,
        strength: 0.5,
        mode: WarpMode.pull,
      );

      setState(() {
        _status = result != null ? '✅ 테스트 성공' : '❌ 테스트 실패';
      });
    } catch (e) {
      setState(() {
        _status = '❌ 테스트 에러: $e';
      });
    }
  }
}