#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Streamlit Makeup App
향상된 스트림릿 메이크업 앱 - Task 3의 모든 기능 포함
"""

import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFilter
import io
from typing import List, Tuple

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
    
    # 볼 영역 (블러셔용)
    left_cheek_indices = [116, 117, 118, 119, 120, 121, 126, 142, 36, 205, 206, 207, 213]
    points['left_cheek'] = []
    for idx in left_cheek_indices:
        if idx < len(landmarks.landmark):
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            points['left_cheek'].append((x, y))
    
    right_cheek_indices = [345, 346, 347, 348, 349, 350, 451, 452, 453, 464, 435, 410, 454]
    points['right_cheek'] = []
    for idx in right_cheek_indices:
        if idx < len(landmarks.landmark):
            x = int(landmarks.landmark[idx].x * w)
            y = int(landmarks.landmark[idx].y * h)
            points['right_cheek'].append((x, y))
    
    return points

def apply_lipstick(image, mouth_points, color=(255, 0, 0), intensity=0.6, glossiness=0.0):
    """향상된 립스틱 효과 적용"""
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
    result = Image.blend(pil_image, result, intensity)
    
    # 광택 효과 추가
    if glossiness > 0:
        highlight = Image.new('RGB', pil_image.size, (255, 255, 255))
        highlight_mask = mask.filter(ImageFilter.GaussianBlur(radius=5))
        # 상단 부분만 하이라이트
        highlight_array = np.array(highlight_mask)
        highlight_array[len(highlight_array)//2:] = 0
        highlight_mask = Image.fromarray(highlight_array)
        
        result = Image.composite(highlight, result, highlight_mask)
        result = Image.blend(pil_image, result, intensity + glossiness * 0.3)
    
    return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)

def apply_eyeshadow(image, eye_points, colors=[(128, 0, 128)], intensity=0.3, style="natural", shimmer=0.0):
    """향상된 아이섀도 효과 적용"""
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
            
            if style == "natural":
                left = min(x_coords) - 10
                right = max(x_coords) + 10
                top = min(y_coords) - 15
                bottom = max(y_coords) + 5
            elif style == "smoky":
                left = min(x_coords) - 20
                right = max(x_coords) + 20
                top = min(y_coords) - 25
                bottom = max(y_coords) + 10
            elif style == "dramatic":
                left = min(x_coords) - 25
                right = max(x_coords) + 25
                top = min(y_coords) - 30
                bottom = max(y_coords) + 15
            else:
                left = min(x_coords) - 10
                right = max(x_coords) + 10
                top = min(y_coords) - 15
                bottom = max(y_coords) + 5
            
            draw.ellipse([left, top, right, bottom], fill=255)
    except:
        return image
    
    # 스타일에 따른 블러 강도
    blur_radius = {"natural": 8, "smoky": 12, "dramatic": 15}.get(style, 8)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # 다중 색상 그라데이션
    if len(colors) > 1:
        # 그라데이션 효과
        for i, color in enumerate(colors):
            color_layer = Image.new('RGB', pil_image.size, color)
            layer_intensity = intensity * (1.0 - i * 0.3)  # 각 레이어마다 강도 감소
            temp_result = Image.composite(color_layer, pil_image, mask)
            pil_image = Image.blend(pil_image, temp_result, layer_intensity)
    else:
        # 단일 색상
        color_layer = Image.new('RGB', pil_image.size, colors[0])
        result = Image.composite(color_layer, pil_image, mask)
        pil_image = Image.blend(pil_image, result, intensity)
    
    # 시머 효과
    if shimmer > 0:
        shimmer_layer = Image.new('RGB', pil_image.size, (255, 255, 255))
        shimmer_mask = mask.filter(ImageFilter.GaussianBlur(radius=3))
        pil_image = Image.composite(shimmer_layer, pil_image, shimmer_mask)
        pil_image = Image.blend(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)), pil_image, intensity + shimmer * 0.2)
    
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

def apply_blush(image, cheek_points, color=(255, 182, 193), intensity=0.3):
    """블러셔 효과 적용"""
    if not cheek_points:
        return image
        
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # 마스크 생성
    mask = Image.new('L', pil_image.size, 0)
    draw = ImageDraw.Draw(mask)
    
    # 볼 영역 그리기
    try:
        if len(cheek_points) >= 3:
            x_coords = [p[0] for p in cheek_points]
            y_coords = [p[1] for p in cheek_points]
            
            center_x = sum(x_coords) // len(x_coords)
            center_y = sum(y_coords) // len(y_coords)
            
            # 타원형 블러셔
            radius_x = 30
            radius_y = 25
            draw.ellipse([center_x - radius_x, center_y - radius_y,
                         center_x + radius_x, center_y + radius_y], fill=255)
    except:
        return image
    
    # 부드러운 블러 효과
    mask = mask.filter(ImageFilter.GaussianBlur(radius=15))
    
    # 컬러 레이어 생성
    color_layer = Image.new('RGB', pil_image.size, color)
    
    # 블렌딩
    result = Image.composite(color_layer, pil_image, mask)
    result = Image.blend(pil_image, result, intensity)
    
    return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)

def apply_foundation(image, intensity=0.2, skin_tone=(245, 222, 179)):
    """파운데이션 효과 적용"""
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # 전체 얼굴에 파운데이션 적용
    foundation_layer = Image.new('RGB', pil_image.size, skin_tone)
    result = Image.blend(pil_image, foundation_layer, intensity)
    
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
        page_title="🎨 향상된 메이크업 앱 - Task 3 전체 기능",
        page_icon="🎨",
        layout="wide"
    )
    
    st.title("🎨 향상된 메이크업 앱")
    st.markdown("**Task 3의 모든 메이크업 기능을 체험해보세요!**")
    
    # 사이드바 설정
    st.sidebar.title("🎨 메이크업 컨트롤")
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
        
        # 세션 상태 초기화
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
        
        # 메인 레이아웃
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if face_landmarks:
                st.success("✅ 얼굴이 검출되었습니다!")
            else:
                st.warning("⚠️ 얼굴이 검출되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
            
            # 이미지 표시
            rgb_image = cv2.cvtColor(st.session_state.current_image, cv2.COLOR_BGR2RGB)
            st.image(rgb_image, caption="결과 이미지", use_container_width=True)
        
        with col2:
            # 전체 강도 조절
            st.sidebar.markdown("### 🎚️ 전체 강도 조절")
            global_intensity = st.sidebar.slider("전체 메이크업 강도", 0.1, 1.0, 0.6, 0.1)
            
            # 립스틱 섹션
            st.sidebar.markdown("### 💋 립스틱")
            lipstick_intensity = st.sidebar.slider("립스틱 강도", 0.1, 1.0, 0.6, 0.1)
            lipstick_glossiness = st.sidebar.slider("광택도", 0.0, 1.0, 0.0, 0.1)
            
            lipstick_col1, lipstick_col2 = st.sidebar.columns(2)
            with lipstick_col1:
                if st.button("💋 빨간 립스틱"):
                    if face_landmarks and 'mouth' in face_landmarks:
                        st.session_state.current_image = apply_lipstick(
                            st.session_state.current_image,
                            face_landmarks['mouth'],
                            color=(255, 0, 0),
                            intensity=lipstick_intensity * global_intensity,
                            glossiness=lipstick_glossiness
                        )
                        st.rerun()
            
            with lipstick_col2:
                if st.button("💋 핑크 립스틱"):
                    if face_landmarks and 'mouth' in face_landmarks:
                        st.session_state.current_image = apply_lipstick(
                            st.session_state.current_image,
                            face_landmarks['mouth'],
                            color=(255, 105, 180),
                            intensity=lipstick_intensity * global_intensity,
                            glossiness=lipstick_glossiness
                        )
                        st.rerun()
            
            # 아이섀도 섹션
            st.sidebar.markdown("### 👁️ 아이섀도")
            eyeshadow_intensity = st.sidebar.slider("아이섀도 강도", 0.1, 1.0, 0.4, 0.1)
            eyeshadow_shimmer = st.sidebar.slider("시머 효과", 0.0, 1.0, 0.0, 0.1)
            eyeshadow_style = st.sidebar.selectbox("스타일", ["natural", "smoky", "dramatic"])
            
            # 색상 선택
            eyeshadow_color1 = st.sidebar.color_picker("주 색상", "#800080")
            eyeshadow_color2 = st.sidebar.color_picker("보조 색상", "#DDA0DD")
            
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            if st.sidebar.button("👁️ 아이섀도 적용"):
                if face_landmarks:
                    colors = [hex_to_rgb(eyeshadow_color1), hex_to_rgb(eyeshadow_color2)]
                    
                    if 'left_eye' in face_landmarks:
                        st.session_state.current_image = apply_eyeshadow(
                            st.session_state.current_image,
                            face_landmarks['left_eye'],
                            colors=colors,
                            intensity=eyeshadow_intensity * global_intensity,
                            style=eyeshadow_style,
                            shimmer=eyeshadow_shimmer
                        )
                    if 'right_eye' in face_landmarks:
                        st.session_state.current_image = apply_eyeshadow(
                            st.session_state.current_image,
                            face_landmarks['right_eye'],
                            colors=colors,
                            intensity=eyeshadow_intensity * global_intensity,
                            style=eyeshadow_style,
                            shimmer=eyeshadow_shimmer
                        )
                    st.rerun()
            
            # 블러셔 섹션
            st.sidebar.markdown("### 🌸 블러셔")
            blush_intensity = st.sidebar.slider("블러셔 강도", 0.1, 1.0, 0.3, 0.1)
            blush_color = st.sidebar.color_picker("블러셔 색상", "#FFB6C1")
            
            if st.sidebar.button("🌸 블러셔 적용"):
                if face_landmarks:
                    blush_rgb = hex_to_rgb(blush_color)
                    
                    if 'left_cheek' in face_landmarks:
                        st.session_state.current_image = apply_blush(
                            st.session_state.current_image,
                            face_landmarks['left_cheek'],
                            color=blush_rgb,
                            intensity=blush_intensity * global_intensity
                        )
                    if 'right_cheek' in face_landmarks:
                        st.session_state.current_image = apply_blush(
                            st.session_state.current_image,
                            face_landmarks['right_cheek'],
                            color=blush_rgb,
                            intensity=blush_intensity * global_intensity
                        )
                    st.rerun()
            
            # 파운데이션 섹션
            st.sidebar.markdown("### 🎨 파운데이션")
            foundation_intensity = st.sidebar.slider("파운데이션 강도", 0.1, 0.5, 0.2, 0.05)
            foundation_color = st.sidebar.color_picker("파운데이션 색상", "#F5DEB3")
            
            if st.sidebar.button("🎨 파운데이션 적용"):
                foundation_rgb = hex_to_rgb(foundation_color)
                st.session_state.current_image = apply_foundation(
                    st.session_state.current_image,
                    intensity=foundation_intensity * global_intensity,
                    skin_tone=foundation_rgb
                )
                st.rerun()
            
            # 눈 효과 섹션
            st.sidebar.markdown("### 👀 눈 효과")
            eye_strength = st.sidebar.slider("눈 확대 강도", 0.5, 2.0, 1.3, 0.1)
            
            if st.sidebar.button("👀 눈 크게 하기"):
                if face_landmarks:
                    if 'left_eye' in face_landmarks:
                        st.session_state.current_image = magnify_eye(
                            st.session_state.current_image,
                            face_landmarks['left_eye'],
                            radius=40,
                            strength=eye_strength
                        )
                    if 'right_eye' in face_landmarks:
                        st.session_state.current_image = magnify_eye(
                            st.session_state.current_image,
                            face_landmarks['right_eye'],
                            radius=40,
                            strength=eye_strength
                        )
                    st.rerun()
            
            # 유틸리티 버튼
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🔧 유틸리티")
            
            if st.sidebar.button("🔄 원본으로 복원"):
                st.session_state.current_image = st.session_state.original_image.copy()
                st.rerun()
            
            # 결과 다운로드
            if st.sidebar.button("💾 결과 다운로드"):
                is_success, buffer = cv2.imencode(".jpg", st.session_state.current_image)
                if is_success:
                    st.sidebar.download_button(
                        label="📥 이미지 다운로드",
                        data=buffer.tobytes(),
                        file_name="enhanced_makeup_result.jpg",
                        mime="image/jpeg"
                    )
    
    else:
        st.info("👆 이미지를 업로드하여 Task 3의 모든 메이크업 기능을 체험해보세요!")
        
        # 기능 소개
        st.markdown("---")
        st.markdown("## 🎨 Task 3 구현된 메이크업 기능들")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 💄 기본 색상 블렌딩 시스템
            - **Alpha 블렌딩**: 투명도 기반 색상 합성
            - **Multiply 블렌딩**: 어두운 부분 강조
            - **Overlay 블렌딩**: 대비 강화
            - **Soft Light 블렌딩**: 부드러운 조명 효과
            
            ### 💋 립스틱 적용 기능
            - **정확한 입술 감지**: MediaPipe 기반
            - **자연스러운 색상 적용**: 그라데이션 효과
            - **광택 효과**: 매트부터 글로시까지
            - **강도 조절**: 0.1 ~ 1.0 세밀 조절
            """)
        
        with col2:
            st.markdown("""
            ### 👁️ 아이섀도 적용 기능
            - **다중 색상 블렌딩**: 최대 2색 그라데이션
            - **스타일 템플릿**: Natural, Smoky, Dramatic
            - **시머 효과**: 반짝임 효과 조절
            - **정확한 눈꺼풀 감지**: 확장된 영역 적용
            
            ### 🌸 블러셔 & 파운데이션
            - **볼 영역 자동 감지**: 얼굴형에 맞는 위치
            - **전체 얼굴 파운데이션**: 자연스러운 피부 보정
            - **색상 커스터마이징**: 사용자 정의 색상
            - **부드러운 블렌딩**: 자연스러운 경계 처리
            """)

if __name__ == "__main__":
    main()