import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/app_state.dart';
import '../../services/warp_benchmark.dart';
import '../../services/warp_service.dart';

/// 워핑 성능 벤치마크 위젯 (디버그 전용)
class WarpBenchmarkWidget extends StatefulWidget {
  const WarpBenchmarkWidget({super.key});

  @override
  State<WarpBenchmarkWidget> createState() => _WarpBenchmarkWidgetState();
}

class _WarpBenchmarkWidgetState extends State<WarpBenchmarkWidget> {
  BenchmarkReport? _lastReport;
  QuickBenchmarkResult? _quickResult;
  bool _isRunning = false;
  String _currentStatus = '';

  @override
  Widget build(BuildContext context) {
    if (!kDebugMode) {
      return const SizedBox.shrink();
    }

    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (appState.currentImage == null) {
          return const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                '벤치마크를 실행하려면 이미지를 업로드하세요',
                style: TextStyle(color: Colors.grey),
              ),
            ),
          );
        }

        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 헤더
                Row(
                  children: [
                    const Icon(Icons.speed, size: 20),
                    const SizedBox(width: 8),
                    const Text(
                      '워핑 성능 벤치마크',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Spacer(),
                    if (_isRunning)
                      const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                  ],
                ),
                
                const SizedBox(height: 16),

                // 빠른 테스트 섹션
                _buildQuickTestSection(appState),
                
                const SizedBox(height: 16),

                // 전체 벤치마크 섹션
                _buildFullBenchmarkSection(appState),
                
                const SizedBox(height: 16),

                // 결과 표시
                if (_quickResult != null) ...[
                  _buildQuickResults(_quickResult!),
                  const SizedBox(height: 16),
                ],

                if (_lastReport != null) ...[
                  _buildDetailedResults(_lastReport!),
                ],

                // 현재 상태
                if (_currentStatus.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      _currentStatus,
                      style: const TextStyle(fontSize: 12),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildQuickTestSection(AppState appState) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '빠른 성능 체크',
          style: TextStyle(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: _isRunning ? null : () => _runQuickBenchmark(appState),
            icon: const Icon(Icons.flash_on, size: 16),
            label: const Text('빠른 테스트 (1회)'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFullBenchmarkSection(AppState appState) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '종합 성능 벤치마크',
          style: TextStyle(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _isRunning ? null : () => _runFullBenchmark(appState, 5),
                icon: const Icon(Icons.assessment, size: 16),
                label: const Text('표준 (5회)'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _isRunning ? null : () => _runFullBenchmark(appState, 10),
                icon: const Icon(Icons.precision_manufacturing, size: 16),
                label: const Text('정밀 (10회)'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildQuickResults(QuickBenchmarkResult result) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '빠른 테스트 결과',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          _buildResultRow('엔진 상태', result.engineLoaded ? '✅ 로드됨' : '❌ 실패'),
          _buildResultRow('이미지 추출', '${result.imageExtractionTime}ms'),
          _buildResultRow('워핑 처리', '${result.singleWarpTime.toStringAsFixed(1)}ms'),
          _buildResultRow('성공 여부', result.warpSuccess ? '✅ 성공' : '❌ 실패'),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: _getRecommendationColor(result.recommendation).withOpacity(0.2),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              result.recommendation,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: _getRecommendationColor(result.recommendation),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailedResults(BenchmarkReport report) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                '종합 벤치마크 결과',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getScoreColor(report.overallScore),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${report.overallScore.toStringAsFixed(1)}/100',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 12),

          // 기본 정보
          _buildResultRow('전체 소요시간', '${report.totalTime}ms'),
          _buildResultRow('엔진 로드', '${report.engineLoadTime}ms'),
          _buildResultRow('이미지 추출', '${report.imageExtractionTime}ms'),
          
          if (report.memoryUsage != null) ...[
            _buildResultRow('메모리 사용량', '${report.memoryUsage!.totalEstimatedMB}MB'),
          ],

          const SizedBox(height: 12),

          // 워핑 모드별 결과
          if (report.warpModeResults.isNotEmpty) ...[
            const Text(
              '워핑 모드별 성능',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
            ),
            const SizedBox(height: 8),
            ...report.warpModeResults.entries.map((entry) {
              final result = entry.value;
              return _buildResultRow(
                entry.key.displayName,
                '${result.averageTime.toStringAsFixed(1)}ms (${(result.successRate * 100).toStringAsFixed(0)}%)',
              );
            }),
          ],

          const SizedBox(height: 12),

          // 프리셋 결과
          if (report.presetResults.isNotEmpty) ...[
            const Text(
              '프리셋별 성능',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
            ),
            const SizedBox(height: 8),
            ...report.presetResults.entries.map((entry) {
              final result = entry.value;
              return _buildResultRow(
                _getPresetDisplayName(entry.key),
                '${result.averageTime.toStringAsFixed(1)}ms (${(result.successRate * 100).toStringAsFixed(0)}%)',
              );
            }),
          ],

          // 에러 목록
          if (report.errors.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text(
              '에러 목록',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: Colors.red),
            ),
            const SizedBox(height: 4),
            ...report.errors.map((error) => Text(
              '• $error',
              style: const TextStyle(fontSize: 12, color: Colors.red),
            )),
          ],

          const SizedBox(height: 12),

          // 결과 공유 버튼
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _shareResults(report),
              icon: const Icon(Icons.share, size: 16),
              label: const Text('결과 공유'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ),
          Text(
            value,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Future<void> _runQuickBenchmark(AppState appState) async {
    setState(() {
      _isRunning = true;
      _currentStatus = '빠른 벤치마크 실행 중...';
      _quickResult = null;
    });

    try {
      final result = await WarpBenchmark.runQuickBenchmark(
        imageBytes: appState.currentImage!,
      );

      setState(() {
        _quickResult = result;
        _currentStatus = '';
      });
    } catch (e) {
      setState(() {
        _currentStatus = '벤치마크 실패: $e';
      });
    } finally {
      setState(() {
        _isRunning = false;
      });
    }
  }

  Future<void> _runFullBenchmark(AppState appState, int iterations) async {
    setState(() {
      _isRunning = true;
      _currentStatus = '종합 벤치마크 실행 중... (${iterations}회 반복)';
      _lastReport = null;
    });

    try {
      final report = await WarpBenchmark.runComprehensiveBenchmark(
        imageBytes: appState.currentImage!,
        iterations: iterations,
      );

      setState(() {
        _lastReport = report;
        _currentStatus = '';
      });
    } catch (e) {
      setState(() {
        _currentStatus = '벤치마크 실패: $e';
      });
    } finally {
      setState(() {
        _isRunning = false;
      });
    }
  }

  void _shareResults(BenchmarkReport report) {
    // 결과를 JSON으로 변환하여 클립보드에 복사하거나 파일로 저장
    final json = report.toJson();
    debugPrint('벤치마크 결과: $json');
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('벤치마크 결과가 디버그 콘솔에 출력되었습니다'),
      ),
    );
  }

  Color _getRecommendationColor(String recommendation) {
    if (recommendation.contains('매우 빠름') || recommendation.contains('강력 권장')) {
      return Colors.green;
    } else if (recommendation.contains('양호') || recommendation.contains('권장')) {
      return Colors.blue;
    } else if (recommendation.contains('느림') || recommendation.contains('⚠')) {
      return Colors.orange;
    } else {
      return Colors.red;
    }
  }

  Color _getScoreColor(double score) {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.blue;
    if (score >= 40) return Colors.orange;
    return Colors.red;
  }

  String _getPresetDisplayName(String presetType) {
    switch (presetType) {
      case 'lower_jaw': return '아래턱';
      case 'middle_jaw': return '중간턱';
      case 'cheek': return '볼';
      case 'front_protusion': return '앞트임';
      case 'back_slit': return '뒷트임';
      default: return presetType;
    }
  }
}

/// 간단한 성능 모니터 위젯
class SimpleWarpMonitor extends StatelessWidget {
  final VoidCallback? onOpenFullBenchmark;

  const SimpleWarpMonitor({
    super.key,
    this.onOpenFullBenchmark,
  });

  @override
  Widget build(BuildContext context) {
    if (!kDebugMode) {
      return const SizedBox.shrink();
    }

    return Consumer<AppState>(
      builder: (context, appState, child) {
        return Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.8),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.speed,
                    color: Colors.white,
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '성능 모니터',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'JavaScript 엔진: ${WarpService.isEngineLoaded ? "Ready" : "Loading"}',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 10,
                ),
              ),
              if (onOpenFullBenchmark != null) ...[
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: onOpenFullBenchmark,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      padding: const EdgeInsets.symmetric(vertical: 4),
                    ),
                    child: const Text(
                      '벤치마크',
                      style: TextStyle(fontSize: 10),
                    ),
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}