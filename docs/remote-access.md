# Remote Access

<!-- TODO: Write full remote access guide for SB-05 session -->
<!-- Content: Headscale architecture (self-hosted VPN coordinator), Tailscale client config,
     Caddy reverse proxy setup, bearer token auth for public endpoints,
     VPS role (Caddy HTTPS termination, no services run there),
     recommended access patterns (LAN direct vs VPN vs public HTTPS) -->

## Placeholder

This document will cover:

- **Network architecture** — Desk (LAN) → VPS (Caddy HTTPS) → public internet
- **Headscale** — self-hosted Tailscale coordinator, why self-hosted
- **Tailscale clients** — laptop, mobile, team member setup
- **Caddy configuration** — bearer token auth, HTTPS termination on VPS
- **Public endpoints** — which services are exposed and how
- **Security model** — what's behind VPN-only vs publicly accessible
- **Access patterns**:
  - LAN: direct IP + port (no auth needed)
  - VPN: Tailscale IP (no auth needed)
  - Public: HTTPS + bearer token via Caddy

Coming in SB-05 session.
