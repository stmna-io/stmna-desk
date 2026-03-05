# Remote Access

How to reach the Desk from anywhere. The short version: Tailscale handles device-to-device access, Caddy on a VPS handles public-facing endpoints. No SSH or admin ports are exposed to the internet.

---

## Network Architecture

```
+---------------------------------------------------+
|                    Internet                         |
+------------------------+--------------------------+
                         |
                +--------v--------+
                |    VPS (Caddy)  |
                |    Public IP    |
                |    HTTPS + TLS  |
                +--------+--------+
                         | Tailscale tunnel
                +--------v--------+
                |   STMNA Desk    |
                |   LAN: 10.x.x.x|
                |   TS: 100.x.x.x|
                +-----------------+
```

| Layer | What | Access Method |
|-------|------|--------------|
| LAN | Direct connection on home network | IP:port (no auth needed on most services) |
| Tailscale | Encrypted mesh VPN between your devices | Tailscale IP or MagicDNS hostname |
| Public (Caddy) | HTTPS endpoints for external services | Domain name + TLS, bearer token where needed |

The Desk has no ports open to the internet. All external access goes through either Tailscale (for admin/development) or Caddy on the VPS (for automated services like Signal webhooks and git push hooks).

---

## Tailscale Setup

### Device Registration

Add a new device to your Tailscale network:

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (opens browser)
sudo tailscale up

# Verify connection to Desk
tailscale ping desk
```

Once connected, your device can reach the Desk using its Tailscale IP or MagicDNS hostname.

### Accessing the Desk

```bash
# SSH via Tailscale (MagicDNS)
ssh stmna@desk

# SSH via Tailscale IP
ssh stmna@100.x.x.x

# SSH via LAN (when on the same network)
ssh stmna@10.x.x.x
```

The `stmna` user is an unprivileged account. It can manage all containers and services under `/home/stmna/` but cannot sudo, modify system config, or access other users. This is intentional. The user IS the sandbox.

### Accessing Services via Tailscale

Once on the Tailscale network, services are accessible by IP and port:

| Service | URL | Port |
|---------|-----|------|
| Open WebUI | `http://desk:3000` | 3000 |
| n8n | `http://desk:5678` | 5678 |
| Dockge | `http://desk:5001` | 5001 |
| Agent Zero | `http://desk:50001` | 50001 |
| llama-swap API | `http://desk:8081` | 8081 |
| Forgejo | `http://desk:3300` | 3300 |
| NextCloud | `http://desk:8090` | 8090 |
| SearXNG | `http://desk:8888` | 8888 |

Replace `desk` with your Tailscale MagicDNS hostname or IP.

### What Stays LAN-Only

Some services should generally only be accessed from the local network or via SSH, not directly over Tailscale:

| Service | Port | Reason |
|---------|------|--------|
| PostgreSQL | 5432 | Database access should go through application layers, not direct connections |
| llama-swap (direct) | 8081 | Safe to access, but model loading takes resources. Use via Open WebUI or n8n for normal work. |
| whisper.cpp | 8083/8084 | Internal services consumed by n8n workflows |
| TEI | 9003 | Internal embedding service |
| Kokoro TTS | 9005 | Internal TTS service |

These services are reachable over Tailscale (nothing blocks them), but there's no reason to access them directly under normal operation.

---

## Public Endpoints (via Caddy + VPS)

The VPS runs Caddy as a reverse proxy, terminating HTTPS and forwarding requests to the Desk through the Tailscale tunnel.

| Service | Public URL Pattern | Purpose |
|---------|-------------------|---------|
| Signal API | `signal.yourdomain.com` | Receiving Signal messages from the signal-cli-rest-api |
| Voice API | `stv.yourdomain.com` | Voice transcription endpoint (OpenAI-compatible) |
| Forgejo | `git.yourdomain.com` | Git hosting, webhook source for vault sync |
| NextCloud | `cloud.yourdomain.com` | File access, audio delivery |
| n8n | `n8n.yourdomain.com` | Workflow automation UI and webhook endpoints |

Caddy handles TLS certificate provisioning automatically via Let's Encrypt. No manual certificate management.

The Caddy configuration lives on the VPS, not in this repo. A typical Caddyfile entry:

```
n8n.yourdomain.com {
    reverse_proxy desk-tailscale-ip:5678
}

stv.yourdomain.com {
    reverse_proxy desk-tailscale-ip:5678 {
        header_up Host {upstream_hostport}
    }
    rewrite /v1/audio/transcriptions /webhook/transcribe
}
```

---

## SSH Key Patterns

### Persistent Key (for automation)

For tools like Claude Code that need repeated SSH access:

```bash
# Connect with a mounted key
ssh -i ~/.ssh/stmna_desk \
    -o IdentitiesOnly=yes \
    -o UserKnownHostsFile=/dev/null \
    -o StrictHostKeyChecking=no \
    stmna@desk
```

The flags matter:
- `IdentitiesOnly=yes` prevents leaking other SSH keys from the agent
- `UserKnownHostsFile=/dev/null` avoids write permission issues on read-only `.ssh/` mounts
- `StrictHostKeyChecking=no` skips the host key prompt for automation

### Temporary Key (for one-off sessions)

For a collaborator or tool that needs temporary access:

```bash
# 1. Generate a temporary ed25519 key
ssh-keygen -t ed25519 -f /tmp/desk-temp -N ""

# 2. Add the public key to Desk authorized_keys (operator does this)
cat /tmp/desk-temp.pub >> ~/.ssh/authorized_keys  # on Desk

# 3. Connect
ssh -i /tmp/desk-temp stmna@desk

# 4. After the session, remove the key (operator does this)
# Edit ~/.ssh/authorized_keys on Desk, remove the temporary key line
```

---

## Security Notes

**No public SSH.** SSH is only reachable via Tailscale or the LAN. There is no SSH port forwarded through the VPS.

**Rootless containers.** Every container runs under the unprivileged `stmna` user. Container escape lands in a user namespace with no path to root.

**Caddy handles TLS.** Automatic certificate provisioning and renewal. No expired certificates, no manual rotation.

**n8n API authentication.** The n8n API requires an API key (JWT token). Workflows that accept external input use webhook-specific authentication (bearer tokens, webhook secrets).

**Vault is read-only on Desk.** The Obsidian vault is mounted read-only in the n8n container. Writes go through the Vault Ops workflow, which commits to git. Direct filesystem writes to the vault on Desk are blocked to prevent ownership issues with rootless Podman.

---

*Last updated: 2026-03-04*
