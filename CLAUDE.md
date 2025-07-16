# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-platform makeup and facial transformation application with:

1. **Android Application** (`app/`): Native Android app for real-time makeup application and facial feature modifications
2. **Python Applications** (`python_makeup_app/`): Python ports providing desktop and web-based makeup tools with advanced image warping capabilities

## Build and Development Commands

### Android Application

```bash
# Build the Android app
./gradlew build

# Clean build artifacts
./gradlew clean

# Install on connected device
./gradlew installDebug

# Run tests
./gradlew test
./gradlew connectedAndroidTest
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

### Android App Structure (`app/src/main/java/com/ding/makeup/`)

**Core Activities:**

- `MainActivity.java`: Main entry point, handles makeup application and eye magnification
- `MagnifyActivity.java`: Dedicated eye enlargement interface
- `SmallFaceActivity.java`: Face slimming functionality
- `AdjustLegActivity.java`: Leg lengthening feature

**Key Components:**

- `beauty/`: Contains transformation algorithms (`MagnifyEyeUtils`, `SmallFaceUtils`, `LongLegsUtils`)
- `draw/`: Makeup rendering classes (`BlushDraw`, `BrowDraw`, `EyeDraw`, `FoundationDraw`, `LipDraw`)
- `utils/`: Utility classes for bitmap processing, face point detection, and drawing operations

**Makeup Types (Region.java):**

- Foundation, Blush, Lip, Brow
- Eye Lash, Eye Contact, Eye Double, Eye Line, Eye Shadow

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

- **Android**: Uses custom face point detection with JSON-based landmark storage (`face_point.json`, `face_point1.json`)
- **Python**: Uses MediaPipe Face Mesh for real-time facial landmark detection
- Both implementations support similar transformation algorithms with mathematical warping formulas

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

- **Android**: Images and face point data stored in `app/src/main/assets/`
- **Python**: Uses MediaPipe for dynamic face detection, no static assets required
- Sample images available in `doc/` directory for testing

## Native Dependencies

- **Android**: Uses `libAmniXSkinSmooth.so` for skin smoothing (ARM and x86 versions in `jniLibs/`)
- **Python**: Pure Python implementation, no native dependencies

## Testing

- **Android**: Standard Android testing with JUnit and Espresso
- **Python**: No formal test structure, but applications include built-in validation

## Development Notes

- The Android version uses a fixed 200x200 mesh grid for transformations
- Python versions support flexible resolution and real-time parameter adjustment
- Both platforms implement similar core algorithms but with platform-specific optimizations
- Face point coordinates are normalized and scaled appropriately for different image sizes

## Rules

- 코드 수정 시 자동으로 .claude 폴더에 필요한 사항을 저장하고 업데이트해라
- 코드 수정 시 자동으로 이 파일에 필요한 부분이 있으면 수정을 해라
