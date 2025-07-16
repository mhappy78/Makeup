import cv2
import numpy as np
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFilter
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageTk
import os

class FaceLandmarkDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
    
    def get_face_landmarks(self, image):
        """얼굴 랜드마크 검출"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            return self.convert_landmarks_to_points(landmarks, image.shape)
        return None
    
    def convert_landmarks_to_points(self, landmarks, image_shape):
        """랜드마크를 좌표로 변환"""
        h, w = image_shape[:2]
        points = {}
        
        # 입술 영역 (간단화된 버전)
        mouth_indices = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        points['mouth'] = []
        for idx in mouth_indices:
            # if idx < len(landmarks.landmark):
                
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            points['mouth'].append((x, y))
        
        # 왼쪽 눈 영역
        left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158]
        points['left_eye'] = []
        for idx in left_eye_indices:
            if idx < len(landmarks.landmark):
                x = int(landmarks.landmark[idx].x * w)
                y = int(landmarks.landmark[idx].y * h)
                points['left_eye'].append((x, y))
        
        # 오른쪽 눈 영역
        right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387]
        points['right_eye'] = []
        for idx in right_eye_indices:
            if idx < len(landmarks.landmark):
                x = int(landmarks.landmark[idx].x * w)
                y = int(landmarks.landmark[idx].y * h)
                points['right_eye'].append((x, y))
        
        # 눈 중심점 계산
        if points['left_eye']:
            left_eye_center = self.calculate_center(points['left_eye'])
            points['left_eye_center'] = left_eye_center
        
        if points['right_eye']:
            right_eye_center = self.calculate_center(points['right_eye'])
            points['right_eye_center'] = right_eye_center
            
        return points
    
    def calculate_center(self, points):
        """포인트들의 중심 계산"""
        if not points:
            return None
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        return (int(sum(x_coords) / len(x_coords)), int(sum(y_coords) / len(y_coords)))

class MakeupEffects:
    def __init__(self):
        pass
    
    def apply_lipstick(self, image, mouth_points, color=(255, 0, 0), alpha=0.6):
        """립스틱 효과 적용"""
        if not mouth_points:
            return image
            
        # OpenCV 이미지를 PIL로 변환
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # 마스크 생성
        mask = Image.new('L', pil_image.size, 0)
        draw = ImageDraw.Draw(mask)
        
        # 입술 영역 그리기
        try:
            draw.polygon(mouth_points, fill=255)
        except:
            # 포인트가 부족하면 원형으로 그리기
            if len(mouth_points) >= 2:
                center = self.calculate_center(mouth_points)
                radius = 20
                draw.ellipse([center[0]-radius, center[1]-radius, 
                            center[0]+radius, center[1]+radius], fill=255)
        
        # 블러 효과
        mask = mask.filter(ImageFilter.GaussianBlur(radius=2))
        
        # 컬러 레이어 생성
        color_layer = Image.new('RGB', pil_image.size, color)
        
        # 블렌딩
        result = Image.composite(color_layer, pil_image, mask)
        result = Image.blend(pil_image, result, alpha)
        
        return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
    
    def apply_eyeshadow(self, image, eye_points, color=(128, 0, 128), alpha=0.3):
        """아이섀도 효과 적용"""
        if not eye_points:
            return image
            
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # 마스크 생성
        mask = Image.new('L', pil_image.size, 0)
        draw = ImageDraw.Draw(mask)
        
        # 눈 영역 확장하여 그리기
        try:
            if len(eye_points) >= 3:
                # 바운딩 박스 계산
                x_coords = [p[0] for p in eye_points]
                y_coords = [p[1] for p in eye_points]
                
                left = min(x_coords) - 10
                right = max(x_coords) + 10
                top = min(y_coords) - 15
                bottom = max(y_coords) + 5
                
                draw.ellipse([left, top, right, bottom], fill=255)
        except:
            return image
        
        # 그라데이션 효과
        mask = mask.filter(ImageFilter.GaussianBlur(radius=8))
        
        # 컬러 적용
        color_layer = Image.new('RGB', pil_image.size, color)
        result = Image.composite(color_layer, pil_image, mask)
        result = Image.blend(pil_image, result, alpha)
        
        return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
    
    def magnify_eye(self, image, eye_center, radius=40, strength=1.3):
        """눈 크게 하기 효과"""
        if not eye_center:
            return image
            
        h, w = image.shape[:2]
        result = image.copy()
        
        x_center, y_center = eye_center
        
        # 안전 범위 체크
        if x_center < 0 or x_center >= w or y_center < 0 or y_center >= h:
            return image
        
        for y in range(max(0, y_center - radius), min(h, y_center + radius)):
            for x in range(max(0, x_center - radius), min(w, x_center + radius)):
                # 중심점으로부터의 거리 계산
                dx = x - x_center
                dy = y - y_center
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance < radius and distance > 0:
                    # 변형 강도 계산
                    factor = (radius - distance) / radius
                    scale = 1 + strength * factor * factor
                    
                    # 새로운 좌표 계산
                    new_x = int(x_center + dx / scale)
                    new_y = int(y_center + dy / scale)
                    
                    # 경계 검사
                    if 0 <= new_x < w and 0 <= new_y < h:
                        result[y, x] = image[new_y, new_x]
        
        return result
    
    def calculate_center(self, points):
        """포인트들의 중심 계산"""
        if not points:
            return None
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        return (int(sum(x_coords) / len(x_coords)), int(sum(y_coords) / len(y_coords)))

class MakeupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Python 메이크업 앱")
        self.root.geometry("1000x700")
        
        # 초기화
        self.face_detector = FaceLandmarkDetector()
        self.makeup_effects = MakeupEffects()
        self.current_image = None
        self.original_image = None
        self.face_landmarks = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 이미지 영역
        self.image_frame = ttk.Frame(main_frame)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.image_label = ttk.Label(self.image_frame, text="이미지를 선택하세요\n(JPG, PNG 파일 지원)")
        self.image_label.pack(pady=50)
        
        # 컨트롤 패널
        control_frame = ttk.Frame(main_frame, width=250)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        control_frame.pack_propagate(False)
        
        # 제목
        title_label = ttk.Label(control_frame, text="🎨 메이크업 앱", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 파일 선택 버튼
        ttk.Button(control_frame, text="📁 이미지 선택", 
                  command=self.select_image).pack(pady=10, fill=tk.X)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # 메이크업 효과 섹션
        makeup_label = ttk.Label(control_frame, text="💄 메이크업 효과", 
                                font=("Arial", 12, "bold"))
        makeup_label.pack(pady=(10, 5))
        
        # 립스틱 효과
        lipstick_frame = ttk.Frame(control_frame)
        lipstick_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(lipstick_frame, text="💋 립스틱 (빨강)", 
                  command=lambda: self.apply_lipstick((255, 0, 0))).pack(side=tk.LEFT, padx=2)
        ttk.Button(lipstick_frame, text="💋 립스틱 (핑크)", 
                  command=lambda: self.apply_lipstick((255, 105, 180))).pack(side=tk.LEFT, padx=2)
        
        # 아이섀도 효과
        eyeshadow_frame = ttk.Frame(control_frame)
        eyeshadow_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(eyeshadow_frame, text="👁️ 아이섀도 (보라)", 
                  command=lambda: self.apply_eyeshadow((128, 0, 128))).pack(side=tk.LEFT, padx=2)
        ttk.Button(eyeshadow_frame, text="👁️ 아이섀도 (갈색)", 
                  command=lambda: self.apply_eyeshadow((139, 69, 19))).pack(side=tk.LEFT, padx=2)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # 이미지 변형 섹션
        transform_label = ttk.Label(control_frame, text="✨ 이미지 변형", 
                                   font=("Arial", 12, "bold"))
        transform_label.pack(pady=(10, 5))
        
        ttk.Button(control_frame, text="👀 눈 크게 하기", 
                  command=self.magnify_eyes).pack(pady=5, fill=tk.X)
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # 유틸리티 버튼
        utility_label = ttk.Label(control_frame, text="🔧 유틸리티", 
                                 font=("Arial", 12, "bold"))
        utility_label.pack(pady=(10, 5))
        
        ttk.Button(control_frame, text="🔄 원본으로 복원", 
                  command=self.reset_image).pack(pady=5, fill=tk.X)
        
        ttk.Button(control_frame, text="💾 결과 저장", 
                  command=self.save_result).pack(pady=5, fill=tk.X)
        
        # 상태 표시
        self.status_label = ttk.Label(control_frame, text="이미지를 선택해주세요", 
                                     font=("Arial", 9))
        self.status_label.pack(pady=10)
    
    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[("이미지 파일", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path):
        try:
            # 이미지 로드
            self.original_image = cv2.imread(file_path)
            if self.original_image is None:
                messagebox.showerror("오류", "이미지를 불러올 수 없습니다.")
                return
            
            self.current_image = self.original_image.copy()
            
            # 얼굴 랜드마크 검출
            self.status_label.config(text="얼굴 분석 중...")
            self.root.update()
            
            self.face_landmarks = self.face_detector.get_face_landmarks(self.original_image)
            
            if self.face_landmarks:
                self.status_label.config(text="얼굴 검출 성공! 메이크업을 적용해보세요.")
            else:
                self.status_label.config(text="얼굴이 검출되지 않았습니다.")
                messagebox.showwarning("경고", "얼굴이 검출되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
            
            # 이미지 표시
            self.display_image(self.current_image)
            
        except Exception as e:
            messagebox.showerror("오류", f"이미지 로드 중 오류가 발생했습니다: {str(e)}")
    
    def display_image(self, image):
        try:
            # OpenCV 이미지를 PIL로 변환
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # 이미지 크기 조정 (최대 600x400)
            max_width, max_height = 600, 400
            img_width, img_height = pil_image.size
            
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width / img_width, max_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # tkinter 이미지로 변환
            tk_image = ImageTk.PhotoImage(pil_image)
            
            # 이미지 표시
            self.image_label.configure(image=tk_image, text="")
            self.image_label.image = tk_image  # 참조 유지
            
        except Exception as e:
            messagebox.showerror("오류", f"이미지 표시 중 오류가 발생했습니다: {str(e)}")
    
    def apply_lipstick(self, color):
        if self.current_image is None:
            messagebox.showwarning("경고", "먼저 이미지를 선택해주세요.")
            return
        
        if not self.face_landmarks or 'mouth' not in self.face_landmarks:
            messagebox.showwarning("경고", "얼굴이 검출되지 않아 립스틱을 적용할 수 없습니다.")
            return
        
        try:
            self.current_image = self.makeup_effects.apply_lipstick(
                self.current_image, 
                self.face_landmarks['mouth'],
                color=color,
                alpha=0.6
            )
            self.display_image(self.current_image)
            self.status_label.config(text="립스틱 효과가 적용되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"립스틱 적용 중 오류가 발생했습니다: {str(e)}")
    
    def apply_eyeshadow(self, color):
        if self.current_image is None:
            messagebox.showwarning("경고", "먼저 이미지를 선택해주세요.")
            return
        
        if not self.face_landmarks:
            messagebox.showwarning("경고", "얼굴이 검출되지 않아 아이섀도를 적용할 수 없습니다.")
            return
        
        try:
            # 양쪽 눈에 아이섀도 적용
            if 'left_eye' in self.face_landmarks:
                self.current_image = self.makeup_effects.apply_eyeshadow(
                    self.current_image,
                    self.face_landmarks['left_eye'],
                    color=color,
                    alpha=0.3
                )
            
            if 'right_eye' in self.face_landmarks:
                self.current_image = self.makeup_effects.apply_eyeshadow(
                    self.current_image,
                    self.face_landmarks['right_eye'],
                    color=color,
                    alpha=0.3
                )
            
            self.display_image(self.current_image)
            self.status_label.config(text="아이섀도 효과가 적용되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"아이섀도 적용 중 오류가 발생했습니다: {str(e)}")
    
    def magnify_eyes(self):
        if self.current_image is None:
            messagebox.showwarning("경고", "먼저 이미지를 선택해주세요.")
            return
        
        if not self.face_landmarks:
            messagebox.showwarning("경고", "얼굴이 검출되지 않아 눈 크게 하기를 적용할 수 없습니다.")
            return
        
        try:
            # 양쪽 눈 크게 하기
            if 'left_eye_center' in self.face_landmarks:
                self.current_image = self.makeup_effects.magnify_eye(
                    self.current_image,
                    self.face_landmarks['left_eye_center'],
                    radius=40,
                    strength=1.3
                )
            
            if 'right_eye_center' in self.face_landmarks:
                self.current_image = self.makeup_effects.magnify_eye(
                    self.current_image,
                    self.face_landmarks['right_eye_center'],
                    radius=40,
                    strength=1.3
                )
            
            self.display_image(self.current_image)
            self.status_label.config(text="눈 크게 하기 효과가 적용되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"눈 크게 하기 적용 중 오류가 발생했습니다: {str(e)}")
    
    def reset_image(self):
        if self.original_image is None:
            messagebox.showwarning("경고", "원본 이미지가 없습니다.")
            return
        
        self.current_image = self.original_image.copy()
        self.display_image(self.current_image)
        self.status_label.config(text="원본 이미지로 복원되었습니다.")
    
    def save_result(self):
        if self.current_image is None:
            messagebox.showwarning("경고", "저장할 이미지가 없습니다.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="결과 저장",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")]
        )
        
        if file_path:
            try:
                cv2.imwrite(file_path, self.current_image)
                messagebox.showinfo("성공", f"이미지가 저장되었습니다:\n{file_path}")
                self.status_label.config(text="이미지가 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"이미지 저장 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MakeupApp(root)
    root.mainloop() 