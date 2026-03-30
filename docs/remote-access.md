# Remote Access

Running AI services on a local machine means they're only reachable on your LAN by default. Depending on your use case, you may need private access from your own devices or public access from the internet.

## Private Access (Device Mesh)

If you only need to reach your server from your own devices (laptops, phones, tablets), a mesh VPN is the simplest and most secure option. No ports are opened on your network. No services are exposed to the internet.

Install Tailscale on your server and on each client device. Devices join the same virtual network and can reach each other directly over WireGuard. Tailscale's coordination servers handle key exchange and NAT traversal only, they never see your traffic. The client is open source.

Your AI services stay on private Tailscale IPs with no public exposure. For private-only access, HTTPS is optional since WireGuard encryption covers the transport.

Tailscale docs: https://tailscale.com/kb/1017/install


## Public Access (Internet-Facing)

Products like [STMNA_Signal](https://github.com/stmna-io/stmna-signal) (which receives webhooks from Signal)
or [STMNA_Voice](https://github.com/stmna-io/stmna-voice) (which accepts API calls from mobile devices on the go) need HTTPS endpoints reachable from the public internet. External clients don't have VPN keys, so TLS must be terminated somewhere on their behalf.

| Approach | Complexity | Sovereignty | Security | Best For |
|----------|-----------|-------------|----------|----------|
| Managed tunnel (Cloudflare Tunnels, Tailscale Funnel) | Low | Medium (traffic routes through provider) | Provider terminates TLS for public clients, then forwards over encrypted tunnel to your machine. Provider can see decrypted payloads at their edge | Quick setup, free tier, no VPS needed |
| VPS + Reverse Proxy | Medium | High (you control the entire path) | You terminate TLS on your own VPS. Only machines you control see decrypted traffic | Production deployments, custom domains, full control |

### Managed Tunnels

Cloudflare Tunnels and Tailscale Funnel work the same way: install an agent on your machine, it connects outbound to the provider's edge, and the provider routes incoming HTTPS traffic back through the tunnel. You never open an inbound port on your network.

**Cloudflare Tunnels** give you custom domains and a generous free tier with no bandwidth restrictions.
Docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/

**Tailscale Funnel** is a natural fit if you already use Tailscale for private device access. Funnel is available on all plans including the free Personal tier. The limitations: Tailscale controls the domain name (yourhost.tailnet-name.ts.net, no custom domains), traffic is subject to undisclosed non-configurable bandwidth limits on all plans, and you can only expose ports 443, 8443, and 10000. Funnel is currently in beta.
Docs: https://tailscale.com/kb/1223/funnel

Both are solid options for getting started quickly. The trade-off is that your decrypted traffic passes through the provider's edge infrastructure, because public clients need someone to terminate TLS on their behalf.

### VPS + Reverse Proxy

Run a lightweight VPS with a reverse proxy (Caddy or Nginx) that terminates HTTPS and forwards traffic to your machine through a VPN tunnel. Full control over domains, certificates, and routing. More setup, but no third party sees your decrypted traffic.

For full sovereignty over the coordination layer as well, you can run [Headscale](https://github.com/juanfont/headscale) (an open-source Tailscale-compatible coordinator) on the VPS instead of using Tailscale's SaaS. The WireGuard mesh traffic remains end-to-end encrypted either way. Headscale just means you also control the key exchange and NAT traversal server.

We recommend the VPS + reverse proxy approach for STMNA_Desk.

## What You Need

At minimum, your public access solution must provide:
- HTTPS with valid TLS certificates (webhooks from Signal and other services require HTTPS)
- Forwarding to specific local ports (each service runs on its own port)
- Reliability for always-on services (Signal messages arrive at any time)

