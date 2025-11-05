FROM python:3.10-slim

# Set build-time arguments
ARG UID=1000
ARG GID=1000
ARG REQUIREMENTS=./requirements.txt
ARG SERVICE_NAME=app

ENV USERNAME=user
ENV HOME=/home/$USERNAME
ENV DEBIAN_FRONTEND=noninteractive

RUN groupadd -g $GID $USERNAME && \
    useradd -m -u $UID -g $GID -s /bin/bash $USERNAME

# Install required system dependencies including libmagic1
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="$HOME/.local/bin:$PATH"

COPY $REQUIREMENTS /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

WORKDIR $HOME/$SERVICE_NAME
COPY . .

RUN chown -R $USERNAME:$USERNAME $HOME

USER $USERNAME

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]