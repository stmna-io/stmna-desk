# Hardware Guide

This guide covers the physical hardware running the STMNA Desk stack: what it is, why these specific components, and what to expect from them under sustained AI inference workloads. If you're evaluating whether to build something similar, the reasoning behind each choice is here.

---

## The Machine

| Component | Specification |
|-----------|---------------|
| **Chassis** | Framework Desktop DIY Edition |
| **CPU/APU** | AMD Ryzen AI Max+ 395 (Strix Halo) |
| **Cores** | 16 cores / 32 threads (Zen 5) |
| **GPU** | Radeon 8060S (integrated, gfx1151) |
| **Unified Memory** | 128GB DDR5 (shared CPU + GPU pool) |
| **GPU-Allocatable RAM** | ~96GB (Windows), ~110GB (Linux) |
| **Storage** | 2TB NVMe SSD |
| **OS** | Ubuntu 24.04 LTS Server |
| **Repairability** | Fully user-repairable (Framework design) |

The architectural feature that matters most for LLM inference is the 128GB unified memory pool. CPU and GPU share the same physical memory with no transfer bottleneck between them. When llama.cpp loads a 70B model via the Vulkan backend, it goes directly into this shared pool. No PCIe bus transfer, no VRAM ceiling separate from system RAM. The GPU accesses model weights at memory bandwidth speed, and the CPU handles everything else from the same pool.

This is fundamentally different from discrete GPU setups where VRAM is a hard cap. A 24GB GPU can only hold a 24GB model regardless of how much system RAM you have. Here, the entire 128GB (minus OS overhead) is available for model weights, KV cache, and service memory combined.

---

## Why This Hardware

### Cost-per-token economics

The total hardware cost is approximately EUR 2,650 (Framework Desktop ~EUR 2,500, 2TB NVMe ~EUR 150). Annual power costs run EUR 200-400 depending on inference load. Over five years, the total cost of ownership is roughly EUR 3,850.

Compare that to cloud API costs at moderate usage (50-100 requests/day with mixed model sizes): EUR 12,000-21,600 over the same period. After hardware amortization, every token is effectively free. The economics get better the more you use it, which is the opposite of API pricing.

### What 128GB enables

Most consumer AI hardware maxes out at 64GB unified (Mac Studio) or 24GB VRAM (RTX 4090). At 128GB:

- Qwen3.5-122B (68.4GB at Q4_K_XL) loads in full with room left for services
- Qwen3.5-35B (30.3GB at Q6_K_XL) leaves 90GB+ free for concurrent models and context
- Multiple models stay warm simultaneously (daily driver + voice model + embeddings)
- 65K+ token context windows don't compete with model weight memory

At 64GB, you'd be choosing between model quality and context length. At 128GB, you don't have to.

### The GPU situation

Strix Halo's integrated Radeon 8060S runs llama.cpp and whisper.cpp natively through Vulkan. It handles inference at production-usable speeds (Qwen3.5-35B at 28-29 t/s, Qwen3-30B at 64 t/s). For the workloads this stack runs (summarization, transcription, translation, RAG), Vulkan inference is sufficient.

The trade-off is real though. Standard transformer models run well on Vulkan. Qwen3.5's newer gated delta net (linear attention) architecture doesn't yet have an optimized Vulkan shader in llama.cpp, resulting in ~55% slower speeds compared to standard transformers of equivalent active parameter count. This is a software limitation, not hardware. The upstream fix is tracked in [llama.cpp PR #19504](https://github.com/ggml-org/llama.cpp/pull/19504).

---

## Storage Layout

| Path | Purpose | Typical Size |
|------|---------|-------------|
| `~/stacks/` | Compose files for all services (one directory per stack) | ~50MB |
| `~/models/` | LLM and whisper model files (GGUF format) | ~107GB |
| `~/data/` | Service data volumes (n8n, PostgreSQL, Open WebUI, etc.) | ~5-20GB |
| `/data/second-brain/` | Obsidian vault on disk (mounted read-only in n8n) | ~500MB |

Models, stack configs, and data volumes are deliberately separated. Models are large, static files that rarely change. Stack configs are small and version-controlled. Data volumes grow over time and need backup consideration. Keeping them in separate paths makes backup, migration, and storage monitoring straightforward.

The 2TB NVMe handles all of this comfortably. Model loading speed from NVMe is not the bottleneck (memory bandwidth is). A fast SSD reduces initial model load time (the first request after a swap) but doesn't affect inference speed once loaded.

---

## Power and Thermals

| State | Power Draw |
|-------|-----------|
| Idle (all services running, no inference) | ~50W |
| Active inference (single model loaded) | ~200-300W |
| Estimated annual cost (moderate usage) | EUR 200-400 |

The Framework Desktop runs continuously as a headless server. Under sustained inference load, the fan is audible but not disruptive in a home office. The chassis thermal design handles extended generation runs without throttling.

Power monitoring from the host uses sysfs rather than rocm-smi (which is not installed):

```bash
# GPU utilization
cat /sys/class/drm/card1/device/gpu_busy_percent

# GPU clock speed
cat /sys/class/drm/card1/device/pp_dpm_sclk

# Temperature
cat /sys/class/drm/card1/device/hwmon/hwmon*/temp1_input
```

---

## What This Doesn't Do

No discrete GPU means no CUDA or ROCm GPU acceleration for workloads that require it. Training, fine-tuning, and batch embedding jobs that depend on GPU-specific frameworks (PyTorch with CUDA, DeepSpeed) won't run here.

vLLM support for Strix Halo requires kernel 6.18.4+ and safetensors model format. The current stable kernel (6.17.0) doesn't meet this requirement. Ubuntu 26.04 LTS (expected April 2026) should resolve this. Until then, llama.cpp with Vulkan is the inference path.

This hardware is a single-user inference server, not a multi-tenant GPU cluster. It handles concurrent requests (llama-swap routes to available slots) but it's designed for one person's workloads, not shared team infrastructure.

---

*Last updated: 2026-03-04*
