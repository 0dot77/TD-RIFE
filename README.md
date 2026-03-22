[English](#english) | [한국어](#한국어)

# TD-RIFE

## English

A **RIFE real-time video frame interpolation** plugin for TouchDesigner.

Generates intermediate frames between two frames using AI to create **slow motion**, **frame interpolation**, and **time remapping** effects.

![RIFE](https://img.shields.io/badge/RIFE-v4.9-blue) ![ONNX](https://img.shields.io/badge/ONNX-Runtime-green) ![TD](https://img.shields.io/badge/TouchDesigner-2025+-orange)

### Features

- Real-time frame interpolation based on **RIFE v4.9**
- **ONNX Runtime GPU** acceleration (CUDA / TensorRT)
- Arbitrary **Timestep** interpolation support — generate any point between 0.0 (Frame A) and 1.0 (Frame B)
- Script TOP based — drop-in usage via `.tox`
- Automatic resolution padding (pads to multiples of 32, restores original size on output)

### Requirements

| Item | Minimum | Recommended |
|---|---|---|
| TouchDesigner | 2025.30000+ | Latest build |
| GPU | NVIDIA GTX 1060 (CUDA) | RTX 3060+ |
| VRAM | 4GB | 8GB+ |
| Python packages | `onnxruntime-gpu`, `numpy` | — |

> **Note:** On Mac (Apple Silicon), only CPU mode is available due to lack of CUDA. Real-time performance requires an NVIDIA GPU.

### Quick Start

#### Step 1: Download the Model

In terminal:

```bash
cd TD-RIFE
python scripts/download_model.py
```

Or download manually from [HuggingFace](https://huggingface.co/yuvraj108c/rife-onnx/tree/main):
- File: `rife49_ensemble_True_scale_1_sim.onnx` (21.5MB)
- Save to: `models/` folder

#### Step 2: Install Python Packages

You need to install `onnxruntime-gpu` in TouchDesigner's Python environment.

**Method A: TDPyEnvManager (built into TD 2025)**

```
# In TD Textport:
import subprocess, sys
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'onnxruntime-gpu'])
```

**Method B: From system terminal**

```bash
# Find TD's Python path and install directly
# Windows example:
"C:\Program Files\Derivative\TouchDesigner\bin\python.exe" -m pip install onnxruntime-gpu

# macOS example (CPU only):
/Applications/TouchDesigner.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 -m pip install onnxruntime
```

#### Step 3: Setup in TouchDesigner

##### 3-1. Create Base COMP

1. Right-click in the Network Editor → **Add Operator** → **COMP** → **Base**
2. Rename to `TD_RIFE`
3. Enter the Base COMP (double-click)

##### 3-2. Create and Configure Script TOP

1. Right-click inside → **Add Operator** → **TOP** → **Script**
2. Rename to `script_rife`
3. Paste the contents of `td/TDRIFE_Callbacks.py` into the Script TOP's **Callbacks DAT**
   - Script TOP parameters → **Callbacks DAT** field → open the linked Text DAT and paste the code

##### 3-3. Connect Inputs

1. Prepare two frame sources for interpolation (e.g., 2 Movie File In TOPs, or Cache TOP + Delay)
2. **input0** (left input): Previous frame (Frame A)
3. **input1** (right input): Next frame (Frame B)

##### 3-4. Parameter Settings

After creating the Script TOP, parameters are automatically generated on the Custom page:

| Parameter | Description | Default |
|---|---|---|
| **Timestep** | Interpolation position. 0.0=Frame A, 0.5=midpoint, 1.0=Frame B | `0.5` |
| **Model Path** | Absolute path to the ONNX model file | (empty — must be set) |
| **Provider** | Inference engine. CUDA (default), TensorRT (faster), CPU (slower) | `CUDA` |
| **Active** | Enable/disable interpolation toggle | `On` |

**How to set Model Path:**
- Enter the **absolute path** to `models/rife49_ensemble_True_scale_1_sim.onnx`
- Example: `C:/Users/username/Desktop/TD-RIFE/models/rife49_ensemble_True_scale_1_sim.onnx`

##### 3-5. Using the Extension (Optional)

For automatic model detection and dependency checking:

1. Add a Text DAT to the Base COMP (`TD_RIFE`) → name: `text_extension`
2. Paste the contents of `td/TDRIFE_Extension.py`
3. Base COMP parameters → **Extensions** → OP: `text_extension`, Name: `TDRIFEExt`
4. Run in Textport:

```python
op('TD_RIFE').ext.TDRIFEExt.CheckDependencies()  # Check packages
op('TD_RIFE').ext.TDRIFEExt.DownloadModel()       # Download model
op('TD_RIFE').ext.TDRIFEExt.Setup()                # Auto setup
```

### Usage Examples

#### Slow Motion (Video File)

```
[Movie File In TOP] ──→ [Cache TOP (size=2)] ──→ frame[0] ──→ [script_rife input0]
                                                  frame[1] ──→ [script_rife input1]
                                                               Timestep: 0.5
                                                               ↓
                                                           [Interpolated Frame]
```

1. Load video with **Movie File In TOP**
2. Buffer 2 consecutive frames with **Cache TOP** (Size=2)
3. Connect Cache's `[0]` and `[1]` to script_rife's input0 and input1 respectively
4. Animate Timestep from 0.0 to 1.0 to smoothly transition between frames

#### Live Camera Input

```
[Video Device In TOP] ──→ [Cache TOP] ──→ [Delay TOP (1frame)] ──→ input0
                              └─────────────────────────────────→ input1
```

1. Capture webcam with **Video Device In TOP**
2. Store current frame with **Cache TOP**
3. Generate previous frame with **Delay TOP** (1 frame)
4. Connect both frames to script_rife

#### Multiple Interpolation (2x → 4x)

Generate multiple interpolated frames with different Timestep values:

```
script_rife_1 (Timestep=0.25) ──→ [Switch TOP]
script_rife_2 (Timestep=0.50) ──→     ↓
script_rife_3 (Timestep=0.75) ──→ [Sequential output]
```

### Performance Guide

| GPU | Resolution | Expected FPS | Notes |
|---|---|---|---|
| RTX 3060 | 720p | ~30 fps | Real-time capable |
| RTX 3080 | 1080p | ~30 fps | Real-time capable |
| RTX 4090 | 1080p | ~60 fps | High performance |
| RTX 4090 | 4K | ~15 fps | Non-real-time |
| GTX 1060 | 720p | ~10 fps | Non-real-time |

> **Tip:** Using the TensorRT Provider is ~2x faster than CUDA (engine build takes several minutes on first run).

### Troubleshooting

#### "Cannot find onnxruntime-gpu"
→ Check the package installation from Step 2. You may need to restart TD.

#### "CUDAExecutionProvider not detected"
→ `onnxruntime-gpu` must be installed instead of `onnxruntime`.
→ Verify that CUDA Toolkit is installed.

#### Output is a black screen
→ Check that Model Path is correctly set (absolute path).
→ Verify that both input TOPs are connected.
→ Make sure the Active toggle is On.

#### Slow performance
→ Try changing Provider to `TensorRT`.
→ Reduce input resolution (downscale with Resolution TOP).
→ Set Script TOP's Cook Type to "Explicit" and cook only when needed.

#### NumPy version conflict error
→ TD's built-in NumPy and onnxruntime's required version may conflict.
→ Using TD 2025.30000+ is recommended (TDPyEnvManager built-in).

### Project Structure

```
TD-RIFE/
├── td/                          # TouchDesigner files
│   ├── TDRIFE_Extension.py      # Base COMP Extension (auto setup, dependency check)
│   └── TDRIFE_Callbacks.py      # Script TOP callbacks (core inference logic)
├── scripts/
│   └── download_model.py        # ONNX model download script
├── models/                      # ONNX model storage folder (.gitignore)
│   └── rife49_ensemble_*.onnx   # (download required)
├── .gitignore
└── README.md
```

### Credits

- **RIFE** (Real-Time Intermediate Flow Estimation): [Practical-RIFE](https://github.com/hzwer/Practical-RIFE) by Zhewei Huang et al.
- **ONNX Model**: [yuvraj108c/rife-onnx](https://huggingface.co/yuvraj108c/rife-onnx)
- RIFE Paper: "Real-Time Intermediate Flow Estimation for Video Frame Interpolation" (ECCV 2022)

### License

MIT License

---

## 한국어

TouchDesigner용 **RIFE 실시간 비디오 프레임 보간** 플러그인.

두 프레임 사이의 중간 프레임을 AI로 생성하여 **슬로우 모션**, **프레임 보간**, **타임 리매핑** 효과를 만듭니다.

![RIFE](https://img.shields.io/badge/RIFE-v4.9-blue) ![ONNX](https://img.shields.io/badge/ONNX-Runtime-green) ![TD](https://img.shields.io/badge/TouchDesigner-2025+-orange)

### 기능

- **RIFE v4.9** 기반 실시간 프레임 보간
- **ONNX Runtime GPU** 가속 (CUDA / TensorRT)
- 임의 시간값(**Timestep**) 보간 지원 — 0.0(프레임A)~1.0(프레임B) 사이 어느 지점이든 생성
- Script TOP 기반 — `.tox`로 드롭인 사용
- 해상도 자동 패딩 (32의 배수로 맞춤, 출력 시 원본 크기로 복원)

### 요구사항

| 항목 | 최소 | 권장 |
|---|---|---|
| TouchDesigner | 2025.30000+ | 최신 빌드 |
| GPU | NVIDIA GTX 1060 (CUDA) | RTX 3060+ |
| VRAM | 4GB | 8GB+ |
| Python 패키지 | `onnxruntime-gpu`, `numpy` | — |

> **참고:** Mac (Apple Silicon)에서는 CUDA가 없어 CPU 모드만 가능합니다. 실시간 성능은 NVIDIA GPU가 필요합니다.

### 빠른 시작 (Quick Start)

#### Step 1: 모델 다운로드

터미널에서:

```bash
cd TD-RIFE
python scripts/download_model.py
```

또는 [HuggingFace](https://huggingface.co/yuvraj108c/rife-onnx/tree/main)에서 수동 다운로드:
- 파일: `rife49_ensemble_True_scale_1_sim.onnx` (21.5MB)
- 저장 위치: `models/` 폴더

#### Step 2: Python 패키지 설치

TouchDesigner의 Python에 `onnxruntime-gpu`를 설치해야 합니다.

**방법 A: TDPyEnvManager (TD 2025 내장)**

```
# TD Textport에서:
import subprocess, sys
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'onnxruntime-gpu'])
```

**방법 B: 시스템 터미널에서**

```bash
# TD의 Python 경로를 찾아서 직접 설치
# Windows 예시:
"C:\Program Files\Derivative\TouchDesigner\bin\python.exe" -m pip install onnxruntime-gpu

# macOS 예시 (CPU only):
/Applications/TouchDesigner.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 -m pip install onnxruntime
```

#### Step 3: TouchDesigner에서 세팅

##### 3-1. Base COMP 생성

1. 네트워크 에디터에서 우클릭 → **Add Operator** → **COMP** → **Base**
2. 이름을 `TD_RIFE`로 변경
3. Base COMP 안으로 들어가기 (더블클릭)

##### 3-2. Script TOP 생성 및 설정

1. 안에서 우클릭 → **Add Operator** → **TOP** → **Script**
2. 이름을 `script_rife`로 변경
3. `td/TDRIFE_Callbacks.py`의 내용을 Script TOP의 **Callbacks DAT**에 붙여넣기
   - Script TOP 파라미터 → **Callbacks DAT** 항목 → 연결된 Text DAT을 열어서 코드 붙여넣기

##### 3-3. 입력 연결

1. 보간할 두 프레임 소스를 준비 (예: Movie File In TOP 2개, 또는 Cache TOP + 딜레이)
2. **input0** (왼쪽 입력): 이전 프레임 (Frame A)
3. **input1** (오른쪽 입력): 다음 프레임 (Frame B)

##### 3-4. 파라미터 설정

Script TOP 생성 후 Custom 페이지에 파라미터가 자동 생성됩니다:

| 파라미터 | 설명 | 기본값 |
|---|---|---|
| **Timestep** | 보간 위치. 0.0=프레임A, 0.5=정중앙, 1.0=프레임B | `0.5` |
| **Model Path** | ONNX 모델 파일의 절대 경로 | (비어있음 — 설정 필요) |
| **Provider** | 추론 엔진. CUDA(기본), TensorRT(빠름), CPU(느림) | `CUDA` |
| **Active** | 보간 활성화/비활성화 토글 | `On` |

**Model Path 설정 방법:**
- `models/rife49_ensemble_True_scale_1_sim.onnx`의 **절대 경로**를 입력
- 예: `C:/Users/username/Desktop/TD-RIFE/models/rife49_ensemble_True_scale_1_sim.onnx`

##### 3-5. Extension 사용 (선택사항)

자동 모델 감지와 의존성 확인을 원하면:

1. Base COMP(`TD_RIFE`)에 Text DAT 추가 → 이름: `text_extension`
2. `td/TDRIFE_Extension.py` 내용 붙여넣기
3. Base COMP 파라미터 → **Extensions** → OP: `text_extension`, Name: `TDRIFEExt`
4. Textport에서 실행:

```python
op('TD_RIFE').ext.TDRIFEExt.CheckDependencies()  # 패키지 확인
op('TD_RIFE').ext.TDRIFEExt.DownloadModel()       # 모델 다운로드
op('TD_RIFE').ext.TDRIFEExt.Setup()                # 자동 설정
```

### 활용 예시

#### 슬로우 모션 (비디오 파일)

```
[Movie File In TOP] ──→ [Cache TOP (size=2)] ──→ frame[0] ──→ [script_rife input0]
                                                  frame[1] ──→ [script_rife input1]
                                                               Timestep: 0.5
                                                               ↓
                                                           [보간된 프레임]
```

1. **Movie File In TOP**으로 영상 로드
2. **Cache TOP** (Size=2)으로 연속 2프레임 버퍼링
3. Cache의 `[0]`과 `[1]`을 각각 script_rife의 input0, input1에 연결
4. Timestep을 0.0~1.0으로 애니메이션하면 프레임 사이를 부드럽게 이동

#### 라이브 카메라 입력

```
[Video Device In TOP] ──→ [Cache TOP] ──→ [Delay TOP (1frame)] ──→ input0
                              └─────────────────────────────────→ input1
```

1. **Video Device In TOP**으로 웹캠 입력
2. **Cache TOP**으로 현재 프레임 저장
3. **Delay TOP** (1프레임)으로 이전 프레임 생성
4. 두 프레임을 script_rife에 연결

#### 다중 보간 (2x → 4x)

여러 Timestep 값으로 여러 보간 프레임 생성:

```
script_rife_1 (Timestep=0.25) ──→ [Switch TOP]
script_rife_2 (Timestep=0.50) ──→     ↓
script_rife_3 (Timestep=0.75) ──→ [순서대로 출력]
```

### 성능 가이드

| GPU | 해상도 | 예상 FPS | 비고 |
|---|---|---|---|
| RTX 3060 | 720p | ~30 fps | 실시간 가능 |
| RTX 3080 | 1080p | ~30 fps | 실시간 가능 |
| RTX 4090 | 1080p | ~60 fps | 고성능 |
| RTX 4090 | 4K | ~15 fps | 비실시간 |
| GTX 1060 | 720p | ~10 fps | 비실시간 |

> **팁:** TensorRT Provider를 사용하면 CUDA 대비 ~2x 빨라집니다 (첫 실행 시 엔진 빌드에 수 분 소요).

### 트러블슈팅

#### "onnxruntime-gpu를 찾을 수 없습니다"
→ Step 2의 패키지 설치를 확인하세요. TD를 재시작해야 할 수 있습니다.

#### "CUDAExecutionProvider 미감지"
→ `onnxruntime` 대신 `onnxruntime-gpu`가 설치되어야 합니다.
→ CUDA Toolkit이 설치되어 있는지 확인하세요.

#### 출력이 검은 화면
→ Model Path가 올바르게 설정되었는지 확인하세요 (절대 경로).
→ 입력 TOP 2개가 모두 연결되어 있는지 확인하세요.
→ Active 토글이 On인지 확인하세요.

#### 느린 성능
→ Provider를 `TensorRT`로 변경해보세요.
→ 입력 해상도를 낮춰보세요 (Resolution TOP으로 다운스케일).
→ Script TOP의 Cook Type을 "Explicit"으로 설정하고 필요할 때만 cook하세요.

#### NumPy 버전 충돌 에러
→ TD 내장 NumPy와 onnxruntime 요구 버전이 충돌할 수 있습니다.
→ TD 2025.30000+ 사용을 권장합니다 (TDPyEnvManager 내장).

### 프로젝트 구조

```
TD-RIFE/
├── td/                          # TouchDesigner 파일
│   ├── TDRIFE_Extension.py      # Base COMP Extension (자동 설정, 의존성 확인)
│   └── TDRIFE_Callbacks.py      # Script TOP 콜백 (핵심 추론 로직)
├── scripts/
│   └── download_model.py        # ONNX 모델 다운로드 스크립트
├── models/                      # ONNX 모델 저장 폴더 (.gitignore)
│   └── rife49_ensemble_*.onnx   # (다운로드 필요)
├── .gitignore
└── README.md
```

### 크레딧

- **RIFE** (Real-Time Intermediate Flow Estimation): [Practical-RIFE](https://github.com/hzwer/Practical-RIFE) by Zhewei Huang et al.
- **ONNX 모델**: [yuvraj108c/rife-onnx](https://huggingface.co/yuvraj108c/rife-onnx)
- RIFE 논문: "Real-Time Intermediate Flow Estimation for Video Frame Interpolation" (ECCV 2022)

### 라이선스

MIT License
