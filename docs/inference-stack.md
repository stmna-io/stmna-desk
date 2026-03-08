# Inference Stack

Everything about what's running, on what port, and how it's configured. Read this when deploying a similar stack, debugging service conflicts, adding a new model, or trying to understand why a request is slow.

---

## Service Map

| Service | Container | Port | Always On | Purpose |
|---------|-----------|------|-----------|---------|
| llama-swap | llama-swap | 8081 | Yes | LLM reverse proxy, OpenAI-compatible API, model hot-swap |
| whisper.cpp (Voice) | whisper-voice | 8083 | Yes | Speech-to-text for Voice pipeline, Vulkan, large-v3-turbo Q5 |
| whisper.cpp (Signal) | whisper-signal | 8084 | Yes | Speech-to-text for Signal pipeline, Vulkan, large-v3-turbo Q5 |
| Open WebUI | open-webui | 3000 | Yes | Chat interface with SearXNG tool calling |
| n8n | n8n | 5678 | Yes | Workflow automation (Signal, Voice, Vault pipelines) |
| PostgreSQL | postgres-voice | 5432 | Yes | Pipeline queue, cache, training pairs, metrics |
| Kokoro TTS | kokoro-tts | 9005 | Yes | Text-to-speech, OpenAI-compatible API, CPU-only |
| Agent Zero | agent-zero | 50001 | Yes | AI agent with tool use (LAN only) |
| SearXNG | searxng | 8888 | Yes | Self-hosted meta-search engine |
| Crawl4AI | crawl4ai | 11235 | Yes | Web page scraping |
| Dockge | dockge | 5001 | Yes | Container management UI |

Two separate whisper instances prevent the Voice and Signal pipelines from blocking each other. If you only run one pipeline, a single instance works fine.

---

## Model Inventory

### Daily Group (exclusive swap, one loaded at a time)

| Model | Quantization | Size | Context | Speed (t/s) | Primary Use |
|-------|-------------|------|---------|-------------|-------------|
| Qwen3.5-35B-A3B | UD-Q6_K_XL | 30.3GB | 65536 | 28.3 | Daily driver: summarization, tool calling, agentic tasks |
| Qwen3.5-122B-A10B | UD-Q4_K_XL | 68.4GB | 65536 | 24 | Translation (TEaR 3-pass), high-quality reasoning |
| Qwen3.5-9B | UD-Q6_K_XL | 8.76GB | 65536 | 22.1 | Lightweight tasks (slower than 35B, see note below) |
| GLM-4.7-Flash | Q6_K | ~6GB | 65536 | 56.0 | Fast agentic tasks, standard transformer |
| Qwen3-30B-A3B | UD-Q6_K_XL | ~29GB | 65536 | 63.8 | Batch pipelines, fast summarization |
| Mistral Large 2411 | Q4_K_M | ~65GB | 32768 | - | Multilingual generation |

Each model has a "nothink" variant (same file, different config) that disables chain-of-thought reasoning for faster, more deterministic output.

**Why is 9B slower than 35B?** The 9B model is dense (all 9 billion parameters active per token). The 35B is a Mixture-of-Experts model with only 3 billion parameters active per token. On unified memory architecture, bandwidth is the bottleneck, and the MoE model moves less data per token despite having more total parameters.

### Always-On Group (persistent, never swapped)

| Model | Quantization | Port | Context | Purpose |
|-------|-------------|------|---------|---------|
| Qwen3-4B-Instruct | Q4_K_M | 9002 | 4096 | Voice transcript cleanup (sub-second latency) |

### Non-LLM Models

| Service | Model | Port | Purpose |
|---------|-------|------|---------|
| whisper.cpp | large-v3-turbo Q5 | 8083/8084 | Speech-to-text (Vulkan) |
| Kokoro TTS | 82M param | 9005 | Text-to-speech (af_heart EN, ff_siwis FR) |

---

## Benchmarks

All measurements: Radeon 8060S (gfx1151), Vulkan, llama.cpp build b8182, 2026-03-02.

| Model | Architecture | Active Params | Speed (t/s) |
|-------|-------------|---------------|-------------|
| Qwen3.5-9B | Dense, gated delta net | 9B | 22.1 |
| Qwen3.5-35B-A3B | MoE, gated delta net | 3B | 28.3 |
| Qwen3.5-122B-A10B | MoE, gated delta net | 10B | 24 |
| Qwen3-30B-A3B | MoE, standard transformer | 3B | 63.8 |
| GLM-4.7-Flash | Dense, standard transformer | ~6B | 56.0 |

Qwen3.5 models run ~55% slower than equivalently-sized standard transformers. The gated delta net (linear attention) mechanism lacks an optimized Vulkan shader in llama.cpp. The computation falls back to CPU for those operations. This is a known issue tracked in:

- [PR #19504](https://github.com/ggml-org/llama.cpp/pull/19504): Fused GATED_DELTA_NET with Vulkan shader (active development)
- [PR #18792](https://github.com/ggml-org/llama.cpp/pull/18792): Alternative approach (stalled)

The quality and tool-calling capabilities of Qwen3.5 justify the speed trade-off for interactive use. For batch processing where speed matters more than capability, Qwen3-30B at 63.8 t/s remains the better choice.

---

## Deployment: Rootless Podman

All containers run under the `stmna` user (UID 1001) with rootless Podman. No Docker daemon, no root containers, no sudo required for day-to-day operations.

Why rootless:

- **Security:** Container escape gives you an unprivileged user, not root
- **No daemon:** No long-running root process managing containers
- **OCI compliant:** Same container images as Docker, just a different runtime
- **User isolation:** Each user gets their own container namespace

The compose directory structure:

```
~/stacks/
  llama-swap/
    compose.yaml
    config.yaml
  n8n/
    compose.yaml
    Dockerfile
  postgres/
    compose.yaml
  whisper-server/
    compose.yaml
  ...
```

Each service lives in its own directory with its own `compose.yaml`. All services join the shared `stmna-net` Podman network for cross-compose communication. Containers reference each other by hostname (e.g., `http://llama-swap:8080`, `http://postgres-voice:5432`).

Rootless Podman quirk: compose files need `x-podman: in_pod: false` to prevent automatic pod creation, which breaks cross-compose networking.

---

## Adding a New Service

1. Create a new directory: `~/stacks/your-service/`
2. Write a `compose.yaml` joining `stmna-net`:
   ```yaml
   services:
     your-service:
       image: your-image:tag
       ports:
         - "YOUR_PORT:CONTAINER_PORT"
       networks:
         - stmna-net

   networks:
     stmna-net:
       external: true

   x-podman:
     in_pod: false
   ```
3. Pick a port that doesn't conflict with the service map above
4. Start it: `cd ~/stacks/your-service && podman compose up -d`
5. Add the container name to `~/start-all-stacks.sh` for boot persistence
6. If it needs to survive reboots, cycle it through Dockge once (Dockge only tracks containers it starts itself)

---

*Last updated: 2026-03-04*
