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

  [🔧 What Runs on It](#what-runs-on-it) · [📖 Architecture](#architecture) · [⚡ Performance](#performance) · [🚀 Quick Start](#quick-start) · [📚 Guides](#guides) · [🔗 Ecosystem](#ecosystem)

</div>

---



---

## What is STMNA Desk?

STMNA Desk is a full self-hosted AI stack running on a Framework Desktop with 128GB unified memory (AMD Ryzen AI Max+ 395). It runs local LLM inference, autonomous AI agents, speech-to-text and content ingestion pipelines, cloud storage, and a chat interface with RAG over your own documents. Everything runs simultaneously, everything talks to everything, and nothing leaves the network thanks to private and secure rootless containers on Ubuntu 24.04 LTS.

Personal AI workstations have become a reality with open-weight models that compete with frontier cloud APIs on real benchmarks, a mature open-source application ecosystem, and hardware-agnostic inference through Vulkan. Qwen3.5-35B runs at 29 tokens per second on this hardware (even before upcoming optimisations). The 122B variant beats GPT-5 mini on tool use by a 30% margin. These are production models running daily on a machine that sits dead silent on a desk, draws under 200 watts, costs a fraction of a single year of cloud API bills while ensuring full data sovereignty.

The stack is live, accessible remotely, and provides a single OpenAI-compatible API serving inference to every other service. Every architectural decision has been tested and documented with rationale in [`/docs/`](docs/). What STMNA Desk unlocks is below.

---

## What Runs on It

🧠 **Local LLM Inference**  -- Run state-of-the-art open-weight models like Qwen3.5-35B and 122B locally and always-warm lightweight models for low-latency tasks like speech-to-text correction. (llama-swap, llama.cpp, Vulkan)

🗨️ **Interactive Chat with RAG**  -- Ask questions, search the web, and query your own documents through a local chat interface with retrieval-augmented generation. (Open WebUI, SearXNG)

📥 **Content Ingestion + Audio Summaries**  -- Send a YouTube video, a URL, or a full book via Signal messenger or Nextcloud and get a structured summary in your vault with a voice memo version. Handles summarization, translation (full ebooks!) and TTS. ([STMNA Signal](https://github.com/stmna-io/stmna-signal))

🎙️ **Self-Improving Speech-to-Text**  -- Push-to-talk dictation from Linux or Android with Whisper transcription, LLM-powered correction, and automatic training pair collection for fine-tuning. ([STMNA Voice](https://github.com/stmna-io/stmna-voice))

🤖 **Autonomous AI Agents**  -- Run Agent Zero against local inference with full web access for deep research, content scraping, and recurring scheduled tasks. Set up proactive monitoring jobs, automated report generation, and multi-step problem solving with no API costs. (Agent Zero)

⚡ **Workflow Automation**  -- Chain LLM calls, web scraping, and database writes into automated pipelines. This is the orchestration layer that powers STMNA Signal and STMNA Voice behind the scenes. (n8n, Crawl4AI, PostgreSQL)

🏠 **Self-Hosted Infrastructure**  -- Private git forge with full version history for your notes, configs, and code. Sovereign cloud storage that doubles as an ingestion endpoint for STMNA Signal. No third-party accounts required. (Forgejo, Nextcloud)

---

## Architecture

![STMNA Desk Architecture](docs/architecture-v1.svg)

| Service | Port | Purpose |
|---------|------|---------|
| llama-swap | 8081 | Model hot-swap proxy, OpenAI-compatible API |
| whisper.cpp | 8083/8084 | Speech-to-text, Vulkan, separate Voice and Signal instances |
| Open WebUI | 3000 | Chat interface with SearXNG tool calling |
| n8n | 5678 | Workflow automation |
| PostgreSQL | 5432 | Pipeline queue, training pairs, metrics |
| SearXNG | 8888 | Self-hosted meta-search |
| Crawl4AI | 11235 | Web scraping |
| Dockge | 5001 | Container management UI |

All containers run rootless under a non-privileged user. No root Podman daemon. Day-to-day operations require no `sudo`.

---

## Hardware

| Component | Specification |
|-----------|---------------|
| **CPU/APU** | AMD Ryzen AI Max+ 395 (Strix Halo) |
| **Unified Memory** | 128GB (96GB allocatable to GPU under Linux) |
| **Storage** | 2TB NVMe SSD |
| **Form Factor** | Framework Desktop DIY Edition |
| **OS** | Ubuntu 24.04 LTS |

The 128GB unified pool is what makes this class of hardware interesting for AI workloads: 70B models load in full, multiple models stay warm simultaneously, and the Vulkan GPU runs llama.cpp and whisper.cpp natively without any CUDA dependency. Ubuntu 24.04 LTS was a deliberate choice; most Strix Halo documentation targets Fedora, and the gap for Ubuntu on production LTS is real.

Full hardware notes and Ubuntu install specifics: [docs/hardware-guide.md](docs/hardware-guide.md)

---

## Performance

Benchmarked on Radeon 8060S (gfx1151), Vulkan, llama.cpp build b8182.

| Model | Quant | Speed | Best for |
|-------|-------|-------|----------|
| Qwen3.5-35B-A3B | UD-Q6_K_XL | 29 t/s | Daily driver, tool calling, agentic tasks |
| Qwen3.5-122B-A10B | UD-Q4_K_XL | 24 t/s | High-quality reasoning |
| Qwen3-30B-A3B | Q4_K_M | 66 t/s | Batch pipelines, summarization |
| GLM-4.7-Flash | Q6_K | 58 t/s | Fast agentic tasks |
| whisper large-v3-turbo | Q5 | 3-4GB VRAM | Speech-to-text |

Qwen3-30B at 66 t/s is the right model for batch pipeline work. Qwen3.5-35B at 29 t/s is slower because its gated delta net linear attention mechanism doesn't yet have an optimized Vulkan kernel in llama.cpp, so those operations fall back to CPU. The upstream fix is in progress. The quality and tool-calling capabilities of Qwen3.5 justify the speed trade-off for interactive and agentic use. Both situations are documented in [docs/inference-stack.md](docs/inference-stack.md), including which upstream PR to watch.

---

## Quick Start

> Full deployment walkthrough: [docs/architecture.md](docs/architecture.md)

**Prerequisites:** Framework Desktop 128GB (or equivalent AMD Strix Halo system), Ubuntu 24.04 LTS, Podman installed (rootless).

```bash
git clone https://github.com/stmna-io/stmna-desk.git
cd stmna-desk
cp .env.example .env
# Edit .env with your paths, ports, and model locations
```

The `examples/` directory has individual service compose files to start from. The docs go deep on hardware setup, inference tuning, container topology, remote access via Headscale, and an optional full-stack build with Nextcloud and Forgejo.

---

## 📚 Guides

| Guide | What's in it |
|-------|-------------|
| [Hardware Guide](docs/hardware-guide.md) | Framework Desktop setup, Ubuntu 24.04 install, driver notes for Strix Halo |
| [Inference Stack](docs/inference-stack.md) | Model inventory, benchmark data, Vulkan kernel notes |
| [Architecture](docs/architecture.md) | Container topology, rootless Podman, stmna-net networking |
| [Remote Access](docs/remote-access.md) | Options for exposing services over HTTPS |
| [Full Stack Deployment](docs/full-stack-deployment.md) | Optional: add Nextcloud and Forgejo to the same machine |

> **Note:** Vault automation, remote access configuration, and knowledge management workflows are part of the private STMNA operational layer and are not included in this repository.

---

## 🔗 Ecosystem

| Product | Description | Repo |
|---------|-------------|------|
| **STMNA Signal** | Send a YouTube URL or web link via Signal messenger, get a structured intelligence note in your Obsidian vault. Whisper transcription, Qwen summarization, PostgreSQL dedup cache. End-to-end in under 5 minutes for a 2-hour video. | [stmna-signal](https://github.com/stmna-io/stmna-signal) |
| **STMNA Voice** | Push-to-talk speech-to-text on Linux and Android from a shared Desk backend. Whisper large-v3-turbo, Qwen3 accent correction, training pair collection for fine-tuning. | [stmna-voice](https://github.com/stmna-io/stmna-voice) |

---

## Acknowledgments

STMNA Desk runs because of the work these projects put in:

- [llama.cpp](https://github.com/ggerganov/llama.cpp) by Georgi Gerganov  -- the inference engine underneath everything
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov  -- local STT that actually works on AMD
- [llama-swap](https://github.com/mostlygeek/llama-swap) by mostlygeek  -- model hot-swapping without the complexity
- [n8n](https://n8n.io)  -- workflow automation that makes complex pipelines visual and modifiable
- [Podman](https://podman.io)  -- rootless containers that made the security model here possible
- [Open WebUI](https://github.com/open-webui/open-webui)  -- the chat interface
- [SearXNG](https://github.com/searxng/searxng)  -- self-hosted meta-search
- [Crawl4AI](https://github.com/unclecode/crawl4ai)  -- web scraping
- [Framework](https://frame.work)  -- hardware worth documenting because it's worth keeping
- The Strix Halo community, especially [kyuz0](https://github.com/kyuz0) for early inference container work on this architecture

---

## Contributing

Benchmark data on non-Framework AMD Strix Halo hardware is the most useful contribution right now. If you run this on a different board or APU, open an issue with your speeds and configuration.

Other welcome contributions: documentation corrections, additional service compose files in `examples/`, and bug reports with hardware and OS details.

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

Apache 2.0  -- see [LICENSE](LICENSE)

---

<div align="center">
  <sub>Built by <a href="https://stmna.io">STMNA_</a> · Engineered resilience. Sovereign by design.</sub>
</div>
