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

### Preset Extension

New presets can be easily added by:
1. Creating new preset function following the naming pattern `apply_*_preset()`
2. Adding UI button in `setup_warp_controls()`
3. Using existing transformation functions with specific parameters
4. Adding visualization calls with `draw_preset_visualization()`

## Development Notes

- Python versions support flexible resolution and real-time parameter adjustment
- Uses advanced algorithms like Thin Plate Spline (TPS) for natural image transformations
- Face point coordinates are normalized and scaled appropriately for different image sizes
- Modular architecture allows easy extension of makeup styles and surgical modifications
- Preset system enables one-click application of complex multi-point transformations

## Rules

- 코드 수정 시 자동으로 .claude 폴더에 필요한 사항을 저장하고 업데이트해라
- 코드 수정 시 자동으로 이 파일에 필요한 부분이 있으면 수정을 해라
- 필요하면 자동 compact를 실행해라.
