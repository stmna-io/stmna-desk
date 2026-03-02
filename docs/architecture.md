# Architecture

<!-- TODO: Write full architecture guide for SB-05 session -->
<!-- Content: rootless Podman rationale, stmna-net bridge network, compose file structure,
     container topology diagram, service dependencies, startup sequence (systemd user service),
     cross-compose networking (n8n <-> postgres), volume mounts, user UID mapping -->

## Placeholder

This document will cover:

- **Rootless Podman** — why rootless, what it changes vs Docker
- **Container topology** — all services, ports, dependencies
- **stmna-net** — shared bridge network for cross-compose communication
- **Compose file structure** — one stack per directory under `~/stacks/`
- **Dockge** — container management UI, how to use it
- **Systemd user service** — auto-start on boot without root
- **Volume mounts** — data paths, model paths, vault mounts
- **UID mapping** — rootless Podman and file ownership gotchas
- **Service startup sequence** — order matters (postgres before n8n)

Coming in SB-05 session.
