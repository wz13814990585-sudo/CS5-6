FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY dashboard/frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY dashboard/frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY dashboard/requirements.txt /app/dashboard/requirements.txt
RUN pip install --no-cache-dir -r dashboard/requirements.txt && useradd --uid 10001 --create-home appuser
COPY dashboard/server/ /app/dashboard/server/
COPY dashboard/start.py /app/dashboard/start.py
COPY --from=frontend /build/dist/ /app/dashboard/frontend/dist/
COPY FINAL_OUTPUTS/01_saved_model_replay/verified_replay/ /app/FINAL_OUTPUTS/01_saved_model_replay/verified_replay/
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"
CMD ["python", "dashboard/start.py", "--host", "0.0.0.0", "--port", "8000"]
