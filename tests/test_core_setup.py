"""
핵심 인터페이스 및 데이터 모델 테스트
"""
import sys
import traceback

def test_imports():
    """모든 핵심 모듈 임포트 테스트"""
    try:
        # 데이터 모델 임포트 테스트
        from models import (
            Point3D, Color, BoundingBox, FaceRegion, Vector3D,
            FaceShape, EyeShape, NoseShape, LipShape, FaceAnalysis,
            BlendMode, EyeshadowStyle, LipstickConfig, EyeshadowConfig,
            BlushConfig, FoundationConfig, EyelinerConfig, MakeupConfig,
            FeatureType, ModificationType, NoseConfig, EyeConfig,
            JawlineConfig, CheekboneConfig, SurgeryConfig
        )
        
        # 엔진 인터페이스 임포트 테스트
        from engines import (
            FaceEngine, FaceDetectionResult, FaceFrame, VideoStream,
            MakeupEngine, MakeupResult, ColorBlender,
            SurgeryEngine, SurgeryResult, MeshWarper
        )
        
        print("✅ 모든 모듈 임포트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 임포트 실패: {e}")
        traceback.print_exc()
        return False

def test_data_models():
    """데이터 모델 기본 기능 테스트"""
    try:
        from models import Point3D, Color, BoundingBox, FaceRegion, Vector3D
        from models import LipstickConfig, BlendMode, NoseConfig
        
        # Point3D 테스트
        point = Point3D(10.5, 20.3, 5.0)
        assert point.to_tuple() == (10.5, 20.3, 5.0)
        assert point.to_2d() == (10.5, 20.3)
        
        # Color 테스트
        color = Color(255, 128, 64, 200)
        assert color.to_rgb() == (255, 128, 64)
        assert color.to_tuple() == (255, 128, 64, 200)
        
        # BoundingBox 테스트
        bbox = BoundingBox(10, 20, 100, 80)
        assert bbox.x2 == 110
        assert bbox.y2 == 100
        center = bbox.center
        assert center.x == 60.0
        assert center.y == 60.0
        
        # Vector3D 테스트
        vector = Vector3D(3, 4, 0)
        assert vector.magnitude() == 5.0
        normalized = vector.normalize()
        assert abs(normalized.magnitude() - 1.0) < 0.001
        
        # LipstickConfig 테스트
        lipstick = LipstickConfig(
            color=Color(200, 50, 50),
            intensity=0.8,
            glossiness=0.3,
            blend_mode=BlendMode.NORMAL
        )
        assert lipstick.intensity == 0.8
        
        # NoseConfig 테스트
        nose = NoseConfig(
            height_adjustment=0.2,
            width_adjustment=-0.1,
            tip_adjustment=0.0,
            bridge_adjustment=0.1
        )
        assert nose.height_adjustment == 0.2
        
        print("✅ 데이터 모델 기본 기능 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 데이터 모델 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_validation():
    """데이터 검증 기능 테스트"""
    try:
        from models import Color, LipstickConfig, BlendMode, NoseConfig
        
        # Color 범위 검증 테스트
        try:
            invalid_color = Color(300, 128, 64)  # 잘못된 값
            assert False, "잘못된 색상 값이 허용되었습니다"
        except ValueError:
            pass  # 예상된 예외
        
        # LipstickConfig 강도 검증 테스트
        try:
            invalid_lipstick = LipstickConfig(
                color=Color(200, 50, 50),
                intensity=1.5,  # 잘못된 값
                glossiness=0.3,
                blend_mode=BlendMode.NORMAL
            )
            assert False, "잘못된 강도 값이 허용되었습니다"
        except ValueError:
            pass  # 예상된 예외
        
        # NoseConfig 조정값 검증 테스트
        try:
            invalid_nose = NoseConfig(height_adjustment=2.0)  # 잘못된 값
            assert False, "잘못된 조정값이 허용되었습니다"
        except ValueError:
            pass  # 예상된 예외
        
        print("✅ 데이터 검증 기능 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 데이터 검증 테스트 실패: {e}")
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("=== 핵심 설정 테스트 시작 ===\n")
    
    tests = [
        ("모듈 임포트", test_imports),
        ("데이터 모델 기본 기능", test_data_models),
        ("데이터 검증 기능", test_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 {test_name} 테스트 중...")
        if test_func():
            passed += 1
        print()
    
    print("=== 테스트 결과 ===")
    print(f"통과: {passed}/{total}")
    
    if passed == total:
        print("🎉 모든 테스트 통과!")
        return True
    else:
        print("⚠️  일부 테스트 실패")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)