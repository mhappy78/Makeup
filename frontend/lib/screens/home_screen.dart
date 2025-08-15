import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:math' as math;
import '../models/app_state.dart';
import '../widgets/image_upload_widget.dart';
import '../widgets/image_display_widget.dart';
import '../widgets/warp_controls_widget.dart';
import '../widgets/landmark_controls_widget.dart';
import '../widgets/face_regions_widget.dart';

/// 메인 홈 스크린
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    
    // 탭 변경 감지
    _tabController.addListener(() {
      if (_tabController.indexIsChanging) return; // 탭 변경 중이면 무시
      
      final appState = context.read<AppState>();
      
      // 현재 탭 인덱스 업데이트
      appState.setCurrentTabIndex(_tabController.index);
      
      // 전문가 탭(index 2)으로 전환할 때 원본 이미지 복원
      if (_tabController.index == 2) {
        appState.restoreOriginalImage();
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Face Simulator',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          Consumer<AppState>(
            builder: (context, appState, child) {
              return IconButton(
                onPressed: appState.currentImage != null
                    ? () => _showResetDialog(context)
                    : null,
                icon: const Icon(Icons.refresh),
                tooltip: '초기화',
              );
            },
          ),
        ],
      ),
      body: Consumer<AppState>(
        builder: (context, appState, child) {
          return Stack(
            children: [
              // 메인 컨텐츠
              if (appState.isLoading)
                const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('처리 중...'),
                    ],
                  ),
                )
              else if (appState.errorMessage != null)
                Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.error_outline,
                        size: 64,
                        color: Theme.of(context).colorScheme.error,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        appState.errorMessage!,
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.error,
                          fontSize: 16,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: appState.clearError,
                        child: const Text('다시 시도'),
                      ),
                    ],
                  ),
                )
              else if (appState.currentImage == null)
                const ImageUploadWidget()
              else
                _buildMainLayout(context, appState),
              
            ],
          );

        },
      ),
    );
  }

  Widget _buildMainLayout(BuildContext context, AppState appState) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isMobile = constraints.maxWidth < 768;
        
        if (isMobile) {
          // 모바일 레이아웃: 전체 스크롤 가능
          return SingleChildScrollView(
            child: Column(
              children: [
                // 이미지 표시 영역 (모바일 최적화)
                Container(
                  height: math.max(600, math.min(constraints.maxWidth * 1.2, constraints.maxHeight * 0.6)),
                  margin: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: Theme.of(context).colorScheme.outline,
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const ClipRRect(
                    borderRadius: BorderRadius.all(Radius.circular(12)),
                    child: ImageDisplayWidget(),
                  ),
                ),
                
                // 컨트롤 패널 (탭 형태)
                SizedBox(
                  height: constraints.maxHeight * 1.05, // 50% 더 늘려서 스크롤 공간 확보
                  child: Column(
                    children: [
                      Container(
                        height: 42, // 탭 높이 정의
                        child: TabBar(
                          controller: _tabController,
                          tabs: const [
                            Tab(icon: Icon(Icons.analytics, size: 18), text: '분석'),
                            Tab(icon: Icon(Icons.edit, size: 18), text: '수정'),
                            Tab(icon: Icon(Icons.psychology, size: 18), text: '전문가'),
                          ],
                          indicatorColor: Theme.of(context).colorScheme.primary,
                          labelColor: Theme.of(context).colorScheme.primary,
                          labelStyle: const TextStyle(fontSize: 12),
                          unselectedLabelStyle: const TextStyle(fontSize: 12),
                        ),
                      ),
                      Expanded(
                        child: TabBarView(
                          controller: _tabController,
                          children: const [
                            FaceRegionsWidget(),
                            LandmarkControlsWidget(),
                            WarpControlsWidget(),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        } else {
          // 데스크톱 레이아웃: 가로 분할
          return Row(
            children: [
              // 이미지 표시 영역
              Expanded(
                flex: 3,
                child: Container(
                  margin: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: Theme.of(context).colorScheme.outline,
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const ClipRRect(
                    borderRadius: BorderRadius.all(Radius.circular(12)),
                    child: ImageDisplayWidget(),
                  ),
                ),
              ),
              
              // 컨트롤 패널
              SizedBox(
                width: 350,
                child: Container(
                  margin: const EdgeInsets.only(top: 16, right: 16, bottom: 16),
                  child: Column(
                    children: [
                      Container(
                        height: 42, // 탭 높이 정의
                        child: TabBar(
                          controller: _tabController,
                          tabs: const [
                            Tab(icon: Icon(Icons.analytics, size: 18), text: '분석'),
                            Tab(icon: Icon(Icons.edit, size: 18), text: '수정'),
                            Tab(icon: Icon(Icons.psychology, size: 18), text: '전문가'),
                          ],
                          indicatorColor: Theme.of(context).colorScheme.primary,
                          labelColor: Theme.of(context).colorScheme.primary,
                          labelStyle: const TextStyle(fontSize: 12),
                          unselectedLabelStyle: const TextStyle(fontSize: 12),
                        ),
                      ),
                      Expanded(
                        child: TabBarView(
                          controller: _tabController,
                          children: const [
                            FaceRegionsWidget(),
                            LandmarkControlsWidget(),
                            WarpControlsWidget(),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        }
      },
    );
  }

  void _showResetDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('초기화'),
          content: const Text('모든 변경사항이 사라집니다. 계속하시겠습니까?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('취소'),
            ),
            FilledButton(
              onPressed: () {
                context.read<AppState>().reset();
                Navigator.of(context).pop();
              },
              child: const Text('초기화'),
            ),
          ],
        );
      },
    );
  }
}