<div align="center">

  <h1>STMNA Desk</h1>
  <h3>Sovereign AI Workstation Stack</h3>
  <p><em>Run frontier-class AI models locally on AMD hardware. 100% sovereign, zero cloud.</em></p>

  [![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
  [![Built on AMD](https://img.shields.io/badge/Built%20on-AMD%20Strix%20Halo-ED1C24)](https://www.amd.com)
  [![Ubuntu 24.04](https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420)](https://ubuntu.com)
  [![Rootless Podman](https://img.shields.io/badge/Containers-Rootless%20Podman-892CA0)](https://podman.io)
  ![Status](https://img.shields.io/badge/Status-Live-brightgreen)

  <br/>

  [📖 Docs](#documentation) · [🚀 Quick Start](#quick-start) · [🏗️ Architecture](#architecture) · [🤝 Contributing](#contributing)

</div>

---

<!-- TODO: Hero GIF — OWU inference demo with Qwen 3.5 + SearXNG tool calling -->

---

## What is STMNA Desk?

STMNA Desk is a **complete self-hosted AI workstation stack** built on the AMD Ryzen AI Max+ 395 (Strix Halo) inside a Framework Desktop. It runs 70B+ parameter models locally with no cloud dependency, no subscriptions, and no data leaving your network.

**Think of it as the application layer that nobody else is building.**
Tools like [kyuz0's containers](https://github.com/kyuz0) show you how to run models. STMNA Desk shows you what to build with them.

### Hardware

| Component | Specification |
|-----------|---------------|
| **CPU/NPU** | AMD Ryzen AI Max+ 395 (Strix Halo) |
| **Unified Memory** | 128GB (96GB allocatable to GPU under Linux) |
| **Storage** | 2TB NVMe SSD |
| **Form Factor** | Framework Desktop DIY Edition |
| **OS** | Ubuntu 24.04 LTS |

### Why AMD? Why Framework?

- **AMD Vulkan** — llama.cpp and whisper.cpp run natively. No CUDA required.
- **128GB unified memory** — Run 70B models at full context without multi-GPU complexity.
- **Framework = repairable** — No vendor lock-in. No planned obsolescence.
- **Ubuntu-first** — Production LTS, not Fedora. Underserved gap in Strix Halo documentation.

---

## Service Stack

| Service | Port | Purpose |
|---------|------|---------|
| llama-swap | 8081 | Model hot-swap proxy (OpenAI-compatible API) |
| whisper.cpp | 8083 | Local speech-to-text (Vulkan) |
| Open WebUI | 3000 | Chat interface + SearXNG tool calling |
| n8n | 5678 | Workflow automation (STMNA Signal + Voice) |
| PostgreSQL | 5432 | Pipeline data, training pairs |
| Qdrant | 6333 | Vector database for RAG |
| SearXNG | 8888 | Privacy-focused meta-search |
| Crawl4AI | 11235 | Web scraping |
| Dockge | 5001 | Container management UI |

All containers run **rootless under a non-privileged user**. No root Podman. No `sudo` required for day-to-day operations.

---

## Models Validated

Benchmarked on AMD Ryzen AI Max+ 395 · Radeon 8060S (gfx1151) · Vulkan

| Model | Quantization | Speed | Notes |
|-------|--------------|-------|-------|
| Qwen3.5-35B-A3B | UD-Q6_K_XL | ~29 t/s | Daily driver, tool calling |
| Qwen3.5-122B-A10B | UD-Q4_K_XL | ~24 t/s | High-quality reasoning |
| Qwen3-30B-A3B | Q4_K_M | ~66 t/s | Batch pipeline work |
| GLM-4.7-Flash | Q6_K | ~58 t/s | Fast agentic tasks |
| whisper large-v3-turbo | Q5 | ~3-4GB VRAM | Voice transcription |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STMNA Desk                               │
│                                                                 │
│  ┌──────────────┐   ┌───────────────────────────────────────┐  │
│  │  llama-swap  │──▶│  llama.cpp (Vulkan)                   │  │
│  │  :8081       │   │  Loads models on demand               │  │
│  └──────────────┘   └───────────────────────────────────────┘  │
│         │                                                       │
│  ┌──────┴──────┬────────────┬────────────┐                     │
│  ▼             ▼            ▼            ▼                     │
│ Open WebUI    n8n       whisper.cpp   Crawl4AI                 │
│ (Chat+Search) (Signal)  (Voice STT)  (Web scrape)             │
│                                                                 │
│  ┌──────────────┐   ┌────────────┐   ┌────────────────────┐   │
│  │  SearXNG     │   │  Qdrant    │   │  PostgreSQL        │   │
│  │  :8888       │   │  :6333     │   │  :5432             │   │
│  └──────────────┘   └────────────┘   └────────────────────┘   │
│                                                                 │
│  All containers: rootless Podman · stmna-net bridge            │
└─────────────────────────────────────────────────────────────────┘
         │  Tailscale / Headscale VPN
         │
    ┌────┴────┐
    │  Caddy  │  ← VPS, HTTPS termination, bearer token auth
    └─────────┘
         │
    Remote clients (laptop, mobile, team)
```

---

## Quick Start

> Full setup guide: [docs/architecture.md](docs/architecture.md)

### Prerequisites

- Framework Desktop 128GB (or equivalent AMD Strix Halo system)
- Ubuntu 24.04 LTS installed
- Podman installed (rootless, no root daemon needed)

### 1. Clone

```bash
git clone https://github.com/stmna-io/stmna-desk.git
cd stmna-desk
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your paths, ports, and model locations
```

### 3. Deploy Core Stack

```bash
# See docs/architecture.md for full deployment sequence
# Examples in examples/ for individual service compose files
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Hardware Guide](docs/hardware-guide.md) | Framework Desktop specs, AMD considerations, RAM requirements |
| [Inference Stack](docs/inference-stack.md) | llama-swap, llama.cpp, Qwen 3.5 family, think/nothink modes |
| [Architecture](docs/architecture.md) | Rootless Podman topology, networking, container architecture |
| [Remote Access](docs/remote-access.md) | Headscale VPN, Caddy bearer token auth |
| [Full Stack Deployment](docs/full-stack-deployment.md) | Optional: Nextcloud + Forgejo on the same machine |

---

## Products Built on STMNA Desk

| Product | Description | Repo |
|---------|-------------|------|
| **STMNA Signal** | Content intelligence pipeline (YouTube → vault) | [stmna-signal](https://github.com/stmna-io/stmna-signal) |
| **STMNA Voice** | Sovereign speech-to-text pipeline | [stmna-voice](https://github.com/stmna-io/stmna-voice) |

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

Areas appreciated:
- 📊 Benchmark data on different AMD hardware configurations
- 📝 Documentation improvements
- 🔧 Additional compose snippets for services
- 🐛 Bug reports and fixes

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

<div align="center">
  <sub>Built by <a href="https://stmna.io">STMNA_</a> · Engineered resilience. Sovereign by design.</sub>
</div>
