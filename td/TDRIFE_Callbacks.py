"""
TD-RIFE Script TOP Callbacks.
RIFE v4.9 ONNX 모델을 사용한 실시간 프레임 보간.

Script TOP에 이 코드를 붙여넣고, 두 개의 입력 TOP을 연결하세요.
- input0: 이전 프레임 (Frame A)
- input1: 다음 프레임 (Frame B)
- output: 보간된 중간 프레임
"""

import numpy as np


def onSetupParameters(scriptOp):
    page = scriptOp.appendCustomPage("RIFE")
    page.appendFloat("Timestep", label="Timestep", default=0.5, min=0.0, max=1.0)
    page.appendStr("Modelpath", label="Model Path", default="")
    page.appendMenu(
        "Provider",
        label="Provider",
        menuNames=["cuda", "tensorrt", "cpu"],
        menuLabels=["CUDA", "TensorRT", "CPU"],
        default="cuda",
    )
    page.appendToggle("Active", label="Active", default=True)


def onPulse(par):
    return


# 모듈 레벨 세션 (한 번만 초기화)
_session = None
_session_provider = None
_session_model = None


def _get_session(model_path, provider):
    global _session, _session_provider, _session_model

    if _session is not None and _session_provider == provider and _session_model == model_path:
        return _session

    try:
        import onnxruntime as ort
    except ImportError:
        raise ImportError(
            "onnxruntime-gpu가 설치되지 않았습니다.\n"
            "TD-PackMan 또는 TDPyEnvManager로 설치하세요:\n"
            "  pip install onnxruntime-gpu"
        )

    providers_map = {
        "cuda": ["CUDAExecutionProvider", "CPUExecutionProvider"],
        "tensorrt": [
            ("TensorrtExecutionProvider", {"trt_fp16_enable": True}),
            "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ],
        "cpu": ["CPUExecutionProvider"],
    }
    providers = providers_map.get(provider, providers_map["cuda"])

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    _session = ort.InferenceSession(model_path, sess_options=opts, providers=providers)
    _session_provider = provider
    _session_model = model_path

    actual = _session.get_providers()
    print(f"[TD-RIFE] 모델 로드 완료: {model_path}")
    print(f"[TD-RIFE] 활성 Provider: {actual}")

    return _session


def _pad_to_multiple(img, multiple=32):
    """이미지를 multiple의 배수로 패딩."""
    h, w = img.shape[2], img.shape[3]
    ph = ((h - 1) // multiple + 1) * multiple
    pw = ((w - 1) // multiple + 1) * multiple
    if ph == h and pw == w:
        return img, h, w
    padded = np.zeros((1, 3, ph, pw), dtype=img.dtype)
    padded[:, :, :h, :w] = img
    return padded, h, w


def onCook(scriptOp):
    if not scriptOp.par.Active.eval():
        return

    if len(scriptOp.inputs) < 2:
        scriptOp.clear()
        return

    model_path = scriptOp.par.Modelpath.eval()
    if not model_path:
        print("[TD-RIFE] Model Path를 설정하세요.")
        scriptOp.clear()
        return

    # 입력 읽기 (NHWC, uint8, RGBA or RGB)
    img0_raw = scriptOp.inputs[0].numpyArray(delayed=True)
    img1_raw = scriptOp.inputs[1].numpyArray(delayed=True)

    if img0_raw is None or img1_raw is None:
        scriptOp.clear()
        return

    # NHWC uint8 → RGB float32 NCHW
    img0 = img0_raw[:, :, :3].astype(np.float32) / 255.0
    img1 = img1_raw[:, :, :3].astype(np.float32) / 255.0

    # HWC → CHW → NCHW
    img0 = np.expand_dims(np.transpose(img0, (2, 0, 1)), 0)
    img1 = np.expand_dims(np.transpose(img1, (2, 0, 1)), 0)

    # 32의 배수로 패딩
    img0_p, orig_h, orig_w = _pad_to_multiple(img0)
    img1_p, _, _ = _pad_to_multiple(img1)

    # timestep
    timestep = np.array([scriptOp.par.Timestep.eval()], dtype=np.float32)

    # 추론
    provider = scriptOp.par.Provider.eval()
    session = _get_session(model_path, provider)

    result = session.run(None, {
        "img0": img0_p,
        "img1": img1_p,
        "timestep": timestep,
    })

    # 후처리: NCHW → HWC, 크롭, uint8
    out = result[0][0]  # (3, H, W)
    out = out[:, :orig_h, :orig_w]  # 패딩 제거
    out = np.transpose(out, (1, 2, 0))  # CHW → HWC
    out = (out * 255.0).clip(0, 255).astype(np.uint8)

    scriptOp.copyNumpyArray(out)
