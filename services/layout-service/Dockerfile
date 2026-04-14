FROM pytorch/pytorch:2.3.1-cuda11.8-cudnn8-runtime

ENV LD_LIBRARY_PATH=/opt/conda/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/layout-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/layout-service/app ./app
ENV PYTHONUNBUFFERED=1
ENV MODEL_CACHE_DIR=/models_cache
ENV CUDA_VISIBLE_DEVICES=0
ENV ML_REQUIRE_GPU=true
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
