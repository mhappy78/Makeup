"""
간단한 웹 메이크업 인터페이스 - Flask 기반
Streamlit 대신 사용할 수 있는 간단한 웹 인터페이스
"""
try:
    from flask import Flask, render_template, request, send_file, jsonify
    import os
    import cv2
    import numpy as np
    from werkzeug.utils import secure_filename
    import base64
    import io
    from PIL import Image
    import sys
    
    # 프로젝트 루트 디렉토리를 Python 경로에 추가
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from utils.enhanced_makeup_utils import *
    
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask가 설치되지 않았습니다. pip install flask로 설치하세요.")


def create_simple_html_interface():
    """간단한 HTML 인터페이스 생성"""
    html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎭 Virtual Makeup Studio</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
        }
        .controls {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .results {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .color-input {
            width: 100%;
            height: 40px;
            border: none;
            border-radius: 5px;
            margin: 10px 0;
        }
        .slider {
            width: 100%;
            margin: 10px 0;
        }
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
        }
        .button:hover {
            opacity: 0.9;
        }
        .file-input {
            margin: 15px 0;
            padding: 10px;
            border: 2px dashed #ccc;
            border-radius: 5px;
            text-align: center;
        }
        .image-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .image-item {
            text-align: center;
        }
        .image-item img {
            max-width: 100%;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .preset-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎭 Virtual Makeup Studio</h1>
        <p>Reference Files 기반 고품질 가상 메이크업</p>
    </div>
    
    <div class="container">
        <div class="controls">
            <h2>🎨 메이크업 컨트롤</h2>
            
            <div class="file-input">
                <h3>📁 이미지 업로드</h3>
                <p>얼굴이 포함된 이미지를 선택하세요</p>
                <input type="file" id="imageInput" accept="image/*">
            </div>
            
            <h3>💄 색상 설정</h3>
            <label>💋 입술 색상:</label>
            <input type="color" id="lipColor" class="color-input" value="#FF0000">
            
            <label>👁️ 아이라이너 색상:</label>
            <input type="color" id="eyelinerColor" class="color-input" value="#8B0000">
            
            <label>🎨 아이섀도 색상:</label>
            <input type="color" id="eyeshadowColor" class="color-input" value="#006400">
            
            <label>🤎 눈썹 색상:</label>
            <input type="color" id="eyebrowColor" class="color-input" value="#8B4513">
            
            <h3>⚡ 강도 설정</h3>
            <label>🔀 메이크업 강도: <span id="alphaValue">0.3</span></label>
            <input type="range" id="maskAlpha" class="slider" min="0" max="1" step="0.05" value="0.3">
            
            <label>🌫️ 블러 강도: <span id="blurValue">7</span></label>
            <input type="range" id="blurStrength" class="slider" min="1" max="21" step="2" value="7">
            
            <h3>🎭 프리셋 스타일</h3>
            <div class="preset-buttons">
                <button class="button" onclick="applyPreset('natural')">자연스러운</button>
                <button class="button" onclick="applyPreset('dramatic')">드라마틱</button>
                <button class="button" onclick="applyPreset('romantic')">로맨틱</button>
                <button class="button" onclick="applyPreset('basic')">기본</button>
            </div>
            
            <button class="button" onclick="applyMakeup()" style="width: 100%; margin-top: 20px;">
                🎨 메이크업 적용
            </button>
        </div>
        
        <div class="results">
            <h2>📺 메이크업 결과</h2>
            
            <div class="info-box">
                <h3>📖 사용 방법:</h3>
                <ol>
                    <li>왼쪽에서 이미지를 업로드하세요</li>
                    <li>색상과 강도를 조정하세요</li>
                    <li>프리셋 스타일을 선택하거나 커스텀 설정을 사용하세요</li>
                    <li>"메이크업 적용" 버튼을 클릭하세요</li>
                </ol>
            </div>
            
            <div id="imageGallery" class="image-gallery">
                <div class="image-item">
                    <h4>📸 샘플 이미지</h4>
                    <img src="demo_sample_face.jpg" alt="샘플 얼굴" onerror="this.style.display='none'">
                    <p>데모용 샘플 이미지</p>
                </div>
                
                <div class="image-item">
                    <h4>🎭 기본 메이크업</h4>
                    <img src="test_basic_makeup.jpg" alt="기본 메이크업" onerror="this.style.display='none'">
                    <p>Reference Files 방식</p>
                </div>
                
                <div class="image-item">
                    <h4>💋 빨간 립스틱</h4>
                    <img src="test_red_lips_makeup.jpg" alt="빨간 립스틱" onerror="this.style.display='none'">
                    <p>드라마틱 스타일</p>
                </div>
                
                <div class="image-item">
                    <h4>🌸 핑크 메이크업</h4>
                    <img src="test_pink_makeup.jpg" alt="핑크 메이크업" onerror="this.style.display='none'">
                    <p>로맨틱 스타일</p>
                </div>
            </div>
            
            <div class="info-box" style="margin-top: 30px;">
                <h3>🔧 기술적 특징:</h3>
                <ul>
                    <li><strong>MediaPipe 기반</strong>: 정확한 468개 얼굴 랜드마크 사용</li>
                    <li><strong>Reference Files 호환</strong>: 검증된 알고리즘 적용</li>
                    <li><strong>자연스러운 블렌딩</strong>: 고품질 색상 적용</li>
                    <li><strong>실시간 처리</strong>: 빠른 메이크업 적용</li>
                </ul>
            </div>
        </div>
    </div>
    
    <script>
        // 슬라이더 값 업데이트
        document.getElementById('maskAlpha').oninput = function() {
            document.getElementById('alphaValue').textContent = this.value;
        }
        
        document.getElementById('blurStrength').oninput = function() {
            document.getElementById('blurValue').textContent = this.value;
        }
        
        // 프리셋 적용
        function applyPreset(preset) {
            const presets = {
                'natural': {
                    lip: '#B450B4',
                    eyeliner: '#8B4513',
                    eyeshadow: '#DEB887',
                    eyebrow: '#8B7355'
                },
                'dramatic': {
                    lip: '#DC143C',
                    eyeliner: '#000000',
                    eyeshadow: '#800080',
                    eyebrow: '#2F4F4F'
                },
                'romantic': {
                    lip: '#FFB6C1',
                    eyeliner: '#CD853F',
                    eyeshadow: '#F5DEB3',
                    eyebrow: '#D2B48C'
                },
                'basic': {
                    lip: '#FF0000',
                    eyeliner: '#8B0000',
                    eyeshadow: '#006400',
                    eyebrow: '#8B4513'
                }
            };
            
            if (presets[preset]) {
                document.getElementById('lipColor').value = presets[preset].lip;
                document.getElementById('eyelinerColor').value = presets[preset].eyeliner;
                document.getElementById('eyeshadowColor').value = presets[preset].eyeshadow;
                document.getElementById('eyebrowColor').value = presets[preset].eyebrow;
            }
        }
        
        // 메이크업 적용 (실제로는 Python 스크립트 실행)
        function applyMakeup() {
            alert('메이크업 적용 기능은 Python 스크립트로 실행됩니다.\\n\\n' +
                  '터미널에서 다음 명령을 실행하세요:\\n' +
                  'python simple_makeup_test.py\\n\\n' +
                  '또는 CLI 방식으로:\\n' +
                  'python enhanced_makeup_app_reference.py --image your_image.jpg');
        }
        
        // 이미지 업로드 처리
        document.getElementById('imageInput').onchange = function(event) {
            const file = event.target.files[0];
            if (file) {
                alert('이미지가 선택되었습니다: ' + file.name + '\\n\\n' +
                      '실제 처리를 위해서는 Python 스크립트를 사용하세요.');
            }
        }
    </script>
</body>
</html>
"""
    
    with open("makeup_interface.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML 인터페이스 생성: makeup_interface.html")
    print("💡 웹 브라우저에서 makeup_interface.html 파일을 열어보세요!")


def run_flask_app():
    """Flask 앱 실행 (Flask가 설치된 경우)"""
    if not FLASK_AVAILABLE:
        print("❌ Flask가 설치되지 않았습니다.")
        print("💡 pip install flask로 설치하거나 HTML 인터페이스를 사용하세요.")
        return
    
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # 업로드 폴더 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    @app.route('/')
    def index():
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Virtual Makeup Studio</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .upload-area { border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; }
                .controls { background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
                .color-input { width: 50px; height: 30px; border: none; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>🎭 Virtual Makeup Studio</h1>
            <div class="upload-area">
                <h3>이미지 업로드</h3>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept="image/*" required>
                    <br><br>
                    <input type="submit" value="업로드" class="button">
                </form>
            </div>
            
            <div class="controls">
                <h3>메이크업 설정</h3>
                <p>💋 입술: <input type="color" class="color-input" value="#FF0000"></p>
                <p>👁️ 아이라이너: <input type="color" class="color-input" value="#8B0000"></p>
                <p>🎨 아이섀도: <input type="color" class="color-input" value="#006400"></p>
                <p>🤎 눈썹: <input type="color" class="color-input" value="#8B4513"></p>
            </div>
            
            <div>
                <h3>📁 생성된 결과 이미지들</h3>
                <p><a href="/image/test_basic_makeup.jpg">기본 메이크업</a></p>
                <p><a href="/image/test_red_lips_makeup.jpg">빨간 립스틱</a></p>
                <p><a href="/image/test_pink_makeup.jpg">핑크 메이크업</a></p>
                <p><a href="/image/test_makeup_comparison.jpg">비교 이미지</a></p>
            </div>
        </body>
        </html>
        """)
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return '파일이 선택되지 않았습니다.'
        
        file = request.files['file']
        if file.filename == '':
            return '파일이 선택되지 않았습니다.'
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 메이크업 적용
            try:
                result = apply_simple_makeup_from_reference(filepath)
                result_path = f"result_{filename}"
                cv2.imwrite(result_path, result)
                
                return f"""
                <h2>메이크업 적용 완료!</h2>
                <p>결과 이미지: <a href="/image/{result_path}">{result_path}</a></p>
                <p><a href="/">다시 시도</a></p>
                """
            except Exception as e:
                return f"오류 발생: {str(e)}"
    
    @app.route('/image/<filename>')
    def serve_image(filename):
        try:
            return send_file(filename)
        except:
            return "이미지를 찾을 수 없습니다."
    
    print("🚀 Flask 앱 시작...")
    print("💡 브라우저에서 http://localhost:5000 을 열어보세요!")
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    print("🎭 웹 메이크업 인터페이스")
    print("=" * 40)
    
    # HTML 인터페이스 생성
    create_simple_html_interface()
    
    # Flask 앱 실행 시도
    if FLASK_AVAILABLE:
        print("\n🌐 Flask 웹 서버를 시작하시겠습니까? (y/n): ", end="")
        try:
            choice = input().lower()
            if choice == 'y':
                run_flask_app()
        except:
            pass
    
    print("\n💡 사용 방법:")
    print("1. makeup_interface.html 파일을 웹 브라우저에서 열기")
    print("2. 또는 python simple_makeup_test.py 실행")
    print("3. 또는 python enhanced_makeup_app_reference.py --image image.jpg")