# STMNA Desk -- Compose Stacks

Reference compose files for every service in the STMNA Desk stack. Each directory contains a `compose.yaml` ready to paste into Dockge or run with `podman compose`.

## Services

| Stack | Service | Port | Tier |
|-------|---------|------|------|
| dockge | Container management UI | 5001 | Core |
| postgres | PostgreSQL 17 | 5432 | Core |
| llama-swap | LLM reverse proxy (Vulkan) | 8081 | Core |
| open-webui | Chat UI | 3000 | Core |
| n8n | Workflow automation (custom image) | 5678 | Automation |
| whisper | Whisper STT (voice + signal) | 8083, 8084 | Automation |
| kokoro-tts | Text-to-speech | 9005 | Extended |
| forgejo | Self-hosted git forge | 3300 | Extended |
| nextcloud | Sovereign cloud storage | 8090 | Extended |
| agent-zero | AI agent | 50001 | Extended |
| crawl4ai | Web scraping API | 11235 | Extended |
| searxng | Search engine | 8888 | Extended |
| excalidraw | Diagram editor | 8585 | Extended |

## Before you deploy

1. Follow the [install guide](../docs/install-guide.md) for base system setup (user account, Podman, networking)
2. Replace all `REQUIRED:` values in the compose files
3. Create the `stmna-net` network: `podman network create stmna-net`
4. Deploy in the order listed above (dependencies flow top to bottom)

## Compose file conventions

- `REQUIRED:` -- you must replace this value before deploying
- `OPTIONAL:` -- safe defaults provided, adjust to taste
- `NO ACTION NEEDED` -- internal values, leave as-is
- `NOTE:` -- read the comment for context

All files include `x-podman: in_pod: false` for rootless Podman compatibility.
