# BeautyGen

**AI-Powered Facial Analysis and Virtual Beauty Simulation Platform**

BeautyGen is a comprehensive facial analysis application that combines professional beauty scoring with real-time facial transformations and virtual plastic surgery simulation. Built with Flutter and FastAPI, it provides both analytical insights and interactive beauty enhancement tools for professional-grade results.

## 🎯 Latest Updates

### ✨ Enhanced User Experience
- **Streamlined Interface**: Optimized first screen with enhanced logo branding
- **Smart Image Processing**: Automatic face detection with intelligent cropping
- **Multiple Face Handling**: Detects multiple faces and automatically selects the largest
- **User-Friendly Errors**: Improved error messages with helpful photography tips

### 🖼️ Visual Improvements
- **Professional Logo**: Custom brand identity with shadow effects (logo_e.png)
- **Web-Ready Assets**: Favicon, social media sharing images, splash screen
- **Responsive Design**: Mobile-first approach with overflow protection
- **Clean Layout**: Removed redundant text elements for cleaner interface

## 🚀 Features

### 📊 Professional Beauty Analysis
- **Real-time Facial Landmark Detection** - 468-point MediaPipe integration
- **Comprehensive Beauty Scoring** - Multi-factor analysis with weighted algorithms
- **Interactive Dashboard** - Professional charts and radar visualizations
- **AI-Powered Recommendations** - GPT-based beauty analysis and suggestions

### ⚡ Preset Transformations
- **💉 Facial Contouring** - Jaw, cheek, and chin enhancement
- **👁️ Eye Treatments** - Front/back eye corner adjustments
- **Shot-based System** - Realistic treatment progression tracking
- **Real-time Preview** - Laser animation effects during application

### 🎨 Freestyle Warping
- **Advanced Image Warping** - Pull, push, expand, shrink modes
- **Precision Controls** - Percentage-based influence radius
- **Undo/Redo System** - Up to 20-step history management
- **Before/After Comparison** - Side-by-side slider visualization

### 📸 Smart Camera & Upload System
- **Cross-platform Support** - Desktop webcam and mobile front camera
- **Face Guidelines** - Real-time 3:4 aspect ratio preview with overlay
- **Intelligent Cropping** - Face-based automatic cropping with 60% padding
- **Multiple Face Detection** - Handles multiple faces, selects largest automatically
- **Comprehensive Photo Guide** - Built-in tips for optimal photo quality
- **Minimum Size Guarantee** - Ensures images are at least 600x800 pixels

## 🏗️ Architecture

### Frontend (Flutter Web)
```
frontend/
├── lib/
│   ├── main.dart                    # Application entry point
│   ├── models/
│   │   └── app_state.dart          # Global state management
│   ├── screens/
│   │   └── home_screen.dart        # Main tab navigation
│   ├── services/
│   │   └── api_service.dart        # Backend API communication
│   ├── widgets/
│   │   ├── beauty_score_dashboard.dart     # Professional analysis UI
│   │   ├── landmark_controls_widget.dart   # Preset transformation controls
│   │   ├── warp_controls_widget.dart       # Freestyle warping interface
│   │   ├── before_after_comparison.dart    # Image comparison slider
│   │   └── camera_capture_widget.dart      # Camera integration
│   └── utils/
│       └── image_processor.dart    # Client-side image processing
├── assets/
│   └── images/
│       └── face_guide.png          # Camera guideline overlay
└── web/
    ├── index.html                  # Entry point with splash screen
    ├── favicon.png                 # Browser tab icon
    ├── manifest.json               # PWA configuration
    └── images/
        ├── logo_e.png              # Main brand logo (480x240)
        ├── og-image.png            # Social media sharing (1200x630)
        └── og-image-square.png     # Square social sharing (1200x1200)
```

### Backend (FastAPI)
```
backend/
├── main.py              # FastAPI application with all endpoints
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container deployment
└── temp_images/        # Temporary image storage
```

## 🛠️ Technology Stack

**Frontend:**
- Flutter 3.10+ (Cross-platform web application)
- Provider (State management)
- MediaPipe (Facial landmark detection)
- fl_chart 0.69.0 (Professional chart visualization)
- Camera package (Webcam/mobile integration)

**Backend:**
- FastAPI (High-performance API server)
- MediaPipe (468-point facial landmark detection)
- OpenCV (Image processing and transformations)
- PIL/Pillow (Image manipulation)
- NumPy (Numerical operations)

## 🚀 Quick Start

### Prerequisites
- Flutter SDK 3.10+
- Python 3.8+
- Chrome browser (for web development)

### Frontend Setup
```bash
cd frontend
flutter pub get
flutter run -d chrome --web-port=3000
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Docker Deployment
```bash
cd backend
docker build -t beautygen-backend .
docker run -p 8000:8000 beautygen-backend
```

## 📐 Core Algorithms

### Image Warping Formula
```
e = ((pow_r - dd) * (pow_r - dd)) / ((pow_r - dd + d_pull * d_pull) * (pow_r - dd + d_pull * d_pull))
```
Where:
- `pow_r`: squared influence radius
- `dd`: squared distance from touch point to pixel  
- `d_pull`: drag distance

### Beauty Score Calculation
```dart
final weightedScore = 
    (verticalScore * 0.25) +    // Horizontal Golden Ratio 25%
    (horizontalScore * 0.20) +  // Vertical Symmetry 20%
    (lowerFaceScore * 0.15) +   // Lower Face Harmony 15%
    (symmetry * 0.15) +         // Basic Symmetry 15%
    (eyeScore * 0.10) +         // Eyes 10%
    (noseScore * 0.08) +        // Nose 8%
    (lipScore * 0.05) +         // Lips 5%
    (jawScore * 0.02);          // Jaw Curvature 2%
```

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload-image` | POST | Image upload and storage |
| `/get-face-landmarks` | POST | MediaPipe face detection |
| `/apply-warp` | POST | Image warping transformations |
| `/apply-preset` | POST | Predefined transformation presets |
| `/get-beauty-analysis` | POST | Comprehensive beauty scoring |
| `/analyze-beauty-gpt` | POST | AI-powered analysis with recommendations |

## 🎨 Preset System

### Available Treatments
1. **💉 아래턱 (Lower Jaw)** - Landmarks 150, 379 → 4 (nose bridge direction)
2. **💉 중간턱 (Middle Jaw)** - Landmarks 172, 397 → 4 (nose bridge direction)
3. **💉 볼 (Cheek)** - Landmarks 215, 435 → 4 (nose bridge direction)
   - *Updated: Enhanced cheek targeting with landmark 361 for better precision*
4. **💉 앞트임 (Front Protusion)** - Eye landmarks with elliptical transformation
5. **💉 뒷트임 (Back Slit)** - Outer eye corner extension

### Shot Count System
- **Jaw/Cheek Treatments**: 100-500 shots
- **Eye Treatments**: 1%-10% intensity
- **Real-time Animation**: Laser treatment visualization
- **Cumulative Progress**: Session tracking and history

## 📱 User Interface

### Tab Navigation
- **📊 뷰티스코어 (BeautyScore)** - Professional analysis dashboard
- **⚡ 프리셋 (Preset)** - Quick transformations with laser effects
- **🎨 프리스타일 (Freestyle)** - Advanced warping and editing tools

### Mobile-First Design
- Dynamic image sizing based on screen constraints
- Touch-friendly interface elements
- Optimized margins and spacing
- SingleChildScrollView for full-screen scrollability

## 🔧 Development Notes

### Current State
- ✅ Multiple face detection with automatic largest face selection
- ✅ Enhanced UI with professional branding and shadow effects
- ✅ Smart image processing with face-based cropping
- ✅ User-friendly error handling and photography guides
- ✅ Web deployment ready with PWA assets
- ✅ Responsive layout with overflow protection
- ✅ AI analysis text parsing improvements

### Technical Details
- Zero-flicker UI with smooth transitions
- Professional chart integration with hover tooltips
- Comprehensive state management with Provider pattern
- Mobile-first responsive design with 480x240 logo branding
- Client-side image processing with minimum size guarantee
- Scalable architecture for easy feature extension

## 🚀 Getting Started

### 🎨 For Users
1. **Upload Photo**: Use gallery or camera to capture/select your front-facing photo
2. **Follow Guide**: Use the comprehensive photo guide for best results
3. **Analyze Beauty**: Get professional beauty scoring and AI recommendations
4. **Try Presets**: Experiment with virtual plastic surgery simulations
5. **Freestyle Edit**: Use advanced warping tools for precise adjustments

### 👩‍💻 For Developers
1. Clone the repository
2. Set up Flutter frontend and FastAPI backend (see Quick Start above)
3. Review CLAUDE.md for detailed technical guidance
4. Follow mobile-first design principles
5. Ensure user-friendly error messaging

## 📄 License

This project is for educational and demonstration purposes. Commercial use may require additional licensing for included assets and AI models.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Follow the coding guidelines in CLAUDE.md
4. Test on both mobile and desktop viewports
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request