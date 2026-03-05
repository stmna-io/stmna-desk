---
title: "STMNA Desk Install Guide"
repo: stmna-desk
prereq: none
validated: staging
updated: 2026-03-05
---

# STMNA Desk Install Guide

> By the end of this guide, you will have the full STMNA Desk inference stack running: LLM serving, speech-to-text, text-to-speech, embeddings, a chat UI, an automation engine, and an AI agent. All self-hosted, all rootless.
>
> Tested on Ubuntu 24.04 LTS with rootless Podman 4.9, deployed via Dockge on a staging VM (10.0.10.55) during SB-06.

## Prerequisites

| Requirement | Where to get it |
|-------------|----------------|
| Linux (Ubuntu 24.04 LTS recommended) | [ubuntu.com](https://ubuntu.com) |
| Podman 4.x+ | Pre-installed on Ubuntu 24.04. Run `podman --version` to check |
| A user account for running containers | See Step 1 below |
| GPU with Vulkan support (AMD recommended) | Required for llama-swap and Whisper inference |
| 32GB+ RAM (128GB recommended) | LLMs need memory. 128GB UMA lets you run 70B+ models |
| pipx | See Step 1 below |

> **Note:** The GPU requirement applies to llama-swap (LLM inference) and Whisper (transcription). Services like n8n, PostgreSQL, TEI, Kokoro TTS, Open WebUI, and Dockge run on CPU and work on any hardware.

## Installation Tiers

The STMNA Desk stack is organized into three tiers. Install what you need.

| Tier | Steps | Services | When you need it |
|------|-------|----------|-----------------|
| **Core** | 1-6 | System Setup, Network, Dockge, PostgreSQL+PGVector, llama-swap, Open WebUI | Chat + local LLM inference. Every user installs this. |
| **Automation** | 7-8 | n8n (custom image), Whisper (2 instances) | Adding Signal or Voice products. |
| **Extended** | 9-14 | TEI, Kokoro TTS, Forgejo, Agent Zero, Crawl4AI, SearXNG | Vault RAG, audio summaries, git hosting, AI agent, web scraping, search. Install what you need. |

---

# Core Tier (Steps 1-6)

> Chat + local LLM inference. Every user installs this.

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

## Step 3: Install Dockge

Dockge is the web UI for managing all your container stacks. Every service from this point forward is deployed through Dockge.

Create the stacks directory and the Dockge stack:

```bash
mkdir -p ~/stacks/dockge
```

Open `http://YOUR_IP:5001` in your browser after deployment. On first visit, create an admin account.

Create a new stack in Dockge named `dockge`, or create the file `~/stacks/dockge/compose.yaml` with the following content:

```yaml
# ============================================================
# STMNA Desk -- Dockge (Container Management UI)
# Part of: stmna-desk install guide, Step 3 (Core)
# Requires: rootless Podman, podman-compose
# ============================================================

x-podman:
  in_pod: false

services:
  dockge:
    # INFO: Web UI for managing Podman compose stacks
    image: docker.io/louislam/dockge:1
    container_name: dockge
    restart: always
    ports:
      # OPTIONAL -- change host port if 5001 conflicts
      - "5001:5001"
    volumes:
      # NO ACTION NEEDED -- rootless Podman socket
      # NOTE -- replace 1000 with your UID (run: id -u)
      - /run/user/1000/podman/podman.sock:/var/run/docker.sock
      # NO ACTION NEEDED -- persists Dockge settings
      - dockge_data:/app/data
      # USER INPUT REQUIRED -- path where your stacks live (must match your actual stacks directory)
      - /home/stmna/stacks:/home/stmna/stacks
    environment:
      # USER INPUT REQUIRED -- must match the stacks volume path above
      - DOCKGE_STACKS_DIR=/home/stmna/stacks

volumes:
  dockge_data:
    driver: local
    name: dockge_data
```

> **Required:** Replace `1000` in the Podman socket path with your actual UID. Run `id -u` to check.

> **Required:** Replace `/home/stmna/stacks` with your actual stacks directory path if different.

For the initial deploy (Dockge can not deploy itself through its own UI):

```bash
cd ~/stacks/dockge && podman-compose up -d
```

**Expected result:** Dockge is accessible at `http://YOUR_IP:5001`.

> **Note:** From this point forward, all stacks are deployed through the Dockge web UI. Open Dockge, click "Create", give the stack a name, paste the compose file, and click "Deploy". Terminal commands are only used for verification and troubleshooting.

---

## Step 4: PostgreSQL + PGVector

PostgreSQL stores the Signal pipeline data (queue, cache, users) and vault embeddings. The PGVector extension enables vector similarity search for RAG.

In Dockge, create a new stack named `postgres` with the following compose file:

```yaml
# ============================================================
# STMNA Desk -- PostgreSQL + PGVector
# Part of: stmna-desk install guide, Step 4 (Core)
# Requires: stmna-net network
# ============================================================

x-podman:
  in_pod: false

services:
  postgres-voice:
    # INFO: PostgreSQL 17 with pgvector extension for Signal pipeline and vault RAG
    image: docker.io/pgvector/pgvector:pg17
    container_name: postgres-voice
    restart: unless-stopped
    ports:
      # OPTIONAL -- change host port if 5432 conflicts
      - "5432:5432"
    environment:
      # USER INPUT REQUIRED -- name for the default database
      POSTGRES_DB: stmna_voice
      # USER INPUT REQUIRED -- database username
      POSTGRES_USER: voice
      # USER INPUT REQUIRED -- generate a strong password (openssl rand -hex 16)
      POSTGRES_PASSWORD: YOUR_PASSWORD_HERE
    volumes:
      # NO ACTION NEEDED -- persistent data storage
      - /home/stmna/data/postgres:/var/lib/postgresql/data
    networks:
      - default
      - stmna-net

networks:
  default: {}
  stmna-net:
    external: true
```

> **Required:** Set `POSTGRES_PASSWORD` to a strong password. Generate one with `openssl rand -hex 16`. Save this password -- you will need it for Open WebUI and n8n credential configuration.

After deploying, create the Signal pipeline database and enable PGVector:

```bash
podman exec postgres-voice psql -U voice -d stmna_voice -c "CREATE DATABASE stmna_signal OWNER voice;"
podman exec postgres-voice psql -U voice -d stmna_signal -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Expected result:**

```
CREATE DATABASE
CREATE EXTENSION
```

Verify PostgreSQL is accepting connections:

```bash
podman exec postgres-voice pg_isready
```

**Expected result:**

```
/var/run/postgresql:5432 - accepting connections
```

---

## Step 5: llama-swap (LLM Reverse Proxy)

*Documented from production reference. Not staging-validated for inference.*

llama-swap routes LLM requests to the right model, manages VRAM, and hot-swaps models on demand. It wraps llama.cpp and exposes an OpenAI-compatible API.

In Dockge, create a new stack named `llama-swap`:

```yaml
# ============================================================
# STMNA Desk -- llama-swap (LLM Reverse Proxy)
# Part of: stmna-desk install guide, Step 5 (Core)
# Requires: stmna-net network, GPU (Vulkan)
# ============================================================

x-podman:
  in_pod: false

services:
  llama-swap:
    # INFO: Routes LLM requests to the right model, manages VRAM, hot-swaps on demand
    image: ghcr.io/mostlygeek/llama-swap:vulkan
    container_name: llama-swap
    restart: always
    ports:
      # OPTIONAL -- main proxy port (other services connect here)
      - "8081:8080"
      # OPTIONAL -- additional ports for direct model access
      - "9001:9001"
      - "9002:9002"
    volumes:
      # USER INPUT REQUIRED -- path to your downloaded GGUF models
      - /home/stmna/models:/models
      # NO ACTION NEEDED -- llama-swap configuration file
      - ./config.yaml:/app/config.yaml
    # NOTE -- GPU passthrough (requires Vulkan drivers on host)
    devices:
      - /dev/dri:/dev/dri
    group_add:
      - video
    security_opt:
      - seccomp=unconfined
    networks:
      - default
      - stmna-net

networks:
  default: {}
  stmna-net:
    external: true
```

> **Required:** Download at least one GGUF model to `/home/stmna/models/` before deploying. See the [inference stack reference](inference-stack.md) for recommended models.

> **Required:** Create a `config.yaml` in your llama-swap stack directory (`~/stacks/llama-swap/config.yaml`). Example minimal config:

```yaml
# llama-swap config.yaml -- minimal example with one model
# See https://github.com/mostlygeek/llama-swap for full documentation
healthCheckTimeout: 300
models:
  # USER INPUT REQUIRED -- model name (clients request this name)
  my-model:
    # USER INPUT REQUIRED -- path to your GGUF file in /models/
    cmd: /app/llama-server -m /models/YOUR_MODEL.gguf --host 0.0.0.0 --port 9001 -ngl 99 -fa on --no-mmap -c 32768
    proxy: http://127.0.0.1:9001

groups:
  # Models in the same group share a port and are swapped on demand (only one active at a time)
  default:
    swap: true
    exclusive: true
    members:
    - my-model
```

> Each model entry specifies a `cmd` (llama-server command line) and a `proxy` (where to forward requests). Models in the same group share resources -- llama-swap unloads one before loading another. Key flags: `-ngl 99` (GPU layers), `-fa on` (flash attention), `-c 32768` (context length).

> **Note:** The `devices`, `group_add`, and `security_opt` entries are required for GPU passthrough via Vulkan. If you do not have a GPU, remove these lines, but LLM inference will not work.

Verify:

```bash
curl -s http://localhost:8081/v1/models
```

**Expected result:** A JSON response listing your configured models.

---

## Step 6: Open WebUI (Chat Interface)

Open WebUI provides a web-based chat interface for interacting with your local LLMs via llama-swap.

In Dockge, create a new stack named `open-webui`:

```yaml
# ============================================================
# STMNA Desk -- Open WebUI
# Part of: stmna-desk install guide, Step 6 (Core)
# Requires: stmna-net network, llama-swap running, PostgreSQL running
# ============================================================

x-podman:
  in_pod: false

services:
  open-webui:
    # INFO: Chat UI for interacting with local LLMs via llama-swap
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: always
    ports:
      # OPTIONAL -- change host port if 3000 conflicts
      - "3000:8080"
    volumes:
      # NO ACTION NEEDED -- persistent settings, chat history, uploaded files
      - /home/stmna/data/open-webui:/app/backend/data
    environment:
      # USER INPUT REQUIRED -- llama-swap API endpoint (use your server IP or container hostname)
      - OPENAI_API_BASE_URL=http://llama-swap:8080/v1
      # NO ACTION NEEDED -- llama-swap does not require a real key
      - OPENAI_API_KEY=sk-none
      # OPTIONAL -- set to false to disable login (single-user mode)
      - WEBUI_AUTH=true
      # NO ACTION NEEDED -- uses PGVector for RAG document storage
      - VECTOR_DB=pgvector
      # USER INPUT REQUIRED -- PostgreSQL connection string (update password to match your postgres setup)
      - PGVECTOR_DB_URL=postgresql://voice:YOUR_POSTGRES_PASSWORD@postgres-voice:5432/stmna_signal
    networks:
      - default
      - stmna-net

networks:
  default: {}
  stmna-net:
    external: true
```

> **Required:** Update the PostgreSQL password in `PGVECTOR_DB_URL` to match the password you set in Step 4.

> **Note:** The `stmna_signal` database must exist before deploying Open WebUI. If you skipped the database creation step in Step 4, Open WebUI will fail to start. See Troubleshooting below.

**Expected result:** Open WebUI is accessible at `http://YOUR_IP:3000`. On first visit, create an admin account.

At this point, your Core tier is complete. You can chat with local LLMs through Open WebUI. If you only need chat + inference, you can stop here.

---

# Automation Tier (Steps 7-8)

> Required for running STMNA Signal or STMNA Voice products. Adds workflow automation and speech-to-text.

---

## Step 7: n8n (Workflow Automation)

n8n is the automation engine that runs Signal and Voice workflows. STMNA uses a custom image that adds ffmpeg, yt-dlp, pandoc, and python3 for media processing.

### Build the custom n8n image

```bash
mkdir -p ~/docker/n8n
```

Copy the Dockerfile from the [stmna-desk repo](https://f.slowdawn.cc/stmna-io/stmna-desk/src/branch/main/docker/n8n/Dockerfile) into `~/docker/n8n/Dockerfile`, then build:

```bash
cd ~/docker/n8n
podman build -t stmna-n8n:latest .
```

**Expected result:** Build completes with `Successfully tagged localhost/stmna-n8n:latest`.

Verify all tools are available:

```bash
podman run --rm --entrypoint /usr/bin/ffmpeg stmna-n8n:latest -version 2>&1 | head -1
podman run --rm --entrypoint /usr/local/bin/yt-dlp stmna-n8n:latest --version
podman run --rm --entrypoint /usr/bin/pandoc stmna-n8n:latest --version 2>&1 | head -1
podman run --rm --entrypoint /usr/bin/python3 stmna-n8n:latest --version
```

**Expected result:**

```
ffmpeg version 7.0.2-static ...
2026.03.03
pandoc 3.6.4
Python 3.12.13
```

### Fix data directory permissions

Before deploying n8n, fix the data directory ownership for rootless Podman:

```bash
mkdir -p ~/data/n8n
podman unshare chown -R 1000:1000 ~/data/n8n
```

> **Note:** This is required because n8n runs as user `node` (UID 1000 inside the container). In rootless Podman, UIDs are remapped. Without this step, n8n will fail with `EACCES: permission denied, open '/home/node/.n8n/config'`.

### Deploy n8n

In Dockge, create a new stack named `n8n`:

```yaml
# ============================================================
# STMNA Desk -- n8n Workflow Automation
# Part of: stmna-desk install guide, Step 7 (Automation)
# Requires: stmna-net network, PostgreSQL running, custom n8n image built
# ============================================================

x-podman:
  in_pod: false

services:
  n8n:
    # INFO: Custom image with ffmpeg, yt-dlp, pandoc, python3 for Signal workflows
    # Build first: cd ~/docker/n8n && podman build -t stmna-n8n:latest .
    image: localhost/stmna-n8n:latest
    container_name: n8n
    restart: always
    ports:
      # OPTIONAL -- change host port if 5678 conflicts
      - "5678:5678"
    environment:
      # NO ACTION NEEDED -- n8n server config
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      # USER INPUT REQUIRED -- your public URL or local IP for webhooks
      - WEBHOOK_URL=http://YOUR_IP:5678/
      # NO ACTION NEEDED -- allows Code nodes to use filesystem and subprocess
      - NODE_FUNCTION_ALLOW_BUILTIN=fs,child_process,path
      # OPTIONAL -- your timezone (default: UTC)
      - GENERIC_TIMEZONE=Europe/Amsterdam
      # NO ACTION NEEDED -- required for some workflow operations
      - N8N_EXECUTE_COMMAND_ENABLED=true
      # NO ACTION NEEDED -- extended timeouts for long-running tasks (book translation)
      - N8N_RUNNERS_HEARTBEAT_INTERVAL=1800
      - N8N_RUNNERS_TASK_TIMEOUT=43200
      - EXECUTIONS_TIMEOUT=-1
      # NO ACTION NEEDED -- disable secure cookie for HTTP access (set to true if using HTTPS)
      - N8N_SECURE_COOKIE=false
    volumes:
      # NO ACTION NEEDED -- persistent n8n data (workflows, credentials, settings)
      - /home/stmna/data/n8n:/home/node/.n8n
      # OPTIONAL -- mount a directory for Signal pipeline output (vault notes, exports)
      # Required if using STMNA Signal to write processed notes
      # - /path/to/your/output/directory:/vault
    networks:
      - default
      - stmna-net

networks:
  default: {}
  stmna-net:
    external: true
```

> **Required:** Set `WEBHOOK_URL` to your server's IP or domain. For local network access: `http://YOUR_IP:5678/`. For public access with HTTPS: `https://n8n.yourdomain.com/`.

> **Note:** Set `N8N_SECURE_COOKIE=true` once you have HTTPS configured via the [remote access guide](remote-access.md).

**Expected result:** n8n is accessible at `http://YOUR_IP:5678`. On first visit, create an admin account.

Verify:

```bash
curl -s http://localhost:5678/healthz
```

**Expected result:**

```json
{"status":"ok"}
```

---

## Step 8: Whisper Server (Speech-to-Text)

*Documented from production reference. Not staging-validated for transcription.*

The Whisper server provides speech-to-text transcription via an OpenAI-compatible API. The STMNA stack runs two instances: one for short voice clips (Voice product) and one for long recordings (Signal pipeline).

In Dockge, create a new stack named `whisper`:

```yaml
# ============================================================
# STMNA Desk -- Whisper Server (Speech-to-Text)
# Part of: stmna-desk install guide, Step 8 (Automation)
# Requires: stmna-net network, GPU (Vulkan)
# ============================================================

x-podman:
  in_pod: false

services:
  whisper-voice:
    # INFO: Dedicated whisper instance for STMNA_Voice (short clips, low latency)
    image: ghcr.io/ggml-org/whisper.cpp:main-vulkan
    container_name: whisper-voice
    restart: always
    read_only: true
    init: true
    ports:
      # OPTIONAL -- change if 8083 conflicts
      - "8083:8083"
    devices:
      - /dev/dri:/dev/dri
    tmpfs:
      - /root/.cache/mesa_shader_cache
      - /app
    volumes:
      # USER INPUT REQUIRED -- path to whisper model files
      - /home/stmna/models:/models:ro
    command:
      - whisper-server
      - "-m"
      - "/models/ggml-large-v3-turbo-q5_0.bin"
      - "--host"
      - "0.0.0.0"
      - "--port"
      - "8083"
      - "--inference-path"
      - "/v1/audio/transcriptions"
      - "--convert"
      - "-t"
      - "4"
      - "-fa"
    networks:
      - default
      - stmna-net

  whisper-signal:
    # INFO: Dedicated whisper instance for STMNA_Signal (long YouTube/podcast transcription)
    image: ghcr.io/ggml-org/whisper.cpp:main-vulkan
    container_name: whisper-signal
    restart: always
    read_only: true
    init: true
    ports:
      # OPTIONAL -- change if 8084 conflicts
      - "8084:8084"
    devices:
      - /dev/dri:/dev/dri
    tmpfs:
      - /root/.cache/mesa_shader_cache
      - /app
    volumes:
      - /home/stmna/models:/models:ro
    command:
      - whisper-server
      - "-m"
      - "/models/ggml-large-v3-turbo-q5_0.bin"
      - "--host"
      - "0.0.0.0"
      - "--port"
      - "8084"
      - "--inference-path"
      - "/v1/audio/transcriptions"
      - "--convert"
      - "-t"
      - "4"
      - "-fa"
    networks:
      - default
      - stmna-net

networks:
  default: {}
  stmna-net:
    external: true
```

> **Required:** Download the Whisper model to your models directory before deploying: `ggml-large-v3-turbo-q5_0.bin` (recommended). Available from the [whisper.cpp models page](https://huggingface.co/ggerganov/whisper.cpp/tree/main).

> **Optional:** If you only need one Whisper instance, remove the `whisper-signal` service. The Voice product uses `whisper-voice` on port 8083.

---

# Extended Tier (Steps 9-12)

> Optional services. Install what you need: vault RAG search, audio summaries, git hosting, AI agent.

---

## Step 9: TEI (Text Embeddings)

TEI serves embedding vectors for vault RAG search. It is used by n8n (vault search), Open WebUI (document RAG), and Agent Zero (knowledge base).

In Dockge, create a new stack named `text-embeddings`:

```yaml
# ============================================================
# STMNA Desk -- Text Embeddings Inference (TEI)
# Part of: stmna-desk install guide, Step 9 (Extended)
# Requires: stmna-net network
# ============================================================

x-podman:
  in_pod: false

services:
  text-embeddings:
    # INFO: Serves embedding vectors for vault RAG search (used by n8n, Open WebUI, Agent Zero)
    image: ghcr.io/huggingface/text-embeddings-inference:cpu-1.9
    container_name: text-embeddings
    restart: always
    ports:
      # OPTIONAL -- change host port if 9003 conflicts
      - "9003:80"
    volumes:
      # NO ACTION NEEDED -- model cache directory
      - /home/stmna/data/tei:/data
    environment:
      # OPTIONAL -- embedding model (1024 dims, ~43ms/query on CPU)
      - MODEL_ID=perplexity-ai/pplx-embed-context-v1-0.6b
      # NO ACTION NEEDED
      - DTYPE=float32
      # OPTIONAL -- batch token budget. Default 16384 needs ~16GB RAM for attention buffers.
      # Reduce to 512 on machines with 8GB or less RAM.
      - MAX_BATCH_TOKENS=16384
      # OPTIONAL -- increase for batch workloads (default: 32)
      - MAX_CLIENT_BATCH_SIZE=128
    networks:
      - stmna-net

networks:
  stmna-net:
    external: true
```

> **Note:** On first deploy, TEI will download the model (~1.2GB). This takes 1-2 minutes.

> **Note:** If TEI crashes with an out-of-memory error, reduce `MAX_BATCH_TOKENS` to `512` or `1024`. See Troubleshooting below.

Verify:

```bash
curl -s http://localhost:9003/embed -X POST \
  -H "Content-Type: application/json" \
  -d '{"inputs": "test embedding"}'
```

**Expected result:** A JSON array of floating-point numbers (the embedding vector).

---

## Step 10: Kokoro TTS (Text-to-Speech)

Kokoro provides text-to-speech via an OpenAI-compatible API. The Signal Worker uses it to generate audio summaries.

In Dockge, create a new stack named `kokoro-tts`:

```yaml
# ============================================================
# STMNA Desk -- Kokoro TTS
# Part of: stmna-desk install guide, Step 10 (Extended)
# Requires: stmna-net network
# ============================================================

x-podman:
  in_pod: false

services:
  kokoro-tts:
    # INFO: Text-to-speech engine (OpenAI-compatible API). Called by Signal Worker via HTTP.
    image: ghcr.io/remsky/kokoro-fastapi-cpu:v0.2.4
    container_name: kokoro-tts
    restart: always
    ports:
      # OPTIONAL -- change host port if 9005 conflicts
      - "9005:8880"
    environment:
      # NO ACTION NEEDED
      - USE_GPU=false
      - DEVICE_TYPE=cpu
      - API_LOG_LEVEL=INFO
      - DISABLE_LOCAL_SAVING=true
      # OPTIONAL -- default voice (af_heart=English Grade A+, ff_siwis=French Grade B-)
      - DEFAULT_VOICE=af_heart
    networks:
      - stmna-net

networks:
  stmna-net:
    external: true
```

> **Note:** Models are baked into the image. No external model download needed.

Verify:

```bash
curl -s http://localhost:9005/v1/audio/voices | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), indent=2)[:200])"
```

**Expected result:** A JSON list of available voices.

---

## Step 11: Forgejo (Git Hosting)

Forgejo is a self-hosted git forge. Use it to host your vault repository (for the embedding pipeline webhook), workflow exports, and source code.

In Dockge, create a new stack named `forgejo`:

```yaml
# ============================================================
# STMNA Desk -- Forgejo (Self-Hosted Git)
# Part of: stmna-desk install guide, Step 11 (Extended)
# Requires: stmna-net network
# ============================================================

x-podman:
  in_pod: false

services:
  forgejo:
    # INFO: Self-hosted git forge for vault repos, workflow exports, source code
    image: codeberg.org/forgejo/forgejo:10
    container_name: forgejo
    restart: always
    ports:
      # OPTIONAL -- HTTP web UI (avoid conflict with Open WebUI on 3000)
      - "3300:3000"
      # OPTIONAL -- SSH for git over SSH (remove if not needed)
      - "2222:22"
    volumes:
      # NO ACTION NEEDED -- persistent data (repos, config, database)
      - /home/stmna/data/forgejo:/data
    environment:
      # NO ACTION NEEDED -- Forgejo runs as UID 1000 inside the container
      - USER_UID=1000
      - USER_GID=1000
      # USER INPUT REQUIRED -- your server's domain or IP for clone URLs
      - FORGEJO__server__ROOT_URL=http://YOUR_IP:3300/
      # NO ACTION NEEDED -- use built-in SQLite (sufficient for single-user/small-team)
      - FORGEJO__database__DB_TYPE=sqlite3
      # OPTIONAL -- disable registration after creating your admin account
      # - FORGEJO__service__DISABLE_REGISTRATION=true
    networks:
      - default
      - stmna-net

networks:
  default: {}
  stmna-net:
    external: true
```

> **Required:** Set `FORGEJO__server__ROOT_URL` to your server's IP or domain (e.g., `http://10.0.10.54:3300/` or `https://git.yourdomain.com/`). This controls clone URLs displayed in the web UI.

> **Optional:** After creating your admin account on first visit, set `FORGEJO__service__DISABLE_REGISTRATION=true` to prevent public signups.

> **Optional:** Remove the SSH port mapping (`2222:22`) if you only need HTTPS git access.

**Expected result:** Forgejo is accessible at `http://YOUR_IP:3300`. On first visit, complete the installation wizard and create an admin account.

Verify:

```bash
curl -s http://localhost:3300/api/v1/version
```

**Expected result:** A JSON response with the Forgejo version (e.g., `{"version":"10.0.0"}`).

### Configure webhook for vault embedding pipeline

If you use the vault embedding pipeline (see [vault-embedding workflow](../workflows/vault-embedding.json)):

1. Create a repository for your vault in Forgejo
2. Go to the repo Settings > Webhooks > Add Webhook > Forgejo
3. Set the target URL to `http://n8n:5678/webhook/vault-embedding` (uses container network)
4. Set the secret to match the webhook secret in your n8n workflow
5. Select "Push Events" only

---

## Step 12: Agent Zero (AI Agent)

Agent Zero is an autonomous AI agent with memory, tools, and code execution. It connects to llama-swap for LLM inference and TEI for embeddings.

In Dockge, create a new stack named `agent-zero`:

```yaml
# ============================================================
# STMNA Desk -- Agent Zero (AI Agent)
# Part of: stmna-desk install guide, Step 12 (Extended)
# Requires: stmna-net network, llama-swap running, TEI running
# ============================================================

x-podman:
  in_pod: false

services:
  agent-zero:
    # INFO: Autonomous AI agent with memory, tools, and code execution
    image: docker.io/agent0ai/agent-zero:latest
    container_name: agent-zero
    restart: unless-stopped
    ports:
      # OPTIONAL -- change host port if 50001 conflicts
      - "50001:80"
    volumes:
      # NO ACTION NEEDED -- persistent user data
      - ./usr:/a0/usr
      - ./agents:/a0/agents
      - ./work_dir:/a0/work_dir
      - ./knowledge:/a0/knowledge
      - ./logs:/a0/logs
    environment:
      # USER INPUT REQUIRED -- chat model (must match a model in your llama-swap config)
      - A0_SET_chat_model_provider=openai
      - A0_SET_chat_model_name=qwen3.5-35b-nothink
      - A0_SET_chat_model_api_base=http://llama-swap:8080/v1
      - A0_SET_chat_model_ctx_length=65536
      # USER INPUT REQUIRED -- utility model
      - A0_SET_util_model_provider=openai
      - A0_SET_util_model_name=qwen3.5-35b-nothink
      - A0_SET_util_model_api_base=http://llama-swap:8080/v1
      - A0_SET_util_model_ctx_length=65536
      # USER INPUT REQUIRED -- embedding model (TEI container)
      - A0_SET_embed_model_provider=openai
      - A0_SET_embed_model_name=openai/pplx-embed-context-v1-0.6b
      - A0_SET_embed_model_api_base=http://text-embeddings:80/v1
      # USER INPUT REQUIRED -- browser/vision model
      - A0_SET_browser_model_provider=openai
      - A0_SET_browser_model_name=qwen3.5-35b-nothink
      - A0_SET_browser_model_api_base=http://llama-swap:8080/v1
      - A0_SET_browser_model_ctx_length=65536
      # NO ACTION NEEDED -- llama-swap does not require a real key
      - API_KEY_OPENAI=sk-not-needed
    networks:
      - stmna-net

networks:
  stmna-net:
    external: true
```

> **Required:** Update the model names to match models configured in your llama-swap `config.yaml`.

> **Note:** The `openai/` prefix on the embedding model name is required. Agent Zero uses LiteLLM internally, which strips the prefix before calling TEI.

**Expected result:** Agent Zero is accessible at `http://YOUR_IP:50001`.

---

## Step 13: Crawl4AI (Web Scraping)

Crawl4AI provides a web scraping API used by the Signal Worker to extract content from web articles. Required for the Signal pipeline's web content type.

In Dockge, create a new stack named `crawl4ai`:

```yaml
# ============================================================
# STMNA Desk -- Crawl4AI (Web Scraping)
# Part of: stmna-desk install guide, Step 13 (Extended)
# Requires: stmna-net network
# ============================================================

x-podman:
  in_pod: false

services:
  crawl4ai:
    # INFO: Web scraping API for extracting article content (used by Signal Worker)
    image: docker.io/unclecode/crawl4ai:latest
    container_name: crawl4ai
    restart: always
    ports:
      # OPTIONAL -- change host port if 11235 conflicts
      - "11235:11235"
    environment:
      # USER INPUT REQUIRED -- API token for authentication (generate with: openssl rand -hex 16)
      - CRAWL4AI_API_TOKEN=YOUR_TOKEN_HERE
      # OPTIONAL -- max concurrent scraping tasks
      - MAX_CONCURRENT_TASKS=5
      # NO ACTION NEEDED -- for LLM-based extraction (optional, not used by default)
      - OPENAI_API_KEY=sk-none
      - OPENAI_API_BASE=http://llama-swap:8080/v1
    volumes:
      # NO ACTION NEEDED -- persistent cache
      - /home/stmna/data/crawl4ai:/root/.crawl4ai
    networks:
      - default
      - stmna-net

networks:
  default: {}
  stmna-net:
    external: true
```

> **Required:** Set `CRAWL4AI_API_TOKEN` to a strong token. Save it -- the Signal Worker needs this token to authenticate scraping requests.

Verify:

```bash
curl -s http://localhost:11235/health
```

**Expected result:** A JSON response indicating the service is healthy.

---

## Step 14: SearXNG (Search Engine)

SearXNG is a privacy-respecting metasearch engine. The Signal Worker uses it for web search queries. Optional but recommended.

In Dockge, create a new stack named `searxng`:

```yaml
# ============================================================
# STMNA Desk -- SearXNG (Search Engine)
# Part of: stmna-desk install guide, Step 14 (Extended)
# ============================================================
# NOTE: SearXNG is not on stmna-net because it does not need
# to be reached by other containers. n8n calls it via host port.

x-podman:
  in_pod: false

services:
  searxng:
    # INFO: Privacy-respecting metasearch engine
    image: docker.io/searxng/searxng:latest
    container_name: searxng
    restart: always
    ports:
      # OPTIONAL -- change host port if 8888 conflicts
      - "8888:8080"
    volumes:
      # NO ACTION NEEDED -- persistent settings
      - /home/stmna/data/searxng:/etc/searxng:rw
    environment:
      # USER INPUT REQUIRED -- your server's IP or domain
      - SEARXNG_BASE_URL=http://YOUR_IP:8888/
      # USER INPUT REQUIRED -- generate a secret (openssl rand -hex 16)
      # NOTE -- literal $ signs must be doubled ($$) in compose files
      - SEARXNG_SECRET=YOUR_SECRET_HERE
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID

networks: {}
```

> **Note:** SearXNG uses port 8888 on the host (mapped from container port 8080) to avoid conflicts with other services on port 8080.

> **Note:** If your `SEARXNG_SECRET` contains `$` characters, double them (`$$`) in the compose file. Docker/Podman Compose interprets `$` as variable substitution.

Verify:

```bash
curl -s http://localhost:8888/ | head -5
```

**Expected result:** HTML content from the SearXNG search page.

---

## Verification

After deploying, verify your containers are running. The expected output depends on which tiers you installed.

```bash
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Core tier (Steps 1-6) -- 4 containers

```
NAMES            STATUS                  PORTS
dockge           Up X minutes            0.0.0.0:5001->5001/tcp
postgres-voice   Up X minutes            0.0.0.0:5432->5432/tcp
llama-swap       Up X minutes (healthy)  0.0.0.0:8081->8080/tcp
open-webui       Up X minutes            0.0.0.0:3000->8080/tcp
```

### + Automation tier (Steps 7-8) -- 7 containers

```
NAMES            STATUS                  PORTS
...core containers above...
n8n              Up X minutes            0.0.0.0:5678->5678/tcp
whisper-voice    Up X minutes            0.0.0.0:8083->8083/tcp
whisper-signal   Up X minutes            0.0.0.0:8084->8084/tcp
```

### + Extended tier (Steps 9-14) -- up to 13 containers

```
NAMES            STATUS                  PORTS
...core + automation containers above...
text-embeddings  Up X minutes            0.0.0.0:9003->80/tcp
kokoro-tts       Up X minutes            0.0.0.0:9005->8880/tcp
forgejo          Up X minutes            0.0.0.0:3300->3000/tcp
agent-zero       Up X minutes            0.0.0.0:50001->80/tcp
crawl4ai         Up X minutes            0.0.0.0:11235->11235/tcp
searxng          Up X minutes            0.0.0.0:8888->8080/tcp
```

### Port map

| Service | Port | Tier | Protocol | Access |
|---------|------|------|----------|--------|
| Dockge | 5001 | Core | HTTP | LAN only |
| PostgreSQL | 5432 | Core | TCP | LAN only (never expose publicly) |
| llama-swap | 8081 | Core | HTTP | LAN or Tailscale |
| Open WebUI | 3000 | Core | HTTP | LAN or Tailscale |
| n8n | 5678 | Automation | HTTP | LAN or public (webhooks need public access) |
| Whisper (Voice) | 8083 | Automation | HTTP | LAN or Tailscale |
| Whisper (Signal) | 8084 | Automation | HTTP | LAN or Tailscale |
| TEI | 9003 | Extended | HTTP | Internal (container network) |
| Kokoro TTS | 9005 | Extended | HTTP | Internal (container network) |
| Forgejo | 3300 | Extended | HTTP | LAN or Tailscale |
| Agent Zero | 50001 | Extended | HTTP | LAN only |
| Crawl4AI | 11235 | Extended | HTTP | Internal (container network) |
| SearXNG | 8888 | Extended | HTTP | LAN only |

---

## Smoke Test

### TEI embedding test

```bash
curl -s http://localhost:9003/embed -X POST \
  -H "Content-Type: application/json" \
  -d '{"inputs": "STMNA Desk is running"}' | python3 -c "import json,sys; v=json.load(sys.stdin)[0]; print(f'Embedding dims: {len(v)}, first 3: {v[:3]}')"
```

**Expected result:** `Embedding dims: 1024, first 3: [0.015..., ...]`

### n8n health check

```bash
curl -s http://localhost:5678/healthz
```

**Expected result:** `{"status":"ok"}`

### Kokoro TTS voice list

```bash
curl -s http://localhost:9005/v1/audio/voices | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Available voices: {len(d)}')"
```

**Expected result:** `Available voices: N` (where N > 0)

---

## Troubleshooting

### n8n: `EACCES: permission denied, open '/home/node/.n8n/config'`

**Cause:** Rootless Podman UID remapping. The n8n container runs as user `node` (UID 1000 inside), but the mounted data directory is owned by the host user. Rootless Podman remaps UIDs, causing a mismatch.

**Fix:**

```bash
podman stop n8n
podman unshare chown -R 1000:1000 ~/data/n8n
```

Then restart n8n through Dockge.

### n8n: "Your n8n server is configured to use a secure cookie"

**Cause:** n8n requires HTTPS by default for cookies. When accessing via HTTP (local network), this blocks the setup page.

**Fix:** Add `N8N_SECURE_COOKIE=false` to the n8n environment variables. Set it back to `true` once HTTPS is configured.

### TEI: `Failed to allocate memory for requested buffer of size 17179869184`

**Cause:** `MAX_BATCH_TOKENS=16384` with `DTYPE=float32` requires ~16GB RAM for attention matrix allocation. Machines with 8GB or less RAM cannot allocate this buffer.

**Fix:** Reduce `MAX_BATCH_TOKENS` in the TEI compose file:

```yaml
- MAX_BATCH_TOKENS=512
```

Restart the stack through Dockge. TEI will work with reduced batch size -- individual queries are unaffected, only concurrent batch throughput is lower.

### Open WebUI: `FATAL: database "stmna_signal" does not exist`

**Cause:** The `stmna_signal` database was not created in PostgreSQL before Open WebUI tried to connect.

**Fix:** Create the database (see Step 4), then restart Open WebUI through Dockge:

```bash
podman exec postgres-voice psql -U voice -d stmna_voice -c "CREATE DATABASE stmna_signal OWNER voice;"
podman exec postgres-voice psql -U voice -d stmna_signal -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### n8n deprecation: `N8N_RUNNERS_ENABLED -> Remove this environment variable`

**Cause:** n8n 2.9.0 enables the JS task runner by default. The `N8N_RUNNERS_ENABLED` environment variable is no longer needed.

**Fix:** Remove `N8N_RUNNERS_ENABLED=true` from the n8n compose file. This is a warning only -- n8n still works.

### podman-compose: "executable file not found in $PATH"

**Cause:** pipx installs binaries to `~/.local/bin/`, which may not be in your PATH.

**Fix:**

```bash
pipx ensurepath
source ~/.bashrc
```

Or open a new terminal session.

---

## What's Next

- [Signal install guide](https://f.slowdawn.cc/stmna-io/stmna-signal/src/branch/main/docs/install-guide.md) -- add the Signal content pipeline
- [Voice install guide](https://f.slowdawn.cc/stmna-io/stmna-voice/src/branch/main/docs/install-guide.md) -- add voice transcription
- [Remote access guide](remote-access.md) -- set up remote access via Tailscale + Caddy reverse proxy
