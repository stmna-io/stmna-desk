# STMNA Custom n8n Image
#
# Extends the official n8n image with system tools required by the
# Signal Worker pipeline:
#   - ffmpeg: audio extraction from video files, yt-dlp audio encoding
#   - yt-dlp: YouTube and media downloads
#   - pandoc: EPUB-to-markdown conversion for book processing
#   - python3: EPUB metadata extraction and EPUB repackaging in Code nodes
#
# Kokoro TTS runs as a separate container (HTTP API at kokoro-tts:8880).
# No TTS dependencies needed in this image.
#
# Multi-stage build keeps the final image small by copying only the
# binaries and libraries needed at runtime.

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

# --- Stage 3: pandoc static binary ---
# pandoc-cli from Alpine fails in rootless Podman (I/O error on 280MB
# Haskell binary). Download the official static Linux build instead.
FROM alpine:3.22 AS pandoc-download
RUN wget -O /tmp/pandoc.tar.gz \
      https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-linux-amd64.tar.gz && \
    tar -xzf /tmp/pandoc.tar.gz -C /tmp && \
    cp /tmp/pandoc-3.6.4/bin/pandoc /usr/local/bin/pandoc && \
    chmod +x /usr/local/bin/pandoc

# --- Final image ---
# USER INPUT REQUIRED -- pin to match your n8n version
FROM docker.io/n8nio/n8n:2.9.0

USER root

# ffmpeg: static binary, no runtime dependencies
COPY --from=ffmpeg-download /usr/local/bin/ffmpeg /usr/bin/ffmpeg

# yt-dlp: full Python environment (also used by Code nodes for EPUB processing)
COPY --from=ytdlp-setup /usr/local /usr/local
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3

# pandoc: static binary, no shared library dependencies
COPY --from=pandoc-download /usr/local/bin/pandoc /usr/bin/pandoc

USER node
