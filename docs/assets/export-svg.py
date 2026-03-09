#!/usr/bin/env python3
"""
Export .excalidraw JSON to SVG.
Works for clean style (roughness=0) diagrams with rectangles, text, and arrows.
"""
import json
import html
import math

def load_excalidraw(path):
    with open(path) as f:
        return json.load(f)

def hex_to_rgba(hex_color, opacity=100):
    """Convert hex color + opacity to rgba string."""
    if hex_color == "transparent":
        return "none"
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if opacity < 100:
        return f"rgba({r},{g},{b},{opacity/100})"
    return hex_color

def font_family_name(family_id):
    return {1: "Virgil, cursive", 2: "Helvetica, Arial, sans-serif",
            3: "'JetBrains Mono', 'Fira Code', monospace"}.get(family_id, "sans-serif")

def render_element(el, svg_parts):
    """Render a single Excalidraw element to SVG."""
    etype = el.get("type")
    if el.get("isDeleted"):
        return

    opacity = el.get("opacity", 100)
    opacity_attr = f' opacity="{opacity/100}"' if opacity < 100 else ""

    if etype == "rectangle":
        x, y = el["x"], el["y"]
        w, h = el["width"], el["height"]
        stroke = el.get("strokeColor", "#000")
        bg = hex_to_rgba(el.get("backgroundColor", "transparent"), opacity)
        stroke_w = el.get("strokeWidth", 2)
        rounded = el.get("roundness")
        rx = 8 if rounded else 0

        stroke_dash = ""
        if el.get("strokeStyle") == "dashed":
            stroke_dash = ' stroke-dasharray="8 4"'

        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'rx="{rx}" ry="{rx}" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="{stroke_w}"{stroke_dash}{opacity_attr}/>'
        )

    elif etype == "text":
        # Skip text bound to a container — we'll render it when we render the container
        container_id = el.get("containerId")
        x, y = el["x"], el["y"]
        w = el.get("width", 100)
        h = el.get("height", 20)
        content = el.get("text", "")
        size = el.get("fontSize", 16)
        color = el.get("strokeColor", "#000")
        family = font_family_name(el.get("fontFamily", 2))
        align = el.get("textAlign", "left")
        valign = el.get("verticalAlign", "top")

        # For contained text, position is relative to container center
        # We handle that in a second pass
        if container_id:
            return  # Handled by container rendering

        lines = content.split("\n")
        line_height = size * 1.25

        # Compute text anchor
        anchor = {"left": "start", "center": "middle", "right": "end"}.get(align, "start")

        # Starting x based on alignment
        if align == "center":
            tx = x + w / 2
        elif align == "right":
            tx = x + w
        else:
            tx = x

        # Starting y
        total_text_h = len(lines) * line_height
        if valign == "middle":
            ty = y + (h - total_text_h) / 2 + size * 0.85
        else:
            ty = y + size * 0.85

        for i, line in enumerate(lines):
            svg_parts.append(
                f'<text x="{tx}" y="{ty + i * line_height}" '
                f'font-family="{family}" font-size="{size}" '
                f'fill="{color}" text-anchor="{anchor}" '
                f'dominant-baseline="auto">{html.escape(line)}</text>'
            )

    elif etype == "arrow":
        x, y = el["x"], el["y"]
        points = el.get("points", [[0, 0], [100, 0]])
        stroke = el.get("strokeColor", "#000")
        stroke_w = el.get("strokeWidth", 2)
        end_head = el.get("endArrowhead")
        start_head = el.get("startArrowhead")

        stroke_dash = ""
        if el.get("strokeStyle") == "dashed":
            stroke_dash = ' stroke-dasharray="8 4"'

        # Build path
        path_d = f"M {x + points[0][0]} {y + points[0][1]}"
        for pt in points[1:]:
            path_d += f" L {x + pt[0]} {y + pt[1]}"

        # Marker references
        marker_end = ""
        marker_start = ""
        marker_id_end = f"arrow-end-{el['id']}"
        marker_id_start = f"arrow-start-{el['id']}"

        if end_head == "arrow":
            marker_end = f' marker-end="url(#{marker_id_end})"'
            # Add arrowhead marker definition
            svg_parts.append(
                f'<defs><marker id="{marker_id_end}" markerWidth="10" markerHeight="10" '
                f'refX="9" refY="5" orient="auto-start-reverse">'
                f'<path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="{stroke}" '
                f'stroke-width="1.5"/></marker></defs>'
            )

        if start_head == "arrow":
            marker_start = f' marker-start="url(#{marker_id_start})"'
            svg_parts.append(
                f'<defs><marker id="{marker_id_start}" markerWidth="10" markerHeight="10" '
                f'refX="1" refY="5" orient="auto-start-reverse">'
                f'<path d="M 10 0 L 0 5 L 10 10" fill="none" stroke="{stroke}" '
                f'stroke-width="1.5"/></marker></defs>'
            )

        svg_parts.append(
            f'<path d="{path_d}" fill="none" stroke="{stroke}" '
            f'stroke-width="{stroke_w}"{stroke_dash}{marker_end}{marker_start}{opacity_attr}/>'
        )


def render_contained_text(elements, svg_parts):
    """Second pass: render text elements that are bound to containers."""
    # Build element lookup
    el_map = {el["id"]: el for el in elements}

    for el in elements:
        if el.get("type") != "text" or el.get("isDeleted"):
            continue
        container_id = el.get("containerId")
        if not container_id:
            continue

        container = el_map.get(container_id)
        if not container:
            continue

        cx = container["x"]
        cy = container["y"]
        cw = container["width"]
        ch = container["height"]

        content = el.get("text", "")
        size = el.get("fontSize", 16)
        color = el.get("strokeColor", "#000")
        family = font_family_name(el.get("fontFamily", 2))
        align = el.get("textAlign", "center")

        lines = content.split("\n")
        line_height = size * 1.25

        anchor = {"left": "start", "center": "middle", "right": "end"}.get(align, "middle")

        # Center text in container
        tx = cx + cw / 2
        total_text_h = len(lines) * line_height
        ty = cy + (ch - total_text_h) / 2 + size * 0.85

        for i, line in enumerate(lines):
            svg_parts.append(
                f'<text x="{tx}" y="{ty + i * line_height}" '
                f'font-family="{family}" font-size="{size}" '
                f'fill="{color}" text-anchor="{anchor}" '
                f'dominant-baseline="auto">{html.escape(line)}</text>'
            )


def export_svg(excalidraw_path, svg_path):
    doc = load_excalidraw(excalidraw_path)
    elements = doc.get("elements", [])
    bg_color = doc.get("appState", {}).get("viewBackgroundColor", "#ffffff")

    # Compute bounding box
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")
    for el in elements:
        if el.get("isDeleted"):
            continue
        x = el.get("x", 0)
        y = el.get("y", 0)
        w = el.get("width", 0)
        h = el.get("height", 0)
        if el["type"] == "arrow":
            pts = el.get("points", [])
            for pt in pts:
                px, py = x + pt[0], y + pt[1]
                min_x = min(min_x, px)
                min_y = min(min_y, py)
                max_x = max(max_x, px)
                max_y = max(max_y, py)
        else:
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)

    padding = 40
    vx = min_x - padding
    vy = min_y - padding
    vw = (max_x - min_x) + 2 * padding
    vh = (max_y - min_y) + 2 * padding

    svg_parts = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx} {vy} {vw} {vh}" '
        f'width="{vw}" height="{vh}">'
    )
    # Background
    svg_parts.append(f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="{bg_color}"/>')

    # Render all elements (first pass: rects, standalone text, arrows)
    for el in elements:
        render_element(el, svg_parts)

    # Second pass: contained text
    render_contained_text(elements, svg_parts)

    svg_parts.append("</svg>")

    svg_content = "\n".join(svg_parts)
    with open(svg_path, "w") as f:
        f.write(svg_content)

    print(f"Exported SVG to {svg_path} ({vw:.0f}x{vh:.0f})")
    return svg_content


if __name__ == "__main__":
    base = "/home/claude/repos/stmna-desk/docs/assets"
    export_svg(f"{base}/architecture.excalidraw", f"{base}/architecture.svg")
