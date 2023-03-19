FROM python:3.10.9-slim-bullseye

ARG CRON_SCHEDULE="*/5 * * * *"
ARG KUMA_PUSH_URL=""

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    cron

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN /root/.local/bin/poetry export -o requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

# Install module
COPY . .
RUN pip install --no-cache-dir --no-deps .

RUN echo "\
$CRON_SCHEDULE /usr/local/bin/python /src/main.py --url '$KUMA_PUSH_URL' >> /logs/logfile 2>&1 \
" > crontab

RUN crontab crontab

CMD ["cron", "-f"]