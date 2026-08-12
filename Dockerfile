FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

ENV FORGELOOP_USE_MOCK=1 \
    FORGELOOP_FORCE_FILE_CREDS=1 \
    FORGELOOP_MASTER_PASSWORD=change-me-in-production \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Do NOT bake API keys into the image. Configure at runtime:
#   docker run -e FORGELOOP_MASTER_PASSWORD=... -e FORGELOOP_API_KEY=... ...
# or exec: forgeloop creds set

CMD ["uvicorn", "forgeloop.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
