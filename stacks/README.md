# STMNA Desk -- Compose Stacks

Reference compose files for every service in the STMNA Desk stack. Each directory contains a `compose.yaml` ready to paste into Dockge or run with `podman compose`.

## Services

| Stack | Service | Port | Install Guide Section |
|-------|---------|------|-----------------------|
| dockge | Container management UI | 5001 | 3 |
| postgres | PostgreSQL 17 + PGVector | 5432 | 4 |
| llama-swap | LLM reverse proxy (Vulkan) | 8081 | 5 |
| whisper | Whisper STT (voice + signal) | 8083, 8084 | 6 |
| n8n | Workflow automation (custom image) | 5678 | 7 |
| open-webui | Chat UI | 3000 | 8 |
| text-embeddings | TEI embedding server | 9003 | 9 |
| kokoro-tts | Text-to-speech | 9005 | 10 |
| agent-zero | AI agent | 50001 | 11 |

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
