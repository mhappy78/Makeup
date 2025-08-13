"""
포괄적인 오류 처리 시스템 구현
커스텀 예외 클래스 계층 구조 및 오류 처리 유틸리티
"""
import time
import logging
import traceback
from typing import Optional, Dict, Any, Callable, List
from enum import Enum
from dataclasses import dataclass


class ErrorSeverity(Enum):
    """오류 심각도 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """오류 카테고리"""
    FACE_DETECTION = "face_detection"
    IMAGE_PROCESSING = "image_processing"
    MAKEUP_APPLICATION = "makeup_application"
    SURGERY_SIMULATION = "surgery_simulation"
    FILE_OPERATION = "file_operation"
    CAMERA_ACCESS = "camera_access"
    RESOURCE_MANAGEMENT = "resource_management"
    VALIDATION = "validation"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """오류 컨텍스트 정보"""
    timestamp: float
    function_name: str
    file_name: str
    line_number: int
    user_action: Optional[str] = None
    system_state: Optional[Dict[str, Any]] = None
    additional_info: Optional[Dict[str, Any]] = None


class BeautySimulationError(Exception):
    """기본 예외 클래스 - 모든 커스텀 예외의 부모 클래스"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[ErrorContext] = None,
                 original_exception: Optional[Exception] = None,
                 user_message: Optional[str] = None,
                 recovery_suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context
        self.original_exception = original_exception
        self.user_message = user_message or self._generate_user_message()
        self.recovery_suggestions = recovery_suggestions or []
        self.timestamp = time.time()
    
    def _generate_user_message(self) -> str:
        """사용자 친화적 오류 메시지 생성"""
        return "처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
    
    def to_dict(self) -> Dict[str, Any]:
        """오류 정보를 딕셔너리로 변환"""
        return {
            "message": self.message,
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "recovery_suggestions": self.recovery_suggestions,
            "context": self.context.__dict__ if self.context else None,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }


class FaceDetectionError(BeautySimulationError):
    """얼굴 감지 관련 오류"""
    
    def __init__(self, message: str, detection_confidence: Optional[float] = None,
                 image_quality_score: Optional[float] = None, **kwargs):
        self.detection_confidence = detection_confidence
        self.image_quality_score = image_quality_score
        super().__init__(
            message, 
            category=ErrorCategory.FACE_DETECTION,
            **kwargs
        )
    
    def _generate_user_message(self) -> str:
        if hasattr(self, 'detection_confidence') and self.detection_confidence is not None and self.detection_confidence < 0.3:
            return "얼굴을 명확하게 감지할 수 없습니다. 조명을 밝게 하고 카메라를 얼굴 정면으로 향해주세요."
        return "얼굴 감지에 실패했습니다. 카메라 앞에 얼굴이 잘 보이도록 위치를 조정해주세요."


class InvalidImageError(BeautySimulationError):
    """잘못된 이미지 형식 오류"""
    
    def __init__(self, message: str, image_format: Optional[str] = None,
                 image_size: Optional[tuple] = None, **kwargs):
        self.image_format = image_format
        self.image_size = image_size
        super().__init__(
            message,
            category=ErrorCategory.IMAGE_PROCESSING,
            **kwargs
        )
    
    def _generate_user_message(self) -> str:
        if hasattr(self, 'image_format') and self.image_format:
            return f"지원하지 않는 이미지 형식입니다 ({self.image_format}). JPG, PNG 형식의 이미지를 사용해주세요."
        return "이미지 파일이 손상되었거나 지원하지 않는 형식입니다. 다른 이미지를 선택해주세요."


class ProcessingTimeoutError(BeautySimulationError):
    """처리 시간 초과 오류"""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None,
                 operation_type: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.timeout_duration = timeout_duration
        self.operation_type = operation_type
    
    def _generate_user_message(self) -> str:
        if self.operation_type:
            return f"{self.operation_type} 처리 시간이 초과되었습니다. 이미지 크기를 줄이거나 잠시 후 다시 시도해주세요."
        return "처리 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."


class InsufficientResourceError(BeautySimulationError):
    """리소스 부족 오류"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None,
                 available_amount: Optional[float] = None,
                 required_amount: Optional[float] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RESOURCE_MANAGEMENT,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.resource_type = resource_type
        self.available_amount = available_amount
        self.required_amount = required_amount
    
    def _generate_user_message(self) -> str:
        if self.resource_type == "memory":
            return "메모리가 부족합니다. 다른 프로그램을 종료하거나 이미지 크기를 줄여주세요."
        elif self.resource_type == "storage":
            return "저장 공간이 부족합니다. 불필요한 파일을 삭제하거나 다른 위치에 저장해주세요."
        return "시스템 리소스가 부족합니다. 잠시 후 다시 시도해주세요."


class CameraAccessError(BeautySimulationError):
    """카메라 접근 오류"""
    
    def __init__(self, message: str, camera_id: Optional[int] = None,
                 permission_denied: bool = False, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CAMERA_ACCESS,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.camera_id = camera_id
        self.permission_denied = permission_denied
    
    def _generate_user_message(self) -> str:
        if self.permission_denied:
            return "카메라 접근 권한이 필요합니다. 브라우저 설정에서 카메라 권한을 허용해주세요."
        return "카메라에 접근할 수 없습니다. 카메라가 다른 프로그램에서 사용 중이지 않은지 확인해주세요."


class MakeupApplicationError(BeautySimulationError):
    """메이크업 적용 오류"""
    
    def __init__(self, message: str, makeup_type: Optional[str] = None,
                 invalid_config: bool = False, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.MAKEUP_APPLICATION,
            **kwargs
        )
        self.makeup_type = makeup_type
        self.invalid_config = invalid_config
    
    def _generate_user_message(self) -> str:
        if self.makeup_type:
            return f"{self.makeup_type} 적용 중 오류가 발생했습니다. 설정을 확인하고 다시 시도해주세요."
        return "메이크업 적용 중 오류가 발생했습니다. 설정을 초기화하고 다시 시도해주세요."


class SurgerySimulationError(BeautySimulationError):
    """성형 시뮬레이션 오류"""
    
    def __init__(self, message: str, surgery_type: Optional[str] = None,
                 excessive_modification: bool = False, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SURGERY_SIMULATION,
            **kwargs
        )
        self.surgery_type = surgery_type
        self.excessive_modification = excessive_modification
    
    def _generate_user_message(self) -> str:
        if self.excessive_modification:
            return "변형 정도가 너무 큽니다. 자연스러운 범위 내에서 조정해주세요."
        if self.surgery_type:
            return f"{self.surgery_type} 시뮬레이션 중 오류가 발생했습니다. 설정을 확인하고 다시 시도해주세요."
        return "성형 시뮬레이션 중 오류가 발생했습니다. 설정을 초기화하고 다시 시도해주세요."


class FileOperationError(BeautySimulationError):
    """파일 작업 오류"""
    
    def __init__(self, message: str, file_path: Optional[str] = None,
                 operation_type: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.FILE_OPERATION,
            **kwargs
        )
        self.file_path = file_path
        self.operation_type = operation_type
    
    def _generate_user_message(self) -> str:
        if self.operation_type == "save":
            return "파일 저장에 실패했습니다. 저장 위치와 권한을 확인해주세요."
        elif self.operation_type == "load":
            return "파일을 불러올 수 없습니다. 파일이 존재하고 접근 가능한지 확인해주세요."
        return "파일 작업 중 오류가 발생했습니다. 파일 경로와 권한을 확인해주세요."


class ValidationError(BeautySimulationError):
    """데이터 검증 오류"""
    
    def __init__(self, message: str, field_name: Optional[str] = None,
                 invalid_value: Optional[Any] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )
        self.field_name = field_name
        self.invalid_value = invalid_value
    
    def _generate_user_message(self) -> str:
        if self.field_name:
            return f"입력값이 올바르지 않습니다 ({self.field_name}). 올바른 값을 입력해주세요."
        return "입력값이 올바르지 않습니다. 설정을 확인하고 다시 시도해주세요."

class ErrorHandler:
    """중앙화된 오류 처리 시스템"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.error_history: List[BeautySimulationError] = []
        self.max_history_size = 100
        
        # 재시도 설정
        self.retry_config = {
            ErrorCategory.FACE_DETECTION: {"max_retries": 3, "delay": 1.0},
            ErrorCategory.IMAGE_PROCESSING: {"max_retries": 2, "delay": 0.5},
            ErrorCategory.CAMERA_ACCESS: {"max_retries": 2, "delay": 2.0},
            ErrorCategory.FILE_OPERATION: {"max_retries": 3, "delay": 0.5},
            ErrorCategory.NETWORK: {"max_retries": 3, "delay": 2.0}
        }
        
        # 폴백 옵션
        self.fallback_handlers = {}
    
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger("beauty_simulation_errors")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def handle_error(self, error: BeautySimulationError, 
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        오류 처리 메인 메서드
        
        Args:
            error: 처리할 오류
            context: 추가 컨텍스트 정보
            
        Returns:
            오류 처리 결과
        """
        # 오류 로깅
        self._log_error(error, context)
        
        # 오류 히스토리에 추가
        self._add_to_history(error)
        
        # 복구 시도
        recovery_result = self._attempt_recovery(error, context)
        
        # 결과 반환
        return {
            "error": error.to_dict(),
            "recovery_attempted": recovery_result["attempted"],
            "recovery_successful": recovery_result["successful"],
            "fallback_used": recovery_result.get("fallback_used", False),
            "user_message": error.user_message,
            "recovery_suggestions": error.recovery_suggestions
        }
    
    def _log_error(self, error: BeautySimulationError, 
                  context: Optional[Dict[str, Any]] = None):
        """오류 로깅"""
        log_message = f"[{error.category.value}] {error.message}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra={"error": error.to_dict(), "context": context})
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra={"error": error.to_dict(), "context": context})
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra={"error": error.to_dict(), "context": context})
        else:
            self.logger.info(log_message, extra={"error": error.to_dict(), "context": context})
    
    def _add_to_history(self, error: BeautySimulationError):
        """오류 히스토리에 추가"""
        self.error_history.append(error)
        
        # 히스토리 크기 제한
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
    
    def _attempt_recovery(self, error: BeautySimulationError,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """복구 시도"""
        recovery_result = {
            "attempted": False,
            "successful": False,
            "fallback_used": False
        }
        
        # 재시도 가능한 오류인지 확인
        if error.category in self.retry_config:
            recovery_result["attempted"] = True
            retry_success = self._attempt_retry(error, context)
            recovery_result["successful"] = retry_success
            
            if not retry_success:
                # 재시도 실패 시 폴백 시도
                fallback_success = self._attempt_fallback(error, context)
                recovery_result["fallback_used"] = fallback_success
                recovery_result["successful"] = fallback_success
        
        return recovery_result
    
    def _attempt_retry(self, error: BeautySimulationError,
                      context: Optional[Dict[str, Any]] = None) -> bool:
        """재시도 메커니즘"""
        if error.category not in self.retry_config:
            return False
        
        config = self.retry_config[error.category]
        max_retries = config["max_retries"]
        delay = config["delay"]
        
        for attempt in range(max_retries):
            try:
                time.sleep(delay * (attempt + 1))  # 지수적 백오프
                
                # 재시도 로직 (실제 구현에서는 원래 작업을 재실행)
                self.logger.info(f"재시도 {attempt + 1}/{max_retries}: {error.category.value}")
                
                # 여기서는 시뮬레이션을 위해 성공으로 가정
                # 실제로는 원래 실패한 작업을 다시 시도해야 함
                return True
                
            except Exception as retry_error:
                self.logger.warning(f"재시도 {attempt + 1} 실패: {str(retry_error)}")
                continue
        
        return False
    
    def _attempt_fallback(self, error: BeautySimulationError,
                         context: Optional[Dict[str, Any]] = None) -> bool:
        """폴백 옵션 시도"""
        if error.category not in self.fallback_handlers:
            return False
        
        try:
            fallback_handler = self.fallback_handlers[error.category]
            return fallback_handler(error, context)
        except Exception as fallback_error:
            self.logger.error(f"폴백 처리 실패: {str(fallback_error)}")
            return False
    
    def register_fallback_handler(self, category: ErrorCategory, 
                                 handler: Callable[[BeautySimulationError, Optional[Dict[str, Any]]], bool]):
        """폴백 핸들러 등록"""
        self.fallback_handlers[category] = handler
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """오류 통계 반환"""
        if not self.error_history:
            return {"total_errors": 0}
        
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "by_category": category_counts,
            "by_severity": severity_counts,
            "recent_errors": [error.to_dict() for error in self.error_history[-5:]]
        }


def with_error_handling(category: ErrorCategory = ErrorCategory.SYSTEM,
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                       user_message: Optional[str] = None,
                       recovery_suggestions: Optional[List[str]] = None):
    """
    오류 처리 데코레이터
    
    Args:
        category: 오류 카테고리
        severity: 오류 심각도
        user_message: 사용자 메시지
        recovery_suggestions: 복구 제안사항
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BeautySimulationError:
                # 이미 처리된 커스텀 예외는 그대로 전파
                raise
            except Exception as e:
                # 일반 예외를 커스텀 예외로 변환
                error_context = ErrorContext(
                    timestamp=time.time(),
                    function_name=func.__name__,
                    file_name=func.__code__.co_filename,
                    line_number=func.__code__.co_firstlineno
                )
                
                raise BeautySimulationError(
                    message=f"함수 {func.__name__}에서 오류 발생: {str(e)}",
                    category=category,
                    severity=severity,
                    context=error_context,
                    original_exception=e,
                    user_message=user_message,
                    recovery_suggestions=recovery_suggestions
                )
        
        return wrapper
    return decorator


# 전역 오류 핸들러 인스턴스
global_error_handler = ErrorHandler()


def handle_graceful_degradation(primary_func: Callable, 
                               fallback_func: Optional[Callable] = None,
                               error_message: str = "기본 기능으로 전환합니다."):
    """
    Graceful degradation 구현
    
    Args:
        primary_func: 주요 기능 함수
        fallback_func: 폴백 함수
        error_message: 오류 메시지
    """
    def wrapper(*args, **kwargs):
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            global_error_handler.logger.warning(f"주요 기능 실패, 폴백 시도: {str(e)}")
            
            if fallback_func:
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    global_error_handler.logger.error(f"폴백 기능도 실패: {str(fallback_error)}")
                    raise BeautySimulationError(
                        message=f"주요 기능과 폴백 기능 모두 실패: {str(e)}",
                        severity=ErrorSeverity.HIGH,
                        user_message=error_message
                    )
            else:
                raise BeautySimulationError(
                    message=f"기능 실행 실패: {str(e)}",
                    severity=ErrorSeverity.MEDIUM,
                    user_message=error_message
                )
    
    return wrapper


def create_error_context(func_name: str, user_action: Optional[str] = None,
                        system_state: Optional[Dict[str, Any]] = None) -> ErrorContext:
    """오류 컨텍스트 생성 헬퍼 함수"""
    import inspect
    
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_frame = frame.f_back
        return ErrorContext(
            timestamp=time.time(),
            function_name=func_name,
            file_name=caller_frame.f_code.co_filename,
            line_number=caller_frame.f_lineno,
            user_action=user_action,
            system_state=system_state
        )
    
    return ErrorContext(
        timestamp=time.time(),
        function_name=func_name,
        file_name="unknown",
        line_number=0,
        user_action=user_action,
        system_state=system_state
    )


def safe_execute(func: Callable, *args, default_return=None, 
                error_handler: Optional[ErrorHandler] = None, **kwargs):
    """
    안전한 함수 실행 유틸리티
    
    Args:
        func: 실행할 함수
        args: 함수 인자
        default_return: 오류 시 반환할 기본값
        error_handler: 사용할 오류 핸들러
        kwargs: 함수 키워드 인자
    """
    handler = error_handler or global_error_handler
    
    try:
        return func(*args, **kwargs)
    except BeautySimulationError as e:
        handler.handle_error(e)
        return default_return
    except Exception as e:
        # 일반 예외를 커스텀 예외로 변환
        custom_error = BeautySimulationError(
            message=f"함수 {func.__name__} 실행 중 오류: {str(e)}",
            original_exception=e,
            context=create_error_context(func.__name__)
        )
        handler.handle_error(custom_error)
        return default_return