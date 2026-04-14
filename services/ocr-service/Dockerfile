# CUDA 11.8 runtime + cuDNN; matches paddlepaddle-gpu cu118 wheels.
FROM pytorch/pytorch:2.3.1-cuda11.8-cudnn8-runtime

# Base image sets LD_LIBRARY_PATH only under /usr/local/nvidia/*. Paddle also needs
# libnvrtc and cuDNN from the conda/python environment during GPU inference.
ENV LD_LIBRARY_PATH=/opt/conda/lib:/opt/conda/lib/python3.10/site-packages/nvidia/cudnn/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# PaddlePaddle GPU (CUDA 11.8 — same as PyTorch base image).
RUN pip install --no-cache-dir paddlepaddle-gpu==2.6.2 \
    -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
RUN pip install --no-cache-dir nvidia-cudnn-cu11==8.9.6.50
# Paddle dlopen() uses unversioned sonames; conda ships versioned .so only.
RUN CUDNN_LIB="$(/opt/conda/bin/python -c "import glob,site; p=site.getsitepackages()[0]; print(glob.glob(p+'/nvidia/cudnn/lib')[0])")" \
    && ln -sfn libcudnn.so.8 "${CUDNN_LIB}/libcudnn.so" \
    && ln -sfn libcublas.so.11 /opt/conda/lib/libcublas.so \
    && ln -sfn libcublasLt.so.11 /opt/conda/lib/libcublasLt.so

COPY services/ocr-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/ocr-service/app ./app
ENV PYTHONUNBUFFERED=1
ENV MODEL_CACHE_DIR=/models_cache
# Single-GPU containers: default to first card (override in compose if needed).
ENV CUDA_VISIBLE_DEVICES=0
ENV ML_REQUIRE_GPU=true
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
