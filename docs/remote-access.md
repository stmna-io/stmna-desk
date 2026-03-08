# Remote Access

Running AI services on a local machine means they're only reachable on your LAN by default.
To use products like STMNA Signal (which receives webhooks from Signal)
or STMNA Voice (which accepts API calls from mobile devices),
your services need to be reachable from the internet over HTTPS.

## Options

| Approach | Complexity | Sovereignty | Best For |
|----------|-----------|-------------|----------|
| Cloudflare Tunnels | Low | Medium — traffic routes through Cloudflare | Quick setup, free tier available |
| Tailscale Funnel | Low | Medium — traffic routes through Tailscale | Already using Tailscale for device mesh |
| VPS + Reverse Proxy | Medium | High — you control the entire path | Production deployments, custom domains |

### Cloudflare Tunnels
Install `cloudflared` on your machine, create a tunnel, point it at your local service ports.
Cloudflare handles DNS, TLS certificates, and proxying. Free tier supports most use cases.
Docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/

### Tailscale Funnel
If you already use Tailscale for device-to-device access, Funnel exposes a local port
to the internet via Tailscale's infrastructure. Simple but limited: Tailscale controls
the domain name and there are bandwidth caps on free tier.
Docs: https://tailscale.com/kb/1223/funnel

### VPS + Reverse Proxy
Run a lightweight VPS with a reverse proxy (Caddy or Nginx) that terminates HTTPS
and forwards traffic to your machine through a VPN tunnel. Full control over domains,
certificates, and routing. More setup, but the most flexible and sovereign option.

STMNA Desk uses the VPS + reverse proxy approach.

## What You Need

At minimum, your remote access solution must provide:
- HTTPS with valid TLS certificates (webhooks from Signal and other services require HTTPS)
- Forwarding to specific local ports (each service runs on its own port)
- Reliability for always-on services (Signal messages arrive at any time)
