FROM e2bdev/code-interpreter:latest

USER root
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required by Headless Chromium (Playwright) and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ffmpeg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Pre-install Wave 1 empirical probe Python packages & Playwright Chromium
RUN pip install --no-cache-dir \
    pypdf \
    python-pptx \
    langdetect \
    imageio-ffmpeg \
    playwright \
    pytest \
    hypothesis \
    SALib \
    scipy \
    numpy \
    && python3 -m playwright install --with-deps chromium

# Pre-install Wave 2 Gemini CLI
RUN npm install -g @google/gemini-cli@0.68.0

RUN mkdir -p /judge/out /judge/work && chmod -R 777 /judge
WORKDIR /judge
