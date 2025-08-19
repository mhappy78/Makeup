/**
 * BeautyGen - JavaScript 워핑 엔진
 * 백엔드 Python OpenCV 알고리즘을 Canvas API로 포팅
 */

class WarpEngine {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.imageData = null;
        this.width = 0;
        this.height = 0;
    }

    /**
     * 이미지 초기화
     * @param {ImageData} imageData - Canvas ImageData 객체
     */
    initialize(imageData) {
        this.imageData = imageData;
        this.width = imageData.width;
        this.height = imageData.height;
        
        // 작업용 캔버스 생성
        if (!this.canvas) {
            this.canvas = document.createElement('canvas');
            this.ctx = this.canvas.getContext('2d');
        }
        
        this.canvas.width = this.width;
        this.canvas.height = this.height;
        this.ctx.putImageData(imageData, 0, 0);
    }

    /**
     * 워핑 변형 적용 (메인 함수)
     * @param {number} startX - 시작 X 좌표
     * @param {number} startY - 시작 Y 좌표  
     * @param {number} endX - 끝 X 좌표
     * @param {number} endY - 끝 Y 좌표
     * @param {number} influenceRadius - 영향 반경 (픽셀)
     * @param {number} strength - 변형 강도 (0.0 ~ 1.0)
     * @param {string} mode - 워핑 모드 ('pull', 'push', 'expand', 'shrink')
     * @returns {ImageData} 변형된 이미지 데이터
     */
    applyWarp(startX, startY, endX, endY, influenceRadius, strength, mode) {
        // 좌표 경계 검사
        startX = Math.max(0, Math.min(startX, this.width - 1));
        startY = Math.max(0, Math.min(startY, this.height - 1));
        endX = Math.max(0, Math.min(endX, this.width - 1));
        endY = Math.max(0, Math.min(endY, this.height - 1));

        switch(mode) {
            case 'pull':
                return this.applyPullWarp(startX, startY, endX, endY, influenceRadius, strength);
            case 'push':
                return this.applyPushWarp(startX, startY, endX, endY, influenceRadius, strength);
            case 'expand':
                return this.applyRadialWarp(startX, startY, influenceRadius, strength, true);
            case 'shrink':
                return this.applyRadialWarp(startX, startY, influenceRadius, strength, false);
            default:
                return this.imageData;
        }
    }

    /**
     * 당기기 워핑 (Python apply_pull_warp 포팅)
     */
    applyPullWarp(startX, startY, endX, endY, influenceRadius, strength) {
        // 드래그 벡터 (방향 수정: 끝점에서 시작점으로)
        const dx = endX - startX;
        const dy = endY - startY;

        return this.applyDirectionalWarp(startX, startY, dx, dy, influenceRadius, strength);
    }

    /**
     * 밀어내기 워핑 (Python apply_push_warp 포팅)
     */
    applyPushWarp(startX, startY, endX, endY, influenceRadius, strength) {
        // 드래그 벡터 (방향 수정: 시작점에서 끝점으로 반대)
        const dx = startX - endX;
        const dy = startY - endY;

        return this.applyDirectionalWarp(startX, startY, dx, dy, influenceRadius, strength);
    }

    /**
     * 방향성 워핑 공통 로직
     */
    applyDirectionalWarp(centerX, centerY, dx, dy, influenceRadius, strength) {
        const sourceData = this.imageData.data;
        const resultCanvas = document.createElement('canvas');
        const resultCtx = resultCanvas.getContext('2d');
        
        resultCanvas.width = this.width;
        resultCanvas.height = this.height;
        
        const resultImageData = resultCtx.createImageData(this.width, this.height);
        const resultData = resultImageData.data;

        // 초기화 - 원본 이미지로 채움
        for (let i = 0; i < sourceData.length; i++) {
            resultData[i] = sourceData[i];
        }

        // 워핑 변형 적용 (역방향 매핑)
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                // 중심점으로부터의 거리 계산
                const pixelDx = x - centerX;
                const pixelDy = y - centerY;
                const pixelDist = Math.sqrt(pixelDx * pixelDx + pixelDy * pixelDy);

                // 영향 반경 내부인지 확인
                if (pixelDist < influenceRadius) {
                    // 변형 강도 계산 (Python과 동일한 공식)
                    const distRatio = pixelDist / influenceRadius;
                    const strengthMap = (1 - distRatio) * (1 - distRatio) * strength;

                    // 원본 좌표 계산 (역방향 매핑)
                    const sourceX = x - dx * strengthMap;
                    const sourceY = y - dy * strengthMap;

                    // 경계 검사
                    if (sourceX >= 0 && sourceX < this.width - 1 && 
                        sourceY >= 0 && sourceY < this.height - 1) {
                        
                        // 바이리니어 보간으로 픽셀 값 계산
                        const interpolatedPixel = this.bilinearInterpolation(
                            sourceData, sourceX, sourceY, this.width, this.height
                        );

                        // 결과 이미지에 적용
                        const targetIndex = (y * this.width + x) * 4;
                        resultData[targetIndex] = interpolatedPixel.r;     // R
                        resultData[targetIndex + 1] = interpolatedPixel.g; // G
                        resultData[targetIndex + 2] = interpolatedPixel.b; // B
                        resultData[targetIndex + 3] = interpolatedPixel.a; // A
                    }
                }
            }
        }

        return resultImageData;
    }

    /**
     * 방사형 워핑 (확대/축소)
     */
    applyRadialWarp(centerX, centerY, influenceRadius, strength, expand) {
        const sourceData = this.imageData.data;
        const resultCanvas = document.createElement('canvas');
        const resultCtx = resultCanvas.getContext('2d');
        
        resultCanvas.width = this.width;
        resultCanvas.height = this.height;
        
        const resultImageData = resultCtx.createImageData(this.width, this.height);
        const resultData = resultImageData.data;

        // 초기화
        for (let i = 0; i < sourceData.length; i++) {
            resultData[i] = sourceData[i];
        }

        // 변형 계수 (Python과 동일)
        const strengthFactor = strength * 0.3;

        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                const dx = x - centerX;
                const dy = y - centerY;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < influenceRadius && distance > 0) {
                    let scaleFactor;
                    
                    if (expand) {
                        // 확대: 중심으로 가까워지게
                        scaleFactor = 1 - strengthFactor * (1 - distance / influenceRadius);
                    } else {
                        // 축소: 중심에서 멀어지게  
                        scaleFactor = 1 + strengthFactor * (1 - distance / influenceRadius);
                    }

                    scaleFactor = Math.max(scaleFactor, 0.1); // 최소 스케일 제한

                    // 원본 좌표 계산
                    const sourceX = centerX + dx * scaleFactor;
                    const sourceY = centerY + dy * scaleFactor;

                    if (sourceX >= 0 && sourceX < this.width - 1 && 
                        sourceY >= 0 && sourceY < this.height - 1) {
                        
                        const interpolatedPixel = this.bilinearInterpolation(
                            sourceData, sourceX, sourceY, this.width, this.height
                        );

                        const targetIndex = (y * this.width + x) * 4;
                        resultData[targetIndex] = interpolatedPixel.r;
                        resultData[targetIndex + 1] = interpolatedPixel.g;
                        resultData[targetIndex + 2] = interpolatedPixel.b;
                        resultData[targetIndex + 3] = interpolatedPixel.a;
                    }
                }
            }
        }

        return resultImageData;
    }

    /**
     * 바이리니어 보간 (OpenCV INTER_LINEAR 모방)
     * @param {Uint8ClampedArray} imageData - 원본 이미지 데이터
     * @param {number} x - X 좌표 (실수)
     * @param {number} y - Y 좌표 (실수)
     * @param {number} width - 이미지 너비
     * @param {number} height - 이미지 높이
     * @returns {Object} {r, g, b, a} 보간된 픽셀 값
     */
    bilinearInterpolation(imageData, x, y, width, height) {
        const x1 = Math.floor(x);
        const y1 = Math.floor(y);
        const x2 = Math.min(x1 + 1, width - 1);
        const y2 = Math.min(y1 + 1, height - 1);

        const fx = x - x1;
        const fy = y - y1;

        // 4개 인접 픽셀 가져오기
        const getPixel = (px, py) => {
            const index = (py * width + px) * 4;
            return {
                r: imageData[index],
                g: imageData[index + 1],
                b: imageData[index + 2],
                a: imageData[index + 3]
            };
        };

        const topLeft = getPixel(x1, y1);
        const topRight = getPixel(x2, y1);
        const bottomLeft = getPixel(x1, y2);
        const bottomRight = getPixel(x2, y2);

        // 바이리니어 보간 계산
        const interpolateChannel = (tl, tr, bl, br) => {
            const top = tl * (1 - fx) + tr * fx;
            const bottom = bl * (1 - fx) + br * fx;
            return top * (1 - fy) + bottom * fy;
        };

        return {
            r: Math.round(interpolateChannel(topLeft.r, topRight.r, bottomLeft.r, bottomRight.r)),
            g: Math.round(interpolateChannel(topLeft.g, topRight.g, bottomLeft.g, bottomRight.g)),
            b: Math.round(interpolateChannel(topLeft.b, topRight.b, bottomLeft.b, bottomRight.b)),
            a: Math.round(interpolateChannel(topLeft.a, topRight.a, bottomLeft.a, bottomRight.a))
        };
    }

    /**
     * 프리셋 변형 적용 (백엔드 프리셋 로직 포팅)
     * @param {Array} landmarks - 468개 얼굴 랜드마크 배열 [[x, y], ...]
     * @param {string} presetType - 프리셋 타입
     * @returns {ImageData} 변형된 이미지
     */
    applyPreset(landmarks, presetType) {
        const PRESET_CONFIGS = {
            'lower_jaw': {
                strength: 0.005,  // 0.5%로 조정
                influenceRatio: 0.4,
                pullRatio: 0.1,
                faceSizeLandmarks: [234, 447],
                targetLandmarks: [150, 379, 4]
            },
            'middle_jaw': {
                strength: 0.005,  // 0.5%로 조정
                influenceRatio: 0.65,
                pullRatio: 0.1,
                faceSizeLandmarks: [234, 447],
                targetLandmarks: [172, 397, 4]
            },
            'cheek': {
                strength: 0.005,  // 0.5%로 조정
                influenceRatio: 0.65,
                pullRatio: 0.1,
                faceSizeLandmarks: [234, 447],
                targetLandmarks: [215, 435, 4]
            },
            'front_protusion': {
                strength: 0.03,  // 3%로 조정
                influenceRatio: 0.1,
                pullRatio: 0.1,
                faceSizeLandmarks: [234, 447],
                targetLandmarks: [243, 463, [56, 190], [414, 286], 168, 6],
                ellipseRatio: 1.3
            },
            'back_slit': {
                strength: 0.03,  // 3%로 조정
                influenceRatio: 0.1,
                pullRatio: 0.1,
                faceSizeLandmarks: [234, 447],
                targetLandmarks: [33, 359, [34, 162], [368, 264]]
            }
        };

        if (!PRESET_CONFIGS[presetType]) {
            console.error('Unknown preset type:', presetType);
            return this.imageData;
        }

        const config = PRESET_CONFIGS[presetType];
        
        // 얼굴 크기 계산
        const faceLeft = landmarks[config.faceSizeLandmarks[0]];
        const faceRight = landmarks[config.faceSizeLandmarks[1]];
        const faceWidth = Math.abs(faceRight[0] - faceLeft[0]);
        const influenceRadius = faceWidth * config.influenceRatio;

        let result = this.imageData;

        // 프리셋별 변형 적용
        switch(presetType) {
            case 'lower_jaw':
            case 'middle_jaw':
            case 'cheek':
                result = this.applyJawCheekPreset(landmarks, config, influenceRadius);
                break;
            case 'front_protusion':
                result = this.applyFrontProtusionPreset(landmarks, config, influenceRadius);
                break;
            case 'back_slit':
                result = this.applyBackSlitPreset(landmarks, config, influenceRadius);
                break;
        }

        return result;
    }

    /**
     * 턱/볼 프리셋 적용
     */
    applyJawCheekPreset(landmarks, config, influenceRadius) {
        const [leftIdx, rightIdx, targetIdx] = config.targetLandmarks;
        
        const leftLandmark = landmarks[leftIdx];
        const rightLandmark = landmarks[rightIdx];
        const targetLandmark = landmarks[targetIdx];

        // 좌측 변형
        this.initialize(this.imageData);
        let result = this.applyPullWarp(
            leftLandmark[0], leftLandmark[1],
            targetLandmark[0], targetLandmark[1],
            influenceRadius, config.strength
        );

        // 우측 변형
        this.initialize(result);
        result = this.applyPullWarp(
            rightLandmark[0], rightLandmark[1],
            targetLandmark[0], targetLandmark[1],
            influenceRadius, config.strength
        );

        return result;
    }

    /**
     * 앞트임 프리셋 적용
     */
    applyFrontProtusionPreset(landmarks, config, influenceRadius) {
        // 구현 복잡도로 인해 기본 당기기 모드로 단순화
        const [leftIdx, rightIdx] = [config.targetLandmarks[0], config.targetLandmarks[1]];
        const targetCenter = [(landmarks[168][0] + landmarks[6][0]) / 2, (landmarks[168][1] + landmarks[6][1]) / 2];
        
        this.initialize(this.imageData);
        let result = this.applyPullWarp(
            landmarks[leftIdx][0], landmarks[leftIdx][1],
            targetCenter[0], targetCenter[1],
            influenceRadius, config.strength
        );

        this.initialize(result);
        result = this.applyPullWarp(
            landmarks[rightIdx][0], landmarks[rightIdx][1],
            targetCenter[0], targetCenter[1],
            influenceRadius, config.strength
        );

        return result;
    }

    /**
     * 뒷트임 프리셋 적용
     */
    applyBackSlitPreset(landmarks, config, influenceRadius) {
        const [leftIdx, rightIdx] = [config.targetLandmarks[0], config.targetLandmarks[1]];
        
        // 타겟 중간점 계산
        const leftTarget = [(landmarks[34][0] + landmarks[162][0]) / 2, (landmarks[34][1] + landmarks[162][1]) / 2];
        const rightTarget = [(landmarks[368][0] + landmarks[264][0]) / 2, (landmarks[368][1] + landmarks[264][1]) / 2];

        this.initialize(this.imageData);
        let result = this.applyPullWarp(
            landmarks[leftIdx][0], landmarks[leftIdx][1],
            leftTarget[0], leftTarget[1],
            influenceRadius, config.strength
        );

        this.initialize(result);
        result = this.applyPullWarp(
            landmarks[rightIdx][0], landmarks[rightIdx][1],
            rightTarget[0], rightTarget[1],
            influenceRadius, config.strength
        );

        return result;
    }
}

// 전역 인스턴스 생성
window.warpEngine = new WarpEngine();

/**
 * Dart에서 호출할 수 있는 전역 함수들
 */
// ImageData를 JPEG 바이트로 변환하는 동기 함수
window.imageDataToJpegBytes = function(imageData, width, height) {
    try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = width;
        canvas.height = height;
        ctx.putImageData(imageData, 0, 0);
        
        // DataURL로 변환 (동기)
        const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
        
        // Base64 추출
        const base64 = dataUrl.split(',')[1];
        
        // Base64를 바이트 배열로 변환
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        return Array.from(bytes);
    } catch (error) {
        console.error('❌ ImageData to JPEG 변환 실패:', error);
        return null;
    }
};

window.applyWarpTransformation = function(imageDataArray, width, height, startX, startY, endX, endY, influenceRadius, strength, mode) {
    try {
        // Uint8ClampedArray로 변환
        const uint8Array = new Uint8ClampedArray(imageDataArray);
        const imageData = new ImageData(uint8Array, width, height);
        
        // 워핑 엔진 초기화 및 적용
        window.warpEngine.initialize(imageData);
        const result = window.warpEngine.applyWarp(startX, startY, endX, endY, influenceRadius, strength, mode);
        
        // 결과를 JPEG 바이트로 변환하여 반환
        return window.imageDataToJpegBytes(result, width, height);
    } catch (error) {
        console.error('Warp transformation error:', error);
        return null;
    }
};

window.applyPresetTransformation = function(imageDataArray, width, height, landmarks, presetType) {
    try {
        const uint8Array = new Uint8ClampedArray(imageDataArray);
        const imageData = new ImageData(uint8Array, width, height);
        
        window.warpEngine.initialize(imageData);
        const result = window.warpEngine.applyPreset(landmarks, presetType);
        
        // 결과를 JPEG 바이트로 변환하여 반환
        return window.imageDataToJpegBytes(result, width, height);
    } catch (error) {
        console.error('Preset transformation error:', error);
        return null;
    }
};

console.log('BeautyGen Warp Engine loaded successfully');