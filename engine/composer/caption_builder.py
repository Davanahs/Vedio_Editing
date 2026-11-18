"""
Caption Builder for Reel Editor.
Generates HyperFrames-compatible captions.html from EDL CaptionBursts.
"""
from typing import List, Union
from engine.director.edl_schema import CaptionBurst

def build_captions_html(captions: List[Union[CaptionBurst, dict]]) -> str:
    """
    Renders captions.html containing all caption bursts with GSAP spring animations
    and word highlights.
    """
    items_html = []
    
    for i, c in enumerate(captions):
        if isinstance(c, dict):
            c_id = c.get("id", f"cap_{i}")
            start = float(c.get("start", 0.0))
            end = float(c.get("end", 0.0))
            lead = c.get("lead", "")
            keyword = c.get("keyword", "")
            highlight_color = c.get("highlight_color", "#FFE600")
        else:
            c_id = c.id
            start = c.start
            end = c.end
            lead = c.lead
            keyword = c.keyword
            highlight_color = c.highlight_color

        duration = max(0.1, round(end - start, 3))
        clean_lead = lead.strip()
        clean_keyword = keyword.strip()
        
        lead_span = f'<span class="caption-lead">{clean_lead}</span>' if clean_lead else ''
        
        item = f'''      <div class="caption-item" id="{c_id}" data-start="{start:.3f}" data-duration="{duration:.3f}" data-layout-allow-safe-zone>
        {lead_span}
        <span class="caption-keyword" style="--hl-color: {highlight_color};">{clean_keyword}</span>
      </div>'''
        items_html.append(item)

    items_block = "\n".join(items_html)

    html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080, height=1920">
    <title>Captions</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@700;800;900&display=swap');

      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}

      html, body {{
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: transparent;
      }}

      #root {{
        position: relative;
        width: 1080px;
        height: 1920px;
        pointer-events: none;
      }}

      .caption-item {{
        position: absolute;
        top: 1120px;
        left: 50%;
        transform: translateX(-50%);
        width: 920px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        opacity: 0;
      }}

      .caption-lead {{
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 34px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.9);
        text-shadow: 0 4px 14px rgba(0, 0, 0, 0.95), 0 2px 4px rgba(0, 0, 0, 0.8);
        text-transform: lowercase;
        margin-bottom: 4px;
        letter-spacing: -0.01em;
      }}

      .caption-keyword {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 96px;
        font-weight: 900;
        line-height: 0.92;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        text-shadow: 
          0 4px 20px rgba(0, 0, 0, 0.95),
          0 8px 30px rgba(0, 0, 0, 0.75),
          0 0 24px var(--hl-color, #FFE600);
        background: linear-gradient(180deg, #FFFFFF 20%, var(--hl-color, #FFE600) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 4px 12px;
        display: inline-block;
      }}
    </style>
  </head>
  <body>
    <div id="root">
{items_block}
    </div>

    <script>
      // HyperFrames frame driver triggers or GSAP timeline
      document.querySelectorAll('.caption-item').forEach((el) => {{
        const start = parseFloat(el.getAttribute('data-start') || '0');
        const dur = parseFloat(el.getAttribute('data-duration') || '1');
        
        gsap.timeline({{
          scrollTrigger: null
        }})
        .fromTo(el, 
          {{ opacity: 0, scale: 1.15, y: 15 }}, 
          {{ opacity: 1, scale: 1.0, y: 0, duration: 0.15, ease: "power2.out", delay: start }}
        )
        .to(el, 
          {{ opacity: 0, scale: 0.96, duration: 0.1, ease: "power2.in", delay: Math.max(0, dur - 0.25) }}
        );
      }});
    </script>
  </body>
</html>'''
    return html
