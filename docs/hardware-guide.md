# Hardware Guide

This guide covers the physical hardware running the STMNA_Desk stack, how it compares to the alternatives, and why the specific choices were made. If you're evaluating hardware for local AI inference, whether for personal use, a solo practice, or a small team, the reasoning and trade-offs for each option are documented here.

---


## The Machine

| Component | Specification |
|-----------|---------------|
| **Chassis** | Framework Desktop DIY Edition (4.5L Mini-ITX) |
| **CPU/APU** | AMD Ryzen AI Max+ 395 (Strix Halo, gfx1151) |
| **Cores** | 16 cores / 32 threads (Zen 5) |
| **GPU** | Radeon 8060S (integrated, 40 RDNA 3.5 CUs) |
| **Unified Memory** | 128GB LPDDR5X-8000 (shared CPU + GPU pool) |
| **Memory Bandwidth** | 256 GB/s |
| **GPU-Allocatable RAM** | ~96GB (Windows), ~110GB (Linux) |
| **Storage** | 2x M.2 2280 NVMe slots (user-replaceable) |
| **OS** | Ubuntu 24.04 LTS Server |
| **Cooling** | Noctua NF-A12x25 HS-PWM (recommended upgrade) |
| **Price (EU, March 2026)** | ~€3,100 (128GB + Noctua fan, without SSD) |

The 128GB unified memory pool is the feature that defines this class of hardware for AI workloads. CPU and GPU share the same physical memory. When llama.cpp loads a model via the Vulkan backend, it goes directly into this shared pool. The GPU reads model weights at memory speed, the CPU handles everything else, and there's no bus transfer between the two.

On cooling: the Framework Desktop ships with a choice of fans. The Noctua NF-A12x25 HS-PWM is worth the upgrade. Under sustained inference load, it keeps the machine quiet enough to sit on a desk in a home office without being disruptive. This matters because the machine runs 24/7 as a headless server. The larger 4.5L Mini-ITX chassis also helps: NotebookCheck measured the Framework Desktop at around 144W under sustained load (Prime95), compared to ~186W for the GMKtec EVO-X2 running the same silicon in a smaller chassis. The extra thermal headroom means cooler operation, lower fan speeds, and longer component life.

---

## What 128GB Enables

Qwen3.5-122B (68.4GB at Q4_K_XL) loads in full with room left for concurrent services. Qwen3.5-35B (30.3GB at Q6_K_XL) leaves over 90GB free for additional models and extended context. You can keep multiple models warm simultaneously: a daily driver for chat and autonomous agents, a lightweight model for fast low-latency tasks, speech-to-text running in parallel, text-to-speech ready on demand. Context windows of 65K+ tokens don't compete with model weight memory.

At 64GB, every model choice is a compromise. You're picking between running the best model at short context or a smaller model at long context. At 128GB, there's room for the flagship model, room for concurrent services, and room for the context window the task actually requires.


---


## Framework vs. Other Strix Halo Systems

The Ryzen AI Max+ 395 isn't exclusive to Framework. Several mini PCs ship with the same silicon, and the performance differences between them are minimal since they all share the same CPU, GPU, and memory controller. The variables are cooling, build quality, form factor, warranty, and price.

### The Strix Halo Landscape (March 2026)

| System | Price (EU, 128GB) | Storage | Notes |
|--------|------------------|---------|-------|
| **Framework Desktop** | ~€3,100 (no SSD) | 2x M.2 2280, replaceable | Best thermals/noise, lowest power (~144W load), Noctua option, Mini-ITX standard, PCIe x4 slot |
| **Corsair AI Workstation 300** | ~€2,400 | 2x M.2 2280 (2x 2TB included) | Liquid-cooled, 2-year warranty with advance replacement, quiet under normal load, integrated 350W PSU. Liquid cooling longevity is a question mark for a 24/7 server |
| **GMKtec EVO-X2** | ~€2,750 (with 2TB) | 1x M.2 2280 | Decent community adoption but inconsistent availability. Plastic build, higher power draw (~186W), and unknown long-term warranty/support track record |
| **Beelink GTR9 Pro** | Availability unclear | M.2 2280 | Dual 10GbE. Early units had stability issues (motherboard revision 2.2+ required). Not readily available in EU as of March 2026 |
| **Minisforum MS-S1 MAX** | Availability unclear | M.2 2280, PCIe slot | PCIe expansion, dual 10GbE. Some Linux NIC issues reported. Not readily available in EU as of March 2026 |
| **HP Z2 Mini G1a** | ~€3,600 (128GB, 2TB) | 2x M.2 2280 | ISV-certified workstation. Tool-less chassis, 300W internal PSU, Flex I/O modules (10GbE optional), Thunderbolt 4. Pro variant uses Ryzen AI Max Pro. Loud under full load (~70dB reported). Enterprise warranty and support |

**Why Framework was chosen for STMNA_Desk:**

The Framework Desktop draws roughly 40W less than smaller-chassis alternatives under the same sustained load. Over months of 24/7 operation, that difference compounds in power costs, heat output, and component stress. The Noctua fan makes it the quietest air-cooled option in the lineup. The 4.5L Mini-ITX chassis uses standard PC components: standard ATX power connector, standard 120mm fan mount, two M.2 2280 SSD slots, and a PCI-E 4.0 x4 expansion slot.

The CPU and RAM are soldered to the mainboard. This is a physics constraint shared by every Strix Halo system on the market, not a Framework-specific choice. The 256-bit LPDDR5X memory bus requires signal integrity that socketed memory can't achieve. Framework worked with AMD to explore alternatives (including LPCAMM) and concluded that detachable RAM would cut bandwidth roughly in half.

If the RAM or CPU fails, the mainboard needs to be replaced. But SSD, PSU, fan, and expansion cards remain fully user-replaceable with standard off-the-shelf parts. No other Strix Halo system on the market offers that. The Corsair, GMKtec, and Beelink units are effectively sealed boxes where the only accessible component is the SSD.

**The Corsair is worth a look at €2,400.** The 2-year warranty with advance replacement is notably better than what most Strix Halo vendors offer, and the machine includes 4TB of SSD storage. The question is whether liquid cooling is the right choice for a machine you intend to run 24/7. AIO liquid coolers degrade over time (pump wear, coolant evaporation), and replacement in a compact proprietary chassis is not straightforward. For a headless server expected to run continuously for years, air cooling is probably a safer bet.


---


## Hardware Alternatives: DGX Spark (GB10)

The DGX Spark and its OEM variants (ASUS Ascent GX10, Lenovo ThinkStation PGX) are the direct competitor to Strix Halo. Same 128GB unified memory, different architecture, different trade-offs. The Lenovo PGX uses the same GB10 chip as the DGX Spark in a ThinkStation chassis, priced at ~€3,700 (1TB) in the EU. It adds Lenovo's corporate procurement and Premier Support, making it the most enterprise-friendly GB10 option. All GB10 variants share essentially identical performance since NVIDIA keeps tight control over the hardware configuration.

### Comparison Table

| | Framework Desktop (Strix Halo) | DGX Spark / OEM GB10 variants |
|---|---|---|
| **Price (EU, March 2026)** | ~€3,320 (with 2TB SSD) | €4,500 (Founders, 4TB) / €3,500 (ASUS, 1TB) / €3,700 (Lenovo PGX, 1TB) |
| **CPU** | x86 Zen 5, 16c/32t | Arm (10x Cortex-X925 + 10x A725) |
| **GPU Compute** | Vulkan via Radeon 8060S | CUDA via Blackwell GPU |
| **Memory** | 128GB LPDDR5X, 256 GB/s | 128GB LPDDR5X, 273 GB/s |
| **FP4 Hardware** | No | Yes (NVFP4, fifth-gen Tensor Cores) |
| **Storage** | 2TB NVMe M.2 2280 (replaceable) | 4TB M.2 2242 (Founders) / 1TB (ASUS). Rare form factor, difficult replacement |
| **OS** | Any Linux distro, Windows | DGX OS (Ubuntu for Arm) |
| **General Purpose** | Full desktop/server | AI-focused appliance |
| **Networking** | 5GbE, Wi-Fi 7, PCIe x4 slot | 10GbE + dual ConnectX-7 200Gbps (NVLink clustering) |
| **Power Draw (sustained)** | ~144W (under inference load) | ~140W TDP (GB10 chip), ~180-200W system total |
| **Noise** | Quiet with Noctua (sub-40 dBA) | Small chassis, audible under load. OEM units vary |
| **Repairability** | SSD/PSU/fan replaceable | Fully sealed |

### Where the DGX Spark Wins

**Prompt processing (prefill).** The Blackwell GPU processes input context 2-3x faster than Strix Halo's Radeon 8060S. This matters for workloads that ingest large codebases, extended conversation histories, or deep context before generating output. The gap widens with longer inputs.

**CUDA ecosystem.** If your workflow depends on PyTorch, vLLM, TensorRT-LLM, or other CUDA-specific tools, the Spark runs them natively. These frameworks are mature, well-documented, and have the largest community. On Strix Halo, GPU-accelerated inference runs through Vulkan (stable but smaller ecosystem), and training workloads wait for ROCm maturity.

**Fine-tuning.** Both platforms can run QLoRA fine-tuning on this class of hardware. The GB10 does it roughly 2-3x faster thanks to CUDA and its Tensor Cores. For teams that fine-tune models regularly, this time difference adds up. For occasional fine-tuning, Strix Halo handles it adequately through Vulkan.

**NVLink clustering.** Two DGX Spark units can be linked via ConnectX-7 for 256GB combined memory, enabling models that don't fit in 128GB. No Strix Halo system offers equivalent hardware-level scaling.

**Day-one software experience.** The Spark ships with a pre-configured AI development environment, playbooks, and documentation. For someone new to local AI who wants to unbox and start experimenting, the friction is lower.

### Where Strix Halo Wins

**Price-to-performance for daily inference.** Strix Halo at 256 GB/s and the DGX Spark at 273 GB/s produce nearly identical token generation speeds for the same models. The difference is the price tag: a Framework Desktop at €3,320 delivers a great daily-use experience while the DGX Spark does it at €4,500 and the ASUS Ascent at €3,700. Dollar for dollar, Strix Halo is the better deal for inference-focused workloads.

**x86 compatibility.** Strix Halo runs standard x86 Linux. Every container image on Docker Hub, every amd64 binary, every tool in the Linux ecosystem works without emulation. The Spark runs Arm, and while Arm support has improved significantly, the ecosystem is thinner. For an always-on server, x86 means fewer surprises.

**The real comparison with the ASUS Ascent GX10 and Lenovo PGX.** Both ship with 1TB of storage. Adding a 2TB M.2 2242 drive costs around €200, bringing the ASUS to ~€3,700 and the Lenovo PGX to ~€3,900. The Framework Desktop with 2TB SSD comes to ~€3,320. That's a ~€400-€600 gap, depending on the GB10 variant, for a sealed Arm device. ASUS's FAQ states that opening the unit voids the warranty. The Lenovo PGX includes Premier Support.

**Repairability and longevity.** The Framework Desktop lets you replace the SSD, PSU, fan, and expansion cards with standard off-the-shelf parts. The DGX Spark variants are sealed units where component replacement is limited.

### When to Choose the DGX Spark Anyway

If your workflow lives in the CUDA ecosystem (PyTorch training, vLLM serving, TensorRT optimization), the Spark removes a category of friction that Strix Halo can't match today. If you need NVLink scaling to 256GB for models that don't fit in 128GB, nothing else in this price range offers it. And if the time saved with faster prefill and fine-tuning justifies the premium, it's a legitimate choice.


---


## Hardware Alternatives: Mac Studio

Apple's Mac Studio with the M4 Ultra is the premium option in unified memory inference hardware.

### Comparison Table

| | Framework Desktop (Strix Halo) | Mac Studio M4 Ultra (128GB) |
|---|---|---|
| **Price (EU, March 2026)** | ~€3,320 (with 2TB SSD) | ~€4,200 (512GB SSD) / ~€5,000 (2TB SSD) |
| **Max Memory** | 128GB | 192GB (M4 Ultra max config) |
| **Memory Bandwidth** | 256 GB/s | 819 GB/s (M4 Ultra) |
| **GPU Compute** | Vulkan | Metal |
| **Inference Runtime** | llama.cpp (Vulkan) | llama.cpp (Metal) |
| **OS** | Linux (any distro) | macOS only |
| **Container Runtime** | Podman/Docker (native Linux) | Docker Desktop (Linux VM layer) |
| **Power Draw** | ~144W under load, ~50W idle | ~60W under load, ~10W idle |
| **Noise** | Quiet with Noctua | Near-silent (Apple thermal design) |
| **Warranty** | Framework standard | Apple 1yr (AppleCare+ extends to 3yr) |
| **Repairability** | SSD/PSU/fan replaceable | Fully sealed, Apple service only |

### The Mac Studio's Real Advantage: Bandwidth and Efficiency

The M4 Ultra's 819 GB/s memory bandwidth is over 3x what Strix Halo delivers. For single-user token generation, this translates directly to faster output. The Mac Studio is also remarkably power-efficient (under 60W during inference) and near-silent. If raw inference speed, silence, and power efficiency are your priorities, nothing else in this class touches it.

### The Trade-offs vs. The Framework Desktop

**Cost.** The 128GB M4 Ultra starts at ~€4,200 with a 512GB SSD, or ~€5,000 with 2TB. That's 25-50% more than a Framework Desktop.

**macOS as a server OS.** The Mac Studio can run as a headless server, but it takes extra work. Docker containers run inside a Linux VM, adding overhead and networking complexity. Headless operation and sleep management require workarounds that Linux doesn't need. These are solved problems, but they add setup and maintenance time compared to Ubuntu where always-on operation is the default.

### Who Should Pick the Mac Studio

The Mac Studio is the best pure inference machine in this price class. Its memory bandwidth advantage (819 GB/s vs 256 GB/s) translates directly to faster token generation, and it does this near-silently at under 60W. For any use case where speed-per-token matters most, it's hard to beat.

Where it's less suited is as an all-in-one server running a full stack of containerized services, automated pipelines, and remote access. That workload is more natural on Linux. But as a dedicated inference endpoint that a Linux server orchestrates and clients can query over the network, the Mac Studio is an excellent option if price is not an issue. Apple's warranty and support ecosystem are well-established, and the 192GB M4 Ultra config goes beyond what any Strix Halo system offers in memory capacity.


---


## Hardware Alternatives: Discrete GPUs

Discrete NVIDIA GPUs remain the default recommendation in most AI communities. For training and fine-tuning, that recommendation is correct. For inference at the scale STMNA_Desk operates (Qwen3.5-122B as the flagship model), the trade-offs are worth examining.

### The VRAM Constraint

The current consumer ceiling is 24GB (RTX 4090) or 32GB (RTX 5090) of VRAM. Qwen3.5-122B at Q4_K_XL requires 68.4GB. Neither card can hold it. You can offload layers to system RAM, but the PCIe bus becomes a severe bottleneck and token generation drops to single digits.

The cheapest path the community has found to large VRAM pools is used RTX 3090s (24GB each), which remain the best VRAM-per-euro on the secondary market:

| Configuration | Total VRAM | Approx. Cost (EU) | Status |
|---------------|-----------|-------------------|--------|
| 3x RTX 3090 (used) | 72GB | ~€3,000-~€3,600 + host system (~€500-1,000) | Used market only. Still short of 122B Q4 + KV cache |
| RTX 5090 (new) | 32GB | ~€3,450 (street price, volatile) | 32GB GDDR7, 1.7 TB/s bandwidth. Scarce stock, prices well above MSRP |
| RTX 4090 (new) | 24GB | ~€2,800 (while stock lasts) | Production ceased Oct 2024. Prices rising |

### Where Discrete GPUs Win

**Training and fine-tuning.** CUDA tensor cores and high-bandwidth VRAM are purpose-built for these workloads. An RTX 4090 doing LoRA fine-tuning outperforms Strix Halo by a wide margin. If regular fine-tuning on custom datasets is core to your workflow, discrete GPU hardware (or the DGX Spark) is the better fit.

**Raw speed for models that fit in VRAM.** For a model that sits entirely in a single GPU's memory, a discrete card generates tokens much faster. An RTX 4090 at 936 GB/s of memory bandwidth is nearly 4x what Strix Halo offers. For models up to ~13B at Q8 or ~30B at Q4, a single discrete GPU is faster and often cheaper.

### Where Unified Memory Wins

**Running the largest models at all.** Qwen3.5-122B doesn't fit in 24GB or 32GB of VRAM. Even 72GB across three 3090s is tight once you account for KV cache at long context. Unified memory at 128GB is the only consumer-accessible path to running 122B-class models from a single machine without layer offloading.

**Noise, power, and form factor.** Three RTX 3090s pull 350W each under load, over a kilowatt for the GPUs alone. An RTX 5090 at 575W needs serious cooling on its own. The noise output is server-room territory, not desk territory. The Framework Desktop at 144W total system power with a Noctua fan is a different category entirely.

**Concurrent model serving.** Strix Halo can keep multiple models warm in memory simultaneously: an always-on inference model, a lightweight model for fast tasks, speech-to-text and text-to-speech ready on demand. On a 24GB GPU, you pick one model at a time.

**Operational simplicity.** Getting a single unified-memory machine running inference is much simpler than getting a multi-GPU rig working. Choosing the latter means you're ready to deal with PCIe slot topology, multi-GPU driver configuration, power delivery across multiple high-wattage cables, and thermal management for a kilowatt of heat in an enclosed space. It's a rewarding project if you enjoy the process, but spending days on it is simply a different kind of commitment.


---


## Cost Analysis vs. Cloud APIs

The total hardware cost is approximately €3,320 (Framework Desktop ~€3,100 with Noctua fan, 2TB NVMe ~€220). Annual power costs run €200-400 depending on inference load. Over five years, the total cost of ownership is roughly €4,520.

Cloud API costs depend heavily on usage patterns and model tier. A managed AI subscription caps out quickly for power users. API-level access for daily inference workloads (summarization, translation, transcription, RAG queries) can run €1,000-4,000/year depending on volume and model size. There's also the value of running everything locally: your data stays on your network, your workflows don't depend on external API availability, and you're not subject to changes in a provider's pricing or privacy terms. It's hard to put a number on that, but it can't be discounted.


---


## Storage Recommendations

Models are the largest storage consumer. Qwen3.5-122B alone takes 68.4GB in its quantized form. If you plan to keep several model variants available for hot-swapping, budget accordingly. A 2TB NVMe is comfortable for a moderate collection; users stocking many large models may want to add a second drive (the Framework Desktop has two M.2 2280 slots).

Model loading speed from NVMe is not the inference bottleneck (memory bandwidth is). A fast SSD reduces initial model load time when swapping models, but doesn't affect token generation speed once a model is loaded. Prioritize capacity over sequential read speed when choosing a drive.


---


## Power and Thermals

| State | Power Draw (wall) |
|-------|-------------------|
| Idle (system off / sleep) | ~12W |
| Idle (all services running, no inference) | ~50W |
| Active inference (single model loaded) | ~100-150W |
| Peak (sustained heavy workload) | ~180W |
| Estimated annual cost (moderate usage) | €200-400 |

The Framework Desktop runs continuously as a headless server. With the Noctua NF-A12x25 fan, it handles sustained inference loads while being hardly noticeable. The chassis thermal design prevents throttling during extended generation runs.

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


## A Word on Vulkan vs. ROCm

The entire STMNA_Desk inference layer runs through Vulkan. ROCm support for gfx1151 (Strix Halo) on Ubuntu 24.04 LTS is incomplete today, and Vulkan through llama.cpp is stable and production-ready on this hardware. This is a pragmatic choice, not a permanent one.

For the full rationale, the Fedora/vLLM path, and upstream PRs tracking Vulkan shader improvements: [Inference Stack](inference-stack.md#why-vulkan-not-rocm).


---


## What The Framework Desktop Doesn't Do (and What It Does, With Caveats)

**Training and fine-tuning:** possible, but slower than dedicated GPU hardware. QLoRA fine-tuning of models up to 30B parameters works on this hardware through the Vulkan backend. It's not fast compared to an RTX 4090 or a DGX Spark, but it's functional for workflows that include occasional fine-tuning rather than continuous training runs. Full fine-tuning of large models is impractical without ROCm or CUDA, but that's a software constraint that Ubuntu 26.04 is expected to address.

**vLLM:** not officially supported on gfx1151 yet, but functional through community effort. kyuz0's containerized vLLM toolbox (Fedora 43-based, ROCm nightly builds, patched for gfx1151 device detection) runs on kernel 6.18.4+. Fedora ships newer kernels faster than Ubuntu, making it the preferred distro for this path today. The trade-off: you're running nightly ROCm builds and community patches rather than stable upstream releases, and the setup requires more hands-on configuration. 


