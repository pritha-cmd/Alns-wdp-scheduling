FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so this layer is cached between code changes.
# highspy is pinned to 1.12.0: newer releases segfaulted in the ILP baseline.
COPY requirements.txt requirements-optional.txt ./
RUN pip install -r requirements.txt -r requirements-optional.txt "highspy==1.12.0"

COPY . .

# Default: run the test suite. Override the command to run anything else.
CMD ["python", "-m", "pytest", "tests/", "-v"]
