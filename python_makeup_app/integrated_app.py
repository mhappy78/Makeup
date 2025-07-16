import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageDraw
import math
import mediapipe as mp

class IntegratedMakeupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 통합 메이크업 & 이미지 변형 도구")
        self.root.geometry("1400x900")
        
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
        self.eye_effect_strength = 0.0  # 누적 강도 (-는 축소, +는 확대)
        self.eye_effect_positions = None  # 눈 위치 저장
        
        # 코 효과 누적 파라미터
        self.nose_effect_strength = 0.0  # 누적 강도 (-는 축소, +는 확대)
        self.nose_effect_position = None  # 코 위치 저장
        
        # 눈 형태 효과 누적 파라미터
        self.eye_width_strength = 0.0   # 눈 가로 길이 (-는 축소, +는 확대)
        self.eye_height_strength = 0.0  # 눈 세로 길이 (-는 축소, +는 확대)
        self.eye_shape_positions = None  # 눈 위치 저장 (형태 변경용)
        
        # 변형 도구 관련 변수
        self.influence_radius = 80
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
        
        # 히스토리 관리
        self.history = []
        self.max_history = 10
        
        # 메이크업 설정
        self.makeup_opacity = 0.6
        
        self.setup_ui()
        
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 좌측 컨트롤 패널
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # 제목
        title_label = ttk.Label(control_frame, text="🎨 통합 메이크업 도구", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 파일 로드
        ttk.Button(control_frame, text="📁 이미지 열기", 
                  command=self.load_image).pack(pady=5, fill=tk.X)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 탭 노트북
        self.notebook = ttk.Notebook(control_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 메이크업 탭
        self.makeup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.makeup_frame, text="💄 메이크업")
        self.setup_makeup_controls()
        
        # 변형 탭
        self.warp_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.warp_frame, text="🔧 얼굴 변형")
        self.setup_warp_controls()
        
        # 공통 버튼들
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 히스토리 및 리셋 버튼
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="↶ 뒤로가기", 
                  command=self.undo_last_action).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        ttk.Button(button_frame, text="🔄 원본 복원", 
                  command=self.reset_image).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        ttk.Button(control_frame, text="💾 이미지 저장", 
                  command=self.save_image).pack(pady=5, fill=tk.X)
        
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
        
    def setup_makeup_controls(self):
        """메이크업 컨트롤 설정"""
        # 투명도 조절
        ttk.Label(self.makeup_frame, text="✨ 메이크업 강도:", 
                 font=("Arial", 10, "bold")).pack(pady=(10, 5))
        
        opacity_frame = ttk.Frame(self.makeup_frame)
        opacity_frame.pack(fill=tk.X, pady=5)
        
        self.opacity_var = tk.DoubleVar(value=0.6)
        ttk.Scale(opacity_frame, from_=0.1, to=1.0, 
                 variable=self.opacity_var, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        opacity_label = ttk.Label(opacity_frame, text="60%", width=6)
        opacity_label.pack(side=tk.RIGHT)
        
        def update_opacity_label(*args):
            opacity_label.config(text=f"{int(self.opacity_var.get()*100)}%")
            self.makeup_opacity = self.opacity_var.get()
        self.opacity_var.trace('w', update_opacity_label)
        
        # 구분선
        ttk.Separator(self.makeup_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 립스틱 효과
        ttk.Label(self.makeup_frame, text="💋 립스틱:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        lipstick_frame = ttk.Frame(self.makeup_frame)
        lipstick_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(lipstick_frame, text="빨간 립스틱", 
                  command=self.apply_red_lipstick).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(lipstick_frame, text="핑크 립스틱", 
                  command=self.apply_pink_lipstick).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 아이섀도 효과
        ttk.Label(self.makeup_frame, text="👁️ 아이섀도:", 
                 font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        eyeshadow_frame = ttk.Frame(self.makeup_frame)
        eyeshadow_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(eyeshadow_frame, text="보라 아이섀도", 
                  command=self.apply_purple_eyeshadow).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(eyeshadow_frame, text="갈색 아이섀도", 
                  command=self.apply_brown_eyeshadow).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 눈 확대
        ttk.Label(self.makeup_frame, text="👀 눈 효과:", 
                 font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        ttk.Button(self.makeup_frame, text="눈 크게 하기", 
                  command=lambda: self.adjust_eyes(expand=True)).pack(pady=5, fill=tk.X)
        
        ttk.Button(self.makeup_frame, text="눈 작게 하기", 
                  command=lambda: self.adjust_eyes(expand=False)).pack(pady=5, fill=tk.X)
        
        # 눈 효과 상태 표시
        self.eye_status_label = ttk.Label(self.makeup_frame, text="눈 효과: 0.0", 
                                         foreground="gray", font=("Arial", 9))
        self.eye_status_label.pack(pady=5)
        
        # 눈 효과 리셋 버튼
        ttk.Button(self.makeup_frame, text="👁️ 눈 효과 리셋", 
                  command=self.reset_eye_effect).pack(pady=5, fill=tk.X)
        
        # 눈 형태 조절
        ttk.Label(self.makeup_frame, text="👀 눈 형태 조절:", 
                 font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        # 눈 가로 길이 조절
        ttk.Label(self.makeup_frame, text="↔️ 가로 길이:", 
                 font=("Arial", 9)).pack(pady=(5, 2))
        
        width_frame = ttk.Frame(self.makeup_frame)
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
        
        self.eye_width_label = ttk.Label(self.makeup_frame, text="가로: 0.0", 
                                        foreground="gray", font=("Arial", 8))
        self.eye_width_label.pack()
        
        # 눈 세로 길이 조절
        ttk.Label(self.makeup_frame, text="↕️ 세로 길이:", 
                 font=("Arial", 9)).pack(pady=(5, 2))
        
        height_frame = ttk.Frame(self.makeup_frame)
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
        
        self.eye_height_label = ttk.Label(self.makeup_frame, text="세로: 0.0", 
                                         foreground="gray", font=("Arial", 8))
        self.eye_height_label.pack()
        
        # 눈 형태 리셋 버튼
        ttk.Button(self.makeup_frame, text="👀 눈 형태 리셋", 
                  command=self.reset_eye_shape).pack(pady=5, fill=tk.X)
        
        # 코 효과
        ttk.Label(self.makeup_frame, text="👃 코 효과:", 
                 font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        ttk.Button(self.makeup_frame, text="코 크게 하기", 
                  command=lambda: self.adjust_nose(expand=True)).pack(pady=5, fill=tk.X)
        
        ttk.Button(self.makeup_frame, text="코 작게 하기", 
                  command=lambda: self.adjust_nose(expand=False)).pack(pady=5, fill=tk.X)
        
        # 코 효과 상태 표시
        self.nose_status_label = ttk.Label(self.makeup_frame, text="코 효과: 0.0", 
                                          foreground="gray", font=("Arial", 9))
        self.nose_status_label.pack(pady=5)
        
        # 코 효과 리셋 버튼
        ttk.Button(self.makeup_frame, text="👃 코 효과 리셋", 
                  command=self.reset_nose_effect).pack(pady=5, fill=tk.X)
        
        # 얼굴 검출 상태
        ttk.Separator(self.makeup_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        self.face_status_label = ttk.Label(self.makeup_frame, text="얼굴을 검출하세요", 
                                          foreground="gray")
        self.face_status_label.pack(pady=5)
        
    def setup_warp_controls(self):
        """변형 도구 컨트롤 설정"""
        # 영향 반경 조절
        ttk.Label(self.warp_frame, text="🎯 영향 반경:", 
                 font=("Arial", 10, "bold")).pack(pady=(10, 5))
        
        radius_frame = ttk.Frame(self.warp_frame)
        radius_frame.pack(fill=tk.X, pady=5)
        
        self.radius_var = tk.IntVar(value=80)
        ttk.Scale(radius_frame, from_=20, to=150, 
                 variable=self.radius_var, orient=tk.HORIZONTAL,
                 command=self.update_radius).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.radius_label = ttk.Label(radius_frame, text="80px", width=6)
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
• 메이크업 후 변형 적용 권장
• 줌 인 후 세밀한 작업 가능
• 뒤로가기로 이전 상태 복원
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
                
                # 눈 효과 누적 파라미터 초기화
                self.eye_effect_strength = 0.0
                self.eye_effect_positions = None
                
                # 코 효과 누적 파라미터 초기화
                self.nose_effect_strength = 0.0
                self.nose_effect_position = None
                
                # 눈 형태 효과 누적 파라미터 초기화
                self.eye_width_strength = 0.0
                self.eye_height_strength = 0.0
                self.eye_shape_positions = None
                
                # 얼굴 검출
                self.detect_face()
                
                # UI 상태 업데이트
                if hasattr(self, 'eye_status_label'):
                    self.eye_status_label.config(text="눈 효과: 0.0 (원본)", foreground="gray")
                if hasattr(self, 'nose_status_label'):
                    self.nose_status_label.config(text="코 효과: 0.0 (원본)", foreground="gray")
                if hasattr(self, 'eye_width_label'):
                    self.eye_width_label.config(text="가로: 0.0 (원본)", foreground="gray")
                if hasattr(self, 'eye_height_label'):
                    self.eye_height_label.config(text="세로: 0.0 (원본)", foreground="gray")
                if hasattr(self, 'eye_width_var'):
                    self.eye_width_var.set(0.0)
                if hasattr(self, 'eye_height_var'):
                    self.eye_height_var.set(0.0)
                
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
            
        except Exception as e:
            print(f"Display error: {e}")
    
    # 메이크업 관련 메서드들
    def apply_red_lipstick(self):
        """빨간 립스틱 적용"""
        self.apply_lipstick((220, 20, 60))  # 빨간색
    
    def apply_pink_lipstick(self):
        """핑크 립스틱 적용"""
        self.apply_lipstick((255, 20, 147))  # 핑크색
    
    def apply_lipstick(self, color):
        """립스틱 효과 적용"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        self.save_to_history()
        
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            # 입술 특징점 (MediaPipe 기준) - makeup_app.py와 동일하게 변경
            lip_indices = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
            
            # 입술 좌표 추출
            lip_points = []
            for idx in lip_indices:
                landmark = self.face_landmarks.landmark[idx]
                x = int(landmark.x * img_width)
                y = int(landmark.y * img_height)
                lip_points.append((x, y))
            
            # PIL을 사용한 립스틱 적용
            pil_image = Image.fromarray(self.current_image)
            overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # 입술 영역에 색상 적용
            if len(lip_points) > 3:
                draw.polygon(lip_points, fill=(*color, int(255 * self.makeup_opacity)))
            
            # 블렌딩
            pil_image = pil_image.convert('RGBA')
            blended = Image.alpha_composite(pil_image, overlay)
            self.current_image = np.array(blended.convert('RGB'))
            
            self.update_display()
            
        except Exception as e:
            print(f"립스틱 적용 실패: {str(e)}")
    
    def apply_purple_eyeshadow(self):
        """보라색 아이섀도 적용"""
        self.apply_eyeshadow((128, 0, 128))  # 보라색
    
    def apply_brown_eyeshadow(self):
        """갈색 아이섀도 적용"""
        self.apply_eyeshadow((139, 69, 19))  # 갈색
    
    def apply_eyeshadow(self, color):
        """아이섀도 효과 적용"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        self.save_to_history()
        
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            # 눈 주변 특징점 - makeup_app.py와 동일하게 변경
            left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158]
            right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387]
            
            def apply_eye_shadow(eye_indices):
                eye_points = []
                for idx in eye_indices:
                    landmark = self.face_landmarks.landmark[idx]
                    x = int(landmark.x * img_width)
                    y = int(landmark.y * img_height)
                    eye_points.append((x, y))
                
                if len(eye_points) >= 3:
                    # PIL을 사용한 아이섀도 적용 - makeup_app.py 방식으로 변경
                    pil_image = Image.fromarray(self.current_image)
                    overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(overlay)
                    
                    # 바운딩 박스 계산하여 ellipse로 그리기
                    x_coords = [p[0] for p in eye_points]
                    y_coords = [p[1] for p in eye_points]
                    
                    left = min(x_coords) - 10
                    right = max(x_coords) + 10
                    top = min(y_coords) - 15
                    bottom = max(y_coords) + 5
                    
                    draw.ellipse([left, top, right, bottom], fill=(*color, int(255 * self.makeup_opacity * 0.3)))
                    
                    # 그라데이션 효과를 위한 블러
                    from PIL import ImageFilter
                    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=8))
                    
                    # 블렌딩
                    pil_image = pil_image.convert('RGBA')
                    blended = Image.alpha_composite(pil_image, overlay)
                    return np.array(blended.convert('RGB'))
                
                return self.current_image
            
            # 양쪽 눈에 아이섀도 적용
            self.current_image = apply_eye_shadow(left_eye_indices)
            self.current_image = apply_eye_shadow(right_eye_indices)
            
            self.update_display()
            
        except Exception as e:
            print(f"아이섀도 적용 실패: {str(e)}")
    
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
                print(f"눈 확대: 현재 강도 {self.eye_effect_strength:.1f}")
            else:
                self.eye_effect_strength -= step
                print(f"눈 축소: 현재 강도 {self.eye_effect_strength:.1f}")
            
            # 강도 제한 (-1.0 ~ 1.0)
            self.eye_effect_strength = max(-1.0, min(1.0, self.eye_effect_strength))
            
            # 원본 이미지에서 누적된 효과 적용
            if abs(self.eye_effect_strength) > 0.01:  # 효과가 있을 때만
                # 메이크업이 적용된 기준 이미지 찾기
                if len(self.history) > 0:
                    base_image = self.history[-1].copy()  # 마지막 히스토리 (메이크업 적용 상태)
                else:
                    base_image = self.original_image.copy()
                
                # 양쪽 눈에 누적 효과 적용
                result_image = base_image.copy()
                for eye_center in self.eye_effect_positions:
                    if self.eye_effect_strength > 0:  # 확대
                        result_image = self.magnify_area(
                            result_image, eye_center, radius=40, 
                            strength=abs(self.eye_effect_strength), expand=True
                        )
                    else:  # 축소
                        result_image = self.magnify_area(
                            result_image, eye_center, radius=40, 
                            strength=abs(self.eye_effect_strength), expand=False
                        )
                
                self.current_image = result_image
            else:
                # 효과가 없으면 기준 이미지로 복원
                if len(self.history) > 0:
                    self.current_image = self.history[-1].copy()
                else:
                    self.current_image = self.original_image.copy()
            
            self.update_display()
            
            # UI 상태 업데이트
            if self.eye_effect_strength > 0:
                self.eye_status_label.config(text=f"눈 효과: +{self.eye_effect_strength:.1f} (확대)", 
                                           foreground="blue")
            elif self.eye_effect_strength < 0:
                self.eye_status_label.config(text=f"눈 효과: {self.eye_effect_strength:.1f} (축소)", 
                                           foreground="red")
            else:
                self.eye_status_label.config(text="눈 효과: 0.0 (원본)", 
                                           foreground="gray")
            
        except Exception as e:
            print(f"눈 효과 적용 실패: {str(e)}")
    
    def magnify_area(self, image, center, radius=40, strength=0.1, expand=True):
        print("magnify_area", expand)
        """특정 영역 확대"""
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
    
    # 변형 도구 관련 메서드들 (simple_warping.py에서 가져옴)
    def screen_to_image_coords(self, screen_x, screen_y):
        """화면 좌표를 이미지 좌표로 변환"""
        img_x = ((screen_x - self.offset_x - self.pan_x) / self.scale_factor) / self.zoom_factor
        img_y = ((screen_y - self.offset_y - self.pan_y) / self.scale_factor) / self.zoom_factor
        return int(img_x), int(img_y)
    
    def on_mouse_move(self, event):
        """마우스 이동 이벤트"""
        if self.current_image is None or self.is_dragging or self.is_panning:
            return
        
        # 변형 탭이 활성화된 경우에만 영향 범위 표시
        if self.notebook.index(self.notebook.select()) == 1:  # 변형 탭
            self.canvas.delete("preview_circle")
            radius_screen = self.influence_radius * self.scale_factor * self.zoom_factor
            
            self.canvas.create_oval(
                event.x - radius_screen, event.y - radius_screen,
                event.x + radius_screen, event.y + radius_screen,
                outline="#ff6b6b", width=2, dash=(5, 5), tags="preview_circle"
            )
    
    def on_mouse_down(self, event):
        """마우스 다운 이벤트"""
        if self.current_image is None:
            return
        
        # 변형 탭이 활성화된 경우에만 변형 모드
        if self.notebook.index(self.notebook.select()) == 1:  # 변형 탭
            self.start_pos = (event.x, event.y)
            self.is_dragging = True
            
            self.canvas.delete("preview_circle")
            radius_screen = self.influence_radius * self.scale_factor * self.zoom_factor
            
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
        
        # 변형 적용 전 현재 상태를 히스토리에 저장
        self.save_to_history()
        
        # 좌표 변환
        start_img_x, start_img_y = self.screen_to_image_coords(self.start_pos[0], self.start_pos[1])
        end_img_x, end_img_y = self.screen_to_image_coords(event.x, event.y)
        
        # 변형 적용
        self.apply_warp(start_img_x, start_img_y, end_img_x, end_img_y)
        
        # 상태 초기화
        self.is_dragging = False
        self.start_pos = None
        
        # 화면 정리 및 업데이트
        self.canvas.delete("warp_circle")
        self.canvas.delete("direction_line")
        self.update_display()
    
    def apply_warp(self, start_x, start_y, end_x, end_y):
        """변형 적용"""
        if self.current_image is None:
            return
            
        img_height, img_width = self.current_image.shape[:2]
        
        # 경계 검사
        start_x = max(0, min(start_x, img_width - 1))
        start_y = max(0, min(start_y, img_height - 1))
        end_x = max(0, min(end_x, img_width - 1))
        end_y = max(0, min(end_y, img_height - 1))
        
        # 변형 모드에 따른 처리
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
        
        # 변형 맵 생성
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        # 각 픽셀에서 시작점까지의 거리 계산
        pixel_dx = map_x - start_x
        pixel_dy = map_y - start_y
        pixel_dist = np.sqrt(pixel_dx*pixel_dx + pixel_dy*pixel_dy)
        
        # 영향받는 영역 마스크
        mask = pixel_dist < self.influence_radius
        
        # 변형 강도 계산
        strength_map = np.zeros_like(pixel_dist)
        valid_dist = pixel_dist[mask]
        
        if len(valid_dist) > 0:
            strength_map[mask] = (1 - valid_dist / self.influence_radius) ** 2
            strength_map[mask] *= self.strength_var.get()
            
            # 변형 적용
            map_x[mask] += dx * strength_map[mask]
            map_y[mask] += dy * strength_map[mask]
        
        # 경계 클리핑
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        # 리맵핑 적용 - 고품질 보간 사용
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
        
        # 변형 맵 생성
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        # 중심점으로부터의 거리
        dx = map_x - center_x
        dy = map_y - center_y
        distance = np.sqrt(dx*dx + dy*dy)
        
        # 영향받는 영역
        mask = distance < self.influence_radius
        
        # 변형 계수 계산
        strength = self.strength_var.get() * 0.3
        
        if expand:
            scale_factor = 1 - strength * (1 - distance / self.influence_radius)
        else:
            scale_factor = 1 + strength * (1 - distance / self.influence_radius)
        
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
        self.current_image = cv2.remap(
            self.current_image, map_x, map_y, 
            cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
        )
    
    # 줌 및 이동 관련 메서드들
    def zoom_in(self):
        """줌 인"""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor *= 1.2
            self.update_display()
            self.update_zoom_label()
    
    def zoom_out(self):
        """줌 아웃"""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor /= 1.2
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
    
    def on_mouse_wheel(self, event):
        """마우스 휠 줌"""
        if self.current_image is None:
            return
            
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
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
    def update_radius(self, value):
        """영향 반경 업데이트"""
        self.influence_radius = int(float(value))
        self.radius_label.config(text=f"{self.influence_radius}px")
    
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
            
            # 얼굴 재검출
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
            
            # 눈 효과 누적 파라미터 초기화
            self.eye_effect_strength = 0.0
            self.eye_effect_positions = None
            
            # 코 효과 누적 파라미터 초기화
            self.nose_effect_strength = 0.0
            self.nose_effect_position = None
            
            # 눈 형태 효과 누적 파라미터 초기화
            self.eye_width_strength = 0.0
            self.eye_height_strength = 0.0
            self.eye_shape_positions = None
            
            self.update_display()
            self.canvas.delete("preview_circle")
            
            # 얼굴 재검출
            self.detect_face()
            
            # UI 상태 업데이트
            if hasattr(self, 'eye_status_label'):
                self.eye_status_label.config(text="눈 효과: 0.0 (원본)", foreground="gray")
            if hasattr(self, 'nose_status_label'):
                self.nose_status_label.config(text="코 효과: 0.0 (원본)", foreground="gray")
            if hasattr(self, 'eye_width_label'):
                self.eye_width_label.config(text="가로: 0.0 (원본)", foreground="gray")
            if hasattr(self, 'eye_height_label'):
                self.eye_height_label.config(text="세로: 0.0 (원본)", foreground="gray")
            if hasattr(self, 'eye_width_var'):
                self.eye_width_var.set(0.0)
            if hasattr(self, 'eye_height_var'):
                self.eye_height_var.set(0.0)
    
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

    def reset_eye_effect(self):
        """눈 효과 리셋"""
        if self.eye_effect_strength != 0.0:
            self.save_to_history()
            
        self.eye_effect_strength = 0.0
        self.eye_effect_positions = None
        
        # 메이크업이 적용된 기준 이미지로 복원
        if len(self.history) > 0 and self.eye_effect_strength == 0.0:
            self.current_image = self.history[-1].copy()  # 마지막 메이크업 상태
        else:
            self.current_image = self.original_image.copy()
            
        self.update_display()
        self.eye_status_label.config(text="눈 효과: 0.0 (원본)", foreground="gray")
        print("눈 효과가 리셋되었습니다.")

    def adjust_nose(self, expand=True):
        """코 확대/축소 효과 - 누적 방식으로 화질 보존"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        # 첫 번째 호출시에만 히스토리 저장
        if self.nose_effect_strength == 0.0:
            self.save_to_history()
        
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            # 코 위치 저장 (첫 번째 호출시에만)
            if self.nose_effect_position is None:
                # MediaPipe 코 랜드마크: 코끝(1), 코 중앙(2)
                nose_tip = self.face_landmarks.landmark[1]  # 코끝
                nose_center = self.face_landmarks.landmark[2]  # 코 중앙
                
                # 코의 중심점 계산
                nose_x = int((nose_tip.x + nose_center.x) / 2 * img_width)
                nose_y = int((nose_tip.y + nose_center.y)*0.94 / 2 * img_height)
                print("nose_tip.y, nose_center.y, nose_tip.x, nose_center.x", nose_tip.y, nose_center.y, nose_tip.x, nose_center.x)
                
                self.nose_effect_position = (nose_x, nose_y)
            
            # 누적 강도 업데이트
            step = 0.1
            if expand:
                self.nose_effect_strength += step
                print(f"코 확대: 현재 강도 {self.nose_effect_strength:.1f}")
            else:
                self.nose_effect_strength -= step
                print(f"코 축소: 현재 강도 {self.nose_effect_strength:.1f}")
            
            # 강도 제한 (-1.0 ~ 1.0)
            self.nose_effect_strength = max(-1.0, min(1.0, self.nose_effect_strength))
            
            # 원본 이미지에서 누적된 효과 적용
            if abs(self.nose_effect_strength) > 0.01:  # 효과가 있을 때만
                # 메이크업이 적용된 기준 이미지 찾기
                if len(self.history) > 0:
                    base_image = self.history[-1].copy()  # 마지막 히스토리 (메이크업 적용 상태)
                else:
                    base_image = self.original_image.copy()
                
                # 코에 누적 효과 적용
                result_image = base_image.copy()
                if self.nose_effect_strength > 0:  # 확대
                    result_image = self.magnify_area(
                        result_image, self.nose_effect_position, radius=60, 
                        strength=abs(self.nose_effect_strength), expand=True
                    )
                else:  # 축소
                    result_image = self.magnify_area(
                        result_image, self.nose_effect_position, radius=60, 
                        strength=abs(self.nose_effect_strength), expand=False
                    )
                
                self.current_image = result_image
            else:
                # 효과가 없으면 기준 이미지로 복원
                if len(self.history) > 0:
                    self.current_image = self.history[-1].copy()
                else:
                    self.current_image = self.original_image.copy()
            
            self.update_display()
            
            # UI 상태 업데이트
            if self.nose_effect_strength > 0:
                self.nose_status_label.config(text=f"코 효과: +{self.nose_effect_strength:.1f} (확대)", 
                                            foreground="blue")
            elif self.nose_effect_strength < 0:
                self.nose_status_label.config(text=f"코 효과: {self.nose_effect_strength:.1f} (축소)", 
                                            foreground="red")
            else:
                self.nose_status_label.config(text="코 효과: 0.0 (원본)", 
                                            foreground="gray")
            
        except Exception as e:
            print(f"코 효과 적용 실패: {str(e)}")
    
    def reset_nose_effect(self):
        """코 효과 리셋"""
        if self.nose_effect_strength != 0.0:
            self.save_to_history()
            
        self.nose_effect_strength = 0.0
        self.nose_effect_position = None
        
        # 메이크업이 적용된 기준 이미지로 복원
        if len(self.history) > 0 and self.nose_effect_strength == 0.0:
            self.current_image = self.history[-1].copy()  # 마지막 메이크업 상태
        else:
            self.current_image = self.original_image.copy()
            
        self.update_display()
        self.nose_status_label.config(text="코 효과: 0.0 (원본)", foreground="gray")
        print("코 효과가 리셋되었습니다.")

    def adjust_eye_width(self, value):
        """눈 가로 길이 조절"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        # 첫 번째 호출시에만 히스토리 저장
        if self.eye_width_strength == 0.0 and value != 0.0:
            self.save_to_history()
            
        old_value = self.eye_width_strength
        self.eye_width_strength += value
        self.eye_width_strength = max(-1.0, min(1.0, self.eye_width_strength))
        
        # 값이 실제로 변경되었을 때만 적용
        if abs(self.eye_width_strength - old_value) > 0.01:
            self.apply_eye_shape_effects()
            self.update_eye_shape_labels()
            print(f"눈 가로 길이 조절: {self.eye_width_strength:.1f}")
    
    def adjust_eye_height(self, value):
        """눈 세로 길이 조절"""
        if self.face_landmarks is None:
            print("얼굴이 검출되지 않았습니다.")
            return
        
        # 첫 번째 호출시에만 히스토리 저장
        if self.eye_height_strength == 0.0 and value != 0.0:
            self.save_to_history()
            
        old_value = self.eye_height_strength
        self.eye_height_strength += value
        self.eye_height_strength = max(-1.0, min(1.0, self.eye_height_strength))
        
        # 값이 실제로 변경되었을 때만 적용
        if abs(self.eye_height_strength - old_value) > 0.01:
            self.apply_eye_shape_effects()
            self.update_eye_shape_labels()
            print(f"눈 세로 길이 조절: {self.eye_height_strength:.1f}")
    
    def reset_eye_shape(self):
        """눈 형태 리셋"""
        if self.eye_width_strength != 0.0 or self.eye_height_strength != 0.0:
            self.save_to_history()
            
        self.eye_width_strength = 0.0
        self.eye_height_strength = 0.0
        self.eye_shape_positions = None
        
        # 기준 이미지로 복원
        if len(self.history) > 0:
            self.current_image = self.history[-1].copy()
        else:
            self.current_image = self.original_image.copy()
            
        self.update_display()
        self.update_eye_shape_labels()
        print("눈 형태가 리셋되었습니다.")

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
            
            # 눈 위치 저장 (첫 번째 호출시에만)
            if self.eye_shape_positions is None:
                left_eye_center_top = self.face_landmarks.landmark[159]  # 왼쪽 눈 위
                left_eye_center_bottom = self.face_landmarks.landmark[145]  # 왼쪽 눈 아래
                
                right_eye_center_top = self.face_landmarks.landmark[386]  # 오른쪽 눈 위
                right_eye_center_bottom = self.face_landmarks.landmark[374]  # 오른쪽 눈 아래
                
                self.eye_shape_positions = [
                    (int((left_eye_center_top.x + left_eye_center_bottom.x) / 2 * img_width ), int((left_eye_center_top.y + left_eye_center_bottom.y) / 2 * img_height)),
                    (int((right_eye_center_top.x + right_eye_center_bottom.x) / 2 * img_width ), int((right_eye_center_top.y + right_eye_center_bottom.y) / 2 * img_height)),
                ]
            
            # 기준 이미지 선택
            if len(self.history) > 0:
                base_image = self.history[-1].copy()
            else:
                base_image = self.original_image.copy()
            
            # 눈 형태 효과 적용
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
    
    def elliptical_warp_natural(self, image, eye_center, width_strength=0.0, height_strength=0.0, eye_landmarks=None):
        """자연스러운 눈 형태 변형 - 가로는 양끝 당기기, 세로는 기존 방식"""
        img_height, img_width = image.shape[:2]
        center_x, center_y = eye_center
        
        # 디버깅 정보
        print(f"자연스러운 눈 변형 - 위치: ({center_x}, {center_y}), 가로: {width_strength:.2f}, 세로: {height_strength:.2f}")
        
        result_image = image.copy()
        
        # 가로 방향 변형 - 양끝 당기기 방식
        if width_strength != 0.0:
            # 현재 눈이 왼쪽인지 오른쪽인지 판단 (이미지 중앙 기준)
            is_left_eye = center_x < img_width / 2
            
            # 눈의 양끝 랜드마크 계산
            if is_left_eye:
                # 왼쪽 눈: 외측(33), 내측(133)
                if self.face_landmarks:
                    outer_landmark = self.face_landmarks.landmark[33]
                    inner_landmark = self.face_landmarks.landmark[133]
                    outer_pos = (int(outer_landmark.x * img_width), int(outer_landmark.y * img_height))
                    inner_pos = (int(inner_landmark.x * img_width), int(inner_landmark.y * img_height))
                else:
                    # 기본값으로 추정
                    outer_pos = (center_x - 25, center_y)
                    inner_pos = (center_x + 15, center_y)
            else:
                # 오른쪽 눈: 외측(263), 내측(362)
                if self.face_landmarks:
                    outer_landmark = self.face_landmarks.landmark[263]
                    inner_landmark = self.face_landmarks.landmark[362]
                    outer_pos = (int(outer_landmark.x * img_width), int(outer_landmark.y * img_height))
                    inner_pos = (int(inner_landmark.x * img_width), int(inner_landmark.y * img_height))
                else:
                    # 기본값으로 추정
                    outer_pos = (center_x + 25, center_y)
                    inner_pos = (center_x - 15, center_y)
            
            # 당기기 변형 적용
            result_image = self.apply_eye_width_pull_warp(result_image, outer_pos, inner_pos, 
                                                         width_strength, is_left_eye)
        
        # 세로 방향 변형 - 기존 방식 유지
        if height_strength != 0.0:
            result_image = self.apply_eye_height_warp(result_image, eye_center, height_strength)
        
        return result_image
    
    def apply_eye_width_pull_warp(self, image, outer_pos, inner_pos, width_strength, is_left_eye):
        """눈 가로 길이 조절 - 양끝 당기기 방식"""
        img_height, img_width = image.shape[:2]
        
        # 당기기 거리 계산
        pull_distance = abs(width_strength) * 10  # 최대 10픽셀 이동
        
        if width_strength > 0:  # 가로 확대 - 외측을 더 바깥으로
            if is_left_eye:
                # 왼쪽 눈: 외측을 더 왼쪽으로
                start_pos = outer_pos
                end_pos = (max(0, outer_pos[0] - pull_distance), outer_pos[1])
            else:
                # 오른쪽 눈: 외측을 더 오른쪽으로
                start_pos = outer_pos
                end_pos = (min(img_width-1, outer_pos[0] + pull_distance), outer_pos[1])
        else:  # 가로 축소 - 외측을 안쪽으로
            if is_left_eye:
                # 왼쪽 눈: 내측을 안쪽으로
                start_pos = outer_pos
                end_pos = (min(img_width-1, outer_pos[0] + pull_distance), outer_pos[1])
            else:
                # 오른쪽 눈: 내측을 안쪽으로
                start_pos = outer_pos
                end_pos = (max(0, outer_pos[0] - pull_distance), outer_pos[1])
        
        # 당기기 변형 적용
        temp_image = image.copy()
        self.current_image = temp_image
        
        # 임시 파라미터 설정
        original_radius = self.influence_radius
        self.influence_radius = 25  # 작은 반경으로 정밀 변형
        
        # 당기기 변형 적용
        self.apply_pull_warp_with_params(start_pos[0], start_pos[1], end_pos[0], end_pos[1], 
                                       min(abs(width_strength) * 2.0, 3.0))
        
        result = self.current_image.copy()
        
        # 원래 파라미터 복원
        self.influence_radius = original_radius
        
        return result
    
    def apply_eye_height_warp(self, image, eye_center, height_strength):
        """눈 세로 길이 조절 - 기존 방식 유지"""
        img_height, img_width = image.shape[:2]
        center_x, center_y = eye_center
        
        # 변형 맵 생성
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        # 중심점으로부터의 거리
        dx = map_x - center_x
        dy = map_y - center_y
        distance = np.sqrt(dx*dx + dy*dy)
        
        # 전체 영향 반경 (눈 크기에 맞게 조정)
        radius = 50
        mask = distance < radius
        
        # 눈동자 보호 영역 (중심에서 18픽셀 반경)
        pupil_radius = 18
        pupil_mask = distance < pupil_radius
        
        # 세로 방향 변형
        strength_map_y = np.zeros_like(distance)
        valid_dist = distance[mask]
        
        if len(valid_dist) > 0:
            strength_map_y[mask] = (1 - valid_dist / radius) ** 1.2
            
            # 눈동자 영역은 변형 강도 크게 줄이기
            strength_map_y[pupil_mask] *= 0.2
            strength_map_y *= abs(height_strength)
            
            if height_strength > 0:  # 세로 확대
                scale_factor_y = 1 - strength_map_y
            else:  # 세로 축소
                scale_factor_y = 1 + strength_map_y
            
            new_y = center_y + dy * scale_factor_y
            map_y = np.where(mask, new_y, map_y)
        
        # 경계 클리핑
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        # 리맵핑 적용 - 고품질 보간 사용
        return cv2.remap(image, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    
    def apply_pull_warp_with_params(self, start_x, start_y, end_x, end_y, strength):
        """파라미터를 지정한 당기기 변형"""
        if self.current_image is None:
            return
            
        img_height, img_width = self.current_image.shape[:2]
        
        # 경계 검사
        start_x = max(0, min(start_x, img_width - 1))
        start_y = max(0, min(start_y, img_height - 1))
        end_x = max(0, min(end_x, img_width - 1))
        end_y = max(0, min(end_y, img_height - 1))
        
        dx = start_x - end_x
        dy = start_y - end_y
        
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return
        
        # 변형 맵 생성
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        # 각 픽셀에서 시작점까지의 거리 계산
        pixel_dx = map_x - start_x
        pixel_dy = map_y - start_y
        pixel_dist = np.sqrt(pixel_dx*pixel_dx + pixel_dy*pixel_dy)
        
        # 영향받는 영역 마스크
        mask = pixel_dist < self.influence_radius
        
        # 변형 강도 계산
        strength_map = np.zeros_like(pixel_dist)
        valid_dist = pixel_dist[mask]
        
        if len(valid_dist) > 0:
            strength_map[mask] = (1 - valid_dist / self.influence_radius) ** 2
            strength_map[mask] *= strength
            
            # 변형 적용
            map_x[mask] += dx * strength_map[mask]
            map_y[mask] += dy * strength_map[mask]
        
        # 경계 클리핑
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        # 리맵핑 적용 - 고품질 보간 사용
        self.current_image = cv2.remap(
            self.current_image, map_x, map_y, 
            cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
        )
    
    def update_eye_shape_labels(self):
        """눈 형태 라벨 업데이트"""
        # 가로 라벨 업데이트
        if self.eye_width_strength > 0:
            self.eye_width_label.config(text=f"가로: +{self.eye_width_strength:.1f} (확대)", foreground="blue")
        elif self.eye_width_strength < 0:
            self.eye_width_label.config(text=f"가로: {self.eye_width_strength:.1f} (축소)", foreground="red")
        else:
            self.eye_width_label.config(text="가로: 0.0 (원본)", foreground="gray")
        
        # 세로 라벨 업데이트
        if self.eye_height_strength > 0:
            self.eye_height_label.config(text=f"세로: +{self.eye_height_strength:.1f} (확대)", foreground="blue")
        elif self.eye_height_strength < 0:
            self.eye_height_label.config(text=f"세로: {self.eye_height_strength:.1f} (축소)", foreground="red")
        else:
            self.eye_height_label.config(text="세로: 0.0 (원본)", foreground="gray")
        
        # 슬라이더 값 동기화
        self.eye_width_var.set(self.eye_width_strength)
        self.eye_height_var.set(self.eye_height_strength)

def main():
    root = tk.Tk()
    app = IntegratedMakeupApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 