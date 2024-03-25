# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

ARG PYTHON_VERSION=3.10.12
FROM python:${PYTHON_VERSION} as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

ENV POETRY_VIRTUALENVS_CREATE=false


# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

# Install system dependencies
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

RUN pip install poetry
RUN pip install --upgrade pip setuptools wheel

# https://github.com/openai/chatgpt-retrieval-plugin/issues/131
RUN apt-get install -y gcc curl
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
SHELL ["bash", "-lc"]

# Disable PEP 517 builds for sudachipy
RUN pip wheel --no-cache-dir --use-pep517 "sudachipy==0.6.8"
# https://github.com/huggingface/transformers/issues/2831
RUN pip install transformers

RUN poetry config installer.max-workers 10
# https://blog.tzing.tw/posts/rethink-before-installing-poetry-into-docker-94f18935
RUN poetry install --no-interaction --no-ansi --no-dev

# Run the application.
CMD poetry run python main.py 