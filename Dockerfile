FROM python:3.11-alpine

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYTHONDONTWRITEBYTECODE=1 
    
RUN pip install poetry==1.8.5

WORKDIR /app

RUN apk --no-cache add \
    bash \
    ffmpeg
    
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

COPY . .

ENTRYPOINT [ "poetry", "run", "python", "bot.py" ]