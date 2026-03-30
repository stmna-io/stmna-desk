# STMNA_Desk Install Guide

> Step-by-step base system setup for STMNA_Desk: Ubuntu installation, AMD GPU drivers, Vulkan validation, rootless Podman, and container networking. Once the base is ready, deploy services using the compose files in [`/stacks/`](../stacks/).
>
> This guide was built and validated on a Framework Desktop with AMD Ryzen AI Max+ 395 (Strix Halo) running Ubuntu 24.04 LTS. The Podman and networking steps (Steps 4-5) apply to any Linux system. The driver and kernel configuration (Steps 1-3) are specific to AMD Strix Halo on Ubuntu. If you're running different hardware, follow your vendor's driver documentation and pick up from Step 4.
>
> The GTT memory configuration in this guide builds on the work documented by [technigmaai](https://github.com/technigmaai/technigmaai-wiki/wiki/AMD-Ryzen-AI-Max--395:-GTT--Memory-Step%E2%80%90by%E2%80%90Step-Instructions-%28Ubuntu-24.04%29).

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Framework Desktop 128GB (or equivalent Strix Halo system) | See [hardware-guide.md](hardware-guide.md) for the full hardware breakdown |
| Ubuntu 24.04 LTS Server ISO | [ubuntu.com/download/server](https://ubuntu.com/download/server) |
| USB drive (4GB+) | For the Ubuntu installer |
| Internet connection | WiFi during install, Ethernet after HWE kernel |

---

## Step 1: Ubuntu 24.04 LTS on Strix Halo

### Creating the installer

Download Ubuntu 24.04 LTS Server and flash it to a USB drive:

```bash
sudo dd if=ubuntu-24.04-live-server-amd64.iso of=/dev/sdX bs=4M status=progress
sync
```

### BIOS settings

Enter BIOS (F2 during POST on Framework Desktop) and configure:

| Setting | Value | Why |
|---------|-------|-----|
| UMA Frame Buffer Size | 512MB | Base VRAM allocation. Linux overrides this via kernel params for the full 128GB GTT pool |
| IOMMU | Disabled | Prevents memory allocation failures with large GPU allocations on Strix Halo |

### Installation notes

- Use **WiFi during installation**. Ethernet (enp191s0) requires the HWE kernel and won't work on the stock 6.8 kernel
- Choose "Ubuntu Server (minimized)" if offered. No desktop environment needed for a headless inference server
- Create the `stmna` user during installation, or create it in Step 4
- Enable OpenSSH server when prompted
- Use LVM, no LUKS encryption. LUKS only protects powered-off machines and complicates remote reboots

### Expand the LVM volume

Ubuntu Server defaults to a 100GB root partition regardless of drive size. Expand it immediately after first boot, before downloading anything:

```bash
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```

Verify:

```bash
df -h /
```

**Expected:** Your full drive capacity minus a small overhead.

### Install the HWE kernel

The stock 6.8 kernel has incomplete support for gfx1151. The Hardware Enablement (HWE) kernel is required for stable Vulkan inference and Ethernet.

```bash
sudo apt update && sudo apt install -y linux-generic-hwe-24.04
sudo reboot
```

After reboot, verify:

```bash
uname -r
```

**Expected:** `6.14` or newer (this guide was validated on 6.17).

### Configure Ethernet

With the HWE kernel installed, Ethernet becomes available:

```bash
sudo nano /etc/netplan/01-ethernet.yaml
```

```yaml
network:
  version: 2
  ethernets:
    enp191s0:
      dhcp4: true
```

```bash
sudo netplan apply
```

You can now switch from WiFi to Ethernet for the rest of the setup.

---

## Step 2: GPU Memory Configuration

Strix Halo's integrated GPU shares the system memory pool, but the kernel needs explicit parameters to allocate enough of it for large model inference. Without these, llama.cpp will fail to load models larger than a few GB.

### Kernel parameters

```bash
sudo nano /etc/default/grub
```

Find the `GRUB_CMDLINE_LINUX_DEFAULT` line and set:

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amd_iommu=off amdgpu.gttsize=131072 ttm.pages_limit=33554432"
```

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `amd_iommu` | off | Disables IOMMU, reduces latency for Strix Halo |
| `amdgpu.gttsize` | 131072 | Sets GTT (Graphics Translation Table) size to 128GB |
| `ttm.pages_limit` | 33554432 | Sets the TTM page pool to 128GB (33554432 x 4KB pages) |

```bash
sudo update-grub
```

### udev rules for GPU device access

Without these, rootless containers won't be able to access the GPU:

```bash
sudo tee /etc/udev/rules.d/99-amd-kfd.rules << 'EOF'
SUBSYSTEM=="kfd", GROUP="render", MODE="0666", OPTIONS+="last_rule"
SUBSYSTEM=="drm", KERNEL=="card[0-9]*", GROUP="render", MODE="0666", OPTIONS+="last_rule"
SUBSYSTEM=="drm", KERNEL=="renderD[0-9]*", GROUP="render", MODE="0666"
EOF
```

### Add the stmna user to GPU groups

```bash
sudo usermod -aG video,render stmna
```

### Reboot and verify

```bash
sudo reboot
```

After reboot:

```bash
# Verify kernel parameters
cat /proc/cmdline
# Should show: amd_iommu=off amdgpu.gttsize=131072 ttm.pages_limit=33554432

# Verify GPU memory pool (128GB)
cat /sys/class/drm/card1/device/mem_info_gtt_total
# Expected: ~137438953472 (128GB in bytes)

# Verify GPU device permissions
ls -la /dev/dri/
# Expected: card1 and renderD128 with render group
```

> **Note:** The card number (`card1`) may differ on your system. Check with `ls /sys/class/drm/` and look for the entry with an amdgpu driver: `cat /sys/class/drm/card*/device/uevent | grep DRIVER`.

---

## Step 3: Vulkan Verification

The HWE kernel pulls in Mesa with Vulkan RADV drivers as part of the standard update path. Ensure everything is current and install the diagnostic tools:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y vulkan-tools
```

Verify Vulkan sees the GPU:

```bash
vulkaninfo --summary
```

**Expected:** `Radeon 8060S` (or similar AMD device) listed under `Devices`. If `vulkaninfo` reports no devices, the kernel parameters from Step 2 may not be applied correctly. Check with `cat /proc/cmdline`.

---

## Step 4: Rootless Podman Setup

> From this step onward, the instructions apply to any Linux system with Podman, not just Strix Halo hardware.

### Create the stmna user (if not done during install)

```bash
sudo adduser stmna
```

### Configure rootless container support

```bash
# Enable linger (containers survive logout, start on boot)
sudo loginctl enable-linger stmna

# Configure subordinate UID/GID ranges for rootless containers
echo "stmna:200000:65536" | sudo tee -a /etc/subuid
echo "stmna:200000:65536" | sudo tee -a /etc/subgid
```

### Install Podman

```bash
sudo apt install -y podman podman-compose
```

### Verify

Log in as the `stmna` user:

```bash
sudo -u stmna -i
podman system migrate
podman run --rm docker.io/library/alpine echo "rootless podman works"
```

**Expected:** `rootless podman works` printed to the terminal.

```bash
podman --version
podman-compose version
```

**Expected:** Podman 4.x+ and podman-compose installed.

> **Note:** Your UID may differ from 1000. Note your UID, you'll need it when configuring Dockge's socket mount path (`/run/user/<UID>/podman/podman.sock`).

---

## Step 5: Container Network and Directory Structure

### Create the shared network

All STMNA services communicate over a shared Podman network:

```bash
podman network create stmna-net
```

Verify:

```bash
podman network ls
```

**Expected:** Both `podman` (default) and `stmna-net` listed.

### Create the directory structure

```bash
mkdir -p ~/stacks ~/models ~/data
```

| Path | Purpose | Notes |
|------|---------|-------|
| `~/stacks/` | Compose files, one directory per service | Copy from this repo's `/stacks/` |
| `~/models/` | GGUF model files for llama.cpp and whisper | 100GB+ depending on model selection |
| `~/data/` | Service data volumes (PostgreSQL, n8n, Open WebUI, etc.) | Include in backups |

Download models from [Hugging Face](https://huggingface.co) into `~/models/`. See [inference-stack.md](inference-stack.md) for model recommendations and benchmark data.

---

## Next Steps

You're set. From here:

1. **Deploy services** using the compose files in [`/stacks/`](../stacks/). Each has a `compose.yaml` with inline comments. Deploy via [Dockge](https://github.com/louislam/dockge) (recommended) or `podman-compose up -d`. All compose files should include `x-podman: in_pod: false` to prevent cgroup issues with rootless Podman
2. **Set up inference** with llama-swap. See [inference-stack.md](inference-stack.md) for model configuration and Vulkan kernel notes. Critical llama-server flags for Strix Halo: `-fa on --no-mmap` (both required, crashes without them)
3. **Configure remote access** if you need to reach the stack from outside your LAN. See [remote-access.md](remote-access.md) for options
4. **Deploy application pipelines** from the product repos:
   - [STMNA_Signal](https://github.com/stmna-io/stmna-signal): content ingestion and processing pipeline
   - [STMNA_Voice](https://github.com/stmna-io/stmna-voice): speech-to-text pipeline

---

## Troubleshooting

### Ethernet not working after install

**Cause:** The stock Ubuntu 6.8 kernel doesn't support the Framework Desktop's Ethernet controller. WiFi works on the stock kernel.

**Fix:** Install the HWE kernel (Step 1), reboot, then configure Netplan for Ethernet.

### Root partition full (100GB on larger drive)

Ubuntu Server LVM defaults to allocating only 100GB regardless of drive size.
```bash
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```

### Vulkan: "No devices found" in vulkaninfo

**Cause:** Missing kernel parameters or HWE kernel not installed.

**Fix:** Verify kernel parameters are active:

```bash
cat /proc/cmdline
```

Check for `amdgpu.gttsize=131072` and `ttm.pages_limit=33554432`. If missing, re-check `/etc/default/grub` and run `sudo update-grub && sudo reboot`.

### llama.cpp: model fails to load, Vulkan memory allocation error

**Cause:** GPU memory pool too small. Usually means kernel parameters are missing.

**Fix:** Verify GPU memory:

```bash
cat /sys/class/drm/card1/device/mem_info_gtt_total
```

Should show ~137 billion (128GB). If smaller, kernel parameters aren't applied. See Step 2.

### llama-server crashes on start

Both `-fa on` and `--no-mmap` are required in the llama-server command line on Strix Halo. Without them, it will either crash or produce corrupted output. Check your config.

### "Container name already in use" on reboot

`podman-compose up -d` tries to recreate containers that already exist. For auto-start on boot, use `podman start <container-name>` in your startup script instead. Use compose only for first-time creation.

### podman-compose not found
```bash
sudo apt install -y podman-compose
```

If you installed via pipx instead: `pipx ensurepath && source ~/.bashrc`.

