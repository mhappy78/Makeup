"""
실시간 처리 성능 최적화 엔진
GPU 가속, 멀티스레딩, 메모리 최적화 구현
"""
import threading
import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Optional, Callable, Any, Tuple
import numpy as np
import time
import psutil
import gc
from dataclasses import dataclass
from enum import Enum
import queue
import weakref

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None

try:
    import numba
    from numba import jit, cuda
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    numba = None


class ProcessingMode(Enum):
    """처리 모드"""
    CPU_SINGLE = "cpu_single"
    CPU_MULTI = "cpu_multi"
    GPU_CUDA = "gpu_cuda"
    HYBRID = "hybrid"


class OptimizationLevel(Enum):
    """최적화 레벨"""
    BASIC = "basic"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class PerformanceConfig:
    """성능 설정"""
    processing_mode: ProcessingMode = ProcessingMode.CPU_MULTI
    optimization_level: OptimizationLevel = OptimizationLevel.BALANCED
    max_threads: int = 4
    enable_gpu: bool = True
    memory_limit_mb: int = 1024
    cache_size: int = 50
    enable_async: bool = True
    frame_skip_threshold: float = 0.033  # 30fps 기준


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    fps: float = 0.0
    avg_processing_time: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_usage_percent: float = 0.0
    cpu_usage_percent: float = 0.0
    cache_hit_rate: float = 0.0
    frame_drops: int = 0
    total_frames: int = 0


class MemoryManager:
    """메모리 관리자"""
    
    def __init__(self, limit_mb: int = 1024):
        self.limit_bytes = limit_mb * 1024 * 1024
        self.allocated_objects = weakref.WeakSet()
        self.memory_pool = {}
        self._lock = threading.Lock()
    
    def allocate_array(self, shape: tuple, dtype=np.float32) -> np.ndarray:
        """메모리 풀에서 배열 할당"""
        size_key = (shape, dtype)
        
        with self._lock:
            if size_key in self.memory_pool and self.memory_pool[size_key]:
                array = self.memory_pool[size_key].pop()
                array.fill(0)  # 초기화
                return array
            else:
                array = np.zeros(shape, dtype=dtype)
                self.allocated_objects.add(array)
                return array
    
    def deallocate_array(self, array: np.ndarray):
        """배열을 메모리 풀로 반환"""
        if array is None:
            return
        
        size_key = (array.shape, array.dtype)
        
        with self._lock:
            if size_key not in self.memory_pool:
                self.memory_pool[size_key] = []
            
            # 풀 크기 제한
            if len(self.memory_pool[size_key]) < 5:
                self.memory_pool[size_key].append(array)
    
    def get_memory_usage(self) -> float:
        """현재 메모리 사용량 (MB)"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def cleanup(self):
        """메모리 정리"""
        with self._lock:
            self.memory_pool.clear()
        gc.collect()
        
        if CUPY_AVAILABLE:
            try:
                cp.get_default_memory_pool().free_all_blocks()
            except:
                pass


class GPUAccelerator:
    """GPU 가속 처리기"""
    
    def __init__(self):
        self.gpu_available = CUPY_AVAILABLE and self._check_gpu()
        self.memory_pool = None
        
        if self.gpu_available:
            try:
                self.memory_pool = cp.get_default_memory_pool()
                self.pinned_memory_pool = cp.get_default_pinned_memory_pool()
            except:
                self.gpu_available = False
    
    def _check_gpu(self) -> bool:
        """GPU 사용 가능성 확인"""
        try:
            if not CUPY_AVAILABLE:
                return False
            
            # GPU 메모리 확인
            device = cp.cuda.Device()
            meminfo = device.mem_info
            free_memory = meminfo[0]
            
            # 최소 512MB 필요
            return free_memory > 512 * 1024 * 1024
        except:
            return False
    
    def to_gpu(self, array: np.ndarray) -> Any:
        """배열을 GPU로 전송"""
        if not self.gpu_available:
            return array
        
        try:
            return cp.asarray(array)
        except:
            return array
    
    def to_cpu(self, gpu_array: Any) -> np.ndarray:
        """GPU 배열을 CPU로 전송"""
        if not self.gpu_available or not hasattr(gpu_array, 'get'):
            return gpu_array
        
        try:
            return gpu_array.get()
        except:
            return gpu_array
    
    def gpu_blur(self, image: np.ndarray, kernel_size: int) -> np.ndarray:
        """GPU 가속 블러 처리"""
        if not self.gpu_available:
            import cv2
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        
        try:
            gpu_image = self.to_gpu(image)
            
            # 간단한 GPU 블러 구현
            kernel = cp.ones((kernel_size, kernel_size), dtype=cp.float32) / (kernel_size * kernel_size)
            
            if len(gpu_image.shape) == 3:
                blurred = cp.zeros_like(gpu_image)
                for c in range(gpu_image.shape[2]):
                    blurred[:, :, c] = cp.convolve2d(gpu_image[:, :, c], kernel, mode='same')
            else:
                blurred = cp.convolve2d(gpu_image, kernel, mode='same')
            
            return self.to_cpu(blurred)
        except:
            import cv2
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    
    def get_gpu_usage(self) -> float:
        """GPU 사용률 조회"""
        if not self.gpu_available:
            return 0.0
        
        try:
            device = cp.cuda.Device()
            meminfo = device.mem_info
            used_memory = meminfo[1] - meminfo[0]
            total_memory = meminfo[1]
            return (used_memory / total_memory) * 100 if total_memory > 0 else 0.0
        except:
            return 0.0
    
    def cleanup(self):
        """GPU 메모리 정리"""
        if self.gpu_available and self.memory_pool:
            try:
                self.memory_pool.free_all_blocks()
                self.pinned_memory_pool.free_all_blocks()
            except:
                pass


class AsyncProcessor:
    """비동기 처리기"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=min(max_workers, multiprocessing.cpu_count()))
        self.task_queue = asyncio.Queue()
        self.result_cache = {}
        self._running = False
    
    async def process_async(self, func: Callable, *args, **kwargs) -> Any:
        """비동기 처리 실행"""
        loop = asyncio.get_event_loop()
        
        # CPU 집약적 작업은 프로세스 풀 사용
        if kwargs.get('cpu_intensive', False):
            future = self.process_pool.submit(func, *args)
        else:
            future = self.thread_pool.submit(func, *args)
        
        return await loop.run_in_executor(None, future.result)
    
    def submit_task(self, task_id: str, func: Callable, *args, **kwargs):
        """작업 제출"""
        if task_id in self.result_cache:
            return self.result_cache[task_id]
        
        if kwargs.get('cpu_intensive', False):
            future = self.process_pool.submit(func, *args)
        else:
            future = self.thread_pool.submit(func, *args)
        
        self.result_cache[task_id] = future
        return future
    
    def get_result(self, task_id: str, timeout: float = None) -> Any:
        """결과 조회"""
        if task_id not in self.result_cache:
            return None
        
        try:
            return self.result_cache[task_id].result(timeout=timeout)
        except Exception as e:
            print(f"작업 {task_id} 실행 중 오류: {e}")
            return None
        finally:
            # 완료된 작업은 캐시에서 제거
            if task_id in self.result_cache:
                del self.result_cache[task_id]
    
    def cleanup(self):
        """리소스 정리"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        self.result_cache.clear()


class PerformanceOptimizer:
    """성능 최적화 메인 클래스"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.memory_manager = MemoryManager(config.memory_limit_mb)
        self.gpu_accelerator = GPUAccelerator()
        self.async_processor = AsyncProcessor(config.max_threads)
        
        # 성능 메트릭
        self.metrics = PerformanceMetrics()
        self._frame_times = []
        self._last_cleanup = time.time()
        
        # 적응적 설정
        self.adaptive_settings = {
            'current_skip_frames': 1,
            'quality_level': 1.0,
            'processing_threads': config.max_threads
        }
    
    def optimize_image_processing(self, func: Callable) -> Callable:
        """이미지 처리 함수 최적화 데코레이터"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # GPU 가속 시도
            if self.config.enable_gpu and self.gpu_accelerator.gpu_available:
                try:
                    # 첫 번째 인자가 이미지라고 가정
                    if len(args) > 0 and isinstance(args[0], np.ndarray):
                        gpu_args = list(args)
                        gpu_args[0] = self.gpu_accelerator.to_gpu(args[0])
                        result = func(*gpu_args, **kwargs)
                        
                        if hasattr(result, 'get'):
                            result = self.gpu_accelerator.to_cpu(result)
                        
                        processing_time = time.time() - start_time
                        self._update_metrics(processing_time)
                        return result
                except Exception as e:
                    print(f"GPU 처리 실패, CPU로 대체: {e}")
            
            # CPU 처리
            result = func(*args, **kwargs)
            processing_time = time.time() - start_time
            self._update_metrics(processing_time)
            
            return result
        
        return wrapper
    
    def optimize_face_detection(self, detection_func: Callable) -> Callable:
        """얼굴 감지 최적화"""
        def wrapper(image: np.ndarray, *args, **kwargs):
            # 이미지 크기 적응적 조정
            original_shape = image.shape
            scale_factor = self._calculate_optimal_scale(original_shape)
            
            if scale_factor < 1.0:
                # 이미지 축소로 처리 속도 향상
                import cv2
                new_height = int(original_shape[0] * scale_factor)
                new_width = int(original_shape[1] * scale_factor)
                resized_image = cv2.resize(image, (new_width, new_height))
                
                # 축소된 이미지로 감지
                result = detection_func(resized_image, *args, **kwargs)
                
                # 결과를 원본 크기로 스케일링
                if result and hasattr(result, 'landmarks'):
                    scaled_landmarks = []
                    for landmark in result.landmarks:
                        scaled_landmarks.append(Point3D(
                            landmark.x / scale_factor,
                            landmark.y / scale_factor,
                            landmark.z
                        ))
                    result.landmarks = scaled_landmarks
                
                return result
            else:
                return detection_func(image, *args, **kwargs)
        
        return wrapper
    
    def _calculate_optimal_scale(self, image_shape: tuple) -> float:
        """최적 스케일 계산"""
        height, width = image_shape[:2]
        
        # 기본 목표 해상도 (성능과 품질의 균형)
        target_pixels = 640 * 480
        current_pixels = height * width
        
        if current_pixels > target_pixels:
            scale_factor = np.sqrt(target_pixels / current_pixels)
            return max(0.5, min(1.0, scale_factor))
        
        return 1.0
    
    def batch_process_images(self, images: List[np.ndarray], 
                           process_func: Callable, 
                           batch_size: int = 4) -> List[Any]:
        """배치 이미지 처리"""
        results = []
        
        # 배치 단위로 처리
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            if self.config.enable_async:
                # 비동기 배치 처리
                futures = []
                for j, img in enumerate(batch):
                    task_id = f"batch_{i}_{j}"
                    future = self.async_processor.submit_task(task_id, process_func, img)
                    futures.append((task_id, future))
                
                # 결과 수집
                batch_results = []
                for task_id, future in futures:
                    result = self.async_processor.get_result(task_id, timeout=5.0)
                    batch_results.append(result)
                
                results.extend(batch_results)
            else:
                # 동기 배치 처리
                batch_results = [process_func(img) for img in batch]
                results.extend(batch_results)
        
        return results
    
    def adaptive_quality_control(self, current_fps: float, target_fps: float = 30.0):
        """적응적 품질 제어"""
        if current_fps < target_fps * 0.8:  # FPS가 목표의 80% 미만
            # 품질 낮추기
            self.adaptive_settings['current_skip_frames'] = min(4, 
                self.adaptive_settings['current_skip_frames'] + 1)
            self.adaptive_settings['quality_level'] = max(0.5, 
                self.adaptive_settings['quality_level'] - 0.1)
        elif current_fps > target_fps * 1.1:  # FPS가 목표의 110% 초과
            # 품질 높이기
            self.adaptive_settings['current_skip_frames'] = max(1, 
                self.adaptive_settings['current_skip_frames'] - 1)
            self.adaptive_settings['quality_level'] = min(1.0, 
                self.adaptive_settings['quality_level'] + 0.05)
    
    def _update_metrics(self, processing_time: float):
        """성능 메트릭 업데이트"""
        self._frame_times.append(processing_time)
        
        # 최근 30프레임만 유지
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)
        
        # 메트릭 계산
        if self._frame_times:
            self.metrics.avg_processing_time = np.mean(self._frame_times)
            self.metrics.fps = 1.0 / self.metrics.avg_processing_time if self.metrics.avg_processing_time > 0 else 0
        
        self.metrics.memory_usage_mb = self.memory_manager.get_memory_usage()
        self.metrics.gpu_usage_percent = self.gpu_accelerator.get_gpu_usage()
        self.metrics.cpu_usage_percent = psutil.cpu_percent()
        
        # 적응적 품질 제어
        self.adaptive_quality_control(self.metrics.fps)
        
        # 주기적 정리
        current_time = time.time()
        if current_time - self._last_cleanup > 30:  # 30초마다
            self._periodic_cleanup()
            self._last_cleanup = current_time
    
    def _periodic_cleanup(self):
        """주기적 메모리 정리"""
        self.memory_manager.cleanup()
        self.gpu_accelerator.cleanup()
        
        # 오래된 프레임 시간 정리
        if len(self._frame_times) > 10:
            self._frame_times = self._frame_times[-10:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        return {
            "metrics": {
                "fps": self.metrics.fps,
                "avg_processing_time_ms": self.metrics.avg_processing_time * 1000,
                "memory_usage_mb": self.metrics.memory_usage_mb,
                "gpu_usage_percent": self.metrics.gpu_usage_percent,
                "cpu_usage_percent": self.metrics.cpu_usage_percent
            },
            "adaptive_settings": self.adaptive_settings.copy(),
            "gpu_available": self.gpu_accelerator.gpu_available,
            "optimization_recommendations": self._get_optimization_recommendations()
        }
    
    def _get_optimization_recommendations(self) -> List[str]:
        """최적화 권장사항"""
        recommendations = []
        
        if self.metrics.fps < 20:
            recommendations.append("FPS가 낮습니다. 이미지 해상도를 낮추거나 프레임 스킵을 늘려보세요.")
        
        if self.metrics.memory_usage_mb > self.config.memory_limit_mb * 0.8:
            recommendations.append("메모리 사용량이 높습니다. 캐시 크기를 줄이거나 정리 주기를 단축하세요.")
        
        if self.metrics.cpu_usage_percent > 80:
            recommendations.append("CPU 사용률이 높습니다. 멀티스레딩을 활용하거나 처리 복잡도를 낮추세요.")
        
        if not self.gpu_accelerator.gpu_available and self.config.enable_gpu:
            recommendations.append("GPU를 사용할 수 없습니다. CUDA 및 CuPy 설치를 확인하세요.")
        
        return recommendations
    
    def cleanup(self):
        """리소스 정리"""
        self.memory_manager.cleanup()
        self.gpu_accelerator.cleanup()
        self.async_processor.cleanup()


# 성능 최적화된 유틸리티 함수들
if NUMBA_AVAILABLE:
    @jit(nopython=True)
    def fast_color_blend(base: np.ndarray, overlay: np.ndarray, alpha: float) -> np.ndarray:
        """JIT 컴파일된 빠른 색상 블렌딩"""
        result = np.zeros_like(base)
        for i in range(base.shape[0]):
            for j in range(base.shape[1]):
                for k in range(base.shape[2]):
                    result[i, j, k] = base[i, j, k] * (1 - alpha) + overlay[i, j, k] * alpha
        return result
else:
    def fast_color_blend(base: np.ndarray, overlay: np.ndarray, alpha: float) -> np.ndarray:
        """일반 색상 블렌딩"""
        return base * (1 - alpha) + overlay * alpha


def optimize_for_realtime(func: Callable) -> Callable:
    """실시간 처리 최적화 데코레이터"""
    def wrapper(*args, **kwargs):
        # 간단한 성능 모니터링
        start_time = time.time()
        result = func(*args, **kwargs)
        processing_time = time.time() - start_time
        
        # 처리 시간이 33ms(30fps) 초과시 경고
        if processing_time > 0.033:
            print(f"경고: {func.__name__} 처리 시간 {processing_time*1000:.1f}ms (목표: 33ms)")
        
        return result
    
    return wrapper