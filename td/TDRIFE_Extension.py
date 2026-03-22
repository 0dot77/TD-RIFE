"""
TD-RIFE Extension.
Base COMP에 부착하여 RIFE 프레임 보간 기능을 관리합니다.

이 Extension은 다음을 처리합니다:
- ONNX 모델 경로 자동 감지
- onnxruntime-gpu 설치 확인
- Script TOP 초기화
"""

import os
import subprocess
import sys


class TDRIFEExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self._model_path = None

    @property
    def ModelPath(self):
        """ONNX 모델 파일 경로를 반환."""
        if self._model_path and os.path.exists(self._model_path):
            return self._model_path

        # 프로젝트 폴더 기준으로 models/ 탐색
        project_dir = project.folder
        candidates = [
            os.path.join(project_dir, "models", "rife49_ensemble_True_scale_1_sim.onnx"),
            os.path.join(project_dir, "TD-RIFE", "models", "rife49_ensemble_True_scale_1_sim.onnx"),
            os.path.join(os.path.dirname(__file__), "..", "models", "rife49_ensemble_True_scale_1_sim.onnx"),
        ]

        for path in candidates:
            normalized = os.path.normpath(path)
            if os.path.exists(normalized):
                self._model_path = normalized
                print(f"[TD-RIFE] 모델 발견: {normalized}")
                return normalized

        print("[TD-RIFE] 모델을 찾을 수 없습니다. Model Path를 수동으로 설정하거나")
        print("[TD-RIFE] scripts/download_model.py를 실행하세요.")
        return ""

    def CheckDependencies(self):
        """필요한 Python 패키지 설치 여부 확인."""
        missing = []
        try:
            import onnxruntime
            print(f"[TD-RIFE] onnxruntime {onnxruntime.__version__} 감지")
            providers = onnxruntime.get_available_providers()
            print(f"[TD-RIFE] 사용 가능한 Provider: {providers}")
            if "CUDAExecutionProvider" not in providers:
                print("[TD-RIFE] 경고: CUDAExecutionProvider 미감지. GPU 가속 불가.")
                print("[TD-RIFE] onnxruntime-gpu를 설치하세요.")
        except ImportError:
            missing.append("onnxruntime-gpu")

        try:
            import numpy
            print(f"[TD-RIFE] numpy {numpy.__version__} 감지")
        except ImportError:
            missing.append("numpy")

        if missing:
            print(f"[TD-RIFE] 누락된 패키지: {', '.join(missing)}")
            print("[TD-RIFE] 설치 방법:")
            print(f"  pip install {' '.join(missing)}")
            return False

        return True

    def Setup(self):
        """Script TOP 초기화. 모델 경로를 자동 설정."""
        ok = self.CheckDependencies()
        if not ok:
            return

        model = self.ModelPath
        if not model:
            return

        # Script TOP의 Model Path 파라미터 업데이트
        script_top = self.ownerComp.op("script_rife")
        if script_top:
            script_top.par.Modelpath = model
            print(f"[TD-RIFE] Script TOP 모델 경로 설정: {model}")
        else:
            print("[TD-RIFE] 'script_rife' Script TOP을 찾을 수 없습니다.")

    def DownloadModel(self):
        """ONNX 모델을 HuggingFace에서 다운로드."""
        project_dir = project.folder
        models_dir = os.path.join(project_dir, "models")
        dest = os.path.join(models_dir, "rife49_ensemble_True_scale_1_sim.onnx")

        if os.path.exists(dest):
            print(f"[TD-RIFE] 모델이 이미 존재합니다: {dest}")
            return

        url = "https://huggingface.co/yuvraj108c/rife-onnx/resolve/main/rife49_ensemble_True_scale_1_sim.onnx"
        print(f"[TD-RIFE] 다운로드 중: {url}")

        import urllib.request
        os.makedirs(models_dir, exist_ok=True)
        urllib.request.urlretrieve(url, dest)
        print(f"[TD-RIFE] 다운로드 완료: {dest}")
        self._model_path = dest
