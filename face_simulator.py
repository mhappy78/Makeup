import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import math
import mediapipe as mp

class FaceSimulator:
    # 아래턱 100샷+ 프리셋 상수
    LOWER_JAW_PRESET_STRENGTH = 0.05       # 변형 강도
    LOWER_JAW_PRESET_INFLUENCE_RATIO = 0.4  # 얼굴 크기 대비 영향반경 (40%)
    LOWER_JAW_PRESET_PULL_RATIO = 0.1       # 랜드마크 간 거리 대비 당기는 거리 (10%)
    LOWER_JAW_FACE_SIZE_LANDMARKS = (234, 447)  # 얼굴 크기 기준 랜드마크
    LOWER_JAW_TARGET_LANDMARKS = (150, 379, 4)  # 변형 대상 랜드마크 (150, 379 → 4)
    
    # 중간턱 100샷+ 프리셋 상수
    MIDDLE_JAW_PRESET_STRENGTH = 0.05       # 변형 강도
    MIDDLE_JAW_PRESET_INFLUENCE_RATIO = 0.65 # 얼굴 크기 대비 영향반경 (65%)
    MIDDLE_JAW_PRESET_PULL_RATIO = 0.1       # 랜드마크 간 거리 대비 당기는 거리 (10%)
    MIDDLE_JAW_FACE_SIZE_LANDMARKS = (234, 447)  # 얼굴 크기 기준 랜드마크
    MIDDLE_JAW_TARGET_LANDMARKS = (172, 397, 4)  # 변형 대상 랜드마크 (172, 397 → 4)
    
    # 볼 100샷+ 프리셋 상수
    CHEEK_PRESET_STRENGTH = 0.05       # 변형 강도
    CHEEK_PRESET_INFLUENCE_RATIO = 0.65 # 얼굴 크기 대비 영향반경 (65%)
    CHEEK_PRESET_PULL_RATIO = 0.1       # 랜드마크 간 거리 대비 당기는 거리 (10%)
    CHEEK_FACE_SIZE_LANDMARKS = (234, 447)  # 얼굴 크기 기준 랜드마크
    CHEEK_TARGET_LANDMARKS = (215, 435, 4)  # 변형 대상 랜드마크 (215, 435 → 4)
    
    # 앞튀임+ 프리셋 상수
    FRONT_PROTUSION_PRESET_STRENGTH = 0.05       # 변형 강도
    FRONT_PROTUSION_PRESET_INFLUENCE_RATIO = 0.1 # 얼굴 크기 대비 영향반경 (10%)
    FRONT_PROTUSION_PRESET_PULL_RATIO = 0.1       # 랜드마크 간 거리 대비 당기는 거리 (10%)
    FRONT_PROTUSION_FACE_SIZE_LANDMARKS = (234, 447)  # 얼굴 크기 기준 랜드마크
    FRONT_PROTUSION_TARGET_LANDMARKS = (243, 463, (56, 190), (414, 286), 168, 6)  # 변형 대상 랜드마크 (243, 463, 56과190중간, 414와286중간 → 168과 6의 중간점)
    FRONT_PROTUSION_ELLIPSE_RATIO = 1.3           # 타원 세로 비율 (가로 대비 세로가 30% 더 김)
    
    # 뒷트임+ 프리셋 상수
    BACK_SLIT_PRESET_STRENGTH = 0.1               # 변형 강도 (10%)
    BACK_SLIT_PRESET_INFLUENCE_RATIO = 0.1        # 얼굴 크기 대비 영향반경 (10%)
    BACK_SLIT_PRESET_PULL_RATIO = 0.1             # 랜드마크 간 거리 대비 당기는 거리 (10%)
    BACK_SLIT_FACE_SIZE_LANDMARKS = (234, 447)    # 얼굴 크기 기준 랜드마크
    BACK_SLIT_TARGET_LANDMARKS = (33, 359, (34, 162), (368, 264))  # 변형 대상 랜드마크 (33→34/162중간, 359→368/264중간)
    
    # 얼굴 황금비율 상수
    GOLDEN_RATIO = 1.618                           # 황금비율 상수
    FACE_GOLDEN_RATIOS = {
        "전체_얼굴_비율": 1.618,                    # 얼굴 길이 : 얼굴 너비
        "얼굴_삼등분": 1.0,                         # 이마:중간:아래 = 1:1:1
        "눈_간격": 1.0,                             # 눈 너비 = 눈 사이 간격
        "입_너비": 1.618,                           # 입 너비 : 코 너비
        "코_길이": 1.0,                             # 코 길이 비율
        "턱_각도": 120,                             # 이상적인 턱 각도 (도)
    }
    
    # 얼굴 측정 랜드마크 정의
    FACE_MEASUREMENT_LANDMARKS = {
        "얼굴_윤곽": {"top": 10, "bottom": 152, "left": 234, "right": 454},
        "이마": {"top": 10, "bottom": 9},
        "중간_얼굴": {"top": 9, "bottom": 164},
        "아래_얼굴": {"top": 164, "bottom": 152},
        "왼쪽_눈": {"inner": 133, "outer": 33, "top": 159, "bottom": 145},
        "오른쪽_눈": {"inner": 362, "outer": 263, "top": 386, "bottom": 374},
        "코": {"top": 9, "bottom": 2, "left": 129, "right": 358},
        "입": {"left": 61, "right": 291, "top": 13, "bottom": 14},
        "턱선": {"left": 172, "right": 397, "center": 18}
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("🔧 얼굴 성형 시뮬레이터")
        self.root.geometry("1400x1550")
        
        # 이미지 관련 변수
        self.original_image = None
        self.current_image = None
        self.display_image = None
        
        # MediaPipe 얼굴 검출 초기화
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # 얼굴 특징점
        self.face_landmarks = None
        
        # 눈 효과 누적 파라미터
        self.eye_effect_strength = 0.0
        self.eye_effect_positions = None
        
        # 코 효과 누적 파라미터
        self.nose_effect_strength = 0.0
        self.nose_effect_position = None
        
        # 눈 형태 효과 누적 파라미터
        self.eye_width_strength = 0.0
        self.eye_height_strength = 0.0
        self.eye_shape_positions = None
        
        # 턱선 효과 누적 파라미터
        self.jaw_effect_strength = 0.0
        self.jaw_effect_position = None
        
        # 광대 효과 누적 파라미터
        self.cheek_effect_strength = 0.0
        self.cheek_effect_positions = None
        
        # 변형 도구 관련 변수 (백분율 기반)
        self.influence_radius_percent = 5.0  # 이미지 너비의 5%
        self.strength = 1.0
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # 줌 및 이동 파라미터
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.pan_x = 0
        self.pan_y = 0
        
        # 프리셋별 카운터
        self.lower_jaw_shot_count = 0
        self.middle_jaw_shot_count = 0
        self.cheek_shot_count = 0
        self.front_protusion_shot_count = 0
        self.back_slit_shot_count = 0
        
        # 마우스 상태
        self.is_dragging = False
        self.is_panning = False
        self.start_pos = None
        self.pan_start_pos = None
        self.last_mouse_pos = None
        
        # 히스토리 관리
        self.history = []
        self.max_history = 20
        
        # 랜드마크 표시 상태
        self.show_landmarks = False
        self.show_landmark_numbers = False
        
        
        # 랜드마크 그룹별 가시성 상태
        self.landmark_group_visibility = {
            "eyes": tk.BooleanVar(value=True),
            "iris": tk.BooleanVar(value=True),
            "eyelid_upper": tk.BooleanVar(value=True),
            "eyelid_lower": tk.BooleanVar(value=True),
            "eyelid_surround_upper": tk.BooleanVar(value=True),
            "eyelid_surround_lower": tk.BooleanVar(value=True),
            "eyelid_lower_surround_area": tk.BooleanVar(value=True),
            "eyelid_lower_area": tk.BooleanVar(value=True),
            "eyelid_upper_surround_area": tk.BooleanVar(value=True),
            "eyelid_upper_area": tk.BooleanVar(value=True),
            "nose_tip": tk.BooleanVar(value=True),
            "nose_bridge": tk.BooleanVar(value=True),
            "nose_wings": tk.BooleanVar(value=True),
            "nose_sides": tk.BooleanVar(value=True),
            "lip_upper": tk.BooleanVar(value=True),
            "lip_lower": tk.BooleanVar(value=True),
            "jawline": tk.BooleanVar(value=True),
            "jawline_area": tk.BooleanVar(value=True),
            "mouth_area": tk.BooleanVar(value=True),
            "nose_area": tk.BooleanVar(value=True),
            "nasolabial": tk.BooleanVar(value=True),
            "eyebrow_area": tk.BooleanVar(value=True),
            "eyebrows": tk.BooleanVar(value=True),
            "forehead": tk.BooleanVar(value=True),
            "glabella": tk.BooleanVar(value=True),
            "cheekbones": tk.BooleanVar(value=True),
            "cheek_area": tk.BooleanVar(value=True)
        }
        self.show_all_landmarks = False
        
        # 랜드마크 크기 설정
        self.landmark_point_size = 3  # 기본 점 크기
        self.landmark_font_size = 5  # 기본 폰트 크기 (50% 더 작게)
        
        # 선 연결 표시 상태
        self.show_landmark_lines = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 좌측 컨트롤 패널 (너비 확장)
        control_frame = ttk.Frame(main_frame, width=380)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # 제목
        title_label = ttk.Label(control_frame, text="🔧 얼굴 성형 시뮬레이터", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 파일 로드
        ttk.Button(control_frame, text="📁 이미지 열기", 
                  command=self.load_image).pack(pady=5, fill=tk.X)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 탭 노트북 (높이 최적화 - 300픽셀 증가)
        notebook_frame = ttk.Frame(control_frame, height=1250)
        notebook_frame.pack(fill=tk.X, pady=5)
        notebook_frame.pack_propagate(False)  # 높이 고정
        
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 얼굴 특징 탭
        self.features_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.features_frame, text="👤 얼굴 특징")
        self.setup_features_controls()
        
        # 자유 변형 탭 (스크롤 가능)
        warp_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(warp_tab_frame, text="🎨 자유 변형")
        
        # 스크롤 가능한 캔버스 생성
        warp_canvas = tk.Canvas(warp_tab_frame, highlightthickness=0)
        warp_scrollbar = ttk.Scrollbar(warp_tab_frame, orient="vertical", command=warp_canvas.yview)
        self.warp_frame = ttk.Frame(warp_canvas)
        
        # 캔버스 너비를 자동으로 맞추기
        def configure_scroll_region(event=None):
            warp_canvas.configure(scrollregion=warp_canvas.bbox("all"))
            # 캔버스 너비에 맞게 내부 프레임 너비 조정
            canvas_width = warp_canvas.winfo_width()
            if canvas_width > 1:
                warp_canvas.itemconfig(canvas_window, width=canvas_width-20)  # 스크롤바 여유공간
        
        self.warp_frame.bind("<Configure>", configure_scroll_region)
        warp_canvas.bind("<Configure>", configure_scroll_region)
        
        canvas_window = warp_canvas.create_window((0, 0), window=self.warp_frame, anchor="nw")
        warp_canvas.configure(yscrollcommand=warp_scrollbar.set)
        
        # 마우스 휠 스크롤 바인딩 (자유 변형 탭 전용)
        def _on_warp_mousewheel(event):
            warp_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # 마우스가 캔버스 위에 있을 때만 스크롤 동작
        def bind_warp_mousewheel(event):
            warp_canvas.bind_all("<MouseWheel>", _on_warp_mousewheel)
        def unbind_warp_mousewheel(event):
            warp_canvas.unbind_all("<MouseWheel>")
            
        warp_canvas.bind("<Enter>", bind_warp_mousewheel)
        warp_canvas.bind("<Leave>", unbind_warp_mousewheel)
        
        # 패킹
        warp_canvas.pack(side="left", fill="both", expand=True)
        warp_scrollbar.pack(side="right", fill="y")
        
        self.setup_warp_controls()
        
        # 공통 버튼들 (항상 하단에 표시)
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=(10, 5))
        
        # 공통 컨트롤 라벨
        ttk.Label(control_frame, text="🔧 공통 컨트롤", 
                 font=("Arial", 11, "bold")).pack(pady=(0, 5))
        
        # 히스토리 및 리셋 버튼
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(button_frame, text="↶ 뒤로가기", 
                  command=self.undo_last_action).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        ttk.Button(button_frame, text="🔄 원본 복원", 
                  command=self.reset_image).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 이미지 저장 버튼
        ttk.Button(control_frame, text="💾 이미지 저장", 
                  command=self.save_image).pack(pady=(5, 10), fill=tk.X)
        
        # 우측 이미지 캔버스
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#f0f0f0', cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 마우스 이벤트 바인딩
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-3>", self.on_pan_start)
        self.canvas.bind("<B3-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_pan_end)
        
    def setup_features_controls(self):
        """얼굴 특징 컨트롤 설정"""
        
        # 눈 효과
        ttk.Label(self.features_frame, text="👀 눈 효과:", 
                 font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        eye_frame = ttk.Frame(self.features_frame)
        eye_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(eye_frame, text="눈 크게", 
                  command=lambda: self.adjust_eyes(expand=True)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(eye_frame, text="눈 작게", 
                  command=lambda: self.adjust_eyes(expand=False)).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 눈 효과 상태 표시
        self.eye_status_label = ttk.Label(self.features_frame, text="눈 효과: 0.0", 
                                         foreground="gray", font=("Arial", 9))
        self.eye_status_label.pack(pady=2)
        
        # 눈 효과 리셋 버튼
        ttk.Button(self.features_frame, text="👁️ 눈 효과 리셋", 
                  command=self.reset_eye_effect).pack(pady=5, fill=tk.X)
        
        # 눈 형태 조절
        ttk.Label(self.features_frame, text="👀 눈 형태 조절:", 
                 font=("Arial", 11, "bold")).pack(pady=(15, 5))
        
        # 눈 가로 길이 조절
        ttk.Label(self.features_frame, text="↔️ 가로 길이:", 
                 font=("Arial", 9)).pack(pady=(5, 2))
        
        width_frame = ttk.Frame(self.features_frame)
        width_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(width_frame, text="-", width=3,
                  command=lambda: self.adjust_eye_width(-0.1)).pack(side=tk.LEFT)
        
        self.eye_width_var = tk.DoubleVar(value=0.0)
        self.eye_width_scale = ttk.Scale(width_frame, from_=-1.0, to=1.0, 
                                        variable=self.eye_width_var, orient=tk.HORIZONTAL,
                                        command=self.on_eye_width_change)
        self.eye_width_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(width_frame, text="+", width=3,
                  command=lambda: self.adjust_eye_width(0.1)).pack(side=tk.RIGHT)
        
        self.eye_width_label = ttk.Label(self.features_frame, text="가로: 0.0", 
                                        foreground="gray", font=("Arial", 8))
        self.eye_width_label.pack()
        
        # 눈 세로 길이 조절
        ttk.Label(self.features_frame, text="↕️ 세로 길이:", 
                 font=("Arial", 9)).pack(pady=(5, 2))
        
        height_frame = ttk.Frame(self.features_frame)
        height_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(height_frame, text="-", width=3,
                  command=lambda: self.adjust_eye_height(-0.1)).pack(side=tk.LEFT)
        
        self.eye_height_var = tk.DoubleVar(value=0.0)
        self.eye_height_scale = ttk.Scale(height_frame, from_=-1.0, to=1.0, 
                                         variable=self.eye_height_var, orient=tk.HORIZONTAL,
                                         command=self.on_eye_height_change)
        self.eye_height_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(height_frame, text="+", width=3,
                  command=lambda: self.adjust_eye_height(0.1)).pack(side=tk.RIGHT)
        
        self.eye_height_label = ttk.Label(self.features_frame, text="세로: 0.0", 
                                         foreground="gray", font=("Arial", 8))
        self.eye_height_label.pack()
        
        # 눈 형태 리셋 버튼
        ttk.Button(self.features_frame, text="👀 눈 형태 리셋", 
                  command=self.reset_eye_shape).pack(pady=5, fill=tk.X)
        
        # 코 효과
        ttk.Label(self.features_frame, text="👃 코 효과:", 
                 font=("Arial", 12, "bold")).pack(pady=(15, 5))
        
        nose_frame = ttk.Frame(self.features_frame)
        nose_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(nose_frame, text="코 크게", 
                  command=lambda: self.adjust_nose(expand=True)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(nose_frame, text="코 작게", 
                  command=lambda: self.adjust_nose(expand=False)).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 코 효과 상태 표시
        self.nose_status_label = ttk.Label(self.features_frame, text="코 효과: 0.0", 
                                          foreground="gray", font=("Arial", 9))
        self.nose_status_label.pack(pady=2)
        
        # 코 효과 리셋 버튼
        ttk.Button(self.features_frame, text="👃 코 효과 리셋", 
                  command=self.reset_nose_effect).pack(pady=5, fill=tk.X)
        
        # 턱선 효과
        ttk.Label(self.features_frame, text="🦴 턱선 효과:", 
                 font=("Arial", 12, "bold")).pack(pady=(15, 5))
        
        jaw_frame = ttk.Frame(self.features_frame)
        jaw_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(jaw_frame, text="턱선 강화", 
                  command=lambda: self.adjust_jawline(strengthen=True)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(jaw_frame, text="턱선 부드럽게", 
                  command=lambda: self.adjust_jawline(strengthen=False)).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 턱선 효과 상태 표시
        self.jaw_status_label = ttk.Label(self.features_frame, text="턱선 효과: 0.0", 
                                         foreground="gray", font=("Arial", 9))
        self.jaw_status_label.pack(pady=2)
        
        # 턱선 효과 리셋 버튼
        ttk.Button(self.features_frame, text="🦴 턱선 효과 리셋", 
                  command=self.reset_jaw_effect).pack(pady=5, fill=tk.X)
        
        # 광대 효과
        ttk.Label(self.features_frame, text="😊 광대 효과:", 
                 font=("Arial", 12, "bold")).pack(pady=(15, 5))
        
        cheek_frame = ttk.Frame(self.features_frame)
        cheek_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(cheek_frame, text="광대 축소", 
                  command=lambda: self.adjust_cheekbones(reduce=True)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(cheek_frame, text="광대 확대", 
                  command=lambda: self.adjust_cheekbones(reduce=False)).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 광대 효과 상태 표시
        self.cheek_status_label = ttk.Label(self.features_frame, text="광대 효과: 0.0", 
                                           foreground="gray", font=("Arial", 9))
        self.cheek_status_label.pack(pady=2)
        
        # 광대 효과 리셋 버튼
        ttk.Button(self.features_frame, text="😊 광대 효과 리셋", 
                  command=self.reset_cheek_effect).pack(pady=5, fill=tk.X)
        
        # 얼굴 검출 상태
        ttk.Separator(self.features_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        self.face_status_label = ttk.Label(self.features_frame, text="얼굴을 검출하세요", 
                                          foreground="gray")
        self.face_status_label.pack(pady=5)
        
    def setup_warp_controls(self):
        """자유 변형 도구 컨트롤 설정"""
        # 영향 반경 조절
        ttk.Label(self.warp_frame, text="🎯 영향 반경:", 
                 font=("Arial", 10, "bold")).pack(pady=(10, 5))
        
        radius_frame = ttk.Frame(self.warp_frame)
        radius_frame.pack(fill=tk.X, pady=5)
        
        self.radius_var = tk.DoubleVar(value=5.0)
        ttk.Scale(radius_frame, from_=1.0, to=50.0, 
                 variable=self.radius_var, orient=tk.HORIZONTAL,
                 command=self.update_radius).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.radius_label = ttk.Label(radius_frame, text="5.0% (80px)", width=12)
        self.radius_label.pack(side=tk.RIGHT)
        
        # 변형 강도 조절
        ttk.Label(self.warp_frame, text="💪 변형 강도:", 
                 font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        strength_frame = ttk.Frame(self.warp_frame)
        strength_frame.pack(fill=tk.X, pady=5)
        
        self.strength_var = tk.DoubleVar(value=1.0)
        ttk.Scale(strength_frame, from_=0.1, to=3.0, 
                 variable=self.strength_var, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        strength_value_label = ttk.Label(strength_frame, text="1.0x", width=6)
        strength_value_label.pack(side=tk.RIGHT)
        
        def update_strength_label(*args):
            strength_value_label.config(text=f"{self.strength_var.get():.1f}x")
        self.strength_var.trace('w', update_strength_label)
        
        # 구분선
        ttk.Separator(self.warp_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 프리셋 섹션
        ttk.Label(self.warp_frame, text="⚡ 빠른 프리셋:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        preset_frame = ttk.Frame(self.warp_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        
        # 아래턱 100샷+ 프리셋
        lower_jaw_frame = ttk.Frame(preset_frame)
        lower_jaw_frame.pack(fill=tk.X, pady=2)
        ttk.Button(lower_jaw_frame, text="💉 아래턱 100샷+", 
                  command=self.apply_lower_jaw_100shot_preset).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lower_jaw_counter_label = ttk.Label(lower_jaw_frame, text="", 
                                               font=("Arial", 8), foreground="blue")
        self.lower_jaw_counter_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 중간턱 100샷+ 프리셋
        middle_jaw_frame = ttk.Frame(preset_frame)
        middle_jaw_frame.pack(fill=tk.X, pady=2)
        ttk.Button(middle_jaw_frame, text="💉 중간턱 100샷+", 
                  command=self.apply_middle_jaw_100shot_preset).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.middle_jaw_counter_label = ttk.Label(middle_jaw_frame, text="", 
                                                font=("Arial", 8), foreground="blue")
        self.middle_jaw_counter_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 볼 100샷+ 프리셋
        cheek_frame = ttk.Frame(preset_frame)
        cheek_frame.pack(fill=tk.X, pady=2)
        ttk.Button(cheek_frame, text="💉 볼 100샷+", 
                  command=self.apply_cheek_100shot_preset).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.cheek_counter_label = ttk.Label(cheek_frame, text="", 
                                           font=("Arial", 8), foreground="blue")
        self.cheek_counter_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 앞튀임+ 프리셋
        front_protusion_frame = ttk.Frame(preset_frame)
        front_protusion_frame.pack(fill=tk.X, pady=2)
        ttk.Button(front_protusion_frame, text="💉 앞튀임+", 
                  command=self.apply_front_protusion_100shot_preset).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.front_protusion_counter_label = ttk.Label(front_protusion_frame, text="", 
                                                     font=("Arial", 8), foreground="blue")
        self.front_protusion_counter_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 뒷트임+ 프리셋
        back_slit_frame = ttk.Frame(preset_frame)
        back_slit_frame.pack(fill=tk.X, pady=2)
        ttk.Button(back_slit_frame, text="💉 뒷트임+", 
                  command=self.apply_back_slit_100shot_preset).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.back_slit_counter_label = ttk.Label(back_slit_frame, text="", 
                                               font=("Arial", 8), foreground="blue")
        self.back_slit_counter_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 시각화 옵션
        self.show_preset_visualization = tk.BooleanVar(value=True)
        ttk.Checkbutton(preset_frame, text="프리셋 시각화 표시", 
                       variable=self.show_preset_visualization).pack(fill=tk.X, pady=2)
        
        # Before/After 비교 버튼
        ttk.Button(preset_frame, text="📷 Before / After 비교", 
                  command=self.show_before_after_comparison).pack(fill=tk.X, pady=2)
        
        # 황금비율 분석 버튼
        ttk.Button(preset_frame, text="📊 얼굴 황금비율 분석", 
                  command=self.analyze_golden_ratio).pack(fill=tk.X, pady=2)
        
        # 구분선
        ttk.Separator(self.warp_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 랜드마크 표시 토글
        ttk.Label(self.warp_frame, text="🎯 랜드마크 표시:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        landmark_frame = ttk.Frame(self.warp_frame)
        landmark_frame.pack(fill=tk.X, pady=5)
        
        self.landmark_button = ttk.Button(landmark_frame, text="👁️ 랜드마크 보기", 
                                        command=self.toggle_landmarks)
        self.landmark_button.pack(fill=tk.X, pady=2)
        
        # 랜드마크 번호 표시 버튼
        self.landmark_numbers_button = ttk.Button(landmark_frame, text="🔢 번호 보기", 
                                                command=self.toggle_landmark_numbers)
        self.landmark_numbers_button.pack(fill=tk.X, pady=2)
        
        # 선 연결 표시 버튼
        self.landmark_lines_button = ttk.Button(landmark_frame, text="📏 선 연결 보기", 
                                              command=self.toggle_landmark_lines)
        self.landmark_lines_button.pack(fill=tk.X, pady=2)
        
        
        # 새로고침 버튼
        ttk.Button(landmark_frame, text="🔄 새로고침", 
                  command=self.refresh_landmarks).pack(fill=tk.X, pady=2)
        
        # 랜드마크 크기 조절 (토글 버튼 바로 아래로 이동)
        size_frame = ttk.LabelFrame(landmark_frame, text="🎯 크기 조절", padding=5)
        size_frame.pack(fill=tk.X, pady=5)
        
        # 점 크기 조절
        ttk.Label(size_frame, text="점 크기:", font=("Arial", 9)).pack(anchor=tk.W)
        point_size_frame = ttk.Frame(size_frame)
        point_size_frame.pack(fill=tk.X, pady=2)
        
        self.point_size_var = tk.IntVar(value=self.landmark_point_size)
        ttk.Scale(point_size_frame, from_=1, to=8, 
                 variable=self.point_size_var, orient=tk.HORIZONTAL,
                 command=self.update_point_size).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.point_size_label = ttk.Label(point_size_frame, text=f"{self.landmark_point_size}px", width=4)
        self.point_size_label.pack(side=tk.RIGHT)
        
        # 폰트 크기 조절
        ttk.Label(size_frame, text="번호 크기:", font=("Arial", 9)).pack(anchor=tk.W, pady=(5, 0))
        font_size_frame = ttk.Frame(size_frame)
        font_size_frame.pack(fill=tk.X, pady=2)
        
        self.font_size_var = tk.IntVar(value=self.landmark_font_size)
        ttk.Scale(font_size_frame, from_=3, to=10, 
                 variable=self.font_size_var, orient=tk.HORIZONTAL,
                 command=self.update_font_size).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.font_size_label = ttk.Label(font_size_frame, text=f"{self.landmark_font_size}pt", width=4)
        self.font_size_label.pack(side=tk.RIGHT)
        
        
        # 랜드마크 그룹 선택 프레임
        group_frame = ttk.LabelFrame(landmark_frame, text="🎨 부위별 표시", padding=5)
        group_frame.pack(fill=tk.X, pady=5)
        
        # 전체 선택/해제 버튼
        select_all_frame = ttk.Frame(group_frame)
        select_all_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(select_all_frame, text="✅ 전체 선택", width=12,
                  command=self.select_all_groups).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(select_all_frame, text="❌ 전체 해제", width=12,
                  command=self.deselect_all_groups).pack(side=tk.RIGHT, padx=(2, 0))
        
        # 그룹별 토글 버튼들
        self.create_landmark_group_buttons(group_frame)
        
        # 구분선
        ttk.Separator(self.warp_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 변형 모드 선택
        ttk.Label(self.warp_frame, text="🔧 변형 모드:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        self.warp_mode = tk.StringVar(value="pull")
        mode_frame = ttk.Frame(self.warp_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(mode_frame, text="당기기", variable=self.warp_mode, 
                       value="pull").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="밀어내기", variable=self.warp_mode, 
                       value="push").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="확대", variable=self.warp_mode, 
                       value="expand").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="축소", variable=self.warp_mode, 
                       value="shrink").pack(anchor=tk.W)
        
        # 구분선
        ttk.Separator(self.warp_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 줌 컨트롤
        ttk.Label(self.warp_frame, text="🔍 줌 컨트롤:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        zoom_frame = ttk.Frame(self.warp_frame)
        zoom_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(zoom_frame, text="🔍-", width=6,
                  command=self.zoom_out).pack(side=tk.LEFT, padx=(0, 2))
        
        self.zoom_label = ttk.Label(zoom_frame, text="100%", width=8)
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(zoom_frame, text="🔍+", width=6,
                  command=self.zoom_in).pack(side=tk.LEFT, padx=(2, 0))
        
        ttk.Button(self.warp_frame, text="🎯 줌 리셋", 
                  command=self.reset_zoom).pack(pady=5, fill=tk.X)
        
        # 사용법 안내
        instructions_text = """
🖱️ 사용법:
• 좌클릭 후 드래그로 변형
• 우클릭 후 드래그로 이미지 이동
• 마우스 휠로 줌 인/아웃

💡 팁:
• 줌 인 후 세밀한 작업 가능
• 뒤로가기로 이전 상태 복원
• 특징별 조절은 첫 번째 탭 활용
        """
        
        ttk.Label(self.warp_frame, text=instructions_text, 
                 justify=tk.LEFT, wraplength=280,
                 font=("Arial", 9)).pack(pady=(15, 0))
    
    def load_image(self):
        """이미지 파일 로드"""
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[("이미지 파일", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff")]
        )
        
        if file_path:
            try:
                # OpenCV로 이미지 로드
                self.original_image = cv2.imread(file_path)
                self.original_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
                
                # 현재 이미지를 원본으로 초기화
                self.current_image = self.original_image.copy()
                
                # 프리셋 카운터 리셋
                self.lower_jaw_shot_count = 0
                self.middle_jaw_shot_count = 0
                self.cheek_shot_count = 0
                self.front_protusion_shot_count = 0
                self.back_slit_shot_count = 0
                self.lower_jaw_counter_label.config(text="")
                self.middle_jaw_counter_label.config(text="")
                self.cheek_counter_label.config(text="")
                self.front_protusion_counter_label.config(text="")
                self.back_slit_counter_label.config(text="")
                
                # 캔버스에 맞게 조정 및 표시
                self.fit_and_display_image()
                
                # 줌 및 이동 초기화
                self.zoom_factor = 1.0
                self.pan_x = 0
                self.pan_y = 0
                self.update_zoom_label()
                
                # 히스토리 초기화
                self.history = []
                
                # 모든 효과 누적 파라미터 초기화
                self.reset_all_effects()
                
                # 얼굴 검출
                self.detect_face()
                
            except Exception as e:
                print(f"이미지 로드 실패: {str(e)}")
    
    def detect_face(self):
        """얼굴 검출 및 특징점 추출"""
        if self.current_image is None:
            return
            
        try:
            # MediaPipe로 얼굴 검출
            results = self.face_mesh.process(self.current_image)
            
            if results.multi_face_landmarks:
                self.face_landmarks = results.multi_face_landmarks[0]
                self.face_status_label.config(text="✅ 얼굴 검출 완료", foreground="green")
            else:
                self.face_landmarks = None
                self.face_status_label.config(text="❌ 얼굴을 찾을 수 없음", foreground="red")
                
        except Exception as e:
            print(f"얼굴 검출 실패: {str(e)}")
            self.face_landmarks = None
            self.face_status_label.config(text="❌ 얼굴 검출 실패", foreground="red")
    
    def fit_and_display_image(self):
        """이미지를 캔버스에 맞게 조정하여 표시"""
        if self.current_image is None:
            return
            
        # 캔버스 크기 가져오기
        self.canvas.update()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1:
            self.root.after(100, self.fit_and_display_image)
            return
        
        img_height, img_width = self.current_image.shape[:2]
        
        # 스케일 계산
        margin = 30
        scale_x = (canvas_width - margin) / img_width
        scale_y = (canvas_height - margin) / img_height
        self.scale_factor = min(scale_x, scale_y, 1.0)
        
        # 새로운 크기 및 위치 계산
        new_width = int(img_width * self.scale_factor)
        new_height = int(img_height * self.scale_factor)
        self.offset_x = (canvas_width - new_width) // 2
        self.offset_y = (canvas_height - new_height) // 2
        
        # 화면에 표시
        self.update_display()
    
    def update_display(self):
        """화면에 이미지 업데이트"""
        if self.current_image is None:
            return
            
        try:
            # 표시용 이미지 리사이징
            img_height, img_width = self.current_image.shape[:2]
            display_width = int(img_width * self.scale_factor * self.zoom_factor)
            display_height = int(img_height * self.scale_factor * self.zoom_factor)
            
            display_img = cv2.resize(self.current_image, (display_width, display_height))
            
            # PIL로 변환
            pil_image = Image.fromarray(display_img)
            self.display_image = ImageTk.PhotoImage(pil_image)
            
            # 캔버스에 표시
            self.canvas.delete("image")
            self.canvas.create_image(
                self.offset_x + self.pan_x, self.offset_y + self.pan_y, 
                anchor=tk.NW, image=self.display_image, tags="image"
            )
            
            # 랜드마크 표시 (활성화된 경우)
            if self.show_landmarks:
                self.draw_landmarks()
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def adjust_eyes(self, expand=True):
        """눈 확대/축소 효과 - 누적 방식으로 화질 보존"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        # 첫 번째 호출시에만 히스토리 저장
        if self.eye_effect_strength == 0.0:
            self.save_to_history()
        
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            # 눈 위치 저장 (첫 번째 호출시에만)
            if self.eye_effect_positions is None:
                left_eye_center = self.face_landmarks.landmark[159]  # 왼쪽 눈
                right_eye_center = self.face_landmarks.landmark[386]  # 오른쪽 눈
                
                self.eye_effect_positions = [
                    (int(left_eye_center.x * img_width), int(left_eye_center.y * img_height)),
                    (int(right_eye_center.x * img_width), int(right_eye_center.y * img_height))
                ]
            
            # 누적 강도 업데이트
            step = 0.1
            if expand:
                self.eye_effect_strength += step
            else:
                self.eye_effect_strength -= step
            
            # 강도 제한 (-1.0 ~ 1.0)
            self.eye_effect_strength = max(-1.0, min(1.0, self.eye_effect_strength))
            
            # 원본 이미지에서 누적된 효과 적용
            if abs(self.eye_effect_strength) > 0.01:
                if len(self.history) > 0:
                    base_image = self.history[-1].copy()
                else:
                    base_image = self.original_image.copy()
                
                result_image = base_image.copy()
                for eye_center in self.eye_effect_positions:
                    if self.eye_effect_strength > 0:
                        result_image = self.magnify_area(
                            result_image, eye_center, radius=40, 
                            strength=abs(self.eye_effect_strength), expand=True
                        )
                    else:
                        result_image = self.magnify_area(
                            result_image, eye_center, radius=40, 
                            strength=abs(self.eye_effect_strength), expand=False
                        )
                
                self.current_image = result_image
            else:
                if len(self.history) > 0:
                    self.current_image = self.history[-1].copy()
                else:
                    self.current_image = self.original_image.copy()
            
            self.update_display()
            self.update_eye_status_label()
            
        except Exception as e:
            print(f"눈 효과 적용 실패: {str(e)}")
    
    def magnify_area(self, image, center, radius=40, strength=0.1, expand=True):
        """특정 영역 확대/축소"""
        img_height, img_width = image.shape[:2]
        center_x, center_y = center
        
        # 확대/축소 맵 생성
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        # 중심점으로부터의 거리
        dx = map_x - center_x
        dy = map_y - center_y
        distance = np.sqrt(dx*dx + dy*dy)
        
        # 영향받는 영역
        mask = distance < radius
        
        # 확대 계수 계산
        if expand:
            scale_factor = 1 - strength * (1 - distance / radius)
        else:
            scale_factor = 1 + strength * (1 - distance / radius)
        scale_factor = np.maximum(scale_factor, 0.1)
        
        # 새로운 좌표 계산
        new_x = center_x + dx * scale_factor
        new_y = center_y + dy * scale_factor
        
        # 영향받는 영역만 업데이트
        map_x = np.where(mask, new_x, map_x)
        map_y = np.where(mask, new_y, map_y)
        
        # 경계 클리핑
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        # 리맵핑 적용 - 고품질 보간 사용
        return cv2.remap(image, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    
    def adjust_nose(self, expand=True):
        """코 확대/축소 효과"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        if self.nose_effect_strength == 0.0:
            self.save_to_history()
        
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            if self.nose_effect_position is None:
                nose_tip = self.face_landmarks.landmark[1]
                nose_center = self.face_landmarks.landmark[2]
                
                nose_x = int((nose_tip.x + nose_center.x) / 2 * img_width)
                nose_y = int((nose_tip.y + nose_center.y) * 0.94 / 2 * img_height)
                
                self.nose_effect_position = (nose_x, nose_y)
            
            step = 0.1
            if expand:
                self.nose_effect_strength += step
            else:
                self.nose_effect_strength -= step
            
            self.nose_effect_strength = max(-1.0, min(1.0, self.nose_effect_strength))
            
            if abs(self.nose_effect_strength) > 0.01:
                if len(self.history) > 0:
                    base_image = self.history[-1].copy()
                else:
                    base_image = self.original_image.copy()
                
                result_image = base_image.copy()
                if self.nose_effect_strength > 0:
                    result_image = self.magnify_area(
                        result_image, self.nose_effect_position, radius=50, 
                        strength=abs(self.nose_effect_strength), expand=True
                    )
                else:
                    result_image = self.magnify_area(
                        result_image, self.nose_effect_position, radius=50, 
                        strength=abs(self.nose_effect_strength), expand=False
                    )
                
                self.current_image = result_image
            else:
                if len(self.history) > 0:
                    self.current_image = self.history[-1].copy()
                else:
                    self.current_image = self.original_image.copy()
            
            self.update_display()
            self.update_nose_status_label()
            
        except Exception as e:
            print(f"코 효과 적용 실패: {str(e)}")
    
    def adjust_jawline(self, strengthen=True):
        """턱선 강화/부드럽게 효과"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        if self.jaw_effect_strength == 0.0:
            self.save_to_history()
        
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            if self.jaw_effect_position is None:
                # 턱 끝점 (MediaPipe landmark 175)
                jaw_point = self.face_landmarks.landmark[175]
                self.jaw_effect_position = (int(jaw_point.x * img_width), int(jaw_point.y * img_height))
            
            step = 0.1
            if strengthen:
                self.jaw_effect_strength += step
            else:
                self.jaw_effect_strength -= step
            
            self.jaw_effect_strength = max(-1.0, min(1.0, self.jaw_effect_strength))
            
            if abs(self.jaw_effect_strength) > 0.01:
                if len(self.history) > 0:
                    base_image = self.history[-1].copy()
                else:
                    base_image = self.original_image.copy()
                
                result_image = base_image.copy()
                if self.jaw_effect_strength > 0:  # 강화
                    result_image = self.magnify_area(
                        result_image, self.jaw_effect_position, radius=60, 
                        strength=abs(self.jaw_effect_strength), expand=False
                    )
                else:  # 부드럽게
                    result_image = self.magnify_area(
                        result_image, self.jaw_effect_position, radius=60, 
                        strength=abs(self.jaw_effect_strength), expand=True
                    )
                
                self.current_image = result_image
            else:
                if len(self.history) > 0:
                    self.current_image = self.history[-1].copy()
                else:
                    self.current_image = self.original_image.copy()
            
            self.update_display()
            self.update_jaw_status_label()
            
        except Exception as e:
            print(f"턱선 효과 적용 실패: {str(e)}")
    
    def adjust_cheekbones(self, reduce=True):
        """광대 축소/확대 효과"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        if self.cheek_effect_strength == 0.0:
            self.save_to_history()
        
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            if self.cheek_effect_positions is None:
                # 좌우 광대뼈 위치 (MediaPipe landmarks)
                left_cheek = self.face_landmarks.landmark[116]
                right_cheek = self.face_landmarks.landmark[345]
                
                self.cheek_effect_positions = [
                    (int(left_cheek.x * img_width), int(left_cheek.y * img_height)),
                    (int(right_cheek.x * img_width), int(right_cheek.y * img_height))
                ]
            
            step = 0.1
            if reduce:
                self.cheek_effect_strength += step
            else:
                self.cheek_effect_strength -= step
            
            self.cheek_effect_strength = max(-1.0, min(1.0, self.cheek_effect_strength))
            
            if abs(self.cheek_effect_strength) > 0.01:
                if len(self.history) > 0:
                    base_image = self.history[-1].copy()
                else:
                    base_image = self.original_image.copy()
                
                result_image = base_image.copy()
                for cheek_center in self.cheek_effect_positions:
                    if self.cheek_effect_strength > 0:  # 축소
                        result_image = self.magnify_area(
                            result_image, cheek_center, radius=55, 
                            strength=abs(self.cheek_effect_strength), expand=False
                        )
                    else:  # 확대
                        result_image = self.magnify_area(
                            result_image, cheek_center, radius=55, 
                            strength=abs(self.cheek_effect_strength), expand=True
                        )
                
                self.current_image = result_image
            else:
                if len(self.history) > 0:
                    self.current_image = self.history[-1].copy()
                else:
                    self.current_image = self.original_image.copy()
            
            self.update_display()
            self.update_cheek_status_label()
            
        except Exception as e:
            print(f"광대 효과 적용 실패: {str(e)}")
    
    # 눈 형태 조절 관련 메서드들 (integrated_app.py에서 가져옴)
    def adjust_eye_width(self, value):
        """눈 가로 길이 조절"""
        if self.face_landmarks is None:
            return
        
        if self.eye_width_strength == 0.0 and value != 0.0:
            self.save_to_history()
            
        old_value = self.eye_width_strength
        self.eye_width_strength += value
        self.eye_width_strength = max(-1.0, min(1.0, self.eye_width_strength))
        
        if abs(self.eye_width_strength - old_value) > 0.01:
            self.apply_eye_shape_effects()
            self.update_eye_shape_labels()
    
    def adjust_eye_height(self, value):
        """눈 세로 길이 조절"""
        if self.face_landmarks is None:
            return
        
        if self.eye_height_strength == 0.0 and value != 0.0:
            self.save_to_history()
            
        old_value = self.eye_height_strength
        self.eye_height_strength += value
        self.eye_height_strength = max(-1.0, min(1.0, self.eye_height_strength))
        
        if abs(self.eye_height_strength - old_value) > 0.01:
            self.apply_eye_shape_effects()
            self.update_eye_shape_labels()
    
    def on_eye_width_change(self, value):
        """눈 가로 길이 슬라이더 변경 이벤트"""
        if self.face_landmarks is None:
            return
            
        new_value = float(value)
        if abs(new_value - self.eye_width_strength) > 0.01:
            if self.eye_width_strength == 0.0 and new_value != 0.0:
                self.save_to_history()
                
            self.eye_width_strength = new_value
            self.apply_eye_shape_effects()
            self.update_eye_shape_labels()
    
    def on_eye_height_change(self, value):
        """눈 세로 길이 슬라이더 변경 이벤트"""
        if self.face_landmarks is None:
            return
            
        new_value = float(value)
        if abs(new_value - self.eye_height_strength) > 0.01:
            if self.eye_height_strength == 0.0 and new_value != 0.0:
                self.save_to_history()
                
            self.eye_height_strength = new_value
            self.apply_eye_shape_effects()
            self.update_eye_shape_labels()
    
    def apply_eye_shape_effects(self):
        """눈 형태 효과 적용"""
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            if self.eye_shape_positions is None:
                left_eye_center_top = self.face_landmarks.landmark[159]
                left_eye_center_bottom = self.face_landmarks.landmark[145]
                right_eye_center_top = self.face_landmarks.landmark[386]
                right_eye_center_bottom = self.face_landmarks.landmark[374]
                
                self.eye_shape_positions = [
                    (int((left_eye_center_top.x + left_eye_center_bottom.x) / 2 * img_width), 
                     int((left_eye_center_top.y + left_eye_center_bottom.y) / 2 * img_height)),
                    (int((right_eye_center_top.x + right_eye_center_bottom.x) / 2 * img_width), 
                     int((right_eye_center_top.y + right_eye_center_bottom.y) / 2 * img_height)),
                ]
            
            if len(self.history) > 0:
                base_image = self.history[-1].copy()
            else:
                base_image = self.original_image.copy()
            
            if abs(self.eye_width_strength) > 0.01 or abs(self.eye_height_strength) > 0.01:
                result_image = base_image.copy()
                
                for eye_center in self.eye_shape_positions:
                    result_image = self.elliptical_warp_natural(
                        result_image, eye_center,
                        width_strength=self.eye_width_strength,
                        height_strength=self.eye_height_strength
                    )
                
                self.current_image = result_image
            else:
                self.current_image = base_image
            
            self.update_display()
            
        except Exception as e:
            print(f"눈 형태 효과 적용 실패: {str(e)}")
    
    def elliptical_warp_natural(self, image, eye_center, width_strength=0.0, height_strength=0.0):
        """자연스러운 눈 형태 변형"""
        img_height, img_width = image.shape[:2]
        center_x, center_y = eye_center
        
        result_image = image.copy()
        
        # 가로 방향 변형
        if width_strength != 0.0:
            is_left_eye = center_x < img_width / 2
            
            if is_left_eye:
                if self.face_landmarks:
                    outer_landmark = self.face_landmarks.landmark[33]
                    inner_landmark = self.face_landmarks.landmark[133]
                    outer_pos = (int(outer_landmark.x * img_width), int(outer_landmark.y * img_height))
                    inner_pos = (int(inner_landmark.x * img_width), int(inner_landmark.y * img_height))
                else:
                    outer_pos = (center_x - 25, center_y)
                    inner_pos = (center_x + 15, center_y)
            else:
                if self.face_landmarks:
                    outer_landmark = self.face_landmarks.landmark[263]
                    inner_landmark = self.face_landmarks.landmark[362]
                    outer_pos = (int(outer_landmark.x * img_width), int(outer_landmark.y * img_height))
                    inner_pos = (int(inner_landmark.x * img_width), int(inner_landmark.y * img_height))
                else:
                    outer_pos = (center_x + 25, center_y)
                    inner_pos = (center_x - 15, center_y)
            
            result_image = self.apply_eye_width_pull_warp(result_image, outer_pos, inner_pos, 
                                                         width_strength, is_left_eye)
        
        # 세로 방향 변형
        if height_strength != 0.0:
            result_image = self.apply_eye_height_warp(result_image, eye_center, height_strength)
        
        return result_image
    
    def apply_eye_width_pull_warp(self, image, outer_pos, inner_pos, width_strength, is_left_eye):
        """눈 가로 길이 조절"""
        img_height, img_width = image.shape[:2]
        
        pull_distance = abs(width_strength) * 10
        
        if width_strength > 0:
            if is_left_eye:
                start_pos = outer_pos
                end_pos = (max(0, outer_pos[0] - pull_distance), outer_pos[1])
            else:
                start_pos = outer_pos
                end_pos = (min(img_width-1, outer_pos[0] + pull_distance), outer_pos[1])
        else:
            if is_left_eye:
                start_pos = outer_pos
                end_pos = (min(img_width-1, outer_pos[0] + pull_distance), outer_pos[1])
            else:
                start_pos = outer_pos
                end_pos = (max(0, outer_pos[0] - pull_distance), outer_pos[1])
        
        temp_image = image.copy()
        self.current_image = temp_image
        
        original_radius_percent = self.influence_radius_percent
        self.influence_radius_percent = 2.0  # 임시로 2%로 설정
        
        self.apply_pull_warp_with_params(start_pos[0], start_pos[1], end_pos[0], end_pos[1], 
                                       min(abs(width_strength) * 2.0, 3.0))
        
        result = self.current_image.copy()
        self.influence_radius_percent = original_radius_percent
        
        return result
    
    def apply_eye_height_warp(self, image, eye_center, height_strength):
        """눈 세로 길이 조절"""
        img_height, img_width = image.shape[:2]
        center_x, center_y = eye_center
        
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        dx = map_x - center_x
        dy = map_y - center_y
        distance = np.sqrt(dx*dx + dy*dy)
        
        radius = 50
        mask = distance < radius
        
        pupil_radius = 18
        pupil_mask = distance < pupil_radius
        
        strength_map_y = np.zeros_like(distance)
        valid_dist = distance[mask]
        
        if len(valid_dist) > 0:
            strength_map_y[mask] = (1 - valid_dist / radius) ** 1.2
            strength_map_y[pupil_mask] *= 0.2
            strength_map_y *= abs(height_strength)
            
            if height_strength > 0:
                scale_factor_y = 1 - strength_map_y
            else:
                scale_factor_y = 1 + strength_map_y
            
            new_y = center_y + dy * scale_factor_y
            map_y = np.where(mask, new_y, map_y)
        
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        return cv2.remap(image, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    
    def apply_pull_warp_with_params(self, start_x, start_y, end_x, end_y, strength, influence_radius_px=None, ellipse_ratio=None):
        """파라미터를 지정한 당기기 변형 (타원형 영향반경 지원)"""
        if self.current_image is None:
            return
            
        img_height, img_width = self.current_image.shape[:2]
        
        start_x = max(0, min(start_x, img_width - 1))
        start_y = max(0, min(start_y, img_height - 1))
        end_x = max(0, min(end_x, img_width - 1))
        end_y = max(0, min(end_y, img_height - 1))
        
        dx = start_x - end_x
        dy = start_y - end_y
        
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return
        
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        pixel_dx = map_x - start_x
        pixel_dy = map_y - start_y
        
        # 커스텀 영향반경 사용 또는 기본값
        if influence_radius_px is not None:
            influence_radius = influence_radius_px
            print(f"커스텀 영향반경 사용: {influence_radius}px")
        else:
            influence_radius = self.get_influence_radius_pixels()
            print(f"기본 영향반경 사용: {influence_radius}px")
        
        # 타원형 영향반경 계산
        if ellipse_ratio is not None:
            # 타원형: 가로 반경 = influence_radius, 세로 반경 = influence_radius * ellipse_ratio
            ellipse_x_radius = influence_radius
            ellipse_y_radius = influence_radius * ellipse_ratio
            
            # 타원 방정식: (x/a)² + (y/b)² < 1
            ellipse_dist = (pixel_dx / ellipse_x_radius) ** 2 + (pixel_dy / ellipse_y_radius) ** 2
            mask = ellipse_dist < 1.0
            
            # 타원형 거리 계산 (정규화된 타원 거리)
            pixel_dist = np.sqrt(ellipse_dist) * influence_radius
            print(f"타원형 영향반경 사용: 가로 {ellipse_x_radius}px, 세로 {ellipse_y_radius}px")
        else:
            # 원형 영향반경 (기존 방식)
            pixel_dist = np.sqrt(pixel_dx*pixel_dx + pixel_dy*pixel_dy)
            mask = pixel_dist < influence_radius
        
        strength_map = np.zeros_like(pixel_dist)
        valid_dist = pixel_dist[mask]
        
        if len(valid_dist) > 0:
            strength_map[mask] = (1 - valid_dist / influence_radius) ** 2
            # 커스텀 강도 사용
            strength_map[mask] *= strength
            print(f"실제 적용 강도: {strength}")
            
            map_x[mask] += dx * strength_map[mask]
            map_y[mask] += dy * strength_map[mask]
        
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        self.current_image = cv2.remap(
            self.current_image, map_x, map_y, 
            cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
        )
    
    # 자유 변형 도구 관련 메서드들
    def screen_to_image_coords(self, screen_x, screen_y):
        """화면 좌표를 이미지 좌표로 변환"""
        img_x = ((screen_x - self.offset_x - self.pan_x) / self.scale_factor) / self.zoom_factor
        img_y = ((screen_y - self.offset_y - self.pan_y) / self.scale_factor) / self.zoom_factor
        return int(img_x), int(img_y)
    
    def on_mouse_move(self, event):
        """마우스 이동 이벤트"""
        if self.current_image is None or self.is_dragging or self.is_panning:
            return
        
        # 마지막 마우스 위치 저장
        self.last_mouse_pos = (event.x, event.y)
        
        # 자유 변형 탭이 활성화된 경우에만 영향 범위 표시
        if self.notebook.index(self.notebook.select()) == 1:
            self.update_influence_circle(event.x, event.y)
            # 마우스 이동 시 프리셋 시각화 제거
            self.clear_preset_visualization()
    
    def update_influence_circle(self, x, y):
        """영향 범위 원 업데이트"""
        self.canvas.delete("preview_circle")
        radius_pixels = self.get_influence_radius_pixels()
        radius_screen = radius_pixels * self.scale_factor * self.zoom_factor
        
        self.canvas.create_oval(
            x - radius_screen, y - radius_screen,
            x + radius_screen, y + radius_screen,
            outline="#ff6b6b", width=2, dash=(5, 5), tags="preview_circle"
        )
    
    def on_mouse_down(self, event):
        """마우스 다운 이벤트"""
        if self.current_image is None:
            return
        
        # 자유 변형 탭이 활성화된 경우에만 변형 모드
        if self.notebook.index(self.notebook.select()) == 1:
            self.start_pos = (event.x, event.y)
            self.is_dragging = True
            
            self.canvas.delete("preview_circle")
            self.update_influence_circle(event.x, event.y)
            
            # 드래그 중에는 다른 색상으로 표시
            self.canvas.delete("preview_circle")
            radius_pixels = self.get_influence_radius_pixels()
            radius_screen = radius_pixels * self.scale_factor * self.zoom_factor
            
            self.canvas.create_oval(
                event.x - radius_screen, event.y - radius_screen,
                event.x + radius_screen, event.y + radius_screen,
                outline="#ffc107", width=3, tags="warp_circle"
            )
    
    def on_mouse_drag(self, event):
        """마우스 드래그 이벤트"""
        if not self.is_dragging or self.start_pos is None:
            return
            
        self.canvas.delete("direction_line")
        self.canvas.create_line(
            self.start_pos[0], self.start_pos[1],
            event.x, event.y,
            fill="#ffc107", width=3, tags="direction_line"
        )
    
    def on_mouse_up(self, event):
        """마우스 업 이벤트"""
        if not self.is_dragging or self.start_pos is None:
            return
        
        self.save_to_history()
        
        start_img_x, start_img_y = self.screen_to_image_coords(self.start_pos[0], self.start_pos[1])
        end_img_x, end_img_y = self.screen_to_image_coords(event.x, event.y)
        
        self.apply_warp(start_img_x, start_img_y, end_img_x, end_img_y)
        
        self.is_dragging = False
        self.start_pos = None
        
        self.canvas.delete("warp_circle")
        self.canvas.delete("direction_line")
        self.update_display()
    
    def apply_warp(self, start_x, start_y, end_x, end_y):
        """변형 적용"""
        if self.current_image is None:
            return
            
        img_height, img_width = self.current_image.shape[:2]
        
        start_x = max(0, min(start_x, img_width - 1))
        start_y = max(0, min(start_y, img_height - 1))
        end_x = max(0, min(end_x, img_width - 1))
        end_y = max(0, min(end_y, img_height - 1))
        
        mode = self.warp_mode.get()
        
        if mode == "push":
            self.apply_push_warp(start_x, start_y, end_x, end_y)
        elif mode == "pull":
            self.apply_pull_warp(start_x, start_y, end_x, end_y)
        elif mode == "expand":
            self.apply_radial_warp(start_x, start_y, expand=True)
        elif mode == "shrink":
            self.apply_radial_warp(start_x, start_y, expand=False)
    
    def apply_push_warp(self, start_x, start_y, end_x, end_y):
        """밀어내기 변형"""
        img_height, img_width = self.current_image.shape[:2]
        
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return
        
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        pixel_dx = map_x - start_x
        pixel_dy = map_y - start_y
        pixel_dist = np.sqrt(pixel_dx*pixel_dx + pixel_dy*pixel_dy)
        
        influence_radius = self.get_influence_radius_pixels()
        mask = pixel_dist < influence_radius
        
        strength_map = np.zeros_like(pixel_dist)
        valid_dist = pixel_dist[mask]
        
        if len(valid_dist) > 0:
            strength_map[mask] = (1 - valid_dist / influence_radius) ** 2
            strength_map[mask] *= self.strength_var.get()
            
            map_x[mask] += dx * strength_map[mask]
            map_y[mask] += dy * strength_map[mask]
        
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        self.current_image = cv2.remap(
            self.current_image, map_x, map_y, 
            cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
        )
    
    def apply_pull_warp(self, start_x, start_y, end_x, end_y):
        """당기기 변형"""
        dx = start_x - end_x
        dy = start_y - end_y
        self.apply_push_warp(start_x, start_y, start_x + dx, start_y + dy)
    
    def apply_radial_warp(self, center_x, center_y, expand=True):
        """방사형 변형"""
        img_height, img_width = self.current_image.shape[:2]
        
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        dx = map_x - center_x
        dy = map_y - center_y
        distance = np.sqrt(dx*dx + dy*dy)
        
        influence_radius = self.get_influence_radius_pixels()
        mask = distance < influence_radius
        
        strength = self.strength_var.get() * 0.3
        
        if expand:
            scale_factor = 1 - strength * (1 - distance / influence_radius)
        else:
            scale_factor = 1 + strength * (1 - distance / influence_radius)
        
        scale_factor = np.maximum(scale_factor, 0.1)
        
        new_x = center_x + dx * scale_factor
        new_y = center_y + dy * scale_factor
        
        map_x = np.where(mask, new_x, map_x)
        map_y = np.where(mask, new_y, map_y)
        
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        self.current_image = cv2.remap(
            self.current_image, map_x, map_y, 
            cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
        )
    
    # 줌 및 이동 관련 메서드들
    def zoom_in(self, cursor_x=None, cursor_y=None):
        """줌 인 (커서 위치 기준)"""
        if self.zoom_factor < self.max_zoom:
            old_zoom = self.zoom_factor
            self.zoom_factor *= 1.2
            
            # 커서 위치가 주어진 경우 해당 지점 기준으로 줌
            if cursor_x is not None and cursor_y is not None:
                self.adjust_pan_for_zoom(cursor_x, cursor_y, old_zoom, self.zoom_factor)
            
            self.update_display()
            self.update_zoom_label()
    
    def zoom_out(self, cursor_x=None, cursor_y=None):
        """줌 아웃 (커서 위치 기준)"""
        if self.zoom_factor > self.min_zoom:
            old_zoom = self.zoom_factor
            self.zoom_factor /= 1.2
            
            # 커서 위치가 주어진 경우 해당 지점 기준으로 줌
            if cursor_x is not None and cursor_y is not None:
                self.adjust_pan_for_zoom(cursor_x, cursor_y, old_zoom, self.zoom_factor)
            
            self.update_display()
            self.update_zoom_label()
    
    def reset_zoom(self):
        """줌 리셋"""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.update_display()
        self.update_zoom_label()
    
    def update_zoom_label(self):
        """줌 레이블 업데이트"""
        zoom_percentage = int(self.zoom_factor * 100)
        self.zoom_label.config(text=f"{zoom_percentage}%")
    
    def adjust_pan_for_zoom(self, cursor_x, cursor_y, old_zoom, new_zoom):
        """줌 변경 시 커서 위치를 기준으로 팬 조정"""
        if self.current_image is None:
            return
        
        # 줌 비율 계산
        zoom_ratio = new_zoom / old_zoom
        
        # 커서 위치에서 이미지 시작점까지의 거리
        cursor_to_image_x = cursor_x - (self.offset_x + self.pan_x)
        cursor_to_image_y = cursor_y - (self.offset_y + self.pan_y)
        
        # 새로운 팬 값 계산 (커서 위치가 고정되도록)
        new_pan_x = cursor_x - self.offset_x - (cursor_to_image_x * zoom_ratio)
        new_pan_y = cursor_y - self.offset_y - (cursor_to_image_y * zoom_ratio)
        
        # 팬 값 업데이트
        self.pan_x = new_pan_x
        self.pan_y = new_pan_y
    
    def on_mouse_wheel(self, event):
        """마우스 휠 줌 (커서 위치 기준)"""
        if self.current_image is None:
            return
            
        # 마우스 커서 위치 가져오기
        cursor_x = event.x
        cursor_y = event.y
            
        if event.delta > 0:
            self.zoom_in(cursor_x, cursor_y)
        else:
            self.zoom_out(cursor_x, cursor_y)
    
    def on_pan_start(self, event):
        """이미지 이동 시작"""
        if self.current_image is None:
            return
            
        self.is_panning = True
        self.pan_start_pos = (event.x, event.y)
        self.canvas.config(cursor="fleur")
    
    def on_pan_drag(self, event):
        """이미지 이동 중"""
        if not self.is_panning or self.pan_start_pos is None:
            return
            
        dx = event.x - self.pan_start_pos[0]
        dy = event.y - self.pan_start_pos[1]
        
        self.pan_x += dx
        self.pan_y += dy
        
        self.pan_start_pos = (event.x, event.y)
        self.update_display()
    
    def on_pan_end(self, event):
        """이미지 이동 종료"""
        self.is_panning = False
        self.pan_start_pos = None
        self.canvas.config(cursor="crosshair")
    
    # 공통 기능들
    def get_influence_radius_pixels(self):
        """백분율 기반 영향 반경을 픽셀로 변환"""
        if self.current_image is None:
            return 80  # 기본값
        
        img_height, img_width = self.current_image.shape[:2]
        # 이미지의 더 작은 차원을 기준으로 백분율 계산 (정사각형에 가깝게)
        base_size = min(img_width, img_height)
        return int(base_size * (self.influence_radius_percent / 100.0))
    
    def update_radius(self, value):
        """영향 반경 업데이트 (백분율 기반)"""
        self.influence_radius_percent = float(value)
        
        # 현재 픽셀 크기 계산 및 레이블 업데이트
        pixel_radius = self.get_influence_radius_pixels()
        self.radius_label.config(text=f"{self.influence_radius_percent:.1f}% ({pixel_radius}px)")
        
        # 현재 마우스 위치가 있다면 영향 범위 원을 즉시 업데이트
        if hasattr(self, 'last_mouse_pos') and self.last_mouse_pos and self.current_image is not None:
            self.update_influence_circle(self.last_mouse_pos[0], self.last_mouse_pos[1])
    
    def save_to_history(self):
        """현재 이미지 상태를 히스토리에 저장"""
        if self.current_image is not None:
            self.history.append(self.current_image.copy())
            
            if len(self.history) > self.max_history:
                self.history.pop(0)
    
    def undo_last_action(self):
        """마지막 작업 되돌리기"""
        if len(self.history) > 0:
            self.current_image = self.history.pop()
            self.update_display()
            self.canvas.delete("preview_circle")
            self.detect_face()
        else:
            if self.original_image is not None:
                self.current_image = self.original_image.copy()
                self.update_display()
                self.canvas.delete("preview_circle")
                self.detect_face()
    
    def reset_image(self):
        """원본 이미지로 복원"""
        if self.original_image is not None:
            self.save_to_history()
            self.current_image = self.original_image.copy()
            self.reset_all_effects()
            
            # 프리셋 카운터 리셋
            self.lower_jaw_shot_count = 0
            self.middle_jaw_shot_count = 0
            self.cheek_shot_count = 0
            self.front_protusion_shot_count = 0
            self.back_slit_shot_count = 0
            self.lower_jaw_counter_label.config(text="")
            self.middle_jaw_counter_label.config(text="")
            self.cheek_counter_label.config(text="")
            self.front_protusion_counter_label.config(text="")
            self.back_slit_counter_label.config(text="")
            print("프리셋 카운터가 리셋되었습니다.")
            
            self.update_display()
            self.canvas.delete("preview_circle")
            self.detect_face()
    
    def reset_all_effects(self):
        """모든 효과 파라미터 초기화"""
        self.eye_effect_strength = 0.0
        self.eye_effect_positions = None
        self.nose_effect_strength = 0.0
        self.nose_effect_position = None
        self.eye_width_strength = 0.0
        self.eye_height_strength = 0.0
        self.eye_shape_positions = None
        self.jaw_effect_strength = 0.0
        self.jaw_effect_position = None
        self.cheek_effect_strength = 0.0
        self.cheek_effect_positions = None
        
        # UI 상태 업데이트
        self.update_all_status_labels()
    
    def save_image(self):
        """변형된 이미지 저장"""
        if self.current_image is None:
            return
            
        file_path = filedialog.asksaveasfilename(
            title="이미지 저장",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("모든 파일", "*.*")]
        )
        
        if file_path:
            try:
                save_image = cv2.cvtColor(self.current_image, cv2.COLOR_RGB2BGR)
                cv2.imwrite(file_path, save_image)
                print(f"이미지 저장 완료: {file_path}")
                
            except Exception as e:
                print(f"이미지 저장 실패: {str(e)}")
    
    # 리셋 메서드들
    def reset_eye_effect(self):
        """눈 효과 리셋"""
        if self.eye_effect_strength != 0.0:
            self.save_to_history()
            
        self.eye_effect_strength = 0.0
        self.eye_effect_positions = None
        
        if len(self.history) > 0 and self.eye_effect_strength == 0.0:
            self.current_image = self.history[-1].copy()
        else:
            self.current_image = self.original_image.copy()
            
        self.update_display()
        self.update_eye_status_label()
    
    def reset_nose_effect(self):
        """코 효과 리셋"""
        if self.nose_effect_strength != 0.0:
            self.save_to_history()
            
        self.nose_effect_strength = 0.0
        self.nose_effect_position = None
        
        if len(self.history) > 0 and self.nose_effect_strength == 0.0:
            self.current_image = self.history[-1].copy()
        else:
            self.current_image = self.original_image.copy()
            
        self.update_display()
        self.update_nose_status_label()
    
    def reset_eye_shape(self):
        """눈 형태 리셋"""
        if self.eye_width_strength != 0.0 or self.eye_height_strength != 0.0:
            self.save_to_history()
            
        self.eye_width_strength = 0.0
        self.eye_height_strength = 0.0
        self.eye_shape_positions = None
        
        if len(self.history) > 0:
            self.current_image = self.history[-1].copy()
        else:
            self.current_image = self.original_image.copy()
            
        self.update_display()
        self.update_eye_shape_labels()
    
    def reset_jaw_effect(self):
        """턱선 효과 리셋"""
        if self.jaw_effect_strength != 0.0:
            self.save_to_history()
            
        self.jaw_effect_strength = 0.0
        self.jaw_effect_position = None
        
        if len(self.history) > 0:
            self.current_image = self.history[-1].copy()
        else:
            self.current_image = self.original_image.copy()
            
        self.update_display()
        self.update_jaw_status_label()
    
    def reset_cheek_effect(self):
        """광대 효과 리셋"""
        if self.cheek_effect_strength != 0.0:
            self.save_to_history()
            
        self.cheek_effect_strength = 0.0
        self.cheek_effect_positions = None
        
        if len(self.history) > 0:
            self.current_image = self.history[-1].copy()
        else:
            self.current_image = self.original_image.copy()
            
        self.update_display()
        self.update_cheek_status_label()
    
    # 상태 라벨 업데이트 메서드들
    def update_eye_status_label(self):
        """눈 효과 상태 라벨 업데이트"""
        if hasattr(self, 'eye_status_label'):
            if self.eye_effect_strength > 0:
                self.eye_status_label.config(text=f"눈 효과: +{self.eye_effect_strength:.1f} (확대)", foreground="blue")
            elif self.eye_effect_strength < 0:
                self.eye_status_label.config(text=f"눈 효과: {self.eye_effect_strength:.1f} (축소)", foreground="red")
            else:
                self.eye_status_label.config(text="눈 효과: 0.0 (원본)", foreground="gray")
    
    def update_nose_status_label(self):
        """코 효과 상태 라벨 업데이트"""
        if hasattr(self, 'nose_status_label'):
            if self.nose_effect_strength > 0:
                self.nose_status_label.config(text=f"코 효과: +{self.nose_effect_strength:.1f} (확대)", foreground="blue")
            elif self.nose_effect_strength < 0:
                self.nose_status_label.config(text=f"코 효과: {self.nose_effect_strength:.1f} (축소)", foreground="red")
            else:
                self.nose_status_label.config(text="코 효과: 0.0 (원본)", foreground="gray")
    
    def update_jaw_status_label(self):
        """턱선 효과 상태 라벨 업데이트"""
        if hasattr(self, 'jaw_status_label'):
            if self.jaw_effect_strength > 0:
                self.jaw_status_label.config(text=f"턱선 효과: +{self.jaw_effect_strength:.1f} (강화)", foreground="blue")
            elif self.jaw_effect_strength < 0:
                self.jaw_status_label.config(text=f"턱선 효과: {self.jaw_effect_strength:.1f} (부드럽게)", foreground="red")
            else:
                self.jaw_status_label.config(text="턱선 효과: 0.0 (원본)", foreground="gray")
    
    def update_cheek_status_label(self):
        """광대 효과 상태 라벨 업데이트"""
        if hasattr(self, 'cheek_status_label'):
            if self.cheek_effect_strength > 0:
                self.cheek_status_label.config(text=f"광대 효과: +{self.cheek_effect_strength:.1f} (축소)", foreground="blue")
            elif self.cheek_effect_strength < 0:
                self.cheek_status_label.config(text=f"광대 효과: {self.cheek_effect_strength:.1f} (확대)", foreground="red")
            else:
                self.cheek_status_label.config(text="광대 효과: 0.0 (원본)", foreground="gray")
    
    def update_eye_shape_labels(self):
        """눈 형태 라벨 업데이트"""
        if hasattr(self, 'eye_width_label'):
            if self.eye_width_strength > 0:
                self.eye_width_label.config(text=f"가로: +{self.eye_width_strength:.1f} (확대)", foreground="blue")
            elif self.eye_width_strength < 0:
                self.eye_width_label.config(text=f"가로: {self.eye_width_strength:.1f} (축소)", foreground="red")
            else:
                self.eye_width_label.config(text="가로: 0.0 (원본)", foreground="gray")
        
        if hasattr(self, 'eye_height_label'):
            if self.eye_height_strength > 0:
                self.eye_height_label.config(text=f"세로: +{self.eye_height_strength:.1f} (확대)", foreground="blue")
            elif self.eye_height_strength < 0:
                self.eye_height_label.config(text=f"세로: {self.eye_height_strength:.1f} (축소)", foreground="red")
            else:
                self.eye_height_label.config(text="세로: 0.0 (원본)", foreground="gray")
        
        # 슬라이더 값 동기화
        if hasattr(self, 'eye_width_var'):
            self.eye_width_var.set(self.eye_width_strength)
        if hasattr(self, 'eye_height_var'):
            self.eye_height_var.set(self.eye_height_strength)
    
    def update_all_status_labels(self):
        """모든 상태 라벨 업데이트"""
        self.update_eye_status_label()
        self.update_nose_status_label()
        self.update_jaw_status_label()
        self.update_cheek_status_label()
        self.update_eye_shape_labels()
    
    def toggle_landmarks(self):
        """랜드마크 표시 토글"""
        self.show_landmarks = not self.show_landmarks
        
        if self.show_landmarks:
            self.landmark_button.config(text="👁️ 랜드마크 숨기기")
        else:
            self.landmark_button.config(text="👁️ 랜드마크 보기")
            self.canvas.delete("landmarks")  # 랜드마크 지우기
            # 랜드마크가 꺼지면 번호도 자동으로 꺼짐
            if self.show_landmark_numbers:
                self.show_landmark_numbers = False
                self.landmark_numbers_button.config(text="🔢 번호 보기")
        
        self.update_display()
        print(f"랜드마크 표시: {'ON' if self.show_landmarks else 'OFF'}")
    
    def toggle_landmark_numbers(self):
        """랜드마크 번호 표시 토글"""
        if not self.show_landmarks:
            print("먼저 랜드마크를 표시해주세요.")
            return
        
        self.show_landmark_numbers = not self.show_landmark_numbers
        
        if self.show_landmark_numbers:
            self.landmark_numbers_button.config(text="🔢 번호 숨기기")
        else:
            self.landmark_numbers_button.config(text="🔢 번호 보기")
        
        self.update_display()
        print(f"랜드마크 번호 표시: {'ON' if self.show_landmark_numbers else 'OFF'}")
    
    def toggle_landmark_lines(self):
        """랜드마크 선 연결 토글"""
        if not self.show_landmarks:
            print("먼저 랜드마크를 표시해주세요.")
            return
        
        self.show_landmark_lines = not self.show_landmark_lines
        
        if self.show_landmark_lines:
            self.landmark_lines_button.config(text="📏 선 연결 숨기기")
        else:
            self.landmark_lines_button.config(text="📏 선 연결 보기")
        
        self.update_display()
        print(f"랜드마크 선 연결: {'ON' if self.show_landmark_lines else 'OFF'}")
    
    
    def update_point_size(self, value):
        """점 크기 업데이트"""
        self.landmark_point_size = int(float(value))
        self.point_size_label.config(text=f"{self.landmark_point_size}px")
        if self.show_landmarks:
            self.update_display()
    
    def update_font_size(self, value):
        """폰트 크기 업데이트"""
        self.landmark_font_size = int(float(value))
        self.font_size_label.config(text=f"{self.landmark_font_size}pt")
        if self.show_landmarks:
            self.update_display()
    
    def refresh_landmarks(self):
        """랜드마크 새로고침"""
        if self.current_image is not None:
            self.detect_face()
            if self.show_landmarks:
                self.update_display()
        print("랜드마크 새로고침 완료")
    
    def draw_landmarks(self):
        """캔버스에 얼굴 랜드마크 표시"""
        if self.face_landmarks is None or self.current_image is None:
            return
        
        try:
            # 기존 랜드마크 지우기
            self.canvas.delete("landmarks")
            
            img_height, img_width = self.current_image.shape[:2]
            
            # 주요 랜드마크 그룹 정의
            landmark_groups = {
                "eyes": {
                    "indices": [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246,  # 왼쪽 눈
                              362, 382, 381, 380, 374, 373, 390, 249, 359, 263, 466, 388, 387, 386, 385, 384, 398],  # 오른쪽 눈 (359 추가)
                    "color": "#00ff00"  # 녹색
                },
                "iris_left": {
                    "indices": [474, 475, 476, 477],  # 왼쪽 눈동자
                    "color": "#00ccff"  # 밝은 청록색
                },
                "iris_right": {
                    "indices": [469, 470, 471, 472],  # 오른쪽 눈동자
                    "color": "#00ccff"  # 밝은 청록색
                },
                "iris": {
                    "indices": [470, 471, 472, 469, 475, 476, 477, 474],  # 통합 눈동자 (순서 수정)
                    "color": "#00ccff"  # 밝은 청록색
                },
                "eyelid_upper_left": {
                    "indices": [226, 247, 30, 29, 27, 28, 56, 190, 243],  # 왼쪽 상 눈꺼풀 (130 삭제)
                    "color": "#66ff66"  # 연한 녹색
                },
                "eyelid_lower_left": {
                    "indices": [226, 25, 110, 24, 23, 22, 26, 112, 243],  # 왼쪽 하 눈꺼풀 (130 삭제)
                    "color": "#99ff99"  # 더 연한 녹색
                },
                "eyelid_upper_right": {
                    "indices": [463, 414, 286, 258, 257, 260, 467, 446],  # 오른쪽 상 눈꺼풀 (259, 359 삭제)
                    "color": "#66ff66"  # 연한 녹색
                },
                "eyelid_lower_right": {
                    "indices": [463, 341, 256, 252, 253, 254, 339, 255, 446],  # 오른쪽 하 눈꺼풀 (359 삭제)
                    "color": "#99ff99"  # 더 연한 녹색
                },
                "eyelid_surround_upper_left": {
                    "indices": [35, 113, 225, 224, 223, 222, 221, 189, 244],  # 왼쪽 눈꺼풀 윗 주변라인
                    "color": "#ccffcc"  # 매우 연한 녹색
                },
                "eyelid_surround_lower_left": {
                    "indices": [35, 31, 228, 229, 230, 231, 232, 233, 244],  # 왼쪽 눈꺼풀 아래 주변라인
                    "color": "#e6ffe6"  # 아주 연한 녹색
                },
                "eyelid_surround_upper_right": {
                    "indices": [465, 413, 441, 442, 443, 444, 445, 342, 265],  # 오른쪽 눈꺼풀 윗 주변라인
                    "color": "#ccffcc"  # 매우 연한 녹색
                },
                "eyelid_surround_lower_right": {
                    "indices": [465, 453, 452, 451, 450, 449, 448, 261, 265],  # 오른쪽 눈꺼풀 아래 주변라인
                    "color": "#e6ffe6"  # 아주 연한 녹색
                },
                "eyelid_lower_surround_area": {
                    "indices": [
                        # 왼쪽 하꺼풀 + 하주변 통합
                        226, 25, 110, 24, 23, 22, 26, 112, 243,  # 왼쪽 하꺼풀
                        35, 31, 228, 229, 230, 231, 232, 233, 244,  # 왼쪽 하주변
                        # 오른쪽 하꺼풀 + 하주변 통합  
                        463, 341, 256, 252, 253, 254, 339, 255, 446,  # 오른쪽 하꺼풀
                        465, 453, 452, 451, 450, 449, 448, 261, 265   # 오른쪽 하주변
                    ],
                    "color": "#b3ffb3"  # 하주변영역 전용 색상 (중간 녹색)
                },
                "eyelid_lower_area": {
                    "indices": [
                        # 하꺼풀 랜드마크 (왼쪽 + 오른쪽)
                        226, 25, 110, 24, 23, 22, 26, 112, 243,  # 왼쪽 하꺼풀
                        463, 341, 256, 252, 253, 254, 339, 255, 446,  # 오른쪽 하꺼풀
                        # 눈 하단 랜드마크
                        33, 7, 163, 144, 145, 153, 154, 155, 133,  # 왼쪽 눈 하단
                        362, 382, 381, 380, 374, 373, 390, 249, 359  # 오른쪽 눈 하단
                    ],
                    "color": "#66ccff"  # 하꺼풀영역 전용 색상 (밝은 청록색)
                },
                "eyelid_upper_surround_area": {
                    "indices": [
                        # 왼쪽 상꺼풀 + 상주변 통합
                        226, 247, 30, 29, 27, 28, 56, 190, 243,  # 왼쪽 상꺼풀
                        35, 113, 225, 224, 223, 222, 221, 189, 244,  # 왼쪽 상주변
                        # 오른쪽 상꺼풀 + 상주변 통합
                        463, 414, 286, 258, 257, 260, 467, 446,  # 오른쪽 상꺼풀
                        465, 413, 441, 442, 443, 444, 445, 342, 265  # 오른쪽 상주변
                    ],
                    "color": "#cccc66"  # 상주변영역 전용 색상 (연한 황록색)
                },
                "eyelid_upper_area": {
                    "indices": [
                        # 상꺼풀 랜드마크 (왼쪽 + 오른쪽)
                        226, 247, 30, 29, 27, 28, 56, 190, 243,  # 왼쪽 상꺼풀
                        463, 414, 286, 258, 257, 260, 467, 446,  # 오른쪽 상꺼풀
                        # 눈 상단 랜드마크
                        33, 246, 161, 160, 159, 158, 157, 173, 133,  # 왼쪽 눈 상단
                        362, 398, 384, 385, 386, 387, 388, 466, 263, 359  # 오른쪽 눈 상단
                    ],
                    "color": "#ff9966"  # 상꺼풀영역 전용 색상 (밝은 주황색)
                },
                "nose_tip": {
                    "indices": [1, 2],  # 코 끝
                    "color": "#ff0000"  # 빨간색
                },
                "nose_bridge": {
                    "indices": [4, 5, 6, 19, 94, 168, 195, 197],  # 코 기둥
                    "color": "#ff4400"  # 주황빨강
                },
                "nose_wings": {
                    "indices": [45, 129, 64, 98, 97, 115, 220, 275, 278, 294, 326, 327, 344, 440],  # 콧볼 (기존 + 코 중앙 측면 통합)
                    "color": "#ff8800"  # 주황색
                },
                "lip_upper": {
                    "indices": [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 308, 415, 310, 312, 13, 82, 81, 80, 191, 78],
                    "color": "#ff3300"  # 밝은 빨간색
                },
                "lip_lower": {
                    "indices": [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 402, 317, 14, 87, 178, 88, 95, 78],
                    "color": "#ff6600"  # 주황색
                },
                "jawline": {
                    "indices": [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 58, 132, 137],
                    "color": "#0066ff"  # 파란색
                },
                "jawline_area": {
                    "indices": [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 58, 132, 137,  # 기존 턱선 (175 제외)
                               123, 50, 207, 212, 202, 204, 194, 201, 200, 421, 418, 424, 422, 432, 427, 280, 352],  # 추가 랜드마크
                    "color": "#0088ff"  # 밝은 파란색
                },
                "mouth_area": {
                    "indices": [167, 164, 393, 391, 322, 410, 287, 273, 335, 406, 313, 18, 83, 182, 106, 43, 57, 186, 92, 165],  # 입 주변 영역
                    "color": "#ff9966"  # 연한 주황색
                },
                "nose_area": {
                    "indices": [55, 9, 285, 413, 464, 453, 350, 329, 266, 425, 426, 391, 393, 164, 167, 165, 206, 205, 36, 100, 121, 233, 243, 189],  # 코 주변 영역
                    "color": "#ffdd66"  # 연한 황색
                },
                "nasolabial_left": {
                    "indices": [126, 131, 49, 129, 165, 61, 181, 194, 204, 202, 212, 216, 36, 142],  # 좌측 팔자주름 영역 (106→181)
                    "color": "#cc99ff"  # 연한 보라색
                },
                "nasolabial_right": {
                    "indices": [355, 371, 266, 436, 432, 422, 424, 418, 405, 291, 391, 278, 360, 321, 363],  # 우측 팔자주름 영역 (191→291로 변경)
                    "color": "#dd99ff"  # 밝은 연보라색
                },
                "eyebrow_area": {
                    "indices": [139, 71, 68, 104, 69, 108, 151, 337, 299, 333, 298, 301, 383, 353, 260, 259, 257, 258, 286, 413, 417, 168, 193, 189, 56, 28, 27, 29, 30, 156],  # 눈썹 주변 영역
                    "color": "#bb77ff"  # 중간 보라색
                },
                "eyebrows": {
                    "indices": [55, 107, 66, 105, 63, 70, 46, 53, 52, 65,  # 왼쪽 눈썹
                              285, 336, 296, 334, 293, 300, 276, 283, 282, 295],  # 오른쪽 눈썹 (282 추가)
                    "color": "#9900ff"  # 보라색
                },
                "forehead": {
                    "indices": [10, 338, 297, 332, 284, 251, 301, 293, 334, 296, 336, 9, 107, 66, 105, 63, 71, 21, 54, 103, 67, 109],  # 이마 영역
                    "color": "#ffdd99"  # 연한 살색
                },
                "glabella": {
                    "indices": [107, 9, 336, 285, 417, 168, 193, 55],  # 미간 영역
                    "color": "#ffcc88"  # 더 진한 살색
                },
                "cheekbones": {
                    "indices": [116, 117, 118, 119, 120, 121, 126, 142,  # 왼쪽 광대
                              345, 346, 347, 348, 349, 350, 355, 371],  # 오른쪽 광대
                    "color": "#ff0099"  # 분홍색
                },
                "cheek_area_left": {
                    "indices": [116, 117, 118, 119, 120, 121, 126, 142, 36, 205, 147, 187, 123, 50],  # 왼쪽 볼 영역 (123, 50 추가)
                    "color": "#ff6699"  # 밝은분홍색
                },
                "cheek_area_right": {
                    "indices": [345, 346, 347, 348, 349, 350, 355, 371, 266, 425, 376, 411, 352, 280],  # 오른쪽 볼 영역 (352, 280 추가)
                    "color": "#ff6699"  # 밝은분홍색
                },
                "nose_side_left": {
                    "indices": [193, 122, 196, 236, 198, 209, 49],  # 왼쪽 코 측면 선
                    "color": "#ff9900"  # 주황색
                },
                "nose_side_right": {
                    "indices": [417, 351, 419, 456, 420, 360, 279],  # 오른쪽 코 측면 선
                    "color": "#ff9900"  # 주황색
                }
            }
            
            # 각 그룹별로 랜드마크 그리기 (가시성 확인)
            for group_name, group_data in landmark_groups.items():
                # 그룹 가시성 확인
                visibility_key = self.get_visibility_key(group_name)
                if visibility_key and visibility_key in self.landmark_group_visibility:
                    if not self.landmark_group_visibility[visibility_key].get():
                        continue  # 이 그룹은 숨김
                
                indices = group_data["indices"]
                color = group_data["color"]
                
                for idx in indices:
                    if idx < len(self.face_landmarks.landmark):
                        landmark = self.face_landmarks.landmark[idx]
                        
                        # 이미지 좌표를 화면 좌표로 변환
                        img_x = landmark.x * img_width
                        img_y = landmark.y * img_height
                        
                        # 화면 좌표로 변환 (줌 및 이동 고려)
                        screen_x = img_x * self.scale_factor * self.zoom_factor + self.offset_x + self.pan_x
                        screen_y = img_y * self.scale_factor * self.zoom_factor + self.offset_y + self.pan_y
                        
                        # 점 크기 (사용자 설정 + 줌 고려) - 50% 크기로 축소
                        point_size = max(1, int(self.landmark_point_size * self.zoom_factor * 0.5))
                        
                        # 캔버스에 점 그리기
                        self.canvas.create_oval(
                            screen_x - point_size, screen_y - point_size,
                            screen_x + point_size, screen_y + point_size,
                            fill=color, outline="white", width=1,
                            tags="landmarks"
                        )
                        
                        # 번호 표시 (활성화된 경우)
                        if self.show_landmark_numbers:
                            # 텍스트 크기 (사용자 설정 + 줌 고려)
                            font_size = max(3, int(self.landmark_font_size * self.zoom_factor))
                            
                            # 번호 텍스트 그리기
                            self.canvas.create_text(
                                screen_x + point_size + 2, screen_y - point_size - 2,
                                text=str(idx), 
                                fill="yellow", 
                                font=("Arial", font_size, "bold"),
                                tags="landmarks"
                            )
            
            # 선 연결 그리기 (활성화된 경우)
            if self.show_landmark_lines:
                self.draw_landmark_lines(landmark_groups, img_width, img_height)
            
            # 범례 표시
            self.draw_landmark_legend()
            
        except Exception as e:
            print(f"랜드마크 표시 오류: {str(e)}")
    
    def draw_landmark_lines(self, landmark_groups, img_width, img_height):
        """랜드마크 그룹별 선 연결 그리기"""
        try:
            # 선 연결을 지원하는 그룹 정의
            line_groups = [
                "forehead", "glabella", "nose_area", "jawline_area", "jawline",
                "lip_lower", "lip_upper", "eyes", "iris", "mouth_area",
                "eyebrows", "eyebrow_area", "cheek_area_left", "cheek_area_right",
                "nasolabial_left", "nasolabial_right", "nose_bridge", "nose_wings",
                "eyelid_lower_surround_area", "eyelid_lower_area", "eyelid_upper_surround_area", "eyelid_upper_area",
                "nose_side_left", "nose_side_right"  # 코 측면 선 추가
            ]
            
            for group_name in line_groups:
                # 해당 그룹이 가시화되어 있는지 확인
                visibility_key = self.get_visibility_key(group_name) or group_name
                if (visibility_key in self.landmark_group_visibility and 
                    not self.landmark_group_visibility[visibility_key].get()):
                    continue
                
                # 그룹 데이터 찾기
                if group_name not in landmark_groups:
                    continue
                    
                group_data = landmark_groups[group_name]
                indices = group_data["indices"]
                color = group_data["color"]
                
                # 랜드마크 좌표 수집
                points = []
                for idx in indices:
                    if idx < len(self.face_landmarks.landmark):
                        landmark = self.face_landmarks.landmark[idx]
                        
                        # 이미지 좌표를 화면 좌표로 변환
                        img_x = landmark.x * img_width
                        img_y = landmark.y * img_height
                        
                        # 화면 좌표로 변환 (줌 및 이동 고려)
                        screen_x = img_x * self.scale_factor * self.zoom_factor + self.offset_x + self.pan_x
                        screen_y = img_y * self.scale_factor * self.zoom_factor + self.offset_y + self.pan_y
                        
                        points.append((screen_x, screen_y))
                
                # 연속된 점들을 선으로 연결
                if len(points) > 1:
                    print(f"draw_landmark_lines에서 {group_name} 그룹 처리 중, 점 개수: {len(points)}")
                    self._draw_group_lines(points, color, group_name)
        
        except Exception as e:
            print(f"랜드마크 선 그리기 오류: {str(e)}")
    
    def draw_all_landmark_lines(self, landmark_groups, img_width, img_height):
        """모든 랜드마크 그룹의 선 연결 그리기"""
        try:
            # 각 그룹별로 선 연결 처리
            for group_name, group_data in landmark_groups.items():
                # 그룹이 가시화되어 있는지 확인
                visibility_key = self.get_visibility_key(group_name)
                if (visibility_key in self.landmark_group_visibility and 
                    not self.landmark_group_visibility[visibility_key].get()):
                    continue
                
                indices = group_data["indices"]
                color = group_data["color"]
                
                # 랜드마크 좌표 수집
                points = []
                for idx in indices:
                    if idx < len(self.face_landmarks.landmark):
                        landmark = self.face_landmarks.landmark[idx]
                        
                        # 이미지 좌표를 화면 좌표로 변환
                        img_x = landmark.x * img_width
                        img_y = landmark.y * img_height
                        
                        # 화면 좌표로 변환 (줌 및 이동 고려)
                        screen_x = img_x * self.scale_factor * self.zoom_factor + self.offset_x + self.pan_x
                        screen_y = img_y * self.scale_factor * self.zoom_factor + self.offset_y + self.pan_y
                        
                        points.append((screen_x, screen_y))
                
                # 그룹별 선 그리기
                if len(points) > 1:
                    self.draw_lines_for_group(points, color, group_name)
        
        except Exception as e:
            print(f"모든 랜드마크 선 그리기 오류: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _draw_smooth_curve(self, points, color, line_width):
        """매우 부드러운 곡선 그리기 - 수동 베지어 곡선 구현"""
        if len(points) < 2:
            return
        
        print(f"_draw_smooth_curve 호출됨: {len(points)}개 점, 색상: {color}")
        
        try:
            # 2개 점이면 부드러운 선으로
            if len(points) == 2:
                x1, y1 = points[0]
                x2, y2 = points[1]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=line_width,
                    smooth=True,
                    tags="landmarks"
                )
                return
            
            # 3개 이상의 점이면 수동 베지어 곡선으로 그리기
            if len(points) >= 3:
                print(f"베지어 곡선 생성 중: {len(points)}개 원본 점")
                # 많은 작은 선분들로 부드러운 곡선 만들기
                curve_points = self._generate_bezier_curve_points(points)
                print(f"생성된 곡선 점 개수: {len(curve_points)}")
                
                # 더 부드러운 곡선을 위해 polygon 사용 시도
                try:
                    # 모든 곡선 점을 하나의 부드러운 선으로 그리기
                    coords = []
                    for point in curve_points:
                        coords.extend([point[0], point[1]])
                    
                    # Tkinter의 smooth polygon 사용
                    self.canvas.create_line(
                        *coords,
                        fill=color,
                        width=line_width,
                        smooth=True,
                        splinesteps=50,  # 매우 높은 스플라인 단계
                        tags="landmarks"
                    )
                    print(f"polygon으로 곡선 그리기 완료")
                    
                except Exception as e:
                    print(f"polygon 방식 실패, 개별 선분으로 대체: {e}")
                    # 실패시 작은 선분들로 곡선 그리기
                    for i in range(len(curve_points) - 1):
                        x1, y1 = curve_points[i]
                        x2, y2 = curve_points[i + 1]
                        
                        self.canvas.create_line(
                            x1, y1, x2, y2,
                            fill=color,
                            width=line_width,
                            smooth=True,
                            splinesteps=10,
                            tags="landmarks"
                        )
            
        except Exception as e:
            print(f"부드러운 곡선 그리기 오류: {str(e)}")
            # 오류 발생시 기본 부드러운 선으로 대체
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=line_width,
                    smooth=True,
                    tags="landmarks"
                )
    
    def _generate_catmull_rom_points(self, control_points, segments_per_curve=10):
        """카테인 롬 스플라인을 사용하여 부드러운 보간점 생성"""
        if len(control_points) < 3:
            return control_points
            
        smooth_points = []
        
        # 첫 번째 점 추가
        smooth_points.append(control_points[0])
        
        # 각 구간에 대해 카테인 롬 스플라인 적용
        for i in range(len(control_points) - 1):
            # 제어점 4개 선택 (현재 구간의 양 끝 + 전후 점)
            p0 = control_points[max(0, i - 1)]
            p1 = control_points[i]
            p2 = control_points[i + 1]
            p3 = control_points[min(len(control_points) - 1, i + 2)]
            
            # 구간을 여러 작은 세그먼트로 나누어 부드러운 곡선 생성
            for t in range(1, segments_per_curve + 1):
                t_normalized = t / segments_per_curve
                point = self._catmull_rom_interpolate(p0, p1, p2, p3, t_normalized)
                smooth_points.append(point)
        
        return smooth_points
    
    def _catmull_rom_interpolate(self, p0, p1, p2, p3, t):
        """카테인 롬 스플라인 보간 공식"""
        x0, y0 = p0
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        
        # t의 제곱과 세제곱
        t2 = t * t
        t3 = t2 * t
        
        # 카테인 롬 스플라인 계수
        # P(t) = 0.5 * [(2*P1) + (-P0 + P2)*t + (2*P0 - 5*P1 + 4*P2 - P3)*t^2 + (-P0 + 3*P1 - 3*P2 + P3)*t^3]
        
        x = 0.5 * (
            2 * x1 +
            (-x0 + x2) * t +
            (2 * x0 - 5 * x1 + 4 * x2 - x3) * t2 +
            (-x0 + 3 * x1 - 3 * x2 + x3) * t3
        )
        
        y = 0.5 * (
            2 * y1 +
            (-y0 + y2) * t +
            (2 * y0 - 5 * y1 + 4 * y2 - y3) * t2 +
            (-y0 + 3 * y1 - 3 * y2 + y3) * t3
        )
        
        return (x, y)
    
    def _generate_bezier_curve_points(self, control_points, resolution=100):
        """베지어 곡선 점들을 생성하여 부드러운 곡선 만들기"""
        if len(control_points) < 3:
            return control_points
        
        curve_points = []
        
        # 각 3개 점씩 그룹으로 나누어 2차 베지어 곡선 생성
        for i in range(len(control_points) - 2):
            p0 = control_points[i]
            p1 = control_points[i + 1]
            p2 = control_points[i + 2]
            
            # 중점을 제어점으로 사용하여 더 부드러운 곡선 생성
            if i == 0:
                # 첫 번째 구간
                start_point = p0
            else:
                # 이전 구간과 연결되는 중점
                prev_p1 = control_points[i]
                start_point = ((prev_p1[0] + p1[0]) / 2, (prev_p1[1] + p1[1]) / 2)
            
            if i == len(control_points) - 3:
                # 마지막 구간
                end_point = p2
            else:
                # 다음 구간과 연결되는 중점
                next_p1 = control_points[i + 2]
                end_point = ((p1[0] + next_p1[0]) / 2, (p1[1] + next_p1[1]) / 2)
            
            # 2차 베지어 곡선 점들 생성
            segment_points = self._quadratic_bezier_points(start_point, p1, end_point, resolution // (len(control_points) - 2))
            
            if i == 0:
                curve_points.extend(segment_points)
            else:
                # 첫 번째 점은 이전 구간의 마지막 점과 겹치므로 제외
                curve_points.extend(segment_points[1:])
        
        return curve_points
    
    def _quadratic_bezier_points(self, p0, p1, p2, num_points=50):
        """2차 베지어 곡선의 점들을 생성"""
        points = []
        
        for i in range(num_points + 1):
            t = i / num_points
            
            # 2차 베지어 곡선 공식: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
            
            points.append((x, y))
        
        return points
    

    def draw_lines_for_group(self, points, color, group_name):
        """특정 그룹에 대한 선 그리기"""
        try:
            line_width = max(1, int(1 * self.zoom_factor))
            
            # 지원되는 그룹만 선 연결
            line_supported_groups = [
                "forehead", "glabella", "nose_area", "jawline_area", "jawline",
                "lip_lower", "lip_upper", "eyes", "iris", "mouth_area",
                "eyebrows", "eyebrow_area", "cheek_area_left", "cheek_area_right",
                "nasolabial_left", "nasolabial_right", "nose_bridge", "nose_wings",
                "eyelid_lower_surround_area", "eyelid_lower_area", "eyelid_upper_surround_area", "eyelid_upper_area"
            ]
            
            if group_name not in line_supported_groups:
                return
            
            # 그룹별 특별 처리
            if group_name == "eyes":
                self._draw_eye_lines(points, color, line_width)
            elif group_name == "iris":
                self._draw_circular_lines(points, color, line_width)
            elif group_name == "jawline_area":
                self._draw_jawline_lines(points, color, line_width)
            elif group_name == "jawline":
                self._draw_jawline_basic_lines(points, color, line_width)
            elif group_name == "eyebrows":
                self._draw_eyebrow_lines(points, color, line_width)
            elif group_name in ["cheek_area_left", "cheek_area_right"]:
                self._draw_cheek_area_lines(points, color, line_width, group_name)
            elif group_name in ["nasolabial_left", "nasolabial_right"]:
                self._draw_nasolabial_lines(points, color, line_width, group_name)
            elif group_name == "nose_bridge":
                self._draw_nose_bridge_lines(points, color, line_width)
            elif group_name == "nose_wings":
                self._draw_nose_wings_lines(points, color, line_width)
            else:
                # 부드러운 곡선 그리기
                self._draw_smooth_curve(points, color, line_width)
                
                # 닫힌 다각형이 필요한 그룹들
                closed_groups = ["forehead", "glabella", "nose_area", 
                               "lip_lower", "lip_upper", "mouth_area", "eyebrow_area"]
                
                if group_name in closed_groups and len(points) > 2:
                    # 첫 번째와 마지막 점 사이도 부드럽게 연결
                    closing_points = [points[-1], points[0]]
                    self._draw_smooth_curve(closing_points, color, line_width)
                    
        except Exception as e:
            print(f"그룹 선 그리기 오류 ({group_name}): {str(e)}")
    
    def draw_simple_lines_for_all_groups(self, landmark_groups, img_width, img_height):
        """모든 그룹에 대해 간단한 선 그리기 테스트"""
        try:
            # 테스트용 그룹들만 선 그리기
            test_groups = ["mouth_area", "eyebrows", "iris", "forehead", "lip_upper", "lip_lower"]
            
            for group_name in test_groups:
                if group_name not in landmark_groups:
                    continue
                    
                # 그룹 가시성 확인
                visibility_key = self.get_visibility_key(group_name)
                if (visibility_key in self.landmark_group_visibility and 
                    not self.landmark_group_visibility[visibility_key].get()):
                    continue
                
                group_data = landmark_groups[group_name]
                indices = group_data["indices"]
                color = group_data["color"]
                
                # 좌표 수집
                points = []
                for idx in indices:
                    if idx < len(self.face_landmarks.landmark):
                        landmark = self.face_landmarks.landmark[idx]
                        img_x = landmark.x * img_width
                        img_y = landmark.y * img_height
                        screen_x = img_x * self.scale_factor * self.zoom_factor + self.offset_x + self.pan_x
                        screen_y = img_y * self.scale_factor * self.zoom_factor + self.offset_y + self.pan_y
                        points.append((screen_x, screen_y))
                
                # 간단한 선 그리기
                if len(points) > 1:
                    line_width = max(1, int(1 * self.zoom_factor))
                    
                    # 연속된 점들을 선으로 연결
                    for i in range(len(points) - 1):
                        x1, y1 = points[i]
                        x2, y2 = points[i + 1]
                        
                        self.canvas.create_line(
                            x1, y1, x2, y2,
                            fill=color,
                            width=line_width,
                            smooth=True,
                            tags="landmarks"
                        )
                    
                    # 닫힌 다각형 (첫점과 마지막점 연결)
                    if len(points) > 2:
                        x1, y1 = points[-1]
                        x2, y2 = points[0]
                        
                        self.canvas.create_line(
                            x1, y1, x2, y2,
                            fill=color,
                            width=line_width,
                            smooth=True,
                            tags="landmarks"
                        )
                        
        except Exception as e:
            print(f"간단한 선 그리기 오류: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def draw_actual_landmark_lines(self, landmark_groups, img_width, img_height):
        """실제 랜드마크 선 연결 그리기"""
        try:
            print("실제 랜드마크 선 연결 시작")
            
            # 선 연결을 지원하는 그룹들 (하나씩 테스트)
            line_groups = [
                "mouth_area",     # 입 주변 (이미 작동했던 것)
                "eyebrows",       # 눈썹 (특별 처리)
                "iris",           # 눈동자 (원형)
                "forehead",       # 이마 (닫힌 다각형)
                "lip_upper",      # 윗입술
                "lip_lower",      # 아래입술
            ]
            
            for group_name in line_groups:
                print(f"처리 중: {group_name}")
                
                if group_name not in landmark_groups:
                    print(f"  -> {group_name} 그룹이 landmark_groups에 없음")
                    continue
                
                # 그룹 가시성 확인 (간단한 직접 체크)
                skip_group = False
                if group_name in self.landmark_group_visibility:
                    if not self.landmark_group_visibility[group_name].get():
                        print(f"  -> {group_name} 그룹이 비활성화됨")
                        skip_group = True
                elif group_name == "mouth_area" and not self.landmark_group_visibility["mouth_area"].get():
                    print(f"  -> {group_name} 그룹이 비활성화됨")
                    skip_group = True
                elif group_name == "eyebrows" and not self.landmark_group_visibility["eyebrows"].get():
                    print(f"  -> {group_name} 그룹이 비활성화됨") 
                    skip_group = True
                elif group_name == "iris" and not self.landmark_group_visibility["iris"].get():
                    print(f"  -> {group_name} 그룹이 비활성화됨")
                    skip_group = True
                elif group_name == "forehead" and not self.landmark_group_visibility["forehead"].get():
                    print(f"  -> {group_name} 그룹이 비활성화됨")
                    skip_group = True
                elif group_name in ["lip_upper", "lip_lower"] and not self.landmark_group_visibility.get("lip_upper", tk.BooleanVar(value=True)).get():
                    print(f"  -> {group_name} 그룹이 비활성화됨")
                    skip_group = True
                
                if skip_group:
                    continue
                
                print(f"  -> {group_name} 그룹 처리 시작")
                
                group_data = landmark_groups[group_name]
                indices = group_data["indices"]
                color = group_data["color"]
                
                print(f"  -> 랜드마크 인덱스 개수: {len(indices)}")
                
                # 좌표 수집
                points = []
                for idx in indices:
                    if idx < len(self.face_landmarks.landmark):
                        landmark = self.face_landmarks.landmark[idx]
                        img_x = landmark.x * img_width
                        img_y = landmark.y * img_height
                        screen_x = img_x * self.scale_factor * self.zoom_factor + self.offset_x + self.pan_x
                        screen_y = img_y * self.scale_factor * self.zoom_factor + self.offset_y + self.pan_y
                        points.append((screen_x, screen_y))
                
                print(f"  -> 수집된 좌표 개수: {len(points)}")
                
                if len(points) > 1:
                    line_width = max(1, int(1 * self.zoom_factor))
                    line_count = 0
                    
                    # 부드러운 곡선으로 연결
                    self._draw_smooth_curve(points, color, line_width)
                    line_count += len(points) - 1
                    
                    # 닫힌 다각형 (첫점과 마지막점 연결)
                    if len(points) > 2:
                        closing_points = [points[-1], points[0]]
                        self._draw_smooth_curve(closing_points, color, line_width)
                        line_count += 1
                    
                    print(f"  -> {group_name}: {line_count}개 선 그리기 완료")
                else:
                    print(f"  -> {group_name}: 포인트 부족 ({len(points)}개)")
                    
        except Exception as e:
            print(f"실제 랜드마크 선 그리기 오류: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _draw_group_lines(self, points, color, group_name):
        """특정 그룹의 선 그리기"""
        try:
            print(f"_draw_group_lines 호출: {group_name}, 점 개수: {len(points)}")
            line_width = max(1, int(1 * self.zoom_factor))  # 줄에 따른 선 두께 조정 (50% 감소)
            
            # 특별 처리가 필요한 그룹들
            if group_name == "eyes":
                # 눈 그룹의 경우 좌우 눈을 별도로 처리
                self._draw_eye_lines(points, color, line_width)
            elif group_name == "iris":
                # 눈동자의 경우 원형으로 연결
                self._draw_circular_lines(points, color, line_width)
            elif group_name == "jawline_area":
                # 턱선 영역의 경우 특별 처리
                self._draw_jawline_lines(points, color, line_width)
            elif group_name == "jawline":
                # 턱선의 경우 사용자 지정 순서로 처리
                self._draw_jawline_basic_lines(points, color, line_width)
            elif group_name == "eyebrows":
                # 눈썹의 경우 좌우 분리 처리
                self._draw_eyebrow_lines(points, color, line_width)
            elif group_name == "eyebrow_area":
                # 눈썹 주변 영역의 경우 닫힌 다각형
                self._draw_closed_polygon_lines(points, color, line_width)
            elif group_name in ["cheek_area_left", "cheek_area_right"]:
                # 볼영역의 경우 50, 280 제외하고 연결
                self._draw_cheek_area_lines(points, color, line_width, group_name)
            elif group_name in ["nasolabial_left", "nasolabial_right"]:
                # 팔자주름의 경우 특별 처리
                self._draw_nasolabial_lines(points, color, line_width, group_name)
            elif group_name == "nose_bridge":
                # 코 기둥의 경우 연속 선
                self._draw_nose_bridge_lines(points, color, line_width)
            elif group_name == "nose_wings":
                # 콧볼의 경우 좌우 분리 연결
                self._draw_nose_wings_lines(points, color, line_width)
            elif group_name == "eyelid_lower_surround_area":
                # 하주변영역의 경우 특별 연결 처리
                self._draw_eyelid_lower_surround_area_lines(points, color, line_width)
            elif group_name == "eyelid_lower_area":
                # 하꺼풀영역의 경우 특별 연결 처리
                self._draw_eyelid_lower_area_lines(points, color, line_width)
            elif group_name == "eyelid_upper_surround_area":
                # 상주변영역의 경우 특별 연결 처리
                self._draw_eyelid_upper_surround_area_lines(points, color, line_width)
            elif group_name == "eyelid_upper_area":
                # 상꺼풀영역의 경우 특별 연결 처리
                self._draw_eyelid_upper_area_lines(points, color, line_width)
            elif group_name in ["nose_side_left", "nose_side_right"]:
                # 코 측면 선의 경우 연속 선으로 그리기
                self._draw_nose_side_lines(points, color, line_width)
            else:
                # 부드러운 곡선으로 그리기
                print(f"일반 그룹 {group_name}에 대해 _draw_smooth_curve 호출")
                self._draw_smooth_curve(points, color, line_width)
                
                # 닫힌 다각형이 필요한 그룹들
                closed_groups = ["forehead", "glabella", "nose_area", 
                               "lip_lower", "lip_upper", "mouth_area"]
                
                if group_name in closed_groups and len(points) > 2:
                    # 첫 번째와 마지막 점도 부드럽게 연결
                    closing_points = [points[-1], points[0]]
                    self._draw_smooth_curve(closing_points, color, line_width)
        
        except Exception as e:
            print(f"그룹 선 그리기 오류 ({group_name}): {str(e)}")
    
    def _draw_eye_lines(self, points, color, line_width):
        """눈 그룹 특별 처리 - 좌우 눈 개별 연결"""
        try:
            # 눈 랜드마크는 일반적으로 좌우 눈이 섞여있어서 
            # 연속 연결보다는 각 눈의 윤곽선을 그리는 것이 좋음
            if len(points) > 6:  # 충분한 점이 있을 때만
                mid_point = len(points) // 2
                
                # 첫 번째 눈 (좌측) - 부드러운 곡선으로 연결
                left_eye_points = points[:mid_point]
                if len(left_eye_points) > 2:
                    # 닫힌 곡선으로 그리기 (첫 점과 마지막 점도 연결)
                    closed_left_points = left_eye_points + [left_eye_points[0]]
                    self._draw_smooth_curve(closed_left_points, color, line_width)
                
                # 두 번째 눈 (우측) - 부드러운 곡선으로 연결
                right_eye_points = points[mid_point:]
                if len(right_eye_points) > 2:
                    # 닫힌 곡선으로 그리기 (첫 점과 마지막 점도 연결)
                    closed_right_points = right_eye_points + [right_eye_points[0]]
                    self._draw_smooth_curve(closed_right_points, color, line_width)
        except Exception as e:
            print(f"눈 선 그리기 오류: {str(e)}")
    
    def _draw_circular_lines(self, points, color, line_width):
        """원형 선 그리기 (홍채 등) - 좌우 눈동자 분리 처리"""
        try:
            if len(points) < 4:
                return
            
            # 눈동자는 좌우로 분리되어 있음 (각각 4개씩)
            mid_point = len(points) // 2
            
            # 왼쪽 눈동자 (첫 4개: 470, 471, 469, 472) - 부드러운 원형으로
            left_iris = points[:mid_point]
            if len(left_iris) >= 4:
                # 닫힌 원형 곡선으로 그리기
                closed_left_iris = left_iris + [left_iris[0]]
                self._draw_smooth_curve(closed_left_iris, color, line_width)
            
            # 오른쪽 눈동자 (나머지 4개: 475, 476, 474, 477) - 부드러운 원형으로
            right_iris = points[mid_point:]
            if len(right_iris) >= 4:
                # 닫힌 원형 곡선으로 그리기
                closed_right_iris = right_iris + [right_iris[0]]
                self._draw_smooth_curve(closed_right_iris, color, line_width)
                    
        except Exception as e:
            print(f"원형 선 그리기 오류: {str(e)}")
    
    def _draw_jawline_lines(self, points, color, line_width):
        """턱선 영역 특별 처리 - 58번과 172번을 연결하고 특정 선 제거"""
        try:
            if len(points) < 3:
                return
            
            # 턱선 영역의 랜드마크 순서
            # jawline_area indices: [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 58, 132, 137, 123, 50, 207, 212, 202, 204, 194, 201, 200, 421, 418, 424, 422, 432, 427, 280, 352]
            
            # 연속 선분들을 곡선으로 그리기 (끊어지는 부분 제외)
            # 세그먼트 1: 0~15 (172 ~ 323)
            if len(points) > 15:
                segment1 = points[0:16]  # 172 ~ 323
                self._draw_smooth_curve(segment1, color, line_width)
            
            # 세그먼트 2: 16~끝 (58 ~ 352) - 323->58 연결은 제외하고 시작
            if len(points) > 16:
                segment2 = points[16:]  # 58 ~ 352
                self._draw_smooth_curve(segment2, color, line_width)
            
            # 특별 연결: 58번(인덱스 16)과 172번(인덱스 0)을 부드럽게 연결
            if len(points) > 16:
                special_connection_1 = [points[16], points[0]]  # 58 -> 172
                self._draw_smooth_curve(special_connection_1, color, line_width)
            
            # 특별 연결: 352번(인덱스 35)과 323번(인덱스 15)을 부드럽게 연결
            if len(points) > 35:
                special_connection_2 = [points[35], points[15]]  # 352 -> 323
                self._draw_smooth_curve(special_connection_2, color, line_width)
            
            # 마지막 점(352, 인덱스 35)과 첫 번째 점(172, 인덱스 0)의 연결은 제외
            # (닫힌 다각형을 만들지 않음)
            
        except Exception as e:
            print(f"턱선 선 그리기 오류: {str(e)}")
    
    def _draw_jawline_basic_lines(self, points, color, line_width):
        """턱선 기본 선 그리기 - 사용자 지정 순서대로 연결"""
        try:
            if len(points) < 19:
                return
            
            # 턱선 랜드마크: [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 58, 132, 137]
            # 인덱스:        [0,   1,   2,   3,   4,   5,   6,   7,   8,   9,   10,  11,  12,  13,  14,  15,  16, 17,  18]
            
            # 랜드마크 번호를 인덱스로 매핑
            landmark_to_index = {
                172: 0, 136: 1, 150: 2, 149: 3, 176: 4, 148: 5, 152: 6, 377: 7, 400: 8, 378: 9,
                379: 10, 365: 11, 397: 12, 288: 13, 361: 14, 323: 15, 58: 16, 132: 17, 137: 18
            }
            
            # 사용자 지정 순서: 137 -> 132 -> 58 -> 172 -> 136 -> 150 -> 149 -> 176 -> 148 -> 152 -> 377 -> 400 -> 378 -> 379 -> 365 -> 397 -> 288 -> 361 -> 323
            draw_order = [137, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323]
            
            # 순서대로 점들을 수집
            ordered_points = []
            for landmark_num in draw_order:
                if landmark_num in landmark_to_index:
                    index = landmark_to_index[landmark_num]
                    if index < len(points):
                        ordered_points.append(points[index])
            
            # 지정된 순서대로 부드러운 곡선으로 그리기
            if len(ordered_points) > 1:
                self._draw_smooth_curve(ordered_points, color, line_width)
                
        except Exception as e:
            print(f"턱선 기본 선 그리기 오류: {str(e)}")
    
    def _draw_eyebrow_lines(self, points, color, line_width):
        """눈썹 선 그리기 - 좌우 눈썹 분리 처리 및 특별 연결"""
        try:
            if len(points) < 4:
                return
            
            # 눈썹은 좌우로 분리되어 있으므로 중간 지점으로 나눔
            mid_point = len(points) // 2
            
            # 왼쪽 눈썹 연결 (첫 절반) - 부드러운 곡선으로
            left_eyebrow = points[:mid_point]
            if len(left_eyebrow) > 1:
                self._draw_smooth_curve(left_eyebrow, color, line_width)
                
                # 65(인덱스 9)와 55(인덱스 0) 연결 - 부드럽게
                if len(left_eyebrow) >= 10:
                    closing_points = [left_eyebrow[9], left_eyebrow[0]]  # 65 -> 55
                    self._draw_smooth_curve(closing_points, color, line_width)
            
            # 오른쪽 눈썹 연결 (나머지 절반) - 부드러운 곡선으로
            right_eyebrow = points[mid_point:]
            if len(right_eyebrow) > 1:
                self._draw_smooth_curve(right_eyebrow, color, line_width)
                
                # 295(인덱스 9)와 285(인덱스 0) 연결 - 부드럽게
                if len(right_eyebrow) >= 10:
                    closing_points = [right_eyebrow[9], right_eyebrow[0]]  # 295 -> 285
                    self._draw_smooth_curve(closing_points, color, line_width)
                    
        except Exception as e:
            print(f"눈썹 선 그리기 오류: {str(e)}")
    
    def _draw_closed_polygon_lines(self, points, color, line_width):
        """닫힌 다각형 선 그리기"""
        try:
            if len(points) < 3:
                return
            
            # 부드러운 닫힌 곡선으로 연결 (마지막 점과 첫 번째 점도 자동 연결)
            closed_points = points + [points[0]]
            self._draw_smooth_curve(closed_points, color, line_width)
            
        except Exception as e:
            print(f"닫힌 다각형 선 그리기 오류: {str(e)}")
    
    def _draw_cheek_area_lines(self, points, color, line_width, group_name):
        """볼영역 선 그리기 - 특별 연결 처리"""
        try:
            if len(points) < 3:
                return
            
            # 볼영역 랜드마크에서 50(왼쪽)과 280(오른쪽) 제외하고 연결
            if group_name == "cheek_area_left":
                # 왼쪽 볼: 50 제외 (마지막에서 두번째), 특별 연결 추가
                # indices: [116, 117, 118, 119, 120, 121, 126, 142, 36, 205, 147, 187, 123, 50]
                # 123-147 연결, 187-206 연결 (206은 없으므로 205로 가정)
                filtered_points = points[:-1]  # 50 제외
                
                # 각 세그먼트를 부드러운 곡선으로 그리기
                # 세그먼트 1: 0~9 (끊어지는 부분 전까지)
                if len(filtered_points) > 9:
                    segment1 = filtered_points[0:10]  # 116~205
                    self._draw_smooth_curve(segment1, color, line_width)
                
                # 세그먼트 2: 10~11 (147~187)
                if len(filtered_points) > 11:
                    segment2 = filtered_points[10:12]  # 147~187
                    self._draw_smooth_curve(segment2, color, line_width)
                
                # 세그먼트 3: 12 (123)
                # 특별 연결들을 부드러운 곡선으로
                if len(filtered_points) > 12:
                    # 123-147 연결
                    connection1 = [filtered_points[12], filtered_points[10]]  # 123 -> 147
                    self._draw_smooth_curve(connection1, color, line_width)
                    
                    # 187-205 연결 
                    connection2 = [filtered_points[11], filtered_points[9]]   # 187 -> 205
                    self._draw_smooth_curve(connection2, color, line_width)
                
                # 닫힌 다각형 연결
                if len(filtered_points) > 2:
                    closing_connection = [filtered_points[-1], filtered_points[0]]
                    self._draw_smooth_curve(closing_connection, color, line_width)
                    
            elif group_name == "cheek_area_right":
                # 오른쪽 볼: 280 제외, 특별 연결 추가
                # indices: [345, 346, 347, 348, 349, 350, 355, 371, 266, 425, 376, 411, 352, 280]
                # 152-376 연결, 411-425 연결 (152가 없으므로 352로 가정)
                filtered_points = points[:-1]  # 280 제외
                
                # 각 세그먼트를 부드러운 곡선으로 그리기
                # 세그먼트 1: 0~9 (끊어지는 부분 전까지)
                if len(filtered_points) > 9:
                    segment1 = filtered_points[0:10]  # 345~425
                    self._draw_smooth_curve(segment1, color, line_width)
                
                # 세그먼트 2: 10~11 (376~411)
                if len(filtered_points) > 11:
                    segment2 = filtered_points[10:12]  # 376~411
                    self._draw_smooth_curve(segment2, color, line_width)
                
                # 특별 연결들을 부드러운 곡선으로
                if len(filtered_points) > 12:
                    # 352-376 연결
                    connection1 = [filtered_points[12], filtered_points[10]]  # 352 -> 376
                    self._draw_smooth_curve(connection1, color, line_width)
                    
                    # 425-411 연결 
                    connection2 = [filtered_points[9], filtered_points[11]]   # 425 -> 411
                    self._draw_smooth_curve(connection2, color, line_width)
                
                # 닫힌 다각형 연결
                if len(filtered_points) > 2:
                    closing_connection = [filtered_points[-1], filtered_points[0]]
                    self._draw_smooth_curve(closing_connection, color, line_width)
            else:
                # 기본 연결
                self._draw_closed_polygon_lines(points, color, line_width)
                
        except Exception as e:
            print(f"볼영역 선 그리기 오류: {str(e)}")
    
    def _draw_continuous_lines(self, points, color, line_width):
        """연속 선 그리기 (팔자주름 등) - 부드러운 곡선으로"""
        try:
            if len(points) < 2:
                return
                
            # 부드러운 연속 곡선으로 연결
            self._draw_smooth_curve(points, color, line_width)
                
        except Exception as e:
            print(f"연속 선 그리기 오류: {str(e)}")
    
    def _draw_nasolabial_lines(self, points, color, line_width, group_name):
        """팔자주름 선 그리기 - 특별 연결 처리"""
        try:
            if len(points) < 2:
                return
                
            if group_name == "nasolabial_right":
                # 우측 팔자주름 특별 연결: 360-363, 363-355, 360-278 추가
                # indices: [355, 371, 266, 436, 432, 422, 424, 418, 405, 291, 391, 278, 360, 321, 363]
                # 363-321 삭제, 360-321 삭제, 360-363 연결, 363-355 연결, 360-278 연결 추가
                
                # 특별 연결을 위한 점들 순서 재구성
                if len(points) > 14:
                    # 기본 연결 부분 (0~11): 355~278까지 부드러운 곡선
                    main_curve_points = points[0:12]  # 355부터 278까지
                    self._draw_smooth_curve(main_curve_points, color, line_width)
                    
                    # 360-363 특별 연결 (부드러운 곡선)
                    special_points_1 = [points[12], points[14]]  # 360, 363
                    self._draw_smooth_curve(special_points_1, color, line_width)
                    
                    # 363-355 특별 연결 (부드러운 곡선)
                    special_points_2 = [points[14], points[0]]  # 363, 355
                    self._draw_smooth_curve(special_points_2, color, line_width)
                    
                    # 360-278 특별 연결 추가 (부드러운 곡선)
                    special_points_3 = [points[12], points[11]]  # 360, 278
                    self._draw_smooth_curve(special_points_3, color, line_width)
                else:
                    # 점이 부족한 경우 일반 연속 연결
                    self._draw_continuous_lines(points, color, line_width)
                    
            elif group_name == "nasolabial_left":
                # 좌측 팔자주름: 일반 연속 연결 + 142-126 연결 추가
                # indices: [126, 131, 49, 129, 165, 61, 181, 194, 204, 202, 212, 216, 36, 142]
                if len(points) > 13:
                    # 기본 연속 연결
                    self._draw_continuous_lines(points, color, line_width)
                    
                    # 142-126 특별 연결 추가 (부드러운 곡선)
                    special_points = [points[13], points[0]]  # 142, 126
                    self._draw_smooth_curve(special_points, color, line_width)
                else:
                    # 점이 부족한 경우 일반 연속 연결만
                    self._draw_continuous_lines(points, color, line_width)
                
        except Exception as e:
            print(f"팔자주름 선 그리기 오류: {str(e)}")
    
    def _draw_nose_bridge_lines(self, points, color, line_width):
        """코 기둥 선 그리기 - 사용자 지정 연결 순서"""
        try:
            if len(points) < 2:
                return
            
            # 코 기둥 랜드마크: [4, 5, 6, 19, 94, 168, 195, 197]
            # 인덱스:           [0, 1, 2, 3,  4,  5,   6,   7]
            # 사용자 지정 연결 순서: 168->6->197->195->5->4->19->94
            
            # 랜드마크를 딕셔너리로 매핑 (랜드마크 번호 -> 좌표)
            landmark_map = {}
            landmark_indices = [4, 5, 6, 19, 94, 168, 195, 197]  # 원본 순서
            for i, landmark_num in enumerate(landmark_indices):
                if i < len(points):
                    landmark_map[landmark_num] = points[i]
            
            # 사용자 지정 연결 순서
            connection_sequence = [168, 6, 197, 195, 5, 4, 19, 94]
            
            # 지정된 순서대로 선 연결
            for i in range(len(connection_sequence) - 1):
                start_landmark = connection_sequence[i]
                end_landmark = connection_sequence[i + 1]
                
                # 해당 랜드마크가 존재하는지 확인
                if start_landmark in landmark_map and end_landmark in landmark_map:
                    x1, y1 = landmark_map[start_landmark]
                    x2, y2 = landmark_map[end_landmark]
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        smooth=True,
                        tags="landmarks"
                    )
                
        except Exception as e:
            print(f"코 기둥 선 그리기 오류: {str(e)}")
    
    def _draw_nose_wings_lines(self, points, color, line_width):
        """콧볼 선 그리기 - 지정된 순서대로 연결"""
        try:
            if len(points) < 14:
                return
            
            # 콧볼 랜드마크: [45, 129, 64, 98, 97, 115, 220, 275, 278, 294, 326, 327, 344, 440]
            # 인덱스:        [0,  1,   2,  3,  4,  5,   6,   7,   8,   9,   10,  11,  12,  13]
            
            # 랜드마크 번호를 인덱스로 매핑
            landmark_to_index = {
                45: 0, 129: 1, 64: 2, 98: 3, 97: 4, 115: 5,
                220: 6, 275: 7, 278: 8, 294: 9, 326: 10, 327: 11, 344: 12, 440: 13
            }
            
            # 사용자 지정 순서: 115 -> 129 -> 64 -> 98 -> 97 -> 326 -> 327 -> 294 -> 278 -> 344 -> 440 -> 275 -> 45 -> 220 -> 115
            draw_order = [115, 129, 64, 98, 97, 326, 327, 294, 278, 344, 440, 275, 45, 220, 115]
            
            # 순서대로 점들을 수집
            ordered_points = []
            for landmark_num in draw_order:
                if landmark_num in landmark_to_index:
                    index = landmark_to_index[landmark_num]
                    if index < len(points):
                        ordered_points.append(points[index])
            
            # 지정된 순서대로 부드러운 곡선으로 그리기
            if len(ordered_points) > 1:
                self._draw_smooth_curve(ordered_points, color, line_width)
                
        except Exception as e:
            print(f"콧볼 선 그리기 오류: {str(e)}")
    
    def _draw_nose_side_lines(self, points, color, line_width):
        """코 측면 선 그리기 - 부드러운 곡선으로"""
        try:
            print(f"_draw_nose_side_lines 호출됨: 점 개수 {len(points)}, 색상 {color}")
            if len(points) < 2:
                print("점이 부족합니다 (2개 미만)")
                return
            
            # 전체 점들을 하나의 부드러운 곡선으로 그리기
            self._draw_smooth_curve(points, color, line_width)
                
        except Exception as e:
            print(f"코 측면 선 그리기 오류: {str(e)}")
    
    def _draw_eyelid_lower_surround_area_lines(self, points, color, line_width):
        """하주변영역 선 그리기 - 특별 연결 규칙 적용"""
        try:
            if len(points) < 4:
                return
            
            # 하주변영역을 4개 세그먼트로 나누어 곡선 그리기
            # 왼쪽 하꺼풀: [226, 25, 110, 24, 23, 22, 26, 112, 243]  (인덱스 0-8)
            if len(points) > 8:
                left_lower_lid = points[0:9]  # 226 ~ 243
                self._draw_smooth_curve(left_lower_lid, color, line_width)
            
            # 왼쪽 하주변: [35, 31, 228, 229, 230, 231, 232, 233, 244]  (인덱스 9-17)
            if len(points) > 17:
                left_lower_surround = points[9:18]  # 35 ~ 244
                self._draw_smooth_curve(left_lower_surround, color, line_width)
            
            # 오른쪽 하꺼풀: [463, 341, 256, 252, 253, 254, 339, 255, 446]  (인덱스 18-26)
            if len(points) > 26:
                right_lower_lid = points[18:27]  # 463 ~ 446
                self._draw_smooth_curve(right_lower_lid, color, line_width)
            
            # 오른쪽 하주변: [465, 453, 452, 451, 450, 449, 448, 261, 265]  (인덱스 27-35)
            if len(points) > 35:
                right_lower_surround = points[27:36]  # 465 ~ 265
                self._draw_smooth_curve(right_lower_surround, color, line_width)
            
            # 특별 연결들을 곡선으로 추가
            if len(points) > 35:
                # 35-226 연결 (인덱스 9->0)
                connection1 = [points[9], points[0]]   # 35 -> 226
                self._draw_smooth_curve(connection1, color, line_width)
                
                # 243-244 연결 (인덱스 8->17)
                if len(points) > 17:
                    connection2 = [points[8], points[17]]  # 243 -> 244
                    self._draw_smooth_curve(connection2, color, line_width)
                
                # 465-463 연결 (인덱스 27->18)
                if len(points) > 27:
                    connection3 = [points[27], points[18]]  # 465 -> 463
                    self._draw_smooth_curve(connection3, color, line_width)
                
                # 446-265 연결 (인덱스 26->35)
                if len(points) > 26:
                    connection4 = [points[26], points[35]]  # 446 -> 265
                    self._draw_smooth_curve(connection4, color, line_width)
            
            # 닫힌 다각형 연결 (265-226) 삭제 - 사용자 요청에 따라 제거
                
        except Exception as e:
            print(f"하주변영역 선 그리기 오류: {str(e)}")
    
    def draw_landmark_legend(self):
        """랜드마크 범례 표시"""
        try:
            legend_items = [
                ("👀 눈", "#00ff00"),
                ("👁️ 눈동자", "#00ccff"),
                ("👆 상 눈꺼풀", "#66ff66"),
                ("👇 하 눈꺼풀", "#99ff99"),
                ("🔍 상 주변", "#ccffcc"),
                ("🔍 하 주변", "#e6ffe6"),
                ("🔴 코끝", "#ff0000"),
                ("🟠 코기둥", "#ff4400"),
                ("🟡 콧볼", "#ff8800"),
                ("🟨 코측면", "#ffcc00"),
                ("💋 윗입술", "#ff3300"),
                ("👄 아래입술", "#ff6600"),
                ("🦴 턱선", "#0066ff"),
                ("🤨 눈썹", "#9900ff"),
                ("🏛️ 이마", "#ffdd99"),
                ("👁️‍🗨️ 미간", "#ffcc88"),
                ("😊 광대", "#ff0099"),
                ("😶 좌측볼", "#ff6699"),
                ("😶 우측볼", "#ff6699")
            ]
            
            legend_x = 10
            legend_y = 10
            
            # 범례 배경
            legend_bg = self.canvas.create_rectangle(
                legend_x - 5, legend_y - 5,
                legend_x + 120, legend_y + len(legend_items) * 25 + 5,
                fill="white", outline="gray", width=1,
                tags="landmarks"
            )
            
            # 범례 항목들
            for i, (label, color) in enumerate(legend_items):
                y_pos = legend_y + i * 25
                
                # 색상 점
                self.canvas.create_oval(
                    legend_x, y_pos,
                    legend_x + 10, y_pos + 10,
                    fill=color, outline="white", width=1,
                    tags="landmarks"
                )
                
                # 라벨
                self.canvas.create_text(
                    legend_x + 15, y_pos + 5,
                    text=label, anchor="w",
                    font=("Arial", 8), fill="black",
                    tags="landmarks"
                )
                
        except Exception as e:
            print(f"범례 표시 오류: {str(e)}")
    
    def create_landmark_group_buttons(self, parent_frame):
        """랜드마크 그룹별 토글 버튼 생성"""
        # 그룹 정의 (UI 표시용)
        group_definitions = [
            # 눈 영역
            ("eyes", "👀 눈", "#00ff00"),
            ("iris", "👁️ 눈동자", "#00ccff"),
            ("eyelid_upper", "👆 상꺼풀", "#66ff66"),
            ("eyelid_lower", "👇 하꺼풀", "#99ff99"),
            ("eyelid_surround_upper", "🔍 상주변", "#ccffcc"),
            ("eyelid_surround_lower", "🔍 하주변", "#e6ffe6"),
            ("eyelid_lower_surround_area", "👁️‍🗨️ 하주변영역", "#b3ffb3"),
            ("eyelid_lower_area", "👁️ 하꺼풀영역", "#66ccff"),
            ("eyelid_upper_surround_area", "👁️‍🗨️ 상주변영역", "#cccc66"),
            ("eyelid_upper_area", "👁️ 상꺼풀영역", "#ff9966"),
            # 코 영역
            ("nose_tip", "🔴 코끝", "#ff0000"),
            ("nose_bridge", "🟠 코기둥", "#ff4400"),
            ("nose_wings", "🟡 콧볼", "#ff8800"),
            ("nose_sides", "🟨 코측면", "#ffcc00"),
            # 입술
            ("lip_upper", "💋 윗입술", "#ff3300"),
            ("lip_lower", "👄 아래입술", "#ff6600"),
            # 기타
            ("jawline", "🦴 턱선", "#0066ff"),
            ("jawline_area", "🦴 턱선영역", "#0088ff"),
            ("mouth_area", "👄 입주변영역", "#ff9966"),
            ("nose_area", "👃 코주변영역", "#ffdd66"),
            ("nasolabial", "😔 팔자주름", "#cc99ff"),
            ("eyebrow_area", "🤨 눈썹주변영역", "#bb77ff"),
            ("eyebrows", "🤨 눈썹", "#9900ff"),
            ("forehead", "🏛️ 이마", "#ffdd99"),
            ("glabella", "👁️‍🗨️ 미간", "#ffcc88"),
            ("cheekbones", "😊 광대", "#ff0099"),
            ("cheek_area", "😶 볼영역", "#ff6699")
        ]
        
        # 스크롤 가능한 프레임 생성 (토글 영역 높이 조정 - 100픽셀 증가)
        canvas = tk.Canvas(parent_frame, height=400)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # 스크롤 영역 업데이트 함수
        def update_scroll_region(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", update_scroll_region)
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 마우스 휠 스크롤 바인딩 (부위별 표시 전용)
        def _on_group_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # 마우스가 캔버스 위에 있을 때만 스크롤 동작
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_group_mousewheel)
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            
        canvas.bind("<Enter>", bind_mousewheel)
        canvas.bind("<Leave>", unbind_mousewheel)
        
        # 그룹별 체크버튼 생성
        row = 0
        col = 0
        for group_key, label, color in group_definitions:
            if group_key in self.landmark_group_visibility:
                # 체크버튼 프레임
                check_frame = ttk.Frame(scrollable_frame)
                check_frame.grid(row=row, column=col, sticky="w", padx=2, pady=1)
                
                # 체크버튼
                chk = ttk.Checkbutton(
                    check_frame,
                    text=label,
                    variable=self.landmark_group_visibility[group_key],
                    command=self.refresh_landmarks
                )
                chk.pack(side=tk.LEFT)
                
                # 색상 표시
                color_label = tk.Label(check_frame, text="●", fg=color, font=("Arial", 12))
                color_label.pack(side=tk.LEFT, padx=(2, 0))
                
                # 2열로 배치
                col += 1
                if col >= 2:
                    col = 0
                    row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 토글 버튼 생성 완료 후 스크롤 영역 강제 업데이트
        canvas.update_idletasks()
        update_scroll_region()
    
    def select_all_groups(self):
        """모든 랜드마크 그룹 선택"""
        for var in self.landmark_group_visibility.values():
            var.set(True)
        self.refresh_landmarks()
    
    def deselect_all_groups(self):
        """모든 랜드마크 그룹 선택 해제"""
        for var in self.landmark_group_visibility.values():
            var.set(False)
        self.refresh_landmarks()
    
    def _draw_eyelid_lower_area_lines(self, points, color, line_width):
        """하꺼풀영역 선 그리기 - 하꺼풀 + 눈 하단 랜드마크 연결"""
        try:
            if len(points) < 4:
                return
            
            # 하꺼풀영역 랜드마크 순서:
            # 왼쪽 하꺼풀: [226, 25, 110, 24, 23, 22, 26, 112, 243]  (인덱스 0-8)
            # 오른쪽 하꺼풀: [463, 341, 256, 252, 253, 254, 339, 255, 446]  (인덱스 9-17)
            # 왼쪽 눈 하단: [33, 7, 163, 144, 145, 153, 154, 155, 133]  (인덱스 18-26)
            # 오른쪽 눈 하단: [362, 382, 381, 380, 374, 373, 390, 249, 359]  (인덱스 27-35)
            
            print(f"하꺼풀영역 선 그리기: 총 {len(points)}개 점")
            
            # 1. 왼쪽 하꺼풀 부드러운 곡선 (인덱스 0-8)
            if len(points) > 8:
                left_lower_eyelid = points[0:9]
                self._draw_smooth_curve(left_lower_eyelid, color, line_width)
            
            # 2. 오른쪽 하꺼풀 부드러운 곡선 (인덱스 9-17)
            if len(points) > 17:
                right_lower_eyelid = points[9:18]
                self._draw_smooth_curve(right_lower_eyelid, color, line_width)
            
            # 3. 왼쪽 눈 하단 부드러운 곡선 (인덱스 18-26)
            if len(points) > 26:
                left_lower_eye = points[18:27]
                self._draw_smooth_curve(left_lower_eye, color, line_width)
            
            # 4. 오른쪽 눈 하단 부드러운 곡선 (인덱스 27-35)
            if len(points) > 35:
                right_lower_eye = points[27:36]
                self._draw_smooth_curve(right_lower_eye, color, line_width)
            
            # 5. 특별 연결: 하꺼풀과 눈 하단 연결 (사용자 요청에 따른 수정) - 곡선으로
            # 463(인덱스9) - 362(인덱스27) 연결
            if len(points) > 27:
                connection1 = [points[9], points[27]]  # 463 -> 362
                self._draw_smooth_curve(connection1, color, line_width)
            
            # 359(인덱스35) - 446(인덱스17) 연결
            if len(points) > 35:
                connection2 = [points[35], points[17]]  # 359 -> 446
                self._draw_smooth_curve(connection2, color, line_width)
            
            # 226(인덱스0) - 33(인덱스18) 연결
            if len(points) > 18:
                connection3 = [points[0], points[18]]  # 226 -> 33
                self._draw_smooth_curve(connection3, color, line_width)
            
            # 133(인덱스26) - 243(인덱스8) 연결
            if len(points) > 26:
                connection4 = [points[26], points[8]]  # 133 -> 243
                self._draw_smooth_curve(connection4, color, line_width)
                
        except Exception as e:
            print(f"하꺼풀영역 선 그리기 오류: {str(e)}")
    
    def _draw_eyelid_upper_surround_area_lines(self, points, color, line_width):
        """상주변영역 선 그리기 - 상꺼풀 + 상주변 랜드마크 연결"""
        try:
            if len(points) < 4:
                return
            
            # 상주변영역 랜드마크 순서:
            # 왼쪽 상꺼풀: [226, 247, 30, 29, 27, 28, 56, 190, 243]  (인덱스 0-8)
            # 왼쪽 상주변: [35, 113, 225, 224, 223, 222, 221, 189, 244]  (인덱스 9-17)
            # 오른쪽 상꺼풀: [463, 414, 286, 258, 257, 260, 467, 446]  (인덱스 18-25)
            # 오른쪽 상주변: [465, 413, 441, 442, 443, 444, 445, 342, 265]  (인덱스 26-34)
            
            print(f"상주변영역 선 그리기: 총 {len(points)}개 점")
            
            # 1. 왼쪽 상꺼풀 부드러운 곡선 (인덱스 0-8)
            if len(points) > 8:
                left_upper_eyelid = points[0:9]
                self._draw_smooth_curve(left_upper_eyelid, color, line_width)
            
            # 2. 왼쪽 상주변 부드러운 곡선 (인덱스 9-17)
            if len(points) > 17:
                left_upper_surround = points[9:18]
                self._draw_smooth_curve(left_upper_surround, color, line_width)
            
            # 3. 오른쪽 상꺼풀 부드러운 곡선 (인덱스 18-25)
            if len(points) > 25:
                right_upper_eyelid = points[18:26]
                self._draw_smooth_curve(right_upper_eyelid, color, line_width)
            
            # 4. 오른쪽 상주변 부드러운 곡선 (인덱스 26-34)
            if len(points) > 34:
                right_upper_surround = points[26:35]
                self._draw_smooth_curve(right_upper_surround, color, line_width)
            
            # 5. 특별 연결: 상꺼풀과 상주변 연결 - 곡선으로
            # 왼쪽: 226(인덱스0) - 35(인덱스9) 연결
            if len(points) > 9:
                connection1 = [points[0], points[9]]   # 226 -> 35
                self._draw_smooth_curve(connection1, color, line_width)
            
            # 왼쪽: 243(인덱스8) - 244(인덱스17) 연결
            if len(points) > 17:
                connection2 = [points[8], points[17]]  # 243 -> 244
                self._draw_smooth_curve(connection2, color, line_width)
            
            # 오른쪽: 463(인덱스18) - 465(인덱스26) 연결
            if len(points) > 26:
                connection3 = [points[18], points[26]]  # 463 -> 465
                self._draw_smooth_curve(connection3, color, line_width)
            
            # 오른쪽: 446(인덱스25) - 265(인덱스34) 연결
            if len(points) > 34:
                connection4 = [points[25], points[34]]  # 446 -> 265
                self._draw_smooth_curve(connection4, color, line_width)
                
        except Exception as e:
            print(f"상주변영역 선 그리기 오류: {str(e)}")
    
    def _draw_eyelid_upper_area_lines(self, points, color, line_width):
        """상꺼풀영역 선 그리기 - 상꺼풀 + 눈 상단 랜드마크 연결"""
        try:
            if len(points) < 4:
                return
            
            # 상꺼풀영역 랜드마크 순서:
            # 왼쪽 상꺼풀: [226, 247, 30, 29, 27, 28, 56, 190, 243]  (인덱스 0-8)
            # 오른쪽 상꺼풀: [463, 414, 286, 258, 257, 260, 467, 446]  (인덱스 9-16)
            # 왼쪽 눈 상단: [33, 246, 161, 160, 159, 158, 157, 173, 133]  (인덱스 17-25)
            # 오른쪽 눈 상단: [362, 398, 384, 385, 386, 387, 388, 466, 263, 359]  (인덱스 26-35)
            
            print(f"상꺼풀영역 선 그리기: 총 {len(points)}개 점")
            
            # 1. 왼쪽 상꺼풀 부드러운 곡선 (인덱스 0-8)
            if len(points) > 8:
                left_upper_eyelid = points[0:9]
                self._draw_smooth_curve(left_upper_eyelid, color, line_width)
            
            # 2. 오른쪽 상꺼풀 부드러운 곡선 (인덱스 9-16)
            if len(points) > 16:
                right_upper_eyelid = points[9:17]
                self._draw_smooth_curve(right_upper_eyelid, color, line_width)
            
            # 3. 왼쪽 눈 상단 부드러운 곡선 (인덱스 17-25)
            if len(points) > 25:
                left_upper_eye = points[17:26]
                self._draw_smooth_curve(left_upper_eye, color, line_width)
            
            # 4. 오른쪽 눈 상단 부드러운 곡선 (인덱스 26-35)
            if len(points) > 35:
                right_upper_eye = points[26:36]
                self._draw_smooth_curve(right_upper_eye, color, line_width)
            
            # 5. 특별 연결: 상꺼풀과 눈 상단 연결 - 곡선으로
            # 왼쪽: 226(인덱스0) - 33(인덱스17) 연결
            if len(points) > 17:
                connection1 = [points[0], points[17]]   # 226 -> 33
                self._draw_smooth_curve(connection1, color, line_width)
            
            # 왼쪽: 243(인덱스8) - 133(인덱스25) 연결
            if len(points) > 25:
                connection2 = [points[8], points[25]]   # 243 -> 133
                self._draw_smooth_curve(connection2, color, line_width)
            
            # 오른쪽: 463(인덱스9) - 362(인덱스26) 연결
            if len(points) > 26:
                connection3 = [points[9], points[26]]   # 463 -> 362
                self._draw_smooth_curve(connection3, color, line_width)
            
            # 오른쪽: 446(인덱스16) - 359(인덱스35) 연결
            if len(points) > 35:
                connection4 = [points[16], points[35]]  # 446 -> 359
                self._draw_smooth_curve(connection4, color, line_width)
                
        except Exception as e:
            print(f"상꺼풀영역 선 그리기 오류: {str(e)}")
    
    
    def get_visibility_key(self, group_name):
        """그룹 이름을 가시성 키로 변환"""
        # 랜드마크 그룹 이름을 가시성 딕셔너리 키로 매핑
        mapping = {
            "eyes_left": "eyes",
            "eyes_right": "eyes",
            "iris_left": "iris",
            "iris_right": "iris", 
            "eyelid_upper_left": "eyelid_upper",
            "eyelid_upper_right": "eyelid_upper",
            "eyelid_lower_left": "eyelid_lower",
            "eyelid_lower_right": "eyelid_lower",
            "eyelid_surround_upper_left": "eyelid_surround_upper",
            "eyelid_surround_upper_right": "eyelid_surround_upper",
            "eyelid_surround_lower_left": "eyelid_surround_lower",
            "eyelid_surround_lower_right": "eyelid_surround_lower",
            "eyelid_lower_surround_area": "eyelid_lower_surround_area",
            "nose_tip": "nose_tip",
            "nose_bridge": "nose_bridge", 
            "nose_wings": "nose_wings",
            "nose_sides": "nose_sides",
            "nose_side_left": "nose_sides",
            "nose_side_right": "nose_sides",
            "lip_upper": "lip_upper",
            "lip_lower": "lip_lower",
            "jawline": "jawline",
            "jawline_area": "jawline_area",
            "mouth_area": "mouth_area",
            "nose_area": "nose_area",
            "nasolabial_left": "nasolabial",
            "nasolabial_right": "nasolabial",
            "eyebrow_area": "eyebrow_area",
            "eyebrows": "eyebrows",
            "forehead": "forehead",
            "glabella": "glabella",
            "cheekbones": "cheekbones",
            "cheek_area_left": "cheek_area",
            "cheek_area_right": "cheek_area"
        }
        
        return mapping.get(group_name, group_name)
    
    def clear_preset_visualization(self):
        """프리셋 시각화 요소들 제거"""
        self.canvas.delete("preset_visualization")
    
    def bring_preset_visualization_to_front(self):
        """프리셋 시각화 요소들을 맨 앞으로 가져오기"""
        try:
            preset_items = self.canvas.find_withtag("preset_visualization")
            
            print(f"맨 앞으로 가져올 프리셋 요소: {len(preset_items)}개")
            
            # 모든 프리셋 시각화 요소를 맨 앞으로
            for item in preset_items:
                self.canvas.tag_raise(item)
                
            print("프리셋 시각화 요소들을 맨 앞으로 이동 완료")
            
        except Exception as e:
            print(f"프리셋 시각화 맨 앞으로 가져오기 오류: {str(e)}")
    
    def draw_preset_visualization(self, start_point, end_point, influence_radius_px, strength, label="", ellipse_ratio=None):
        """프리셋 시각화 요소 그리기"""
        if not self.show_preset_visualization.get():
            print(f"시각화 비활성화됨")
            return
            
        print(f"시각화 그리기 시작: {label}, 출발점: {start_point}, 끝점: {end_point}")
        try:
            # 화면 좌표로 변환
            start_screen = self.image_to_screen_coords(start_point[0], start_point[1])
            end_screen = self.image_to_screen_coords(end_point[0], end_point[1])
            
            if not start_screen or not end_screen:
                print(f"좌표 변환 실패: start_screen={start_screen}, end_screen={end_screen}")
                return
                
            start_x, start_y = start_screen
            end_x, end_y = end_screen
            print(f"화면 좌표: 시작({start_x:.1f}, {start_y:.1f}), 끝({end_x:.1f}, {end_y:.1f})")
            
            # 화면상 영향반경 크기
            screen_radius = influence_radius_px * self.scale_factor * self.zoom_factor
            
            print(f"Canvas 요소 그리기 시작, 화면반경: {screen_radius:.1f}")
            
            # 1. 출발점 표시 (빨간 원) - 80% 작게
            start_oval = self.canvas.create_oval(
                start_x - 1.4, start_y - 1.4, start_x + 1.4, start_y + 1.4,
                fill="#ff0000", outline="",
                tags="preset_visualization"
            )
            print(f"출발점 원 생성: ID={start_oval}")
            
            # 2. 끝점 표시 (파란 원) - 80% 작게
            end_oval = self.canvas.create_oval(
                end_x - 1.4, end_y - 1.4, end_x + 1.4, end_y + 1.4,
                fill="#0000ff", outline="",
                tags="preset_visualization"
            )
            print(f"끝점 원 생성: ID={end_oval}")
            
            # 3. 방향 화살표 - 80% 작게
            arrow_line = self.canvas.create_line(
                start_x, start_y, end_x, end_y,
                fill="#ff6600", width=1, arrow=tk.LAST, arrowshape=(4, 5, 2),
                tags="preset_visualization"
            )
            print(f"화살표 생성: ID={arrow_line}")
            
            # 4. 영향반경 표시 (원형 또는 타원형)
            if screen_radius > 10:  # 너무 작으면 그리지 않음
                if ellipse_ratio is not None:
                    # 타원형 영향반경
                    ellipse_x_radius = screen_radius
                    ellipse_y_radius = screen_radius * ellipse_ratio
                    
                    radius_circle = self.canvas.create_oval(
                        start_x - ellipse_x_radius, start_y - ellipse_y_radius,
                        start_x + ellipse_x_radius, start_y + ellipse_y_radius,
                        outline="#ffaa00", width=2, dash=(10, 10),
                        tags="preset_visualization"
                    )
                    print(f"타원형 영향반경 생성: ID={radius_circle}, 가로={ellipse_x_radius:.1f}px, 세로={ellipse_y_radius:.1f}px")
                else:
                    # 원형 영향반경 (기존 방식)
                    radius_circle = self.canvas.create_oval(
                        start_x - screen_radius, start_y - screen_radius,
                        start_x + screen_radius, start_y + screen_radius,
                        outline="#ffaa00", width=2, dash=(10, 10),
                        tags="preset_visualization"
                    )
                    print(f"원형 영향반경 생성: ID={radius_circle}, 반경={screen_radius:.1f}px")
            else:
                print(f"영향반경이 너무 작아서 건너뜀: {screen_radius:.1f}")
            
            # 모든 시각화 요소를 맨 앞으로 가져오기
            for item in self.canvas.find_withtag("preset_visualization"):
                self.canvas.tag_raise(item)
            print(f"시각화 요소 개수: {len(self.canvas.find_withtag('preset_visualization'))}")
            
            # 5. 정보 라벨 - 각 줄마다 다른 색깔로 표시
            distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            
            # 라벨 위치 (출발점 오른쪽)
            label_x = start_x + 50
            label_y = start_y - 30
            
            # 첫 번째 줄: 라벨 (파란색)
            text_label1 = self.canvas.create_text(
                label_x, label_y - 12, text=label, font=("Arial", 8, "normal"), 
                fill="#0066cc", justify=tk.CENTER, tags="preset_visualization"
            )
            
            # 두 번째 줄: 거리 (초록색)
            text_label2 = self.canvas.create_text(
                label_x, label_y, text=f"거리: {distance/self.scale_factor/self.zoom_factor:.1f}px", 
                font=("Arial", 8, "normal"), fill="#00aa00", justify=tk.CENTER, tags="preset_visualization"
            )
            
            # 세 번째 줄: 강도 (빨간색)
            text_label3 = self.canvas.create_text(
                label_x, label_y + 12, text=f"강도: {strength:.1f}x", 
                font=("Arial", 8, "normal"), fill="#cc0000", justify=tk.CENTER, tags="preset_visualization"
            )
            print(f"라벨 텍스트 생성: ID1={text_label1}, ID2={text_label2}, ID3={text_label3}")
            
            # 최종 레이어링 확인
            print(f"최종 시각화 요소들 맨 앞으로 이동")
            for item in self.canvas.find_withtag("preset_visualization"):
                self.canvas.tag_raise(item)
                
        except Exception as e:
            print(f"시각화 그리기 오류: {str(e)}")
    
    def image_to_screen_coords(self, img_x, img_y):
        """이미지 좌표를 화면 좌표로 변환"""
        try:
            screen_x = img_x * self.scale_factor * self.zoom_factor + self.offset_x + self.pan_x
            screen_y = img_y * self.scale_factor * self.zoom_factor + self.offset_y + self.pan_y
            return (screen_x, screen_y)
        except:
            return None
    
    def get_landmark_coordinates(self, landmark_index):
        """특정 랜드마크의 이미지 좌표 반환"""
        if (self.face_landmarks is None or 
            landmark_index >= len(self.face_landmarks.landmark)):
            return None
            
        landmark = self.face_landmarks.landmark[landmark_index]
        img_height, img_width = self.current_image.shape[:2]
        
        x = int(landmark.x * img_width)
        y = int(landmark.y * img_height)
        
        return (x, y)
    
    def calculate_distance(self, point1, point2):
        """두 점 사이의 유클리드 거리 계산"""
        if point1 is None or point2 is None:
            return 0
        
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def update_preset_counter(self, preset_type):
        """프리셋별 카운터 업데이트"""
        if preset_type == "lower_jaw":
            self.lower_jaw_shot_count += 100
            self.lower_jaw_counter_label.config(text=f"(총: {self.lower_jaw_shot_count}샷)")
            print(f"아래턱 카운터 업데이트: 총 {self.lower_jaw_shot_count}샷")
        elif preset_type == "middle_jaw":
            self.middle_jaw_shot_count += 100
            self.middle_jaw_counter_label.config(text=f"(총: {self.middle_jaw_shot_count}샷)")
            print(f"중간턱 카운터 업데이트: 총 {self.middle_jaw_shot_count}샷")
        elif preset_type == "cheek":
            self.cheek_shot_count += 100
            self.cheek_counter_label.config(text=f"(총: {self.cheek_shot_count}샷)")
            print(f"볼 카운터 업데이트: 총 {self.cheek_shot_count}샷")
        elif preset_type == "front_protusion":
            self.front_protusion_shot_count += 1
            self.front_protusion_counter_label.config(text=f"(총: {self.front_protusion_shot_count}번)")
            print(f"앞튀임 카운터 업데이트: 총 {self.front_protusion_shot_count}번")
        elif preset_type == "back_slit":
            self.back_slit_shot_count += 1
            self.back_slit_counter_label.config(text=f"(총: {self.back_slit_shot_count}번)")
            print(f"뒷트임 카운터 업데이트: 총 {self.back_slit_shot_count}번")
    
    def apply_lower_jaw_100shot_preset(self):
        """아래턱 100샷+ 프리셋 적용"""
        if self.current_image is None:
            print("이미지가 로드되지 않았습니다. 먼저 이미지를 로드해주세요.")
            return
        
        try:
            # 랜드마크 새로고침 (최신 상태로 재검출)
            print("랜드마크 재검출 중...")
            self.refresh_landmarks()
            
            if self.face_landmarks is None:
                print("얼굴이 검출되지 않았습니다. 얼굴이 명확히 보이는 이미지를 사용해주세요.")
                return
            
            # 히스토리 저장
            self.save_to_history()
            
            # 필요한 랜드마크 좌표 가져오기
            landmark_150 = self.get_landmark_coordinates(self.LOWER_JAW_TARGET_LANDMARKS[0])  # 왼쪽 턱선
            landmark_379 = self.get_landmark_coordinates(self.LOWER_JAW_TARGET_LANDMARKS[1])  # 오른쪽 턱선  
            landmark_4 = self.get_landmark_coordinates(self.LOWER_JAW_TARGET_LANDMARKS[2])    # 코 기둥 상단
            
            if not all([landmark_150, landmark_379, landmark_4]):
                print("필요한 랜드마크를 찾을 수 없습니다.")
                return
            
            # 거리 계산
            distance_150_to_4 = self.calculate_distance(landmark_150, landmark_4)
            distance_379_to_4 = self.calculate_distance(landmark_379, landmark_4)
            
            # 당기는 거리 계산
            pull_distance_150 = distance_150_to_4 * self.LOWER_JAW_PRESET_PULL_RATIO
            pull_distance_379 = distance_379_to_4 * self.LOWER_JAW_PRESET_PULL_RATIO
            
            # 프리셋 파라미터 설정
            original_radius = self.radius_var.get()
            original_strength = self.strength_var.get()
            
            # 프리셋 설정 적용
            self.radius_var.set(30.0)  # 영향 반경 30%
            self.strength_var.set(self.LOWER_JAW_PRESET_STRENGTH)  # 변형 강도
            
            # 영향 반경 픽셀 계산 (얼굴 크기 기준)
            # 랜드마크로 얼굴 크기 기준 설정
            landmark_234 = self.get_landmark_coordinates(self.LOWER_JAW_FACE_SIZE_LANDMARKS[0])
            landmark_447 = self.get_landmark_coordinates(self.LOWER_JAW_FACE_SIZE_LANDMARKS[1])
            
            if landmark_234 and landmark_447:
                face_size = self.calculate_distance(landmark_234, landmark_447)
                influence_radius_px = int(face_size * self.LOWER_JAW_PRESET_INFLUENCE_RATIO)
            else:
                # 234, 447을 찾을 수 없는 경우 기존 방식 사용
                face_width = abs(landmark_150[0] - landmark_379[0])
                influence_radius_px = int(face_width * 0.3)
            
            print(f"아래턱 100샷+ 프리셋 적용:")
            print(f"  - 랜드마크 150 좌표: {landmark_150}")
            print(f"  - 랜드마크 379 좌표: {landmark_379}")
            print(f"  - 랜드마크 4 좌표: {landmark_4}")
            if landmark_234 and landmark_447:
                print(f"  - 얼굴 크기 기준 (234↔447): {face_size:.1f}px")
                print(f"  - 영향 반경 (얼굴크기 {int(self.LOWER_JAW_PRESET_INFLUENCE_RATIO*100)}%): {influence_radius_px}px")
            else:
                print(f"  - 영향 반경 (대체 계산): {influence_radius_px}px")
            print(f"  - 150→4 거리: {distance_150_to_4:.1f}px, 당기는 거리: {pull_distance_150:.1f}px")
            print(f"  - 379→4 거리: {distance_379_to_4:.1f}px, 당기는 거리: {pull_distance_379:.1f}px")
            print(f"  - 변형 강도: {self.LOWER_JAW_PRESET_STRENGTH}x")
            
            # 기존 시각화 제거
            self.clear_preset_visualization()
            
            # 150번 랜드마크를 4번 방향으로 당기기
            # 방향 벡터 계산
            dx_150 = landmark_4[0] - landmark_150[0]
            dy_150 = landmark_4[1] - landmark_150[1]
            length_150 = math.sqrt(dx_150 * dx_150 + dy_150 * dy_150)
            
            if length_150 > 0:
                # 정규화된 방향 벡터
                unit_dx_150 = dx_150 / length_150
                unit_dy_150 = dy_150 / length_150
                
                # 당기는 목표 좌표 계산
                target_x_150 = landmark_150[0] + unit_dx_150 * pull_distance_150
                target_y_150 = landmark_150[1] + unit_dy_150 * pull_distance_150
                
                # Pull 변형 적용
                self.apply_pull_warp_with_params(
                    landmark_150[0], landmark_150[1],  # 시작점
                    target_x_150, target_y_150,       # 끝점
                    self.LOWER_JAW_PRESET_STRENGTH,   # 강도
                    influence_radius_px               # 영향반경
                )
                
                # 시각화 추가 (150번 랜드마크)
                self.draw_preset_visualization(
                    landmark_150, (target_x_150, target_y_150),
                    influence_radius_px, self.LOWER_JAW_PRESET_STRENGTH, "L-150"
                )
            
            # 379번 랜드마크를 4번 방향으로 당기기
            dx_379 = landmark_4[0] - landmark_379[0]
            dy_379 = landmark_4[1] - landmark_379[1]
            length_379 = math.sqrt(dx_379 * dx_379 + dy_379 * dy_379)
            
            if length_379 > 0:
                # 정규화된 방향 벡터
                unit_dx_379 = dx_379 / length_379
                unit_dy_379 = dy_379 / length_379
                
                # 당기는 목표 좌표 계산
                target_x_379 = landmark_379[0] + unit_dx_379 * pull_distance_379
                target_y_379 = landmark_379[1] + unit_dy_379 * pull_distance_379
                
                # Pull 변형 적용
                self.apply_pull_warp_with_params(
                    landmark_379[0], landmark_379[1],  # 시작점
                    target_x_379, target_y_379,       # 끝점
                    self.LOWER_JAW_PRESET_STRENGTH,   # 강도
                    influence_radius_px               # 영향반경
                )
                
                # 시각화 추가 (379번 랜드마크)
                self.draw_preset_visualization(
                    landmark_379, (target_x_379, target_y_379),
                    influence_radius_px, self.LOWER_JAW_PRESET_STRENGTH, "R-379"
                )
            
            # 원래 설정 복원
            self.radius_var.set(original_radius)
            self.strength_var.set(original_strength)
            
            # 화면 업데이트
            self.update_display()
            
            # update_display() 이후에 프리셋 시각화를 다시 맨 앞으로 가져오기
            self.root.after(100, self.bring_preset_visualization_to_front)
            
            # 5초 후 시각화 자동 제거
            self.root.after(5000, self.clear_preset_visualization)
            
            # 카운터 업데이트
            self.update_preset_counter("lower_jaw")
            
            print("아래턱 100샷+ 프리셋 적용 완료!")
            print("시각화는 5초 후 자동으로 사라집니다.")
            
        except Exception as e:
            print(f"아래턱 100샷+ 프리셋 적용 실패: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def apply_jaw_preset(self, preset_name, target_landmarks, face_size_landmarks, 
                         strength, influence_ratio, pull_ratio, labels, ellipse_ratio=None):
        """공통 턱선 프리셋 적용 함수"""
        if self.current_image is None:
            print("이미지가 로드되지 않았습니다. 먼저 이미지를 로드해주세요.")
            return
        
        try:
            # 랜드마크 새로고침 (최신 상태로 재검출)
            print("랜드마크 재검출 중...")
            self.refresh_landmarks()
            
            if self.face_landmarks is None:
                print("얼굴이 검출되지 않았습니다. 얼굴이 명확히 보이는 이미지를 사용해주세요.")
                return
            
            # 히스토리 저장
            self.save_to_history()
            
            # 랜드마크 좌표 가져오기 (2개 또는 4개 랜드마크 지원)
            if len(target_landmarks) == 3:
                # 기존 방식: 2개 랜드마크 + 1개 타겟
                left_landmark = self.get_landmark_coordinates(target_landmarks[0])   # 왼쪽 랜드마크
                right_landmark = self.get_landmark_coordinates(target_landmarks[1])  # 오른쪽 랜드마크  
                target_landmark = self.get_landmark_coordinates(target_landmarks[2]) # 타겟 랜드마크
                landmarks_to_transform = [left_landmark, right_landmark]
                
            elif len(target_landmarks) == 4:
                # 뒷트임+ 방식: 2개 랜드마크 + 각각 다른 중간점 타겟
                landmarks_to_transform = []
                
                # 첫 번째 랜드마크 (단일)
                landmark_1 = self.get_landmark_coordinates(target_landmarks[0])
                landmarks_to_transform.append(landmark_1)
                
                # 두 번째 랜드마크 (단일)
                landmark_2 = self.get_landmark_coordinates(target_landmarks[1])
                landmarks_to_transform.append(landmark_2)
                
                # 각 랜드마크별로 다른 타겟 중간점 계산
                target_midpoints = []
                
                # 첫 번째 랜드마크의 타겟 중간점
                if isinstance(target_landmarks[2], tuple) and len(target_landmarks[2]) == 2:
                    t1_1 = self.get_landmark_coordinates(target_landmarks[2][0])
                    t1_2 = self.get_landmark_coordinates(target_landmarks[2][1])
                    if t1_1 and t1_2:
                        target_1 = ((t1_1[0] + t1_2[0]) / 2, (t1_1[1] + t1_2[1]) / 2)
                        target_midpoints.append(target_1)
                        print(f"첫 번째 타겟 중간점: {target_landmarks[2][0]}({t1_1}) + {target_landmarks[2][1]}({t1_2}) = {target_1}")
                    else:
                        target_midpoints.append(None)
                else:
                    target_midpoints.append(None)
                
                # 두 번째 랜드마크의 타겟 중간점
                if isinstance(target_landmarks[3], tuple) and len(target_landmarks[3]) == 2:
                    t2_1 = self.get_landmark_coordinates(target_landmarks[3][0])
                    t2_2 = self.get_landmark_coordinates(target_landmarks[3][1])
                    if t2_1 and t2_2:
                        target_2 = ((t2_1[0] + t2_2[0]) / 2, (t2_1[1] + t2_2[1]) / 2)
                        target_midpoints.append(target_2)
                        print(f"두 번째 타겟 중간점: {target_landmarks[3][0]}({t2_1}) + {target_landmarks[3][1]}({t2_2}) = {target_2}")
                    else:
                        target_midpoints.append(None)
                else:
                    target_midpoints.append(None)
                
                left_landmark = landmark_1  # 호환성을 위해
                right_landmark = landmark_2  # 호환성을 위해
                target_landmark = target_midpoints[0] if target_midpoints else None  # 첫 번째 타겟
                
            elif len(target_landmarks) == 6:
                # 새로운 방식: 다양한 타입의 랜드마크 지원
                landmarks_to_transform = []
                
                # 각 랜드마크 처리 (단일 또는 중간점)
                for i in range(4):  # 처음 4개는 변형할 랜드마크
                    landmark_def = target_landmarks[i]
                    
                    if isinstance(landmark_def, tuple) and len(landmark_def) == 2:
                        # 중간점 랜드마크
                        lm1 = self.get_landmark_coordinates(landmark_def[0])
                        lm2 = self.get_landmark_coordinates(landmark_def[1])
                        if lm1 and lm2:
                            midpoint = ((lm1[0] + lm2[0]) / 2, (lm1[1] + lm2[1]) / 2)
                            landmarks_to_transform.append(midpoint)
                            print(f"중간점 랜드마크 {i}: {landmark_def[0]}({lm1}) + {landmark_def[1]}({lm2}) = {midpoint}")
                        else:
                            landmarks_to_transform.append(None)
                    else:
                        # 단일 랜드마크
                        landmark = self.get_landmark_coordinates(landmark_def)
                        landmarks_to_transform.append(landmark)
                        print(f"단일 랜드마크 {i}: {landmark_def} = {landmark}")
                
                # 타겟 중간점 계산
                target_1 = self.get_landmark_coordinates(target_landmarks[4])     # 타겟 랜드마크 1
                target_2 = self.get_landmark_coordinates(target_landmarks[5])     # 타겟 랜드마크 2
                
                if target_1 and target_2:
                    target_landmark = ((target_1[0] + target_2[0]) / 2, (target_1[1] + target_2[1]) / 2)
                    print(f"타겟 중간점 계산: {target_landmarks[4]}({target_1}) + {target_landmarks[5]}({target_2}) = {target_landmark}")
                else:
                    target_landmark = None
                    
                left_landmark = landmarks_to_transform[0] if landmarks_to_transform else None  # 호환성을 위해
                right_landmark = landmarks_to_transform[1] if len(landmarks_to_transform) > 1 else None  # 호환성을 위해
                
            else:
                print(f"지원하지 않는 랜드마크 개수: {len(target_landmarks)}")
                return
            
            # 유효성 검사
            if not target_landmark or not all(landmarks_to_transform):
                print("필요한 랜드마크를 찾을 수 없습니다.")
                return
            
            # 거리 계산
            distance_left_to_target = self.calculate_distance(left_landmark, target_landmark)
            distance_right_to_target = self.calculate_distance(right_landmark, target_landmark)
            
            # 당기는 거리 계산
            pull_distance_left = distance_left_to_target * pull_ratio
            pull_distance_right = distance_right_to_target * pull_ratio
            
            # 프리셋 파라미터 설정
            original_radius = self.radius_var.get()
            original_strength = self.strength_var.get()
            
            # 프리셋 설정 적용
            self.radius_var.set(30.0)  # 영향 반경 30%
            self.strength_var.set(strength)  # 변형 강도
            
            # 영향 반경 픽셀 계산 (얼굴 크기 기준)
            face_size_left = self.get_landmark_coordinates(face_size_landmarks[0])
            face_size_right = self.get_landmark_coordinates(face_size_landmarks[1])
            
            if face_size_left and face_size_right:
                face_size = self.calculate_distance(face_size_left, face_size_right)
                influence_radius_px = int(face_size * influence_ratio)
            else:
                # 얼굴 크기 기준점을 찾을 수 없는 경우 대체 계산
                face_width = abs(left_landmark[0] - right_landmark[0])
                influence_radius_px = int(face_width * 0.3)
            
            # 정보 출력
            print(f"{preset_name} 프리셋 적용:")
            print(f"  - 랜드마크 {target_landmarks[0]} 좌표: {left_landmark}")
            print(f"  - 랜드마크 {target_landmarks[1]} 좌표: {right_landmark}")
            print(f"  - 랜드마크 {target_landmarks[2]} 좌표: {target_landmark}")
            if face_size_left and face_size_right:
                print(f"  - 얼굴 크기 기준 ({face_size_landmarks[0]}↔{face_size_landmarks[1]}): {face_size:.1f}px")
                print(f"  - 영향 반경 (얼굴크기 {int(influence_ratio*100)}%): {influence_radius_px}px")
            else:
                print(f"  - 영향 반경 (대체 계산): {influence_radius_px}px")
            print(f"  - {target_landmarks[0]}→{target_landmarks[2]} 거리: {distance_left_to_target:.1f}px, 당기는 거리: {pull_distance_left:.1f}px")
            print(f"  - {target_landmarks[1]}→{target_landmarks[2]} 거리: {distance_right_to_target:.1f}px, 당기는 거리: {pull_distance_right:.1f}px")
            print(f"  - 변형 강도: {strength}x")
            
            # 기존 시각화 제거
            self.clear_preset_visualization()
            
            # 모든 랜드마크에 대해 변형 적용
            for i, landmark in enumerate(landmarks_to_transform):
                if not landmark:
                    continue
                
                # 타겟 좌표 결정 (개별 타겟이 있는 경우 vs 공통 타겟)
                if len(target_landmarks) == 4 and 'target_midpoints' in locals() and i < len(target_midpoints):
                    # 뒷트임+ 방식: 각 랜드마크별로 다른 타겟
                    current_target = target_midpoints[i]
                    if not current_target:
                        continue
                else:
                    # 기존 방식: 공통 타겟
                    current_target = target_landmark
                    if not current_target:
                        continue
                
                # 해당 랜드마크에서 타겟으로의 방향 및 거리 계산
                dx = current_target[0] - landmark[0]
                dy = current_target[1] - landmark[1]
                length = math.sqrt(dx * dx + dy * dy)
                
                if length > 0:
                    # 단위 벡터 계산
                    unit_dx = dx / length
                    unit_dy = dy / length
                    
                    # 당기는 거리 계산
                    distance_to_target = self.calculate_distance(landmark, current_target)
                    pull_distance = distance_to_target * pull_ratio
                    
                    # 목표 위치 계산
                    target_x = landmark[0] + unit_dx * pull_distance
                    target_y = landmark[1] + unit_dy * pull_distance
                    
                    # Pull 변형 적용
                    self.apply_pull_warp_with_params(
                        landmark[0], landmark[1],        # 시작점
                        target_x, target_y,              # 끝점
                        strength,                        # 강도
                        influence_radius_px,             # 영향반경
                        ellipse_ratio                    # 타원 비율
                    )
                    
                    # 시각화 추가 (모든 랜드마크)
                    label = labels[i] if i < len(labels) else f"LM-{target_landmarks[i]}"
                    self.draw_preset_visualization(
                        landmark, (target_x, target_y),
                        influence_radius_px, strength, label, ellipse_ratio
                    )
                    
                    print(f"랜드마크 {target_landmarks[i]} 변형 완료: ({landmark[0]:.1f}, {landmark[1]:.1f}) → ({target_x:.1f}, {target_y:.1f})")
            
            
            # 원래 설정 복원
            self.radius_var.set(original_radius)
            self.strength_var.set(original_strength)
            
            # 최종 화면 업데이트
            self.update_display()
            
            # 시각화 요소들을 맨 앞으로 가져오기 (100ms 후)
            self.root.after(100, self.bring_preset_visualization_to_front)
            
            # 5초 후 시각화 자동 제거
            self.root.after(5000, self.clear_preset_visualization)
            
            print(f"{preset_name} 프리셋 적용 완료!")
            print("시각화는 5초 후 자동으로 사라집니다.")
            
        except Exception as e:
            print(f"{preset_name} 프리셋 적용 실패: {str(e)}")
            import traceback
            traceback.print_exc()

    def apply_middle_jaw_100shot_preset(self):
        """중간턱 100샷+ 프리셋 적용"""
        if self.current_image is None:
            print("이미지가 로드되지 않았습니다. 먼저 이미지를 로드해주세요.")
            return
        
        try:
            # 랜드마크 새로고침 (최신 상태로 재검출)
            print("랜드마크 재검출 중...")
            self.refresh_landmarks()
            
            if self.face_landmarks is None:
                print("얼굴이 검출되지 않았습니다. 얼굴이 명확히 보이는 이미지를 사용해주세요.")
                return
            
            # 히스토리 저장
            self.save_to_history()
            
            # 필요한 랜드마크 좌표 가져오기
            landmark_172 = self.get_landmark_coordinates(self.MIDDLE_JAW_TARGET_LANDMARKS[0])  # 왼쪽 중간턱
            landmark_397 = self.get_landmark_coordinates(self.MIDDLE_JAW_TARGET_LANDMARKS[1])  # 오른쪽 중간턱  
            landmark_4 = self.get_landmark_coordinates(self.MIDDLE_JAW_TARGET_LANDMARKS[2])    # 코 기둥 상단
            
            if not all([landmark_172, landmark_397, landmark_4]):
                print("필요한 랜드마크를 찾을 수 없습니다.")
                return
            
            # 거리 계산
            distance_172_to_4 = self.calculate_distance(landmark_172, landmark_4)
            distance_397_to_4 = self.calculate_distance(landmark_397, landmark_4)
            
            # 당기는 거리 계산
            pull_distance_172 = distance_172_to_4 * self.MIDDLE_JAW_PRESET_PULL_RATIO
            pull_distance_397 = distance_397_to_4 * self.MIDDLE_JAW_PRESET_PULL_RATIO
            
            # 프리셋 파라미터 설정
            original_radius = self.radius_var.get()
            original_strength = self.strength_var.get()
            
            # 프리셋 설정 적용
            self.radius_var.set(30.0)  # 영향 반경 30%
            self.strength_var.set(self.MIDDLE_JAW_PRESET_STRENGTH)  # 변형 강도
            
            # 영향 반경 픽셀 계산 (얼굴 크기 기준)
            # 랜드마크로 얼굴 크기 기준 설정
            landmark_234 = self.get_landmark_coordinates(self.MIDDLE_JAW_FACE_SIZE_LANDMARKS[0])
            landmark_447 = self.get_landmark_coordinates(self.MIDDLE_JAW_FACE_SIZE_LANDMARKS[1])
            
            if landmark_234 and landmark_447:
                face_size = self.calculate_distance(landmark_234, landmark_447)
                influence_radius_px = int(face_size * self.MIDDLE_JAW_PRESET_INFLUENCE_RATIO)
            else:
                # 234, 447을 찾을 수 없는 경우 기존 방식 사용
                face_width = abs(landmark_172[0] - landmark_397[0])
                influence_radius_px = int(face_width * 0.3)
            
            print(f"중간턱 100샷+ 프리셋 적용:")
            print(f"  - 랜드마크 172 좌표: {landmark_172}")
            print(f"  - 랜드마크 397 좌표: {landmark_397}")
            print(f"  - 랜드마크 4 좌표: {landmark_4}")
            if landmark_234 and landmark_447:
                print(f"  - 얼굴 크기 기준 (234↔447): {face_size:.1f}px")
                print(f"  - 영향 반경 (얼굴크기 {int(self.MIDDLE_JAW_PRESET_INFLUENCE_RATIO*100)}%): {influence_radius_px}px")
            else:
                print(f"  - 영향 반경 (대체 계산): {influence_radius_px}px")
            print(f"  - 172→4 거리: {distance_172_to_4:.1f}px, 당기는 거리: {pull_distance_172:.1f}px")
            print(f"  - 397→4 거리: {distance_397_to_4:.1f}px, 당기는 거리: {pull_distance_397:.1f}px")
            print(f"  - 변형 강도: {self.MIDDLE_JAW_PRESET_STRENGTH}x")
            
            # 기존 시각화 제거
            self.clear_preset_visualization()
            
            # 172번 랜드마크를 4번 방향으로 당기기
            # 방향 벡터 계산
            dx_172 = landmark_4[0] - landmark_172[0]
            dy_172 = landmark_4[1] - landmark_172[1]
            length_172 = math.sqrt(dx_172 * dx_172 + dy_172 * dy_172)
            
            if length_172 > 0:
                # 정규화된 방향 벡터
                unit_dx_172 = dx_172 / length_172
                unit_dy_172 = dy_172 / length_172
                
                # 당기는 목표 좌표 계산
                target_x_172 = landmark_172[0] + unit_dx_172 * pull_distance_172
                target_y_172 = landmark_172[1] + unit_dy_172 * pull_distance_172
                
                # Pull 변형 적용
                self.apply_pull_warp_with_params(
                    landmark_172[0], landmark_172[1],  # 시작점
                    target_x_172, target_y_172,       # 끝점
                    self.MIDDLE_JAW_PRESET_STRENGTH,   # 강도
                    influence_radius_px               # 영향반경
                )
                
                # 시각화 추가 (172번 랜드마크)
                self.draw_preset_visualization(
                    landmark_172, (target_x_172, target_y_172),
                    influence_radius_px, self.MIDDLE_JAW_PRESET_STRENGTH, "L-172"
                )
            
            # 397번 랜드마크를 4번 방향으로 당기기
            dx_397 = landmark_4[0] - landmark_397[0]
            dy_397 = landmark_4[1] - landmark_397[1]
            length_397 = math.sqrt(dx_397 * dx_397 + dy_397 * dy_397)
            
            if length_397 > 0:
                # 정규화된 방향 벡터
                unit_dx_397 = dx_397 / length_397
                unit_dy_397 = dy_397 / length_397
                
                # 당기는 목표 좌표 계산
                target_x_397 = landmark_397[0] + unit_dx_397 * pull_distance_397
                target_y_397 = landmark_397[1] + unit_dy_397 * pull_distance_397
                
                # Pull 변형 적용
                self.apply_pull_warp_with_params(
                    landmark_397[0], landmark_397[1],  # 시작점
                    target_x_397, target_y_397,       # 끝점
                    self.MIDDLE_JAW_PRESET_STRENGTH,   # 강도
                    influence_radius_px               # 영향반경
                )
                
                # 시각화 추가 (397번 랜드마크)
                self.draw_preset_visualization(
                    landmark_397, (target_x_397, target_y_397),
                    influence_radius_px, self.MIDDLE_JAW_PRESET_STRENGTH, "R-397"
                )
            
            # 원래 설정 복원
            self.radius_var.set(original_radius)
            self.strength_var.set(original_strength)
            
            # 최종 화면 업데이트
            self.update_display()
            
            # 시각화 요소들을 맨 앞으로 가져오기 (100ms 후)
            self.root.after(100, self.bring_preset_visualization_to_front)
            
            # 5초 후 시각화 자동 제거
            self.root.after(5000, self.clear_preset_visualization)
            
            # 카운터 업데이트
            self.update_preset_counter("middle_jaw")
            
            print("중간턱 100샷+ 프리셋 적용 완료!")
            print("시각화는 5초 후 자동으로 사라집니다.")
            
        except Exception as e:
            print(f"중간턱 100샷+ 프리셋 적용 실패: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def apply_cheek_100shot_preset(self):
        """볼 100샷+ 프리셋 적용"""
        self.apply_jaw_preset(
            preset_name="볼 100샷+",
            target_landmarks=self.CHEEK_TARGET_LANDMARKS,
            face_size_landmarks=self.CHEEK_FACE_SIZE_LANDMARKS,
            strength=self.CHEEK_PRESET_STRENGTH,
            influence_ratio=self.CHEEK_PRESET_INFLUENCE_RATIO,
            pull_ratio=self.CHEEK_PRESET_PULL_RATIO,
            labels=["L-215", "R-435"]
        )
        # 성공 시에만 카운터 업데이트
        if self.current_image is not None and self.face_landmarks is not None:
            self.update_preset_counter("cheek")
    
    def apply_front_protusion_100shot_preset(self):
        """앞튀임+ 프리셋 적용"""
        self.apply_jaw_preset(
            preset_name="앞튀임+",
            target_landmarks=self.FRONT_PROTUSION_TARGET_LANDMARKS,
            face_size_landmarks=self.FRONT_PROTUSION_FACE_SIZE_LANDMARKS,
            strength=self.FRONT_PROTUSION_PRESET_STRENGTH,
            influence_ratio=self.FRONT_PROTUSION_PRESET_INFLUENCE_RATIO,
            pull_ratio=self.FRONT_PROTUSION_PRESET_PULL_RATIO,
            labels=["L-243", "R-463", "M-56/190", "M-414/286"],
            ellipse_ratio=self.FRONT_PROTUSION_ELLIPSE_RATIO
        )
        # 성공 시에만 카운터 업데이트
        if self.current_image is not None and self.face_landmarks is not None:
            self.update_preset_counter("front_protusion")
    
    def apply_back_slit_100shot_preset(self):
        """뒷트임+ 프리셋 적용"""
        self.apply_jaw_preset(
            preset_name="뒷트임+",
            target_landmarks=self.BACK_SLIT_TARGET_LANDMARKS,
            face_size_landmarks=self.BACK_SLIT_FACE_SIZE_LANDMARKS,
            strength=self.BACK_SLIT_PRESET_STRENGTH,
            influence_ratio=self.BACK_SLIT_PRESET_INFLUENCE_RATIO,
            pull_ratio=self.BACK_SLIT_PRESET_PULL_RATIO,
            labels=["L-33", "R-359"]
        )
        # 성공 시에만 카운터 업데이트
        if self.current_image is not None and self.face_landmarks is not None:
            self.update_preset_counter("back_slit")
    
    def show_before_after_comparison(self):
        """Before/After 비교 창 표시"""
        if self.original_image is None or self.current_image is None:
            print("비교할 이미지가 없습니다. 먼저 이미지를 로드하고 변형을 적용해주세요.")
            return
        
        # Before/After 창 생성
        comparison_window = tk.Toplevel(self.root)
        comparison_window.title("📷 Before / After 비교")
        comparison_window.geometry("1200x800")
        comparison_window.configure(bg='#f0f0f0')
        
        # 제목
        title_label = ttk.Label(comparison_window, text="Before / After 비교", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 이미지 프레임
        images_frame = ttk.Frame(comparison_window)
        images_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Before 섹션
        before_frame = ttk.LabelFrame(images_frame, text="Before (원본)", padding=10)
        before_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        before_canvas = tk.Canvas(before_frame, bg='white')
        before_canvas.pack(fill=tk.BOTH, expand=True)
        
        # After 섹션
        after_frame = ttk.LabelFrame(images_frame, text="After (변형 후)", padding=10)
        after_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        after_canvas = tk.Canvas(after_frame, bg='white')
        after_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 이미지 표시 함수
        def display_comparison_images():
            try:
                # 캔버스 크기 가져오기
                comparison_window.update()
                canvas_width = before_canvas.winfo_width()
                canvas_height = before_canvas.winfo_height()
                
                if canvas_width <= 1 or canvas_height <= 1:
                    comparison_window.after(100, display_comparison_images)
                    return
                
                # Before 이미지 처리
                before_img = self.original_image.copy()
                before_height, before_width = before_img.shape[:2]
                
                # After 이미지 처리
                after_img = self.current_image.copy()
                after_height, after_width = after_img.shape[:2]
                
                # 스케일 계산 (여백 포함)
                margin = 20
                scale_before = min((canvas_width - margin) / before_width, 
                                 (canvas_height - margin) / before_height)
                scale_after = min((canvas_width - margin) / after_width, 
                                (canvas_height - margin) / after_height)
                
                # 동일한 스케일 사용 (더 작은 값)
                scale = min(scale_before, scale_after, 1.0)
                
                # Before 이미지 리사이즈 및 표시
                new_before_width = int(before_width * scale)
                new_before_height = int(before_height * scale)
                before_resized = cv2.resize(before_img, (new_before_width, new_before_height))
                before_pil = Image.fromarray(before_resized)
                before_photo = ImageTk.PhotoImage(before_pil)
                
                before_x = (canvas_width - new_before_width) // 2
                before_y = (canvas_height - new_before_height) // 2
                before_canvas.delete("all")
                before_canvas.create_image(before_x, before_y, anchor=tk.NW, image=before_photo)
                before_canvas.image = before_photo  # 참조 유지
                
                # After 이미지 리사이즈 및 표시
                new_after_width = int(after_width * scale)
                new_after_height = int(after_height * scale)
                after_resized = cv2.resize(after_img, (new_after_width, new_after_height))
                after_pil = Image.fromarray(after_resized)
                after_photo = ImageTk.PhotoImage(after_pil)
                
                after_x = (canvas_width - new_after_width) // 2
                after_y = (canvas_height - new_after_height) // 2
                after_canvas.delete("all")
                after_canvas.create_image(after_x, after_y, anchor=tk.NW, image=after_photo)
                after_canvas.image = after_photo  # 참조 유지
                
                print("Before/After 비교 이미지 표시 완료")
                
            except Exception as e:
                print(f"Before/After 이미지 표시 중 오류: {str(e)}")
        
        # 창이 완전히 로드된 후 이미지 표시
        comparison_window.after(200, display_comparison_images)
        
        # 닫기 버튼
        close_button = ttk.Button(comparison_window, text="닫기", 
                                 command=comparison_window.destroy)
        close_button.pack(pady=10)
        
        # 창을 맨 앞으로
        comparison_window.lift()
        comparison_window.focus_set()
    
    def measure_face_ratios(self):
        """얼굴 비율 측정"""
        if self.face_landmarks is None:
            return None
            
        measurements = {}
        
        try:
            # 1. 전체 얼굴 비율 (길이:너비)
            face_top = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["얼굴_윤곽"]["top"])
            face_bottom = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["얼굴_윤곽"]["bottom"])
            face_left = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["얼굴_윤곽"]["left"])
            face_right = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["얼굴_윤곽"]["right"])
            
            if all([face_top, face_bottom, face_left, face_right]):
                face_height = self.calculate_distance(face_top, face_bottom)
                face_width = self.calculate_distance(face_left, face_right)
                measurements["전체_얼굴_비율"] = face_height / face_width if face_width > 0 else 0
            
            # 2. 얼굴 삼등분 비율
            forehead_top = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["이마"]["top"])
            forehead_bottom = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["이마"]["bottom"])
            mid_face_top = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["중간_얼굴"]["top"])
            mid_face_bottom = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["중간_얼굴"]["bottom"])
            lower_face_top = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["아래_얼굴"]["top"])
            lower_face_bottom = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["아래_얼굴"]["bottom"])
            
            if all([forehead_top, forehead_bottom, mid_face_top, mid_face_bottom, lower_face_top, lower_face_bottom]):
                forehead_height = self.calculate_distance(forehead_top, forehead_bottom)
                mid_face_height = self.calculate_distance(mid_face_top, mid_face_bottom)
                lower_face_height = self.calculate_distance(lower_face_top, lower_face_bottom)
                
                total_height = forehead_height + mid_face_height + lower_face_height
                if total_height > 0:
                    measurements["이마_비율"] = forehead_height / total_height * 3  # 1/3 기준으로 정규화
                    measurements["중간_얼굴_비율"] = mid_face_height / total_height * 3
                    measurements["아래_얼굴_비율"] = lower_face_height / total_height * 3
            
            # 3. 눈 간격 비율
            left_eye_inner = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["왼쪽_눈"]["inner"])
            left_eye_outer = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["왼쪽_눈"]["outer"])
            right_eye_inner = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["오른쪽_눈"]["inner"])
            right_eye_outer = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["오른쪽_눈"]["outer"])
            
            if all([left_eye_inner, left_eye_outer, right_eye_inner, right_eye_outer]):
                left_eye_width = self.calculate_distance(left_eye_inner, left_eye_outer)
                right_eye_width = self.calculate_distance(right_eye_inner, right_eye_outer)
                eye_gap = self.calculate_distance(left_eye_inner, right_eye_inner)
                
                avg_eye_width = (left_eye_width + right_eye_width) / 2
                if avg_eye_width > 0:
                    measurements["눈_간격"] = eye_gap / avg_eye_width
            
            # 4. 입과 코 너비 비율
            nose_left = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["코"]["left"])
            nose_right = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["코"]["right"])
            mouth_left = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["입"]["left"])
            mouth_right = self.get_landmark_coordinates(self.FACE_MEASUREMENT_LANDMARKS["입"]["right"])
            
            if all([nose_left, nose_right, mouth_left, mouth_right]):
                nose_width = self.calculate_distance(nose_left, nose_right)
                mouth_width = self.calculate_distance(mouth_left, mouth_right)
                if nose_width > 0:
                    measurements["입_너비"] = mouth_width / nose_width
            
            return measurements
            
        except Exception as e:
            print(f"얼굴 비율 측정 중 오류: {str(e)}")
            return None
    
    def analyze_golden_ratio(self):
        """황금비율 분석 및 개선 제안"""
        if self.current_image is None:
            print("이미지가 로드되지 않았습니다.")
            return
            
        # 랜드마크 검출
        self.refresh_landmarks()
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
            
        # 현재 얼굴 비율 측정
        current_ratios = self.measure_face_ratios()
        if not current_ratios:
            print("얼굴 비율 측정에 실패했습니다.")
            return
            
        # 분석 창 생성
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("📊 얼굴 황금비율 분석")
        analysis_window.geometry("1000x700")
        analysis_window.configure(bg='#f8f9fa')
        
        # 제목
        title_label = ttk.Label(analysis_window, text="얼굴 황금비율 분석 결과", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=15)
        
        # 메인 프레임
        main_frame = ttk.Frame(analysis_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 좌측: 비율 비교 표
        left_frame = ttk.LabelFrame(main_frame, text="📏 비율 분석", padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 비율 비교 테이블 생성
        self.create_ratio_comparison_table(left_frame, current_ratios)
        
        # 우측: 개선 제안
        right_frame = ttk.LabelFrame(main_frame, text="💡 개선 제안", padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 개선 제안 생성
        self.create_improvement_suggestions(right_frame, current_ratios)
        
        # 하단: 시각화 버튼
        button_frame = ttk.Frame(analysis_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="📈 비율 시각화", 
                  command=lambda: self.show_ratio_visualization(current_ratios)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="🎯 측정점 표시", 
                  command=self.show_measurement_points).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📏 비율 라인 표시", 
                  command=lambda: self.show_ratio_lines(current_ratios)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="🎯 뷰티 스코어", 
                  command=lambda: self.show_beauty_score_visualization(current_ratios)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="🔍 점수 계산 상세", 
                  command=lambda: self.show_score_calculation_details(current_ratios)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="닫기", 
                  command=analysis_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 창을 맨 앞으로
        analysis_window.lift()
        analysis_window.focus_set()
    
    def create_ratio_comparison_table(self, parent, current_ratios):
        """비율 비교 테이블 생성"""
        # 스크롤 가능한 테이블 프레임
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 테이블 헤더
        headers = ["측정 항목", "현재 비율", "황금 비율", "차이", "평가"]
        for i, header in enumerate(headers):
            label = ttk.Label(table_frame, text=header, font=("Arial", 10, "bold"), 
                             background="#e9ecef", relief="solid", width=12)
            label.grid(row=0, column=i, sticky="ew", padx=1, pady=1)
        
        # 비율별 데이터
        ratio_mapping = {
            "전체_얼굴_비율": ("얼굴 길이:너비", "전체_얼굴_비율"),
            "이마_비율": ("이마 비율", "얼굴_삼등분"),
            "중간_얼굴_비율": ("중간얼굴 비율", "얼굴_삼등분"),
            "아래_얼굴_비율": ("아래얼굴 비율", "얼굴_삼등분"),
            "눈_간격": ("눈 간격", "눈_간격"),
            "입_너비": ("입:코 너비", "입_너비")
        }
        
        row = 1
        for current_key, (display_name, golden_key) in ratio_mapping.items():
            if current_key in current_ratios:
                current_value = current_ratios[current_key]
                golden_value = self.FACE_GOLDEN_RATIOS[golden_key]
                difference = abs(current_value - golden_value)
                difference_percent = (difference / golden_value) * 100
                
                # 평가 등급
                if difference_percent <= 5:
                    grade = "A (우수)"
                    grade_color = "#28a745"
                elif difference_percent <= 15:
                    grade = "B (양호)"
                    grade_color = "#ffc107"
                elif difference_percent <= 25:
                    grade = "C (보통)"
                    grade_color = "#fd7e14"
                else:
                    grade = "D (개선필요)"
                    grade_color = "#dc3545"
                
                # 테이블 행 생성
                ttk.Label(table_frame, text=display_name).grid(row=row, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(table_frame, text=f"{current_value:.3f}").grid(row=row, column=1, sticky="w", padx=5, pady=2)
                ttk.Label(table_frame, text=f"{golden_value:.3f}").grid(row=row, column=2, sticky="w", padx=5, pady=2)
                ttk.Label(table_frame, text=f"{difference:.3f}").grid(row=row, column=3, sticky="w", padx=5, pady=2)
                grade_label = ttk.Label(table_frame, text=grade, foreground=grade_color)
                grade_label.grid(row=row, column=4, sticky="w", padx=5, pady=2)
                
                row += 1
    
    def create_improvement_suggestions(self, parent, current_ratios):
        """개선 제안 생성"""
        suggestions_frame = ttk.Frame(parent)
        suggestions_frame.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤 가능한 텍스트 위젯
        text_widget = tk.Text(suggestions_frame, wrap=tk.WORD, width=40, height=20,
                             font=("Arial", 10), bg="#ffffff", relief="solid")
        scrollbar = ttk.Scrollbar(suggestions_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 개선 제안 텍스트 생성
        suggestions = self.generate_improvement_suggestions(current_ratios)
        text_widget.insert(tk.END, suggestions)
        text_widget.config(state=tk.DISABLED)  # 읽기 전용
    
    def generate_improvement_suggestions(self, current_ratios):
        """개선 제안 텍스트 생성"""
        suggestions = "🎯 맞춤형 개선 제안\n\n"
        
        # 전체 얼굴 비율 분석
        if "전체_얼굴_비율" in current_ratios:
            current = current_ratios["전체_얼굴_비율"]
            golden = self.FACE_GOLDEN_RATIOS["전체_얼굴_비율"]
            
            if current < golden * 0.9:
                suggestions += "📏 얼굴 길이 개선:\n"
                suggestions += "• 아래턱 100샷+ 프리셋으로 턱선을 V라인으로 만들어 얼굴을 길어보이게\n"
                suggestions += "• 중간턱 100샷+ 프리셋으로 중간 얼굴을 슬림하게\n\n"
            elif current > golden * 1.1:
                suggestions += "📏 얼굴 너비 개선:\n"
                suggestions += "• 볼 100샷+ 프리셋으로 볼살을 줄여 얼굴을 좁아보이게\n"
                suggestions += "• 광대 축소술 고려\n\n"
        
        # 눈 관련 개선
        if "눈_간격" in current_ratios:
            current = current_ratios["눈_간격"]
            golden = self.FACE_GOLDEN_RATIOS["눈_간격"]
            
            if current < golden * 0.8:
                suggestions += "👁️ 눈 간격 개선:\n"
                suggestions += "• 뒷트임+ 프리셋으로 눈을 바깥쪽으로 확장\n"
                suggestions += "• 외안각 성형술 고려\n\n"
            elif current > golden * 1.2:
                suggestions += "👁️ 눈 크기 개선:\n"
                suggestions += "• 앞튀임+ 프리셋으로 앞트임 효과\n"
                suggestions += "• 쌍꺼풀 수술로 눈을 더 크게\n\n"
        
        # 입과 코 비율
        if "입_너비" in current_ratios:
            current = current_ratios["입_너비"]
            golden = self.FACE_GOLDEN_RATIOS["입_너비"]
            
            if current < golden * 0.8:
                suggestions += "👄 입 크기 개선:\n"
                suggestions += "• 입꼬리 상승술로 입을 더 크게\n"
                suggestions += "• 구각 성형술 고려\n\n"
            elif current > golden * 1.2:
                suggestions += "👃 코 크기 개선:\n"
                suggestions += "• 코 날개 축소술 고려\n"
                suggestions += "• 코끝 성형으로 코를 더 작게\n\n"
        
        # 얼굴 삼등분 비율
        thirds_analysis = []
        if "이마_비율" in current_ratios:
            forehead_ratio = current_ratios["이마_비율"]
            if forehead_ratio > 1.2:
                thirds_analysis.append("• 이마가 상대적으로 큼 - 앞머리나 헤어라인 교정 고려")
            elif forehead_ratio < 0.8:
                thirds_analysis.append("• 이마가 상대적으로 작음 - 이마 확대술 고려")
        
        if "중간_얼굴_비율" in current_ratios:
            mid_ratio = current_ratios["중간_얼굴_비율"]
            if mid_ratio > 1.2:
                thirds_analysis.append("• 중간 얼굴이 김 - 코 길이 단축술 고려")
        
        if "아래_얼굴_비율" in current_ratios:
            lower_ratio = current_ratios["아래_얼굴_비율"]
            if lower_ratio > 1.2:
                thirds_analysis.append("• 아래 얼굴이 김 - 턱 단축술이나 아래턱 100샷+ 집중 적용")
            elif lower_ratio < 0.8:
                thirds_analysis.append("• 아래 얼굴이 짧음 - 턱 연장술 고려")
        
        if thirds_analysis:
            suggestions += "⚖️ 얼굴 비율 균형:\n"
            suggestions += "\n".join(thirds_analysis) + "\n\n"
        
        suggestions += "📝 추가 권장사항:\n"
        suggestions += "• 정확한 진단을 위해 전문 성형외과 상담 권장\n"
        suggestions += "• 여러 프리셋을 조합하여 시뮬레이션 후 결정\n"
        suggestions += "• Before/After 기능으로 변화 확인\n"
        
        return suggestions
    
    def show_ratio_visualization(self, current_ratios):
        """비율 시각화 창 표시"""
        viz_window = tk.Toplevel(self.root)
        viz_window.title("📈 얼굴 비율 시각화")
        viz_window.geometry("600x400")
        
        # 간단한 막대 그래프 형태로 시각화
        canvas = tk.Canvas(viz_window, bg='white')
        canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 비율 데이터 시각화
        y_pos = 50
        for key, current_value in current_ratios.items():
            if key in ["전체_얼굴_비율", "눈_간격", "입_너비"]:
                # 황금비율과 현재 비율 비교
                golden_key = key if key in self.FACE_GOLDEN_RATIOS else "전체_얼굴_비율"
                golden_value = self.FACE_GOLDEN_RATIOS.get(golden_key, 1.0)
                
                # 막대 그래프
                bar_width = 200
                current_bar_length = min(bar_width, (current_value / golden_value) * bar_width)
                golden_bar_length = bar_width
                
                # 라벨
                canvas.create_text(50, y_pos, text=key, anchor="w", font=("Arial", 10))
                
                # 황금비율 막대 (배경)
                canvas.create_rectangle(150, y_pos-8, 150+golden_bar_length, y_pos+8, 
                                      fill="#ffd700", outline="#daa520")
                
                # 현재 비율 막대
                bar_color = "#28a745" if abs(current_value - golden_value) / golden_value <= 0.1 else "#dc3545"
                canvas.create_rectangle(150, y_pos-5, 150+current_bar_length, y_pos+5, 
                                      fill=bar_color, outline="#000000")
                
                # 수치 표시
                canvas.create_text(370, y_pos, text=f"{current_value:.3f} / {golden_value:.3f}", 
                                 anchor="w", font=("Arial", 9))
                
                y_pos += 40
        
        # 범례
        canvas.create_rectangle(50, y_pos+20, 70, y_pos+30, fill="#ffd700", outline="#daa520")
        canvas.create_text(80, y_pos+25, text="황금비율", anchor="w", font=("Arial", 9))
        
        canvas.create_rectangle(50, y_pos+40, 70, y_pos+50, fill="#28a745", outline="#000000")
        canvas.create_text(80, y_pos+45, text="현재 비율 (양호)", anchor="w", font=("Arial", 9))
        
        canvas.create_rectangle(50, y_pos+60, 70, y_pos+70, fill="#dc3545", outline="#000000")
        canvas.create_text(80, y_pos+65, text="현재 비율 (개선필요)", anchor="w", font=("Arial", 9))
    
    def show_measurement_points(self):
        """측정점 시각화"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
            
        # 기존 시각화 제거
        self.canvas.delete("measurement_points")
        
        # 측정점들을 캔버스에 표시
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
        color_idx = 0
        
        for category, landmarks in self.FACE_MEASUREMENT_LANDMARKS.items():
            for point_name, landmark_id in landmarks.items():
                landmark_coord = self.get_landmark_coordinates(landmark_id)
                if landmark_coord:
                    screen_coord = self.image_to_screen_coords(landmark_coord[0], landmark_coord[1])
                    if screen_coord:
                        x, y = screen_coord
                        color = colors[color_idx % len(colors)]
                        
                        # 점 표시
                        self.canvas.create_oval(x-3, y-3, x+3, y+3, 
                                              fill=color, outline="white", width=1,
                                              tags="measurement_points")
                        
                        # 라벨 표시
                        self.canvas.create_text(x+8, y-8, text=f"{category}_{point_name}", 
                                              fill=color, font=("Arial", 7, "bold"),
                                              tags="measurement_points")
            color_idx += 1
        
        # 5초 후 자동 제거
        self.root.after(5000, lambda: self.canvas.delete("measurement_points"))
        print("측정점이 5초간 표시됩니다.")
    
    def draw_circular_ratio_indicator(self, x, y, radius, percentage, label, color="#ff0000"):
        """원형 비율 지시기 그리기 (뷰티 스코어 스타일)"""
        # 원형 테두리
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            outline=color, width=3, tags="ratio_indicators"
        )
        
        # 퍼센티지 텍스트
        self.canvas.create_text(
            x, y - 10, text=f"{percentage:.1f}%",
            fill=color, font=("Arial", 12, "bold"), tags="ratio_indicators"
        )
        
        # 라벨 텍스트
        self.canvas.create_text(
            x, y + 10, text=label,
            fill=color, font=("Arial", 8), tags="ratio_indicators"
        )

    def draw_bidirectional_arrow(self, x1, y1, x2, y2, color="blue", width=2, arrow_size=8, dash=None):
        """양방향 화살표 그리기"""
        import math
        
        # 메인 라인 그리기 (점선 옵션 포함)
        if dash:
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, dash=dash, tags="ratio_lines")
        else:
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, tags="ratio_lines")
        
        # 화살표 방향 계산
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_length = arrow_size
        arrow_angle = math.pi / 6  # 30도
        
        # 시작점 화살표 (역방향)
        start_arrow_x1 = x1 + arrow_length * math.cos(angle + math.pi + arrow_angle)
        start_arrow_y1 = y1 + arrow_length * math.sin(angle + math.pi + arrow_angle)
        start_arrow_x2 = x1 + arrow_length * math.cos(angle + math.pi - arrow_angle)
        start_arrow_y2 = y1 + arrow_length * math.sin(angle + math.pi - arrow_angle)
        
        self.canvas.create_line(x1, y1, start_arrow_x1, start_arrow_y1, fill=color, width=width, tags="ratio_lines")
        self.canvas.create_line(x1, y1, start_arrow_x2, start_arrow_y2, fill=color, width=width, tags="ratio_lines")
        
        # 끝점 화살표 (정방향)
        end_arrow_x1 = x2 + arrow_length * math.cos(angle + arrow_angle)
        end_arrow_y1 = y2 + arrow_length * math.sin(angle + arrow_angle)
        end_arrow_x2 = x2 + arrow_length * math.cos(angle - arrow_angle)
        end_arrow_y2 = y2 + arrow_length * math.sin(angle - arrow_angle)
        
        self.canvas.create_line(x2, y2, end_arrow_x1, end_arrow_y1, fill=color, width=width, tags="ratio_lines")
        self.canvas.create_line(x2, y2, end_arrow_x2, end_arrow_y2, fill=color, width=width, tags="ratio_lines")

    def show_beauty_score_visualization(self, current_ratios):
        """뷰티 스코어 시각화 (원형 영역 + 퍼센티지)"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
            
        # 기존 표시 제거
        self.canvas.delete("ratio_indicators")
        self.canvas.delete("proportion_lines")
        
        print("뷰티 스코어 시각화를 표시합니다...")
        
        try:
            # 1. 1/5 세로 비례선 (5등분)
            self.draw_fifth_proportion_lines()
            
            # 2. 1/3 가로 비례선 (3등분) 
            self.draw_third_proportion_lines()
            
            # 3. 각 부위별 원형 점수 표시
            self.draw_beauty_score_indicators(current_ratios)
            
            # 4. 교차점 기반 원 그리기
            self.draw_intersection_circle()
            
            # 5. 두 번째 교차점 원 그리기  
            self.draw_second_intersection_circle()
            
            # 6. 랜드마크 37을 지나는 수평선
            self.draw_landmark_37_line()
            
            # 7. 왼쪽 테두리와 1/3선, 37선 교차점을 지름으로 하는 원
            self.draw_left_intersection_circle_1()
            
            # 8. 왼쪽 테두리와 하단 테두리, 37선 교차점을 지름으로 하는 원  
            self.draw_left_intersection_circle_2()
            
            # 9-13. 상단 테두리 5개 원들
            self.draw_top_border_circles()
            
            # 눈간격 및 입코비율 시각화 제거 (뷰티 스코어에서 삭제)
            
            # 14. 턱 곡률 시각화
            self.draw_jaw_curvature()
            
            # 15초 후 자동 제거
            self.root.after(15000, lambda: [
                self.canvas.delete("ratio_indicators"),
                self.canvas.delete("proportion_lines"),
                self.canvas.delete("intersection_circle"),
                self.canvas.delete("second_circle"),
                self.canvas.delete("landmark_37_line"),
                self.canvas.delete("left_circle_1"),
                self.canvas.delete("left_circle_2"),
                self.canvas.delete("top_circles"),
                self.canvas.delete("jaw_curvature"),  # 턱 곡률 삭제
                self.canvas.delete("ratio_lines")  # 비율 라인도 삭제
            ])
            print("뷰티 스코어 시각화가 15초간 표시됩니다.")
            
        except Exception as e:
            print(f"뷰티 스코어 시각화 중 오류: {str(e)}")

    def show_ratio_lines(self, current_ratios):
        """얼굴 비율 라인과 수치를 시각적으로 표시"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
            
        # 기존 라인 제거
        self.canvas.delete("ratio_lines")
        
        print("얼굴 비율 라인을 표시합니다...")
        
        try:
            # 1. 전체 얼굴 비율 라인 (길이:너비)
            self.draw_face_outline_ratio(current_ratios)
            
            # 2. 얼굴 삼등분 라인
            self.draw_face_thirds_ratio(current_ratios)
            
            # 3. 눈 간격 비율 라인과 수치 표시
            self.draw_eye_spacing_ratio(current_ratios)
            self.draw_eye_spacing_percentage(current_ratios)
            
            # 4. 입/코 너비 비율 라인과 수치 표시
            self.draw_mouth_nose_ratio(current_ratios)
            self.draw_mouth_nose_percentage(current_ratios)
            
            # 5. 황금비율 가이드라인
            self.draw_golden_ratio_guide()
            
            # 10초 후 자동 제거
            self.root.after(10000, lambda: self.canvas.delete("ratio_lines"))
            print("비율 라인이 10초간 표시됩니다.")
            
        except Exception as e:
            print(f"비율 라인 표시 중 오류: {str(e)}")
    
    def draw_fifth_proportion_lines(self):
        """1/5 세로 비례선 그리기 (각 선이 특정 랜드마크를 지나도록)"""
        face_top = self.get_landmark_coordinates(10)
        face_bottom = self.get_landmark_coordinates(152)
        face_left = self.get_landmark_coordinates(234)
        face_right = self.get_landmark_coordinates(454)
        
        # 각 비례선이 지나는 랜드마크들
        landmark_33 = self.get_landmark_coordinates(33)   # 1/5: 왼쪽 눈 바깥쪽
        landmark_133 = self.get_landmark_coordinates(133) # 2/5: 왼쪽 눈 안쪽
        landmark_362 = self.get_landmark_coordinates(362) # 3/5: 오른쪽 눈 안쪽  
        landmark_359 = self.get_landmark_coordinates(359) # 4/5: 오른쪽 눈 바깥쪽
        landmark_447 = self.get_landmark_coordinates(447) # 5/5: 가장 오른쪽
        
        landmarks = [None, landmark_33, landmark_133, landmark_362, landmark_359, landmark_447]
        labels = ["0/5", "1/5 (눈외)", "2/5 (눈내)", "3/5 (눈내)", "4/5 (눈외)", "5/5 (447)"]
        
        if all([face_top, face_bottom, face_left, face_right]) and all(landmarks[1:]):
            face_width = self.calculate_distance(face_left, face_right)
            top_y = face_top[1]
            bottom_y = face_bottom[1]
            
            # 세로선 그리기 (6개: 0/5, 1/5, 2/5, 3/5, 4/5, 5/5)
            # 1/3선과 3/3선 y 좌표 구하기 (5/5선 분리용)
            landmark_8 = self.get_landmark_coordinates(8)   # 1/3선
            face_bottom = self.get_landmark_coordinates(152) # 3/3선
            
            for i in range(6):
                if i in [1, 2, 3, 4, 5]:  # 랜드마크 기준선들
                    x = landmarks[i][0]
                else:  # 외곽선들 (0/5만)
                    ratio = i / 5.0
                    x = face_left[0] + (face_width * ratio)
                
                # 모든 세로선에서 1/3~3/3 구간을 제외하고 두 개의 선분으로 나누어 그리기
                if landmark_8 and face_bottom:
                    # 첫 번째 선분: 상단~1/3선
                    start_screen_1 = self.image_to_screen_coords(x, top_y)
                    end_screen_1 = self.image_to_screen_coords(x, landmark_8[1])
                    
                    if start_screen_1 and end_screen_1:
                        # 색상 및 굵기 설정
                        color = "white"
                        if i in [1, 2, 3, 4, 5]:  # 랜드마크 기준선들
                            width = 1.5
                        else:  # 외곽선 (0/5만)
                            width = 0.5
                            
                        self.canvas.create_line(
                            start_screen_1[0], start_screen_1[1],
                            end_screen_1[0], end_screen_1[1],
                            fill=color, width=width, dash=(3, 2), tags="proportion_lines"
                        )
                    
                    # 두 번째 선분: 3/3선~하단
                    start_screen_2 = self.image_to_screen_coords(x, face_bottom[1])
                    end_screen_2 = self.image_to_screen_coords(x, bottom_y)
                    
                    if start_screen_2 and end_screen_2:
                        # 색상 및 굵기 설정
                        color = "white"
                        if i in [1, 2, 3, 4, 5]:  # 랜드마크 기준선들
                            width = 1.5
                        else:  # 외곽선 (0/5만)
                            width = 0.5
                            
                        self.canvas.create_line(
                            start_screen_2[0], start_screen_2[1],
                            end_screen_2[0], end_screen_2[1],
                            fill=color, width=width, dash=(3, 2), tags="proportion_lines"
                        )
                else:
                    # 다른 세로선들은 기존대로 전체 길이로 그리기
                    start_screen = self.image_to_screen_coords(x, top_y)
                    end_screen = self.image_to_screen_coords(x, bottom_y)
                    
                    if start_screen and end_screen:
                        # 색상 및 굵기 설정 (모두 흰색, 굵기 절반)
                        color = "white"
                        if i in [1, 2, 3, 4, 5]:  # 랜드마크 기준선들
                            width = 1.5  # 기존 3에서 절반으로 감소
                        else:  # 외곽선 (0/5만)
                            width = 0.5  # 기존 1에서 절반으로 감소
                        
                        self.canvas.create_line(
                            start_screen[0], start_screen[1],
                            end_screen[0], end_screen[1],
                            fill=color, width=width, dash=(3, 2), tags="proportion_lines"
                        )
                    
                    # 비례 라벨 제거 (뷰티 스코어에서 텍스트 숨김)
    
    def draw_third_proportion_lines(self):
        """1/3 가로 비례선 그리기 (각 선이 특정 랜드마크를 지나도록)"""
        face_top = self.get_landmark_coordinates(10)
        face_bottom = self.get_landmark_coordinates(152)
        face_left = self.get_landmark_coordinates(234)
        face_right = self.get_landmark_coordinates(454)
        
        # 각 비례선이 지나는 랜드마크들
        landmark_8 = self.get_landmark_coordinates(8) # 1/3: 이마-눈썹 경계
        landmark_2 = self.get_landmark_coordinates(2)     # 2/3: 코 끝
        
        landmarks = [None, landmark_8, landmark_2, None]
        labels = ["0/3", "1/3 (이마)", "2/3 (코)", "3/3"]
        
        if all([face_top, face_bottom, face_left, face_right]) and all([landmark_8, landmark_2]):
            face_height = self.calculate_distance(face_top, face_bottom)
            left_x = face_left[0]
            right_x = face_right[0]
            
            # 가로선 그리기 (3개: 1/3, 2/3, 3/3) - 최상단 0/3 테두리선 제외
            for i in range(1, 4):  # 0은 제외하고 1, 2, 3만
                if i == 1:  # 1/3 선은 랜드마크 8을 지나는 수평선
                    y = landmark_8[1]
                elif i == 2:  # 2/3 선은 랜드마크 2를 지나는 수평선
                    y = landmark_2[1]
                else:  # 외곽선들 (3/3만)
                    ratio = i / 3.0
                    y = face_top[1] + (face_height * ratio)
                
                start_screen = self.image_to_screen_coords(left_x, y)
                end_screen = self.image_to_screen_coords(right_x, y)
                
                if start_screen and end_screen:
                    # 색상 및 굵기 설정 (모두 흰색, 굵기 절반)
                    color = "white"
                    if i in [1, 2]:  # 랜드마크 기준선들
                        width = 1.5  # 기존 3에서 절반으로 감소
                    else:  # 외곽선
                        width = 0.5  # 기존 1에서 절반으로 감소
                    
                    self.canvas.create_line(
                        start_screen[0], start_screen[1],
                        end_screen[0], end_screen[1],
                        fill=color, width=width, dash=(4, 3), tags="proportion_lines"
                    )
                    
                    # 비례 라벨 제거 (뷰티 스코어에서 텍스트 숨김)
    
    def draw_beauty_score_indicators(self, current_ratios):
        """각 부위별 뷰티 스코어 원형 지시기 표시"""
        # 각 부위별 점수 계산 (황금비율 대비 퍼센티지)
        scores = self.calculate_beauty_scores(current_ratios)
        
        # 주요 얼굴 특징점들의 위치에 원형 지시기 표시 (이마, 눈간격, 눈크기, 입 원 제거)
        indicators = [
            # (랜드마크, 점수키, 라벨, 색상, 오프셋)
            (2, "코길이", "코", "#96CEB4", (30, 0)),          # 코 끝
            (172, "턱라인", "턱", "#DDA0DD", (0, 30))         # 턱 끝
        ]
        
        for landmark_id, score_key, label, color, offset in indicators:
            landmark = self.get_landmark_coordinates(landmark_id)
            if landmark and score_key in scores:
                screen_pos = self.image_to_screen_coords(landmark[0], landmark[1])
                if screen_pos:
                    x = screen_pos[0] + offset[0]
                    y = screen_pos[1] + offset[1]
                    
                    self.draw_circular_ratio_indicator(
                        x, y, 25, scores[score_key], label, color
                    )
    
    def calculate_beauty_scores(self, current_ratios):
        """황금비율 대비 뷰티 스코어 계산 (100% 만점)"""
        scores = {}
        
        # 전체 얼굴 비율 점수
        if "전체_얼굴_비율" in current_ratios:
            ideal = self.FACE_GOLDEN_RATIOS["전체_얼굴_비율"]
            current = current_ratios["전체_얼굴_비율"]
            score = max(0, 100 - abs(current - ideal) / ideal * 100)
            scores["이마"] = score
        
        # 눈 간격 점수
        if "눈_간격" in current_ratios:
            ideal = 1.0
            current = current_ratios["눈_간격"]
            score = max(0, 100 - abs(current - ideal) / ideal * 100)
            scores["눈간격"] = score
            scores["눈크기"] = score * 0.9  # 눈크기는 약간 다른 점수
        
        # 입 너비 점수
        if "입_너비" in current_ratios:
            ideal = self.FACE_GOLDEN_RATIOS["입_너비"]
            current = current_ratios["입_너비"]
            score = max(0, 100 - abs(current - ideal) / ideal * 100)
            scores["입크기"] = score
        
        # 얼굴 삼등분 점수
        if "얼굴_삼등분" in current_ratios:
            ideal = 1.0
            current = current_ratios["얼굴_삼등분"]
            score = max(0, 100 - abs(current - ideal) / ideal * 100)
            scores["코길이"] = score
            scores["턱라인"] = score * 0.8
        
        return scores
    
    def draw_circle_from_intersections(self, point1_coords, point2_coords, color, label, tag, label_offset=(10, -20)):
        """두 교차점을 지름으로 하는 원을 그리는 통일된 함수"""
        if not point1_coords or not point2_coords:
            return
            
        # 화면 좌표로 변환
        point1_screen = self.image_to_screen_coords(point1_coords[0], point1_coords[1])
        point2_screen = self.image_to_screen_coords(point2_coords[0], point2_coords[1])
        
        if point1_screen and point2_screen:
            # 원의 중심점과 반지름 계산
            center_x = (point1_screen[0] + point2_screen[0]) / 2
            center_y = (point1_screen[1] + point2_screen[1]) / 2
            
            import math
            distance = math.sqrt(
                (point2_screen[0] - point1_screen[0])**2 + 
                (point2_screen[1] - point1_screen[1])**2
            )
            radius = distance / 2
            
            # 네온사인 효과를 위한 색상 설정
            neon_red = "#FF0040"  # 밝은 네온 빨간색
            
            # 원 그리기 (red는 실선 + 네온 효과, 나머지는 점선)
            if color == "red":
                # 빨간색 원은 얇은 실선으로 그리기 (30% 더 얇게)
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    outline=neon_red, width=1.0, tags=tag  # 1.5 -> 1.0으로 30% 감소
                )
            else:
                # 다른 색상은 점선으로 그리기 (파란색은 굵기 50% 감소)
                dash_patterns = {
                    "#FF1493": (5, 5),  # 딥핑크
                    "#00CED1": (7, 3),  # 다크터쿼이즈
                    "#32CD32": (4, 4),  # 라임그린
                    "#FF8C00": (6, 2),  # 다크오렌지
                    "#9370DB": (8, 2),  # 미디엄퍼플
                    "#8A2BE2": (3, 5),  # 블루바이올렛
                    "#FF69B4": (4, 3),  # 핫핑크
                    "#FFA500": (5, 4),  # 오렌지
                    "blue": (4, 4),     # 파란색
                }
                dash = dash_patterns.get(color, (5, 5))
                
                # 파란색 원은 굵기를 30% 더 얇게 (1.5 -> 1.0)
                width = 1.0 if color == "blue" else 3
                
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    outline=color, width=width, dash=dash, tags=tag
                )
            
            # 교차점 마커 (빨간색은 네온 효과 적용)
            point_radius = 4
            marker_color = neon_red if color == "red" else color
            for point_screen in [point1_screen, point2_screen]:
                self.canvas.create_oval(
                    point_screen[0] - point_radius, point_screen[1] - point_radius,
                    point_screen[0] + point_radius, point_screen[1] + point_radius,
                    fill=marker_color, outline=marker_color, width=2, tags=tag
                )
            
            # 지름선 (빨간색과 파란색 원은 지름선 제거, 다른 색상만 점선으로 그리기)
            if color != "red" and color != "blue":
                # 빨간색과 파란색이 아닌 색상만 점선으로 그리기
                line_dash = {
                    "#FF1493": (3, 3),
                    "#00CED1": (4, 2), 
                    "#32CD32": (3, 3),
                    "#FF8C00": (2, 4),
                    "#9370DB": (3, 2),
                    "#8A2BE2": (2, 3),  # 블루바이올렛
                    "#FF69B4": (3, 4),  # 핫핑크
                    "#FFA500": (4, 3),  # 오렌지
                }
                self.canvas.create_line(
                    point1_screen[0], point1_screen[1],
                    point2_screen[0], point2_screen[1],
                    fill=color, width=2, dash=line_dash.get(color, (3, 3)), tags=tag
                )
            
            # 뷰티 스코어에서는 정보 라벨 표시하지 않음 (네모박스와 텍스트 제거)
    
    def draw_intersection_circle(self):
        """첫 번째 교차점 원: 1/3 이마선과 2/3 코선이 5/5선과 만나는 점들"""
        landmark_8 = self.get_landmark_coordinates(8)  # 1/3 이마선
        landmark_2 = self.get_landmark_coordinates(2)      # 2/3 코선  
        landmark_447 = self.get_landmark_coordinates(447)  # 5/5선
        
        if all([landmark_8, landmark_2, landmark_447]):
            right_vertical_x = landmark_447[0]
            
            # 교차점 계산
            point1 = (right_vertical_x, landmark_8[1])  # 1/3선 × 5/5선
            point2 = (right_vertical_x, landmark_2[1])    # 2/3선 × 5/5선
            
            self.draw_circle_from_intersections(
                point1, point2, 
                color="red", 
                label="🔴 우상 교차원", 
                tag="intersection_circle",
                label_offset=(10, -20)
            )
            
            # 수직 거리 대비 지름 비율 계산 및 표시
            self.draw_circle_diameter_ratio(point1, point2, "upper_right")
    
    def draw_second_intersection_circle(self):
        """두 번째 교차점 원: 2/3 코선과 3/3 턱선이 5/5선과 만나는 점들"""
        landmark_2 = self.get_landmark_coordinates(2)      # 2/3 코선
        face_bottom = self.get_landmark_coordinates(152)   # 3/3 턱선
        landmark_447 = self.get_landmark_coordinates(447)  # 5/5선
        
        if all([landmark_2, face_bottom, landmark_447]):
            right_vertical_x = landmark_447[0]
            
            # 교차점 계산  
            point1 = (right_vertical_x, landmark_2[1])    # 2/3선 × 5/5선
            point2 = (right_vertical_x, face_bottom[1])   # 3/3선 × 5/5선
            
            self.draw_circle_from_intersections(
                point1, point2,
                color="red",
                label="🔴 우하 교차원",
                tag="second_circle", 
                label_offset=(10, 30)
            )
            
            # 수직 거리 대비 지름 비율 계산 및 표시
            self.draw_circle_diameter_ratio(point1, point2, "lower_right")
    
    def draw_landmark_37_line(self):
        """랜드마크 37을 지나는 수평선 그리기"""
        face_left = self.get_landmark_coordinates(234)
        face_right = self.get_landmark_coordinates(454)
        landmark_37 = self.get_landmark_coordinates(37)  # 하안검 라인
        
        if all([face_left, face_right, landmark_37]):
            left_x = face_left[0]
            right_x = face_right[0]
            line_y = landmark_37[1]  # 랜드마크 37의 y 좌표
            
            # 화면 좌표로 변환
            start_screen = self.image_to_screen_coords(left_x, line_y)
            end_screen = self.image_to_screen_coords(right_x, line_y)
            
            if start_screen and end_screen:
                # 수평선만 그리기 (랜드마크 점과 텍스트 제거)
                self.canvas.create_line(
                    start_screen[0], start_screen[1],
                    end_screen[0], end_screen[1],
                    fill="#9370DB", width=2, dash=(6, 4), tags="landmark_37_line"
                )
    
    def draw_left_intersection_circle_1(self):
        """좌상 교차원: 왼쪽 테두리와 2/3 코선(37선 바로 위), 37선 교차점을 지름으로 하는 원"""
        face_left = self.get_landmark_coordinates(234)     # 왼쪽 테두리
        landmark_2 = self.get_landmark_coordinates(2)      # 2/3 코선 (37선 바로 위)
        landmark_37 = self.get_landmark_coordinates(37)    # 37선
        
        if all([face_left, landmark_2, landmark_37]):
            left_vertical_x = face_left[0]
            
            # 교차점 계산
            point1 = (left_vertical_x, landmark_2[1])   # 왼쪽테두리 × 2/3코선
            point2 = (left_vertical_x, landmark_37[1])  # 왼쪽테두리 × 37선
            
            self.draw_circle_from_intersections(
                point1, point2,
                color="blue",
                label="🔵 좌상 교차원", 
                tag="left_circle_1",
                label_offset=(-160, -20)
            )
            
            # 좌상 원의 지름 비율 계산 및 표시
            self.draw_left_circle_diameter_ratio(point1, point2, "upper_left")
    
    def draw_left_intersection_circle_2(self):
        """좌하 교차원: 왼쪽 테두리와 하단 테두리, 37선 교차점을 지름으로 하는 원"""
        face_left = self.get_landmark_coordinates(234)     # 왼쪽 테두리
        face_bottom = self.get_landmark_coordinates(152)   # 하단 테두리  
        landmark_37 = self.get_landmark_coordinates(37)    # 37선
        
        if all([face_left, face_bottom, landmark_37]):
            left_vertical_x = face_left[0]
            
            # 교차점 계산
            point1 = (left_vertical_x, face_bottom[1])  # 왼쪽테두리 × 하단테두리
            point2 = (left_vertical_x, landmark_37[1])  # 왼쪽테두리 × 37선
            
            self.draw_circle_from_intersections(
                point1, point2,
                color="blue", 
                label="🔵 좌하 교차원",
                tag="left_circle_2",
                label_offset=(-160, 30)
            )
            
            # 좌하 원의 지름 비율 계산 및 표시
            self.draw_left_circle_diameter_ratio(point1, point2, "lower_left")
    
    def draw_top_border_circles(self):
        """상단 테두리에 5개의 원 그리기 (각 수직선 구간별)"""
        # 필요한 랜드마크들
        face_top = self.get_landmark_coordinates(10)       # 상단 테두리
        face_left = self.get_landmark_coordinates(234)     # 0/5 왼쪽 테두리
        landmark_33 = self.get_landmark_coordinates(33)    # 1/5
        landmark_133 = self.get_landmark_coordinates(133)  # 2/5
        landmark_362 = self.get_landmark_coordinates(362)  # 3/5
        landmark_359 = self.get_landmark_coordinates(359)  # 4/5
        landmark_447 = self.get_landmark_coordinates(447)  # 5/5
        
        # 모든 랜드마크가 있는지 확인
        if all([face_top, face_left, landmark_33, landmark_133, landmark_362, landmark_359, landmark_447]):
            top_y = face_top[1]  # 상단 테두리의 y 좌표
            
            # 5개의 수직선 x 좌표들
            vertical_lines = [
                face_left[0],        # 0/5
                landmark_33[0],      # 1/5
                landmark_133[0],     # 2/5
                landmark_362[0],     # 3/5
                landmark_359[0],     # 4/5
                landmark_447[0]      # 5/5
            ]
            
            # 전체 얼굴 가로 길이 계산
            total_face_width = landmark_447[0] - face_left[0]
            
            # 원들의 색상과 라벨 정의 (모두 red로 변경)
            circle_configs = [
                {"color": "red", "label": "🔴 상1구간", "emoji": "1⃣"},  # 빨간색
                {"color": "red", "label": "🔴 상2구간", "emoji": "2⃣"},  # 빨간색
                {"color": "red", "label": "🔴 상3구간", "emoji": "3⃣"},  # 빨간색
                {"color": "red", "label": "🔴 상4구간", "emoji": "4⃣"},  # 빨간색
                {"color": "red", "label": "🔴 상5구간", "emoji": "5⃣"}   # 빨간색
            ]
            
            # 5개 원 그리기
            for i in range(5):
                x1 = vertical_lines[i]     # 왼쪽 수직선
                x2 = vertical_lines[i + 1] # 오른쪽 수직선
                
                # 두 교차점 계산
                point1 = (x1, top_y)  # 왼쪽 교차점
                point2 = (x2, top_y)  # 오른쪽 교차점
                
                config = circle_configs[i]
                
                # 라벨 위치 조정 (원이 겹치지 않도록)
                label_offset_y = -80 - (i * 15)  # 각 원마다 다른 높이
                
                # 이 구간의 가로 길이 및 퍼센티지 계산
                section_width = abs(x2 - x1)
                percentage = (section_width / total_face_width) * 100 if total_face_width > 0 else 0
                
                self.draw_circle_from_intersections(
                    point1, point2,
                    color=config["color"],
                    label=config["label"],
                    tag="top_circles",
                    label_offset=(0, label_offset_y)
                )
                
                # 원의 중앙에 퍼센티지 표시
                self.draw_circle_center_percentage(point1, point2, percentage, config["color"])
    
    def draw_circle_center_percentage(self, point1, point2, percentage, color):
        """원의 중앙에 퍼센티지 텍스트 표시"""
        # 원의 중심점 계산 (두 교차점의 중점)
        center_x = (point1[0] + point2[0]) / 2
        center_y = (point1[1] + point2[1]) / 2
        
        # 화면 좌표로 변환
        center_screen = self.image_to_screen_coords(center_x, center_y)
        
        if center_screen:
            # 퍼센티지 텍스트 (배경 없이 빨간색으로 1.5배 크기)
            self.canvas.create_text(
                center_screen[0], center_screen[1],
                text=f"{percentage:.1f}%", anchor="center",
                fill="red", font=("Arial", 14, "bold"), tags="top_circles"
            )
    
    def draw_circle_diameter_ratio(self, point1, point2, circle_type):
        """원의 중앙에 수직 거리 대비 지름 비율 표시"""
        # 1/3선과 3/3선의 y 좌표 구하기
        landmark_8 = self.get_landmark_coordinates(8)  # 1/3선
        face_bottom = self.get_landmark_coordinates(152)   # 3/3선
        
        if not all([landmark_8, face_bottom]):
            return
        
        # 전체 수직 거리 (1/3선에서 3/3선까지)
        total_vertical_distance = abs(face_bottom[1] - landmark_8[1])
        
        # 현재 원의 지름 (두 교차점 간 거리)
        circle_diameter = abs(point2[1] - point1[1])
        
        # 비율 계산
        if total_vertical_distance > 0:
            ratio = (circle_diameter / total_vertical_distance) * 100
            
            # 원의 중심점 계산
            center_x = (point1[0] + point2[0]) / 2
            center_y = (point1[1] + point2[1]) / 2
            
            # 화면 좌표로 변환
            center_screen = self.image_to_screen_coords(center_x, center_y)
            
            if center_screen:
                # 비율 텍스트 (배경 없이 빨간색으로 1.5배 크기)
                tag = "intersection_circle" if circle_type == "upper_right" else "second_circle"
                self.canvas.create_text(
                    center_screen[0], center_screen[1],
                    text=f"{ratio:.1f}%", anchor="center",
                    fill="red", font=("Arial", 14, "bold"), tags=tag
                )
    
    def draw_left_circle_diameter_ratio(self, point1, point2, circle_type):
        """왼쪽 원의 중앙에 총 지름 대비 각 원의 지름 비율 표시"""
        # 좌상 원과 좌하 원의 교차점들을 구해서 총 지름을 계산
        face_left = self.get_landmark_coordinates(234)     # 왼쪽 테두리
        landmark_2 = self.get_landmark_coordinates(2)      # 2/3 코선
        face_bottom = self.get_landmark_coordinates(152)   # 하단 테두리
        landmark_37 = self.get_landmark_coordinates(37)    # 37선
        
        if not all([face_left, landmark_2, face_bottom, landmark_37]):
            return
        
        # 좌상 원의 지름 (2/3코선에서 37선까지)
        upper_diameter = abs(landmark_37[1] - landmark_2[1])
        
        # 좌하 원의 지름 (하단테두리에서 37선까지) 
        lower_diameter = abs(landmark_37[1] - face_bottom[1])
        
        # 총 지름 (2/3코선에서 하단테두리까지)
        total_diameter = upper_diameter + lower_diameter
        
        # 현재 원의 지름
        current_diameter = abs(point2[1] - point1[1])
        
        # 비율 계산
        if total_diameter > 0:
            ratio = (current_diameter / total_diameter) * 100
            
            # 원의 중심점 계산
            center_x = (point1[0] + point2[0]) / 2
            center_y = (point1[1] + point2[1]) / 2
            
            # 화면 좌표로 변환
            center_screen = self.image_to_screen_coords(center_x, center_y)
            
            if center_screen:
                # 비율 텍스트 (파란색으로 표시)
                tag = "left_circle_1" if circle_type == "upper_left" else "left_circle_2"
                self.canvas.create_text(
                    center_screen[0], center_screen[1],
                    text=f"{ratio:.1f}%", anchor="center",
                    fill="blue", font=("Arial", 9, "bold"), tags=tag
                )

    def draw_jaw_curvature(self):
        """하악각과 턱목각을 계산하여 리프팅 효과 점수화"""
        import math
        
        # 하악각(Gonial Angle) 계산
        gonial_angle = self.calculate_gonial_angle()
        
        # 턱목각(Cervicomental Angle) 계산  
        cervicomental_angle = self.calculate_cervicomental_angle()
        
        if gonial_angle is None or cervicomental_angle is None:
            print("턱 각도를 계산할 수 없습니다.")
            return
        
        # 리프팅 효과 점수 계산 (날카로울수록 높은 점수)
        lifting_score = self.calculate_lifting_score(gonial_angle, cervicomental_angle)
        
        # 점수 시각화
        self.display_jaw_angles_score(gonial_angle, cervicomental_angle, lifting_score)
        
        print(f"하악각: {gonial_angle:.1f}°, 턱목각: {cervicomental_angle:.1f}°, 리프팅점수: {lifting_score:.0f}/100")
    
    def calculate_gonial_angle(self):
        """하악각(Gonial Angle) 계산: 하악지와 하악체 사이의 각도"""
        import math
        
        # 올바른 하악각 측정을 위한 랜드마크
        # 왼쪽: 귀 앞쪽(234) - 턱 모서리(172) - 턱 중앙 방향
        # 오른쪽: 귀 앞쪽(454) - 턱 모서리(397) - 턱 중앙 방향
        
        # 왼쪽 하악각 계산
        left_ear = self.get_landmark_coordinates(234)       # 왼쪽 귀 앞쪽 (얼굴 가장자리)
        left_jaw_corner = self.get_landmark_coordinates(172)  # 왼쪽 턱 모서리
        left_jaw_mid = self.get_landmark_coordinates(150)   # 왼쪽 턱선 중간
        
        # 오른쪽 하악각 계산  
        right_ear = self.get_landmark_coordinates(454)      # 오른쪽 귀 앞쪽 (얼굴 가장자리)
        right_jaw_corner = self.get_landmark_coordinates(397) # 오른쪽 턱 모서리
        right_jaw_mid = self.get_landmark_coordinates(379)  # 오른쪽 턱선 중간
        
        if not all([left_ear, left_jaw_corner, left_jaw_mid, right_ear, right_jaw_corner, right_jaw_mid]):
            return None
        
        # 좌우 하악각 계산 (수직선을 기준으로 각도 측정)
        left_gonial = self.calculate_jaw_angle_improved(left_ear, left_jaw_corner, left_jaw_mid)
        right_gonial = self.calculate_jaw_angle_improved(right_ear, right_jaw_corner, right_jaw_mid)
        
        if left_gonial is None or right_gonial is None:
            return None
        
        # 평균 하악각 (양쪽 평균)
        avg_gonial = (left_gonial + right_gonial) / 2
        return avg_gonial
    
    def calculate_cervicomental_angle(self):
        """턱목각(Cervicomental Angle) 계산: 턱끝과 목 사이의 각도"""
        import math
        
        # 턱목각을 구성하는 포인트들
        # 1. 턱끝: 152
        # 2. 목 앞쪽 최전방점: 18 (아래입술 하단을 목 대용으로 사용)
        # 3. 목 아래쪽 가상점: 턱끝에서 수직 아래로 일정 거리
        
        chin = self.get_landmark_coordinates(152)           # 턱끝
        neck_front = self.get_landmark_coordinates(18)      # 목 앞쪽 (아래입술 하단)
        
        if not all([chin, neck_front]):
            return None
        
        # 목 아래쪽 가상점 생성 (턱끝에서 수직 아래로)
        neck_bottom = (chin[0], chin[1] + abs(chin[1] - neck_front[1]) * 1.5)
        
        # 턱목각 계산 (3점으로 이루는 각도)
        angle = self.calculate_angle_3points(neck_bottom, chin, neck_front)
        return angle
    
    def calculate_angle_3points(self, p1, p2, p3):
        """3개 점으로 이루는 각도 계산 (p2가 꼭짓점)"""
        import math
        
        x1, y1 = p1
        x2, y2 = p2  # 꼭짓점
        x3, y3 = p3
        
        # 벡터 계산
        v1 = (x1 - x2, y1 - y2)  # p2에서 p1로의 벡터
        v2 = (x3 - x2, y3 - y2)  # p2에서 p3로의 벡터
        
        # 벡터 크기 계산
        len1 = math.sqrt(v1[0]**2 + v1[1]**2)
        len2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if len1 == 0 or len2 == 0:
            return None
        
        # 내적 계산
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        
        # 코사인 값 계산 (-1 ~ 1 범위로 클리핑)
        cos_angle = max(-1, min(1, dot_product / (len1 * len2)))
        
        # 라디안을 도(degree)로 변환
        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)
        
        return angle_deg
    
    def calculate_jaw_angle_improved(self, ear_point, jaw_corner, jaw_mid):
        """개선된 하악각 계산 - 수직선 기준으로 턱선 각도 측정"""
        import math
        
        # 수직선 방향 벡터 (위에서 아래로)
        vertical_vector = (0, 1)
        
        # 턱선 방향 벡터 (턱 모서리에서 턱 중간으로)
        jaw_vector = (jaw_mid[0] - jaw_corner[0], jaw_mid[1] - jaw_corner[1])
        
        # 벡터 크기 계산
        jaw_length = math.sqrt(jaw_vector[0]**2 + jaw_vector[1]**2)
        
        if jaw_length == 0:
            return None
        
        # 턱선 벡터 정규화
        jaw_unit = (jaw_vector[0] / jaw_length, jaw_vector[1] / jaw_length)
        
        # 수직선과 턱선 사이의 내적 계산
        dot_product = vertical_vector[0] * jaw_unit[0] + vertical_vector[1] * jaw_unit[1]
        
        # 코사인 값 클리핑 (-1 ~ 1)
        cos_angle = max(-1, min(1, dot_product))
        
        # 각도 계산 (라디안 → 도)
        angle_rad = math.acos(abs(cos_angle))
        angle_deg = math.degrees(angle_rad)
        
        # 하악각은 보통 90도에서 시작하여 180도에 가까워질수록 둔각
        # 실제 하악각으로 변환 (90도 + 계산된 각도)
        gonial_angle = 90 + angle_deg
        
        return gonial_angle
    
    
    def calculate_lifting_score(self, gonial_angle, cervicomental_angle):
        """리프팅 효과를 반영한 턱 점수 계산 (날카로울수록 높은 점수)"""
        
        # 1. 하악각 점수 계산 (90-120도가 이상적, 작을수록 V라인)
        # 점수 범위: 90도=100점, 120도=80점, 140도=20점, 150도 이상=0점
        if gonial_angle <= 90:
            gonial_score = 100
        elif gonial_angle <= 120:
            gonial_score = 100 - ((gonial_angle - 90) * 20 / 30)  # 90-120도: 100-80점
        elif gonial_angle <= 140:
            gonial_score = 80 - ((gonial_angle - 120) * 60 / 20)   # 120-140도: 80-20점
        else:
            gonial_score = max(0, 20 - ((gonial_angle - 140) * 20 / 10))  # 140도 이상: 20-0점
        
        # 2. 턱목각 점수 계산 (100-120도가 이상적, 선명할수록 높은 점수)
        # 점수 범위: 110도=100점, 105도=90점, 90도=60점, 80도 이하=40점
        if 105 <= cervicomental_angle <= 115:
            cervico_score = 100
        elif 100 <= cervicomental_angle <= 120:
            cervico_score = 90 - abs(cervicomental_angle - 110) * 2
        elif 90 <= cervicomental_angle <= 130:
            cervico_score = 70 - abs(cervicomental_angle - 110) * 1.5
        else:
            cervico_score = max(40, 70 - abs(cervicomental_angle - 110) * 2)
        
        # 3. 최종 리프팅 점수 (가중평균: 하악각 70%, 턱목각 30%)
        lifting_score = gonial_score * 0.7 + cervico_score * 0.3
        
        return max(0, min(100, lifting_score))
    
    def display_jaw_angles_score(self, gonial_angle, cervicomental_angle, lifting_score):
        """하악각과 턱목각 점수를 화면에 표시 (턱과 입술 중간 위치)"""
        # 턱 최하단 (152번 랜드마크)과 입술 하단 (18번 랜드마크) 중간 지점 계산
        jaw_bottom = self.get_landmark_coordinates(152)  # 턱 최하단
        lip_bottom = self.get_landmark_coordinates(18)   # 아래입술 하단
        
        if not all([jaw_bottom, lip_bottom]):
            return
        
        # 턱과 입술의 중간 지점 계산
        center_x = (jaw_bottom[0] + lip_bottom[0]) / 2
        center_y = (jaw_bottom[1] + lip_bottom[1]) / 2
        
        # 화면 좌표로 변환
        display_point = self.image_to_screen_coords(center_x, center_y)
        
        if display_point:
            # 메인 턱 곡률 점수 표시 (빨간색 텍스트)
            self.canvas.create_text(
                display_point[0], display_point[1] - 10,
                text=f"턱곡률 {lifting_score:.0f}점", anchor="center",
                fill="red", font=("Arial", 12, "bold"), tags="jaw_curvature"
            )
            
            # 세부 각도 정보 표시 (더 큰 글씨, 흰색)
            self.canvas.create_text(
                display_point[0], display_point[1] + 8,
                text=f"하악각{gonial_angle:.0f}° 턱목각{cervicomental_angle:.0f}°", 
                anchor="center", fill="white", font=("Arial", 11, "bold"), tags="jaw_curvature"
            )

    def show_score_calculation_details(self, current_ratios):
        """각 점수 계산 과정을 상세히 시각화"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
            
        # 기존 표시 제거
        self.canvas.delete("calculation_details")
        self.canvas.delete("calculation_lines")
        
        print("점수 계산 과정을 상세히 표시합니다...")
        
        try:
            # 각 부위별 상세 계산 표시
            self.show_forehead_score_detail(current_ratios)
            self.show_mouth_score_detail(current_ratios)
            self.show_eye_spacing_score_detail(current_ratios)
            
            # 20초 후 자동 제거
            self.root.after(20000, lambda: [
                self.canvas.delete("calculation_details"),
                self.canvas.delete("calculation_lines")
            ])
            print("점수 계산 상세 정보가 20초간 표시됩니다.")
            
        except Exception as e:
            print(f"점수 계산 상세 표시 중 오류: {str(e)}")
    
    def show_forehead_score_detail(self, current_ratios):
        """이마(전체 얼굴 비율) 점수 계산 상세"""
        if "전체_얼굴_비율" not in current_ratios:
            return
            
        face_top = self.get_landmark_coordinates(10)
        face_bottom = self.get_landmark_coordinates(152)
        face_left = self.get_landmark_coordinates(234)
        face_right = self.get_landmark_coordinates(454)
        
        if all([face_top, face_bottom, face_left, face_right]):
            # 실제 측정값
            face_height = self.calculate_distance(face_top, face_bottom)
            face_width = self.calculate_distance(face_left, face_right)
            current_ratio = current_ratios["전체_얼굴_비율"]
            ideal_ratio = self.FACE_GOLDEN_RATIOS["전체_얼굴_비율"]
            
            # 점수 계산
            deviation = abs(current_ratio - ideal_ratio)
            score = max(0, 100 - (deviation / ideal_ratio * 100))
            
            # 화면 좌표
            top_screen = self.image_to_screen_coords(face_top[0], face_top[1])
            left_screen = self.image_to_screen_coords(face_left[0], face_left[1])
            
            if top_screen and left_screen:
                # 측정 영역 강조
                self.draw_bidirectional_arrow(
                    top_screen[0], top_screen[1],
                    self.image_to_screen_coords(face_bottom[0], face_bottom[1])[0], 
                    self.image_to_screen_coords(face_bottom[0], face_bottom[1])[1],
                    color="#FF6B6B", width=4, arrow_size=12
                )
                
                mid_y = (top_screen[1] + self.image_to_screen_coords(face_bottom[0], face_bottom[1])[1]) / 2
                self.draw_bidirectional_arrow(
                    left_screen[0], mid_y,
                    self.image_to_screen_coords(face_right[0], face_right[1])[0], mid_y,
                    color="#FF6B6B", width=4, arrow_size=12
                )
                
                # 상세 정보 박스
                info_x = left_screen[0] - 200
                info_y = top_screen[1] + 50
                
                self.canvas.create_rectangle(
                    info_x, info_y, info_x + 180, info_y + 120,
                    fill="white", outline="#FF6B6B", width=3, tags="calculation_details"
                )
                
                lines = [
                    "🔴 이마 점수 계산",
                    f"얼굴 세로: {face_height:.1f}px",
                    f"얼굴 가로: {face_width:.1f}px", 
                    f"현재 비율: {current_ratio:.3f}",
                    f"이상 비율: {ideal_ratio:.3f}",
                    f"편차: {deviation:.3f}",
                    f"최종 점수: {score:.1f}%"
                ]
                
                for i, line in enumerate(lines):
                    color = "#FF6B6B" if i == 0 else "#000000"
                    font = ("Arial", 8, "bold") if i == 0 else ("Arial", 7)
                    self.canvas.create_text(
                        info_x + 5, info_y + 10 + i*15,
                        text=line, anchor="w", fill=color, font=font,
                        tags="calculation_details"
                    )
    
    def show_mouth_score_detail(self, current_ratios):
        """입 점수 계산 상세"""
        if "입_너비" not in current_ratios:
            return
            
        mouth_left = self.get_landmark_coordinates(61)
        mouth_right = self.get_landmark_coordinates(291)
        nose_left = self.get_landmark_coordinates(129)
        nose_right = self.get_landmark_coordinates(358)
        
        if all([mouth_left, mouth_right, nose_left, nose_right]):
            # 실제 측정값
            mouth_width = self.calculate_distance(mouth_left, mouth_right)
            nose_width = self.calculate_distance(nose_left, nose_right)
            current_ratio = current_ratios["입_너비"]
            ideal_ratio = self.FACE_GOLDEN_RATIOS["입_너비"]
            
            # 점수 계산
            deviation = abs(current_ratio - ideal_ratio)
            score = max(0, 100 - (deviation / ideal_ratio * 100))
            
            # 화면 좌표
            ml_screen = self.image_to_screen_coords(mouth_left[0], mouth_left[1])
            mr_screen = self.image_to_screen_coords(mouth_right[0], mouth_right[1])
            nl_screen = self.image_to_screen_coords(nose_left[0], nose_left[1])
            nr_screen = self.image_to_screen_coords(nose_right[0], nose_right[1])
            
            if all([ml_screen, mr_screen, nl_screen, nr_screen]):
                # 측정 영역 강조
                self.draw_bidirectional_arrow(
                    ml_screen[0], ml_screen[1],
                    mr_screen[0], mr_screen[1],
                    color="#FFEAA7", width=4, arrow_size=10
                )
                
                self.draw_bidirectional_arrow(
                    nl_screen[0], nl_screen[1],
                    nr_screen[0], nr_screen[1],
                    color="#E17055", width=4, arrow_size=10
                )
                
                # 상세 정보 박스
                info_x = mr_screen[0] + 20
                info_y = mr_screen[1] + 20
                
                self.canvas.create_rectangle(
                    info_x, info_y, info_x + 180, info_y + 120,
                    fill="white", outline="#FFEAA7", width=3, tags="calculation_details"
                )
                
                lines = [
                    "💛 입 점수 계산",
                    f"입 너비: {mouth_width:.1f}px",
                    f"코 너비: {nose_width:.1f}px",
                    f"현재 비율: {current_ratio:.3f}",
                    f"이상 비율: {ideal_ratio:.3f}",
                    f"편차: {deviation:.3f}",
                    f"최종 점수: {score:.1f}%"
                ]
                
                for i, line in enumerate(lines):
                    color = "#FFEAA7" if i == 0 else "#000000"
                    font = ("Arial", 8, "bold") if i == 0 else ("Arial", 7)
                    self.canvas.create_text(
                        info_x + 5, info_y + 10 + i*15,
                        text=line, anchor="w", fill=color, font=font,
                        tags="calculation_details"
                    )
    
    def show_eye_spacing_score_detail(self, current_ratios):
        """눈간격 점수 계산 상세"""
        if "눈_간격" not in current_ratios:
            return
            
        left_eye_inner = self.get_landmark_coordinates(133)
        left_eye_outer = self.get_landmark_coordinates(33)
        right_eye_inner = self.get_landmark_coordinates(362)
        right_eye_outer = self.get_landmark_coordinates(263)
        
        if all([left_eye_inner, left_eye_outer, right_eye_inner, right_eye_outer]):
            # 실제 측정값
            left_eye_width = self.calculate_distance(left_eye_inner, left_eye_outer)
            right_eye_width = self.calculate_distance(right_eye_inner, right_eye_outer)
            eye_gap = self.calculate_distance(left_eye_inner, right_eye_inner)
            avg_eye_width = (left_eye_width + right_eye_width) / 2
            current_ratio = current_ratios["눈_간격"]
            ideal_ratio = 1.0
            
            # 점수 계산
            deviation = abs(current_ratio - ideal_ratio)
            score = max(0, 100 - (deviation / ideal_ratio * 100))
            
            # 화면 좌표
            coords = {}
            coords['li'] = self.image_to_screen_coords(left_eye_inner[0], left_eye_inner[1])
            coords['lo'] = self.image_to_screen_coords(left_eye_outer[0], left_eye_outer[1])
            coords['ri'] = self.image_to_screen_coords(right_eye_inner[0], right_eye_inner[1])
            coords['ro'] = self.image_to_screen_coords(right_eye_outer[0], right_eye_outer[1])
            
            if all(coords.values()):
                # 측정 영역 강조
                self.draw_bidirectional_arrow(
                    coords['li'][0], coords['li'][1],
                    coords['lo'][0], coords['lo'][1],
                    color="#74b9ff", width=4, arrow_size=8
                )
                
                self.draw_bidirectional_arrow(
                    coords['ri'][0], coords['ri'][1],
                    coords['ro'][0], coords['ro'][1],
                    color="#74b9ff", width=4, arrow_size=8
                )
                
                self.draw_bidirectional_arrow(
                    coords['li'][0], coords['li'][1],
                    coords['ri'][0], coords['ri'][1],
                    color="#4ECDC4", width=5, arrow_size=10
                )
                
                # 상세 정보 박스
                info_x = coords['ri'][0] + 30
                info_y = coords['ri'][1] - 100
                
                self.canvas.create_rectangle(
                    info_x, info_y, info_x + 190, info_y + 130,
                    fill="white", outline="#4ECDC4", width=3, tags="calculation_details"
                )
                
                lines = [
                    "🔵 눈간격 점수 계산",
                    f"왼쪽 눈: {left_eye_width:.1f}px",
                    f"오른쪽 눈: {right_eye_width:.1f}px",
                    f"평균 눈너비: {avg_eye_width:.1f}px",
                    f"눈사이 간격: {eye_gap:.1f}px",
                    f"현재 비율: {current_ratio:.3f}",
                    f"이상 비율: {ideal_ratio:.3f}",
                    f"편차: {deviation:.3f}",
                    f"최종 점수: {score:.1f}%"
                ]
                
                for i, line in enumerate(lines):
                    color = "#4ECDC4" if i == 0 else "#000000"
                    font = ("Arial", 8, "bold") if i == 0 else ("Arial", 7)
                    self.canvas.create_text(
                        info_x + 5, info_y + 10 + i*13,
                        text=line, anchor="w", fill=color, font=font,
                        tags="calculation_details"
                    )

    def draw_face_outline_ratio(self, current_ratios):
        """전체 얼굴 비율 라인 그리기"""
        face_top = self.get_landmark_coordinates(10)
        face_bottom = self.get_landmark_coordinates(152)
        face_left = self.get_landmark_coordinates(234)
        face_right = self.get_landmark_coordinates(454)
        
        if all([face_top, face_bottom, face_left, face_right]):
            # 화면 좌표 변환
            top_screen = self.image_to_screen_coords(face_top[0], face_top[1])
            bottom_screen = self.image_to_screen_coords(face_bottom[0], face_bottom[1])
            left_screen = self.image_to_screen_coords(face_left[0], face_left[1])
            right_screen = self.image_to_screen_coords(face_right[0], face_right[1])
            
            if all([top_screen, bottom_screen, left_screen, right_screen]):
                # 세로 라인 (얼굴 길이) - 양방향 화살표
                self.draw_bidirectional_arrow(
                    top_screen[0], top_screen[1], 
                    bottom_screen[0], bottom_screen[1],
                    color="#ff0000", width=3, arrow_size=10
                )
                
                # 가로 라인 (얼굴 너비) - 양방향 화살표
                mid_y = (top_screen[1] + bottom_screen[1]) // 2
                self.draw_bidirectional_arrow(
                    left_screen[0], mid_y, 
                    right_screen[0], mid_y,
                    color="#ff0000", width=3, arrow_size=10
                )
                
                # 측정값 표시
                face_height = self.calculate_distance(face_top, face_bottom)
                face_width = self.calculate_distance(face_left, face_right)
                current_ratio = face_height / face_width if face_width > 0 else 0
                golden_ratio = self.FACE_GOLDEN_RATIOS["전체_얼굴_비율"]
                
                # 라벨 배경
                label_x = right_screen[0] + 10
                label_y = mid_y - 30
                
                self.canvas.create_rectangle(
                    label_x, label_y, label_x + 200, label_y + 60,
                    fill="white", outline="#ff0000", width=2, tags="ratio_lines"
                )
                
                # 텍스트 라벨
                self.canvas.create_text(
                    label_x + 5, label_y + 10, 
                    text=f"📏 전체 얼굴 비율", 
                    anchor="w", fill="#000000", font=("Arial", 9, "bold"),
                    tags="ratio_lines"
                )
                self.canvas.create_text(
                    label_x + 5, label_y + 25, 
                    text=f"현재: {current_ratio:.3f}", 
                    anchor="w", fill="#ff0000", font=("Arial", 8),
                    tags="ratio_lines"
                )
                self.canvas.create_text(
                    label_x + 5, label_y + 40, 
                    text=f"황금: {golden_ratio:.3f}", 
                    anchor="w", fill="#ffd700", font=("Arial", 8),
                    tags="ratio_lines"
                )
    
    def draw_face_thirds_ratio(self, current_ratios):
        """얼굴 삼등분 라인 그리기"""
        forehead_top = self.get_landmark_coordinates(10)
        forehead_bottom = self.get_landmark_coordinates(9)
        mid_face_bottom = self.get_landmark_coordinates(164)
        lower_face_bottom = self.get_landmark_coordinates(152)
        face_left = self.get_landmark_coordinates(234)
        face_right = self.get_landmark_coordinates(454)
        
        if all([forehead_top, forehead_bottom, mid_face_bottom, lower_face_bottom, face_left, face_right]):
            # 화면 좌표 변환
            coords = {}
            coords['top'] = self.image_to_screen_coords(forehead_top[0], forehead_top[1])
            coords['f_bottom'] = self.image_to_screen_coords(forehead_bottom[0], forehead_bottom[1])
            coords['m_bottom'] = self.image_to_screen_coords(mid_face_bottom[0], mid_face_bottom[1])
            coords['l_bottom'] = self.image_to_screen_coords(lower_face_bottom[0], lower_face_bottom[1])
            coords['left'] = self.image_to_screen_coords(face_left[0], face_left[1])
            coords['right'] = self.image_to_screen_coords(face_right[0], face_right[1])
            
            if all(coords.values()):
                # 삼등분 가로 라인들
                lines = [
                    (coords['f_bottom'], "이마-중간얼굴 경계"),
                    (coords['m_bottom'], "중간-아래얼굴 경계")
                ]
                
                for (y_coord, label), color in zip(lines, ["#00ff00", "#00aa00"]):
                    # 양방향 화살표 점선으로 그리기
                    self.draw_bidirectional_arrow(
                        coords['left'][0], y_coord[1], 
                        coords['right'][0], y_coord[1],
                        color=color, width=2, arrow_size=7, dash=(5, 3)
                    )
                    
                    # 라벨
                    self.canvas.create_text(
                        coords['left'][0] - 10, y_coord[1], 
                        text=label, anchor="e", fill=color, 
                        font=("Arial", 7), tags="ratio_lines"
                    )
                
                # 비율 계산 및 표시
                if "이마_비율" in current_ratios:
                    label_x = coords['right'][0] + 10
                    label_y = coords['top'][1] + 50
                    
                    self.canvas.create_rectangle(
                        label_x, label_y, label_x + 160, label_y + 80,
                        fill="white", outline="#00ff00", width=2, tags="ratio_lines"
                    )
                    
                    self.canvas.create_text(
                        label_x + 5, label_y + 10, 
                        text="📐 얼굴 삼등분", 
                        anchor="w", fill="#000000", font=("Arial", 9, "bold"),
                        tags="ratio_lines"
                    )
                    
                    ratios = ["이마_비율", "중간_얼굴_비율", "아래_얼굴_비율"]
                    colors = ["#ff6b6b", "#4ecdc4", "#45b7d1"]
                    names = ["이마", "중간", "아래"]
                    
                    for i, (ratio_key, color, name) in enumerate(zip(ratios, colors, names)):
                        if ratio_key in current_ratios:
                            self.canvas.create_text(
                                label_x + 5, label_y + 25 + i*15, 
                                text=f"{name}: {current_ratios[ratio_key]:.2f} (이상:1.0)", 
                                anchor="w", fill=color, font=("Arial", 7),
                                tags="ratio_lines"
                            )
    
    def draw_eye_spacing_ratio(self, current_ratios):
        """눈 간격 비율 라인 그리기"""
        left_eye_inner = self.get_landmark_coordinates(133)
        left_eye_outer = self.get_landmark_coordinates(33)
        right_eye_inner = self.get_landmark_coordinates(362)
        right_eye_outer = self.get_landmark_coordinates(263)
        
        if all([left_eye_inner, left_eye_outer, right_eye_inner, right_eye_outer]):
            # 화면 좌표 변환
            coords = {}
            coords['li'] = self.image_to_screen_coords(left_eye_inner[0], left_eye_inner[1])
            coords['lo'] = self.image_to_screen_coords(left_eye_outer[0], left_eye_outer[1])
            coords['ri'] = self.image_to_screen_coords(right_eye_inner[0], right_eye_inner[1])
            coords['ro'] = self.image_to_screen_coords(right_eye_outer[0], right_eye_outer[1])
            
            if all(coords.values()):
                # 왼쪽 눈 너비 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['li'][0], coords['li'][1], 
                    coords['lo'][0], coords['lo'][1],
                    color="#0066ff", width=2, arrow_size=6
                )
                
                # 오른쪽 눈 너비 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['ri'][0], coords['ri'][1], 
                    coords['ro'][0], coords['ro'][1],
                    color="#0066ff", width=2, arrow_size=6
                )
                
                # 눈 사이 간격 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['li'][0], coords['li'][1], 
                    coords['ri'][0], coords['ri'][1],
                    color="#ffaa00", width=3, arrow_size=8
                )
                
                # 측정값 표시
                if "눈_간격" in current_ratios:
                    left_eye_width = self.calculate_distance(left_eye_inner, left_eye_outer)
                    right_eye_width = self.calculate_distance(right_eye_inner, right_eye_outer)
                    eye_gap = self.calculate_distance(left_eye_inner, right_eye_inner)
                    avg_eye_width = (left_eye_width + right_eye_width) / 2
                    
                    label_x = coords['ri'][0] + 10
                    label_y = coords['ri'][1] - 60
                    
                    self.canvas.create_rectangle(
                        label_x, label_y, label_x + 180, label_y + 70,
                        fill="white", outline="#0066ff", width=2, tags="ratio_lines"
                    )
                    
                    self.canvas.create_text(
                        label_x + 5, label_y + 10, 
                        text="👁️ 눈 간격 비율", 
                        anchor="w", fill="#000000", font=("Arial", 9, "bold"),
                        tags="ratio_lines"
                    )
                    self.canvas.create_text(
                        label_x + 5, label_y + 25, 
                        text=f"눈사이: {eye_gap:.1f}px", 
                        anchor="w", fill="#ffaa00", font=("Arial", 7),
                        tags="ratio_lines"
                    )
                    self.canvas.create_text(
                        label_x + 5, label_y + 40, 
                        text=f"평균눈너비: {avg_eye_width:.1f}px", 
                        anchor="w", fill="#0066ff", font=("Arial", 7),
                        tags="ratio_lines"
                    )
                    self.canvas.create_text(
                        label_x + 5, label_y + 55, 
                        text=f"비율: {current_ratios['눈_간격']:.3f} (이상:1.0)", 
                        anchor="w", fill="#ff0000", font=("Arial", 7),
                        tags="ratio_lines"
                    )
    
    def draw_eye_spacing_percentage(self, current_ratios):
        """눈간격 비율 수치화 % 표시"""
        if "눈_간격" in current_ratios:
            # 이상적인 비율 대비 퍼센티지 계산
            ideal_ratio = 1.0
            current_ratio = current_ratios['눈_간격']
            percentage = (current_ratio / ideal_ratio) * 100
            
            # 얼굴 중앙에 퍼센티지 표시
            face_center = self.get_landmark_coordinates(2)  # 코 끝
            if face_center:
                screen_pos = self.image_to_screen_coords(face_center[0], face_center[1])
                if screen_pos:
                    # 눈간격 퍼센티지 표시 (눈 높이 기준)
                    left_eye = self.get_landmark_coordinates(133)
                    if left_eye:
                        eye_screen = self.image_to_screen_coords(left_eye[0], left_eye[1])
                        if eye_screen:
                            self.canvas.create_text(
                                screen_pos[0] - 50, eye_screen[1] - 40,
                                text=f"👁️ {percentage:.1f}%", anchor="center",
                                fill="blue", font=("Arial", 16, "bold"), tags="ratio_lines"
                            )
    
    def draw_eye_spacing_arrows_only(self, current_ratios):
        """눈간격 화살표만 그리기 (네모박스 없음)"""
        left_eye_inner = self.get_landmark_coordinates(133)
        left_eye_outer = self.get_landmark_coordinates(33)
        right_eye_inner = self.get_landmark_coordinates(362)
        right_eye_outer = self.get_landmark_coordinates(263)
        
        if all([left_eye_inner, left_eye_outer, right_eye_inner, right_eye_outer]):
            # 화면 좌표 변환
            coords = {}
            coords['li'] = self.image_to_screen_coords(left_eye_inner[0], left_eye_inner[1])
            coords['lo'] = self.image_to_screen_coords(left_eye_outer[0], left_eye_outer[1])
            coords['ri'] = self.image_to_screen_coords(right_eye_inner[0], right_eye_inner[1])
            coords['ro'] = self.image_to_screen_coords(right_eye_outer[0], right_eye_outer[1])
            
            if all(coords.values()):
                # 왼쪽 눈 너비 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['li'][0], coords['li'][1], 
                    coords['lo'][0], coords['lo'][1],
                    color="#0066ff", width=2, arrow_size=6
                )
                
                # 오른쪽 눈 너비 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['ri'][0], coords['ri'][1], 
                    coords['ro'][0], coords['ro'][1],
                    color="#0066ff", width=2, arrow_size=6
                )
                
                # 눈 사이 간격 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['li'][0], coords['li'][1], 
                    coords['ri'][0], coords['ri'][1],
                    color="#ffaa00", width=3, arrow_size=8
                )
    
    def draw_mouth_nose_ratio(self, current_ratios):
        """입/코 너비 비율 라인 그리기"""
        nose_left = self.get_landmark_coordinates(129)
        nose_right = self.get_landmark_coordinates(358)
        mouth_left = self.get_landmark_coordinates(61)
        mouth_right = self.get_landmark_coordinates(291)
        
        if all([nose_left, nose_right, mouth_left, mouth_right]):
            # 화면 좌표 변환
            coords = {}
            coords['nl'] = self.image_to_screen_coords(nose_left[0], nose_left[1])
            coords['nr'] = self.image_to_screen_coords(nose_right[0], nose_right[1])
            coords['ml'] = self.image_to_screen_coords(mouth_left[0], mouth_left[1])
            coords['mr'] = self.image_to_screen_coords(mouth_right[0], mouth_right[1])
            
            if all(coords.values()):
                # 코 너비 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['nl'][0], coords['nl'][1], 
                    coords['nr'][0], coords['nr'][1],
                    color="#ff6600", width=2, arrow_size=6
                )
                
                # 입 너비 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['ml'][0], coords['ml'][1], 
                    coords['mr'][0], coords['mr'][1],
                    color="#ff0066", width=2, arrow_size=6
                )
                
                # 측정값 표시
                if "입_너비" in current_ratios:
                    nose_width = self.calculate_distance(nose_left, nose_right)
                    mouth_width = self.calculate_distance(mouth_left, mouth_right)
                    
                    label_x = coords['mr'][0] + 10
                    label_y = coords['mr'][1] - 30
                    
                    self.canvas.create_rectangle(
                        label_x, label_y, label_x + 180, label_y + 70,
                        fill="white", outline="#ff0066", width=2, tags="ratio_lines"
                    )
                    
                    self.canvas.create_text(
                        label_x + 5, label_y + 10, 
                        text="👄 입/코 비율", 
                        anchor="w", fill="#000000", font=("Arial", 9, "bold"),
                        tags="ratio_lines"
                    )
                    self.canvas.create_text(
                        label_x + 5, label_y + 25, 
                        text=f"입너비: {mouth_width:.1f}px", 
                        anchor="w", fill="#ff0066", font=("Arial", 7),
                        tags="ratio_lines"
                    )
                    self.canvas.create_text(
                        label_x + 5, label_y + 40, 
                        text=f"코너비: {nose_width:.1f}px", 
                        anchor="w", fill="#ff6600", font=("Arial", 7),
                        tags="ratio_lines"
                    )
                    self.canvas.create_text(
                        label_x + 5, label_y + 55, 
                        text=f"비율: {current_ratios['입_너비']:.3f} (이상:1.618)", 
                        anchor="w", fill="#ff0000", font=("Arial", 7),
                        tags="ratio_lines"
                    )
    
    def draw_mouth_nose_percentage(self, current_ratios):
        """입코비율 수치화 % 표시"""
        if "입_너비" in current_ratios:
            # 이상적인 비율 대비 퍼센티지 계산 (황금비율 기준)
            ideal_ratio = 1.618  # 황금비율
            current_ratio = current_ratios['입_너비']
            percentage = (current_ratio / ideal_ratio) * 100
            
            # 입 아래쪽에 퍼센티지 표시
            mouth_center = self.get_landmark_coordinates(13)  # 입 아래
            if mouth_center:
                screen_pos = self.image_to_screen_coords(mouth_center[0], mouth_center[1])
                if screen_pos:
                    self.canvas.create_text(
                        screen_pos[0], screen_pos[1] + 30,
                        text=f"👄 {percentage:.1f}%", anchor="center",
                        fill="red", font=("Arial", 16, "bold"), tags="ratio_lines"
                    )
    
    def draw_mouth_nose_arrows_only(self, current_ratios):
        """입코비율 화살표만 그리기 (네모박스 없음)"""
        nose_left = self.get_landmark_coordinates(129)
        nose_right = self.get_landmark_coordinates(358)
        mouth_left = self.get_landmark_coordinates(61)
        mouth_right = self.get_landmark_coordinates(291)
        
        if all([nose_left, nose_right, mouth_left, mouth_right]):
            # 화면 좌표 변환
            coords = {}
            coords['nl'] = self.image_to_screen_coords(nose_left[0], nose_left[1])
            coords['nr'] = self.image_to_screen_coords(nose_right[0], nose_right[1])
            coords['ml'] = self.image_to_screen_coords(mouth_left[0], mouth_left[1])
            coords['mr'] = self.image_to_screen_coords(mouth_right[0], mouth_right[1])
            
            if all(coords.values()):
                # 코 너비 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['nl'][0], coords['nl'][1], 
                    coords['nr'][0], coords['nr'][1],
                    color="#ff6600", width=2, arrow_size=6
                )
                
                # 입 너비 양방향 화살표
                self.draw_bidirectional_arrow(
                    coords['ml'][0], coords['ml'][1], 
                    coords['mr'][0], coords['mr'][1],
                    color="#ff0066", width=2, arrow_size=6
                )
    
    def draw_golden_ratio_guide(self):
        """황금비율 가이드라인 표시"""
        face_top = self.get_landmark_coordinates(10)
        face_bottom = self.get_landmark_coordinates(152)
        face_left = self.get_landmark_coordinates(234)
        face_right = self.get_landmark_coordinates(454)
        
        if all([face_top, face_bottom, face_left, face_right]):
            # 현재 얼굴 크기
            face_height = self.calculate_distance(face_top, face_bottom)
            face_width = self.calculate_distance(face_left, face_right)
            
            # 황금비율로 계산한 이상적인 크기
            ideal_height = face_width * self.GOLDEN_RATIO
            ideal_width = face_height / self.GOLDEN_RATIO
            
            # 화면 좌표
            top_screen = self.image_to_screen_coords(face_top[0], face_top[1])
            left_screen = self.image_to_screen_coords(face_left[0], face_left[1])
            
            if top_screen and left_screen:
                # 황금비율 가이드 박스 (점선)
                center_x = (face_left[0] + face_right[0]) / 2
                center_y = (face_top[1] + face_bottom[1]) / 2
                
                ideal_top = center_y - ideal_height / 2
                ideal_bottom = center_y + ideal_height / 2
                ideal_left = center_x - ideal_width / 2
                ideal_right = center_x + ideal_width / 2
                
                # 화면 좌표로 변환
                ideal_coords = {}
                ideal_coords['top'] = self.image_to_screen_coords(center_x, ideal_top)
                ideal_coords['bottom'] = self.image_to_screen_coords(center_x, ideal_bottom)
                ideal_coords['left'] = self.image_to_screen_coords(ideal_left, center_y)
                ideal_coords['right'] = self.image_to_screen_coords(ideal_right, center_y)
                
                if all(ideal_coords.values()):
                    # 황금비율 가이드 라인 (점선 양방향 화살표)
                    self.draw_bidirectional_arrow(
                        ideal_coords['top'][0], ideal_coords['top'][1],
                        ideal_coords['bottom'][0], ideal_coords['bottom'][1],
                        color="#ffd700", width=2, arrow_size=8, dash=(3, 7)
                    )
                    
                    self.draw_bidirectional_arrow(
                        ideal_coords['left'][0], ideal_coords['left'][1],
                        ideal_coords['right'][0], ideal_coords['right'][1],
                        color="#ffd700", width=2, arrow_size=8, dash=(3, 7)
                    )
                    
                    # 가이드 라벨
                    self.canvas.create_text(
                        ideal_coords['right'][0] + 10, ideal_coords['right'][1] - 20, 
                        text="✨ 황금비율 가이드", 
                        anchor="w", fill="#ffd700", font=("Arial", 8, "bold"),
                        tags="ratio_lines"
                    )

def main():
    root = tk.Tk()
    app = FaceSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()