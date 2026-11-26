# syntax=docker/dockerfile:1
FROM python:3.14-slim-trixie AS dependencies
WORKDIR /build
COPY requirements.lock ./
RUN pip install --no-cache-dir --disable-pip-version-check --require-hashes \
    --only-binary=:all: --prefix=/install -r requirements.lock

FROM python:3.14-slim-trixie AS runtime
COPY --from=dependencies /install /usr/local
WORKDIR /app
COPY deco_mcp_local /app/deco_mcp_local
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin deco
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
ENTRYPOINT ["python", "-B", "-m", "deco_mcp_local"]

FROM runtime AS test
COPY tests /app/tests
ENTRYPOINT ["python", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]
