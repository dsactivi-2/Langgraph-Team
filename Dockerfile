FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY agents ./agents
COPY docs ./docs
COPY js-adapters ./js-adapters
COPY langgraph.json ./
COPY prompts ./prompts
COPY skills ./skills
COPY templates ./templates

RUN pip install --no-cache-dir .

RUN addgroup --system app && adduser --system --ingroup app app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

CMD ["uvicorn", "langgraph_builder_team.api:app", "--host", "0.0.0.0", "--port", "8000"]
