"""
향상된 Streamlit 메이크업 앱 - reference files 기반 구현
MediaPipe 랜드마크를 정확히 사용하는 고품질 메이크업 애플리케이션
"""
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.enhanced_makeup_engine import EnhancedMakeupEngine, get_default_colors

# 페이지 설정
st.set_page_config(
    page_title="🎭 Enhanced Virtual Makeup Studio",
    page_icon="💄",
    layout="wide"
)

# 제목
st.title("🎭 Enhanced Virtual Makeup Studio")
st.markdown("**MediaPipe 기반 정확한 랜드마크를 사용한 고품질 가상 메이크업!**")

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
        
        # 메이크업 모드 선택
        st.subheader("🎯 메이크업 모드")
        makeup_mode = st.radio(
            "메이크업 적용 방식 선택:",
            ["기본 메이크업", "고급 커스텀"],
            help="기본 메이크업은 reference files와 동일한 방식, 고급 커스텀은 세밀한 조정 가능"
        )
        
        if makeup_mode == "기본 메이크업":
            # 기본 메이크업 설정 (reference files와 동일)
            st.subheader("💄 기본 색상 설정")
            
            # 입술 색상
            lip_color = st.color_picker("💋 입술 색상", "#FF0000", key="basic_lip_color")
            lip_r, lip_g, lip_b = tuple(int(lip_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 아이라이너 색상  
            eyeliner_color = st.color_picker("👁️ 아이라이너 색상", "#8B0000", key="basic_eyeliner_color")
            eyeliner_r, eyeliner_g, eyeliner_b = tuple(int(eyeliner_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 아이섀도 색상
            eyeshadow_color = st.color_picker("🎨 아이섀도 색상", "#006400", key="basic_eyeshadow_color")
            eyeshadow_r, eyeshadow_g, eyeshadow_b = tuple(int(eyeshadow_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 눈썹 색상
            eyebrow_color = st.color_picker("🤎 눈썹 색상", "#8B4513", key="basic_eyebrow_color")
            eyebrow_r, eyebrow_g, eyebrow_b = tuple(int(eyebrow_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 기본 강도 설정
            st.subheader("⚡ 메이크업 강도")
            mask_alpha = st.slider(
                "🔀 전체 메이크업 강도", 
                min_value=0.0, 
                max_value=1.0, 
                value=0.2, 
                step=0.05,
                help="reference files와 동일한 기본값 0.2",
                key="basic_mask_alpha"
            )
            
            # 색상 맵 생성 (BGR 형식)
            colors_map = {
                "LIP_UPPER": [lip_b, lip_g, lip_r],
                "LIP_LOWER": [lip_b, lip_g, lip_r],
                "EYELINER_LEFT": [eyeliner_b, eyeliner_g, eyeliner_r],
                "EYELINER_RIGHT": [eyeliner_b, eyeliner_g, eyeliner_r],
                "EYESHADOW_LEFT": [eyeshadow_b, eyeshadow_g, eyeshadow_r],
                "EYESHADOW_RIGHT": [eyeshadow_b, eyeshadow_g, eyeshadow_r],
                "EYEBROW_LEFT": [eyebrow_b, eyebrow_g, eyebrow_r],
                "EYEBROW_RIGHT": [eyebrow_b, eyebrow_g, eyebrow_r],
            }
            
            # 강도 맵 (기본 모드에서는 모두 1.0)
            intensity_map = {
                "LIP_UPPER": 1.0,
                "LIP_LOWER": 1.0,
                "EYELINER_LEFT": 1.0,
                "EYELINER_RIGHT": 1.0,
                "EYESHADOW_LEFT": 1.0,
                "EYESHADOW_RIGHT": 1.0,
                "EYEBROW_LEFT": 1.0,
                "EYEBROW_RIGHT": 1.0,
            }
            
            # 기본 블러 설정
            blur_strength = 7
            blur_sigma = 4
            
        else:  # 고급 커스텀 모드
            st.subheader("💄 고급 색상 조정")
            
            # 입술 색상
            lip_color = st.color_picker("💋 입술 색상", "#FF0000", key="advanced_lip_color")
            lip_r, lip_g, lip_b = tuple(int(lip_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 아이라이너 색상  
            eyeliner_color = st.color_picker("👁️ 아이라이너 색상", "#8B0000", key="advanced_eyeliner_color")
            eyeliner_r, eyeliner_g, eyeliner_b = tuple(int(eyeliner_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 아이섀도 색상
            eyeshadow_color = st.color_picker("🎨 아이섀도 색상", "#006400", key="advanced_eyeshadow_color")
            eyeshadow_r, eyeshadow_g, eyeshadow_b = tuple(int(eyeshadow_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 눈썹 색상
            eyebrow_color = st.color_picker("🤎 눈썹 색상", "#8B4513", key="advanced_eyebrow_color")
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
                key="advanced_mask_alpha"
            )
            
            # 블러 강도
            blur_strength = st.slider(
                "🌫️ 블러 강도", 
                min_value=1, 
                max_value=21, 
                value=7, 
                step=2,
                help="메이크업의 부드러움을 조정합니다 (홀수만 가능)",
                key="advanced_blur_strength"
            )
            
            # 블러 시그마
            blur_sigma = st.slider(
                "🎯 블러 시그마", 
                min_value=1, 
                max_value=10, 
                value=4, 
                step=1,
                help="블러의 확산 정도를 조정합니다",
                key="advanced_blur_sigma"
            )
            
            # 개별 부위 강도 조정
            st.subheader("🎚️ 부위별 강도")
            
            lip_intensity = st.slider("💋 입술 강도", 0.0, 1.0, 1.0, 0.1, key="advanced_lip_intensity")
            eyeliner_intensity = st.slider("👁️ 아이라이너 강도", 0.0, 1.0, 1.0, 0.1, key="advanced_eyeliner_intensity")
            eyeshadow_intensity = st.slider("🎨 아이섀도 강도", 0.0, 1.0, 1.0, 0.1, key="advanced_eyeshadow_intensity")
            eyebrow_intensity = st.slider("🤎 눈썹 강도", 0.0, 1.0, 1.0, 0.1, key="advanced_eyebrow_intensity")
            
            # 색상 맵 생성 (BGR 형식)
            colors_map = {
                "LIP_UPPER": [lip_b, lip_g, lip_r],
                "LIP_LOWER": [lip_b, lip_g, lip_r],
                "EYELINER_LEFT": [eyeliner_b, eyeliner_g, eyeliner_r],
                "EYELINER_RIGHT": [eyeliner_b, eyeliner_g, eyeliner_r],
                "EYESHADOW_LEFT": [eyeshadow_b, eyeshadow_g, eyeshadow_r],
                "EYESHADOW_RIGHT": [eyeshadow_b, eyeshadow_g, eyeshadow_r],
                "EYEBROW_LEFT": [eyebrow_b, eyebrow_g, eyebrow_r],
                "EYEBROW_RIGHT": [eyebrow_b, eyebrow_g, eyebrow_r],
            }
            
            # 강도 맵
            intensity_map = {
                "LIP_UPPER": lip_intensity,
                "LIP_LOWER": lip_intensity,
                "EYELINER_LEFT": eyeliner_intensity,
                "EYELINER_RIGHT": eyeliner_intensity,
                "EYESHADOW_LEFT": eyeshadow_intensity,
                "EYESHADOW_RIGHT": eyeshadow_intensity,
                "EYEBROW_LEFT": eyebrow_intensity,
                "EYEBROW_RIGHT": eyebrow_intensity,
            }
        
        # 고급 옵션
        st.subheader("🔧 고급 옵션")
        
        show_landmarks = st.checkbox("🔍 랜드마크 표시", value=False, key="show_landmarks")
        show_original = st.checkbox("📸 원본 이미지 표시", value=True, key="show_original")
        show_mask = st.checkbox("🎨 마스크 이미지 표시", value=True, key="show_mask")
        
        # 기본 색상 리셋 버튼
        if st.button("🔄 기본 색상으로 리셋"):
            st.rerun()

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
        
        # 메이크업 엔진 초기화
        try:
            makeup_engine = EnhancedMakeupEngine()
            
            if makeup_mode == "기본 메이크업":
                # 기본 메이크업 적용 (reference files 방식)
                result_image = makeup_engine.apply_simple_makeup(image_bgr, colors_map)
                
                # 마스크 생성 (표시용)
                mask = np.zeros_like(image_bgr)
                face_landmarks = makeup_engine.read_landmarks(image_bgr)
                
                face_elements = [
                    "LIP_LOWER", "LIP_UPPER",
                    "EYEBROW_LEFT", "EYEBROW_RIGHT",
                    "EYELINER_LEFT", "EYELINER_RIGHT",
                    "EYESHADOW_LEFT", "EYESHADOW_RIGHT",
                ]
                
                face_connections = [makeup_engine.get_available_landmarks()[idx] for idx in face_elements]
                colors = [colors_map[idx] for idx in face_elements]
                
                mask = makeup_engine.add_mask(mask, face_landmarks, face_connections, colors)
                face_detected = len(face_landmarks) > 0
                
                # 랜드마크 표시
                if show_landmarks and face_landmarks:
                    result_image = makeup_engine.draw_landmarks(result_image, face_landmarks)
                
            else:
                # 고급 메이크업 적용
                result_image, mask, face_detected = makeup_engine.apply_makeup(
                    image_bgr, colors_map, intensity_map, 
                    mask_alpha, blur_strength, blur_sigma, show_landmarks
                )
            
            # BGR을 RGB로 변환 (Streamlit 표시용)
            result_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
            mask_rgb = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
            
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
                    st.image(img, use_container_width=True)
            
            # 상태 표시
            if face_detected:
                st.success("✅ 얼굴이 성공적으로 감지되었습니다!")
                
                # 메이크업 정보 표시
                st.info(f"🎯 적용된 모드: {makeup_mode}")
                if makeup_mode == "기본 메이크업":
                    st.info("📋 Reference files와 동일한 방식으로 메이크업이 적용되었습니다.")
                
                # 다운로드 버튼
                result_pil = Image.fromarray(result_rgb)
                buf = io.BytesIO()
                result_pil.save(buf, format='PNG')
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="💾 결과 이미지 다운로드",
                    data=byte_im,
                    file_name=f"enhanced_makeup_result_{makeup_mode.replace(' ', '_').lower()}.png",
                    mime="image/png",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ 얼굴을 감지하지 못했습니다. 다른 이미지를 시도해보세요.")
        
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            st.info("이미지 처리 중 문제가 발생했습니다. 다른 이미지를 시도해보세요.")
            
            # 디버깅 정보
            with st.expander("🔍 디버깅 정보"):
                st.text(f"오류 타입: {type(e).__name__}")
                st.text(f"오류 메시지: {str(e)}")
                st.text(f"이미지 형태: {image_array.shape if 'image_array' in locals() else 'N/A'}")
    
    else:
        # 이미지 업로드 안내
        st.info("👆 왼쪽에서 이미지를 업로드하세요!")
        
        # 사용 방법 안내
        st.markdown("""
        ### 📖 사용 방법:
        
        1. **📁 이미지 업로드**: 왼쪽에서 얼굴이 포함된 이미지를 업로드하세요
        2. **🎯 모드 선택**: 
           - **기본 메이크업**: Reference files와 동일한 방식 (간단하고 안정적)
           - **고급 커스텀**: 세밀한 조정 가능 (부위별 강도, 블러 등)
        3. **🎨 색상 조정**: 각 메이크업 부위의 색상을 색상 선택기로 조정하세요
        4. **⚡ 강도 조정**: 메이크업 강도를 슬라이더로 조정하세요
        5. **💾 다운로드**: 결과가 마음에 들면 이미지를 다운로드하세요
        
        ### 🎭 지원하는 메이크업 부위:
        - 💋 **입술**: 상하 입술에 립스틱 색상 적용
        - 👁️ **아이라이너**: 눈 윤곽에 아이라이너 적용
        - 🎨 **아이섀도**: 눈두덩이에 아이섀도 적용
        - 🤎 **눈썹**: 눈썹에 색상 적용
        
        ### 🔧 기술적 특징:
        - **MediaPipe 기반**: 정확한 468개 얼굴 랜드마크 사용
        - **Reference Files 호환**: 검증된 알고리즘 적용
        - **실시간 처리**: 설정 변경 시 즉시 결과 업데이트
        - **고품질 렌더링**: 자연스러운 메이크업 효과
        
        ### 💡 팁:
        - **기본 모드**는 빠르고 안정적인 결과를 제공합니다
        - **고급 모드**는 세밀한 조정이 가능하지만 처리 시간이 더 걸릴 수 있습니다
        - 랜드마크 표시로 얼굴 인식 정확도를 확인할 수 있습니다
        - 마스크 이미지로 메이크업이 적용되는 영역을 확인할 수 있습니다
        """)

# 푸터
st.markdown("---")
st.markdown("🎭 **Enhanced Virtual Makeup Studio** - MediaPipe와 Reference Files 기반 고품질 가상 메이크업")
st.markdown("💡 **개선사항**: 정확한 랜드마크 사용, 향상된 마스킹 알고리즘, 자연스러운 블렌딩")