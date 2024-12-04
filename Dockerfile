FROM python:3.12-slim

# Install pipx
RUN python3 -m pip install --upgrade pipx

# Set environment variables for pipx
ENV PIPX_BIN_DIR=/opt/pipx/bin
ENV PIPX_HOME=/opt/pipx/home
ENV PATH=${PIPX_BIN_DIR}:${PATH}

# Set the working directory:
RUN mkdir /app
WORKDIR /app

# Copy in the python prereq files:
COPY ./pyproject.toml ./poetry.lock /app/

# Install packages using pipx
RUN pipx install black
RUN pipx install isort

# Install poetry
RUN pipx install poetry && \
    poetry lock --no-update && \
    poetry config virtualenvs.create false

# Expose the port that the app runs on:
EXPOSE 5000

# Install only python dependencies (skipping dev libraries):
RUN poetry install --no-root

# Copy in the rest of the files:
COPY . /app

RUN export FLASK_DEBUG=1

CMD ["poetry", "run", "gunicorn", "wsgi:app", "-b", "0.0.0.0:5000", "--workers=4"]