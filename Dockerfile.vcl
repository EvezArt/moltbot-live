FROM python:3.11-slim

# Install system deps: Xvfb, FFmpeg, Chromium, fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    ffmpeg \
    chromium \
    fonts-dejavu-core \
    fonts-liberation \
    x11-utils \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy visualizer
COPY visualizer/ /app/visualizer/

# Copy streaming scripts
COPY stream_vcl.py /app/stream_vcl.py
COPY run_forever.sh /app/run_forever.sh
RUN chmod +x /app/run_forever.sh

# Environment
ENV PYTHONUNBUFFERED=1
ENV STREAM_DISPLAY=:99
ENV STREAM_WIDTH=1280
ENV STREAM_HEIGHT=720
ENV FPS=30
ENV BITRATE=2500k
ENV VCL_HTML=/app/visualizer/index.html

# Health check — all 3 processes must be running
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD pgrep -f ffmpeg > /dev/null && pgrep -f chromium > /dev/null

# Run with auto-restart wrapper
ENV MOLTBOT_CMD="python stream_vcl.py"
CMD ["bash", "run_forever.sh"]
