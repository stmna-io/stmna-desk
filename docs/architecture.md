# Architecture Overview

How all the pieces of the STMNA stack connect, why they're structured this way, and where data flows between them. This is the map. The territory (configuration details, port assignments, model inventory) lives in the other docs in this directory.

---

## System Diagram

```
                    ┌──────────────────────────────────────────────────┐
                    |                  STMNA Desk                       |
                    |                                                    |
  Signal app ------+  n8n (5678)                                       |
  (messages,        |    |-- Signal_Ingestion -- Signal_Worker          |
   URLs, audio)     |    |-- Signal_Cleanup                             |
                    |    |-- Vault Ops (read/write/search)              |
                    |    |-- Vault Embedding Pipeline                   |
                    |    +-- STMNA_Voice                                |
                    |                                                    |
                    |  llama-swap (8081) -- llama.cpp (Vulkan)          |
                    |    |-- Qwen3.5-35B (daily driver)                |
                    |    |-- Qwen3.5-122B (translation)                |
                    |    +-- Qwen3-4B (voice, always-on)               |
                    |                                                    |
                    |  whisper.cpp (8083/8084) -- STT                   |
                    |  TEI (9003) -- embeddings                         |
                    |  Kokoro TTS (9005) -- audio generation            |
                    |  PostgreSQL + PGVector (5432)                     |
                    |  Open WebUI (3000) -- chat + RAG                  |
                    |  SearXNG (8888) -- web search                     |
                    |  Crawl4AI (11235) -- web scraping                 |
                    |  Agent Zero (50001) -- AI agent                   |
                    |                                                    |
                    +------------------+-------------------------------+
                                       | Tailscale VPN
                                       v
                              +-------------------+
                              |    VPS (Caddy)    |
                              |    HTTPS + TLS    |
                              +---------+---------+
                                        |
                    +-------------------+-------------------+
                    v                   v                   v
               Signal API        Forgejo (git)       NextCloud
               (incoming         (vault sync,        (file storage,
                messages)         webhooks)           audio delivery)
```

---

## Layer Architecture

### Infrastructure Layer (Desk + VPS)

The Desk runs all compute: inference, transcription, embedding, workflow execution, database. It sits on a home LAN with no ports exposed to the internet.

The VPS runs Caddy as a reverse proxy, terminating HTTPS and forwarding requests to the Desk through a Tailscale tunnel. Forgejo (git hosting) and NextCloud (file storage) also run on the VPS. The VPS does no AI compute; it's a gateway.

This split exists because public endpoints need a stable IP and TLS certificates, which a home connection can't reliably provide. The VPN tunnel means the Desk never needs an open port.

### Orchestration Layer (n8n)

n8n handles all workflow automation. Seven active workflows coordinate the pipelines:

| Workflow | What It Does |
|----------|-------------|
| Signal_Ingestion | Receives Signal messages, parses commands, deduplicates, queues jobs |
| Signal_Worker | Processes queued jobs: download, transcribe, summarize, translate, TTS, vault write |
| Signal_Cleanup | Daily cache purge and deferred message delivery |
| Signal_NextCloud | Monitors NextCloud folders for file drops |
| Vault Ops | 12-action API for vault file operations and semantic search |
| Vault Embedding Pipeline | Auto-embeds vault changes on git push (Forgejo webhook) |
| STMNA_Voice | Webhook-triggered voice transcription pipeline |

n8n runs in a custom container with ffmpeg and yt-dlp baked in. Code nodes have access to `fs`, `child_process`, and `path` for operations that need shell-level control (audio conversion, LLM API calls via spawn).

### Interface Layer

Three interfaces serve different interaction patterns:

- **Signal app:** Mobile-first, async. Send a URL, get a vault note back minutes later. The primary input method for content processing.
- **Open WebUI:** Desktop chat interface. Interactive conversations with Qwen models, SearXNG web search, and vault RAG search. Best for research and exploration.
- **Agent Zero:** Autonomous AI agent with tool use. Can search the vault, browse the web, and execute multi-step tasks. LAN-only access.

### Knowledge Layer (Vault + PGVector)

Content flows through a loop: ingest, process, embed, store, retrieve.

1. **Ingest:** Content arrives via Signal, NextCloud, or direct webhook
2. **Process:** n8n workflows extract, transcribe, summarize, and translate
3. **Store:** Processed content is written as markdown notes in the Obsidian vault
4. **Embed:** On git push, the Embedding Pipeline chunks new content and stores vectors in PGVector
5. **Retrieve:** Semantic search via the Vault Ops webhook returns ranked chunks with source attribution

The vault itself is an Obsidian-compatible collection of markdown files in a Forgejo git repository. Plain text, version-controlled, human-readable. PGVector provides the semantic search layer on top, but the vault is the source of truth, not the vector database.

---

## Key Architectural Decisions

### Local inference over API

Running models locally costs EUR 2,650 in hardware plus ~EUR 300/year in power. Over five years, that's EUR 4,150 total. Equivalent API usage at moderate volume would cost EUR 12,000-21,000 over the same period. After hardware amortization, every token is free.

Beyond economics: no rate limits, no data leaving the network, no dependency on external service availability. The Signal pipeline processes content at any hour without worrying about API quotas. The Voice pipeline runs hundreds of requests daily with zero marginal cost.

The trade-off: you maintain the hardware. Updates, driver issues, model format changes, container restarts. If uptime matters more than sovereignty, managed APIs are simpler.

### n8n as the orchestration backbone

n8n was chosen over custom code for workflow orchestration. The reasoning:

- **Visual debugging:** When a pipeline fails at step 14 of 20, you can see exactly where in the n8n UI
- **Fast iteration:** Changing a prompt, adding a processing step, or rerouting content takes minutes, not a code deploy
- **Existing integrations:** PostgreSQL, HTTP, webhooks, file operations all have first-class nodes
- **Low maintenance:** One container to update, not a custom application to maintain

The trade-off: n8n Code nodes are sandboxed (no `require()` for most modules). Complex logic sometimes needs workarounds like `child_process.spawn` instead of native Node.js modules. The 12-hour task timeout had to be explicitly configured for long book translations.

### Vault-first knowledge management

The knowledge layer is built on an Obsidian vault (markdown files in git), not a database.

- **Portability:** Move to any editor or system by copying a folder
- **Version history:** Every change is a git commit with full diff history
- **Human-readable:** Open any file in any text editor, no special tooling required
- **Composable:** Other tools (n8n, Claude.ai, agents) interact with plain text via webhooks

PGVector provides semantic search, but the vector database is a derived index, not the primary store. If PGVector goes down, the vault is unaffected. If the vault is rebuilt from git, PGVector re-indexes automatically via the Embedding Pipeline.

### Rootless Podman over Docker

Podman runs all containers without a root daemon. If a container is compromised, the attacker lands in an unprivileged user namespace with no escalation path to root.

Docker's daemon model requires a root process. Podman's daemonless, fork-exec model means each container is a child process of the user who started it. This is a meaningful security improvement for a machine that runs untrusted workloads (web scraping, processing arbitrary URLs from Signal messages).

The trade-off: some Docker-native tooling doesn't work. Compose file syntax needs `x-podman: in_pod: false`. Container networking behaves slightly differently. Dockge only tracks containers it starts itself. None of these are blockers, but they add friction during initial setup.

---

## Data Flows

### Signal content ingestion

User sends a YouTube URL via Signal. Signal_Ingestion parses the message, checks the content cache in PostgreSQL, and queues a job. Signal_Worker picks up the job, downloads the audio with yt-dlp, transcribes it with whisper.cpp, summarizes it with Qwen3.5-35B, optionally translates (TEaR 3-pass with Qwen3.5-122B) and generates TTS audio (Kokoro). The result is written as an Obsidian vault note via the Vault Ops webhook, the audio is uploaded to NextCloud, and a confirmation is sent back through Signal. For a 42-minute YouTube video, the full pipeline completes in about 2 minutes.

### Vault search

A query arrives via Claude.ai, Open WebUI, or Agent Zero. The query text is embedded using TEI (pplx-embed-context-v1, 1024 dimensions). PGVector runs a cosine similarity search against the vault_embeddings table. Ranked chunks are returned with file paths, heading context, and relevance scores. The search endpoint is a single n8n webhook (`POST /webhook/vault` with `action: search`), so all consumers use the same search logic.

### Voice transcription

Audio arrives via HTTP POST. FFmpeg converts it to 16kHz mono WAV. Whisper.cpp transcribes with bilingual prompting and anti-hallucination parameters. A 5-method hallucination filter catches phantom phrases and garbage output. Qwen3-4B cleans the transcript (grammar, punctuation) without changing meaning. The whole round-trip averages 2.4 seconds across 423 tested recordings.

---

## What's Not Here

This is a single-owner system. There's no multi-user authentication, no tenant isolation, no high-availability clustering. Services restart on failure via systemd, but there's no automatic failover or load balancing.

Discrete GPU workloads (training, fine-tuning, CUDA-dependent libraries) don't run here. The Vulkan inference path handles generation well, but anything requiring ROCm or CUDA needs different hardware.

The stack doesn't include monitoring or alerting beyond basic systemd status checks. If a service fails silently, you find out when something downstream breaks. Adding Prometheus/Grafana would be a worthwhile improvement for anyone running this in a more production-critical context.

---

## Related Docs

- [Hardware Guide](hardware-guide.md): Framework Desktop specs, why 128GB, power and thermals
- [Inference Stack](inference-stack.md): Service map, memory budget, model inventory, benchmarks, llama-swap config
- [Remote Access](remote-access.md): Tailscale VPN, Caddy reverse proxy, SSH patterns
- [Full Stack Deployment](full-stack-deployment.md): Adding Forgejo and NextCloud to the setup

---

*Last updated: 2026-03-04*
