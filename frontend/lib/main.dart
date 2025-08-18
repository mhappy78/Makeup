import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'config/app_constants.dart';
import 'config/app_theme.dart';
import 'screens/home_screen.dart';
import 'services/api_service.dart';
import 'models/app_state.dart';

void main() {
  runApp(const BeautyGenApp());
}

/// BeautyGen 메인 애플리케이션
class BeautyGenApp extends StatelessWidget {
  const BeautyGenApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AppState()),
        Provider<ApiService>(create: (_) => ApiService()),
      ],
      child: MaterialApp(
        title: AppConstants.appName,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        home: const HomeScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}