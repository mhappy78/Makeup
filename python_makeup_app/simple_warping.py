import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import math

class SimpleWarpingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 간단한 이미지 변형 도구")
        self.root.geometry("1000x700")
        
        # 이미지 관련 변수
        self.original_image = None
        self.current_image = None
        self.display_image = None
        
        # 변형 파라미터
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
        
        # 히스토리 관리 (뒤로가기 기능)
        self.history = []
        self.max_history = 10  # 최대 10개 상태 저장
        
        self.setup_ui()
        
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 좌측 컨트롤 패널
        control_frame = ttk.Frame(main_frame, width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # 제목
        title_label = ttk.Label(control_frame, text="🎨 이미지 변형 도구", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # 파일 로드
        ttk.Button(control_frame, text="📁 이미지 열기", 
                  command=self.load_image).pack(pady=5, fill=tk.X)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        
        # 영향 반경 조절
        ttk.Label(control_frame, text="🎯 영향 반경:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 5))
        self.radius_var = tk.IntVar(value=80)
        radius_frame = ttk.Frame(control_frame)
        radius_frame.pack(fill=tk.X, pady=5)
        
        ttk.Scale(radius_frame, from_=20, to=150, 
                 variable=self.radius_var, orient=tk.HORIZONTAL,
                 command=self.update_radius).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.radius_label = ttk.Label(radius_frame, text="80px", width=6)
        self.radius_label.pack(side=tk.RIGHT)
        
        # 변형 강도 조절
        ttk.Label(control_frame, text="💪 변형 강도:", 
                 font=("Arial", 10, "bold")).pack(pady=(15, 5))
        self.strength_var = tk.DoubleVar(value=1.0)
        strength_frame = ttk.Frame(control_frame)
        strength_frame.pack(fill=tk.X, pady=5)
        
        ttk.Scale(strength_frame, from_=0.1, to=3.0, 
                 variable=self.strength_var, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        strength_value_label = ttk.Label(strength_frame, text="1.0x", width=6)
        strength_value_label.pack(side=tk.RIGHT)
        
        # 강도 레이블 업데이트 함수
        def update_strength_label(*args):
            strength_value_label.config(text=f"{self.strength_var.get():.1f}x")
        self.strength_var.trace('w', update_strength_label)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        
        # 변형 모드 선택
        ttk.Label(control_frame, text="🔧 변형 모드:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        self.warp_mode = tk.StringVar(value="pull")
        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(mode_frame, text="당기기", variable=self.warp_mode, 
                       value="pull").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="밀어내기", variable=self.warp_mode, 
                       value="push").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="확대", variable=self.warp_mode, 
                       value="shrink").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="축소", variable=self.warp_mode, 
                       value="expand").pack(anchor=tk.W)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        
        # 줌 컨트롤
        ttk.Label(control_frame, text="🔍 줌 컨트롤:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        zoom_frame = ttk.Frame(control_frame)
        zoom_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(zoom_frame, text="🔍-", width=6,
                  command=self.zoom_out).pack(side=tk.LEFT, padx=(0, 2))
        
        self.zoom_label = ttk.Label(zoom_frame, text="100%", width=8)
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(zoom_frame, text="🔍+", width=6,
                  command=self.zoom_in).pack(side=tk.LEFT, padx=(2, 0))
        
        # 리셋 버튼
        ttk.Button(control_frame, text="🎯 줌 리셋", 
                  command=self.reset_zoom).pack(pady=5, fill=tk.X)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        
        # 액션 버튼들
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="↶ 뒤로가기", 
                  command=self.undo_last_action).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        ttk.Button(button_frame, text="🔄 원본 복원", 
                  command=self.reset_image).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        ttk.Button(control_frame, text="💾 이미지 저장", 
                  command=self.save_image).pack(pady=5, fill=tk.X)
        
        # 사용법 안내
        instructions_text = """
🖱️ 사용법:
• 좌클릭 후 드래그로 변형
• 우클릭 후 드래그로 이미지 이동
• 마우스 휠로 줌 인/아웃
• 여러 번 적용하여 점진적 변형

💡 팁:
• 작은 반경으로 정밀 작업
• 큰 반경으로 전체적 변형
• 낮은 강도로 자연스러운 효과
• 뒤로가기로 이전 상태 복원
• 줌 인 후 세밀한 작업 가능
        """
        
        instruction_label = ttk.Label(control_frame, text=instructions_text, 
                                    justify=tk.LEFT, wraplength=230,
                                    font=("Arial", 9))
        instruction_label.pack(pady=(20, 0))
        
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
        
        # 줌 및 이동 이벤트
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-3>", self.on_pan_start)  # 우클릭으로 이동 시작
        self.canvas.bind("<B3-Motion>", self.on_pan_drag)  # 우클릭 드래그로 이동
        self.canvas.bind("<ButtonRelease-3>", self.on_pan_end)  # 우클릭 해제
        
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
                
                # 히스토리 초기화 (새 이미지 로드 시)
                self.history = []
                
            except Exception as e:
                print(f"이미지 로드 실패: {str(e)}")
    
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
        """화면에 이미지 업데이트 (줌 및 이동 고려)"""
        if self.current_image is None:
            return
            
        try:
            # 표시용 이미지 리사이징 (줌 고려)
            img_height, img_width = self.current_image.shape[:2]
            display_width = int(img_width * self.scale_factor * self.zoom_factor)
            display_height = int(img_height * self.scale_factor * self.zoom_factor)
            
            display_img = cv2.resize(self.current_image, (display_width, display_height))
            
            # PIL로 변환
            pil_image = Image.fromarray(display_img)
            self.display_image = ImageTk.PhotoImage(pil_image)
            
            # 캔버스에 표시 (이동 고려)
            self.canvas.delete("image")
            self.canvas.create_image(
                self.offset_x + self.pan_x, self.offset_y + self.pan_y, 
                anchor=tk.NW, image=self.display_image, tags="image"
            )
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def screen_to_image_coords(self, screen_x, screen_y):
        """화면 좌표를 이미지 좌표로 변환 (줌 및 이동 고려)"""
        # 줌과 이동을 고려한 좌표 변환
        img_x = ((screen_x - self.offset_x - self.pan_x) / self.scale_factor) / self.zoom_factor
        img_y = ((screen_y - self.offset_y - self.pan_y) / self.scale_factor) / self.zoom_factor
        return int(img_x), int(img_y)
    
    def on_mouse_move(self, event):
        """마우스 이동 이벤트 (영향 범위 표시)"""
        if self.current_image is None or self.is_dragging or self.is_panning:
            return
            
        # 영향 범위 원 표시 (줌 고려)
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
            
        self.start_pos = (event.x, event.y)
        self.is_dragging = True
        
        # 영향 범위 원 표시 (줌 고려)
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
            
        # 방향선 표시
        self.canvas.delete("direction_line")
        self.canvas.create_line(
            self.start_pos[0], self.start_pos[1],
            event.x, event.y,
            fill="#ffc107", width=3, tags="direction_line"
        )
    
    def on_mouse_up(self, event):
        """마우스 업 이벤트 - 변형 적용"""
        if not self.is_dragging or self.start_pos is None:
            return
            
        # 좌표 변환
        start_img_x, start_img_y = self.screen_to_image_coords(self.start_pos[0], self.start_pos[1])
        end_img_x, end_img_y = self.screen_to_image_coords(event.x, event.y)
        
        # 변형 적용 전 현재 상태를 히스토리에 저장
        self.save_to_history()
        
        # 변형 적용
        self.apply_simple_warp(start_img_x, start_img_y, end_img_x, end_img_y)
        
        # 상태 초기화
        self.is_dragging = False
        self.start_pos = None
        
        # 화면 정리 및 업데이트
        self.canvas.delete("warp_circle")
        self.canvas.delete("direction_line")
        self.update_display()
    
    def apply_simple_warp(self, start_x, start_y, end_x, end_y):
        """간단한 변형 적용"""
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
        
        # 드래그 벡터
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
        
        # 변형 강도 계산 (거리에 반비례)
        strength_map = np.zeros_like(pixel_dist)
        valid_dist = pixel_dist[mask]
        
        if len(valid_dist) > 0:
            # 거리에 따른 강도 (중심에서 가장 강함)
            strength_map[mask] = (1 - valid_dist / self.influence_radius) ** 2
            strength_map[mask] *= self.strength_var.get()
            
            # 변형 적용
            map_x[mask] += dx * strength_map[mask]
            map_y[mask] += dy * strength_map[mask]
        
        # 경계 클리핑
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        # 리맵핑 적용
        self.current_image = cv2.remap(
            self.current_image, map_x, map_y, 
            cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT
        )
    
    def apply_pull_warp(self, start_x, start_y, end_x, end_y):
        """당기기 변형 (push의 반대)"""
        # 반대 방향으로 적용
        dx = start_x - end_x
        dy = start_y - end_y
        self.apply_push_warp(start_x, start_y, start_x + dx, start_y + dy)
    
    def apply_radial_warp(self, center_x, center_y, expand=True):
        """방사형 변형 (확대/축소)"""
        img_height, img_width = self.current_image.shape[:2]
        
        # 변형 맵 생성
        map_x = np.arange(img_width, dtype=np.float32).reshape(1, -1)
        map_y = np.arange(img_height, dtype=np.float32).reshape(-1, 1)
        map_x = np.repeat(map_x, img_height, axis=0)
        map_y = np.repeat(map_y, img_width, axis=1)
        
        # 중심점으로부터의 거리와 각도
        dx = map_x - center_x
        dy = map_y - center_y
        distance = np.sqrt(dx*dx + dy*dy)
        
        # 영향받는 영역
        mask = distance < self.influence_radius
        
        # 변형 계수 계산
        strength = self.strength_var.get() * 0.3  # 방사형은 좀 더 약하게
        
        if expand:
            # 확대: 중심에서 멀어지게
            scale_factor = 1 + strength * (1 - distance / self.influence_radius)
        else:
            # 축소: 중심으로 가까워지게
            scale_factor = 1 - strength * (1 - distance / self.influence_radius)
        
        scale_factor = np.maximum(scale_factor, 0.1)  # 최소 스케일 제한
        
        # 새로운 좌표 계산
        new_x = center_x + dx * scale_factor
        new_y = center_y + dy * scale_factor
        
        # 영향받는 영역만 업데이트
        map_x = np.where(mask, new_x, map_x)
        map_y = np.where(mask, new_y, map_y)
        
        # 경계 클리핑
        map_x = np.clip(map_x, 0, img_width - 1)
        map_y = np.clip(map_y, 0, img_height - 1)
        
        # 리맵핑 적용
        self.current_image = cv2.remap(
            self.current_image, map_x, map_y, 
            cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT
        )
    
    def update_radius(self, value):
        """영향 반경 업데이트"""
        self.influence_radius = int(float(value))
        self.radius_label.config(text=f"{self.influence_radius}px")
    
    def save_to_history(self):
        """현재 이미지 상태를 히스토리에 저장"""
        if self.current_image is not None:
            # 현재 이미지를 히스토리에 저장
            self.history.append(self.current_image.copy())
            
            # 히스토리 크기 제한
            if len(self.history) > self.max_history:
                self.history.pop(0)  # 가장 오래된 항목 제거
    
    def undo_last_action(self):
        """마지막 작업 되돌리기"""
        if len(self.history) > 0:
            # 가장 최근 상태로 복원
            self.current_image = self.history.pop()
            self.update_display()
            self.canvas.delete("preview_circle")
        else:
            # 히스토리가 없으면 원본으로 복원
            if self.original_image is not None:
                self.current_image = self.original_image.copy()
                self.update_display()
                self.canvas.delete("preview_circle")
    
    def reset_image(self):
        """원본 이미지로 복원"""
        if self.original_image is not None:
            # 현재 상태를 히스토리에 저장
            self.save_to_history()
            
            self.current_image = self.original_image.copy()
            self.update_display()
            self.canvas.delete("preview_circle")
    
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
                # BGR로 변환하여 저장
                save_image = cv2.cvtColor(self.current_image, cv2.COLOR_RGB2BGR)
                cv2.imwrite(file_path, save_image)
                print(f"이미지 저장 완료: {file_path}")
                
            except Exception as e:
                print(f"이미지 저장 실패: {str(e)}")
    
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
            
        # 줌 인/아웃
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def on_pan_start(self, event):
        """이미지 이동 시작 (우클릭)"""
        if self.current_image is None:
            return
            
        self.is_panning = True
        self.pan_start_pos = (event.x, event.y)
        self.canvas.config(cursor="fleur")  # 이동 커서
    
    def on_pan_drag(self, event):
        """이미지 이동 중 (우클릭 드래그)"""
        if not self.is_panning or self.pan_start_pos is None:
            return
            
        # 이동 거리 계산
        dx = event.x - self.pan_start_pos[0]
        dy = event.y - self.pan_start_pos[1]
        
        # 이동 적용
        self.pan_x += dx
        self.pan_y += dy
        
        # 시작 위치 업데이트
        self.pan_start_pos = (event.x, event.y)
        
        # 화면 업데이트
        self.update_display()
    
    def on_pan_end(self, event):
        """이미지 이동 종료 (우클릭 해제)"""
        self.is_panning = False
        self.pan_start_pos = None
        self.canvas.config(cursor="crosshair")  # 기본 커서로 복원

def main():
    root = tk.Tk()
    app = SimpleWarpingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 