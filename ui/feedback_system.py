"""
사용자 피드백 및 알림 시스템 구현
진행 상황 표시, 오류 메시지, 튜토리얼 기능 제공
"""
import time
import streamlit as st
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass
from models.exceptions import BeautySimulationError, ErrorSeverity, ErrorCategory


class NotificationType(Enum):
    """알림 타입"""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ProgressType(Enum):
    """진행 상황 타입"""
    LOADING = "loading"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    APPLYING = "applying"


@dataclass
class Notification:
    """알림 메시지 데이터 클래스"""
    message: str
    type: NotificationType
    duration: float = 3.0
    dismissible: bool = True
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class ProgressInfo:
    """진행 상황 정보"""
    current: int
    total: int
    message: str
    type: ProgressType
    start_time: float = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()
    
    @property
    def percentage(self) -> float:
        """진행률 계산"""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)
    
    @property
    def elapsed_time(self) -> float:
        """경과 시간 계산"""
        return time.time() - self.start_time
    
    @property
    def estimated_remaining(self) -> float:
        """예상 남은 시간 계산"""
        if self.current == 0:
            return 0.0
        elapsed = self.elapsed_time
        rate = self.current / elapsed
        remaining_items = self.total - self.current
        return remaining_items / rate if rate > 0 else 0.0


class FeedbackSystem:
    """사용자 피드백 시스템"""
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self.current_progress: Optional[ProgressInfo] = None
        self.tutorial_shown = set()
        
        # 세션 상태 초기화
        if 'feedback_notifications' not in st.session_state:
            st.session_state.feedback_notifications = []
        if 'feedback_progress' not in st.session_state:
            st.session_state.feedback_progress = None
        if 'tutorial_shown' not in st.session_state:
            st.session_state.tutorial_shown = set()
    
    def show_notification(self, message: str, type: NotificationType = NotificationType.INFO,
                         duration: float = 3.0, dismissible: bool = True):
        """알림 메시지 표시"""
        notification = Notification(message, type, duration, dismissible)
        
        # Streamlit 알림 표시
        if type == NotificationType.SUCCESS:
            st.success(message)
        elif type == NotificationType.INFO:
            st.info(message)
        elif type == NotificationType.WARNING:
            st.warning(message)
        elif type == NotificationType.ERROR:
            st.error(message)
        
        # 세션 상태에 저장
        st.session_state.feedback_notifications.append(notification)
        
        # 자동 제거 (dismissible인 경우)
        if dismissible and duration > 0:
            time.sleep(duration)
            self._remove_notification(notification)
    
    def show_error_from_exception(self, error: BeautySimulationError):
        """예외 객체로부터 오류 메시지 표시"""
        # 심각도에 따른 알림 타입 결정
        if error.severity == ErrorSeverity.CRITICAL:
            notification_type = NotificationType.ERROR
        elif error.severity == ErrorSeverity.HIGH:
            notification_type = NotificationType.ERROR
        elif error.severity == ErrorSeverity.MEDIUM:
            notification_type = NotificationType.WARNING
        else:
            notification_type = NotificationType.INFO
        
        # 사용자 친화적 메시지 표시
        self.show_notification(error.user_message, notification_type)
        
        # 복구 제안사항이 있으면 추가 표시
        if error.recovery_suggestions:
            with st.expander("해결 방법 보기"):
                for suggestion in error.recovery_suggestions:
                    st.write(f"• {suggestion}")
    
    def start_progress(self, total: int, message: str, 
                      type: ProgressType = ProgressType.PROCESSING):
        """진행 상황 표시 시작"""
        progress_info = ProgressInfo(0, total, message, type)
        self.current_progress = progress_info
        st.session_state.feedback_progress = progress_info
        
        # Streamlit 진행 바 생성
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        return progress_bar, status_text
    
    def update_progress(self, current: int, message: Optional[str] = None,
                       progress_bar=None, status_text=None):
        """진행 상황 업데이트"""
        if not self.current_progress:
            return
        
        self.current_progress.current = current
        if message:
            self.current_progress.message = message
        
        # Streamlit UI 업데이트
        if progress_bar:
            progress_bar.progress(self.current_progress.percentage / 100)
        
        if status_text:
            elapsed = self.current_progress.elapsed_time
            remaining = self.current_progress.estimated_remaining
            
            status_message = f"{self.current_progress.message} ({current}/{self.current_progress.total})"
            if remaining > 0:
                status_message += f" - 예상 남은 시간: {remaining:.1f}초"
            
            status_text.text(status_message)
    
    def complete_progress(self, success_message: str = "완료되었습니다!"):
        """진행 상황 완료"""
        if self.current_progress:
            self.current_progress.current = self.current_progress.total
            self.current_progress = None
            st.session_state.feedback_progress = None
            
            self.show_notification(success_message, NotificationType.SUCCESS)
    
    def show_loading_spinner(self, message: str = "처리 중..."):
        """로딩 스피너 표시"""
        return st.spinner(message)
    
    def _remove_notification(self, notification: Notification):
        """알림 제거"""
        if notification in st.session_state.feedback_notifications:
            st.session_state.feedback_notifications.remove(notification)


class TutorialSystem:
    """튜토리얼 및 도움말 시스템"""
    
    def __init__(self):
        self.tutorials = {
            "first_visit": {
                "title": "뷰티 시뮬레이션에 오신 것을 환영합니다!",
                "steps": [
                    "1. 먼저 카메라를 활성화하거나 이미지를 업로드하세요.",
                    "2. 얼굴이 감지되면 메이크업이나 성형 효과를 선택할 수 있습니다.",
                    "3. 슬라이더를 조정하여 원하는 효과를 적용해보세요.",
                    "4. 결과가 마음에 들면 이미지를 저장할 수 있습니다."
                ]
            },
            "makeup_controls": {
                "title": "메이크업 컨트롤 사용법",
                "steps": [
                    "• 립스틱: 입술 색상과 강도를 조절합니다.",
                    "• 아이섀도: 눈꺼풀 색상과 스타일을 선택합니다.",
                    "• 블러셔: 볼 색상과 위치를 조정합니다.",
                    "• 파운데이션: 피부 톤과 커버리지를 설정합니다."
                ]
            },
            "surgery_controls": {
                "title": "성형 시뮬레이션 사용법",
                "steps": [
                    "• 코 성형: 코의 높이, 폭, 각도를 조절합니다.",
                    "• 눈 성형: 눈의 크기와 모양을 변경합니다.",
                    "• 턱선: 턱선의 각도와 길이를 조정합니다.",
                    "⚠️ 자연스러운 범위 내에서 조절하는 것을 권장합니다."
                ]
            },
            "camera_tips": {
                "title": "최적의 카메라 사용 팁",
                "steps": [
                    "• 충분한 조명이 있는 곳에서 촬영하세요.",
                    "• 얼굴이 화면 중앙에 오도록 위치를 조정하세요.",
                    "• 카메라를 얼굴과 수직으로 맞춰주세요.",
                    "• 머리카락이 얼굴을 가리지 않도록 주의하세요."
                ]
            }
        }
    
    def show_tutorial(self, tutorial_key: str, force_show: bool = False):
        """튜토리얼 표시"""
        if tutorial_key not in self.tutorials:
            return
        
        # 이미 표시된 튜토리얼인지 확인
        if not force_show and tutorial_key in st.session_state.tutorial_shown:
            return
        
        tutorial = self.tutorials[tutorial_key]
        
        with st.expander(f"💡 {tutorial['title']}", expanded=True):
            for step in tutorial['steps']:
                st.write(step)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("이해했습니다", key=f"tutorial_{tutorial_key}_ok"):
                    st.session_state.tutorial_shown.add(tutorial_key)
                    st.experimental_rerun()
            
            with col2:
                if st.button("다시 보지 않기", key=f"tutorial_{tutorial_key}_dismiss"):
                    st.session_state.tutorial_shown.add(tutorial_key)
                    st.experimental_rerun()
    
    def show_help_section(self):
        """도움말 섹션 표시"""
        with st.sidebar:
            st.markdown("### 📚 도움말")
            
            if st.button("🎯 기본 사용법"):
                self.show_tutorial("first_visit", force_show=True)
            
            if st.button("💄 메이크업 가이드"):
                self.show_tutorial("makeup_controls", force_show=True)
            
            if st.button("✨ 성형 시뮬레이션 가이드"):
                self.show_tutorial("surgery_controls", force_show=True)
            
            if st.button("📷 카메라 사용 팁"):
                self.show_tutorial("camera_tips", force_show=True)
    
    def show_contextual_help(self, context: str):
        """상황별 도움말 표시"""
        help_messages = {
            "no_face_detected": {
                "message": "얼굴이 감지되지 않았습니다.",
                "suggestions": [
                    "조명을 밝게 해주세요",
                    "카메라를 얼굴 정면으로 향해주세요",
                    "얼굴이 화면에 완전히 들어오도록 조정해주세요"
                ]
            },
            "low_image_quality": {
                "message": "이미지 품질이 낮습니다.",
                "suggestions": [
                    "더 선명한 이미지를 사용해주세요",
                    "이미지 해상도를 높여주세요",
                    "흔들림 없는 이미지를 촬영해주세요"
                ]
            },
            "processing_slow": {
                "message": "처리 속도가 느립니다.",
                "suggestions": [
                    "이미지 크기를 줄여보세요",
                    "다른 프로그램을 종료해주세요",
                    "잠시 후 다시 시도해주세요"
                ]
            }
        }
        
        if context in help_messages:
            help_info = help_messages[context]
            
            st.warning(help_info["message"])
            with st.expander("해결 방법 보기"):
                for suggestion in help_info["suggestions"]:
                    st.write(f"• {suggestion}")


class UserGuidanceSystem:
    """사용자 가이드 시스템"""
    
    def __init__(self):
        self.feedback_system = FeedbackSystem()
        self.tutorial_system = TutorialSystem()
    
    def initialize_user_session(self):
        """사용자 세션 초기화 및 첫 방문 가이드"""
        if 'first_visit' not in st.session_state:
            st.session_state.first_visit = True
            self.tutorial_system.show_tutorial("first_visit")
        
        # 도움말 섹션 항상 표시
        self.tutorial_system.show_help_section()
    
    def guide_user_through_process(self, current_step: str):
        """프로세스별 사용자 가이드"""
        guidance_messages = {
            "image_upload": "이미지를 업로드하거나 카메라를 활성화해주세요.",
            "face_detection": "얼굴을 감지하는 중입니다...",
            "effect_selection": "원하는 효과를 선택하고 조정해주세요.",
            "result_preview": "결과를 확인하고 저장하거나 조정할 수 있습니다."
        }
        
        if current_step in guidance_messages:
            st.info(guidance_messages[current_step])
    
    def provide_smart_suggestions(self, user_context: Dict[str, Any]):
        """사용자 상황에 맞는 스마트 제안"""
        suggestions = []
        
        # 얼굴 형태에 따른 메이크업 제안
        if 'face_shape' in user_context:
            face_shape = user_context['face_shape']
            if face_shape == 'round':
                suggestions.append("둥근 얼굴형에는 각진 아이라인이 잘 어울립니다.")
            elif face_shape == 'square':
                suggestions.append("각진 얼굴형에는 부드러운 블러셔가 좋습니다.")
        
        # 피부톤에 따른 색상 제안
        if 'skin_tone' in user_context:
            skin_tone = user_context['skin_tone']
            if skin_tone == 'warm':
                suggestions.append("따뜻한 피부톤에는 코랄이나 피치 계열 색상을 추천합니다.")
            elif skin_tone == 'cool':
                suggestions.append("차가운 피부톤에는 로즈나 베리 계열 색상이 잘 어울립니다.")
        
        # 제안사항 표시
        if suggestions:
            with st.expander("💡 맞춤 제안"):
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")
    
    def handle_error_gracefully(self, error: BeautySimulationError):
        """오류 상황에서의 사용자 가이드"""
        self.feedback_system.show_error_from_exception(error)
        
        # 오류 카테고리별 추가 가이드
        if error.category == ErrorCategory.FACE_DETECTION:
            self.tutorial_system.show_contextual_help("no_face_detected")
        elif error.category == ErrorCategory.IMAGE_PROCESSING:
            self.tutorial_system.show_contextual_help("low_image_quality")
        elif error.category == ErrorCategory.SYSTEM:
            self.tutorial_system.show_contextual_help("processing_slow")


# 전역 인스턴스
feedback_system = FeedbackSystem()
tutorial_system = TutorialSystem()
user_guidance = UserGuidanceSystem()


def with_progress_feedback(total_steps: int, operation_name: str = "처리"):
    """진행 상황 피드백 데코레이터"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            progress_bar, status_text = feedback_system.start_progress(
                total_steps, f"{operation_name} 중..."
            )
            
            try:
                result = func(*args, progress_callback=lambda step, msg: 
                            feedback_system.update_progress(step, msg, progress_bar, status_text),
                            **kwargs)
                feedback_system.complete_progress(f"{operation_name} 완료!")
                return result
            except Exception as e:
                feedback_system.show_notification(
                    f"{operation_name} 중 오류가 발생했습니다: {str(e)}", 
                    NotificationType.ERROR
                )
                raise
        
        return wrapper
    return decorator


def show_success_message(message: str):
    """성공 메시지 표시 헬퍼 함수"""
    feedback_system.show_notification(message, NotificationType.SUCCESS)


def show_error_message(message: str):
    """오류 메시지 표시 헬퍼 함수"""
    feedback_system.show_notification(message, NotificationType.ERROR)


def show_warning_message(message: str):
    """경고 메시지 표시 헬퍼 함수"""
    feedback_system.show_notification(message, NotificationType.WARNING)


def show_info_message(message: str):
    """정보 메시지 표시 헬퍼 함수"""
    feedback_system.show_notification(message, NotificationType.INFO)