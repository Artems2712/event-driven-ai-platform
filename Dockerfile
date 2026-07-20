FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY ai_platform ./ai_platform

RUN pip install --no-cache-dir -e ".[runtime]"

EXPOSE 8000

CMD ["uvicorn", "ai_platform.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
