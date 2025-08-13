import sys
import traceback

print("Starting import test...")

try:
    print("Importing streamlit...")
    import streamlit as st
    print("Streamlit imported successfully")
    
    print("Importing other dependencies...")
    import cv2
    import numpy as np
    import time
    from typing import Optional, List, Dict, Any
    from PIL import Image
    import io
    import base64
    print("Basic dependencies imported successfully")
    
    print("Importing project modules...")
    sys.path.append('.')
    
    try:
        from engines.face_engine import MediaPipeFaceEngine, VideoStream
        print("Face engine imported successfully")
    except Exception as e:
        print(f"Face engine import error: {e}")
        
    try:
        from engines.makeup_engine import RealtimeMakeupEngine
        print("Makeup engine imported successfully")
    except Exception as e:
        print(f"Makeup engine import error: {e}")
        
    try:
        from engines.surgery_engine import RealtimeSurgeryEngine
        print("Surgery engine imported successfully")
    except Exception as e:
        print(f"Surgery engine import error: {e}")
        
    try:
        from engines.integrated_engine import IntegratedEngine, IntegratedConfig, EffectPriority
        print("Integrated engine imported successfully")
    except Exception as e:
        print(f"Integrated engine import error: {e}")
        
    try:
        from models.core import Point3D, Color
        print("Core models imported successfully")
    except Exception as e:
        print(f"Core models import error: {e}")
        
    try:
        from models.makeup import MakeupConfig, LipstickConfig, EyeshadowConfig, BlushConfig, FoundationConfig, EyelinerConfig, EyeshadowStyle
        print("Makeup models imported successfully")
    except Exception as e:
        print(f"Makeup models import error: {e}")
        
    try:
        from models.surgery import SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig
        print("Surgery models imported successfully")
    except Exception as e:
        print(f"Surgery models import error: {e}")
        
    try:
        from utils.image_processor import ImageProcessor
        print("Image processor imported successfully")
    except Exception as e:
        print(f"Image processor import error: {e}")
        
    try:
        from utils.image_gallery import ImageGallery
        print("Image gallery imported successfully")
    except Exception as e:
        print(f"Image gallery import error: {e}")
    
    print("All dependencies imported successfully")
    
    print("Now trying to import main interface...")
    import ui.main_interface
    print("Main interface module imported")
    print("Module contents:", dir(ui.main_interface))
    
except Exception as e:
    print(f"Import error: {e}")
    traceback.print_exc()