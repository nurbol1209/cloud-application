FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Зависимости копируются и устанавливаются отдельным слоем:
# изменения исходного кода не инвалидируют этот слой.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/storage/objects \
    && chown -R appuser:appuser /app/storage

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser migrations ./migrations
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser run.py ./

USER appuser

EXPOSE 8000

LABEL org.opencontainers.image.title="Cloud Application" \
      org.opencontainers.image.version="0.7" \
      org.opencontainers.image.description="Cloud Application REST API on FastAPI"

CMD ["python", "run.py"]
