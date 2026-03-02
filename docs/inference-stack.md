# Inference Stack

<!-- TODO: Write full inference stack guide for SB-05 session -->
<!-- Content: llama-swap architecture, llama.cpp Vulkan build, model families (Qwen 3.5 35B/122B,
     Qwen3-30B, GLM-4.7-Flash), think/nothink modes, config.yaml reference,
     model groups (daily, always-on), benchmarks table, llama-swap healthcheck config -->

## Placeholder

This document will cover:

- **llama-swap** — model hot-swap proxy architecture and config
- **llama.cpp Vulkan** — building for AMD gfx1151 (Strix Halo)
- **Model families**:
  - Qwen3.5-35B-A3B (daily driver, tool calling)
  - Qwen3.5-122B-A10B (high-quality reasoning)
  - Qwen3-30B-A3B (fast batch work)
  - GLM-4.7-Flash (agentic tasks)
  - whisper large-v3-turbo Q5 (voice transcription)
- **Think/nothink modes** — when to use each, temperature settings
- **Model groups** — persistent vs on-demand loading
- **Benchmark data** — t/s speeds on Strix Halo Vulkan
- **config.yaml reference** — annotated example

Coming in SB-05 session.
