# Architecture Overview

How the pieces of the STMNA_Desk stack connect and why they're structured this way. This is the map. The territory (configuration details, port assignments, model inventory) lives in the other docs in this directory.

For the system diagram, service table, and port assignments, see the [README](../README.md#architecture).

---

## Infrastructure Layer

The Desk runs all compute: inference, transcription, workflow execution, and database. Every AI workload stays on the machine. No processing is offloaded to external services.

By default, these services are only reachable on your local network. Products like STMNA_Signal (which receives webhooks) and STMNA_Voice (which accepts API calls from mobile devices) need HTTPS endpoints reachable from the internet. There are several ways to set that up, from zero-config tunnels to a full VPS with a reverse proxy. The [Remote Access doc](remote-access.md) covers three approaches at different points on the complexity/sovereignty spectrum.

## Orchestration Layer (n8n)

n8n handles all workflow automation. It was chosen over custom code because when a pipeline fails at step 14 of 20, the visual UI shows exactly where. Changing a prompt, adding a processing step, or rerouting content takes minutes in the workflow editor rather than a code deploy cycle. PostgreSQL, HTTP, webhooks, and file operations all have first-class n8n nodes, and the whole thing is one container to update rather than a custom application to maintain.

n8n runs in a custom container image with ffmpeg and yt-dlp baked in, built specifically to facilitate the deployment of STMNA_Signal and STMNA_Voice. For workflow specifics, see [STMNA_Signal](https://github.com/stmna-io/stmna-signal) and [STMNA_Voice](https://github.com/stmna-io/stmna-voice).

## Interface Layer

Three interfaces serve different interaction patterns:

- **Signal:** Mobile-first, async messaging. Dedicated input layer for [STMNA_Signal](https://github.com/stmna-io/stmna-signal)'s content processing pipeline: send a URL, get a structured note back minutes later.
- **Open WebUI:** Desktop chat interface for interactive conversations with Qwen models and SearXNG web search. Best suited for research and exploration.
- **Agent Zero:** Autonomous AI agent with tool use that can browse the web and execute multi-step tasks.

## Knowledge Layer

The knowledge store is a collection of markdown files in a Forgejo git repository. Content arrives via Signal, NextCloud, or direct webhook. n8n workflows extract, transcribe, summarize, and translate. The results are written as markdown notes in the vault.

Plain text means any file opens in any editor. Git means every change has a commit with full diff history. Webhooks mean other tools (n8n, LLM agents) interact with the vault through standard HTTP. And if you ever want to move to a different system, you just need to copy a folder.

The vault is the primary store, not any derived index. Semantic search can be added on top using embedding models and a vector database, but if that layer goes down, the vault is unaffected. Everything else (search indices, caching layers) is derived and expendable.

## Rootless Podman over Docker

All containers run under the `stmna` user (UID 1001) with rootless Podman, and sudo is not required for day-to-day operations.

Rootless Podman means a container escape lands you in an unprivileged user namespace, not root. There's no long-running root daemon managing containers. Each container is a child process of the user who started it. The same OCI container images work as with Docker. For a machine that runs untrusted workloads (web scraping, processing arbitrary URLs from Signal messages), this is a meaningful security improvement over Docker's daemon model.

The trade-off: some Docker-native tooling assumes a root daemon. Compose files need `x-podman: in_pod: false` to prevent automatic pod creation, which breaks cross-compose networking. Dockge only tracks containers it starts itself. None of these are blockers, but they need your attention during initial setup.

Each service lives in its own directory under `~/stacks/` with its own `compose.yaml`:

```
~/stacks/
  llama-swap/
    compose.yaml
    config.yaml
  n8n/
    compose.yaml
    Dockerfile
  postgres/
    compose.yaml
  whisper-server/
    compose.yaml
  ...
```

All services join the shared `stmna-net` Podman network for cross-compose communication. Containers reference each other by hostname (e.g., `http://llama-swap:8080`, `http://postgres-voice:5432`). See the [Inference Stack doc](inference-stack.md) for instructions on adding a new service to the stack.


---

## Related Docs

- [Hardware Guide](hardware-guide.md): Framework Desktop specs, why 128GB, power and thermals
- [Inference Stack](inference-stack.md): Model inventory, Vulkan/ROCm decision, deployment notes
- [Remote Access](remote-access.md): Options for exposing services over HTTPS

