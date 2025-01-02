FROM python:3.11-slim

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYTHONDONTWRITEBYTECODE=1 
    
RUN pip install poetry==1.8.5

WORKDIR /app

RUN apt-get update -y \
    && apt-get install --no-install-recommends --no-install-suggests -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*
    
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

COPY . .

ENTRYPOINT [ "poetry", "run", "python", "bot.py" ]