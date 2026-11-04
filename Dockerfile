# syntax=docker/dockerfile:1
FROM hackyo/uv:0

USER appuser
WORKDIR /home/appuser/ddddocr-api

COPY --chown=appuser:appuser pyproject.toml .python-version main.py ./
COPY --chown=appuser:appuser app ./app

RUN set -eux; \
    uv sync --no-cache

CMD ["uv", "run", "--no-sync", "main.py"]
