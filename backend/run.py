#!/usr/bin/env python3
"""
Face Simulator Backend 실행 스크립트
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 BeautyGen API 서버 시작...")
    print("📍 서버 주소: http://localhost:8080")
    print("📚 API 문서: http://localhost:8080/docs")
    print("🔄 Interactive API: http://localhost:8080/redoc")
    
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8080,
        reload=True,  # 개발 모드에서 자동 리로드
        log_level="info"
    )