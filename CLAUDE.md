# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BeautyGen is a comprehensive facial analysis and beauty scoring application with AI-powered transformations.

**Backend** (`backend/`): FastAPI-based image processing server with MediaPipe face detection and transformation algorithms
**Frontend** (`frontend/`): Flutter web application providing professional beauty analysis dashboard and real-time facial transformations

## Build and Development Commands

### Flutter Web Application

```bash
# Navigate to frontend directory
cd frontend

# Install Flutter dependencies
flutter pub get

# Run Flutter web application on Chrome
flutter run -d chrome --web-port=3000

# Build for production
flutter build web
```

### Backend API Server

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run FastAPI development server
python main.py

# Run with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Docker deployment
docker build -t beautygen-backend .
docker run -p 8000:8000 beautygen-backend
```

## Architecture

### Frontend Structure (`frontend/`)

**Core Application Files:**
- `lib/main.dart`: Application entry point and routing
- `lib/screens/home_screen.dart`: Main screen with tab navigation
- `lib/models/app_state.dart`: Global state management with Provider
- `lib/services/api_service.dart`: Backend API communication

**Widget Components:**
- `lib/widgets/beauty_score_dashboard.dart`: Professional beauty analysis dashboard
- `lib/widgets/beauty_score_visualizer.dart`: Real-time facial landmark visualization
- `lib/widgets/image_display_widget.dart`: Interactive image display with zoom/pan
- `lib/widgets/landmark_controls_widget.dart`: Preset transformation controls
- `lib/widgets/warp_controls_widget.dart`: Freestyle warping controls
- `lib/widgets/camera_capture_widget.dart`: Camera integration with face guidelines
- `lib/widgets/image_upload_widget.dart`: File upload interface
- `lib/widgets/before_after_comparison.dart`: Side-by-side comparison slider
- `lib/widgets/beauty_comparison_widget.dart`: AI analysis results display

**Utilities:**
- `lib/utils/image_processor.dart`: Client-side image processing and face-based cropping
- `lib/models/face_regions.dart`: Face region definitions for visualization

**Assets:**
- `assets/images/face_guide.png`: Camera guideline overlay
- `web/index.html`: Web application entry point

### Backend Structure (`backend/`)

**Core Files:**
- `main.py`: FastAPI application with all endpoints
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container deployment configuration
- `run.py`: Alternative startup script

**API Endpoints:**
- `POST /upload-image`: Image upload and storage
- `POST /get-face-landmarks`: MediaPipe face detection (468 landmarks)
- `POST /apply-warp`: Image warping transformations
- `POST /apply-preset`: Predefined transformation presets
- `POST /get-beauty-analysis`: Comprehensive beauty scoring
- `POST /analyze-beauty-gpt`: AI-powered analysis with recommendations

**Storage:**
- `temp_images/`: Temporary image storage for processing

## Core Technologies

**Frontend:**
- Flutter 3.10+ for cross-platform web application
- Provider for state management
- MediaPipe integration for facial landmark detection
- fl_chart 0.69.0 for professional chart visualization
- Custom Canvas painting for real-time visualization
- Camera package for webcam/mobile camera integration
- Image package for client-side processing

**Backend:**
- FastAPI for high-performance API server
- MediaPipe for 468-point facial landmark detection
- OpenCV for image processing and transformations
- PIL/Pillow for image manipulation
- NumPy for numerical operations
- Base64 encoding for image data transfer

## Face Detection and Processing

- Uses MediaPipe Face Mesh for real-time facial landmark detection (468 landmarks)
- Automatic face detection-based 3:4 aspect ratio cropping
- Advanced transformation algorithms with mathematical warping formulas
- Real-time visualization with coordinate mapping

## Image Warping Algorithm

The core transformation uses a mathematical formula for natural-looking deformations:

```
e = ((pow_r - dd) * (pow_r - dd)) / ((pow_r - dd + d_pull * d_pull) * (pow_r - dd + d_pull * d_pull))
```

Where:
- `pow_r`: squared influence radius
- `dd`: squared distance from touch point to pixel
- `d_pull`: drag distance

## Preset System

### Available Presets

1. **💉 아래턱 (Lower Jaw)**: Landmarks 150, 379 → 4 (nose bridge direction)
2. **💉 중간턱 (Middle Jaw)**: Landmarks 172, 397 → 4 (nose bridge direction)  
3. **💉 볼 (Cheek)**: Landmarks 215, 435 → 4 (nose bridge direction)
4. **💉 앞트임 (Front Protusion)**: Eye landmarks with elliptical transformation
5. **💉 뒷트임 (Back Slit)**: Outer eye corner extension

### Preset Features

**Frontend Implementation:**
- Compact mobile-optimized layout with sliders
- Shot count system: 100-500 shots for jaw/cheek, 1%-10% for eye treatments
- Real-time laser animation effects during application
- Cumulative counters and progress tracking
- Before/After comparison and save functionality

**Backend Processing:**
- FastAPI `/apply-preset` endpoint
- MediaPipe landmark-based coordinate transformation
- Preset-specific algorithms for each treatment type
- Base64 image encoding for efficient data transfer

## Beauty Score Analysis System

### Professional Dashboard Features

**Real-time Facial Analysis:**
- MediaPipe 468-landmark detection and processing
- Automatic face animation sequence (11 facial regions)
- Progressive beauty score calculation after animation completion

**Interactive Dashboard Components:**

1. **Radar Chart Visualization**
   - 4-axis radar chart showing beauty metrics
   - Custom Canvas painting with animation effects

2. **Interactive Category Cards**
   - 🏛️ **가로 황금비율 (Horizontal Golden Ratio)**: 20%/20%/20%/20%/20% 균등 분석
   - ⚖️ **세로 대칭성 (Vertical Symmetry)**: 50%(눈~코)/50%(코~턱) 균형 분석
   - ✨ **하관 조화 (Lower Face Harmony)**: 33%(인중)/67%(입~턱) 비율 분석
   - 🎯 **턱 곡률 (Jaw Curvature)**: 하악각(90-120°)과 턱목각(105-115°) 조화

3. **Professional Chart Analytics (fl_chart)**
   - Interactive bar charts with hover tooltips
   - 실제값 vs 이상값 comparison visualization
   - Section-specific analysis with deviation indicators

### Weighted Overall Score Calculation

```dart
final weightedScore = 
    (verticalScore * 0.25) +    // 가로 황금비율 25%
    (horizontalScore * 0.20) +  // 세로 대칭성 20%
    (lowerFaceScore * 0.15) +   // 하관 조화 15%
    (symmetry * 0.15) +         // 기본 대칭성 15%
    (eyeScore * 0.10) +         // 눈 10%
    (noseScore * 0.08) +        // 코 8%
    (lipScore * 0.05) +         // 입술 5%
    (jawScore * 0.02);          // 턱 곡률 2%
```

## Tab Navigation System

The application features a 3-tab interface:

- **📊 뷰티스코어 (BeautyScore)**: Comprehensive beauty analysis dashboard
- **⚡ 프리셋 (Preset)**: Quick preset transformations with laser visualization
- **🎨 프리스타일 (Freestyle)**: Advanced image warping and transformation tools

### Tab Features

**뷰티스코어 Tab:**
- Real-time facial landmark animation
- Professional beauty scoring with weighted algorithms
- AI-powered analysis with GPT recommendations
- Interactive charts and visualizations

**프리셋 Tab:**
- 5 predefined transformation types
- Shot count sliders and cumulative counters
- Real-time laser treatment visualization
- Before/After comparison and save functionality

**프리스타일 Tab:**
- 4 warp modes: Pull, Push, Expand, Shrink
- Percentage-based influence radius (0.5%-25%)
- Real-time hover preview with visual indicators
- Undo/Redo history management (up to 20 steps)
- Before/After comparison slider

## Camera Integration

**Camera Capture Features:**
- Cross-platform support (desktop webcam, mobile front camera)
- Real-time 3:4 aspect ratio preview with proper cropping
- Face guideline overlay using `face_guide.png` asset
- 3-second countdown with color-changing indicators
- Automatic face detection-based cropping with 60% padding

**Image Processing:**
- Client-side 3:4 aspect ratio enforcement
- Face detection-based intelligent cropping
- Seamless integration with beauty analysis workflow

## State Management Architecture

**AppState Class (Provider Pattern):**
```dart
class AppState extends ChangeNotifier {
  // Image management
  Uint8List? _currentImage;
  Uint8List? _originalImage;  // Original image backup
  
  // Tab navigation
  int _currentTabIndex = 0;
  
  // Beauty analysis
  Map<String, dynamic> _beautyAnalysis = {};
  bool _isAutoAnimationMode = false;
  
  // Preset management
  Map<String, int> _presetCounters = {};
  Map<String, int> _presetSettings = {};
  
  // Laser animation system
  bool _showLaserEffect = false;
  String? _currentLaserPreset;
  int _laserIterations = 1;
  
  // Warp modes and history
  WarpMode _warpMode = WarpMode.pull;
  List<ImageHistoryItem> _imageHistory = [];
}
```

## API Integration

**Frontend API Service:**
```dart
class ApiService {
  Future<UploadResponse> uploadImage(Uint8List imageBytes, String fileName);
  Future<LandmarkResponse> getFaceLandmarks(String imageId);
  Future<WarpResponse> applyWarp(String imageId, Map<String, dynamic> warpData);
  Future<PresetResponse> applyPreset(String imageId, String presetType);
  Future<BeautyAnalysisResponse> getBeautyAnalysis(String imageId);
  Future<GptAnalysisResponse> analyzeBeautyGpt(String imageId, Map<String, dynamic> scores);
}
```

**Backend FastAPI Endpoints:**
```python
@app.post("/upload-image")
@app.post("/get-face-landmarks") 
@app.post("/apply-warp")
@app.post("/apply-preset")
@app.post("/get-beauty-analysis")
@app.post("/analyze-beauty-gpt")
```

## Mobile-First Design

**Responsive Features:**
- Dynamic image sizing based on screen constraints
- Compact tab design with 42px height
- Touch-friendly interface elements
- Optimized margins and spacing for mobile devices
- SingleChildScrollView for full-screen scrollability

**Professional Chart Integration:**
- fl_chart library for interactive data visualization
- Hover tooltips with precise measurements
- Color-coded performance indicators
- Mobile-optimized touch interactions

## Development Notes

- Flutter web application provides professional-grade beauty analysis dashboard
- Real-time Canvas painting for interactive facial visualization
- Comprehensive state management with Provider pattern
- Mobile-first responsive design with optimized touch interactions
- Professional chart visualization using fl_chart library
- Advanced facial measurement analytics with real-time comparison
- Zero-flicker UI with smooth transitions
- Scalable architecture for easy feature extension

## Rules

- 코드 수정 시 자동으로 .claude 폴더에 필요한 사항을 저장하고 업데이트해라
- 코드 수정 시 자동으로 이 파일에 필요한 부분이 있으면 수정을 해라
- 필요하면 자동 compact를 실행해라.