# Inference Stack

How models are served, what's running, and the decisions behind the software stack. If you're deploying a similar setup, debugging performance, or deciding between Vulkan and ROCm on AMD hardware, this is the doc.

For the full service map and port assignments, see the [README](../README.md).


---


## Why Vulkan, Not ROCm

ROCm is AMD's open-source compute stack (MIT licensed) and the native path for PyTorch, fine-tuning, and ML training workloads on AMD GPUs. On paper it's the obvious choice for an all-AMD machine.

In practice, ROCm support for gfx1151 (Strix Halo) on Ubuntu 24.04 LTS is incomplete. The drivers install but the coverage is patchy, and production stability for always-on inference isn't there yet. Vulkan support through llama.cpp and whisper.cpp is mature, stable, and runs natively on gfx1151 today. The entire inference layer in STMNA_Desk runs through Vulkan for that reason.

This is a pragmatic choice, not a permanent one. Ubuntu 26.04 LTS is expected to ship with native ROCm support for current AMD APUs. When that lands, it opens the door to PyTorch-based workloads on the same hardware: model fine-tuning, WhisperX for speaker diarization, custom training pipelines. If ROCm performance matches or exceeds Vulkan for llama.cpp and whisper.cpp inference, the stack can migrate fully. Until then, Vulkan is the proven path.

### Fedora and the vLLM Path

Fedora ships newer kernels faster than Ubuntu, making it the distro where bleeding-edge AMD support lands first. kyuz0's containerized vLLM toolbox (Fedora 43-based, ROCm nightly builds, patched for gfx1151 device detection) runs on kernel 6.18.4+. It works. If vLLM serving or other ROCm-dependent workloads are a priority for you, Fedora is worth serious consideration.

STMNA_Desk runs Ubuntu 24.04 LTS because LTS stability matters more for a 24/7 headless server running production pipelines. Kernel updates go through the HWE channel on a predictable cadence. Podman, systemd, and the broader container ecosystem have years of battle-tested packages on Ubuntu. There is a clear trade-off: you wait longer for new drivers and kernel features, but you get a base that rarely surprises you when you need the machine the most. For a server where uptime matters more than having the newest kernel, that's the right call.

If you're building a dedicated inference server and plan to iterate on models frequently (vLLM, fine-tuning experiments, rapid model evaluation), Fedora with kyuz0's tooling is a strong option. If you're building a platform that other services depend on (pipelines, agents, always-on transcription), Ubuntu LTS is safer.

### The Qwen3.5 Speed Situation

Qwen3.5 models use a gated delta net (GDN) linear attention mechanism. On current Vulkan builds of llama.cpp, this runs roughly 55% slower than equivalently-sized standard transformer models. The computation falls back to less efficient shader paths for the GDN operations.

This is actively being addressed upstream:

- [PR #20334](https://github.com/ggml-org/llama.cpp/pull/20334): Vulkan compute shader for GATED_DELTA_NET. Merged and functional. On build b8369, Qwen3.5-35B jumps from 29 t/s to 32.6 t/s (+11.7% TG). 
- [PR #20376](https://github.com/ggml-org/llama.cpp/pull/20376): f16 mixed-precision state for GDN. Potential further improvement, in progress.
- [Issue #20099](https://github.com/ggml-org/llama.cpp/issues/20099): Peg-constructed template regression. The current blocker preventing upgrade from b8182. Chat endpoint prompt processing drops from ~200 to ~75 t/s, adding ~3 seconds to time-to-first-token. Token generation is unaffected. Once this is fixed, the upgrade path is straightforward with no config changes needed.

Production stays on b8182 until #20099 is resolved. The GDN shader improvement is real and stable (10/10 stress test, zero Vulkan errors on b8369), so the upgrade will land as soon as the PP regression is fixed.

The quality and tool-calling capabilities of Qwen3.5 justify the speed trade-off for interactive use. For batch processing where throughput matters more than capability, Qwen3-30B-A3B-Instruct-2507 at 66 t/s remains the better choice.


---


## Model Inventory

### Always-On Group (persistent, never swapped)

| Model | Quantization | Port | Context | Speed | Purpose |
|-------|-------------|------|---------|-------|---------|
| Qwen3-30B-A3B-Instruct-2507 | Q6_K_XL | 9001 | 65536 | 66 t/s | Always-on daily driver, Signal pipeline batch processing |
| Qwen3-4B-Instruct-2507 | Q4_K_M | 9002 | 4096 | sub-second | Voice transcript cleanup |

Both groups serve on port 9001 via llama-swap. The always-on model is the default; daily models take over on demand and release back to the always-on model when idle.

### Daily Group (exclusive swap, one loaded at a time on port 9001)

| Model | Quantization | Size | Context | Speed | Best For |
|-------|-------------|------|---------|-------|----------|
| Qwen3.5-35B-A3B | Q6_K_XL | 30.3GB | 65536 | 29 t/s | Interactive chat, tool calling, agentic tasks |
| Qwen3.5-122B-A10B | Q4_K_XL | 68.4GB | 65536 | 24 t/s | High-quality multi-step reasoning, translation |
| GLM-4.7-Flash | Q6_K | ~6GB | 65536 | 58 t/s | Fast agentic tasks |

When a daily group model is loaded on port 9001, it takes over from the always-on Qwen3-30B. Qwen3-4B on port 9002 is unaffected.

**Why is GLM-4.7 faster than the 35B despite being a larger dense model?** Qwen3.5-35B is a Mixture-of-Experts model with only 3B parameters active per token, but it uses the gated delta net architecture, which currently lacks an optimized Vulkan shader in production builds (see the speed situation above). GLM-4.7 is a ~6B dense standard transformer that runs on well-optimized Vulkan code paths. The architecture penalty outweighs the parameter advantage.

### Non-LLM Models

| Service | Model | Port | Purpose |
|---------|-------|------|---------|
| whisper.cpp | large-v3-turbo Q5 | 8083/8084 | Speech-to-text (Vulkan) |
| Kokoro TTS | 82M param | 9005 | Text-to-speech (af_heart EN, ff_siwis FR) |

Two separate whisper instances prevent the STMNA_Voice and STMNA_Signal pipelines from blocking each other. If you only run one pipeline, a single instance works fine.


