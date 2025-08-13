# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based makeup and facial transformation application providing:

**Python Applications** (`python_makeup_app/`): Desktop and web-based makeup tools with advanced image warping capabilities

## Build and Development Commands

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

## Development Notes

- Python versions support flexible resolution and real-time parameter adjustment
- Uses advanced algorithms like Thin Plate Spline (TPS) for natural image transformations
- Face point coordinates are normalized and scaled appropriately for different image sizes
- Modular architecture allows easy extension of makeup styles and surgical modifications

## Rules

- 코드 수정 시 자동으로 .claude 폴더에 필요한 사항을 저장하고 업데이트해라
- 코드 수정 시 자동으로 이 파일에 필요한 부분이 있으면 수정을 해라
- 필요하면 자동 compact를 실행해라.
