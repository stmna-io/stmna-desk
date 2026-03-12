---
title: "STMNA Desk Install Guide"
repo: stmna-desk
prereq: none
validated: staging
updated: 2026-03-05
---

# STMNA Desk Install Guide

> Base system setup for the STMNA Desk inference stack: user account, rootless Podman, and container networking. Once the base is ready, deploy services using the compose files in [`/stacks/`](../stacks/).
>
> Tested on Ubuntu 24.04 LTS with rootless Podman 4.9.

## Prerequisites

| Requirement | Where to get it |
|-------------|----------------|
| Linux (Ubuntu 24.04 LTS recommended) | [ubuntu.com](https://ubuntu.com) |
| Podman 4.x+ | Pre-installed on Ubuntu 24.04. Run `podman --version` to check |
| A user account for running containers | See Step 1 below |
| GPU with Vulkan support (AMD recommended) | Required for llama-swap and Whisper inference |
| 32GB+ RAM (128GB recommended) | LLMs need memory. 128GB UMA lets you run 70B+ models |
| pipx | See Step 1 below |

> **Note:** The GPU requirement applies to llama-swap (LLM inference) and Whisper (transcription). Services like n8n, PostgreSQL, Kokoro TTS, Open WebUI, and Dockge run on CPU and work on any hardware.

---

## Step 1: System Setup

### Create the stmna user

If you do not already have a dedicated user for running containers:

```bash
sudo adduser stmna
sudo loginctl enable-linger stmna
```

**Expected result:** The `stmna` user exists and linger is enabled (containers survive logout and start on boot).

Verify:

```bash
id stmna
loginctl show-user stmna | grep Linger
```

**Expected result:**

```
uid=1000(stmna) gid=1000(stmna) groups=1000(stmna)
Linger=yes
```

> **Note:** Your UID may differ from 1000. Note your UID -- you will need it when configuring Dockge.

### Install pipx and podman-compose

Log in as the `stmna` user, then:

```bash
sudo apt install -y pipx
pipx install podman-compose
pipx ensurepath
source ~/.bashrc
```

> **Note:** `sudo apt install` requires your user to have sudo privileges and will prompt for a password. If deploying via automated scripts (e.g., Ansible, SSH), ensure sudo is configured for passwordless access or run this step interactively.

Verify:

```bash
podman-compose version
```

**Expected result:**

```
podman version 4.9.3
podman-compose version 1.5.0
```

> **Note:** If `podman-compose` is not found after install, run `pipx ensurepath` and open a new terminal.

---

## Step 2: Create the Container Network

All STMNA services communicate over a shared Podman network called `stmna-net`.

```bash
podman network create stmna-net
```

**Expected result:**

```
stmna-net
```

Verify:

```bash
podman network ls
```

**Expected result:** You should see both `podman` (default) and `stmna-net` listed.

---

## Next Steps

With the base system, drivers, and Podman configured, you're ready to deploy services. See the individual compose files in [`/stacks/`](../stacks/) for reference configurations, or check the product repos for complete deployment guides:

- [STMNA Signal](https://github.com/stmna-io/stmna-signal)  -- content ingestion and processing pipeline
- [STMNA Voice](https://github.com/stmna-io/stmna-voice)  -- speech-to-text pipeline

Each service has its own `compose.yaml` in the `stacks/` directory with inline comments explaining required and optional configuration values. Deploy them via [Dockge](https://github.com/louislam/dockge) (recommended) or `podman compose up -d`.

### Troubleshooting

#### podman-compose: "executable file not found in $PATH"

**Cause:** pipx installs binaries to `~/.local/bin/`, which may not be in your PATH.

**Fix:**

```bash
pipx ensurepath
source ~/.bashrc
```

Or open a new terminal session.

