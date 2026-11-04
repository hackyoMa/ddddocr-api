# syntax=docker/dockerfile:1
FROM hackyo/uv:0

USER appuser
WORKDIR /home/appuser/ddddocr-api

COPY --chown=appuser:appuser pyproject.toml .python-version main.py ./
COPY --chown=appuser:appuser app ./app

RUN set -eux; \
    uv sync --no-cache

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 CMD curl -fsI -o /dev/null http://localhost:8000/health
EXPOSE 8000

CMD ["uv", "run", "--no-sync", "main.py"]
