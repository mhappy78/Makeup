# -*- coding: utf-8 -*-
"""
Main User Interface - Streamlit based
"""
import streamlit as st
import cv2
import numpy as np
import time
from typing import Optional, List, Dict, Any
from PIL import Image
import io
import base64

# Project module imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.face_engine import MediaPipeFaceEngine, VideoStream
from engines.makeup_engine import RealtimeMakeupEngine
from engines.surgery_engine import RealtimeSurgeryEngine
from engines.integrated_engine import IntegratedEngine, IntegratedConfig, EffectPriority
from models.core import Point3D, Color
from models.makeup import MakeupConfig, LipstickConfig, EyeshadowConfig, BlushConfig, FoundationConfig, EyelinerConfig, EyeshadowStyle
from models.surgery import SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig
from utils.image_processor import ImageProcessor
from utils.image_gallery import ImageGallery


class MainInterface:
    """Main user interface class"""
    
    def __init__(self):
        """Initialize interface"""
        self.face_engine = MediaPipeFaceEngine()
        self.makeup_engine = RealtimeMakeupEngine()
        self.surgery_engine = RealtimeSurgeryEngine()
        self.integrated_engine = IntegratedEngine()
        self.image_processor = ImageProcessor()
        self.image_gallery = ImageGallery()
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state"""
        # Handle both dictionary and object style session state
        session_keys = [
            ('current_image', None),
            ('original_image', None),
            ('face_landmarks', None),
            ('camera_active', False),
            ('video_stream', None),
            ('processing_results', []),
            ('makeup_config', None),
            ('surgery_config', None)
        ] 
       
        for key, default_value in session_keys:
            if hasattr(st.session_state, key):
                # Object style session_state
                if not hasattr(st.session_state, key) or getattr(st.session_state, key) is None:
                    setattr(st.session_state, key, default_value)
            else:
                # Dictionary style session_state (test environment)
                if key not in st.session_state:
                    st.session_state[key] = default_value
    
    def _get_session_value(self, key: str, default=None):
        """Get value from session state (supports both dictionary and object)"""
        if hasattr(st.session_state, 'get'):
            return st.session_state.get(key, default)
        elif hasattr(st.session_state, key):
            return getattr(st.session_state, key, default)
        else:
            return default
    
    def _set_session_value(self, key: str, value):
        """Set value in session state (supports both dictionary and object)"""
        if hasattr(st.session_state, '__setitem__'):
            st.session_state[key] = value
        else:
            setattr(st.session_state, key, value)
    
    def run(self):
        """Run main interface"""
        st.set_page_config(
            page_title="Natural Makeup & Surgery Simulation",
            page_icon="🎨",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Main header
        st.title("🎨 Natural Makeup & Surgery Simulation")
        st.markdown("**AI-based Real-time Beauty Simulation Platform**")
        
        # Setup sidebar
        self._setup_sidebar()
        
        # Setup main content area
        self._setup_main_content()
        
        # Handle real-time camera processing
        if self._get_session_value('camera_active'):
            self._handle_camera_stream()
    
    def _setup_sidebar(self):
        """Setup sidebar"""
        st.sidebar.title("🎛️ Control Panel")
        
        # Input source selection
        st.sidebar.markdown("### 📷 Input Source")
        input_source = st.sidebar.radio(
            "Select source:",
            ["Image Upload", "Real-time Camera"],
            key="input_source"
        )
        
        if input_source == "Image Upload":
            self._setup_image_upload()
        else:
            self._setup_camera_controls()
        
        st.sidebar.markdown("---")
        
        # Effect setting tabs
        tab1, tab2 = st.sidebar.tabs(["💄 Makeup", "✂️ Surgery"])
        
        with tab1:
            self._setup_makeup_controls()
        
        with tab2:
            self._setup_surgery_controls()
        
        st.sidebar.markdown("---")
        
        # Utility buttons
        self._setup_utility_buttons()  
  
    def _setup_image_upload(self):
        """Setup image upload"""
        uploaded_file = st.sidebar.file_uploader(
            "Select an image",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            help="Supports JPG, PNG, BMP files"
        )
        
        if uploaded_file is not None:
            try:
                # Load image
                file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                
                if image is not None:
                    # BGR to RGB conversion
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Update session state
                    self._set_session_value('original_image', image.copy())
                    self._set_session_value('current_image', image.copy())
                    self._set_session_value('camera_active', False)
                    
                    # Face detection
                    self._detect_face(image)
                    
                    st.sidebar.success("✅ Image loaded successfully!")
                else:
                    st.sidebar.error("❌ Cannot read image.")
            except Exception as e:
                st.sidebar.error(f"❌ Image load failed: {str(e)}")
    
    def _setup_camera_controls(self):
        """Setup camera controls"""
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("📹 Start Camera", key="start_camera"):
                self._start_camera()
        
        with col2:
            if st.button("⏹️ Stop Camera", key="stop_camera"):
                self._stop_camera()
        
        # Camera status display
        if self._get_session_value('camera_active'):
            st.sidebar.success("🟢 Camera Active")
        else:
            st.sidebar.info("🔴 Camera Inactive")
        
        # Camera settings
        if self._get_session_value('camera_active'):
            st.sidebar.markdown("#### 📷 Camera Settings")
            
            # Frame skip setting
            frame_skip = st.sidebar.slider(
                "Frame Skip (Performance Optimization)",
                min_value=1,
                max_value=10,
                value=3,
                help="Higher values improve performance but reduce responsiveness"
            )
            
            # Resolution setting
            resolution = st.sidebar.selectbox(
                "Resolution Setting",
                ["640x480", "800x600", "1280x720"],
                index=0
            )    

    def _setup_makeup_controls(self):
        """Setup enhanced makeup controls with real-time preview"""
        st.markdown("### 💄 Makeup Control Panel")
        
        # Real-time preview toggle
        realtime_preview = st.checkbox(
            "🔄 Real-time Preview",
            value=False,
            key="realtime_preview",
            help="Automatically apply changes as you adjust controls"
        )
        
        # Makeup category tabs for better organization
        lipstick_tab, eyeshadow_tab, blush_tab, foundation_tab, eyeliner_tab = st.tabs([
            "💋 Lipstick", "👁️ Eyeshadow", "🌸 Blush", "🎨 Foundation", "✏️ Eyeliner"
        ])
        
        # Track if any changes were made for real-time updates
        changes_made = False
        
        # Lipstick Controls
        with lipstick_tab:
            st.markdown("#### 💋 Lipstick Settings")
            
            # Lipstick presets
            lipstick_presets = {
                "Natural Pink": "#FFB6C1",
                "Classic Red": "#DC143C", 
                "Deep Berry": "#8B0000",
                "Coral": "#FF7F50",
                "Nude": "#D2B48C",
                "Custom": None
            }
            
            lipstick_preset = st.selectbox(
                "Choose Preset",
                options=list(lipstick_presets.keys()),
                key="lipstick_preset"
            )
            
            # Set color based on preset
            if lipstick_preset != "Custom" and lipstick_presets[lipstick_preset]:
                default_color = lipstick_presets[lipstick_preset]
            else:
                default_color = self._get_session_value('lipstick_color', '#FF1493')
            
            # Color selection with enhanced picker
            col1, col2 = st.columns([2, 1])
            with col1:
                lipstick_color = st.color_picker(
                    "Lipstick Color",
                    value=default_color,
                    key="lipstick_color"
                )
            with col2:
                # Color preview
                st.markdown(f'<div style="width:50px;height:30px;background-color:{lipstick_color};border:1px solid #ccc;border-radius:5px;"></div>', 
                           unsafe_allow_html=True)
            
            # Intensity and glossiness controls
            col1, col2 = st.columns(2)
            with col1:
                lipstick_intensity = st.slider(
                    "Intensity",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.6,
                    step=0.05,
                    key="lipstick_intensity",
                    help="Controls opacity and coverage"
                )
            with col2:
                lipstick_glossiness = st.slider(
                    "Glossiness",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                    key="lipstick_glossiness",
                    help="0 = Matte, 1 = High Gloss"
                )
            
            # Blend mode selection
            blend_modes = ["Normal", "Multiply", "Overlay", "Soft Light"]
            lipstick_blend = st.selectbox(
                "Blend Mode",
                options=blend_modes,
                key="lipstick_blend_mode",
                help="How the lipstick blends with natural lip color"
            )
        
        # Eyeshadow Controls
        with eyeshadow_tab:
            st.markdown("#### 👁️ Eyeshadow Settings")
            
            # Eyeshadow style presets
            eyeshadow_styles = ["Natural", "Smoky", "Cut Crease", "Halo", "Gradient"]
            eyeshadow_style = st.selectbox(
                "Eyeshadow Style",
                options=eyeshadow_styles,
                key="eyeshadow_style"
            )
            
            # Multi-color selection
            st.markdown("**Color Palette**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                eyeshadow_color1 = st.color_picker(
                    "Primary",
                    value="#800080",
                    key="eyeshadow_color1"
                )
            with col2:
                eyeshadow_color2 = st.color_picker(
                    "Secondary",
                    value="#DDA0DD",
                    key="eyeshadow_color2"
                )
            with col3:
                eyeshadow_color3 = st.color_picker(
                    "Highlight",
                    value="#F0E68C",
                    key="eyeshadow_color3"
                )
            
            # Intensity and shimmer controls
            col1, col2 = st.columns(2)
            with col1:
                eyeshadow_intensity = st.slider(
                    "Intensity",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.4,
                    step=0.05,
                    key="eyeshadow_intensity"
                )
            with col2:
                eyeshadow_shimmer = st.slider(
                    "Shimmer",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.2,
                    step=0.05,
                    key="eyeshadow_shimmer",
                    help="0 = Matte, 1 = High Shimmer"
                )
        
        # Blush Controls
        with blush_tab:
            st.markdown("#### 🌸 Blush Settings")
            
            # Blush presets
            blush_presets = {
                "Natural Pink": "#FFB6C1",
                "Peach": "#FFCBA4",
                "Rose": "#FF69B4",
                "Coral": "#FF7F50",
                "Berry": "#DC143C"
            }
            
            blush_preset = st.selectbox(
                "Choose Preset",
                options=list(blush_presets.keys()),
                key="blush_preset"
            )
            
            # Color selection
            col1, col2 = st.columns([2, 1])
            with col1:
                blush_color = st.color_picker(
                    "Blush Color",
                    value=blush_presets.get(blush_preset, "#FFB6C1"),
                    key="blush_color"
                )
            with col2:
                st.markdown(f'<div style="width:50px;height:30px;background-color:{blush_color};border:1px solid #ccc;border-radius:5px;"></div>', 
                           unsafe_allow_html=True)
            
            # Intensity and placement
            col1, col2 = st.columns(2)
            with col1:
                blush_intensity = st.slider(
                    "Intensity",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.05,
                    key="blush_intensity"
                )
            with col2:
                blush_placement = st.selectbox(
                    "Placement",
                    options=["Cheeks", "Temples", "Nose"],
                    key="blush_placement"
                )
        
        # Foundation Controls
        with foundation_tab:
            st.markdown("#### 🎨 Foundation Settings")
            
            # Skin tone presets
            foundation_presets = {
                "Fair": "#F5DEB3",
                "Light": "#DEB887",
                "Medium": "#D2B48C",
                "Tan": "#BC9A6A",
                "Deep": "#8B7355"
            }
            
            foundation_preset = st.selectbox(
                "Skin Tone",
                options=list(foundation_presets.keys()),
                key="foundation_preset"
            )
            
            # Color selection
            col1, col2 = st.columns([2, 1])
            with col1:
                foundation_color = st.color_picker(
                    "Foundation Color",
                    value=foundation_presets.get(foundation_preset, "#F5DEB3"),
                    key="foundation_color"
                )
            with col2:
                st.markdown(f'<div style="width:50px;height:30px;background-color:{foundation_color};border:1px solid #ccc;border-radius:5px;"></div>', 
                           unsafe_allow_html=True)
            
            # Coverage and finish
            col1, col2 = st.columns(2)
            with col1:
                foundation_coverage = st.slider(
                    "Coverage",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.05,
                    key="foundation_coverage",
                    help="0 = Sheer, 1 = Full Coverage"
                )
            with col2:
                foundation_finish = st.selectbox(
                    "Finish",
                    options=["Natural", "Matte", "Dewy"],
                    key="foundation_finish"
                )
        
        # Eyeliner Controls
        with eyeliner_tab:
            st.markdown("#### ✏️ Eyeliner Settings")
            
            # Eyeliner color
            col1, col2 = st.columns([2, 1])
            with col1:
                eyeliner_color = st.color_picker(
                    "Eyeliner Color",
                    value="#000000",
                    key="eyeliner_color"
                )
            with col2:
                st.markdown(f'<div style="width:50px;height:30px;background-color:{eyeliner_color};border:1px solid #ccc;border-radius:5px;"></div>', 
                           unsafe_allow_html=True)
            
            # Thickness and style
            col1, col2 = st.columns(2)
            with col1:
                eyeliner_thickness = st.slider(
                    "Thickness",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                    key="eyeliner_thickness"
                )
            with col2:
                eyeliner_style = st.selectbox(
                    "Style",
                    options=["Natural", "Winged", "Dramatic"],
                    key="eyeliner_style"
                )
            
            # Intensity
            eyeliner_intensity = st.slider(
                "Intensity",
                min_value=0.0,
                max_value=1.0,
                value=1.0,
                step=0.05,
                key="eyeliner_intensity"
            )
        
        # Control buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💄 Apply Makeup", key="apply_makeup", use_container_width=True):
                self._apply_makeup()
        
        with col2:
            if st.button("👁️ Preview", key="preview_makeup", use_container_width=True):
                self._preview_makeup()
        
        with col3:
            if st.button("🔄 Reset", key="reset_makeup", use_container_width=True):
                self._reset_makeup_controls()
        
        # Real-time preview handling
        if realtime_preview and self._get_session_value('current_image') is not None:
            # Check if any control values changed
            if self._makeup_controls_changed():
                self._preview_makeup()
    
    def _surgery_controls_changed(self) -> bool:
        """Check if surgery control values have changed"""
        # This would compare current values with previous values
        # For now, return True to enable real-time updates
        return True
    
    def _create_surgery_config(self) -> SurgeryConfig:
        """Create surgery configuration from current control settings"""
        # Get current control values
        nose_config = NoseConfig(
            height_adjustment=self._get_session_value('nose_height', 0.0),
            width_adjustment=self._get_session_value('nose_width', 0.0),
            tip_adjustment=self._get_session_value('nose_tip', 0.0),
            bridge_adjustment=self._get_session_value('nose_bridge', 0.0)
        )
        
        eye_config = EyeConfig(
            size_adjustment=self._get_session_value('eye_size', 0.0),
            shape_adjustment=self._get_session_value('eye_shape', 0.0),
            position_adjustment=self._get_session_value('eye_position', 0.0),
            angle_adjustment=self._get_session_value('eye_angle', 0.0)
        )
        
        jawline_config = JawlineConfig(
            width_adjustment=self._get_session_value('jaw_width', 0.0),
            angle_adjustment=self._get_session_value('jaw_angle', 0.0),
            length_adjustment=self._get_session_value('jaw_length', 0.0)
        )
        
        cheekbone_config = CheekboneConfig(
            height_adjustment=self._get_session_value('cheek_height', 0.0),
            width_adjustment=self._get_session_value('cheek_width', 0.0),
            prominence_adjustment=self._get_session_value('cheek_prominence', 0.0)
        )
        
        return SurgeryConfig(
            nose=nose_config,
            eyes=eye_config,
            jawline=jawline_config,
            cheekbones=cheekbone_config
        )
    
    def _apply_surgery(self):
        """Apply surgery simulation"""
        if self._get_session_value('current_image') is None:
            st.error("No image available. Please upload an image or start camera first.")
            return
        
        if not self._get_session_value('face_landmarks'):
            st.error("Face not detected. Surgery simulation requires face detection.")
            return
        
        try:
            with st.spinner("Applying surgery simulation..."):
                # Create surgery configuration
                surgery_config = self._create_surgery_config()
                
                # Get current image and landmarks
                current_image = self._get_session_value('current_image')
                face_landmarks = self._get_session_value('face_landmarks')
                
                # Apply surgery simulation
                start_time = time.time()
                surgery_result = self.surgery_engine.apply_full_surgery(
                    current_image, face_landmarks, surgery_config
                )
                processing_time = time.time() - start_time
                
                if surgery_result and surgery_result.is_successful():
                    # Update current image
                    self._set_session_value('current_image', surgery_result.image)
                    self._set_session_value('face_landmarks', surgery_result.modified_landmarks)
                    
                    # Store processing results
                    processing_result = {
                        'processing_time': processing_time,
                        'applied_effects': surgery_result.applied_modifications,
                        'natural_score': surgery_result.natural_score,
                        'quality_score': surgery_result.natural_score
                    }
                    
                    processing_results = self._get_session_value('processing_results', [])
                    processing_results.append(processing_result)
                    self._set_session_value('processing_results', processing_results)
                    
                    # Show success message with natural score
                    if surgery_result.is_natural():
                        st.success(f"✅ Surgery applied successfully! Natural score: {surgery_result.natural_score:.2f}")
                    else:
                        st.warning(f"⚠️ Surgery applied with low natural score: {surgery_result.natural_score:.2f}")
                    
                    st.rerun()
                else:
                    st.error("❌ Surgery simulation failed. Please try with different settings.")
                    
        except Exception as e:
            st.error(f"❌ Surgery simulation error: {str(e)}")
    
    def _preview_surgery(self):
        """Preview surgery simulation without applying permanently"""
        if self._get_session_value('current_image') is None:
            st.warning("No image available for preview.")
            return
        
        if not self._get_session_value('face_landmarks'):
            st.warning("Face not detected. Cannot preview surgery.")
            return
        
        try:
            # Create surgery configuration
            surgery_config = self._create_surgery_config()
            
            # Get original image for preview
            original_image = self._get_session_value('original_image')
            if original_image is None:
                original_image = self._get_session_value('current_image')
            
            face_landmarks = self._get_session_value('face_landmarks')
            
            # Apply surgery simulation for preview
            surgery_result = self.surgery_engine.apply_full_surgery(
                original_image, face_landmarks, surgery_config
            )
            
            if surgery_result and surgery_result.is_successful():
                # Temporarily update current image for preview
                self._set_session_value('current_image', surgery_result.image)
                
                # Show preview info
                st.info(f"👁️ Preview mode - Natural score: {surgery_result.natural_score:.2f}")
                st.rerun()
            else:
                st.error("❌ Preview failed. Please check your settings.")
                
        except Exception as e:
            st.error(f"❌ Preview error: {str(e)}")
    
    def _reset_surgery_controls(self):
        """Reset all surgery controls to default values"""
        # Reset nose controls
        self._set_session_value('nose_height', 0.0)
        self._set_session_value('nose_width', 0.0)
        self._set_session_value('nose_tip', 0.0)
        self._set_session_value('nose_bridge', 0.0)
        
        # Reset eye controls
        self._set_session_value('eye_size', 0.0)
        self._set_session_value('eye_shape', 0.0)
        self._set_session_value('eye_position', 0.0)
        self._set_session_value('eye_angle', 0.0)
        
        # Reset jawline controls
        self._set_session_value('jaw_width', 0.0)
        self._set_session_value('jaw_angle', 0.0)
        self._set_session_value('jaw_length', 0.0)
        
        # Reset cheekbone controls
        self._set_session_value('cheek_height', 0.0)
        self._set_session_value('cheek_width', 0.0)
        self._set_session_value('cheek_prominence', 0.0)
        
        # Reset to original image
        original_image = self._get_session_value('original_image')
        if original_image is not None:
            self._set_session_value('current_image', original_image.copy())
        
        st.success("🔄 Surgery controls reset to default values")
        st.rerun()
    
    def _validate_surgery_proportions(self):
        """Validate surgery proportions and provide feedback"""
        if not self._get_session_value('face_landmarks'):
            st.warning("Face not detected. Cannot validate proportions.")
            return
        
        try:
            # Create surgery configuration
            surgery_config = self._create_surgery_config()
            
            # Get face landmarks
            face_landmarks = self._get_session_value('face_landmarks')
            
            # Calculate modification intensity
            total_intensity = surgery_config.get_total_modification_intensity()
            
            # Validate proportions using surgery engine
            is_natural = self.surgery_engine.validate_proportions(face_landmarks)
            
            # Show validation results
            st.markdown("### 📊 Surgery Validation Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Intensity", f"{total_intensity:.2f}")
                st.metric("Natural Proportions", "✅ Yes" if is_natural else "❌ No")
            
            with col2:
                # Individual feature intensities
                nose_intensity = (abs(surgery_config.nose.height_adjustment) + 
                                abs(surgery_config.nose.width_adjustment) + 
                                abs(surgery_config.nose.tip_adjustment) + 
                                abs(surgery_config.nose.bridge_adjustment)) / 4.0
                
                eye_intensity = (abs(surgery_config.eyes.size_adjustment) + 
                               abs(surgery_config.eyes.shape_adjustment) + 
                               abs(surgery_config.eyes.position_adjustment) + 
                               abs(surgery_config.eyes.angle_adjustment)) / 4.0
                
                st.metric("Nose Intensity", f"{nose_intensity:.2f}")
                st.metric("Eye Intensity", f"{eye_intensity:.2f}")
            
            # Recommendations
            if total_intensity > 0.5:
                st.warning("⚠️ High modification intensity detected. Consider reducing adjustments for more natural results.")
            elif total_intensity > 0.3:
                st.info("ℹ️ Moderate modifications. Preview recommended before applying.")
            else:
                st.success("✅ Natural modification range. Safe to apply.")
            
            # Feature-specific recommendations
            if nose_intensity > 0.4:
                st.warning("👃 Nose modifications are quite strong. Consider reducing for natural look.")
            if eye_intensity > 0.4:
                st.warning("👁️ Eye modifications are quite strong. Consider reducing for natural look.")
                
        except Exception as e:
            st.error(f"❌ Validation error: {str(e)}")
    
    def _setup_surgery_controls(self):
        """Setup enhanced surgery simulation controls with real-time preview"""
        st.markdown("### ✂️ Surgery Simulation Control Panel")
        
        # Real-time preview toggle
        realtime_surgery_preview = st.checkbox(
            "🔄 Real-time Surgery Preview",
            value=False,
            key="realtime_surgery_preview",
            help="Automatically apply changes as you adjust surgery controls"
        )
        
        # Surgery category tabs for better organization
        nose_tab, eye_tab, jaw_tab, cheek_tab = st.tabs([
            "👃 Nose", "👁️ Eyes", "🦴 Jawline", "🏔️ Cheekbones"
        ])
        
        # Track if any changes were made for real-time updates
        surgery_changes_made = False
        
        # Nose Surgery Controls
        with nose_tab:
            st.markdown("#### 👃 Nose Surgery Settings")
            
            # Nose surgery presets
            nose_presets = {
                "Natural": {"height": 0.0, "width": 0.0, "tip": 0.0, "bridge": 0.0},
                "Refined": {"height": 0.2, "width": -0.1, "tip": 0.1, "bridge": 0.1},
                "Dramatic": {"height": 0.4, "width": -0.2, "tip": 0.2, "bridge": 0.2},
                "Subtle": {"height": 0.1, "width": -0.05, "tip": 0.05, "bridge": 0.05},
                "Custom": None
            }
            
            nose_preset = st.selectbox(
                "Choose Preset",
                options=list(nose_presets.keys()),
                key="nose_preset",
                help="Quick preset options for common nose modifications"
            )
            
            # Set values based on preset
            if nose_preset != "Custom" and nose_presets[nose_preset]:
                preset_values = nose_presets[nose_preset]
                default_height = preset_values["height"]
                default_width = preset_values["width"]
                default_tip = preset_values["tip"]
                default_bridge = preset_values["bridge"]
            else:
                default_height = self._get_session_value('nose_height', 0.0)
                default_width = self._get_session_value('nose_width', 0.0)
                default_tip = self._get_session_value('nose_tip', 0.0)
                default_bridge = self._get_session_value('nose_bridge', 0.0)
            
            # Nose adjustment controls with enhanced feedback
            col1, col2 = st.columns(2)
            
            with col1:
                nose_height = st.slider(
                    "Height Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_height,
                    step=0.05,
                    key="nose_height",
                    help="Adjust nose height (-1.0 = lower, +1.0 = higher)"
                )
                
                nose_width = st.slider(
                    "Width Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_width,
                    step=0.05,
                    key="nose_width",
                    help="Adjust nose width (-1.0 = narrower, +1.0 = wider)"
                )
            
            with col2:
                nose_tip = st.slider(
                    "Tip Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_tip,
                    step=0.05,
                    key="nose_tip",
                    help="Adjust nose tip position (-1.0 = up, +1.0 = down)"
                )
                
                nose_bridge = st.slider(
                    "Bridge Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_bridge,
                    step=0.05,
                    key="nose_bridge",
                    help="Adjust nose bridge prominence (-1.0 = flatter, +1.0 = more prominent)"
                )
            
            # Natural range feedback
            nose_intensity = abs(nose_height) + abs(nose_width) + abs(nose_tip) + abs(nose_bridge)
            if nose_intensity > 2.0:
                st.warning("⚠️ High modification intensity - may look unnatural")
            elif nose_intensity > 1.0:
                st.info("ℹ️ Moderate modification - preview recommended")
            elif nose_intensity > 0.1:
                st.success("✅ Natural modification range")
        
        # Eye Surgery Controls
        with eye_tab:
            st.markdown("#### 👁️ Eye Surgery Settings")
            
            # Eye surgery presets
            eye_presets = {
                "Natural": {"size": 0.0, "shape": 0.0, "position": 0.0, "angle": 0.0},
                "Enlarged": {"size": 0.3, "shape": 0.1, "position": 0.0, "angle": 0.1},
                "Almond Shape": {"size": 0.1, "shape": 0.4, "position": 0.0, "angle": 0.2},
                "Wide Set": {"size": 0.0, "shape": 0.0, "position": -0.2, "angle": 0.0},
                "Custom": None
            }
            
            eye_preset = st.selectbox(
                "Choose Preset",
                options=list(eye_presets.keys()),
                key="eye_preset",
                help="Quick preset options for common eye modifications"
            )
            
            # Set values based on preset
            if eye_preset != "Custom" and eye_presets[eye_preset]:
                preset_values = eye_presets[eye_preset]
                default_eye_size = preset_values["size"]
                default_eye_shape = preset_values["shape"]
                default_eye_position = preset_values["position"]
                default_eye_angle = preset_values["angle"]
            else:
                default_eye_size = self._get_session_value('eye_size', 0.0)
                default_eye_shape = self._get_session_value('eye_shape', 0.0)
                default_eye_position = self._get_session_value('eye_position', 0.0)
                default_eye_angle = self._get_session_value('eye_angle', 0.0)
            
            # Eye adjustment controls
            col1, col2 = st.columns(2)
            
            with col1:
                eye_size = st.slider(
                    "Size Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_eye_size,
                    step=0.05,
                    key="eye_size",
                    help="Adjust eye size (-1.0 = smaller, +1.0 = larger)"
                )
                
                eye_shape = st.slider(
                    "Shape Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_eye_shape,
                    step=0.05,
                    key="eye_shape",
                    help="Adjust eye shape (-1.0 = rounder, +1.0 = more almond)"
                )
            
            with col2:
                eye_position = st.slider(
                    "Position Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_eye_position,
                    step=0.05,
                    key="eye_position",
                    help="Adjust eye spacing (-1.0 = closer, +1.0 = wider apart)"
                )
                
                eye_angle = st.slider(
                    "Angle Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_eye_angle,
                    step=0.05,
                    key="eye_angle",
                    help="Adjust eye angle (-1.0 = downward, +1.0 = upward)"
                )
            
            # Natural range feedback
            eye_intensity = abs(eye_size) + abs(eye_shape) + abs(eye_position) + abs(eye_angle)
            if eye_intensity > 2.0:
                st.warning("⚠️ High modification intensity - may look unnatural")
            elif eye_intensity > 1.0:
                st.info("ℹ️ Moderate modification - preview recommended")
            elif eye_intensity > 0.1:
                st.success("✅ Natural modification range")
        
        # Jawline Surgery Controls
        with jaw_tab:
            st.markdown("#### 🦴 Jawline Surgery Settings")
            
            # Jawline surgery presets
            jaw_presets = {
                "Natural": {"width": 0.0, "angle": 0.0, "length": 0.0},
                "V-Line": {"width": -0.3, "angle": 0.2, "length": -0.1},
                "Square Jaw": {"width": 0.2, "angle": -0.2, "length": 0.1},
                "Refined": {"width": -0.1, "angle": 0.1, "length": 0.0},
                "Custom": None
            }
            
            jaw_preset = st.selectbox(
                "Choose Preset",
                options=list(jaw_presets.keys()),
                key="jaw_preset",
                help="Quick preset options for common jawline modifications"
            )
            
            # Set values based on preset
            if jaw_preset != "Custom" and jaw_presets[jaw_preset]:
                preset_values = jaw_presets[jaw_preset]
                default_jaw_width = preset_values["width"]
                default_jaw_angle = preset_values["angle"]
                default_jaw_length = preset_values["length"]
            else:
                default_jaw_width = self._get_session_value('jaw_width', 0.0)
                default_jaw_angle = self._get_session_value('jaw_angle', 0.0)
                default_jaw_length = self._get_session_value('jaw_length', 0.0)
            
            # Jawline adjustment controls
            col1, col2 = st.columns(2)
            
            with col1:
                jaw_width = st.slider(
                    "Width Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_jaw_width,
                    step=0.05,
                    key="jaw_width",
                    help="Adjust jawline width (-1.0 = narrower, +1.0 = wider)"
                )
                
                jaw_angle = st.slider(
                    "Angle Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_jaw_angle,
                    step=0.05,
                    key="jaw_angle",
                    help="Adjust jawline angle (-1.0 = softer, +1.0 = sharper)"
                )
            
            with col2:
                jaw_length = st.slider(
                    "Length Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_jaw_length,
                    step=0.05,
                    key="jaw_length",
                    help="Adjust jawline length (-1.0 = shorter, +1.0 = longer)"
                )
            
            # Natural range feedback
            jaw_intensity = abs(jaw_width) + abs(jaw_angle) + abs(jaw_length)
            if jaw_intensity > 1.5:
                st.warning("⚠️ High modification intensity - may look unnatural")
            elif jaw_intensity > 0.8:
                st.info("ℹ️ Moderate modification - preview recommended")
            elif jaw_intensity > 0.1:
                st.success("✅ Natural modification range")
        
        # Cheekbone Surgery Controls
        with cheek_tab:
            st.markdown("#### 🏔️ Cheekbone Surgery Settings")
            
            # Cheekbone surgery presets
            cheek_presets = {
                "Natural": {"height": 0.0, "width": 0.0, "prominence": 0.0},
                "High Cheekbones": {"height": 0.3, "width": 0.0, "prominence": 0.2},
                "Reduced": {"height": -0.2, "width": -0.1, "prominence": -0.1},
                "Sculpted": {"height": 0.2, "width": -0.1, "prominence": 0.3},
                "Custom": None
            }
            
            cheek_preset = st.selectbox(
                "Choose Preset",
                options=list(cheek_presets.keys()),
                key="cheek_preset",
                help="Quick preset options for common cheekbone modifications"
            )
            
            # Set values based on preset
            if cheek_preset != "Custom" and cheek_presets[cheek_preset]:
                preset_values = cheek_presets[cheek_preset]
                default_cheek_height = preset_values["height"]
                default_cheek_width = preset_values["width"]
                default_cheek_prominence = preset_values["prominence"]
            else:
                default_cheek_height = self._get_session_value('cheek_height', 0.0)
                default_cheek_width = self._get_session_value('cheek_width', 0.0)
                default_cheek_prominence = self._get_session_value('cheek_prominence', 0.0)
            
            # Cheekbone adjustment controls
            col1, col2 = st.columns(2)
            
            with col1:
                cheek_height = st.slider(
                    "Height Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_cheek_height,
                    step=0.05,
                    key="cheek_height",
                    help="Adjust cheekbone height (-1.0 = lower, +1.0 = higher)"
                )
                
                cheek_width = st.slider(
                    "Width Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_cheek_width,
                    step=0.05,
                    key="cheek_width",
                    help="Adjust cheekbone width (-1.0 = narrower, +1.0 = wider)"
                )
            
            with col2:
                cheek_prominence = st.slider(
                    "Prominence Adjustment",
                    min_value=-1.0,
                    max_value=1.0,
                    value=default_cheek_prominence,
                    step=0.05,
                    key="cheek_prominence",
                    help="Adjust cheekbone prominence (-1.0 = flatter, +1.0 = more prominent)"
                )
            
            # Natural range feedback
            cheek_intensity = abs(cheek_height) + abs(cheek_width) + abs(cheek_prominence)
            if cheek_intensity > 1.5:
                st.warning("⚠️ High modification intensity - may look unnatural")
            elif cheek_intensity > 0.8:
                st.info("ℹ️ Moderate modification - preview recommended")
            elif cheek_intensity > 0.1:
                st.success("✅ Natural modification range")
        
        # Overall surgery intensity feedback
        st.markdown("---")
        total_surgery_intensity = (
            abs(nose_height) + abs(nose_width) + abs(nose_tip) + abs(nose_bridge) +
            abs(eye_size) + abs(eye_shape) + abs(eye_position) + abs(eye_angle) +
            abs(jaw_width) + abs(jaw_angle) + abs(jaw_length) +
            abs(cheek_height) + abs(cheek_width) + abs(cheek_prominence)
        )
        
        # Display overall intensity meter
        st.markdown("#### 📊 Overall Surgery Intensity")
        intensity_percentage = min(100, (total_surgery_intensity / 6.0) * 100)
        
        if intensity_percentage > 70:
            st.error(f"🚨 Very High Intensity: {intensity_percentage:.1f}% - Results may look unnatural")
        elif intensity_percentage > 40:
            st.warning(f"⚠️ High Intensity: {intensity_percentage:.1f}% - Preview strongly recommended")
        elif intensity_percentage > 15:
            st.info(f"ℹ️ Moderate Intensity: {intensity_percentage:.1f}% - Natural range")
        elif intensity_percentage > 1:
            st.success(f"✅ Low Intensity: {intensity_percentage:.1f}% - Very natural")
        else:
            st.info("No modifications applied")
        
        # Control buttons
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✂️ Apply Surgery", key="apply_surgery", use_container_width=True):
                self._apply_surgery()
        
        with col2:
            if st.button("👁️ Preview", key="preview_surgery", use_container_width=True):
                self._preview_surgery()
        
        with col3:
            if st.button("🔄 Reset", key="reset_surgery", use_container_width=True):
                self._reset_surgery_controls()
        
        with col4:
            if st.button("📊 Validate", key="validate_surgery", use_container_width=True):
                self._validate_surgery_proportions()
        
        # Real-time preview handling
        if realtime_surgery_preview and self._get_session_value('current_image') is not None:
            # Check if any surgery control values changed
            if self._surgery_controls_changed():
                self._preview_surgery()    

    def _setup_utility_buttons(self):
        """Setup utility buttons"""
        st.sidebar.markdown("### 🔧 Utilities")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🔄 Reset Image", key="reset_image"):
                self._reset_image()
        
        with col2:
            if st.button("💾 Save Image", key="save_image"):
                self._save_current_image()
        
        # Apply integrated effects
        if st.sidebar.button("✨ Apply Integrated Effects", key="apply_integrated"):
            self._apply_integrated_effects()
        
        # View gallery
        if st.sidebar.button("🖼️ View Gallery", key="view_gallery"):
            self._show_gallery()
    
    def _setup_main_content(self):
        """Setup main content area"""
        # Image display area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📸 Result Image")
            
            current_image = self._get_session_value('current_image')
            if current_image is not None:
                # Face detection status display
                if self._get_session_value('face_landmarks'):
                    st.success("✅ Face detected")
                else:
                    st.warning("⚠️ Face not detected")
                
                # Display image
                st.image(
                    current_image,
                    caption="Current Image",
                    use_column_width=True
                )
                
                # Image information
                height, width = current_image.shape[:2]
                st.caption(f"Resolution: {width}x{height}")
            
            else:
                st.info("👆 Upload an image or start camera")
                self._show_usage_guide()
        
        with col2:
            st.markdown("### 📊 Processing Information")
            
            # Processing statistics
            processing_results = self._get_session_value('processing_results', [])
            if processing_results:
                latest_result = processing_results[-1]
                
                st.metric("Processing Time", f"{latest_result.get('processing_time', 0):.2f}s")
                st.metric("Quality Score", f"{latest_result.get('quality_score', 0):.2f}")
                st.metric("Applied Effects", len(latest_result.get('applied_effects', [])))
                
                # Applied effects list
                if latest_result.get('applied_effects'):
                    st.markdown("**Applied Effects:**")
                    for effect in latest_result['applied_effects']:
                        st.write(f"• {effect}")
            
            # Performance monitoring
            st.markdown("### ⚡ Performance Monitoring")
            
            # Real-time FPS (in camera mode)
            if self._get_session_value('camera_active'):
                fps_placeholder = st.empty()
                # FPS is handled in real-time updates
            
            # Memory usage (simple estimation)
            current_image = self._get_session_value('current_image')
            if current_image is not None:
                image_size = current_image.nbytes / (1024 * 1024)  # MB
                st.metric("Image Memory", f"{image_size:.1f} MB")    
 
    def _show_usage_guide(self):
        """Show usage guide"""
        st.markdown("---")
        st.markdown("## 📖 Usage Guide")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🚀 Getting Started
            1. **Upload Image** or **Start Camera**
            2. **Confirm Face Detection**
            3. **Adjust Makeup/Surgery** effects
            4. **Check Results** and **Save**
            """)
        
        with col2:
            st.markdown("""
            ### ✨ Key Features
            - 🎨 **Real-time Makeup** application
            - ✂️ **Surgery Simulation**
            - 📷 **Real-time Camera** support
            - 💾 **Result Saving** and **Gallery**
            """)
        
        st.markdown("---")
        st.markdown("### 🎯 Supported Effects")
        
        tab1, tab2 = st.tabs(["💄 Makeup", "✂️ Surgery"])
        
        with tab1:
            st.markdown("""
            - **Lipstick**: Various colors and intensity control
            - **Eyeshadow**: Multi-color gradients
            - **Blush**: Natural cheek touch
            - **Foundation**: Skin tone correction
            """)
        
        with tab2:
            st.markdown("""
            - **Nose Surgery**: Height, width adjustment
            - **Eye Surgery**: Size, shape adjustment
            - **Jawline Surgery**: Width, angle adjustment
            - **Cheekbone Surgery**: Position, size adjustment
            """)
    
    def _start_camera(self):
        """Start camera"""
        try:
            if not self._get_session_value('camera_active'):
                video_stream = VideoStream(source=0)
                video_stream.start()
                
                self._set_session_value('video_stream', video_stream)
                self._set_session_value('camera_active', True)
                
                st.sidebar.success("📹 Camera started!")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Camera start failed: {str(e)}")
    
    def _stop_camera(self):
        """Stop camera"""
        try:
            if self._get_session_value('camera_active') and self._get_session_value('video_stream'):
                video_stream = self._get_session_value('video_stream')
                video_stream.stop()
                self._set_session_value('video_stream', None)
                self._set_session_value('camera_active', False)
                
                st.sidebar.info("⏹️ Camera stopped")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Camera stop failed: {str(e)}")
    
    def _handle_camera_stream(self):
        """Handle real-time camera stream"""
        video_stream = self._get_session_value('video_stream')
        camera_active = self._get_session_value('camera_active')
        
        if not video_stream or not camera_active:
            return
        
        # Read frame
        frame = video_stream.read_frame()
        if frame is not None:
            # BGR to RGB conversion
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Update session state
            self._set_session_value('current_image', frame)
            
            # Face detection
            self._detect_face(frame)
            
            # Auto refresh (real-time effects)
            time.sleep(0.1)  # Frame rate control
            st.rerun()
    
    def _detect_face(self, image: np.ndarray):
        """Face detection and landmark extraction"""
        try:
            detection_result = self.face_engine.detect_face(image)
            
            if detection_result and detection_result.is_valid():
                self._set_session_value('face_landmarks', detection_result.landmarks)
            else:
                self._set_session_value('face_landmarks', None)
                
        except Exception as e:
            st.error(f"Face detection failed: {str(e)}")
            self._set_session_value('face_landmarks', None)    

    def _apply_makeup(self):
        """Apply makeup"""
        if self._get_session_value('current_image') is None:
            st.error("No image available. Please upload an image or start camera first.")
            return
        
        if not self._get_session_value('face_landmarks'):
            st.error("Face not detected.")
            return
        
        try:
            with st.spinner("Applying makeup..."):
                # Create makeup configuration
                makeup_config = self._create_makeup_config()
                
                # Apply makeup
                result = self.makeup_engine.apply_full_makeup(
                    self._get_session_value('current_image'),
                    self._get_session_value('face_landmarks'),
                    makeup_config
                )
                
                if result.is_successful():
                    self._set_session_value('current_image', result.image)
                    
                    # Save processing results
                    processing_results = self._get_session_value('processing_results', [])
                    processing_results.append({
                        'type': 'makeup',
                        'processing_time': result.processing_time,
                        'applied_effects': result.applied_effects,
                        'quality_score': 0.8  # Default value
                    })
                    self._set_session_value('processing_results', processing_results)
                    
                    st.success("✅ Makeup applied successfully!")
                    st.rerun()
                else:
                    st.error("❌ Makeup application failed.")
                    
        except Exception as e:
            st.error(f"Error during makeup application: {str(e)}")
    

    
    def _apply_integrated_effects(self):
        """Apply integrated effects"""
        if self._get_session_value('current_image') is None:
            st.error("No image available. Please upload an image or start camera first.")
            return
        
        if not self._get_session_value('face_landmarks'):
            st.error("Face not detected.")
            return
        
        try:
            with st.spinner("Applying integrated effects..."):
                # Create integrated configuration
                integrated_config = IntegratedConfig(
                    makeup_config=self._create_makeup_config(),
                    surgery_config=self._create_surgery_config(),
                    effect_priority=EffectPriority.SURGERY_FIRST,
                    enable_caching=True
                )
                
                # Apply integrated effects
                result = self.integrated_engine.apply_integrated_effects(
                    self._get_session_value('current_image'),
                    self._get_session_value('face_landmarks'),
                    integrated_config
                )
                
                if result.is_successful():
                    self._set_session_value('current_image', result.final_image)
                    self._set_session_value('face_landmarks', result.modified_landmarks)
                    
                    # Save processing results
                    processing_results = self._get_session_value('processing_results', [])
                    processing_results.append({
                        'type': 'integrated',
                        'processing_time': result.processing_time,
                        'applied_effects': result.applied_effects,
                        'quality_score': result.quality_score,
                        'conflicts_detected': result.conflicts_detected
                    })
                    self._set_session_value('processing_results', processing_results)
                    
                    st.success("✅ Integrated effects applied successfully!")
                    
                    # Conflict detection notification
                    if result.conflicts_detected:
                        st.warning(f"⚠️ Effect conflicts detected and automatically adjusted: {', '.join(result.conflicts_detected)}")
                    
                    st.rerun()
                else:
                    st.error("❌ Integrated effects application failed.")
                    
        except Exception as e:
            st.error(f"Error during integrated effects application: {str(e)}")    
 
    def _create_makeup_config(self) -> MakeupConfig:
        """Create makeup configuration from enhanced UI settings"""
        # Color conversion function
        def hex_to_color(hex_color: str) -> Color:
            hex_color = hex_color.lstrip('#')
            return Color(
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16)
            )
        
        # Blend mode conversion
        def get_blend_mode(mode_str: str):
            from models.makeup import BlendMode
            mode_map = {
                "Normal": BlendMode.NORMAL,
                "Multiply": BlendMode.MULTIPLY,
                "Overlay": BlendMode.OVERLAY,
                "Soft Light": BlendMode.SOFT_LIGHT
            }
            return mode_map.get(mode_str, BlendMode.NORMAL)
        
        # Eyeshadow style conversion
        def get_eyeshadow_style(style_str: str):
            style_map = {
                "Natural": EyeshadowStyle.NATURAL,
                "Smoky": EyeshadowStyle.SMOKY,
                "Cut Crease": EyeshadowStyle.CUT_CREASE,
                "Halo": EyeshadowStyle.HALO,
                "Gradient": EyeshadowStyle.GRADIENT
            }
            return style_map.get(style_str, EyeshadowStyle.NATURAL)
        
        # Get values from session state (supports both dictionary and object)
        def get_session_value(key: str, default):
            if hasattr(st.session_state, 'get'):
                return st.session_state.get(key, default)
            else:
                return getattr(st.session_state, key, default)
        
        # Enhanced Lipstick configuration
        lipstick_config = LipstickConfig(
            color=hex_to_color(get_session_value('lipstick_color', '#FF1493')),
            intensity=get_session_value('lipstick_intensity', 0.6),
            glossiness=get_session_value('lipstick_glossiness', 0.5),
            blend_mode=get_blend_mode(get_session_value('lipstick_blend_mode', 'Normal'))
        )
        
        # Enhanced Eyeshadow configuration with multiple colors
        eyeshadow_colors = [
            hex_to_color(get_session_value('eyeshadow_color1', '#800080')),
            hex_to_color(get_session_value('eyeshadow_color2', '#DDA0DD'))
        ]
        
        # Add third color if available
        third_color = get_session_value('eyeshadow_color3', None)
        if third_color:
            eyeshadow_colors.append(hex_to_color(third_color))
        
        eyeshadow_config = EyeshadowConfig(
            colors=eyeshadow_colors,
            style=get_eyeshadow_style(get_session_value('eyeshadow_style', 'Natural')),
            intensity=get_session_value('eyeshadow_intensity', 0.4),
            shimmer=get_session_value('eyeshadow_shimmer', 0.2)
        )
        
        # Enhanced Blush configuration with placement
        blush_config = BlushConfig(
            color=hex_to_color(get_session_value('blush_color', '#FFB6C1')),
            intensity=get_session_value('blush_intensity', 0.3),
            placement=get_session_value('blush_placement', 'Cheeks').lower()
        )
        
        # Enhanced Foundation configuration with finish
        foundation_config = FoundationConfig(
            color=hex_to_color(get_session_value('foundation_color', '#F5DEB3')),
            coverage=get_session_value('foundation_coverage', 0.3),
            finish=get_session_value('foundation_finish', 'Natural').lower()
        )
        
        # Enhanced Eyeliner configuration with style
        eyeliner_config = EyelinerConfig(
            color=hex_to_color(get_session_value('eyeliner_color', '#000000')),
            thickness=get_session_value('eyeliner_thickness', 0.5),
            intensity=get_session_value('eyeliner_intensity', 1.0),
            style=get_session_value('eyeliner_style', 'Natural').lower()
        )
        
        return MakeupConfig(
            lipstick=lipstick_config,
            eyeshadow=eyeshadow_config,
            blush=blush_config,
            foundation=foundation_config,
            eyeliner=eyeliner_config
        )
    

    
    def _preview_makeup(self):
        """Preview makeup without permanently applying"""
        if self._get_session_value('current_image') is None:
            st.error("No image available. Please upload an image or start camera first.")
            return
        
        if not self._get_session_value('face_landmarks'):
            st.error("Face not detected.")
            return
        
        try:
            # Create makeup configuration
            makeup_config = self._create_makeup_config()
            
            # Apply makeup to a copy of the original image
            original_image = self._get_session_value('original_image')
            if original_image is not None:
                result = self.makeup_engine.apply_full_makeup(
                    original_image.copy(),
                    self._get_session_value('face_landmarks'),
                    makeup_config
                )
                
                if result.is_successful():
                    # Update current image with preview
                    self._set_session_value('current_image', result.image)
                    st.rerun()
                else:
                    st.error("❌ Makeup preview failed.")
            else:
                st.error("Original image not available for preview.")
                
        except Exception as e:
            st.error(f"Error during makeup preview: {str(e)}")
    
    def _reset_makeup_controls(self):
        """Reset all makeup controls to default values"""
        try:
            # Reset to original image
            original_image = self._get_session_value('original_image')
            if original_image is not None:
                self._set_session_value('current_image', original_image.copy())
            
            # Reset all makeup control values to defaults
            makeup_defaults = {
                'lipstick_color': '#FF1493',
                'lipstick_intensity': 0.6,
                'lipstick_glossiness': 0.5,
                'lipstick_blend_mode': 'Normal',
                'lipstick_preset': 'Natural Pink',
                'eyeshadow_color1': '#800080',
                'eyeshadow_color2': '#DDA0DD',
                'eyeshadow_color3': '#F0E68C',
                'eyeshadow_intensity': 0.4,
                'eyeshadow_shimmer': 0.2,
                'eyeshadow_style': 'Natural',
                'blush_color': '#FFB6C1',
                'blush_intensity': 0.3,
                'blush_placement': 'Cheeks',
                'blush_preset': 'Natural Pink',
                'foundation_color': '#F5DEB3',
                'foundation_coverage': 0.3,
                'foundation_finish': 'Natural',
                'foundation_preset': 'Fair',
                'eyeliner_color': '#000000',
                'eyeliner_thickness': 0.5,
                'eyeliner_intensity': 1.0,
                'eyeliner_style': 'Natural',
                'realtime_preview': False
            }
            
            # Update session state with defaults
            for key, value in makeup_defaults.items():
                self._set_session_value(key, value)
            
            st.success("✅ Makeup controls reset to defaults!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error resetting makeup controls: {str(e)}")
    
    def _makeup_controls_changed(self) -> bool:
        """Check if makeup control values have changed since last application"""
        try:
            # Get current makeup config
            current_config = self._create_makeup_config()
            
            # Get stored config from session
            stored_config = self._get_session_value('makeup_config')
            
            if stored_config is None:
                # First time, consider it changed
                self._set_session_value('makeup_config', current_config)
                return True
            
            # Compare configurations
            if (current_config.lipstick.color != stored_config.lipstick.color or
                current_config.lipstick.intensity != stored_config.lipstick.intensity or
                current_config.lipstick.glossiness != stored_config.lipstick.glossiness or
                current_config.eyeshadow.colors != stored_config.eyeshadow.colors or
                current_config.eyeshadow.intensity != stored_config.eyeshadow.intensity or
                current_config.blush.color != stored_config.blush.color or
                current_config.blush.intensity != stored_config.blush.intensity or
                current_config.foundation.color != stored_config.foundation.color or
                current_config.foundation.coverage != stored_config.foundation.coverage or
                current_config.eyeliner.color != stored_config.eyeliner.color or
                current_config.eyeliner.thickness != stored_config.eyeliner.thickness or
                current_config.eyeliner.intensity != stored_config.eyeliner.intensity):
                
                # Update stored config
                self._set_session_value('makeup_config', current_config)
                return True
            
            return False
            
        except Exception as e:
            # If there's an error, assume changes were made
            return True
    
    def _reset_image(self):
        """Reset image to original"""
        try:
            original_image = self._get_session_value('original_image')
            if original_image is not None:
                self._set_session_value('current_image', original_image.copy())
                st.success("✅ Image reset to original!")
                st.rerun()
            else:
                st.error("No original image available.")
        except Exception as e:
            st.error(f"Error resetting image: {str(e)}")
    
    def _save_current_image(self):
        """Save current image"""
        try:
            current_image = self._get_session_value('current_image')
            if current_image is not None:
                # Create metadata
                from utils.image_processor import ImageMetadata
                metadata = ImageMetadata(
                    timestamp=time.time(),
                    effects_applied=self._get_processing_effects(),
                    quality_score=0.8,
                    original_size=current_image.shape[:2]
                )
                
                # Save image
                saved_path = self.image_processor.save_result(current_image, metadata)
                st.success(f"✅ Image saved: {saved_path}")
            else:
                st.error("No image to save.")
        except Exception as e:
            st.error(f"Error saving image: {str(e)}")
    
    def _get_processing_effects(self) -> List[str]:
        """Get list of currently applied effects"""
        effects = []
        
        # Check makeup effects
        if self._get_session_value('lipstick_intensity', 0) > 0:
            effects.append("Lipstick")
        if self._get_session_value('eyeshadow_intensity', 0) > 0:
            effects.append("Eyeshadow")
        if self._get_session_value('blush_intensity', 0) > 0:
            effects.append("Blush")
        if self._get_session_value('foundation_coverage', 0) > 0:
            effects.append("Foundation")
        if self._get_session_value('eyeliner_intensity', 0) > 0:
            effects.append("Eyeliner")
        
        # Check surgery effects
        if abs(self._get_session_value('nose_height', 0)) > 0.1 or abs(self._get_session_value('nose_width', 0)) > 0.1:
            effects.append("Nose Surgery")
        if abs(self._get_session_value('eye_size', 0)) > 0.1 or abs(self._get_session_value('eye_shape', 0)) > 0.1:
            effects.append("Eye Surgery")
        if abs(self._get_session_value('jaw_width', 0)) > 0.1 or abs(self._get_session_value('jaw_angle', 0)) > 0.1:
            effects.append("Jawline Surgery")
        if abs(self._get_session_value('cheek_height', 0)) > 0.1 or abs(self._get_session_value('cheek_width', 0)) > 0.1:
            effects.append("Cheekbone Surgery")
        
        return effects
    
    def _show_gallery(self):
        """Show image gallery"""
        try:
            st.markdown("### 🖼️ Image Gallery")
            
            # Get saved images
            gallery_images = self.image_gallery.get_all_images()
            
            if gallery_images:
                # Display images in grid
                cols = st.columns(3)
                for i, (image_path, metadata) in enumerate(gallery_images):
                    with cols[i % 3]:
                        # Load and display thumbnail
                        thumbnail = self.image_gallery.get_thumbnail(image_path)
                        if thumbnail is not None:
                            st.image(thumbnail, caption=f"Saved {metadata.get('timestamp', 'Unknown')}")
                            
                            # Load full image button
                            if st.button(f"Load", key=f"load_image_{i}"):
                                full_image = self.image_gallery.load_image(image_path)
                                if full_image is not None:
                                    self._set_session_value('current_image', full_image)
                                    self._set_session_value('original_image', full_image.copy())
                                    self._detect_face(full_image)
                                    st.success("✅ Image loaded from gallery!")
                                    st.rerun()
            else:
                st.info("No saved images in gallery.")
                
        except Exception as e:
            st.error(f"Error displaying gallery: {str(e)}")