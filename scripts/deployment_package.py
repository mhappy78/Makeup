"""
배포 패키지 생성 및 검증 도구
Task 10: 최종 통합 및 배포 준비
"""
import os
import sys
import shutil
import zipfile
import json
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class PackageInfo:
    """패키지 정보"""
    name: str
    version: str
    description: str
    author: str
    created_at: str
    file_count: int
    total_size: int
    checksum: str


@dataclass
class DeploymentConfig:
    """배포 설정"""
    target_platform: str
    python_version: str
    dependencies: List[str]
    entry_point: str
    data_files: List[str]
    exclude_patterns: List[str]


class DeploymentPackager:
    """배포 패키지 생성기"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.package_name = "natural-makeup-surgery-simulation"
        self.version = "1.0.0"
        
        # 기본 배포 설정
        self.deployment_config = DeploymentConfig(
            target_platform="cross-platform",
            python_version="3.8+",
            dependencies=[
                "opencv-python==4.8.1.78",
                "mediapipe==0.10.7",
                "Pillow==10.1.0",
                "numpy==1.24.3",
                "streamlit==1.28.1",
                "customtkinter==5.2.0"
            ],
            entry_point="ui/main_interface.py",
            data_files=[
                "models/",
                "doc/",
                "gallery/",
                "README.md",
                "requirements.txt"
            ],
            exclude_patterns=[
                "__pycache__/",
                "*.pyc",
                "*.pyo",
                ".git/",
                ".vscode/",
                "*.log",
                "test_*.py",
                "debug_*.py",
                "*.jpg",
                "*.png",
                "*.gif",
                ".gradle/",
                "build/",
                "app/",
                "gradle/",
                "*.bat",
                "gradlew"
            ]
        )
    
    def create_package_structure(self, output_dir: str) -> str:
        """패키지 구조 생성"""
        package_dir = os.path.join(output_dir, self.package_name)
        
        # 패키지 디렉토리 생성
        os.makedirs(package_dir, exist_ok=True)
        
        # 소스 파일 복사
        self._copy_source_files(package_dir)
        
        # 설정 파일 생성
        self._create_config_files(package_dir)
        
        # 실행 스크립트 생성
        self._create_launch_scripts(package_dir)
        
        # 문서 생성
        self._create_documentation(package_dir)
        
        return package_dir
    
    def _copy_source_files(self, package_dir: str):
        """소스 파일 복사"""
        print("소스 파일 복사 중...")
        
        # 핵심 디렉토리 복사
        core_dirs = ["engines", "models", "ui", "utils"]
        
        for dir_name in core_dirs:
            src_dir = os.path.join(self.project_root, dir_name)
            dst_dir = os.path.join(package_dir, dir_name)
            
            if os.path.exists(src_dir):
                shutil.copytree(src_dir, dst_dir, ignore=self._ignore_patterns)
                print(f"  복사됨: {dir_name}/")
        
        # 개별 파일 복사
        individual_files = [
            "requirements.txt",
            "README.md",
            "quality_assurance_runner.py",
            "final_integration_test.py"
        ]
        
        for file_name in individual_files:
            src_file = os.path.join(self.project_root, file_name)
            dst_file = os.path.join(package_dir, file_name)
            
            if os.path.exists(src_file):
                shutil.copy2(src_file, dst_file)
                print(f"  복사됨: {file_name}")
        
        # 데모 파일 복사 (선택적)
        demo_files = [
            "demo_makeup_controls.py",
            "demo_surgery_controls.py"
        ]
        
        demo_dir = os.path.join(package_dir, "demos")
        os.makedirs(demo_dir, exist_ok=True)
        
        for file_name in demo_files:
            src_file = os.path.join(self.project_root, file_name)
            dst_file = os.path.join(demo_dir, file_name)
            
            if os.path.exists(src_file):
                shutil.copy2(src_file, dst_file)
                print(f"  복사됨: demos/{file_name}")
    
    def _ignore_patterns(self, dir_path: str, names: List[str]) -> List[str]:
        """무시할 패턴 필터링"""
        ignored = []
        
        for name in names:
            for pattern in self.deployment_config.exclude_patterns:
                if pattern.endswith('/'):
                    # 디렉토리 패턴
                    if name == pattern.rstrip('/'):
                        ignored.append(name)
                        break
                elif '*' in pattern:
                    # 와일드카드 패턴
                    import fnmatch
                    if fnmatch.fnmatch(name, pattern):
                        ignored.append(name)
                        break
                else:
                    # 정확한 매치
                    if name == pattern:
                        ignored.append(name)
                        break
        
        return ignored
    
    def _create_config_files(self, package_dir: str):
        """설정 파일 생성"""
        print("설정 파일 생성 중...")
        
        # setup.py 생성
        setup_content = f'''"""
자연스러운 메이크업 & 성형 시뮬레이션 설치 스크립트
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="{self.package_name}",
    version="{self.version}",
    author="Natural Beauty Simulation Team",
    author_email="team@naturalbeauty.ai",
    description="AI-based Real-time Natural Makeup and Surgery Simulation Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/naturalbeauty/makeup-surgery-simulation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={{
        "console_scripts": [
            "natural-beauty=ui.main_interface:main",
        ],
    }},
    include_package_data=True,
    package_data={{
        "": ["*.md", "*.txt", "*.json"],
    }},
)
'''
        
        with open(os.path.join(package_dir, "setup.py"), "w", encoding="utf-8") as f:
            f.write(setup_content)
        
        # MANIFEST.in 생성
        manifest_content = """
include README.md
include requirements.txt
include LICENSE
recursive-include models *.py
recursive-include engines *.py
recursive-include ui *.py
recursive-include utils *.py
recursive-include demos *.py
recursive-exclude * __pycache__
recursive-exclude * *.pyc
recursive-exclude * *.pyo
"""
        
        with open(os.path.join(package_dir, "MANIFEST.in"), "w", encoding="utf-8") as f:
            f.write(manifest_content.strip())
        
        # 배포 설정 JSON 생성
        config_file = os.path.join(package_dir, "deployment_config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self.deployment_config), f, ensure_ascii=False, indent=2)
        
        print("  생성됨: setup.py")
        print("  생성됨: MANIFEST.in")
        print("  생성됨: deployment_config.json")
    
    def _create_launch_scripts(self, package_dir: str):
        """실행 스크립트 생성"""
        print("실행 스크립트 생성 중...")
        
        # Windows 배치 스크립트
        batch_content = f'''@echo off
echo 자연스러운 메이크업 & 성형 시뮬레이션 시작 중...
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo 오류: Python이 설치되지 않았습니다.
    echo Python 3.8 이상을 설치해주세요.
    pause
    exit /b 1
)

REM 의존성 설치
echo 의존성 설치 중...
pip install -r requirements.txt

REM 애플리케이션 실행
echo 애플리케이션 시작...
python -m streamlit run ui/main_interface.py

pause
'''
        
        with open(os.path.join(package_dir, "start.bat"), "w", encoding="utf-8") as f:
            f.write(batch_content)
        
        # Linux/Mac 셸 스크립트
        shell_content = f'''#!/bin/bash
echo "자연스러운 메이크업 & 성형 시뮬레이션 시작 중..."
echo

# Python 설치 확인
if ! command -v python3 &> /dev/null; then
    echo "오류: Python3이 설치되지 않았습니다."
    echo "Python 3.8 이상을 설치해주세요."
    exit 1
fi

# 의존성 설치
echo "의존성 설치 중..."
pip3 install -r requirements.txt

# 애플리케이션 실행
echo "애플리케이션 시작..."
python3 -m streamlit run ui/main_interface.py

read -p "Press Enter to continue..."
'''
        
        shell_script_path = os.path.join(package_dir, "start.sh")
        with open(shell_script_path, "w", encoding="utf-8") as f:
            f.write(shell_content)
        
        # 실행 권한 부여 (Unix 계열)
        try:
            os.chmod(shell_script_path, 0o755)
        except:
            pass  # Windows에서는 무시
        
        # Python 실행 스크립트
        python_launcher = f'''#!/usr/bin/env python3
"""
자연스러운 메이크업 & 성형 시뮬레이션 런처
"""
import sys
import os
import subprocess

def main():
    """메인 실행 함수"""
    print("자연스러운 메이크업 & 성형 시뮬레이션")
    print("=" * 50)
    
    # 현재 디렉토리를 스크립트 위치로 변경
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 의존성 확인
    try:
        import streamlit
        import cv2
        import mediapipe
        import numpy
        from PIL import Image
    except ImportError as e:
        print(f"의존성 모듈이 없습니다: {{e}}")
        print("다음 명령으로 설치해주세요:")
        print("pip install -r requirements.txt")
        return 1
    
    # Streamlit 애플리케이션 실행
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "ui/main_interface.py"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\\n애플리케이션이 종료되었습니다.")
    except Exception as e:
        print(f"실행 중 오류 발생: {{e}}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open(os.path.join(package_dir, "launch.py"), "w", encoding="utf-8") as f:
            f.write(python_launcher)
        
        print("  생성됨: start.bat (Windows)")
        print("  생성됨: start.sh (Linux/Mac)")
        print("  생성됨: launch.py (Python)")
    
    def _create_documentation(self, package_dir: str):
        """문서 생성"""
        print("문서 생성 중...")
        
        # 설치 가이드 생성
        install_guide = f'''# 설치 가이드

## 시스템 요구사항

### 최소 요구사항
- **운영체제**: Windows 10, macOS 10.14, Ubuntu 18.04 이상
- **Python**: 3.8 이상
- **메모리**: 4GB RAM 이상
- **저장공간**: 2GB 이상
- **카메라**: 웹캠 (실시간 기능 사용시)

### 권장 요구사항
- **운영체제**: Windows 11, macOS 12, Ubuntu 20.04 이상
- **Python**: 3.9 이상
- **메모리**: 8GB RAM 이상
- **저장공간**: 5GB 이상
- **GPU**: CUDA 지원 GPU (성능 향상)

## 설치 방법

### 1. Python 설치
Python 3.8 이상이 설치되어 있는지 확인하세요.

```bash
python --version
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 애플리케이션 실행

#### Windows
```cmd
start.bat
```

#### Linux/Mac
```bash
./start.sh
```

#### Python 직접 실행
```bash
python launch.py
```

## 문제 해결

### 일반적인 문제

#### 1. Python을 찾을 수 없음
- Python이 PATH에 추가되어 있는지 확인
- `python3` 명령어 사용 시도

#### 2. 의존성 설치 실패
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

#### 3. 카메라 접근 권한
- 운영체제의 카메라 권한 설정 확인
- 다른 애플리케이션에서 카메라 사용 중인지 확인

#### 4. 성능 문제
- GPU 드라이버 최신 버전 설치
- 이미지 해상도 낮춤
- 프레임 스킵 설정 증가

### 로그 확인
애플리케이션 실행 시 콘솔에 출력되는 로그를 확인하여 문제를 진단할 수 있습니다.

## 지원

문제가 지속되면 다음 정보와 함께 문의해주세요:
- 운영체제 및 버전
- Python 버전
- 오류 메시지
- 실행 로그
'''
        
        with open(os.path.join(package_dir, "INSTALL.md"), "w", encoding="utf-8") as f:
            f.write(install_guide)
        
        # 사용자 가이드 생성
        user_guide = f'''# 사용자 가이드

## 시작하기

### 1. 애플리케이션 실행
설치 완료 후 실행 스크립트를 사용하여 애플리케이션을 시작하세요.

### 2. 이미지 업로드 또는 카메라 사용
- **이미지 업로드**: 사이드바에서 이미지 파일 선택
- **실시간 카메라**: 카메라 시작 버튼 클릭

### 3. 효과 적용
- **메이크업 탭**: 립스틱, 아이섀도, 블러셔 등 적용
- **성형 탭**: 코, 눈, 턱선 등 조절

## 주요 기능

### 메이크업 시뮬레이션
1. **립스틱**: 다양한 색상과 강도 조절
2. **아이섀도**: 여러 색상 조합과 스타일
3. **블러셔**: 자연스러운 볼터치 효과
4. **파운데이션**: 피부톤 보정
5. **아이라이너**: 눈매 강조

### 성형 시뮬레이션
1. **코 성형**: 높이, 폭, 각도 조절
2. **눈 성형**: 크기, 모양 변경
3. **턱선**: 각도와 길이 조절
4. **광대**: 높이와 폭 조절

### 이미지 관리
1. **저장**: 결과 이미지 고품질 저장
2. **비교**: 원본과 수정본 나란히 비교
3. **갤러리**: 여러 스타일 저장 및 관리

## 팁과 요령

### 자연스러운 결과를 위한 팁
1. **점진적 적용**: 강도를 낮게 시작하여 점진적으로 증가
2. **색상 조화**: 피부톤과 어울리는 색상 선택
3. **균형 유지**: 여러 효과 적용 시 전체적인 균형 고려

### 성능 최적화
1. **이미지 크기**: 너무 큰 이미지는 처리 시간 증가
2. **프레임 스킵**: 실시간 모드에서 성능 향상
3. **효과 조합**: 많은 효과 동시 적용 시 성능 저하 가능

## 단축키

- **Ctrl+S**: 이미지 저장
- **Ctrl+R**: 효과 리셋
- **Ctrl+Z**: 이전 상태로 되돌리기
- **Space**: 실시간 모드 일시정지/재개

## 문제 해결

### 얼굴 인식 문제
- 조명이 충분한 환경에서 사용
- 얼굴이 화면 중앙에 위치하도록 조정
- 머리카락이나 액세서리로 얼굴이 가려지지 않도록 주의

### 성능 문제
- 다른 애플리케이션 종료
- 이미지 해상도 조정
- 실시간 모드에서 프레임 스킵 증가
'''
        
        with open(os.path.join(package_dir, "USER_GUIDE.md"), "w", encoding="utf-8") as f:
            f.write(user_guide)
        
        # 라이선스 파일 생성
        license_content = '''MIT License

Copyright (c) 2024 Natural Beauty Simulation Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
        
        with open(os.path.join(package_dir, "LICENSE"), "w", encoding="utf-8") as f:
            f.write(license_content)
        
        print("  생성됨: INSTALL.md")
        print("  생성됨: USER_GUIDE.md")
        print("  생성됨: LICENSE")
    
    def create_zip_package(self, package_dir: str, output_path: str) -> str:
        """ZIP 패키지 생성"""
        print("ZIP 패키지 생성 중...")
        
        zip_filename = f"{self.package_name}-v{self.version}.zip"
        zip_path = os.path.join(output_path, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, os.path.dirname(package_dir))
                    zipf.write(file_path, arc_name)
        
        print(f"  생성됨: {zip_filename}")
        return zip_path
    
    def verify_package(self, package_dir: str) -> Dict[str, Any]:
        """패키지 검증"""
        print("패키지 검증 중...")
        
        verification_results = {
            'structure_check': True,
            'dependencies_check': True,
            'syntax_check': True,
            'file_integrity': True,
            'issues': []
        }
        
        # 1. 구조 검증
        required_files = [
            "setup.py",
            "requirements.txt",
            "README.md",
            "LICENSE",
            "INSTALL.md",
            "USER_GUIDE.md"
        ]
        
        required_dirs = [
            "engines",
            "models",
            "ui",
            "utils"
        ]
        
        for file_name in required_files:
            file_path = os.path.join(package_dir, file_name)
            if not os.path.exists(file_path):
                verification_results['structure_check'] = False
                verification_results['issues'].append(f"필수 파일 누락: {file_name}")
        
        for dir_name in required_dirs:
            dir_path = os.path.join(package_dir, dir_name)
            if not os.path.exists(dir_path):
                verification_results['structure_check'] = False
                verification_results['issues'].append(f"필수 디렉토리 누락: {dir_name}")
        
        # 2. 의존성 검증
        requirements_file = os.path.join(package_dir, "requirements.txt")
        if os.path.exists(requirements_file):
            try:
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    requirements = f.read().strip().split('\n')
                
                for req in requirements:
                    if req.strip() and not req.startswith('#'):
                        # 기본적인 형식 검증
                        if '==' not in req and '>=' not in req and '<=' not in req:
                            verification_results['dependencies_check'] = False
                            verification_results['issues'].append(f"의존성 버전 명시 필요: {req}")
            except Exception as e:
                verification_results['dependencies_check'] = False
                verification_results['issues'].append(f"requirements.txt 읽기 오류: {e}")
        
        # 3. Python 파일 구문 검증
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        compile(content, file_path, 'exec')
                    except SyntaxError as e:
                        verification_results['syntax_check'] = False
                        verification_results['issues'].append(f"구문 오류 ({file}): {e}")
                    except Exception as e:
                        verification_results['issues'].append(f"파일 검증 오류 ({file}): {e}")
        
        # 4. 파일 무결성 검증
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            verification_results['file_count'] = file_count
            verification_results['total_size'] = total_size
            
        except Exception as e:
            verification_results['file_integrity'] = False
            verification_results['issues'].append(f"파일 무결성 검증 오류: {e}")
        
        # 전체 검증 결과
        verification_results['overall_success'] = (
            verification_results['structure_check'] and
            verification_results['dependencies_check'] and
            verification_results['syntax_check'] and
            verification_results['file_integrity']
        )
        
        if verification_results['overall_success']:
            print("  ✅ 패키지 검증 성공")
        else:
            print("  ❌ 패키지 검증 실패")
            for issue in verification_results['issues']:
                print(f"    - {issue}")
        
        return verification_results
    
    def generate_package_info(self, package_dir: str, verification_results: Dict) -> PackageInfo:
        """패키지 정보 생성"""
        # 체크섬 계산
        checksum = self._calculate_directory_checksum(package_dir)
        
        package_info = PackageInfo(
            name=self.package_name,
            version=self.version,
            description="AI-based Real-time Natural Makeup and Surgery Simulation Platform",
            author="Natural Beauty Simulation Team",
            created_at=datetime.now().isoformat(),
            file_count=verification_results.get('file_count', 0),
            total_size=verification_results.get('total_size', 0),
            checksum=checksum
        )
        
        # 패키지 정보 파일 저장
        info_file = os.path.join(package_dir, "package_info.json")
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(package_info), f, ensure_ascii=False, indent=2)
        
        return package_info
    
    def _calculate_directory_checksum(self, directory: str) -> str:
        """디렉토리 체크섬 계산"""
        hash_md5 = hashlib.md5()
        
        for root, dirs, files in os.walk(directory):
            # 정렬하여 일관된 순서 보장
            dirs.sort()
            files.sort()
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                except:
                    pass  # 읽을 수 없는 파일은 무시
        
        return hash_md5.hexdigest()
    
    def create_deployment_package(self, output_dir: str = "dist") -> Dict[str, Any]:
        """전체 배포 패키지 생성"""
        print("="*80)
        print("배포 패키지 생성 시작")
        print("="*80)
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 1. 패키지 구조 생성
            package_dir = self.create_package_structure(output_dir)
            
            # 2. 패키지 검증
            verification_results = self.verify_package(package_dir)
            
            # 3. 패키지 정보 생성
            package_info = self.generate_package_info(package_dir, verification_results)
            
            # 4. ZIP 패키지 생성
            zip_path = self.create_zip_package(package_dir, output_dir)
            
            # 5. 결과 보고서 생성
            report = {
                'package_info': asdict(package_info),
                'verification_results': verification_results,
                'zip_package': os.path.basename(zip_path),
                'package_directory': os.path.basename(package_dir),
                'created_at': datetime.now().isoformat()
            }
            
            # 보고서 저장
            report_file = os.path.join(output_dir, "deployment_report.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print("\n" + "="*80)
            print("배포 패키지 생성 완료")
            print("="*80)
            print(f"패키지 이름: {package_info.name}")
            print(f"버전: {package_info.version}")
            print(f"파일 수: {package_info.file_count}")
            print(f"총 크기: {package_info.total_size / 1024 / 1024:.2f} MB")
            print(f"체크섬: {package_info.checksum[:16]}...")
            print(f"ZIP 패키지: {zip_path}")
            print(f"검증 결과: {'성공' if verification_results['overall_success'] else '실패'}")
            
            if verification_results['issues']:
                print("\n주의사항:")
                for issue in verification_results['issues']:
                    print(f"  - {issue}")
            
            return report
            
        except Exception as e:
            print(f"\n❌ 배포 패키지 생성 실패: {e}")
            return {'error': str(e)}


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="배포 패키지 생성 도구")
    parser.add_argument("--output", "-o", default="dist", help="출력 디렉토리")
    parser.add_argument("--project-root", "-r", default=".", help="프로젝트 루트 디렉토리")
    
    args = parser.parse_args()
    
    # 배포 패키지 생성
    packager = DeploymentPackager(args.project_root)
    result = packager.create_deployment_package(args.output)
    
    # 결과에 따른 종료 코드
    if 'error' in result:
        sys.exit(1)
    elif not result.get('verification_results', {}).get('overall_success', False):
        print("\n⚠️  경고: 패키지 검증에서 문제가 발견되었습니다.")
        sys.exit(2)
    else:
        print("\n✅ 배포 패키지가 성공적으로 생성되었습니다.")
        sys.exit(0)


if __name__ == "__main__":
    main()