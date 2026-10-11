"""
SVG and Markdown Badge Generator for Peer-Bounty.
Generates self-contained, lightweight vector badges for GitHub issues and READMEs.
"""

def generate_svg_badge(sats: int, status: str = "open", label: str = "Bitcoin Bounty") -> str:
    """
    Renders a standalone SVG badge displaying the bounty satoshi value and settlement status.
    """
    status_lower = status.lower()
    if status_lower == "settled":
        right_bg = "#2da44e"  # Verified Green
        status_text = f"{sats:,} sats [settled]"
    elif status_lower == "funded":
        right_bg = "#f7931a"  # Bitcoin Orange
        status_text = f"{sats:,} sats [funded]"
    elif status_lower == "closed":
        right_bg = "#6e7681"  # Neutral Grey
        status_text = f"{sats:,} sats [closed]"
    else:
        right_bg = "#f7931a"  # Bitcoin Orange
        status_text = f"{sats:,} sats"

    left_bg = "#24292f"  # GitHub Dark Slate
    text_color = "#ffffff"

    # Calculate widths dynamically based on character counts
    left_char_len = len(label)
    right_char_len = len(status_text)
    left_width = max(90, left_char_len * 7 + 16)
    right_width = max(80, right_char_len * 7 + 16)
    total_width = left_width + right_width
    height = 20

    left_text_x = left_width / 2.0
    right_text_x = left_width + (right_width / 2.0)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label}: {status_text}">
  <title>{label}: {status_text}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="{height}" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{left_width}" height="{height}" fill="{left_bg}"/>
    <rect x="{left_width}" width="{right_width}" height="{height}" fill="{right_bg}"/>
    <rect width="{total_width}" height="{height}" fill="url(#s)"/>
  </g>
  <g fill="{text_color}" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text aria-hidden="true" x="{left_text_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(left_width - 14) * 10}">{label}</text>
    <text x="{left_text_x * 10}" y="140" transform="scale(.1)" fill="{text_color}" textLength="{(left_width - 14) * 10}">{label}</text>
    <text aria-hidden="true" x="{right_text_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(right_width - 14) * 10}">{status_text}</text>
    <text x="{right_text_x * 10}" y="140" transform="scale(.1)" fill="{text_color}" textLength="{(right_width - 14) * 10}">{status_text}</text>
  </g>
</svg>"""
    return svg.strip()

def generate_markdown_badge(issue_number: int, sats: int, repo: str, status: str = "open") -> str:
    """
    Generates a Markdown badge snippet for embedding in a GitHub issue body.
    """
    badge_url = f"https://raw.githubusercontent.com/{repo}/main/.peer-bounty/badges/issue-{issue_number}.svg"
    target_url = f"https://github.com/{repo}/issues/{issue_number}"
    return f"[![Bitcoin Bounty: {sats:,} sats]({badge_url})]({target_url})"
