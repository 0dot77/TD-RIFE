"""
RIFE ONNX 모델 다운로드 스크립트.
HuggingFace에서 rife v4.9 ONNX 모델을 다운로드합니다.
"""

import os
import urllib.request
import sys

MODEL_URL = "https://huggingface.co/yuvraj108c/rife-onnx/resolve/main/rife49_ensemble_True_scale_1_sim.onnx"
MODEL_NAME = "rife49_ensemble_True_scale_1_sim.onnx"


def download_model(dest_dir=None):
    if dest_dir is None:
        dest_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, MODEL_NAME)

    if os.path.exists(dest_path):
        print(f"모델이 이미 존재합니다: {dest_path}")
        return dest_path

    print(f"다운로드 중: {MODEL_URL}")
    print(f"저장 위치: {dest_path}")

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        pct = min(downloaded / total_size * 100, 100) if total_size > 0 else 0
        bar = "#" * int(pct // 2)
        sys.stdout.write(f"\r[{bar:<50}] {pct:.1f}%")
        sys.stdout.flush()

    urllib.request.urlretrieve(MODEL_URL, dest_path, reporthook=progress)
    print(f"\n다운로드 완료: {dest_path}")
    return dest_path


if __name__ == "__main__":
    download_model()
