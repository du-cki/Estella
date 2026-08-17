FROM alpine/git AS mipha

WORKDIR /repo
COPY . .

RUN git config --global url."https://github.com/".insteadOf "git@github.com:" \
    && git submodule update --init -- vendor/mipha \
    && cd vendor/mipha \
    && git config submodule.utilities/shared.url https://github.com/AbstractUmbra/_utilities.git \
    && git submodule update --init -- utilities/shared \
    && sed -i '/@app_commands\.guilds(discord\.Object(id=DANNYWARE_ID), discord\.Object(id=705500489248145459))/d' extensions/heights/cog.py

FROM python:3.12-alpine

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

RUN poetry add matplotlib lru-dict lxml python-dateutil parsedatetime

RUN poetry add git+https://github.com/Rapptz/discord-ext-menus

COPY . .
COPY --from=mipha /repo/vendor/mipha/extensions/heights ./ext/heights
COPY --from=mipha /repo/vendor/mipha/utilities          ./utilities

RUN mkdir -p configs/

ENTRYPOINT [ "poetry", "run", "python", "bot.py" ]
