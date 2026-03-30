# Custom n8n Image

The base n8n image does not include the system tools that the STMNA Signal Pipeline needs.
This Dockerfile extends it with the required dependencies using a multi-stage build to keep the final image small.

## What's Added

| Tool | Source | Used by |
|------|--------|---------|
| ffmpeg | Static binary ([johnvansickle.com](https://johnvansickle.com/ffmpeg/)) | Audio extraction from video files (Extract Audio node), yt-dlp audio encoding |
| yt-dlp | pip install | YouTube and media downloads (yt-dlp Download node) |
| pandoc | Static binary ([github.com/jgm/pandoc](https://github.com/jgm/pandoc/releases)) | EPUB-to-markdown conversion for book processing (Extract EPUB nodes, Reconstruct EPUB node) |
| python3 | Included with yt-dlp stage | EPUB metadata extraction (OPF parser) and EPUB repackaging (ZIP compliance fix) in Code nodes |

Kokoro TTS runs as a separate container (`kokoro-tts`). The n8n image calls it via HTTP -- no Python TTS dependencies needed here.

## Build

```bash
cd docker/n8n
podman build -t stmna-n8n:latest .
```

Build takes 2-5 minutes depending on network speed (downloads ~80MB static ffmpeg binary).

## Verify

After building, confirm all tools are available:

```bash
podman run --rm stmna-n8n:latest ffmpeg -version
podman run --rm stmna-n8n:latest yt-dlp --version
podman run --rm stmna-n8n:latest pandoc --version
podman run --rm stmna-n8n:latest python3 --version
```

All four commands should print version info without errors.

## Use

Reference `stmna-n8n:latest` in your n8n compose file instead of `n8nio/n8n:latest`:

```yaml
services:
  n8n:
    image: stmna-n8n:latest
    # ... rest of your n8n config
```

See the [install guide](../../docs/install-guide.md) for full compose configuration.

## Pre-built Image

A pre-built image is published to GitHub Container Registry on every push to `main`:

```bash
podman pull ghcr.io/stmna-io/stmna-n8n:latest
```

Or reference it directly in your compose file:
```yaml
image: ghcr.io/stmna-io/stmna-n8n:latest
```

See [stacks/n8n/compose.yaml](../../stacks/n8n/compose.yaml) for the full deployment config.

## Pinned Versions

The base image is pinned to `n8nio/n8n:2.9.0` for reproducibility. To update:

1. Change the tag in the Dockerfile
2. Rebuild: `podman build -t stmna-n8n:latest .`
3. Verify all four tools still work (see Verify section above)
4. Restart your n8n stack
