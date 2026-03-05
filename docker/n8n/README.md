# Custom n8n Image

The base n8n Docker image doesn't include the system tools the STMNA Signal Pipeline needs.
This Dockerfile extends it with the required dependencies using a multi-stage build to keep the final image small.

## What's Added

| Tool | Source | Used by |
|------|--------|---------|
| ffmpeg | Static binary ([johnvansickle.com](https://johnvansickle.com/ffmpeg/)) | TTS audio processing, MP3 encoding, chunk concatenation |
| yt-dlp | pip install | YouTube and media download in Signal Worker |
| pandoc | Alpine `pandoc-cli` package | Document conversion for EPUB/book processing |

Kokoro TTS runs as a separate container (`kokoro-tts`). The n8n image calls it via HTTP -- no Python TTS dependencies needed here.

## Build

```bash
cd docker/n8n
podman build -t stmna-n8n:latest .
```

## Use

Reference `stmna-n8n:latest` in your compose file instead of `n8nio/n8n:latest`.
See the [full stack deployment guide](../../docs/full-stack-deployment.md) for example compose configurations.

## Verify

```bash
podman run --rm stmna-n8n:latest ffmpeg -version
podman run --rm stmna-n8n:latest yt-dlp --version
podman run --rm stmna-n8n:latest pandoc --version
```

## Pinned Versions

The base image is pinned to `n8nio/n8n:2.9.0` for reproducibility. To update, change the tag in the Dockerfile and rebuild. Test that all three tools still work after updating.
