# STMNA Desk -- Compose Stacks

Reference compose files for every service in the STMNA Desk stack. Each directory contains a `compose.yaml` ready to paste into Dockge or run with `podman compose`.

## Services

| Stack | Service | Port | Tier | Install Guide Step |
|-------|---------|------|------|--------------------|
| dockge | Container management UI | 5001 | Core | 3 |
| postgres | PostgreSQL 17 + PGVector | 5432 | Core | 4 |
| llama-swap | LLM reverse proxy (Vulkan) | 8081 | Core | 5 |
| open-webui | Chat UI | 3000 | Core | 6 |
| n8n | Workflow automation (custom image) | 5678 | Automation | 7 |
| whisper | Whisper STT (voice + signal) | 8083, 8084 | Automation | 8 |
| text-embeddings | TEI embedding server | 9003 | Extended | 9 |
| kokoro-tts | Text-to-speech | 9005 | Extended | 10 |
| forgejo | Self-hosted git forge | 3300 | Extended | 11 |
| nextcloud | Sovereign cloud storage | 8090 | Extended | Signal guide |
| agent-zero | AI agent | 50001 | Extended | 12 |

## Before you deploy

1. Follow the [install guide](../docs/install-guide.md) for step-by-step instructions
2. Replace all `USER INPUT REQUIRED` values in the compose files
3. Create the `stmna-net` network: `podman network create stmna-net`
4. Deploy in the order listed above (dependencies flow top to bottom)

## Compose file conventions

- `USER INPUT REQUIRED` -- you must change this value
- `OPTIONAL` -- safe defaults provided, change if needed
- `NO ACTION NEEDED` -- leave as-is
- `NOTE` -- read the comment for context

All files include `x-podman: in_pod: false` for rootless Podman compatibility.
