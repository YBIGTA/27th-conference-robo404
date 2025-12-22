# Vision API 패키지 가이드

## 1. 패키지 개요

`vision_api`는 ROS 2 기반의 멀티 프로바이더 비전 분석 패키지입니다. 카메라가 안정화되면 캡처한 이미지를 외부 AI Vision API로 전송하여 분석 결과를 받아옵니다.

**지원 API 프로바이더:**
- OpenAI GPT-4o
- Google Gemini 1.5
- Huggingface (BLIP 등 Image Captioning 모델)

---

## 2. 파일 구조

```
vision_api/
├── package.xml                 # ROS 2 패키지 메타데이터
├── setup.py                    # Python 패키지 설정 및 엔트리포인트
├── setup.cfg                   # setuptools 설정
├── test_api.py                 # API 단독 테스트 스크립트
├── launch/
│   └── analyzer.launch.py      # ROS 2 런치 파일
├── resource/
│   └── vision_api              # ament 리소스 마커
└── vision_api/
    ├── __init__.py             # 패키지 초기화
    ├── analyzer_node.py        # 메인 ROS 2 노드
    └── api/
        ├── __init__.py         # API 팩토리 및 모듈 export
        ├── base.py             # 추상 베이스 클래스
        ├── openai_api.py       # OpenAI GPT-4o 구현
        ├── gemini_api.py       # Google Gemini 구현
        └── huggingface_api.py  # Huggingface 구현
```

---

## 3. 아키텍처 및 데이터 흐름

### 3.1 전체 시스템 토픽 연결

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           전체 시스템 토픽 연결 구조                           │
└──────────────────────────────────────────────────────────────────────────────┘

                         /camera/image_raw
┌───────────┐ ─────────────────┬─────────────────────────┐
│  Gazebo   │                  │                         │
│  카메라    │                  ▼                         ▼
└───────────┘           ┌─────────────┐           ┌─────────────┐
                        │  yolo_node  │           │ vision_api  │
                        └──────┬──────┘           └──────┬──────┘
                               │                         ▲
                               │ /yolo/detections        │ /camera/stable
                               ▼                         │
                        ┌─────────────┐                  │
                        │   camera    │──────────────────┘
                        │   tracker   │
                        └──────┬──────┘
                               │
                               │ /camera/pan_cmd
                               │ /camera/tilt_cmd
                               ▼
                        ┌─────────────┐
                        │   Gazebo    │
                        │  Pan/Tilt   │
                        └─────────────┘
```

**노드별 입출력 토픽:**

| 노드 | 입력 토픽 | 출력 토픽 |
|------|----------|----------|
| yolo_node | `/camera/image_raw` | `/yolo/detections` |
| camera_tracker | `/yolo/detections` | `/camera/pan_cmd`, `/camera/tilt_cmd`, `/camera/stable` |
| vision_api | `/camera/image_raw`, `/camera/stable` | `/vision/analysis_result` |

**핵심 포인트:**
- `camera_tracker`는 이미지를 직접 받지 않고, YOLO가 계산한 **bbox 좌표**만 사용
- `vision_api`는 `camera_tracker`의 `/camera/stable` 신호를 받아 안정화 시점에 분석 수행
- Gazebo 카메라 이미지는 `yolo_node`와 `vision_api` 두 노드가 동시에 구독

---

### 3.2 vision_api 노드 내부 흐름

```
┌─────────────────────────────────────────────────────────────────────┐
│                    vision_analyzer 노드 내부 흐름                     │
└─────────────────────────────────────────────────────────────────────┘

[camera_tracker 노드]                    [vision_analyzer 노드]
        │                                        │
        ├── /camera/stable (Bool) ──────────────►├── stable_callback()
        │                                        │      │
[카메라 드라이버]                                 │      ▼
        │                                        │   안정화 상태 체크
        └── /camera/image_raw (Image) ─────────►├── image_callback()
                                                 │      │
                                                 │      ▼
                                                 │   최신 이미지 저장
                                                 │      │
                                                 │      ▼
                                                 │   check_and_analyze()
                                                 │      │ (타이머 0.1s)
                                                 │      ▼
                                                 │   [조건 충족 시]
                                                 │      │
                                                 │      ▼
                                                 │   perform_analysis()
                                                 │      │
                                                 │      ▼
                                                 │   VisionAPIFactory
                                                 │      │
                                                 │      ├──► OpenAI API
                                                 │      ├──► Gemini API
                                                 │      └──► Huggingface API
                                                 │      │
                                                 │      ▼
                                                 └──► /vision/analysis_result (String)
```

### 분석 트리거 조건

1. `is_stable == True` (카메라 안정화)
2. `stable_duration >= min_stable_duration` (최소 안정화 시간)
3. `elapsed >= analysis_cooldown` (쿨다운 경과)
4. `analysis_in_progress == False` (중복 분석 방지)

---

## 4. 파일별 코드 해설

### 4.1 `package.xml`

ROS 2 패키지 메타데이터 정의 파일입니다.

```xml
<exec_depend>rclpy</exec_depend>      # ROS 2 Python 클라이언트
<exec_depend>std_msgs</exec_depend>    # Bool, String 메시지
<exec_depend>sensor_msgs</exec_depend> # Image 메시지
<exec_depend>cv_bridge</exec_depend>   # ROS Image ↔ OpenCV 변환
```

---

### 4.2 `setup.py`

Python 패키지 설정 및 ROS 2 노드 엔트리포인트 정의:

```python
entry_points={
    'console_scripts': [
        'analyzer_node = vision_api.analyzer_node:main',
    ],
},
```

`ros2 run vision_api analyzer_node` 명령으로 실행 가능합니다.

---

### 4.3 `launch/analyzer.launch.py`

ROS 2 런치 파일로, 노드 실행 시 파라미터를 설정합니다.

**주요 런치 파라미터:**

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `api_provider` | `openai` | API 제공자 (openai/gemini/huggingface) |
| `api_key` | 환경변수 `VISION_API_KEY` | API 인증 키 |
| `api_model` | (프로바이더 기본값) | 사용할 모델명 |
| `prompt` | `Describe the main object...` | 분석 프롬프트 |
| `min_stable_duration` | `1.0` | 최소 안정화 시간(초) |
| `analysis_cooldown` | `5.0` | 분석 간 쿨다운(초) |
| `image_topic` | `/camera/image_raw` | 이미지 구독 토픽 |
| `stable_topic` | `/camera/stable` | 안정화 상태 구독 토픽 |

---

### 4.4 `vision_api/analyzer_node.py`

**메인 ROS 2 노드**로, 전체 로직을 관장합니다.

#### 클래스: `VisionAnalyzerNode`

**초기화 (`__init__`)**
```python
# 파라미터 선언 및 로드
self.declare_parameter('api_provider', 'openai')
self.api_provider = self.get_parameter('api_provider').value

# API 클라이언트 생성 (팩토리 패턴)
self.api_client = VisionAPIFactory.create(
    self.api_provider, self.api_key, self.api_model
)

# Subscriber 생성
self.image_sub = self.create_subscription(Image, image_topic, ...)
self.stable_sub = self.create_subscription(Bool, stable_topic, ...)

# Publisher 생성
self.result_pub = self.create_publisher(String, '/vision/analysis_result', 10)

# 주기적 체크 타이머 (0.1초마다)
self.timer = self.create_timer(0.1, self.check_and_analyze)
```

**콜백 함수들:**

| 함수 | 역할 |
|------|------|
| `image_callback()` | 이미지 메시지 → OpenCV 변환 후 저장 |
| `stable_callback()` | 안정화 상태 업데이트, 시작 시간 기록 |
| `check_and_analyze()` | 0.1초마다 분석 조건 체크 |
| `perform_analysis()` | API 호출 및 결과 발행 |

---

### 4.5 `vision_api/api/__init__.py`

**팩토리 패턴**으로 API 클라이언트를 생성합니다.

```python
class VisionAPIFactory:
    _providers = {
        'openai': OpenAIVisionAPI,
        'gemini': GeminiVisionAPI,
        'huggingface': HuggingFaceVisionAPI,
    }

    @classmethod
    def create(cls, provider, api_key, model=None) -> VisionAPIBase:
        return cls._providers[provider](api_key, model)
```

새 API 프로바이더 추가 시 `_providers` 딕셔너리에 등록하면 됩니다.

---

### 4.6 `vision_api/api/base.py`

**추상 베이스 클래스**로, 모든 API 구현체의 인터페이스를 정의합니다.

#### 데이터 클래스: `AnalysisResult`

```python
@dataclass
class AnalysisResult:
    success: bool              # 성공 여부
    description: str           # 분석 결과 텍스트
    detected_objects: List[str]  # 감지된 객체 목록
    confidence: float          # 신뢰도 (0.0~1.0)
    raw_response: Optional[str]  # API 원본 응답
    error_message: Optional[str] # 에러 메시지
    latency_ms: float          # 응답 시간 (ms)
```

#### 추상 클래스: `VisionAPIBase`

```python
class VisionAPIBase(ABC):
    @abstractmethod
    def _validate_credentials(self) -> None:
        """API 자격증명 검증 및 클라이언트 초기화"""
        pass

    @abstractmethod
    def analyze_image(self, image: np.ndarray, prompt: str) -> AnalysisResult:
        """이미지 분석 수행"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """프로바이더 이름 반환"""
        pass

    def _encode_image_base64(self, image: np.ndarray) -> str:
        """이미지를 Base64 문자열로 인코딩 (공통 유틸리티)"""
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')
```

---

### 4.7 `vision_api/api/openai_api.py`

**OpenAI GPT-4o Vision API** 구현체입니다.

```python
class OpenAIVisionAPI(VisionAPIBase):
    DEFAULT_MODEL = "gpt-4o"

    def _validate_credentials(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=self.api_key)

    def analyze_image(self, image, prompt):
        base64_image = self._encode_image_base64(image)

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }}
                ]
            }],
            max_tokens=500
        )
        return AnalysisResult(success=True, description=response.choices[0].message.content, ...)
```

**특징:**
- Base64 인코딩된 이미지를 `image_url` 형식으로 전송
- Chat Completions API 사용

---

### 4.8 `vision_api/api/gemini_api.py`

**Google Gemini Vision API** 구현체입니다.

```python
class GeminiVisionAPI(VisionAPIBase):
    DEFAULT_MODEL = "gemini-1.5-flash"

    def _validate_credentials(self):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self._model_instance = genai.GenerativeModel(self.model)

    def analyze_image(self, image, prompt):
        from PIL import Image

        # BGR → RGB 변환 후 PIL Image로
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        response = self._model_instance.generate_content([prompt, pil_image])
        return AnalysisResult(success=True, description=response.text, ...)
```

**특징:**
- PIL Image 객체를 직접 전달
- OpenCV BGR → RGB 변환 필요

---

### 4.9 `vision_api/api/huggingface_api.py`

**Huggingface Inference API** 구현체입니다.

```python
class HuggingFaceVisionAPI(VisionAPIBase):
    API_URL = "https://router.huggingface.co/hf/"
    DEFAULT_MODEL = "Salesforce/blip-image-captioning-large"

    def _validate_credentials(self):
        self._headers = {"Authorization": f"Bearer {self.api_key}"}

    def analyze_image(self, image, prompt, task=None):
        # JPEG 바이너리로 인코딩
        _, buffer = cv2.imencode('.jpg', image)
        image_bytes = buffer.tobytes()

        response = requests.post(
            f"{self.API_URL}{self.model}",
            headers=self._headers,
            data=image_bytes,
            timeout=30
        )

        # BLIP 응답: [{"generated_text": "..."}]
        result = response.json()
        content = result[0].get('generated_text', ...)
        return AnalysisResult(success=True, description=content, ...)
```

**특징:**
- REST API로 이미지 바이너리 직접 전송
- BLIP 모델의 Image Captioning 기능 사용
- 30초 타임아웃 설정

---

### 4.10 `test_api.py`

ROS 2 없이 API를 단독으로 테스트하는 스크립트입니다.

```bash
# 환경변수 설정
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
export HF_API_KEY="hf_..."

# 테스트 실행
python test_api.py openai /path/to/image.jpg
python test_api.py gemini /path/to/image.jpg
python test_api.py huggingface /path/to/image.jpg
```

---

## 5. 실행 방법

### 5.1 빌드

```bash
cd ~/ros
colcon build --packages-select vision_api --symlink-install
source install/setup.bash
```

### 5.2 실행

```bash
# OpenAI 사용
export VISION_API_KEY="sk-..."
ros2 launch vision_api analyzer.launch.py api_provider:=openai

# Gemini 사용
export VISION_API_KEY="..."
ros2 launch vision_api analyzer.launch.py api_provider:=gemini

# Huggingface 사용
export VISION_API_KEY="hf_..."
ros2 launch vision_api analyzer.launch.py api_provider:=huggingface
```

### 5.3 결과 확인

```bash
# 분석 결과 토픽 구독
ros2 topic echo /vision/analysis_result
```

---

## 6. 확장 방법

### 새 API 프로바이더 추가

1. `vision_api/api/` 폴더에 새 파일 생성 (예: `anthropic_api.py`)

2. `VisionAPIBase`를 상속하여 구현:
```python
class AnthropicVisionAPI(VisionAPIBase):
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def _validate_credentials(self):
        # API 클라이언트 초기화

    def analyze_image(self, image, prompt):
        # 이미지 분석 로직

    def get_provider_name(self):
        return "Anthropic"
```

3. `api/__init__.py`에 등록:
```python
from .anthropic_api import AnthropicVisionAPI

class VisionAPIFactory:
    _providers = {
        ...
        'anthropic': AnthropicVisionAPI,
    }
```

---

## 7. ROS 2 토픽 요약

| 토픽 | 타입 | 방향 | 설명 |
|------|------|------|------|
| `/camera/image_raw` | `sensor_msgs/Image` | 입력 | 카메라 이미지 |
| `/camera/stable` | `std_msgs/Bool` | 입력 | 카메라 안정화 상태 |
| `/vision/analysis_result` | `std_msgs/String` | 출력 | AI 분석 결과 텍스트 |
