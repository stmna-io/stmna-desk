#!/usr/bin/env python3
"""
Generate STMNA Desk architecture diagram as .excalidraw JSON.
Brand colors from 10-STMNA/13-Brand/Brand-Guidelines.md
"""
import json
import random
import math

# Brand colors
DEEP_NAVY = "#1A1A2E"
SLATE_BLUE = "#1A2238"
SLATE_MID = "#2D3A5C"
EMBER_ORANGE = "#FF8C42"
SOLAR_GOLD = "#FFD93D"
CLOUD_GRAY = "#8892A0"
ICE_WHITE = "#F8F9FA"
VOID_BLACK = "#0F0F1A"

# Element counter for unique IDs
_id_counter = 0

def make_id():
    global _id_counter
    _id_counter += 1
    return f"elem_{_id_counter:04d}"

def make_seed():
    return random.randint(100000, 999999999)

def rect(x, y, w, h, stroke="#000000", bg="transparent", fill="solid",
         stroke_w=2, roughness=0, opacity=100, rounded=True, stroke_style="solid"):
    """Create a rectangle element."""
    eid = make_id()
    return {
        "id": eid,
        "type": "rectangle",
        "x": x, "y": y,
        "width": w, "height": h,
        "angle": 0,
        "strokeColor": stroke,
        "backgroundColor": bg,
        "fillStyle": fill,
        "strokeWidth": stroke_w,
        "strokeStyle": stroke_style,
        "roughness": roughness,
        "opacity": opacity,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 3} if rounded else None,
        "seed": make_seed(),
        "version": 1,
        "versionNonce": make_seed(),
        "isDeleted": False,
        "boundElements": [],
        "updated": 1709000000000,
        "link": None,
        "locked": False,
    }

def text(x, y, content, size=16, color="#000000", family=2, align="center",
         valign="middle", w=None, h=None, container_id=None):
    """Create a text element. family: 1=Virgil, 2=Helvetica, 3=Cascadia"""
    eid = make_id()
    # Estimate width/height if not provided
    if w is None:
        w = len(content) * size * 0.6
    if h is None:
        lines = content.count("\n") + 1
        h = lines * (size * 1.4)
    return {
        "id": eid,
        "type": "text",
        "x": x, "y": y,
        "width": w, "height": h,
        "angle": 0,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": make_seed(),
        "version": 1,
        "versionNonce": make_seed(),
        "isDeleted": False,
        "boundElements": None,
        "updated": 1709000000000,
        "link": None,
        "locked": False,
        "text": content,
        "fontSize": size,
        "fontFamily": family,
        "textAlign": align,
        "verticalAlign": valign,
        "containerId": container_id,
        "originalText": content,
        "autoResize": True,
        "lineHeight": 1.25,
    }

def arrow(x1, y1, x2, y2, stroke="#000000", stroke_w=2, start_id=None, end_id=None,
          start_arrow=None, end_arrow="arrow", stroke_style="solid", label=None):
    """Create an arrow element."""
    eid = make_id()
    dx = x2 - x1
    dy = y2 - y1
    el = {
        "id": eid,
        "type": "arrow",
        "x": x1, "y": y1,
        "width": abs(dx), "height": abs(dy),
        "angle": 0,
        "strokeColor": stroke,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": stroke_w,
        "strokeStyle": stroke_style,
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 2},
        "seed": make_seed(),
        "version": 1,
        "versionNonce": make_seed(),
        "isDeleted": False,
        "boundElements": [],
        "updated": 1709000000000,
        "link": None,
        "locked": False,
        "points": [[0, 0], [dx, dy]],
        "startBinding": {"elementId": start_id, "focus": 0, "gap": 4} if start_id else None,
        "endBinding": {"elementId": end_id, "focus": 0, "gap": 4} if end_id else None,
        "startArrowhead": start_arrow,
        "endArrowhead": end_arrow,
    }
    return el

def service_box(x, y, name, port, accent_color, tier_bg):
    """Create a service box with label. Returns (elements_list, box_id)."""
    bw, bh = 150, 56
    box = rect(x, y, bw, bh, stroke=accent_color, bg=tier_bg, fill="solid",
               stroke_w=2, opacity=100)
    box_id = box["id"]

    # Main label
    label_text = f"{name}\n:{port}" if port else name
    lbl = text(0, 0, label_text, size=14, color=ICE_WHITE, family=3,
               align="center", valign="middle", w=bw - 8, h=bh - 8,
               container_id=box_id)

    box["boundElements"] = [{"id": lbl["id"], "type": "text"}]

    return [box, lbl], box_id

def zone_box(x, y, w, h, label_text, bg_color, stroke_color, subtitle=None):
    """Create a zone rectangle with title. Returns (elements_list, zone_id)."""
    zone = rect(x, y, w, h, stroke=stroke_color, bg=bg_color, fill="solid",
                stroke_w=3, opacity=90, rounded=True)
    zone_id = zone["id"]

    # Title at top of zone
    title = text(x + 20, y + 12, label_text, size=22, color=ICE_WHITE, family=2,
                 align="left", w=w - 40, h=30)

    elements = [zone, title]

    if subtitle:
        sub = text(x + 20, y + 40, subtitle, size=11, color=CLOUD_GRAY, family=3,
                   align="left", w=w - 40, h=16)
        elements.append(sub)

    return elements, zone_id

def tier_label(x, y, label_text, color):
    """Create a tier section label."""
    lbl = text(x, y, label_text, size=12, color=color, family=2,
               align="left", w=200, h=18)
    return lbl


def build_diagram():
    elements = []

    # =========================================================================
    # ZONE 1: STMNA DESK (left, largest)
    # =========================================================================
    desk_x, desk_y = 30, 30
    desk_w, desk_h = 940, 820

    desk_els, desk_id = zone_box(
        desk_x, desk_y, desk_w, desk_h,
        "STMNA Desk_",
        DEEP_NAVY, EMBER_ORANGE,
        "Framework Desktop 128GB · AMD Ryzen AI Max+ 395 · Rootless Podman"
    )
    elements.extend(desk_els)

    # --- Core Tier ---
    core_y = desk_y + 70
    elements.append(tier_label(desk_x + 24, core_y, "CORE", EMBER_ORANGE))
    core_y += 24

    # Tier background band
    core_band = rect(desk_x + 16, core_y, desk_w - 32, 180,
                     stroke=EMBER_ORANGE, bg="#1E1E35", fill="solid",
                     stroke_w=1, opacity=40, stroke_style="dashed")
    elements.append(core_band)

    # llama-swap
    svc_els, llama_swap_id = service_box(desk_x + 40, core_y + 16, "llama-swap", "8081", EMBER_ORANGE, "#2A1A10")
    elements.extend(svc_els)

    # llama.cpp (Vulkan) - wider box
    llama_cpp = rect(desk_x + 220, core_y + 16, 200, 56,
                     stroke=EMBER_ORANGE, bg="#2A1A10", fill="solid", stroke_w=2)
    llama_cpp_id = llama_cpp["id"]
    llama_lbl = text(0, 0, "llama.cpp (Vulkan)\nGPU Inference Engine", size=13, color=ICE_WHITE,
                     family=3, align="center", valign="middle", w=192, h=48,
                     container_id=llama_cpp_id)
    llama_cpp["boundElements"] = [{"id": llama_lbl["id"], "type": "text"}]
    elements.extend([llama_cpp, llama_lbl])

    # Arrow: llama-swap -> llama.cpp
    elements.append(arrow(desk_x + 190, core_y + 44, desk_x + 220, core_y + 44,
                          stroke=EMBER_ORANGE, stroke_w=2,
                          start_id=llama_swap_id, end_id=llama_cpp_id))

    # PostgreSQL
    svc_els, postgres_id = service_box(desk_x + 460, core_y + 16, "PostgreSQL", "5432", EMBER_ORANGE, "#2A1A10")
    elements.extend(svc_els)

    # Dockge
    svc_els, dockge_id = service_box(desk_x + 640, core_y + 16, "Dockge", "5001", EMBER_ORANGE, "#2A1A10")
    elements.extend(svc_els)

    # Open WebUI
    svc_els, owui_id = service_box(desk_x + 460, core_y + 100, "Open WebUI", "3000", EMBER_ORANGE, "#2A1A10")
    elements.extend(svc_els)

    # TEI (Embeddings)
    svc_els, tei_id = service_box(desk_x + 640, core_y + 100, "TEI Embed", "9003", EMBER_ORANGE, "#2A1A10")
    elements.extend(svc_els)

    # --- Automation Tier ---
    auto_y = core_y + 200
    elements.append(tier_label(desk_x + 24, auto_y, "AUTOMATION", SOLAR_GOLD))
    auto_y += 24

    auto_band = rect(desk_x + 16, auto_y, desk_w - 32, 120,
                     stroke=SOLAR_GOLD, bg="#1E1E35", fill="solid",
                     stroke_w=1, opacity=40, stroke_style="dashed")
    elements.append(auto_band)

    # n8n
    n8n_box = rect(desk_x + 40, auto_y + 16, 200, 56,
                   stroke=SOLAR_GOLD, bg="#1A1A10", fill="solid", stroke_w=2)
    n8n_id = n8n_box["id"]
    n8n_lbl = text(0, 0, "n8n\n:5678 · Signal · Voice · Vault", size=12, color=ICE_WHITE,
                   family=3, align="center", valign="middle", w=192, h=48,
                   container_id=n8n_id)
    n8n_box["boundElements"] = [{"id": n8n_lbl["id"], "type": "text"}]
    elements.extend([n8n_box, n8n_lbl])

    # whisper-voice
    svc_els, whisper_v_id = service_box(desk_x + 300, auto_y + 16, "whisper.cpp", "8083", SOLAR_GOLD, "#1A1A10")
    elements.extend(svc_els)

    # whisper-signal
    svc_els, whisper_s_id = service_box(desk_x + 490, auto_y + 16, "whisper.cpp", "8084", SOLAR_GOLD, "#1A1A10")
    elements.extend(svc_els)

    # Kokoro TTS
    svc_els, kokoro_id = service_box(desk_x + 680, auto_y + 16, "Kokoro TTS", "9005", SOLAR_GOLD, "#1A1A10")
    elements.extend(svc_els)

    # --- Extended Tier ---
    ext_y = auto_y + 160
    elements.append(tier_label(desk_x + 24, ext_y, "EXTENDED", CLOUD_GRAY))
    ext_y += 24

    ext_band = rect(desk_x + 16, ext_y, desk_w - 32, 100,
                    stroke=CLOUD_GRAY, bg="#1E1E35", fill="solid",
                    stroke_w=1, opacity=40, stroke_style="dashed")
    elements.append(ext_band)

    # Agent Zero
    svc_els, a0_id = service_box(desk_x + 40, ext_y + 16, "Agent Zero", "50001", CLOUD_GRAY, "#1A1A20")
    elements.extend(svc_els)

    # Crawl4AI
    svc_els, crawl_id = service_box(desk_x + 220, ext_y + 16, "Crawl4AI", "11235", CLOUD_GRAY, "#1A1A20")
    elements.extend(svc_els)

    # SearXNG
    svc_els, searx_id = service_box(desk_x + 400, ext_y + 16, "SearXNG", "8888", CLOUD_GRAY, "#1A1A20")
    elements.extend(svc_els)

    # Excalidraw
    svc_els, excali_id = service_box(desk_x + 580, ext_y + 16, "Excalidraw", "8585", CLOUD_GRAY, "#1A1A20")
    elements.extend(svc_els)

    # --- Internal connection arrows ---

    # llama-swap fan-out: -> Open WebUI
    elements.append(arrow(desk_x + 115, core_y + 72, desk_x + 530, core_y + 100,
                          stroke=EMBER_ORANGE, stroke_w=1,
                          start_id=llama_swap_id, end_id=owui_id))

    # llama-swap fan-out: -> n8n
    elements.append(arrow(desk_x + 115, core_y + 72, desk_x + 140, auto_y + 16,
                          stroke=EMBER_ORANGE, stroke_w=1,
                          start_id=llama_swap_id, end_id=n8n_id))

    # llama-swap fan-out: -> Agent Zero
    elements.append(arrow(desk_x + 115, core_y + 72, desk_x + 115, ext_y + 16,
                          stroke=EMBER_ORANGE, stroke_w=1,
                          start_id=llama_swap_id, end_id=a0_id))

    # whisper -> n8n
    elements.append(arrow(desk_x + 375, auto_y + 72, desk_x + 240, auto_y + 44,
                          stroke=SOLAR_GOLD, stroke_w=1,
                          start_id=whisper_v_id, end_id=n8n_id))

    elements.append(arrow(desk_x + 565, auto_y + 72, desk_x + 240, auto_y + 50,
                          stroke=SOLAR_GOLD, stroke_w=1,
                          start_id=whisper_s_id, end_id=n8n_id))

    # SearXNG -> Open WebUI (tool calling)
    elements.append(arrow(desk_x + 475, ext_y + 16, desk_x + 530, core_y + 156,
                          stroke=CLOUD_GRAY, stroke_w=1,
                          start_id=searx_id, end_id=owui_id))

    # n8n -> PostgreSQL
    elements.append(arrow(desk_x + 240, auto_y + 30, desk_x + 460, core_y + 44,
                          stroke=SOLAR_GOLD, stroke_w=1,
                          start_id=n8n_id, end_id=postgres_id))

    # n8n -> TEI
    elements.append(arrow(desk_x + 240, auto_y + 50, desk_x + 640, core_y + 128,
                          stroke=SOLAR_GOLD, stroke_w=1,
                          start_id=n8n_id, end_id=tei_id))

    # =========================================================================
    # ZONE 2: VPS (right top)
    # =========================================================================
    vps_x, vps_y = 1040, 30
    vps_w, vps_h = 420, 490

    vps_els, vps_id = zone_box(
        vps_x, vps_y, vps_w, vps_h,
        "VPS",
        SLATE_BLUE, CLOUD_GRAY,
        "Public Gateway · Stable IP · TLS Termination"
    )
    elements.extend(vps_els)

    # Headscale
    svc_els, headscale_id = service_box(vps_x + 30, vps_y + 70, "Headscale", "", EMBER_ORANGE, "#1A1A10")
    elements.extend(svc_els)

    # Caddy
    caddy_box = rect(vps_x + 30, vps_y + 150, 360, 56,
                     stroke=CLOUD_GRAY, bg="#1A2030", fill="solid", stroke_w=2)
    caddy_id = caddy_box["id"]
    caddy_lbl = text(0, 0, "Caddy — HTTPS Termination + Bearer Token Auth", size=13,
                     color=ICE_WHITE, family=3, align="center", valign="middle",
                     w=352, h=48, container_id=caddy_id)
    caddy_box["boundElements"] = [{"id": caddy_lbl["id"], "type": "text"}]
    elements.extend([caddy_box, caddy_lbl])

    # Forgejo (on VPS)
    svc_els, forgejo_id = service_box(vps_x + 30, vps_y + 240, "Forgejo", "3300", CLOUD_GRAY, "#1A2030")
    elements.extend(svc_els)

    # Nextcloud (on VPS)
    svc_els, nextcloud_id = service_box(vps_x + 210, vps_y + 240, "Nextcloud", "8090", CLOUD_GRAY, "#1A2030")
    elements.extend(svc_els)

    # Headscale label (VPN coordinator)
    coord_lbl = text(vps_x + 190, vps_y + 82, "VPN Coordinator", size=11, color=CLOUD_GRAY,
                     family=2, w=120, h=16)
    elements.append(coord_lbl)

    # Arrow: Caddy -> Forgejo
    elements.append(arrow(vps_x + 120, vps_y + 206, vps_x + 100, vps_y + 240,
                          stroke=CLOUD_GRAY, stroke_w=1,
                          start_id=caddy_id, end_id=forgejo_id))

    # Arrow: Caddy -> Nextcloud
    elements.append(arrow(vps_x + 300, vps_y + 206, vps_x + 285, vps_y + 240,
                          stroke=CLOUD_GRAY, stroke_w=1,
                          start_id=caddy_id, end_id=nextcloud_id))

    # VPS info boxes
    # Forgejo subtitle
    fg_sub = text(vps_x + 30, vps_y + 300, "Git hosting\nVault sync\nWebhooks", size=10,
                  color=CLOUD_GRAY, family=3, w=140, h=50)
    elements.append(fg_sub)

    nc_sub = text(vps_x + 210, vps_y + 300, "File storage\nAudio delivery\nBook drops", size=10,
                  color=CLOUD_GRAY, family=3, w=140, h=50)
    elements.append(nc_sub)

    # =========================================================================
    # ZONE 3: CLIENT DEVICES (right bottom)
    # =========================================================================
    cli_x, cli_y = 1040, 560
    cli_w, cli_h = 420, 290

    cli_els, cli_id = zone_box(
        cli_x, cli_y, cli_w, cli_h,
        "Client Devices",
        SLATE_MID, CLOUD_GRAY,
        "Standard HTTPS · No VPN Required"
    )
    elements.extend(cli_els)

    # Client device boxes
    svc_els, laptop_id = service_box(cli_x + 30, cli_y + 70, "Laptop", "", CLOUD_GRAY, "#3A4A6C")
    elements.extend(svc_els)

    svc_els, mobile_id = service_box(cli_x + 210, cli_y + 70, "Mobile", "", CLOUD_GRAY, "#3A4A6C")
    elements.extend(svc_els)

    svc_els, signal_id = service_box(cli_x + 30, cli_y + 150, "Signal App", "", CLOUD_GRAY, "#3A4A6C")
    elements.extend(svc_els)

    svc_els, browser_id = service_box(cli_x + 210, cli_y + 150, "Browser", "", CLOUD_GRAY, "#3A4A6C")
    elements.extend(svc_els)

    # Client descriptions
    cli_desc = text(cli_x + 30, cli_y + 224, "Open WebUI · Agent Zero · n8n · Signal pipeline · Voice API",
                    size=11, color=CLOUD_GRAY, family=3, w=360, h=16)
    elements.append(cli_desc)

    # =========================================================================
    # INTER-ZONE CONNECTIONS
    # =========================================================================

    # Desk <-> VPS: Headscale VPN Tunnel (thick, orange, bidirectional)
    vpn_arrow = arrow(desk_x + desk_w, desk_y + 100, vps_x, vps_y + 95,
                      stroke=EMBER_ORANGE, stroke_w=4,
                      start_arrow="arrow", end_arrow="arrow")
    elements.append(vpn_arrow)

    # VPN Tunnel label
    vpn_label = text(desk_x + desk_w + 8, desk_y + 72, "Headscale\nVPN Tunnel", size=13,
                     color=EMBER_ORANGE, family=2, w=90, h=36)
    elements.append(vpn_label)

    # Clients -> VPS Caddy: HTTPS connections
    # Laptop -> Caddy
    elements.append(arrow(cli_x + 105, cli_y + 70, vps_x + 120, vps_y + 206,
                          stroke=CLOUD_GRAY, stroke_w=1,
                          start_id=laptop_id, end_id=caddy_id))

    # Mobile -> Caddy
    elements.append(arrow(cli_x + 285, cli_y + 70, vps_x + 300, vps_y + 206,
                          stroke=CLOUD_GRAY, stroke_w=1,
                          start_id=mobile_id, end_id=caddy_id))

    # Signal -> Caddy
    elements.append(arrow(cli_x + 105, cli_y + 150, vps_x + 80, vps_y + 206,
                          stroke=CLOUD_GRAY, stroke_w=1,
                          start_id=signal_id, end_id=caddy_id))

    # Browser -> Caddy
    elements.append(arrow(cli_x + 285, cli_y + 150, vps_x + 340, vps_y + 206,
                          stroke=CLOUD_GRAY, stroke_w=1,
                          start_id=browser_id, end_id=caddy_id))

    # HTTPS label between clients and VPS
    https_label = text(cli_x + vps_w + 10, cli_y + 20, "HTTPS", size=12,
                       color=CLOUD_GRAY, family=2, w=50, h=18)
    # Actually let's place it better
    https_label["x"] = vps_x + vps_w - 60
    https_label["y"] = vps_y + vps_h + 20
    elements.append(https_label)

    # =========================================================================
    # SHARED NETWORK LABEL
    # =========================================================================
    net_label = text(desk_x + 24, desk_y + desk_h - 36,
                     "All containers on stmna-net bridge · Rootless Podman · No root daemon",
                     size=11, color=CLOUD_GRAY, family=3, w=desk_w - 48, h=16)
    elements.append(net_label)

    # =========================================================================
    # LEGEND (bottom center, below VPS/clients)
    # =========================================================================
    leg_x = vps_x
    leg_y = cli_y + cli_h + 20

    # Legend title
    elements.append(text(leg_x, leg_y, "Legend", size=14, color=ICE_WHITE, family=2, w=60, h=20))

    # Legend items - small colored squares + labels
    leg_items = [
        (EMBER_ORANGE, "Core Services"),
        (SOLAR_GOLD, "Automation"),
        (CLOUD_GRAY, "Extended / Clients"),
    ]
    for i, (color, label) in enumerate(leg_items):
        ly = leg_y + 24 + i * 22
        sq = rect(leg_x, ly, 14, 14, stroke=color, bg=color, fill="solid",
                  stroke_w=1, rounded=False)
        elements.append(sq)
        elements.append(text(leg_x + 22, ly - 1, label, size=12, color=ICE_WHITE,
                             family=2, w=160, h=16))

    # Legend connection types
    con_y = leg_y + 24 + 3 * 22 + 4
    elements.append(arrow(leg_x, con_y + 6, leg_x + 40, con_y + 6,
                          stroke=EMBER_ORANGE, stroke_w=4,
                          start_arrow="arrow", end_arrow="arrow"))
    elements.append(text(leg_x + 48, con_y - 1, "VPN Tunnel (Headscale)", size=12,
                         color=ICE_WHITE, family=2, w=180, h=16))

    con_y += 22
    elements.append(arrow(leg_x, con_y + 6, leg_x + 40, con_y + 6,
                          stroke=CLOUD_GRAY, stroke_w=1))
    elements.append(text(leg_x + 48, con_y - 1, "HTTPS / Internal", size=12,
                         color=ICE_WHITE, family=2, w=180, h=16))

    # =========================================================================
    # BUILD FINAL DOCUMENT
    # =========================================================================
    doc = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://stmna.io",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": VOID_BLACK,
        },
        "files": {},
    }

    return doc


if __name__ == "__main__":
    random.seed(42)  # Reproducible layout
    doc = build_diagram()
    output_path = "/home/claude/repos/stmna-desk/docs/assets/architecture.excalidraw"
    with open(output_path, "w") as f:
        json.dump(doc, f, indent=2)
    print(f"Generated {output_path} with {len(doc['elements'])} elements")
