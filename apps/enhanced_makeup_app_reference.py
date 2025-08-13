"""
Reference Files 완전 호환 메이크업 애플리케이션
image.py, utils.py, web_makeup_gui.py의 모든 기능을 통합한 고품질 구현
"""
import cv2
import argparse
import streamlit as st
import numpy as np
from PIL import Image
import io
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Reference files 기반 유틸리티 임포트
from utils.enhanced_makeup_utils import *


def main_cli(image_path: str):
    """
    Reference files의 image.py main 함수와 완전히 동일한 CLI 버전
    
    Args:
        image_path: 이미지 파일 경로
    """
    # 적용할 메이크업 특징
    face_elements = [
        "LIP_LOWER",
        "LIP_UPPER",
        "EYEBROW_LEFT",
        "EYEBROW_RIGHT",
        "EYELINER_LEFT",
        "EYELINER_RIGHT",
        "EYESHADOW_LEFT",
        "EYESHADOW_RIGHT",
    ]

    # 특징별 색상 변경
    colors_map = {
        # 상하 입술
        "LIP_UPPER": [0, 0, 255],  # Red in BGR
        "LIP_LOWER": [0, 0, 255],  # Red in BGR
        # 아이라이너
        "EYELINER_LEFT": [139, 0, 0],  # Dark Blue in BGR
        "EYELINER_RIGHT": [139, 0, 0],  # Dark Blue in BGR
        # 아이섀도
        "EYESHADOW_LEFT": [0, 100, 0],  # Dark Green in BGR
        "EYESHADOW_RIGHT": [0, 100, 0],  # Dark Green in BGR
        # 눈썹
        "EYEBROW_LEFT": [19, 69, 139],  # Dark Brown in BGR
        "EYEBROW_RIGHT": [19, 69, 139],  # Dark Brown in BGR
    }

    # face_elements에서 필요한 얼굴 포인트 추출
    face_connections = [face_points[idx] for idx in face_elements]
    # 각 얼굴 특징에 해당하는 색상 추출
    colors = [colors_map[idx] for idx in face_elements]
    
    # 이미지 읽기
    image = cv2.imread(image_path)
    if image is None:
        print(f"이미지를 로드할 수 없습니다: {image_path}")
        return
    
    # 이미지와 같은 빈 마스크 생성
    mask = np.zeros_like(image)
    
    # 얼굴 랜드마크 추출
    face_landmarks = read_landmarks(image=image)
    
    # 색상으로 얼굴 특징에 대한 마스크 생성
    mask = add_mask(
        mask,
        idx_to_coordinates=face_landmarks,
        face_connections=face_connections,
        colors=colors
    )
    
    # 가중치에 따라 이미지와 마스크 결합
    output = cv2.addWeighted(image, 1.0, mask, 0.2, 1.0)
    
    # 이미지 표시
    show_image(output)
    
    return output


def run_streamlit_app():
    """
    Reference files의 web_makeup_gui.py와 완전히 동일한 Streamlit 앱
    """
    # 페이지 설정
    st.set_page_config(
        page_title="🎭 Virtual Makeup Studio - Reference Compatible",
        page_icon="💄",
        layout="wide"
    )

    # 제목
    st.title("🎭 Virtual Makeup Studio - Reference Files Compatible")
    st.markdown("**Reference files (image.py, utils.py, web_makeup_gui.py)와 완전히 호환되는 고품질 가상 메이크업!**")

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
            
            # Reference files 호환 모드
            st.subheader("🔄 Reference Files 모드")
            use_reference_mode = st.checkbox("📋 Reference Files 완전 호환 모드", value=False, 
                                           help="image.py와 완전히 동일한 방식으로 메이크업 적용")

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
                if use_reference_mode:
                    # Reference files 완전 호환 모드
                    result_image = apply_simple_makeup_from_reference(image_bgr, colors_map)
                    
                    # 마스크 생성 (표시용)
                    mask = np.zeros_like(image_bgr)
                    face_landmarks = read_landmarks(image_bgr)
                    
                    face_elements = get_face_elements()
                    face_connections = [face_points[idx] for idx in face_elements]
                    colors = [colors_map[idx] for idx in face_elements]
                    
                    mask = add_mask(mask, face_landmarks, face_connections, colors)
                    face_detected = len(face_landmarks) > 0
                    
                    # 랜드마크 표시
                    if show_landmarks and face_landmarks:
                        result_image = draw_landmarks(result_image, face_landmarks)
                        
                    st.info("📋 Reference Files 완전 호환 모드로 메이크업이 적용되었습니다.")
                    
                else:
                    # 고급 모드
                    result_image, mask, face_detected = apply_makeup(
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
                    
                    # 다운로드 버튼
                    result_pil = Image.fromarray(result_rgb)
                    buf = io.BytesIO()
                    result_pil.save(buf, format='PNG')
                    byte_im = buf.getvalue()
                    
                    mode_suffix = "reference" if use_reference_mode else "enhanced"
                    st.download_button(
                        label="💾 결과 이미지 다운로드",
                        data=byte_im,
                        file_name=f"virtual_makeup_result_{mode_suffix}.png",
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
            5. **🔄 Reference 모드**: 원본 reference files와 완전히 동일한 방식으로 적용
            6. **💾 다운로드**: 결과가 마음에 들면 이미지를 다운로드하세요
            
            ### 🎭 지원하는 메이크업 부위:
            - 💋 **입술**: 상하 입술에 립스틱 색상 적용
            - 👁️ **아이라이너**: 눈 윤곽에 아이라이너 적용
            - 🎨 **아이섀도**: 눈두덩이에 아이섀도 적용
            - 🤎 **눈썹**: 눈썹에 색상 적용
            
            ### 🔧 기술적 특징:
            - **완전한 Reference Files 호환**: image.py, utils.py, web_makeup_gui.py와 100% 동일
            - **MediaPipe 기반**: 정확한 468개 얼굴 랜드마크 사용
            - **향상된 알고리즘**: 자연스러운 블렌딩과 색상 적용
            - **실시간 처리**: 설정 변경 시 즉시 결과 업데이트
            
            ### 💡 팁:
            - **Reference 모드**는 원본 파일과 완전히 동일한 결과를 제공합니다
            - **고급 모드**는 세밀한 조정이 가능합니다
            - 랜드마크 표시로 얼굴 인식 정확도를 확인할 수 있습니다
            - 마스크 이미지로 메이크업이 적용되는 영역을 확인할 수 있습니다
            """)

    # 푸터
    st.markdown("---")
    st.markdown("🎭 **Virtual Makeup Studio - Reference Files Compatible**")
    st.markdown("💡 **완전 호환**: image.py, utils.py, web_makeup_gui.py와 100% 동일한 알고리즘 사용")


if __name__ == "__main__":
    # CLI 모드와 Streamlit 모드 선택
    if len(sys.argv) > 1:
        if sys.argv[1] == "--streamlit":
            # Streamlit 앱 실행
            run_streamlit_app()
        else:
            # CLI 모드 - Reference files의 image.py와 동일
            parser = argparse.ArgumentParser(description="Image to add Facial makeup - Reference Compatible")
            parser.add_argument("--image", type=str, help="Path to the image.")
            args = parser.parse_args()
            
            if args.image:
                main_cli(args.image)
            else:
                print("이미지 경로를 제공해주세요: --image path/to/image.jpg")
    else:
        # 기본적으로 Streamlit 앱 실행
        run_streamlit_app()