import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
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
        title: 'BeautyGen',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF6366F1), // 인디고 색상
            brightness: Brightness.light,
          ),
          useMaterial3: true,
          fontFamily: 'Malgun Gothic', // Windows 시스템 폰트 우선 사용
          textTheme: GoogleFonts.notoSansKrTextTheme().copyWith(
            // 시스템 폰트를 fallback으로 설정
          ),
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF6366F1),
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
          fontFamily: 'Malgun Gothic',
          textTheme: GoogleFonts.notoSansKrTextTheme(ThemeData.dark().textTheme).copyWith(
            // 시스템 폰트를 fallback으로 설정
          ),
        ),
        themeMode: ThemeMode.system,
        home: const HomeScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}