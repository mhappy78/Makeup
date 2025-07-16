import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFilter
import io

# MediaPipe 초기화
@st.cache_resource
def load_face_mesh():
    return mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    )

def get_face_landmarks(image, face_mesh):
    """얼굴 랜드마크 검출"""
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)
    
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0]
        return convert_landmarks_to_points(landmarks, image.shape)
    return None

def convert_landmarks_to_points(landmarks, image_shape):
    """랜드마크를 좌표로 변환"""
    h, w = image_shape[:2]
    points = {}
    
    # 입술 영역
    mouth_indices = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
    points['mouth'] = []
    for idx in mouth_indices:
        if idx < len(landmarks.landmark):
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            points['mouth'].append((x, y))
    
    # 눈 영역
    left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158]
    points['left_eye'] = []
    for idx in left_eye_indices:
        if idx < len(landmarks.landmark):
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            points['left_eye'].append((x, y))
    
    right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387]
    points['right_eye'] = []
    for idx in right_eye_indices:
        if idx < len(landmarks.landmark):
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            points['right_eye'].append((x, y))
    
    return points

def apply_lipstick(image, mouth_points, color=(255, 0, 0), alpha=0.6):
    """립스틱 효과 적용"""
    if not mouth_points:
        return image
        
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # 마스크 생성
    mask = Image.new('L', pil_image.size, 0)
    draw = ImageDraw.Draw(mask)
    
    # 입술 영역 그리기
    try:
        draw.polygon(mouth_points, fill=255)
    except:
        if len(mouth_points) >= 2:
            # 포인트들의 중심 계산
            x_coords = [p[0] for p in mouth_points]
            y_coords = [p[1] for p in mouth_points]
            center = (int(sum(x_coords) / len(x_coords)), int(sum(y_coords) / len(y_coords)))
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

def apply_eyeshadow(image, eye_points, color=(128, 0, 128), alpha=0.3):
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

def magnify_eye(image, eye_points, radius=40, strength=1.3):
    """눈 크게 하기 효과"""
    if not eye_points:
        return image
    
    # 눈 중심 계산
    x_coords = [p[0] for p in eye_points]
    y_coords = [p[1] for p in eye_points]
    eye_center = (int(sum(x_coords) / len(x_coords)), int(sum(y_coords) / len(y_coords)))
    
    h, w = image.shape[:2]
    result = image.copy()
    
    x_center, y_center = eye_center
    
    # 안전 범위 체크
    if x_center < 0 or x_center >= w or y_center < 0 or y_center >= h:
        return image
    
    for y in range(max(0, y_center - radius), min(h, y_center + radius)):
        for x in range(max(0, x_center - radius), min(w, x_center + radius)):
            dx = x - x_center
            dy = y - y_center
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance < radius and distance > 0:
                factor = (radius - distance) / radius
                scale = 1 + strength * factor * factor
                
                new_x = int(x_center + dx / scale)
                new_y = int(y_center + dy / scale)
                
                if 0 <= new_x < w and 0 <= new_y < h:
                    result[y, x] = image[new_y, new_x]
    
    return result

def main():
    st.set_page_config(
        page_title="🎨 Python 메이크업 앱",
        page_icon="🎨",
        layout="wide"
    )
    
    st.title("🎨 Python 메이크업 앱")
    st.markdown("**이미지를 업로드하고 다양한 메이크업 효과를 적용해보세요!**")
    
    # 사이드바 설정
    st.sidebar.title("🎨 메이크업 효과")
    st.sidebar.markdown("---")
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "이미지를 업로드하세요",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        help="JPG, PNG, BMP 파일을 지원합니다"
    )
    
    if uploaded_file is not None:
        # 이미지 로드
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        
        if image is None:
            st.error("이미지를 불러올 수 없습니다. 다른 이미지를 선택해주세요.")
            return
        
        # 원본 이미지 저장
        if 'original_image' not in st.session_state:
            st.session_state.original_image = image.copy()
        
        if 'current_image' not in st.session_state:
            st.session_state.current_image = image.copy()
        
        # 얼굴 랜드마크 검출
        face_mesh = load_face_mesh()
        
        if 'face_landmarks' not in st.session_state:
            with st.spinner("얼굴 분석 중..."):
                st.session_state.face_landmarks = get_face_landmarks(image, face_mesh)
        
        face_landmarks = st.session_state.face_landmarks
        
        # 컬럼 레이아웃
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if face_landmarks:
                st.success("✅ 얼굴이 검출되었습니다!")
            else:
                st.warning("⚠️ 얼굴이 검출되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
            
            # 이미지 표시
            rgb_image = cv2.cvtColor(st.session_state.current_image, cv2.COLOR_BGR2RGB)
            st.image(rgb_image, caption="결과 이미지", use_column_width=True)
        
        # 사이드바 - 메이크업 효과
        st.sidebar.markdown("### 💄 메이크업 효과")
        
        # 립스틱 효과
        st.sidebar.markdown("**립스틱**")
        lipstick_col1, lipstick_col2 = st.sidebar.columns(2)
        
        with lipstick_col1:
            if st.button("💋 빨간 립스틱"):
                if face_landmarks and 'mouth' in face_landmarks:
                    st.session_state.current_image = apply_lipstick(
                        st.session_state.current_image,
                        face_landmarks['mouth'],
                        color=(255, 0, 0),
                        alpha=0.6
                    )
                    st.rerun()
                else:
                    st.error("얼굴이 검출되지 않아 립스틱을 적용할 수 없습니다.")
        
        with lipstick_col2:
            if st.button("💋 핑크 립스틱"):
                if face_landmarks and 'mouth' in face_landmarks:
                    st.session_state.current_image = apply_lipstick(
                        st.session_state.current_image,
                        face_landmarks['mouth'],
                        color=(255, 105, 180),
                        alpha=0.6
                    )
                    st.rerun()
                else:
                    st.error("얼굴이 검출되지 않아 립스틱을 적용할 수 없습니다.")
        
        # 아이섀도 효과
        st.sidebar.markdown("**아이섀도**")
        eyeshadow_col1, eyeshadow_col2 = st.sidebar.columns(2)
        
        with eyeshadow_col1:
            if st.button("👁️ 보라 아이섀도"):
                if face_landmarks:
                    if 'left_eye' in face_landmarks:
                        st.session_state.current_image = apply_eyeshadow(
                            st.session_state.current_image,
                            face_landmarks['left_eye'],
                            color=(128, 0, 128),
                            alpha=0.3
                        )
                    if 'right_eye' in face_landmarks:
                        st.session_state.current_image = apply_eyeshadow(
                            st.session_state.current_image,
                            face_landmarks['right_eye'],
                            color=(128, 0, 128),
                            alpha=0.3
                        )
                    st.rerun()
                else:
                    st.error("얼굴이 검출되지 않아 아이섀도를 적용할 수 없습니다.")
        
        with eyeshadow_col2:
            if st.button("👁️ 갈색 아이섀도"):
                if face_landmarks:
                    if 'left_eye' in face_landmarks:
                        st.session_state.current_image = apply_eyeshadow(
                            st.session_state.current_image,
                            face_landmarks['left_eye'],
                            color=(139, 69, 19),
                            alpha=0.3
                        )
                    if 'right_eye' in face_landmarks:
                        st.session_state.current_image = apply_eyeshadow(
                            st.session_state.current_image,
                            face_landmarks['right_eye'],
                            color=(139, 69, 19),
                            alpha=0.3
                        )
                    st.rerun()
                else:
                    st.error("얼굴이 검출되지 않아 아이섀도를 적용할 수 없습니다.")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ✨ 이미지 변형")
        
        # 눈 크게 하기
        if st.sidebar.button("👀 눈 크게 하기"):
            if face_landmarks:
                if 'left_eye' in face_landmarks:
                    st.session_state.current_image = magnify_eye(
                        st.session_state.current_image,
                        face_landmarks['left_eye'],
                        radius=40,
                        strength=1.3
                    )
                if 'right_eye' in face_landmarks:
                    st.session_state.current_image = magnify_eye(
                        st.session_state.current_image,
                        face_landmarks['right_eye'],
                        radius=40,
                        strength=1.3
                    )
                st.rerun()
            else:
                st.error("얼굴이 검출되지 않아 눈 크게 하기를 적용할 수 없습니다.")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔧 유틸리티")
        
        # 원본 복원
        if st.sidebar.button("🔄 원본으로 복원"):
            st.session_state.current_image = st.session_state.original_image.copy()
            st.rerun()
        
        # 결과 다운로드
        if st.sidebar.button("💾 결과 다운로드"):
            # 이미지를 바이트로 변환
            is_success, buffer = cv2.imencode(".jpg", st.session_state.current_image)
            if is_success:
                st.sidebar.download_button(
                    label="📥 이미지 다운로드",
                    data=buffer.tobytes(),
                    file_name="makeup_result.jpg",
                    mime="image/jpeg"
                )
    
    else:
        st.info("👆 이미지를 업로드하여 메이크업 효과를 체험해보세요!")
        
        # 사용법 안내
        st.markdown("---")
        st.markdown("## 📖 사용법")
        st.markdown("""
        1. **이미지 업로드**: 얼굴이 나온 이미지를 업로드하세요
        2. **얼굴 분석**: 자동으로 얼굴을 검출하고 특징점을 분석합니다
        3. **메이크업 적용**: 사이드바에서 원하는 메이크업 효과를 선택하세요
        4. **결과 확인**: 실시간으로 적용된 결과를 확인할 수 있습니다
        5. **저장**: 마음에 드는 결과를 다운로드하세요
        """)
        
        st.markdown("---")
        st.markdown("## ✨ 지원하는 효과")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **💄 메이크업 효과**
            - 🔴 빨간 립스틱
            - 🩷 핑크 립스틱
            - 💜 보라 아이섀도
            - 🤎 갈색 아이섀도
            """)
        
        with col2:
            st.markdown("""
            **✨ 이미지 변형**
            - 👀 눈 크게 하기
            - 🔄 원본 복원
            - 💾 결과 저장
            """)

if __name__ == "__main__":
    main() 