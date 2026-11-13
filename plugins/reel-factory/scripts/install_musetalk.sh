#!/usr/bin/env bash
# MuseTalk local lip-sync backend for reel-factory (RTX 3050 4 GB: fp16 inference). Isolated venv; idempotent.
set -e
D="$HOME/.reel-factory/presenter"
mkdir -p "$D" && cd "$D"
[ -d MuseTalk ] || git clone --depth 1 https://github.com/TMElyralab/MuseTalk.git
[ -d venv ] || uv venv --python 3.10 venv
export UV_HTTP_TIMEOUT=${UV_HTTP_TIMEOUT:-900}
PY="$D/venv/Scripts/python.exe"
echo "== torch (cu118)"
uv pip install --python "$PY" torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
echo "== musetalk deps (inference only: no tensorflow/gradio)"
uv pip install --python "$PY" diffusers==0.30.2 accelerate==0.28.0 numpy==1.23.5 opencv-python==4.9.0.80 soundfile==0.12.1 \
  transformers==4.39.2 "huggingface_hub==0.30.2" librosa==0.11.0 einops==0.8.1 gdown requests "imageio[ffmpeg]" omegaconf ffmpeg-python moviepy openmim setuptools
echo "== openmmlab (prebuilt wheels for torch2.0/cu118)"
uv pip install --python "$PY" mmengine
uv pip install --python "$PY" "mmcv==2.0.1" -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.0/index.html
uv pip install --python "$PY" pip "setuptools<70" wheel  # mmengine/mmpose still import pkg_resources
uv pip install --python "$PY" --no-build-isolation chumpy  # mmpose dep; its build needs pip
uv pip install --python "$PY" "mmdet==3.1.0" "mmpose==1.1.0"
echo "== weights"
cd MuseTalk
mkdir -p models
"$PY" - <<'PYEOF'
from huggingface_hub import snapshot_download, hf_hub_download
import os
os.makedirs("models", exist_ok=True)
snapshot_download("TMElyralab/MuseTalk", local_dir="models", allow_patterns=["musetalkV15/*"])
snapshot_download("stabilityai/sd-vae-ft-mse", local_dir="models/sd-vae", allow_patterns=["config.json", "diffusion_pytorch_model.bin"])
snapshot_download("openai/whisper-tiny", local_dir="models/whisper", allow_patterns=["config.json", "pytorch_model.bin", "preprocessor_config.json"])
hf_hub_download("yzd-v/DWPose", "dw-ll_ucoco_384.pth", local_dir="models/dwpose")
hf_hub_download("ByteDance/LatentSync", "latentsync_syncnet.pt", local_dir="models/syncnet")
print("hf weights ok")
PYEOF
mkdir -p models/face-parse-bisent
[ -f models/face-parse-bisent/79999_iter.pth ] || "$D/venv/Scripts/gdown.exe" "https://drive.google.com/uc?id=154JgKpzCPW82qINcVieuPH3fZ2e0P812" -O models/face-parse-bisent/79999_iter.pth
[ -f models/face-parse-bisent/resnet18-5c106cde.pth ] || curl -L https://download.pytorch.org/models/resnet18-5c106cde.pth -o models/face-parse-bisent/resnet18-5c106cde.pth
echo "== patch: preprocessing device selectable (MUSETALK_PREPROC_DEVICE)"
"$PY" - <<'PYEOF'
p = "musetalk/utils/preprocessing.py"
t = open(p, encoding="utf-8").read()
if "MUSETALK_PREPROC_DEVICE" not in t:
    t = t.replace('device = torch.device("cuda" if torch.cuda.is_available() else "cpu")', 'import os
device = torch.device(os.environ.get("MUSETALK_PREPROC_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu"))')
    t = t.replace('device = "cuda" if torch.cuda.is_available() else "cpu"', 'device = os.environ.get("MUSETALK_PREPROC_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")')
    open(p, "w", encoding="utf-8").write(t)
PYEOF
echo "== check"
"$PY" -c "import torch, mmcv, mmpose; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'mmcv', mmcv.__version__)"
echo MUSETALK_READY
