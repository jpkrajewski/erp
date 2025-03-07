FROM python:3.13-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --upgrade pip

RUN apt-get update \
    && apt-get -y install libpq-dev gcc


COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .
EXPOSE 8000

RUN chmod +x  /app/docker/entrypoint.local.sh
RUN chmod +x  /app/docker/entrypoint.worker.sh

FROM builder as dev

CMD ["/app/docker/entrypoint.local.sh"]

FROM builder as prod

CMD ["/app/docker/entrypoint.local.sh"]
