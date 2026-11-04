# ---- 前端构建 ----
FROM node:20-bookworm-slim AS web

WORKDIR /build
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate

COPY web/package.json web/pnpm-lock.yaml ./web/
WORKDIR /build/web
RUN pnpm install --frozen-lockfile

COPY web/ ./
# 产物输出到 /build/app/static（与 vite outDir 一致）
RUN pnpm build

# ---- 运行镜像 ----
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY --from=web /build/app/static ./app/static

EXPOSE 8787

# 无 root 运行
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "app"]
