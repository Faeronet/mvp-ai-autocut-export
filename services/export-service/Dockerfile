FROM python:3.11-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl && rm -rf /var/lib/apt/lists/*
COPY services/export-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/export-service/app ./app
ENV PYTHONUNBUFFERED=1
EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
