/// 애니메이션 관련 상수들
class AnimationConstants {
  // 애니메이션 지속 시간 (밀리초)
  static const int eyebrowAreaDuration = 3000;
  static const int eyebrowsDuration = 2000;
  static const int eyesAreaDuration = 2500;
  static const int eyelidLowerAreaDuration = 2500;
  static const int cheekAreaDuration = 2500;
  static const int noseBridgeDuration = 1500;
  static const int noseSidesDuration = 1500;
  static const int noseWingsDuration = 2000;
  static const int lipUpperDuration = 2000;
  static const int lipLowerDuration = 2000;
  static const int jawlineAreaDuration = 3500;
  static const int defaultDuration = 2000;
  
  // 레이저 효과
  static const int minLaserDuration = 1500;
  static const int maxLaserDuration = 15000;
  static const int laserIterationDuration = 1000;
  
  // 뷰티 스코어 애니메이션
  static const int beautyScoreAnimationDuration = 2000;
  static const int beautyScoreAnimationSteps = 60;
  static const int beautyScoreStepDuration = 33;
  
  // 공통 스텝 설정
  static const int stepDurationMs = 50;
  
  /// 영역별 애니메이션 지속시간 가져오기
  static int getDurationForRegion(String regionKey) {
    switch (regionKey) {
      case 'eyebrow_area':
        return eyebrowAreaDuration;
      case 'eyebrows':
        return eyebrowsDuration;
      case 'eyes':
      case 'eyelid_lower_area':
      case 'cheek_area':
        return eyesAreaDuration;
      case 'nose_bridge':
      case 'nose_sides':
        return noseBridgeDuration;
      case 'nose_wings':
      case 'lip_upper':
      case 'lip_lower':
        return noseWingsDuration;
      case 'jawline_area':
        return jawlineAreaDuration;
      default:
        return defaultDuration;
    }
  }
}