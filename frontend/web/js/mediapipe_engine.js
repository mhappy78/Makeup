/**
 * BeautyGen - MediaPipe JavaScript 엔진
 * 백엔드 없이 브라우저에서 직접 얼굴 랜드마크 검출
 */

class MediaPipeEngine {
    constructor() {
        this.faceMesh = null;
        this.isInitialized = false;
        this.isProcessing = false;
        this.initializeEngine();
    }

    /**
     * MediaPipe Face Mesh 초기화
     */
    async initializeEngine() {
        try {
            console.log('🚀 MediaPipe 엔진 초기화 시작...');
            
            // MediaPipe 라이브러리 로드 확인
            if (typeof FaceMesh === 'undefined') {
                throw new Error('MediaPipe FaceMesh 라이브러리가 로드되지 않았습니다');
            }
            
            console.log('✅ MediaPipe FaceMesh 라이브러리 확인됨');
            
            this.faceMesh = new FaceMesh({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4/${file}`;
                }
            });

            this.faceMesh.setOptions({
                maxNumFaces: 1,
                refineLandmarks: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            this.faceMesh.onResults((results) => {
                this.onResults(results);
            });

            this.isInitialized = true;
            console.log('✅ MediaPipe 엔진 초기화 완료');
        } catch (error) {
            console.error('❌ MediaPipe 엔진 초기화 실패:', error);
            this.isInitialized = false;
        }
    }

    /**
     * 이미지에서 얼굴 랜드마크 검출
     * @param {ImageData|HTMLImageElement|HTMLCanvasElement} imageInput - 입력 이미지
     * @returns {Promise<Array>} 468개 랜드마크 좌표 배열 [[x, y], ...]
     */
    async detectLandmarks(imageInput) {
        if (!this.isInitialized) {
            throw new Error('MediaPipe 엔진이 초기화되지 않았습니다');
        }

        if (this.isProcessing) {
            throw new Error('이미 처리 중입니다. 잠시 후 다시 시도하세요');
        }

        return new Promise((resolve, reject) => {
            this.isProcessing = true;
            this.currentResolve = resolve;
            this.currentReject = reject;

            try {
                // 다양한 입력 타입 처리
                let canvas, ctx;
                
                if (imageInput instanceof ImageData) {
                    // ImageData인 경우 Canvas로 변환
                    canvas = document.createElement('canvas');
                    ctx = canvas.getContext('2d');
                    canvas.width = imageInput.width;
                    canvas.height = imageInput.height;
                    ctx.putImageData(imageInput, 0, 0);
                } else if (imageInput instanceof HTMLCanvasElement) {
                    canvas = imageInput;
                } else if (imageInput instanceof HTMLImageElement) {
                    canvas = document.createElement('canvas');
                    ctx = canvas.getContext('2d');
                    canvas.width = imageInput.naturalWidth || imageInput.width;
                    canvas.height = imageInput.naturalHeight || imageInput.height;
                    ctx.drawImage(imageInput, 0, 0);
                } else {
                    throw new Error('지원하지 않는 이미지 형식입니다');
                }

                // MediaPipe로 처리
                this.faceMesh.send({ image: canvas });
                
            } catch (error) {
                this.isProcessing = false;
                reject(error);
            }
        });
    }

    /**
     * MediaPipe 결과 처리
     */
    onResults(results) {
        try {
            
            this.isProcessing = false;

            if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
                if (this.currentReject) {
                    this.currentReject(new Error('얼굴을 찾을 수 없습니다'));
                }
                return;
            }

            // 첫 번째 얼굴의 랜드마크 사용 (가장 확실한 얼굴)
            const faceLandmarks = results.multiFaceLandmarks[0];
            const imageWidth = results.image.width;
            const imageHeight = results.image.height;
            

            // 468개 랜드마크 좌표 추출
            const landmarks = faceLandmarks.map(landmark => [
                landmark.x * imageWidth,
                landmark.y * imageHeight
            ]);
            

            if (this.currentResolve) {
                this.currentResolve({
                    landmarks: landmarks,
                    imageWidth: imageWidth,
                    imageHeight: imageHeight,
                    confidence: results.multiFaceLandmarks.length > 1 ? 'multiple_faces' : 'single_face'
                });
            }
        } catch (error) {
            console.error('❌ MediaPipe 결과 처리 오류:', error);
            this.isProcessing = false;
            if (this.currentReject) {
                this.currentReject(error);
            }
        }
    }

    /**
     * Uint8Array 이미지 데이터에서 랜드마크 검출
     * @param {Uint8List} imageBytes - 이미지 바이트 데이터
     * @returns {Promise<Object>} 랜드마크 검출 결과
     */
    async detectLandmarksFromBytes(imageBytes) {
        return new Promise((resolve, reject) => {
            try {
                // Blob 생성
                const blob = new Blob([imageBytes]);
                const url = URL.createObjectURL(blob);
                
                // Image 객체 생성
                const img = new Image();
                img.onload = async () => {
                    try {
                        URL.revokeObjectURL(url);
                        const result = await this.detectLandmarks(img);
                        resolve(result);
                    } catch (error) {
                        URL.revokeObjectURL(url);
                        reject(error);
                    }
                };
                
                img.onerror = () => {
                    URL.revokeObjectUrl(url);
                    reject(new Error('이미지 로드 실패'));
                };
                
                img.src = url;
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Canvas ImageData에서 랜드마크 검출
     * @param {ImageData} imageData - Canvas ImageData
     * @returns {Promise<Object>} 랜드마크 검출 결과
     */
    async detectLandmarksFromImageData(imageData) {
        return await this.detectLandmarks(imageData);
    }

    /**
     * 엔진 상태 확인
     */
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            isProcessing: this.isProcessing,
            version: 'MediaPipe Face Mesh v0.4'
        };
    }

    /**
     * 성능 벤치마크
     */
    async runBenchmark(testImageData) {
        if (!this.isInitialized) {
            throw new Error('엔진이 초기화되지 않았습니다');
        }

        const startTime = performance.now();
        
        try {
            const result = await this.detectLandmarksFromImageData(testImageData);
            const endTime = performance.now();
            
            return {
                processingTime: endTime - startTime,
                landmarkCount: result.landmarks.length,
                imageSize: `${testImageData.width}x${testImageData.height}`,
                success: true
            };
        } catch (error) {
            const endTime = performance.now();
            return {
                processingTime: endTime - startTime,
                error: error.message,
                success: false
            };
        }
    }
}

// 전역 MediaPipe 엔진 인스턴스 생성
window.mediaPipeEngine = new MediaPipeEngine();

/**
 * Dart에서 호출할 수 있는 전역 함수들
 */

// 이미지 바이트에서 랜드마크 검출
window.detectFaceLandmarks = async function(imageBytes) {
    try {
        const result = await window.mediaPipeEngine.detectLandmarksFromBytes(imageBytes);
        return {
            landmarks: result.landmarks,
            imageWidth: result.imageWidth,
            imageHeight: result.imageHeight,
            source: 'frontend_mediapipe'
        };
    } catch (error) {
        console.error('❌ 랜드마크 검출 실패:', error);
        throw error;
    }
};

// ImageData에서 랜드마크 검출
window.detectFaceLandmarksFromImageData = async function(imageDataArray, width, height) {
    try {
        const uint8Array = new Uint8ClampedArray(imageDataArray);
        const imageData = new ImageData(uint8Array, width, height);
        
        const result = await window.mediaPipeEngine.detectLandmarksFromImageData(imageData);
        return {
            landmarks: result.landmarks,
            imageWidth: result.imageWidth,
            imageHeight: result.imageHeight,
            source: 'frontend_mediapipe'
        };
    } catch (error) {
        console.error('❌ ImageData 랜드마크 검출 실패:', error);
        throw error;
    }
};

// 엔진 상태 확인
window.getMediaPipeStatus = function() {
    return window.mediaPipeEngine.getStatus();
};

// 성능 벤치마크 실행
window.runMediaPipeBenchmark = async function(imageDataArray, width, height) {
    try {
        const uint8Array = new Uint8ClampedArray(imageDataArray);
        const imageData = new ImageData(uint8Array, width, height);
        
        return await window.mediaPipeEngine.runBenchmark(imageData);
    } catch (error) {
        return {
            error: error.message,
            success: false
        };
    }
};

console.log('📡 BeautyGen MediaPipe Engine loaded successfully');