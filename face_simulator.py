import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import math
import mediapipe as mp

class FaceSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("🔧 얼굴 성형 시뮬레이터")
        self.root.geometry("1400x1300")
        
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
        
        # 탭 노트북 (높이 최적화)
        notebook_frame = ttk.Frame(control_frame, height=950)
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
    
    def apply_pull_warp_with_params(self, start_x, start_y, end_x, end_y, strength):
        """파라미터를 지정한 당기기 변형"""
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
        pixel_dist = np.sqrt(pixel_dx*pixel_dx + pixel_dy*pixel_dy)
        
        influence_radius = self.get_influence_radius_pixels()
        mask = pixel_dist < influence_radius
        
        strength_map = np.zeros_like(pixel_dist)
        valid_dist = pixel_dist[mask]
        
        if len(valid_dist) > 0:
            strength_map[mask] = (1 - valid_dist / influence_radius) ** 2
            strength_map[mask] *= strength
            
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
                "nose_sides": {
                    "indices": [49, 209, 198, 236, 196, 122, 193, 279, 360, 420, 456, 419, 351, 417],  # 코 측면 (좌측+우측 통합)
                    "color": "#ffcc00"  # 밝은 황색
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
                "forehead", "glabella", "nose_area", "jawline_area", 
                "lip_lower", "lip_upper", "eyes", "iris", "mouth_area",
                "eyebrows", "eyebrow_area", "cheek_area_left", "cheek_area_right",
                "nasolabial_left", "nasolabial_right", "nose_bridge", "nose_wings",
                "eyelid_lower_surround_area", "eyelid_lower_area", "eyelid_upper_surround_area", "eyelid_upper_area"
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
            # 2개 점이면 직선
            if len(points) == 2:
                x1, y1 = points[0]
                x2, y2 = points[1]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=line_width,
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
            # 오류 발생시 기본 직선으로 대체
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=line_width,
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
                "forehead", "glabella", "nose_area", "jawline_area", 
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
            
            # 연속된 점들을 선으로 연결 (일반적인 연결)
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                
                # 58-323과 172-352 연결은 제외 (인덱스 기준)
                # 58은 인덱스 16, 323은 인덱스 15
                # 172는 인덱스 0, 352는 인덱스 35 (마지막)
                skip_connection = False
                
                # 58(idx 16) -> 323(idx 15) 연결 제외 (역순이므로 15->16)
                if i == 15:  # 323 -> 58
                    skip_connection = True
                
                if not skip_connection:
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
            
            # 특별 연결: 58번(인덱스 16)과 172번(인덱스 0)을 연결
            if len(points) > 16:
                x1, y1 = points[16]  # 58번
                x2, y2 = points[0]   # 172번
                
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=line_width,
                    tags="landmarks"
                )
            
            # 마지막 점(352, 인덱스 35)과 첫 번째 점(172, 인덱스 0)의 연결은 제외
            # (닫힌 다각형을 만들지 않음)
            
        except Exception as e:
            print(f"턱선 선 그리기 오류: {str(e)}")
    
    def _draw_eyebrow_lines(self, points, color, line_width):
        """눈썹 선 그리기 - 좌우 눈썹 분리 처리 및 특별 연결"""
        try:
            if len(points) < 4:
                return
            
            # 눈썹은 좌우로 분리되어 있으므로 중간 지점으로 나눔
            mid_point = len(points) // 2
            
            # 왼쪽 눈썹 연결 (첫 10개)
            left_eyebrow = points[:mid_point]
            if len(left_eyebrow) > 1:
                for i in range(len(left_eyebrow) - 1):
                    x1, y1 = left_eyebrow[i]
                    x2, y2 = left_eyebrow[i + 1]
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
                
                # 65(인덱스 9)와 55(인덱스 0) 연결
                if len(left_eyebrow) >= 10:
                    x1, y1 = left_eyebrow[9]  # 65
                    x2, y2 = left_eyebrow[0]  # 55
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
            
            # 오른쪽 눈썹 연결 (나머지 10개)
            right_eyebrow = points[mid_point:]
            if len(right_eyebrow) > 1:
                for i in range(len(right_eyebrow) - 1):
                    x1, y1 = right_eyebrow[i]
                    x2, y2 = right_eyebrow[i + 1]
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
                
                # 295(인덱스 9)와 285(인덱스 0) 연결
                if len(right_eyebrow) >= 10:
                    x1, y1 = right_eyebrow[9]  # 295
                    x2, y2 = right_eyebrow[0]  # 285
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
                    
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
                
                # 일반 연속 연결
                for i in range(len(filtered_points) - 1):
                    # 147-205 연결 건너뛰기 (인덱스 9->10)
                    if i == 9:  # 205 -> 147 연결 건너뛰기
                        continue
                    # 123-187 연결 건너뛰기 (인덱스 12->11)
                    if i == 11:  # 187 -> 123 연결 건너뛰기
                        continue
                        
                    x1, y1 = filtered_points[i]
                    x2, y2 = filtered_points[i + 1]
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
                
                # 특별 연결들
                if len(filtered_points) > 12:
                    # 123-147 연결
                    x1, y1 = filtered_points[12]  # 123
                    x2, y2 = filtered_points[10]  # 147
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                    
                    # 187-205 연결 추가
                    x1, y1 = filtered_points[11]  # 187
                    x2, y2 = filtered_points[9]   # 205
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 닫힌 다각형 연결
                if len(filtered_points) > 2:
                    x1, y1 = filtered_points[-1]
                    x2, y2 = filtered_points[0]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                    
            elif group_name == "cheek_area_right":
                # 오른쪽 볼: 280 제외, 특별 연결 추가
                # indices: [345, 346, 347, 348, 349, 350, 355, 371, 266, 425, 376, 411, 352, 280]
                # 152-376 연결, 411-425 연결 (152가 없으므로 352로 가정)
                filtered_points = points[:-1]  # 280 제외
                
                # 일반 연속 연결
                for i in range(len(filtered_points) - 1):
                    # 425-376 연결 건너뛰기 (인덱스 9->10)
                    if i == 9:  # 425 -> 376 연결 건너뛰기
                        continue
                    # 352-411 연결 건너뛰기 (인덱스 12->11)
                    if i == 11:  # 411 -> 352 연결 건너뛰기
                        continue
                        
                    x1, y1 = filtered_points[i]
                    x2, y2 = filtered_points[i + 1]
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
                
                # 특별 연결들
                if len(filtered_points) > 12:
                    # 352-376 연결
                    x1, y1 = filtered_points[12]  # 352
                    x2, y2 = filtered_points[10]  # 376
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                    
                    # 425-411 연결 추가
                    x1, y1 = filtered_points[9]   # 425
                    x2, y2 = filtered_points[11]  # 411
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 닫힌 다각형 연결
                if len(filtered_points) > 2:
                    x1, y1 = filtered_points[-1]
                    x2, y2 = filtered_points[0]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
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
                # 우측 팔자주름 특별 연결: 360-363, 363-355
                # indices: [355, 371, 266, 436, 432, 422, 424, 418, 405, 291, 391, 278, 360, 321, 363]
                # 363-321 삭제, 360-321 삭제, 360-363 연결, 363-355 연결
                
                # 일반 연속 연결 (특정 연결 제외)
                for i in range(len(points) - 1):
                    # 360-321 연결 건너뛰기 (인덱스 12->13)
                    if i == 12:  # 360 -> 321
                        continue
                    # 363-321 역방향 연결 건너뛰기 (인덱스 14->13)  
                    if i == 13:  # 321 -> 363
                        continue
                        
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
                
                # 특별 연결 추가
                if len(points) > 14:
                    # 360-363 연결 (인덱스 12->14)
                    x1, y1 = points[12]  # 360
                    x2, y2 = points[14]  # 363
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                    
                    # 363-355 연결 (인덱스 14->0)
                    x1, y1 = points[14]  # 363
                    x2, y2 = points[0]   # 355
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                    
            else:
                # 좌측 팔자주름은 일반 연속 연결
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
                        tags="landmarks"
                    )
                
        except Exception as e:
            print(f"코 기둥 선 그리기 오류: {str(e)}")
    
    def _draw_nose_wings_lines(self, points, color, line_width):
        """콧볼 선 그리기 - 기존 연결 유지하며 새 연결 추가"""
        try:
            if len(points) < 4:
                return
            
            # 콧볼 랜드마크: [45, 129, 64, 98, 97, 115, 220, 275, 278, 294, 326, 327, 344, 440]
            # 인덱스:        [0,  1,   2,  3,  4,  5,   6,   7,   8,   9,   10,  11,  12,  13]
            
            # 기존에 건너뛰던 연결들 + 새로 삭제할 연결들:
            # 기존: 115-97 (5->4), 344-327 (12->11), 275-278 (7->8), 45-129 (0->1), 294-326 (9->10)
            # 새로 삭제: 220-275 (6->7), 275-278 (7->8) 확실히 삭제
            skip_connections = [4, 8, 11, 0, 9, 6, 7]  # 다음 인덱스로의 연결을 건너뛸 인덱스들
            
            # 일반 순차 연결 (제외할 연결 건너뛰기)
            for i in range(len(points) - 1):
                if i in skip_connections:
                    continue
                
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=line_width,
                    tags="landmarks"
                )
            
            # 특별 연결들:
            if len(points) > 13:
                # 기존 특별 연결들 유지
                # 97-326 연결 (인덱스 4->10) - 기존 유지
                x1, y1 = points[4]   # 97
                x2, y2 = points[10]  # 326
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 45-275 연결 (인덱스 0->7) - 기존 유지
                x1, y1 = points[0]   # 45
                x2, y2 = points[7]   # 275
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 새로 추가할 연결들
                # 129-115 연결 (인덱스 1->5)
                x1, y1 = points[1]   # 129
                x2, y2 = points[5]   # 115
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 327-294 연결 (인덱스 11->9)
                x1, y1 = points[11]  # 327
                x2, y2 = points[9]   # 294
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 294-278 연결 (인덱스 9->8)
                x1, y1 = points[9]   # 294
                x2, y2 = points[8]   # 278
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 278-344 연결 (인덱스 8->12)
                x1, y1 = points[8]   # 278
                x2, y2 = points[12]  # 344
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 440-275 연결 (인덱스 13->7)
                x1, y1 = points[13]  # 440
                x2, y2 = points[7]   # 275
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
                # 220-45 연결 (인덱스 6->0) - 새로 추가
                x1, y1 = points[6]   # 220
                x2, y2 = points[0]   # 45
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
        except Exception as e:
            print(f"콧볼 선 그리기 오류: {str(e)}")
    
    def _draw_eyelid_lower_surround_area_lines(self, points, color, line_width):
        """하주변영역 선 그리기 - 특별 연결 규칙 적용"""
        try:
            if len(points) < 4:
                return
            
            # 하주변영역 랜드마크 순서:
            # 왼쪽 하꺼풀: [226, 25, 110, 24, 23, 22, 26, 112, 243]  (인덱스 0-8)
            # 왼쪽 하주변: [35, 31, 228, 229, 230, 231, 232, 233, 244]  (인덱스 9-17)
            # 오른쪽 하꺼풀: [463, 341, 256, 252, 253, 254, 339, 255, 446]  (인덱스 18-26)
            # 오른쪽 하주변: [465, 453, 452, 451, 450, 449, 448, 261, 265]  (인덱스 27-35)
            
            # 랜드마크를 딕셔너리로 매핑 (랜드마크 번호 -> 좌표)
            landmark_indices = [
                # 왼쪽 하꺼풀
                226, 25, 110, 24, 23, 22, 26, 112, 243,
                # 왼쪽 하주변  
                35, 31, 228, 229, 230, 231, 232, 233, 244,
                # 오른쪽 하꺼풀
                463, 341, 256, 252, 253, 254, 339, 255, 446,
                # 오른쪽 하주변
                465, 453, 452, 451, 450, 449, 448, 261, 265
            ]
            
            landmark_map = {}
            for i, landmark_num in enumerate(landmark_indices):
                if i < len(points):
                    landmark_map[landmark_num] = points[i]
            
            # 삭제할 연결들을 건너뛰기 위한 set
            skip_connections = {
                (35, 243),   # 35-243 삭제
                (243, 35),   # 역방향도 체크
                (244, 463),  # 244-463 삭제
                (463, 244),  # 역방향도 체크
                (465, 446),  # 465-446 삭제
                (446, 465),  # 역방향도 체크
                (226, 265),  # 226-265 삭제
                (265, 226)   # 역방향도 체크
            }
            
            # 일반 순차 연결 (삭제할 연결 건너뛰기)
            for i in range(len(landmark_indices) - 1):
                if i < len(points) - 1:
                    start_landmark = landmark_indices[i]
                    end_landmark = landmark_indices[i + 1]
                    
                    # 삭제할 연결인지 확인
                    if (start_landmark, end_landmark) in skip_connections:
                        continue
                    
                    if start_landmark in landmark_map and end_landmark in landmark_map:
                        x1, y1 = landmark_map[start_landmark]
                        x2, y2 = landmark_map[end_landmark]
                        
                        self.canvas.create_line(
                            x1, y1, x2, y2,
                            fill=color,
                            width=line_width,
                            tags="landmarks"
                        )
            
            # 특별 연결들 추가
            special_connections = [
                (35, 226),   # 35-226 연결
                (243, 244),  # 243-244 연결
                (465, 463),  # 465-463 연결
                (446, 265)   # 446-265 연결
            ]
            
            for start_landmark, end_landmark in special_connections:
                if start_landmark in landmark_map and end_landmark in landmark_map:
                    x1, y1 = landmark_map[start_landmark]
                    x2, y2 = landmark_map[end_landmark]
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=line_width,
                        tags="landmarks"
                    )
            
            # 닫힌 다각형 연결 (첫 번째와 마지막 연결)
            if len(landmark_indices) > 2 and len(points) > 2:
                first_landmark = landmark_indices[0]
                last_landmark = landmark_indices[-1]
                
                if (last_landmark, first_landmark) not in skip_connections:
                    if first_landmark in landmark_map and last_landmark in landmark_map:
                        x1, y1 = landmark_map[last_landmark]
                        x2, y2 = landmark_map[first_landmark]
                        
                        self.canvas.create_line(
                            x1, y1, x2, y2,
                            fill=color,
                            width=line_width,
                            tags="landmarks"
                        )
                
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
        
        # 스크롤 가능한 프레임 생성 (토글 영역 높이 조정)
        canvas = tk.Canvas(parent_frame, height=300)
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
            
            # 1. 왼쪽 하꺼풀 연속 연결 (인덱스 0-8)
            for i in range(8):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 2. 오른쪽 하꺼풀 연속 연결 (인덱스 9-17)
            for i in range(9, 17):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 3. 왼쪽 눈 하단 연속 연결 (인덱스 18-26)
            for i in range(18, 26):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 4. 오른쪽 눈 하단 연속 연결 (인덱스 27-35)
            for i in range(27, 35):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 5. 특별 연결: 하꺼풀과 눈 하단 연결 (사용자 요청에 따른 수정)
            # 463(인덱스9) - 362(인덱스27) 연결
            if len(points) > 27:
                x1, y1 = points[9]   # 463
                x2, y2 = points[27]  # 362
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 359(인덱스35) - 446(인덱스17) 연결
            if len(points) > 35:
                x1, y1 = points[35]  # 359
                x2, y2 = points[17]  # 446
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 226(인덱스0) - 33(인덱스18) 연결
            if len(points) > 18:
                x1, y1 = points[0]   # 226
                x2, y2 = points[18]  # 33
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 133(인덱스26) - 243(인덱스8) 연결
            if len(points) > 26:
                x1, y1 = points[26]  # 133
                x2, y2 = points[8]   # 243
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
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
            
            # 1. 왼쪽 상꺼풀 연속 연결 (인덱스 0-8)
            for i in range(8):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 2. 왼쪽 상주변 연속 연결 (인덱스 9-17)
            for i in range(9, 17):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 3. 오른쪽 상꺼풀 연속 연결 (인덱스 18-25)
            for i in range(18, 25):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 4. 오른쪽 상주변 연속 연결 (인덱스 26-34)
            for i in range(26, 34):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 5. 특별 연결: 상꺼풀과 상주변 연결
            # 왼쪽: 226(인덱스0) - 35(인덱스9) 연결
            if len(points) > 9:
                x1, y1 = points[0]   # 226
                x2, y2 = points[9]   # 35
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 왼쪽: 243(인덱스8) - 244(인덱스17) 연결
            if len(points) > 17:
                x1, y1 = points[8]   # 243
                x2, y2 = points[17]  # 244
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 오른쪽: 463(인덱스18) - 465(인덱스26) 연결
            if len(points) > 26:
                x1, y1 = points[18]  # 463
                x2, y2 = points[26]  # 465
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 오른쪽: 446(인덱스25) - 265(인덱스34) 연결
            if len(points) > 34:
                x1, y1 = points[25]  # 446
                x2, y2 = points[34]  # 265
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
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
            
            # 1. 왼쪽 상꺼풀 연속 연결 (인덱스 0-8)
            for i in range(8):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 2. 오른쪽 상꺼풀 연속 연결 (인덱스 9-16)
            for i in range(9, 16):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 3. 왼쪽 눈 상단 연속 연결 (인덱스 17-25)
            for i in range(17, 25):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 4. 오른쪽 눈 상단 연속 연결 (인덱스 26-35)
            for i in range(26, 35):
                if i + 1 < len(points):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 5. 특별 연결: 상꺼풀과 눈 상단 연결
            # 왼쪽: 226(인덱스0) - 33(인덱스17) 연결
            if len(points) > 17:
                x1, y1 = points[0]   # 226
                x2, y2 = points[17]  # 33
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 왼쪽: 243(인덱스8) - 133(인덱스25) 연결
            if len(points) > 25:
                x1, y1 = points[8]   # 243
                x2, y2 = points[25]  # 133
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 오른쪽: 463(인덱스9) - 362(인덱스26) 연결
            if len(points) > 26:
                x1, y1 = points[9]   # 463
                x2, y2 = points[26]  # 362
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
            
            # 오른쪽: 446(인덱스16) - 359(인덱스35) 연결
            if len(points) > 35:
                x1, y1 = points[16]  # 446
                x2, y2 = points[35]  # 359
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=line_width, smooth=True, tags="landmarks")
                
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

def main():
    root = tk.Tk()
    app = FaceSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()