import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:math' as math;

import '../config/app_constants.dart';
import '../models/app_state.dart';
import '../widgets/image_upload_widget.dart';
import '../widgets/components/app_state_widgets.dart';
import '../widgets/components/app_tab_system.dart';
import '../widgets/components/image_container.dart';

/// BeautyGen 메인 홈 스크린
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
    _tabController = TabController(length: AppTabSystem.tabs.length, vsync: this);
    _tabController.addListener(_onTabChanged);
  }
  
  /// 탭 변경 이벤트 처리
  void _onTabChanged() {
    if (_tabController.indexIsChanging) return;
    
    final appState = context.read<AppState>();
    appState.setCurrentTabIndex(_tabController.index);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<AppState>(
        builder: (context, appState, child) {
          _syncTabController(appState);
          
          return Stack(
            children: [
              _buildMainContent(appState),
              if (appState.currentImage != null) _buildResetButton(),
            ],
          );
        },
      ),
    );
  }
  
  /// 탭 컨트롤러 동기화
  void _syncTabController(AppState appState) {
    if (_tabController.index != appState.currentTabIndex) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_tabController.index != appState.currentTabIndex) {
          _tabController.animateTo(appState.currentTabIndex);
        }
      });
    }
  }
  
  /// 메인 콘텐츠 빌드
  Widget _buildMainContent(AppState appState) {
    if (appState.isLoading) {
      return AppStateWidgets.buildLoadingWidget();
    }
    
    if (appState.errorMessage != null) {
      return AppStateWidgets.buildErrorWidget(
        context,
        appState.errorMessage!,
        appState.clearError,
      );
    }
    
    if (appState.currentImage == null) {
      return const ImageUploadWidget();
    }
    
    return _buildMainLayout();
  }
  
  /// 초기화 버튼 빌드
  Widget _buildResetButton() {
    return Positioned(
      top: MediaQuery.of(context).padding.top + AppConstants.floatingButtonTopOffset,
      right: 16,
      child: FloatingActionButton.small(
        onPressed: () => _showResetDialog(),
        tooltip: '초기화',
        backgroundColor: Theme.of(context).colorScheme.surface.withOpacity(0.9),
        foregroundColor: Theme.of(context).colorScheme.onSurface,
        child: const Icon(Icons.refresh),
      ),
    );
  }

  /// 메인 레이아웃 빌드
  Widget _buildMainLayout() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isMobile = constraints.maxWidth < AppConstants.mobileBreakpoint;
        
        return isMobile
            ? _buildMobileLayout(constraints)
            : _buildDesktopLayout();
      },
    );
  }
  
  /// 모바일 레이아웃
  Widget _buildMobileLayout(BoxConstraints constraints) {
    return SingleChildScrollView(
      child: Column(
        children: [
          // 이미지 영역
          ImageContainer(
            height: _calculateMobileImageHeight(constraints),
            margin: const EdgeInsets.fromLTRB(12, 4, 12, 4),
          ),
          // 탭 시스템
          SizedBox(
            height: constraints.maxHeight * 1.05,
            child: AppTabSystem(controller: _tabController),
          ),
        ],
      ),
    );
  }
  
  /// 데스크톱 레이아웃
  Widget _buildDesktopLayout() {
    return Row(
      children: [
        // 이미지 영역
        Expanded(
          flex: 3,
          child: ImageContainer(
            margin: const EdgeInsets.fromLTRB(16, 4, 16, 16),
          ),
        ),
        // 컨트롤 패널
        SizedBox(
          width: AppConstants.desktopControlPanelWidth,
          child: Container(
            margin: const EdgeInsets.only(top: 4, right: 16, bottom: 16),
            child: AppTabSystem(controller: _tabController),
          ),
        ),
      ],
    );
  }
  
  /// 모바일 이미지 높이 계산
  double _calculateMobileImageHeight(BoxConstraints constraints) {
    return math.max(
      AppConstants.minMobileImageHeight,
      math.min(
        constraints.maxWidth * 1.2,
        constraints.maxHeight * 0.6,
      ),
    );
  }

  /// 리셋 다이얼로그 표시
  void _showResetDialog() {
    AppStateWidgets.showResetDialog(
      context,
      () => context.read<AppState>().reset(),
    );
  }
  
}