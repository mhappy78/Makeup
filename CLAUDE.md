# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive facial analysis and beauty scoring application providing:

**Python Applications** (`python_makeup_app/`): Desktop and web-based makeup tools with advanced image warping capabilities

**Flutter Web Application** (`frontend/`): Professional beauty analysis dashboard with AI-powered facial scoring system

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

### Python Applications

```bash
# Install dependencies
pip install -r requirements.txt

# For python_makeup_app specifically
cd python_makeup_app
pip install -r requirements.txt

# Run desktop makeup application
python python_makeup_app/makeup_app.py

# Run web-based makeup application
streamlit run python_makeup_app/streamlit_app.py

# Run integrated makeup and warping tool
python python_makeup_app/integrated_app.py

# Run simple image warping tool
python python_makeup_app/simple_warping.py
```

## Architecture

### Flutter Web App Structure (`frontend/`)

**Main Components:**

- `lib/main.dart`: Application entry point and routing
- `lib/models/app_state.dart`: Global state management with Provider
- `lib/widgets/beauty_score_dashboard.dart`: Professional beauty analysis dashboard
- `lib/widgets/beauty_score_visualizer.dart`: Real-time facial landmark visualization
- `lib/widgets/image_display_widget.dart`: Interactive image display with zoom/pan
- `lib/services/api_service.dart`: Backend API communication

**Core Technologies:**

- Flutter for cross-platform web application
- MediaPipe 468-point facial landmark detection
- Provider for state management
- fl_chart 0.69.0 for professional chart visualization
- Custom Canvas painting for real-time visualization
- Advanced UI animations and interactions

### Python App Structure (`python_makeup_app/`)

**Applications:**

- `makeup_app.py`: Desktop GUI using CustomTkinter
- `streamlit_app.py`: Web interface using Streamlit
- `integrated_app.py`: Combined makeup and warping tool
- `simple_warping.py`: Simplified image transformation tool

**Core Technologies:**

- OpenCV for image processing
- MediaPipe for face mesh detection
- PIL/Pillow for image manipulation
- NumPy for numerical operations

## Face Detection and Processing

- Uses MediaPipe Face Mesh for real-time facial landmark detection (468 landmarks)
- Supports advanced transformation algorithms with mathematical warping formulas

## Image Warping Algorithm

The core transformation uses a mathematical formula for natural-looking deformations:

```
e = ((pow_r - dd) * (pow_r - dd)) / ((pow_r - dd + d_pull * d_pull) * (pow_r - dd + d_pull * d_pull))
```

Where:

- `pow_r`: squared influence radius
- `dd`: squared distance from touch point to pixel
- `d_pull`: drag distance

## Assets and Resources

- Uses MediaPipe for dynamic face detection, no static assets required
- Sample images available in `samples/` and `doc/` directories for testing

## Native Dependencies

- Pure Python implementation, no native dependencies required

## Testing

- Comprehensive test suite with 30+ test files covering various functionality
- Applications include built-in validation and error handling

## Preset System

The application now includes a preset system for quick application of predefined transformations:

### Available Presets

**아래턱 100샷 (Lower Jaw 100-Shot)**
- **Purpose**: Jaw line contouring simulation
- **Target Landmarks**: 150 (left jaw), 379 (right jaw), 4 (nose bridge)
- **Parameters**:
  - Influence radius: 30%
  - Transformation strength: 0.2x
  - Pull distance: 10% of landmark-to-nose distance
- **Algorithm**: Pull landmarks 150 and 379 towards landmark 4 (nose bridge) direction
- **Visualization**: Real-time visual feedback showing start/end points, pull vectors, and influence radius
- **Implementation**: `apply_lower_jaw_100shot_preset()` in `face_simulator.py`

### Preset Implementation Architecture

```python
def apply_lower_jaw_100shot_preset(self):
    # 1. Get landmark coordinates
    landmark_150 = self.get_landmark_coordinates(150)
    landmark_379 = self.get_landmark_coordinates(379) 
    landmark_4 = self.get_landmark_coordinates(4)
    
    # 2. Calculate distances and pull vectors
    distance_150_to_4 = self.calculate_distance(landmark_150, landmark_4)
    pull_distance = distance_150_to_4 * 0.1  # 10% of distance
    
    # 3. Apply transformations with preset parameters
    self.apply_pull_warp_with_params(start, target, strength=0.2)
```

### Preset Visualization System

The preset system includes comprehensive visual feedback:

**Visual Elements:**
- 🔴 **Start Point**: Red circle marking the original landmark position
- 🔵 **End Point**: Blue circle showing the target position after transformation
- 🔶 **Pull Vector**: Orange arrow indicating direction and magnitude of transformation
- 🟡 **Influence Radius**: Dashed yellow circle showing the area affected by transformation
- 📊 **Info Label**: Real-time display of distance, strength, and radius parameters

**Visualization Features:**
- Automatic scaling with zoom level
- 5-second auto-hide timer
- Manual toggle with checkbox
- Clears on mouse movement for better interaction

**Implementation:**
```python
def draw_preset_visualization(self, start_point, end_point, influence_radius_px, strength, label):
    # Visual elements: start point (red), end point (blue), arrow, radius circle, info label
    # Auto-hide after 5 seconds: self.root.after(5000, self.clear_preset_visualization)
```

### Advanced Preset System (Flutter Web App)

**Latest Implementation Features (January 2025):**

**🎯 Compact Mobile Layout:**
- One-line preset design for mobile optimization
- Each preset item contains: title, total counter, slider, apply button
- Mobile-friendly touch interactions
- Space-efficient card design with proper spacing

**⚡ Dynamic Laser Animation System:**
- Real-time laser visualization during preset application
- Animation duration matches shot count (500 shots = animation for full duration)
- Iteration-based timing system: `_laserDurationMs = (iterations * 1000).clamp(1500, 15000)`
- Progress counter display showing current iteration (e.g., "💉 아래턱 레이저 시술 중... (234/500)")
- Visual laser effects with red/orange gradient patterns
- Treatment area identification with preset-specific effects

**📊 Shot Count System:**
- **Jaw Treatments** (아래턱, 중간턱, 볼): 100-500 shots in 100-shot increments
- **Eye Treatments** (앞트임, 뒷트임): 1%-10% in 1% increments
- Cumulative counters for each preset type
- Total shot accumulation display
- Total treatment percentage display for eye procedures

**🎮 Enhanced Control System:**
- **Undo**: Step-by-step reversal of transformations
- **Restore Original**: Complete reset to original image
- **Before/After**: Interactive slider comparison (borrowed from freestyle tab)
- **Save/Download**: Browser-based image download with HTML5 Blob API
- Individual preset loading states (no full-screen flickering)

**Implementation Details:**

```dart
// AppState.dart - Enhanced preset management
class AppState extends ChangeNotifier {
  // Preset state management
  Map<String, int> _presetCounters = {};
  Map<String, int> _presetSettings = {};
  String? _loadingPresetType;
  
  // Laser animation system
  bool _showLaserEffect = false;
  String? _currentLaserPreset;
  int _laserIterations = 1;
  int _laserDurationMs = 1500;
  
  // Dynamic laser activation
  void activateLaserEffect(String presetType, int iterations) {
    _showLaserEffect = true;
    _currentLaserPreset = presetType;
    _laserIterations = iterations;
    _laserDurationMs = (iterations * 1000).clamp(1500, 15000);
    notifyListeners();
    
    Future.delayed(Duration(milliseconds: _laserDurationMs), () {
      _showLaserEffect = false;
      _currentLaserPreset = null;
      _laserIterations = 1;
      _laserDurationMs = 1500;
      notifyListeners();
    });
  }
}
```

```dart
// LandmarkControlsWidget.dart - Compact preset layout
Widget _buildCompactPresetItem(BuildContext context, AppState appState, 
    String title, String presetType, String unit, int minValue, int maxValue, int stepValue) {
  return Container(
    padding: const EdgeInsets.all(12),
    child: Row(
      children: [
        // Title and counter (2/7 of width)
        Expanded(flex: 2, child: Column([
          Text(title, style: titleSmall.bold),
          Text('총 $currentCounter$unit', style: bodySmall.primary.bold),
        ])),
        
        // Slider with value display (3/7 of width)
        Expanded(flex: 3, child: Column([
          Slider(value: currentValue, min: minValue, max: maxValue, 
                 onChanged: (value) => appState.updatePresetSetting(presetType, value.round())),
          Text('$currentValue$unit'),
        ])),
        
        // Apply button (2/7 of width)
        SizedBox(width: 80, child: ElevatedButton(
          onPressed: () => _applyPresetWithSettings(context, presetType),
          child: Text('적용'),
        )),
      ],
    ),
  );
}
```

```dart
// ImageDisplayWidget.dart - Laser animation painter
class LaserEffectPainter extends CustomPainter {
  final String presetType;
  final int iterations;
  final int durationMs;
  
  @override
  void paint(Canvas canvas, Size size) {
    final totalProgress = ((currentTime / 50) % (durationMs / 50)) / (durationMs / 50);
    final currentIteration = (totalProgress * iterations).floor() + 1;
    
    // Draw laser effects with animated gradients
    final laserPaint = Paint()
      ..shader = RadialGradient(colors: [
        Colors.red.withOpacity(opacity),
        Colors.orange.withOpacity(opacity * 0.5),
        Colors.transparent,
      ]).createShader(Rect.fromCircle(center: center, radius: radius));
    
    // Progress text display
    final textPainter = TextPainter(
      text: TextSpan(text: '$treatmentArea 레이저 시술 중... ($currentIteration/$iterations)'),
      textDirection: TextDirection.ltr,
    );
  }
}
```

**🔧 Backend Integration:**
- FastAPI `/apply-preset` endpoint with 5 preset types
- MediaPipe landmark-based transformations
- Preset-specific algorithms for jaw, cheek, and eye treatments
- Base64 image encoding for smooth data transfer

**Preset Types Available:**
1. **💉 아래턱 (Lower Jaw)**: Landmarks 150, 379 → 4 (nose bridge direction)
2. **💉 중간턱 (Middle Jaw)**: Landmarks 172, 397 → 4 (nose bridge direction)  
3. **💉 볼 (Cheek)**: Landmarks 215, 435 → 4 (nose bridge direction)
4. **💉 앞트임 (Front Protusion)**: Eye landmarks with elliptical transformation
5. **💉 뒷트임 (Back Slit)**: Outer eye corner extension

### Preset Extension

New presets can be easily added by:
1. Creating new preset function following the naming pattern `apply_*_preset()`
2. Adding UI button in `setup_warp_controls()`
3. Using existing transformation functions with specific parameters
4. Adding visualization calls with `draw_preset_visualization()`
5. For Flutter: Adding preset configuration to `_buildCompactPresetItem()` calls
6. For Backend: Extending `PRESET_CONFIGS` dictionary in `apply_preset_transformation()`

## Beauty Score Analysis System

### Professional Dashboard Features

The Flutter web application features a comprehensive beauty analysis system with:

**🎯 Real-time Facial Analysis**
- MediaPipe 468-landmark detection and processing
- Automatic face animation sequence (11 facial regions)
- Progressive beauty score calculation after animation completion

**📊 Interactive Dashboard Components**

1. **Radar Chart Visualization**
   - 4-axis radar chart showing beauty metrics
   - Custom Canvas painting with animation effects
   - Real-time data visualization

2. **Interactive Category Cards**
   - 🏛️ **가로 황금비율 (Horizontal Golden Ratio)**: 20%/20%/20%/20%/20% 균등 분석
   - ⚖️ **세로 대칭성 (Vertical Symmetry)**: 50%(눈~코)/50%(코~턱) 균형 분석
   - ✨ **하관 조화 (Lower Face Harmony)**: 33%(인중)/67%(입~턱) 비율 분석
   - 🎯 **턱 곡률 (Jaw Curvature)**: 하악각(90-120°)과 턱목각(105-115°) 조화
   - Click-to-select with gradient animations
   - Circular progress indicators for each score

3. **Professional Chart Analytics (fl_chart)**
   - fl_chart 라이브러리 기반 인터랙티브 바 차트
   - 실제값 vs 이상값 비교 시각화
   - 호버 툴팁으로 정확한 수치 표시
   - 구간별 세부 분석 (왼쪽바깥, 왼쪽눈, 미간, 오른쪽눈, 오른쪽바깥 등)
   - 평균 대비 편차 분석 및 개선점 식별

### Scoring Algorithm

**Visualization-Based Precision Scoring:**

```dart
// 가로 황금비율 (Central 5 circles - Horizontal analysis)
Map<String, dynamic> _calculateVerticalScoreFromVisualization() {
  // Uses landmarks [234, 33, 133, 362, 359, 447] for 5-section analysis
  // Calculates deviation from ideal 20% per section
  // Score = 100 - (totalDeviation * 2)
  // Sections: 왼쪽바깥, 왼쪽눈, 미간, 오른쪽눈, 오른쪽바깥
}

// 세로 대칭성 (Right 2 circles - Vertical analysis) 
Map<String, dynamic> _calculateHorizontalScoreFromVisualization() {
  // Uses landmarks [8, 2, 152] for 2-section analysis
  // Ideal ratio: 50:50 balance (눈~코 / 코~턱)
  // Score = 100 - (totalDeviation * 1.5)
  // Sections: 눈~코, 인중~턱
}

// 하관 조화 (Left 2 circles - Lower face analysis)
Map<String, dynamic> _calculateLowerFaceScoreFromVisualization() {
  // Uses landmarks [2, 37, 152] for lower face analysis
  // Golden ratio: 33% upper, 67% lower (인중 / 입~턱)
  // Score = 100 - (totalDeviation * 1.2)
  // Sections: 인중, 입술~턱
}

// 턱 곡률 (Jaw curvature analysis)
Map<String, dynamic> _calculateJawlineAnalysis() {
  // 하악각(Gonial Angle): 90-120° 이상적 범위
  // 턱목각(Cervico-Mental Angle): 105-115° 이상적 범위
  // Combined scoring with weighted factors
}
```

**Weighted Overall Score Calculation:**
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

### UI/UX Design Features

**Modern Professional Interface:**
- Gradient backgrounds and shadows
- Smooth fade-in animations
- Interactive hover states
- Mobile-responsive grid layouts
- Professional color schemes

**User Experience Enhancements:**
- Always-visible detailed analytics (no toggle needed)
- Real-time visual feedback with hover tooltips
- Personalized beauty recommendations based on analysis
- Professional analysis timestamps
- Intuitive click-to-explore interactions
- Mobile-optimized responsive design
- Full-screen scrollable interface

**Recent UI/UX Improvements (Latest Updates):**
- **Chart Color Consistency**: Changed all chart colors from blue to indigo/purple theme for unified branding
- **Scrollable Beauty Score Header**: Fixed beauty score title to scroll with content instead of being fixed
- **Improved Mobile Layout**: Extended tab content area height by 50% (from 70% to 105% of screen height) for better scrolling experience
- **Minimum Image Height**: Guaranteed minimum 600px height for image display area across all device sizes

### State Management Architecture

**AppState Class Features:**
```dart
class AppState extends ChangeNotifier {
  // Image management
  Uint8List? _currentImage;
  Uint8List? _originalImage;  // Original image backup for restoration
  
  // Animation control
  bool _isAutoAnimationMode = false;
  double _beautyScoreAnimationProgress = 0.0;
  
  // Beauty analysis results
  Map<String, dynamic> _beautyAnalysis = {};
  
  // Original image restoration for Expert tab
  void restoreOriginalImage() {
    if (_originalImage != null) {
      _currentImage = Uint8List.fromList(_originalImage!);
      _showBeautyScore = false;
      _beautyAnalysis.clear();
      _showLandmarks = false; // Hide landmark visualizations
      
      // Hide all facial region visualizations
      for (final regionKey in _regionVisibility.all.keys) {
        _regionVisibility.setVisible(regionKey, false);
      }
      
      stopAutoAnimation();
    }
  }
  
  // Visualization-based calculations
  void _calculateBeautyAnalysis() {
    // Progressive calculation after face animation completion
    // Integration with visualization circle percentages
    // Comprehensive analysis storage
  }
}
```

## Mobile-First Design & User Interface

### Tab Navigation System

The application features a rebranded 3-tab interface with project name "BeautyGen":

- **📊 뷰티스코어 (BeautyScore)**: Comprehensive beauty score dashboard with professional analytics
- **⚡ 프리셋 (Preset)**: Quick preset transformations with advanced laser visualization and shot counters
- **🎨 프리스타일 (Freestyle)**: Advanced image warping and transformation tools

### Tab Switching Behavior

**Beauty Score Visualization Clearing:**
- When switching to **프리셋 (Preset)** or **프리스타일 (Freestyle)** tabs, the application automatically clears all beauty score visualizations
- This ensures a clean workspace for transformations
- The clearing process:
  - Hides beauty score overlays and animations
  - Stops all ongoing face region animations
  - Clears landmark animation progress
  - Resets beauty score animation progress
- Implementation: Enhanced `setCurrentTabIndex()` method in `AppState` class

**Animation Control:**
- Facial region animations only occur in the **분석 (Analysis)** tab
- Other tabs (Edit/Expert) do not trigger automatic animations
- Tab switching is tracked via `_currentTabIndex` state variable
- Animation prevention: `setLandmarks()` checks current tab before starting animations

**Freestyle Tab Enhanced Features:**
- **Percentage-based Influence Radius**: Similar to face_simulator.py, uses image size percentage (0.5%-25%) instead of fixed pixels
- **Automatic pixel conversion**: `getInfluenceRadiusPixels()` converts percentage to pixels based on smaller image dimension
- **History Management**: 
  - **Undo**: Reverts to previous state (up to 20 steps)
  - **Restore Original**: Returns to unmodified original image
  - Automatic history saving before each warp operation
- **Real-time Hover Visualization**: 
  - **Influence radius preview**: Blue translucent circle showing affected area
  - **Strength visualization**: Inner colored circle representing transformation intensity
  - **Mode-specific indicators**: Visual icons for Pull/Push/Expand/Shrink modes
  - **Color-coded modes**: Green (Pull), Red (Push), Orange (Expand), Purple (Shrink)
  - Only active in Freestyle tab, hidden during dragging operations
- **Improved UI**: Face_simulator.py style buttons and controls with real-time pixel preview

### Mobile Optimization Features

**Dynamic Image Sizing:**
```dart
// Mobile-optimized image container
Container(
  height: math.min(constraints.maxWidth * 1.2, constraints.maxHeight * 0.6),
  // Ensures image stays proportional and fills screen effectively
)
```

**Responsive Layout:**
- SingleChildScrollView for full-screen scrollability
- Compact tab design with 42px height
- Optimized margins and spacing for mobile devices
- Touch-friendly interface elements

**Professional Chart Integration:**
- fl_chart library for interactive data visualization
- Hover tooltips showing precise measurements
- Comparison bars: 이상값 (ideal) vs 실제값 (actual)
- Color-coded performance indicators

### Visualization System Updates

**BeautyScoreVisualizer Improvements:**
- Removed redundant score displays from overlay
- Simplified to show only angle measurements: "하악각123° 턱목각108°"
- Clean, professional appearance without visual clutter

**Dashboard Analytics:**
- Real-time percentage calculations for facial regions
- Visual deviation indicators (red: above average, green: below average)
- Section-specific analysis (왼쪽바깥, 왼쪽눈, 미간, 오른쪽눈, 오른쪽바깥)
- Integrated jaw curvature scoring in main dashboard

## Development Notes

- Python versions support flexible resolution and real-time parameter adjustment
- Uses advanced algorithms like Thin Plate Spline (TPS) for natural image transformations
- Face point coordinates are normalized and scaled appropriately for different image sizes
- Modular architecture allows easy extension of makeup styles and surgical modifications
- Preset system enables one-click application of complex multi-point transformations
- Flutter web application provides professional-grade beauty analysis dashboard
- Real-time Canvas painting for interactive facial visualization
- Comprehensive state management with Provider pattern
- Mobile-first responsive design with optimized touch interactions
- Professional chart visualization using fl_chart library
- Advanced facial measurement analytics with real-time comparison

## Recent Development Evolution (January 2025)

### Phase 1: Project Rebranding & UI Optimization
- **Tab Renaming**: Changed from "분석, 수정, 전문가" to "뷰티스코어, 프리셋, 프리스타일"
- **Project Rebranding**: Renamed from "Face Simulator" to "BeautyGen" across all files
- **AppBar Removal**: Eliminated space-wasting header, added floating reset button with SafeArea positioning
- **Files Modified**: `home_screen.dart`, `index.html`, project documentation

### Phase 2: Preset Functionality Implementation  
- **Backend Integration**: Implemented 5 preset algorithms from `face_simulator.py`
- **API Endpoints**: Added `/apply-preset` with FastAPI backend integration
- **Preset Types**: Lower jaw, middle jaw, cheek, front protusion, back slit transformations
- **MediaPipe Integration**: Landmark-based coordinate transformation logic
- **Files Modified**: `landmark_controls_widget.dart`, `backend/main.py`, `app_state.dart`

### Phase 3: Flickering Resolution & Image Optimization
- **Individual Loading States**: Replaced full-screen loading with preset-specific indicators
- **Image Optimization**: Added `gaplessPlayback`, `RepaintBoundary`, `filterQuality` optimizations
- **Smooth Transitions**: Implemented `updateImageFromPreset()` for flicker-free updates
- **Extended to Freestyle**: Applied same optimization to warp operations
- **User Feedback**: "클릭할때마다 깜빡이는 시간이 줄어들기는 했지만 아직 깜빡인다" → resolved

### Phase 4: Advanced Preset Features - First Implementation
- **Visual Laser Effects**: Real-time laser visualization during preset application
- **Shot Count Sliders**: 100-500 shots for jaw/cheek, 10-100 for eye treatments  
- **Cumulative Counters**: Total shot tracking and display system
- **Control Buttons**: Undo, restore, before/after, save with browser download
- **State Management**: Enhanced AppState with preset counters, settings, laser effects

### Phase 5: Mobile Optimization & Compact Layout
- **Before/After Enhancement**: Changed to use freestyle's slider comparison system
- **Compact Mobile Layout**: One-line preset design with title, counter, slider, button
- **UI Simplification**: Removed description text, optimized for mobile screens
- **Eye Treatment Units**: Changed from 10-100 times to 1-10% increments
- **Counter Updates**: Added "총 트임 %" display alongside "총 누적 샷"
- **Animation Speed**: Doubled laser animation speed as requested

### Phase 6: Dynamic Animation System & Tab Integration
- **Dynamic Animation Duration**: Laser animation time matches shot count (500 shots = 500 seconds duration)
- **Iteration-based Timing**: `_laserDurationMs = (iterations * 1000).clamp(1500, 15000)`
- **Progress Counters**: Real-time iteration display during animation
- **Tab Clearing**: Preset tab clears beauty score visualizations like freestyle tab
- **Continuous Animation**: Animation continues for all iterations without interruption
- **Enhanced Tab Switching**: `setCurrentTabIndex()` clears visualizations when switching tabs

### Error Resolution Timeline
1. **Tab Naming**: Fixed Korean text encoding compilation errors
2. **API Integration**: Resolved 404 errors with backend server restart 
3. **ImageHistoryItem**: Fixed missing `timestamp` and `_addToHistory` method errors
4. **Naming Conflicts**: Resolved `showLaserEffect` getter/method naming collision
5. **Variable Scope**: Fixed `iterations` variable declaration order in `_applyPresetWithSettings`
6. **Opacity Assertions**: Added `.clamp(0.0, 1.0)` to laser animation opacity calculations

### Key Technical Achievements
- **Zero-Flicker UI**: Achieved smooth transitions without screen flickering
- **Medical Simulation**: Professional laser treatment visualization
- **Mobile-First Design**: Optimized for touch interactions and small screens
- **Real-time Analytics**: Dynamic shot counting and progress tracking
- **Scalable Architecture**: Easy preset extension and configuration system
- **Cross-Platform Integration**: Seamless Flutter web and FastAPI backend communication

## Rules

- 코드 수정 시 자동으로 .claude 폴더에 필요한 사항을 저장하고 업데이트해라
- 코드 수정 시 자동으로 이 파일에 필요한 부분이 있으면 수정을 해라
- 필요하면 자동 compact를 실행해라.
