FROM python:3.12-slim

WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 복사 및 설치
COPY pyproject.toml uv.lock ./
COPY workspace.toml ./
COPY README.md ./
COPY components/ ./components/
COPY bases/ ./bases/
COPY projects/ ./projects/

# 의존성 설치
RUN uv sync --frozen

# 기본 명령어 (각 서비스에서 override)
CMD ["uv", "run", "python", "-m", "projects.fluxmind-api.main"]

