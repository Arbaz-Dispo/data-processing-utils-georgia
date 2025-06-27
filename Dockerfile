# Ultra-fast build for Georgia Business Entity Processor
FROM ubuntu:22.04 AS base

# Prevent interactive prompts and optimize for speed
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROME_PATH=/usr/bin/google-chrome \
    DISPLAY=:99 \
    SCREEN_WIDTH=1920 \
    SCREEN_HEIGHT=1080 \
    SCREEN_DEPTH=24

# Install system packages and Chrome in one optimized layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip wget gnupg ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgtk-3-0 \
    libnspr4 libnss3 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libxss1 libxtst6 xdg-utils \
    xvfb x11-utils xfonts-base xfonts-75dpi xfonts-100dpi \
    python3-tk python3-dev scrot imagemagick \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && apt-get clean && apt-get autoremove -y

# Install Python packages (optimized for caching)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Create workspace (no unnecessary verification steps)
WORKDIR /workspace
RUN useradd -m runner && chown runner:runner /workspace

# Create startup script for Xvfb
RUN echo '#!/bin/bash\n\
echo "Starting Xvfb virtual display..."\n\
Xvfb :99 -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} -ac +extension GLX +render -noreset &\n\
export DISPLAY=:99\n\
echo "Waiting for display to be ready..."\n\
sleep 3\n\
echo "Virtual display ready on $DISPLAY"\n\
exec "$@"' > /usr/local/bin/start-xvfb.sh \
    && chmod +x /usr/local/bin/start-xvfb.sh

ENTRYPOINT ["/usr/local/bin/start-xvfb.sh"]
CMD ["/bin/bash"] 
