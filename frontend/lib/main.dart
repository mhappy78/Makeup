import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/app_config.dart';
import 'screens/home_screen.dart';
import 'services/api_service.dart';
import 'models/app_state.dart';

void main() {
  runApp(const FaceSimulatorApp());
}

class FaceSimulatorApp extends StatelessWidget {
  const FaceSimulatorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AppState()),
        Provider<ApiService>(create: (_) => ApiService()),
      ],
      child: MaterialApp(
        title: AppConfig.appName,
        theme: AppConfig.lightTheme,
        darkTheme: AppConfig.darkTheme,
        themeMode: ThemeMode.system,
        home: const HomeScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}