# Full Stack Deployment

<!-- TODO: Write full Nextcloud + Forgejo guide for SB-08 session -->
<!-- Content: Nextcloud compose for rootless Podman (from official docs), Forgejo compose
     for rootless Podman (from official docs), why these are optional vs core stack,
     env var documentation, integration with core services (n8n reads Nextcloud files,
     Forgejo hosts vault backups), networking with stmna-net -->

## Overview

The STMNA Desk core stack (llama-swap, whisper, n8n, PostgreSQL, Qdrant, SearXNG, Crawl4AI, Open WebUI) is sufficient to run STMNA Signal and STMNA Voice.

This document describes **optional services** that complete the sovereign infrastructure picture:

- **Nextcloud** — sovereign cloud storage (file sync, sharing, mobile access)
- **Forgejo** — self-hosted git (source code, vault backups, workflow exports)

Both are configured for **rootless Podman** compatibility.

## Nextcloud

<!-- TODO: Rootless Podman compose for Nextcloud from official docs (SB-08) -->

Placeholder — compose file and configuration guide coming in SB-08 session.

## Forgejo

<!-- TODO: Rootless Podman compose for Forgejo from official docs (SB-08) -->

Placeholder — compose file and configuration guide coming in SB-08 session.

## Integration with Core Stack

- n8n can write processed content directly to Nextcloud via WebDAV
- Forgejo hosts sanitized n8n workflow JSON exports (this repo)
- Both services join `stmna-net` for cross-container communication
