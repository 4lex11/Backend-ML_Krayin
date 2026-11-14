FROM python:3.14.6-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 nginx supervisor \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY ML/requirements.txt ML/requirements.txt
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && pip check
COPY ML/__init__.py ML/features.py ML/inference.py ML/
COPY ML/artifacts/churn180-v1/model.joblib ML/artifacts/churn180-v1/metadata.json ML/artifacts/churn180-v1/
COPY backend/ backend/
COPY deploy/render/ /app/deploy/render/
RUN useradd --create-home app && mkdir -p /tmp/nginx && chown -R app:app /tmp/nginx
USER app
EXPOSE 10000
CMD ["python", "deploy/render/start.py"]
