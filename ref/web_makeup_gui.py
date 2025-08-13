import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
from utils import *

# 페이지 설정
st.set_page_config(
    page_title="🎭 Virtual Makeup Studio",
    page_icon="💄",
    layout="wide"
)

# 제목
st.title("🎭 Virtual Makeup Studio")
st.markdown("**실시간으로 가상 메이크업을 적용하고 색상과 강도를 조정해보세요!**")

# 레이아웃 설정: 좌측 컨트롤, 우측 결과
col_left, col_right = st.columns([1, 2])

with col_left:
    st.header("🎨 메이크업 컨트롤")
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "📁 이미지 업로드", 
        type=['png', 'jpg', 'jpeg'],
        help="얼굴이 포함된 이미지를 업로드하세요"
    )
    
    # 이미지가 업로드되면 컨트롤 표시
    if uploaded_file is not None:
        
        # 메이크업 부위별 색상 조정
        st.subheader("💄 색상 조정")
        
        # 입술 색상
        lip_color = st.color_picker("💋 입술 색상", "#FF0000", key="lip_color")
        lip_r, lip_g, lip_b = tuple(int(lip_color[i:i+2], 16) for i in (1, 3, 5))
        
        # 아이라이너 색상  
        eyeliner_color = st.color_picker("👁️ 아이라이너 색상", "#8B0000", key="eyeliner_color")
        eyeliner_r, eyeliner_g, eyeliner_b = tuple(int(eyeliner_color[i:i+2], 16) for i in (1, 3, 5))
        
        # 아이섀도 색상
        eyeshadow_color = st.color_picker("🎨 아이섀도 색상", "#006400", key="eyeshadow_color")
        eyeshadow_r, eyeshadow_g, eyeshadow_b = tuple(int(eyeshadow_color[i:i+2], 16) for i in (1, 3, 5))
        
        # 눈썹 색상
        eyebrow_color = st.color_picker("🤎 눈썹 색상", "#8B4513", key="eyebrow_color")
        eyebrow_r, eyebrow_g, eyebrow_b = tuple(int(eyebrow_color[i:i+2], 16) for i in (1, 3, 5))
        
        # 강도 조정
        st.subheader("⚡ 강도 조정")
        
        # 마스크 결합 강도 (투명도)
        mask_alpha = st.slider(
            "🔀 메이크업 강도", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.3, 
            step=0.05,
            help="메이크업의 투명도를 조정합니다",
            key="mask_alpha"
        )
        
        # 블러 강도
        blur_strength = st.slider(
            "🌫️ 블러 강도", 
            min_value=1, 
            max_value=21, 
            value=7, 
            step=2,
            help="메이크업의 부드러움을 조정합니다 (홀수만 가능)",
            key="blur_strength"
        )
        
        # 블러 시그마
        blur_sigma = st.slider(
            "🎯 블러 시그마", 
            min_value=1, 
            max_value=10, 
            value=4, 
            step=1,
            help="블러의 확산 정도를 조정합니다",
            key="blur_sigma"
        )
        
        # 개별 부위 강도 조정
        st.subheader("🎚️ 부위별 강도")
        
        lip_intensity = st.slider("💋 입술 강도", 0.0, 1.0, 1.0, 0.1, key="lip_intensity")
        eyeliner_intensity = st.slider("👁️ 아이라이너 강도", 0.0, 1.0, 1.0, 0.1, key="eyeliner_intensity")
        eyeshadow_intensity = st.slider("🎨 아이섀도 강도", 0.0, 1.0, 1.0, 0.1, key="eyeshadow_intensity")
        eyebrow_intensity = st.slider("🤎 눈썹 강도", 0.0, 1.0, 1.0, 0.1, key="eyebrow_intensity")
        
        # 고급 옵션
        st.subheader("🔧 고급 옵션")
        
        show_landmarks = st.checkbox("🔍 랜드마크 표시", value=False, key="show_landmarks")
        show_original = st.checkbox("📸 원본 이미지 표시", value=True, key="show_original")
        show_mask = st.checkbox("🎨 마스크 이미지 표시", value=True, key="show_mask")

# 색상 맵과 강도 맵 업데이트 함수
def update_colors_map():
    return {
        "LIP_UPPER": [lip_b, lip_g, lip_r],  # BGR 형식
        "LIP_LOWER": [lip_b, lip_g, lip_r],
        "EYELINER_LEFT": [eyeliner_b, eyeliner_g, eyeliner_r],
        "EYELINER_RIGHT": [eyeliner_b, eyeliner_g, eyeliner_r],
        "EYESHADOW_LEFT": [eyeshadow_b, eyeshadow_g, eyeshadow_r],
        "EYESHADOW_RIGHT": [eyeshadow_b, eyeshadow_g, eyeshadow_r],
        "EYEBROW_LEFT": [eyebrow_b, eyebrow_g, eyebrow_r],
        "EYEBROW_RIGHT": [eyebrow_b, eyebrow_g, eyebrow_r],
    }

def update_intensity_map():
    return {
        "LIP_UPPER": lip_intensity,
        "LIP_LOWER": lip_intensity,
        "EYELINER_LEFT": eyeliner_intensity,
        "EYELINER_RIGHT": eyeliner_intensity,
        "EYESHADOW_LEFT": eyeshadow_intensity,
        "EYESHADOW_RIGHT": eyeshadow_intensity,
        "EYEBROW_LEFT": eyebrow_intensity,
        "EYEBROW_RIGHT": eyebrow_intensity,
    }

# 향상된 마스크 추가 함수
def add_enhanced_mask(mask, idx_to_coordinates, face_connections, colors_map, intensity_map, face_elements, blur_strength, blur_sigma):
    """강화된 마스크 생성 함수"""
    if not idx_to_coordinates:
        return mask
    
    for i, (connection, element) in enumerate(zip(face_connections, face_elements)):
        if all(idx in idx_to_coordinates for idx in connection):
            points = np.array([idx_to_coordinates[idx] for idx in connection])
            
            # 개별 부위별 마스크 생성
            temp_mask = np.zeros_like(mask)
            color = colors_map[element]
            cv2.fillPoly(temp_mask, [points], color)
            
            # 블러 적용
            temp_mask = cv2.GaussianBlur(temp_mask, (blur_strength, blur_strength), blur_sigma)
            
            # 부위별 강도 적용
            intensity = intensity_map[element]
            temp_mask = (temp_mask * intensity).astype(np.uint8)
            
            # 마스크에 추가
            mask = cv2.add(mask, temp_mask)
    
    return mask

# 랜드마크 그리기 함수
def draw_landmarks(image, landmarks, color=(0, 255, 0), radius=2):
    """얼굴 랜드마크를 이미지에 그립니다"""
    result = image.copy()
    for idx, point in landmarks.items():
        cv2.circle(result, point, radius, color, -1)
    return result

# 메이크업 적용 함수
def apply_makeup(image, colors_map, intensity_map, mask_alpha, blur_strength, blur_sigma, show_landmarks=False):
    """메이크업을 적용하는 함수"""
    # 얼굴 부위 설정
    face_elements = [
        "LIP_LOWER", "LIP_UPPER",
        "EYEBROW_LEFT", "EYEBROW_RIGHT",
        "EYELINER_LEFT", "EYELINER_RIGHT",
        "EYESHADOW_LEFT", "EYESHADOW_RIGHT",
    ]
    
    # 얼굴 연결점 추출
    face_connections = [face_points[idx] for idx in face_elements]
    
    # 빈 마스크 생성
    mask = np.zeros_like(image)
    
    # 얼굴 랜드마크 추출
    face_landmarks = read_landmarks(image=image)
    
    # 향상된 마스크 생성
    mask = add_enhanced_mask(
        mask, face_landmarks, face_connections, 
        colors_map, intensity_map, face_elements,
        blur_strength, blur_sigma
    )
    
    # 이미지와 마스크 결합
    output = cv2.addWeighted(image, 1.0, mask, mask_alpha, 1.0)
    
    # 랜드마크 표시
    if show_landmarks and face_landmarks:
        output = draw_landmarks(output, face_landmarks)
    
    return output, mask, len(face_landmarks) > 0

# 우측 결과 영역
with col_right:
    st.header("📺 메이크업 결과")
    
    if uploaded_file is not None:
        # 이미지 로드
        image = Image.open(uploaded_file)
        image_array = np.array(image)
        
        # RGB를 BGR로 변환 (OpenCV 형식)
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array
        
        # 색상 맵과 강도 맵 업데이트
        colors_map = update_colors_map()
        intensity_map = update_intensity_map()
        
        # 메이크업 적용
        try:
            result_image, mask_image, face_detected = apply_makeup(
                image_bgr, colors_map, intensity_map, 
                mask_alpha, blur_strength, blur_sigma, show_landmarks
            )
            
            # BGR을 RGB로 변환 (Streamlit 표시용)
            result_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
            mask_rgb = cv2.cvtColor(mask_image, cv2.COLOR_BGR2RGB)
            
            # 표시할 이미지 개수에 따라 열 설정
            images_to_show = []
            titles = []
            
            if show_original:
                images_to_show.append(image)
                titles.append("📸 원본 이미지")
            
            images_to_show.append(result_rgb)
            titles.append("🎭 메이크업 결과")
            
            if show_mask:
                images_to_show.append(mask_rgb)
                titles.append("🎨 메이크업 마스크")
            
            # 동적으로 열 생성
            cols = st.columns(len(images_to_show))
            
            for i, (col, img, title) in enumerate(zip(cols, images_to_show, titles)):
                with col:
                    st.subheader(title)
                    st.image(img, use_column_width=True)
            
            # 상태 표시
            if face_detected:
                st.success("✅ 얼굴이 성공적으로 감지되었습니다!")
                
                # 다운로드 버튼
                result_pil = Image.fromarray(result_rgb)
                buf = io.BytesIO()
                result_pil.save(buf, format='PNG')
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="💾 결과 이미지 다운로드",
                    data=byte_im,
                    file_name="virtual_makeup_result.png",
                    mime="image/png",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ 얼굴을 감지하지 못했습니다. 다른 이미지를 시도해보세요.")
        
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            st.info("이미지 처리 중 문제가 발생했습니다. 다른 이미지를 시도해보세요.")
    
    else:
        # 이미지 업로드 안내
        st.info("👆 왼쪽에서 이미지를 업로드하세요!")
        
        # 사용 방법 안내
        st.markdown("""
        ### 📖 사용 방법:
        
        1. **📁 이미지 업로드**: 왼쪽에서 얼굴이 포함된 이미지를 업로드하세요
        2. **🎨 색상 조정**: 각 메이크업 부위의 색상을 색상 선택기로 조정하세요
        3. **⚡ 강도 조정**: 메이크업 강도, 블러 강도를 슬라이더로 조정하세요
        4. **🎚️ 부위별 조정**: 각 부위별로 세밀한 강도 조정이 가능합니다
        5. **💾 다운로드**: 결과가 마음에 들면 이미지를 다운로드하세요
        
        ### 🎭 지원하는 메이크업 부위:
        - 💋 **입술**: 상하 입술에 립스틱 색상 적용
        - 👁️ **아이라이너**: 눈 윤곽에 아이라이너 적용
        - 🎨 **아이섀도**: 눈두덩이에 아이섀도 적용
        - 🤎 **눈썹**: 눈썹에 색상 적용
        
        ### 💡 팁:
        - 설정을 변경하면 **실시간으로 결과가 업데이트**됩니다
        - 랜드마크 표시로 얼굴 인식 정확도를 확인할 수 있습니다
        - 고급 옵션으로 표시할 이미지를 선택할 수 있습니다
        """)
        
        # 샘플 이미지가 있다면 표시
        try:
            sample_image = cv2.imread("sample/face.png")
            if sample_image is not None:
                sample_rgb = cv2.cvtColor(sample_image, cv2.COLOR_BGR2RGB)
                st.subheader("📷 샘플 이미지")
                st.image(sample_rgb, caption="sample/face.png", width=400)
        except:
            pass

# 푸터
st.markdown("---")
st.markdown("🎭 **Virtual Makeup Studio** - MediaPipe와 OpenCV를 활용한 실시간 가상 메이크업") 