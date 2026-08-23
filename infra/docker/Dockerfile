# VARUNA GRID v2 — API + worker image.
# OpenDrift is NOT installed here: it resolves poorly on pip and needs conda.
# The physics worker uses infra/docker/Dockerfile.physics instead.

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/packages:/app

# GDAL/PROJ/GEOS are required by rasterio, geopandas, pyproj, shapely.
RUN apt-get update && apt-get install -y --no-install-recommends \
      gdal-bin libgdal-dev libproj-dev proj-data proj-bin libgeos-dev \
      libpq-dev gcc g++ curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY packages/ ./packages/

# Install the project (all varuna_* packages) plus runtime extras.
RUN pip install --upgrade pip setuptools wheel \
 && pip install -e .

COPY apps/ ./apps/
COPY db/ ./db/

# Non-root.
RUN useradd --create-home --uid 10001 varuna \
 && mkdir -p /app/data /app/models \
 && chown -R varuna:varuna /app
USER varuna

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ── ML variant: adds torch. Large image; build only when training/inferring. ──
FROM base AS ml
USER root
RUN pip install -e ".[ml]"
USER varuna
