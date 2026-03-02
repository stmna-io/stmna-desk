<div align="center">

  <h1>STMNA Desk</h1>
  <h3>Sovereign AI Workstation Stack</h3>
  <p><em>Local inference, automated pipelines, voice transcription. All on hardware you own.</em></p>

  [![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
  [![AMD Strix Halo](https://img.shields.io/badge/AMD-Ryzen%20AI%20Max%2B%20395-ED1C24)](https://www.amd.com)
  [![Ubuntu 24.04](https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420)](https://ubuntu.com)
  [![Rootless Podman](https://img.shields.io/badge/Containers-Rootless%20Podman-892CA0)](https://podman.io)
  ![Status](https://img.shields.io/badge/Status-Live-brightgreen)

  <br/>

  [Architecture](#architecture) · [Performance](#performance) · [Guides](#guides) · [Ecosystem](#ecosystem)

</div>

---

<!-- TODO: Hero GIF — OWU inference with Qwen 3.5 + SearXNG tool calling (SB recording session) -->

---

Getting inference running on AMD Strix Halo is well documented at this point. Getting inference running is step one. What comes after, connecting the LLM to a web scraper, a knowledge base, a voice pipeline, a workflow engine, and making the whole thing actually useful, is where documentation gets thin. This repo is what we built to fill that gap.

STMNA Desk is a full self-hosted AI stack running on a Framework Desktop 128GB (AMD Ryzen AI Max+ 395). Ten services, rootless containers, Ubuntu 24.04 LTS. The inference layer (llama-swap + llama.cpp, Vulkan) serves as a shared backend for everything on the machine: Open WebUI for interactive chat with web search, n8n for workflow automation, whisper.cpp for speech-to-text, Qdrant for vector search. Everything talks to everything. Nothing leaves the network.

The stack runs in production. Qwen3.5 35B at 29 t/s, Qwen3-30B at 66 t/s. The Signal pipeline has processed hundreds of content items end-to-end in under 5 minutes. Voice transcription works on Linux and Android from the same backend. Strix Halo has quirks (the gated delta net attention mechanism runs slower than expected in llama.cpp's Vulkan backend, the upstream PR tracking a fix is linked in the inference docs). Every decision in this repo has a reason, and the reasons are in `/docs/` alongside the alternatives that were considered and rejected.

Clone, configure `.env`, and follow the architecture guide. The `examples/` directory has individual service compose files to start from. The docs go deep on hardware setup, inference tuning, container topology, remote access via Headscale, and an optional full-stack build with Nextcloud and Forgejo.

---

## Architecture

<!-- TODO: Proper architecture diagram with brand colors (SB-10 design assets session) -->

```
┌─────────────────────────────────────────────────────────────────┐
│                        STMNA Desk                               │
│                                                                 │
│  ┌──────────────┐   ┌───────────────────────────────────────┐  │
│  │  llama-swap  │──▶│  llama.cpp (Vulkan)                   │  │
│  │  :8081       │   │  loads models on demand               │  │
│  └──────────────┘   └───────────────────────────────────────┘  │
│         │                                                       │
│  ┌──────┴──────┬────────────┬────────────┐                     │
│  ▼             ▼            ▼            ▼                     │
│ Open WebUI    n8n       whisper.cpp   Crawl4AI                 │
│ (Chat+Search) (Pipelines)  (Voice STT) (Web scrape)           │
│                                                                 │
│  ┌──────────────┐   ┌────────────┐   ┌────────────────────┐   │
│  │  SearXNG     │   │  Qdrant    │   │  PostgreSQL        │   │
│  │  :8888       │   │  :6333     │   │  :5432             │   │
│  └──────────────┘   └────────────┘   └────────────────────┘   │
│                                                                 │
│  All containers: rootless Podman, stmna-net bridge             │
└─────────────────────────────────────────────────────────────────┘
         │  Tailscale / Headscale VPN
         ▼
    Caddy (VPS) — HTTPS termination, bearer token auth
         │
    Remote clients (laptop, mobile, team)
```

| Service | Port | Purpose |
|---------|------|---------|
| llama-swap | 8081 | Model hot-swap proxy, OpenAI-compatible API |
| whisper.cpp | 8083/8084 | Speech-to-text, Vulkan, separate Voice and Signal instances |
| Open WebUI | 3000 | Chat interface with SearXNG tool calling |
| n8n | 5678 | Workflow automation |
| PostgreSQL | 5432 | Pipeline queue, training pairs, metrics |
| Qdrant | 6333 | Vector database |
| SearXNG | 8888 | Self-hosted meta-search |
| Crawl4AI | 11235 | Web scraping |
| Dockge | 5001 | Container management UI |

All containers run rootless under a non-privileged user. No root Podman daemon. Day-to-day operations require no `sudo`.

---

## Hardware

Framework Desktop DIY Edition, AMD Ryzen AI Max+ 395 (Strix Halo), 128GB unified memory, 2TB NVMe, Ubuntu 24.04 LTS.

The 128GB unified pool is what makes this class of hardware interesting for AI workloads: 70B models load in full, multiple models stay warm simultaneously, Qdrant has room to grow without fighting inference for memory, and the Vulkan GPU runs llama.cpp and whisper.cpp natively without any CUDA dependency. Ubuntu 24.04 LTS was a deliberate choice: most Strix Halo documentation targets Fedora, and the gap for Ubuntu on production LTS is real.

Full hardware notes and Ubuntu install specifics: [docs/hardware-guide.md](docs/hardware-guide.md)

---

## Performance

Benchmarked on Radeon 8060S (gfx1151), Vulkan, llama.cpp build b8182.

Qwen3-30B runs at 66 t/s on this hardware and is the right model for batch pipeline work. Qwen3.5-35B runs at 29 t/s. The gap is architectural: Qwen3.5's gated delta net linear attention mechanism does not yet have a optimized Vulkan kernel in llama.cpp, so those operations fall back to CPU. The fix is in progress upstream. The quality and tool-calling capabilities of Qwen3.5 justify the speed trade-off for interactive and agentic use. Both situations are documented in [docs/inference-stack.md](docs/inference-stack.md), including which upstream PR to watch.

| Model | Quant | Speed | Best for |
|-------|-------|-------|----------|
| Qwen3.5-35B-A3B | UD-Q6_K_XL | 29 t/s | Daily driver, tool calling, agentic tasks |
| Qwen3.5-122B-A10B | UD-Q4_K_XL | 24 t/s | High-quality reasoning |
| Qwen3-30B-A3B | Q4_K_M | 66 t/s | Batch pipelines, summarization |
| GLM-4.7-Flash | Q6_K | 58 t/s | Fast agentic tasks |
| whisper large-v3-turbo | Q5 | 3-4GB VRAM | Speech-to-text |

---

## Guides

| Guide | What's in it |
|-------|-------------|
| [Hardware Guide](docs/hardware-guide.md) | Framework Desktop setup, Ubuntu 24.04 install, driver notes for Strix Halo |
| [Inference Stack](docs/inference-stack.md) | llama-swap config reference, model groups, think/nothink modes, benchmark data |
| [Architecture](docs/architecture.md) | Container topology, rootless Podman, stmna-net networking, startup sequence |
| [Remote Access](docs/remote-access.md) | Headscale VPN, Caddy bearer token configuration |
| [Full Stack Deployment](docs/full-stack-deployment.md) | Optional: add Nextcloud and Forgejo to the same machine |

The `examples/` directory has individual service compose files.

---

## Ecosystem

Two production pipelines run on STMNA Desk and are available as separate repos:

**[STMNA Signal](https://github.com/stmna-io/stmna-signal)** — send a YouTube URL or web link via Signal messenger and get a structured intelligence note in your Obsidian vault. Whisper transcription, Qwen summarization, PostgreSQL deduplication cache. End-to-end in under 5 minutes for a 2-hour video.

**[STMNA Voice](https://github.com/stmna-io/stmna-voice)** — push-to-talk speech-to-text on Linux and Android from a shared Desk backend. Whisper large-v3-turbo, Qwen3 accent correction, training pair collection for fine-tuning.

---

## Acknowledgments

STMNA Desk runs because of the work these projects put in:

- [llama.cpp](https://github.com/ggerganov/llama.cpp) by Georgi Gerganov — the inference engine underneath everything
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov — local STT that actually works on AMD
- [llama-swap](https://github.com/mostlygeek/llama-swap) by mostlygeek — model hot-swapping without the complexity
- [n8n](https://n8n.io) — workflow automation that makes complex pipelines visual and modifiable
- [Podman](https://podman.io) — rootless containers that made the security model here possible
- [Open WebUI](https://github.com/open-webui/open-webui) — the chat interface
- [SearXNG](https://github.com/searxng/searxng) — self-hosted meta-search
- [Crawl4AI](https://github.com/unclecode/crawl4ai) — web scraping
- [Qdrant](https://qdrant.tech) — vector storage
- [Framework](https://frame.work) — hardware worth documenting because it's worth keeping
- The Strix Halo community, especially [kyuz0](https://github.com/kyuz0) for early inference container work on this architecture

---

## Contributing

Benchmark data on non-Framework AMD Strix Halo hardware is the most useful contribution right now. If you run this on a different board or APU, open an issue with your speeds and configuration.

Other welcome contributions: documentation corrections, additional service compose files in `examples/`, and bug reports with hardware and OS details.

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

<div align="center">
  <sub>Built by <a href="https://stmna.io">STMNA_</a> · Engineered resilience. Sovereign by design.</sub>
</div>
