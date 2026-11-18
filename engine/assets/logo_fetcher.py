import os
from pathlib import Path
from typing import Optional
import httpx

async def fetch_logo(slug: str, color: Optional[str] = None, output_dir: Optional[str] = None) -> Optional[str]:
    """
    Fetch an SVG logo from simpleicons CDN and cache it locally.
    """
    if not output_dir:
        output_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "cache" / "logos"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{slug}.svg"
    
    if out_file.exists():
        return out_file.read_text(encoding="utf-8")

    clean_color = color.replace("#", "") if color else "FFFFFF"
    url = f"https://cdn.simpleicons.org/{slug}/{clean_color}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and resp.text.strip().startswith("<svg"):
                out_file.write_text(resp.text, encoding="utf-8")
                return resp.text
    except Exception as e:
        print(f"Failed to fetch logo for {slug}: {e}")

    # Fallback placeholder SVG
    placeholder = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <circle cx="50" cy="50" r="45" fill="#{clean_color}" />
  <text x="50" y="55" font-size="20" fill="#ffffff" text-anchor="middle" dominant-baseline="middle" font-family="sans-serif">{slug[:4].upper()}</text>
</svg>'''
    out_file.write_text(placeholder, encoding="utf-8")
    return placeholder
