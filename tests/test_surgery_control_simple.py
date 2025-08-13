#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Surgery Control Tests
간단한 성형 컨트롤 테스트

This script provides simple tests for surgery control functionality
to verify basic operations work correctly.
"""

import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.surgery import SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig
from models.core import Point3D


def test_surgery_config_creation():
    """Test basic surgery configuration creation"""
    print("🧪 Testing Surgery Configuration Creation...")
    
    try:
        # Create individual configs
        nose_config = NoseConfig(
            height_adjustment=0.2,
            width_adjustment=-0.1,
            tip_adjustment=0.1,
            bridge_adjustment=0.05
        )
        
        eye_config = EyeConfig(
            size_adjustment=0.15,
            shape_adjustment=0.1,
            position_adjustment=-0.05,
            angle_adjustment=0.08
        )
        
        jawline_config = JawlineConfig(
            width_adjustment=-0.15,
            angle_adjustment=0.12,
            length_adjustment=-0.03
        )
        
        cheekbone_config = CheekboneConfig(
            height_adjustment=0.18,
            width_adjustment=-0.08,
            prominence_adjustment=0.15
        )
        
        # Create full surgery config
        surgery_config = SurgeryConfig(
            nose=nose_config,
            eyes=eye_config,
            jawline=jawline_config,
            cheekbones=cheekbone_config
        )
        
        print("✅ Surgery configuration created successfully")
        
        # Test intensity calculation
        total_intensity = surgery_config.get_total_modification_intensity()
        print(f"📊 Total modification intensity: {total_intensity:.3f}")
        
        # Verify individual components
        assert isinstance(surgery_config.nose, NoseConfig)
        assert isinstance(surgery_config.eyes, EyeConfig)
        assert isinstance(surgery_config.jawline, JawlineConfig)
        assert isinstance(surgery_config.cheekbones, CheekboneConfig)
        
        print("✅ All surgery config components verified")
        return True
        
    except Exception as e:
        print(f"❌ Surgery config creation failed: {e}")
        return False


def test_surgery_control_ranges():
    """Test surgery control value ranges"""
    print("\n🧪 Testing Surgery Control Ranges...")
    
    try:
        # Test valid ranges
        valid_values = [-1.0, -0.5, 0.0, 0.5, 1.0]
        
        for value in valid_values:
            nose_config = NoseConfig(height_adjustment=value)
            assert -1.0 <= nose_config.height_adjustment <= 1.0
            
            eye_config = EyeConfig(size_adjustment=value)
            assert -1.0 <= eye_config.size_adjustment <= 1.0
        
        print("✅ Valid range tests passed")
        
        # Test invalid ranges (should raise ValueError)
        invalid_values = [-1.1, 1.1, -2.0, 2.0]
        
        for value in invalid_values:
            try:
                NoseConfig(height_adjustment=value)
                print(f"❌ Should have failed for value: {value}")
                return False
            except ValueError:
                pass  # Expected behavior
        
        print("✅ Invalid range validation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Range testing failed: {e}")
        return False


def test_surgery_presets():
    """Test surgery preset functionality"""
    print("\n🧪 Testing Surgery Presets...")
    
    try:
        # Define test presets
        nose_presets = {
            "Natural": {"height": 0.0, "width": 0.0, "tip": 0.0, "bridge": 0.0},
            "Refined": {"height": 0.2, "width": -0.1, "tip": 0.1, "bridge": 0.1},
            "Dramatic": {"height": 0.4, "width": -0.2, "tip": 0.2, "bridge": 0.2},
            "Subtle": {"height": 0.1, "width": -0.05, "tip": 0.05, "bridge": 0.05}
        }
        
        eye_presets = {
            "Natural": {"size": 0.0, "shape": 0.0, "position": 0.0, "angle": 0.0},
            "Enlarged": {"size": 0.3, "shape": 0.1, "position": 0.0, "angle": 0.1},
            "Almond Shape": {"size": 0.1, "shape": 0.4, "position": 0.0, "angle": 0.2},
            "Wide Set": {"size": 0.0, "shape": 0.0, "position": -0.2, "angle": 0.0}
        }
        
        # Test nose presets
        for preset_name, values in nose_presets.items():
            config = NoseConfig(
                height_adjustment=values["height"],
                width_adjustment=values["width"],
                tip_adjustment=values["tip"],
                bridge_adjustment=values["bridge"]
            )
            
            # Verify all values are within range
            assert -1.0 <= config.height_adjustment <= 1.0
            assert -1.0 <= config.width_adjustment <= 1.0
            assert -1.0 <= config.tip_adjustment <= 1.0
            assert -1.0 <= config.bridge_adjustment <= 1.0
        
        print(f"✅ {len(nose_presets)} nose presets tested successfully")
        
        # Test eye presets
        for preset_name, values in eye_presets.items():
            config = EyeConfig(
                size_adjustment=values["size"],
                shape_adjustment=values["shape"],
                position_adjustment=values["position"],
                angle_adjustment=values["angle"]
            )
            
            # Verify all values are within range
            assert -1.0 <= config.size_adjustment <= 1.0
            assert -1.0 <= config.shape_adjustment <= 1.0
            assert -1.0 <= config.position_adjustment <= 1.0
            assert -1.0 <= config.angle_adjustment <= 1.0
        
        print(f"✅ {len(eye_presets)} eye presets tested successfully")
        return True
        
    except Exception as e:
        print(f"❌ Preset testing failed: {e}")
        return False


def test_natural_range_feedback():
    """Test natural range feedback system"""
    print("\n🧪 Testing Natural Range Feedback...")
    
    try:
        # Test different intensity levels
        test_cases = [
            # (config_values, expected_category)
            ({"nose_height": 0.02, "eye_size": 0.01}, "very_natural"),
            ({"nose_height": 0.06, "eye_size": 0.04}, "natural"),
            ({"nose_height": 0.12, "eye_size": 0.08}, "moderate"),
            ({"nose_height": 0.30, "eye_size": 0.20}, "high"),
            ({"nose_height": 0.50, "eye_size": 0.40}, "very_high")
        ]
        
        for values, expected_category in test_cases:
            # Create configuration
            config = SurgeryConfig(
                nose=NoseConfig(height_adjustment=values.get("nose_height", 0.0)),
                eyes=EyeConfig(size_adjustment=values.get("eye_size", 0.0)),
                jawline=JawlineConfig(),
                cheekbones=CheekboneConfig()
            )
            
            # Calculate intensity
            intensity = config.get_total_modification_intensity()
            
            # Verify feedback category
            if expected_category == "very_natural":
                assert intensity <= 0.01, f"Expected very natural, got intensity: {intensity}"
            elif expected_category == "natural":
                assert 0.01 < intensity <= 0.02, f"Expected natural, got intensity: {intensity}"
            elif expected_category == "moderate":
                assert 0.02 < intensity <= 0.04, f"Expected moderate, got intensity: {intensity}"
            elif expected_category == "high":
                assert 0.04 < intensity <= 0.35, f"Expected high, got intensity: {intensity}"
            elif expected_category == "very_high":
                assert intensity > 0.10, f"Expected very high, got intensity: {intensity}"
            
            print(f"✅ {expected_category.replace('_', ' ').title()}: {intensity:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Natural range feedback testing failed: {e}")
        return False


def test_surgery_intensity_calculation():
    """Test surgery intensity calculation accuracy"""
    print("\n🧪 Testing Surgery Intensity Calculation...")
    
    try:
        # Test case 1: All zero values
        config1 = SurgeryConfig(
            nose=NoseConfig(),
            eyes=EyeConfig(),
            jawline=JawlineConfig(),
            cheekbones=CheekboneConfig()
        )
        intensity1 = config1.get_total_modification_intensity()
        assert intensity1 == 0.0, f"Expected 0.0, got {intensity1}"
        print("✅ Zero intensity test passed")
        
        # Test case 2: Maximum values
        config2 = SurgeryConfig(
            nose=NoseConfig(height_adjustment=1.0, width_adjustment=1.0),
            eyes=EyeConfig(size_adjustment=1.0, shape_adjustment=1.0),
            jawline=JawlineConfig(width_adjustment=1.0, angle_adjustment=1.0),
            cheekbones=CheekboneConfig(height_adjustment=1.0, width_adjustment=1.0)
        )
        intensity2 = config2.get_total_modification_intensity()
        assert intensity2 == 1.0, f"Expected 1.0, got {intensity2}"
        print("✅ Maximum intensity test passed")
        
        # Test case 3: Mixed values
        config3 = SurgeryConfig(
            nose=NoseConfig(height_adjustment=0.5, width_adjustment=-0.3),
            eyes=EyeConfig(size_adjustment=-0.2, shape_adjustment=0.4),
            jawline=JawlineConfig(width_adjustment=0.1, angle_adjustment=-0.6),
            cheekbones=CheekboneConfig(height_adjustment=-0.1, width_adjustment=0.2)
        )
        intensity3 = config3.get_total_modification_intensity()
        expected_intensity = (0.5 + 0.3 + 0.2 + 0.4 + 0.1 + 0.6 + 0.1 + 0.2) / 8.0
        assert abs(intensity3 - expected_intensity) < 0.001, f"Expected {expected_intensity}, got {intensity3}"
        print(f"✅ Mixed values test passed: {intensity3:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Intensity calculation testing failed: {e}")
        return False


def run_simple_surgery_tests():
    """Run all simple surgery control tests"""
    print("🎯 SIMPLE SURGERY CONTROL TESTS")
    print("=" * 50)
    
    tests = [
        test_surgery_config_creation,
        test_surgery_control_ranges,
        test_surgery_presets,
        test_natural_range_feedback,
        test_surgery_intensity_calculation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print()  # Add spacing after failed test
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Surgery control implementation is working correctly!")
    else:
        print(f"❌ {total - passed} test(s) failed")
        print("\n🔧 Please check the failed tests and fix any issues.")
    
    return passed == total


if __name__ == "__main__":
    success = run_simple_surgery_tests()
    
    if success:
        print("\n🚀 Ready to proceed with surgery control implementation!")
    else:
        print("\n⚠️ Please resolve test failures before proceeding.")
    
    sys.exit(0 if success else 1)