import 'package:flutter/material.dart';
import '../../config/app_constants.dart';
import '../face_regions_widget.dart';
import '../landmark_controls_widget.dart';
import '../warp_controls_widget.dart';

/// 앱 탭 시스템 관련 클래스들
class AppTabData {
  final IconData icon;
  final String label;
  final Widget widget;
  
  const AppTabData({
    required this.icon,
    required this.label, 
    required this.widget,
  });
}

/// 앱 탭 시스템
class AppTabSystem extends StatelessWidget {
  final TabController controller;
  
  const AppTabSystem({
    super.key,
    required this.controller,
  });
  
  static const double tabHeight = 42.0;
  
  static final List<AppTabData> tabs = [
    AppTabData(
      icon: Icons.analytics,
      label: '뷰티스코어',
      widget: const FaceRegionsWidget(),
    ),
    AppTabData(
      icon: Icons.edit,
      label: '프리셋',
      widget: const LandmarkControlsWidget(),
    ),
    AppTabData(
      icon: Icons.psychology,
      label: '프리스타일',
      widget: const WarpControlsWidget(),
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // 탭 헤더
        SizedBox(
          height: tabHeight,
          child: TabBar(
            controller: controller,
            tabs: tabs.map((tab) => Tab(
              icon: Icon(tab.icon, size: 18),
              text: tab.label,
            )).toList(),
            indicatorColor: Theme.of(context).colorScheme.primary,
            labelColor: Theme.of(context).colorScheme.primary,
            labelStyle: const TextStyle(fontSize: 12),
            unselectedLabelStyle: const TextStyle(fontSize: 12),
          ),
        ),
        // 탭 콘텐츠
        Expanded(
          child: TabBarView(
            controller: controller,
            children: tabs.map((tab) => tab.widget).toList(),
          ),
        ),
      ],
    );
  }
}