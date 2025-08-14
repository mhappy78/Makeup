import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/app_state.dart';
import '../widgets/image_upload_widget.dart';
import '../widgets/image_display_widget.dart';
import '../widgets/warp_controls_widget.dart';
import '../widgets/landmark_controls_widget.dart';
import '../widgets/face_regions_widget.dart';

/// 메인 홈 스크린
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

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
          // 모바일 레이아웃: 세로 스크롤
          return Column(
            children: [
              // 이미지 표시 영역
              Container(
                height: constraints.maxHeight * 0.5,
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
              
              // 컨트롤 패널 (탭 형태)
              Expanded(
                child: DefaultTabController(
                  length: 3,
                  child: Column(
                    children: [
                      TabBar(
                        tabs: const [
                          Tab(icon: Icon(Icons.face), text: '부위'),
                          Tab(icon: Icon(Icons.visibility), text: '랜드마크'),
                          Tab(icon: Icon(Icons.transform), text: '변형'),
                        ],
                        indicatorColor: Theme.of(context).colorScheme.primary,
                        labelColor: Theme.of(context).colorScheme.primary,
                      ),
                      Expanded(
                        child: TabBarView(
                          children: [
                            const FaceRegionsWidget(),
                            const LandmarkControlsWidget(),
                            const WarpControlsWidget(),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
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
                  child: DefaultTabController(
                    length: 3,
                    child: Column(
                      children: [
                        TabBar(
                          tabs: const [
                            Tab(icon: Icon(Icons.face), text: '부위'),
                            Tab(icon: Icon(Icons.visibility), text: '랜드마크'),
                            Tab(icon: Icon(Icons.transform), text: '변형'),
                          ],
                          indicatorColor: Theme.of(context).colorScheme.primary,
                          labelColor: Theme.of(context).colorScheme.primary,
                        ),
                        const Expanded(
                          child: TabBarView(
                            children: [
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