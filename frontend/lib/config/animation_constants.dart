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
  
  // 레이저 효과 시간
  static const int minLaserDuration = 1500;
  static const int maxLaserDuration = 15000;
  static const int laserIterationDuration = 1000;
  
  // 뷰티 스코어 애니메이션
  static const int beautyScoreAnimationDuration = 2000;
  static const int beautyScoreAnimationSteps = 60;
  static const int beautyScoreStepDuration = 33;
  
  // 공통 스텝 설정
  static const int stepDurationMs = 50;
  
  // 애니메이션 시퀀스 순서
  static const List<String> animationSequence = [
    'eyebrow_area',    // 1. 눈썹주변영역
    'eyebrows',        // 2. 눈썹
    'eyes',            // 3. 눈
    'eyelid_lower_area', // 4. 하주변영역
    'nose_bridge',     // 5. 코기둥
    'nose_sides',      // 6. 코측면
    'nose_wings',      // 7. 콧볼
    'cheek_area',      // 8. 볼영역
    'lip_upper',       // 9. 윗입술
    'lip_lower',       // 10. 아래입술
    'jawline_area',    // 11. 턱선영역
  ];
  
  // 히스토리 관리
  static const int maxHistorySize = 20;
}