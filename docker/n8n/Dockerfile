# STMNA Custom n8n Image
#
# Extends the official n8n image with system tools required by the
# Signal Worker pipeline: ffmpeg (audio), yt-dlp (media download),
# pandoc (document conversion).
#
# Kokoro TTS runs as a separate container — n8n calls it via HTTP.
# No Python TTS dependencies needed here.

# --- Stage 1: static ffmpeg binary ---
FROM alpine:3.22 AS ffmpeg-download
RUN wget -O /tmp/ffmpeg.tar.xz \
      https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar -xf /tmp/ffmpeg.tar.xz -C /tmp && \
    cp /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ffmpeg && \
    chmod +x /usr/local/bin/ffmpeg

# --- Stage 2: yt-dlp via pip ---
FROM python:3.12-alpine AS ytdlp-setup
RUN pip install --no-cache-dir yt-dlp

# --- Stage 3: pandoc from Alpine packages ---
FROM alpine:3.22 AS pandoc-setup
RUN apk add --no-cache pandoc-cli

# --- Final image ---
FROM docker.io/n8nio/n8n:2.9.0

USER root

# ffmpeg: static binary, no dependencies
COPY --from=ffmpeg-download /usr/local/bin/ffmpeg /usr/bin/ffmpeg

# yt-dlp: Python + pip-installed packages
COPY --from=ytdlp-setup /usr/local /usr/local
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3

# pandoc: binary + required shared libraries (libgmp, libffi)
COPY --from=pandoc-setup /usr/bin/pandoc /usr/bin/pandoc
COPY --from=pandoc-setup /usr/lib/libgmp.so* /usr/lib/
COPY --from=pandoc-setup /usr/lib/libffi.so* /usr/lib/

USER node
