FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Warsaw
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalacja uv
RUN pip install --no-cache-dir uv

# Użytkownik i grupa systemowa
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

RUN mkdir -p /app/logs && chown appuser:appgroup /app /app/logs

# Zależności
COPY pyproject.toml .

RUN uv pip compile pyproject.toml -o requirements.txt && \
    uv pip sync --system --no-cache requirements.txt && \
    rm requirements.txt

# Kopiowanie kodu aplikacji
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
