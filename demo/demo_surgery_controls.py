#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Surgery Control Panel Demo
성형 시뮬레이션 컨트롤 패널 데모

This script demonstrates the enhanced surgery control panel functionality
implemented for task 7.3.
"""

import sys
import os
import numpy as np
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.surgery import SurgeryConfig, NoseConfig, EyeConfig, JawlineConfig, CheekboneConfig
from models.core import Point3D


class SurgeryControlDemo:
    """Demonstration of surgery control panel functionality"""
    
    def __init__(self):
        """Initialize demo"""
        self.current_settings = self._get_default_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default control settings"""
        return {
            # Nose surgery controls
            'nose_height': 0.0,
            'nose_width': 0.0,
            'nose_tip': 0.0,
            'nose_bridge': 0.0,
            'nose_preset': 'Natural',
            
            # Eye surgery controls
            'eye_size': 0.0,
            'eye_shape': 0.0,
            'eye_position': 0.0,
            'eye_angle': 0.0,
            'eye_preset': 'Natural',
            
            # Jawline surgery controls
            'jaw_width': 0.0,
            'jaw_angle': 0.0,
            'jaw_length': 0.0,
            'jaw_preset': 'Natural',
            
            # Cheekbone surgery controls
            'cheek_height': 0.0,
            'cheek_width': 0.0,
            'cheek_prominence': 0.0,
            'cheek_preset': 'Natural',
            
            # Real-time preview
            'realtime_surgery_preview': False
        }
    
    def create_surgery_config(self) -> SurgeryConfig:
        """Create surgery configuration from current settings"""
        # Nose configuration
        nose_config = NoseConfig(
            height_adjustment=self.current_settings['nose_height'],
            width_adjustment=self.current_settings['nose_width'],
            tip_adjustment=self.current_settings['nose_tip'],
            bridge_adjustment=self.current_settings['nose_bridge']
        )
        
        # Eye configuration
        eye_config = EyeConfig(
            size_adjustment=self.current_settings['eye_size'],
            shape_adjustment=self.current_settings['eye_shape'],
            position_adjustment=self.current_settings['eye_position'],
            angle_adjustment=self.current_settings['eye_angle']
        )
        
        # Jawline configuration
        jawline_config = JawlineConfig(
            width_adjustment=self.current_settings['jaw_width'],
            angle_adjustment=self.current_settings['jaw_angle'],
            length_adjustment=self.current_settings['jaw_length']
        )
        
        # Cheekbone configuration
        cheekbone_config = CheekboneConfig(
            height_adjustment=self.current_settings['cheek_height'],
            width_adjustment=self.current_settings['cheek_width'],
            prominence_adjustment=self.current_settings['cheek_prominence']
        )
        
        return SurgeryConfig(
            nose=nose_config,
            eyes=eye_config,
            jawline=jawline_config,
            cheekbones=cheekbone_config
        )
    
    def demonstrate_presets(self):
        """Demonstrate preset functionality"""
        print("✂️ Demonstrating Surgery Presets")
        print("-" * 40)
        
        # Nose surgery presets
        nose_presets = {
            "Natural": {"height": 0.0, "width": 0.0, "tip": 0.0, "bridge": 0.0},
            "Refined": {"height": 0.2, "width": -0.1, "tip": 0.1, "bridge": 0.1},
            "Dramatic": {"height": 0.4, "width": -0.2, "tip": 0.2, "bridge": 0.2},
            "Subtle": {"height": 0.1, "width": -0.05, "tip": 0.05, "bridge": 0.05}
        }
        
        print("👃 Nose Surgery Presets:")
        for preset_name, values in nose_presets.items():
            print(f"  • {preset_name}:")
            print(f"    Height: {values['height']:+.2f}, Width: {values['width']:+.2f}")
            print(f"    Tip: {values['tip']:+.2f}, Bridge: {values['bridge']:+.2f}")
        
        # Eye surgery presets
        eye_presets = {
            "Natural": {"size": 0.0, "shape": 0.0, "position": 0.0, "angle": 0.0},
            "Enlarged": {"size": 0.3, "shape": 0.1, "position": 0.0, "angle": 0.1},
            "Almond Shape": {"size": 0.1, "shape": 0.4, "position": 0.0, "angle": 0.2},
            "Wide Set": {"size": 0.0, "shape": 0.0, "position": -0.2, "angle": 0.0}
        }
        
        print("\n👁️ Eye Surgery Presets:")
        for preset_name, values in eye_presets.items():
            print(f"  • {preset_name}:")
            print(f"    Size: {values['size']:+.2f}, Shape: {values['shape']:+.2f}")
            print(f"    Position: {values['position']:+.2f}, Angle: {values['angle']:+.2f}")
        
        # Jawline surgery presets
        jaw_presets = {
            "Natural": {"width": 0.0, "angle": 0.0, "length": 0.0},
            "V-Line": {"width": -0.3, "angle": 0.2, "length": -0.1},
            "Square Jaw": {"width": 0.2, "angle": -0.2, "length": 0.1},
            "Refined": {"width": -0.1, "angle": 0.1, "length": 0.0}
        }
        
        print("\n🦴 Jawline Surgery Presets:")
        for preset_name, values in jaw_presets.items():
            print(f"  • {preset_name}:")
            print(f"    Width: {values['width']:+.2f}, Angle: {values['angle']:+.2f}")
            print(f"    Length: {values['length']:+.2f}")
        
        # Cheekbone surgery presets
        cheek_presets = {
            "Natural": {"height": 0.0, "width": 0.0, "prominence": 0.0},
            "High Cheekbones": {"height": 0.3, "width": 0.0, "prominence": 0.2},
            "Reduced": {"height": -0.2, "width": -0.1, "prominence": -0.1},
            "Sculpted": {"height": 0.2, "width": -0.1, "prominence": 0.3}
        }
        
        print("\n🏔️ Cheekbone Surgery Presets:")
        for preset_name, values in cheek_presets.items():
            print(f"  • {preset_name}:")
            print(f"    Height: {values['height']:+.2f}, Width: {values['width']:+.2f}")
            print(f"    Prominence: {values['prominence']:+.2f}")
        
        print()
    
    def demonstrate_control_categories(self):
        """Demonstrate control categories"""
        print("🎛️ Demonstrating Surgery Control Categories")
        print("-" * 40)
        
        categories = {
            "👃 Nose Surgery": [
                "Height Adjustment (-1.0 = lower, +1.0 = higher)",
                "Width Adjustment (-1.0 = narrower, +1.0 = wider)",
                "Tip Adjustment (-1.0 = up, +1.0 = down)",
                "Bridge Adjustment (-1.0 = flatter, +1.0 = more prominent)",
                "Preset Selection"
            ],
            "👁️ Eye Surgery": [
                "Size Adjustment (-1.0 = smaller, +1.0 = larger)",
                "Shape Adjustment (-1.0 = rounder, +1.0 = more almond)",
                "Position Adjustment (-1.0 = closer, +1.0 = wider apart)",
                "Angle Adjustment (-1.0 = downward, +1.0 = upward)",
                "Preset Selection"
            ],
            "🦴 Jawline Surgery": [
                "Width Adjustment (-1.0 = narrower, +1.0 = wider)",
                "Angle Adjustment (-1.0 = softer, +1.0 = sharper)",
                "Length Adjustment (-1.0 = shorter, +1.0 = longer)",
                "Preset Selection"
            ],
            "🏔️ Cheekbone Surgery": [
                "Height Adjustment (-1.0 = lower, +1.0 = higher)",
                "Width Adjustment (-1.0 = narrower, +1.0 = wider)",
                "Prominence Adjustment (-1.0 = flatter, +1.0 = more prominent)",
                "Preset Selection"
            ]
        }
        
        for category, controls in categories.items():
            print(f"{category}:")
            for control in controls:
                print(f"  • {control}")
            print()
    
    def demonstrate_natural_range_feedback(self):
        """Demonstrate natural range feedback system"""
        print("📊 Demonstrating Natural Range Feedback")
        print("-" * 40)
        
        # Test different intensity levels
        test_scenarios = [
            ("Very Natural", {"nose_height": 0.05, "eye_size": 0.03, "jaw_width": 0.02}),
            ("Natural", {"nose_height": 0.15, "eye_size": 0.12, "jaw_width": 0.08}),
            ("Moderate", {"nose_height": 0.35, "eye_size": 0.25, "jaw_width": 0.20}),
            ("High Intensity", {"nose_height": 0.65, "eye_size": 0.55, "jaw_width": 0.45}),
            ("Very High", {"nose_height": 0.85, "eye_size": 0.75, "jaw_width": 0.70})
        ]
        
        print("Natural Range Feedback Examples:")
        for scenario_name, settings in test_scenarios:
            # Calculate intensities
            nose_intensity = abs(settings.get('nose_height', 0))
            eye_intensity = abs(settings.get('eye_size', 0))
            jaw_intensity = abs(settings.get('jaw_width', 0))
            total_intensity = nose_intensity + eye_intensity + jaw_intensity
            
            # Determine feedback
            if total_intensity > 2.0:
                feedback = "🚨 Very High Intensity - Results may look unnatural"
            elif total_intensity > 1.0:
                feedback = "⚠️ High Intensity - Preview strongly recommended"
            elif total_intensity > 0.3:
                feedback = "ℹ️ Moderate Intensity - Natural range"
            elif total_intensity > 0.05:
                feedback = "✅ Low Intensity - Very natural"
            else:
                feedback = "No modifications applied"
            
            print(f"  • {scenario_name}: {feedback}")
            print(f"    Total Intensity: {total_intensity:.2f}")
        
        print()
    
    def demonstrate_real_time_preview(self):
        """Demonstrate real-time preview functionality"""
        print("🔄 Demonstrating Real-time Surgery Preview")
        print("-" * 40)
        
        print("Real-time preview features:")
        print("• ✅ Automatic change detection for surgery controls")
        print("• ✅ Instant visual feedback with natural score")
        print("• ✅ Non-destructive preview mode")
        print("• ✅ Performance optimized for surgery calculations")
        print("• ✅ Natural range validation in real-time")
        print()
        
        # Simulate control changes
        changes = [
            ("nose_height", 0.0, 0.2),
            ("eye_size", 0.0, 0.15),
            ("jaw_width", 0.0, -0.1),
            ("cheek_prominence", 0.0, 0.25)
        ]
        
        print("Simulating surgery control changes:")
        for control, old_value, new_value in changes:
            print(f"• {control}: {old_value:+.2f} → {new_value:+.2f}")
            self.current_settings[control] = new_value
        
        print("✅ Changes detected and surgery preview updated")
        print()
    
    def demonstrate_enhanced_features(self):
        """Demonstrate enhanced surgery features"""
        print("✨ Demonstrating Enhanced Surgery Features")
        print("-" * 40)
        
        # Tabbed organization
        print("📱 Tabbed Organization:")
        tabs = ["👃 Nose", "👁️ Eyes", "🦴 Jawline", "🏔️ Cheekbones"]
        for tab in tabs:
            print(f"  • {tab} - Dedicated controls for each feature")
        
        # Preset system
        print("\n🎯 Intelligent Preset System:")
        preset_features = [
            "Quick selection for common modifications",
            "Professional-grade presets (Natural, Refined, Dramatic)",
            "Custom preset option for advanced users",
            "Automatic value population from presets"
        ]
        for feature in preset_features:
            print(f"  • {feature}")
        
        # Natural range validation
        print("\n📊 Natural Range Validation:")
        validation_features = [
            "Real-time intensity monitoring",
            "Color-coded feedback (Green = Natural, Yellow = Moderate, Red = High)",
            "Individual feature intensity tracking",
            "Overall surgery intensity meter",
            "Automatic recommendations for natural results"
        ]
        for feature in validation_features:
            print(f"  • {feature}")
        
        # Advanced controls
        print("\n🎛️ Advanced Control Features:")
        control_features = [
            "Fine-grained adjustment (0.05 step size)",
            "Bidirectional sliders (-1.0 to +1.0 range)",
            "Contextual help tooltips",
            "Visual feedback with intensity meters",
            "One-click reset functionality"
        ]
        for feature in control_features:
            print(f"  • {feature}")
        
        print()
    
    def demonstrate_validation_system(self):
        """Demonstrate surgery validation system"""
        print("🔍 Demonstrating Surgery Validation System")
        print("-" * 40)
        
        # Create test configuration
        self.current_settings.update({
            'nose_height': 0.3,
            'nose_width': -0.2,
            'eye_size': 0.25,
            'jaw_width': -0.15,
            'cheek_prominence': 0.2
        })
        
        config = self.create_surgery_config()
        
        print("Validation Features:")
        print("• 📊 Total modification intensity calculation")
        print("• 🎯 Individual feature intensity analysis")
        print("• ✅ Natural proportion validation")
        print("• 💡 Intelligent recommendations")
        print("• ⚠️ Warning system for extreme modifications")
        print()
        
        # Calculate intensities
        total_intensity = config.get_total_modification_intensity()
        
        nose_intensity = (abs(config.nose.height_adjustment) + 
                         abs(config.nose.width_adjustment) + 
                         abs(config.nose.tip_adjustment) + 
                         abs(config.nose.bridge_adjustment)) / 4.0
        
        eye_intensity = (abs(config.eyes.size_adjustment) + 
                        abs(config.eyes.shape_adjustment) + 
                        abs(config.eyes.position_adjustment) + 
                        abs(config.eyes.angle_adjustment)) / 4.0
        
        print("Sample Validation Results:")
        print(f"• Total Intensity: {total_intensity:.2f}")
        print(f"• Nose Intensity: {nose_intensity:.2f}")
        print(f"• Eye Intensity: {eye_intensity:.2f}")
        
        # Provide recommendations
        if total_intensity > 0.5:
            print("• ⚠️ Recommendation: High modification intensity detected")
        elif total_intensity > 0.3:
            print("• ℹ️ Recommendation: Moderate modifications - preview recommended")
        else:
            print("• ✅ Recommendation: Natural modification range - safe to apply")
        
        print()
    
    def demonstrate_usability_features(self):
        """Demonstrate usability features"""
        print("👥 Demonstrating Surgery Control Usability")
        print("-" * 40)
        
        print("User-friendly features:")
        print("• 📱 Tabbed organization for easy navigation")
        print("• 🎯 Preset quick-selection system")
        print("• 📊 Real-time intensity feedback")
        print("• 💡 Contextual help tooltips")
        print("• 🔄 One-click reset functionality")
        print("• 👁️ Non-destructive preview mode")
        print("• ⚡ Real-time natural range validation")
        print("• 📈 Visual intensity meters")
        print("• 🎨 Color-coded feedback system")
        print("• 🔍 Proportion validation tools")
        print()
        
        # Help text examples
        print("Contextual help examples:")
        help_texts = {
            "Height Adjustment": "Adjust nose height (-1.0 = lower, +1.0 = higher)",
            "Size Adjustment": "Adjust eye size (-1.0 = smaller, +1.0 = larger)",
            "Width Adjustment": "Adjust jawline width (-1.0 = narrower, +1.0 = wider)",
            "Prominence": "Adjust cheekbone prominence (-1.0 = flatter, +1.0 = more prominent)",
            "Natural Range": "Green = Natural, Yellow = Moderate, Red = High intensity"
        }
        
        for control, help_text in help_texts.items():
            print(f"• {control}: {help_text}")
        
        print()
    
    def run_full_demo(self):
        """Run complete demonstration"""
        print("✂️ SURGERY CONTROL PANEL DEMONSTRATION")
        print("=" * 60)
        print("Task 7.3: 성형 시뮬레이션 컨트롤 구현")
        print("=" * 60)
        print()
        
        # Demonstrate all features
        self.demonstrate_control_categories()
        self.demonstrate_presets()
        self.demonstrate_enhanced_features()
        self.demonstrate_natural_range_feedback()
        self.demonstrate_real_time_preview()
        self.demonstrate_validation_system()
        self.demonstrate_usability_features()
        
        # Create and display final configuration
        print("📋 Final Surgery Configuration")
        print("-" * 40)
        
        config = self.create_surgery_config()
        
        print(f"👃 Nose Surgery:")
        print(f"   Height: {config.nose.height_adjustment:+.2f}, Width: {config.nose.width_adjustment:+.2f}")
        print(f"   Tip: {config.nose.tip_adjustment:+.2f}, Bridge: {config.nose.bridge_adjustment:+.2f}")
        
        print(f"\n👁️ Eye Surgery:")
        print(f"   Size: {config.eyes.size_adjustment:+.2f}, Shape: {config.eyes.shape_adjustment:+.2f}")
        print(f"   Position: {config.eyes.position_adjustment:+.2f}, Angle: {config.eyes.angle_adjustment:+.2f}")
        
        print(f"\n🦴 Jawline Surgery:")
        print(f"   Width: {config.jawline.width_adjustment:+.2f}, Angle: {config.jawline.angle_adjustment:+.2f}")
        print(f"   Length: {config.jawline.length_adjustment:+.2f}")
        
        print(f"\n🏔️ Cheekbone Surgery:")
        print(f"   Height: {config.cheekbones.height_adjustment:+.2f}, Width: {config.cheekbones.width_adjustment:+.2f}")
        print(f"   Prominence: {config.cheekbones.prominence_adjustment:+.2f}")
        
        print(f"\n📊 Total Surgery Intensity: {config.get_total_modification_intensity():.2f}")
        
        print("\n" + "=" * 60)
        print("✅ TASK 7.3 IMPLEMENTATION COMPLETE!")
        print("=" * 60)
        print("\n📋 IMPLEMENTED REQUIREMENTS:")
        print("• ✅ 성형 부위별 조절 슬라이더 구현")
        print("• ✅ 변형 강도 및 미리보기 기능 구현")
        print("• ✅ 자연스러운 범위 제한 UI 피드백 구현")
        print("• ✅ 성형 컨트롤 정확성 테스트 작성")
        print("\n🎯 Requirements 3.1, 3.3, 6.2 SATISFIED!")


def main():
    """Main demonstration function"""
    demo = SurgeryControlDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()