"""
Overlay Builder for Reel Editor.
Generates HyperFrames-compatible overlays.html from EDL GraphicElements and SoundEffects.
"""
from typing import List, Union, Dict, Any
from pathlib import Path
from engine.director.edl_schema import GraphicElement, SoundEffect

def build_overlays_html(
    graphics: List[Union[GraphicElement, dict]],
    sound_effects: List[Union[SoundEffect, dict]],
    video_duration: float = 47.0,
    asset_registry: Any = None
) -> str:
    """
    Renders overlays.html containing animated badges, emojis, keyword graphics,
    and audio SFX elements.
    """
    elements_html = []
    audio_html = []

    # 1. Default Hook Card (0.0s -> 3.0s)
    elements_html.append('''      <!-- Top Hook Badge -->
      <div id="hook-card" class="overlay-element" data-start="0.100" data-duration="2.900" data-layout-allow-safe-zone>
        <span class="hook-emoji">🎉</span>
        <span class="hook-text">FIRST TIME FINALLY POSTING</span>
      </div>''')

    # 2. Dynamic Graphics from EDL
    for i, g in enumerate(graphics):
        if isinstance(g, dict):
            asset_id = g.get("asset_id", "")
            start = float(g.get("start", 0.0))
            end = float(g.get("end", 0.0))
            x = int(g.get("x", 540))
            y = int(g.get("y", 960))
            width = int(g.get("width", 200))
            height = int(g.get("height", 80))
            anim = g.get("animation", "spring_in")
            trigger = g.get("trigger_word", "")
        else:
            asset_id = g.asset_id
            start = g.start
            end = g.end
            x = g.x
            y = g.y
            width = g.width
            height = g.height
            anim = g.animation
            trigger = g.trigger_word

        duration = max(0.5, round(end - start, 3))
        elem_id = f"overlay_gfx_{i}_{asset_id}"

        # Resolve asset content
        content_inner = ""
        bg_style = "background: rgba(20, 24, 38, 0.92); border: 2px solid rgba(255, 230, 0, 0.4);"
        
        # Check logo or sticker
        if asset_id == "instagram":
            bg_style = "background: linear-gradient(135deg, #833AB4, #FD1D1D, #FCAF45); border: none;"
            content_inner = '''<div class="logo-popup-content"><span class="badge-icon">📸</span><span class="badge-label">INSTAGRAM</span></div>'''
        elif asset_id in ["chatgpt", "openai"]:
            bg_style = "background: #10A37F; border: 2px solid #55E6B5;"
            content_inner = '''<div class="logo-popup-content"><span class="badge-icon">🤖</span><span class="badge-label">CHATGPT</span></div>'''
        elif asset_id == "youtube":
            bg_style = "background: #FF0000; border: none;"
            content_inner = '''<div class="logo-popup-content"><span class="badge-icon">▶️</span><span class="badge-label">YOUTUBE</span></div>'''
        elif asset_id in ["content_creator", "rocket"]:
            bg_style = "background: linear-gradient(135deg, #00C6FF, #0072FF); border: 2px solid #FFFFFF;"
            content_inner = '''<div class="logo-popup-content"><span class="badge-icon">🚀</span><span class="badge-label">CONTENT CREATOR</span></div>'''
        elif asset_id in ["shy", "blush"]:
            bg_style = "background: transparent; border: none; box-shadow: none;"
            content_inner = '''<div class="emoji-big">😊</div>'''
        elif asset_id in ["shell"]:
            bg_style = "background: transparent; border: none; box-shadow: none;"
            content_inner = '''<div class="emoji-big">🐚</div>'''
        elif asset_id in ["fire"]:
            bg_style = "background: transparent; border: none; box-shadow: none;"
            content_inner = '''<div class="emoji-big">🔥</div>'''
        else:
            # Fallback general card
            label = trigger.upper() if trigger else asset_id.upper()
            content_inner = f'''<div class="logo-popup-content"><span class="badge-icon">✨</span><span class="badge-label">{label}</span></div>'''

        item_html = f'''      <div id="{elem_id}" class="overlay-element anim-{anim}" 
           style="top: {y}px; left: {x}px; width: {width}px; min-height: {height}px; {bg_style}" 
           data-start="{start:.3f}" data-duration="{duration:.3f}" data-layout-allow-safe-zone>
        {content_inner}
      </div>'''
        elements_html.append(item_html)

    # 3. Default CTA Card (last 3 seconds)
    cta_start = max(0.0, video_duration - 3.0)
    elements_html.append(f'''      <!-- Bottom CTA Banner -->
      <div id="cta-banner" class="overlay-element" data-start="{cta_start:.3f}" data-duration="2.950" data-layout-allow-safe-zone>
        <span class="cta-arrow">👇</span>
        <span class="cta-text">FOLLOW FOR MORE</span>
        <span class="cta-arrow">👇</span>
      </div>''')

    # 4. Audio SFX elements
    sfx_durations = {
        "vine_boom": 0.5, "bruh": 0.6, "bubble_pop": 0.1, "cash_register": 0.3,
        "whoosh": 0.25, "bell_chime": 0.6, "level_up": 0.5, "sad_trombone": 0.8,
        "pop": 0.12, "ding": 1.2
    }

    for i, s in enumerate(sound_effects):
        if isinstance(s, dict):
            s_id = s.get("asset_id", "pop")
            start = float(s.get("start", 0.0))
        else:
            s_id = s.asset_id
            start = s.start
        
        dur = sfx_durations.get(s_id, 0.3)
        audio_item = f'''    <audio id="sfx_{i}_{s_id}" src="../assets/{s_id}.wav" preload="auto" data-start="{start:.3f}" data-duration="{dur:.3f}"></audio>'''
        audio_html.append(audio_item)

    all_elements = "\n".join(elements_html)
    all_audio = "\n".join(audio_html)

    html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080, height=1920">
    <title>Overlays</title>
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

      .overlay-element {{
        position: absolute;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 24px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), 0 0 20px rgba(255, 230, 0, 0.25);
        opacity: 0;
        z-index: 50;
      }}

      /* Hook Card at top */
      #hook-card {{
        top: 240px;
        left: 50%;
        transform: translateX(-50%);
        width: 860px;
        height: 88px;
        background: #FFE600;
        color: #0D0E13;
        gap: 16px;
        border: 3px solid #FFFFFF;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(255, 230, 0, 0.5);
      }}

      .hook-emoji {{
        font-size: 42px;
      }}

      .hook-text {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 50px;
        letter-spacing: 0.04em;
        line-height: 1;
      }}

      /* CTA Banner at bottom */
      #cta-banner {{
        bottom: 240px;
        left: 50%;
        transform: translateX(-50%);
        width: 860px;
        height: 96px;
        background: linear-gradient(90deg, #FFE600, #FFB800);
        color: #0D0E13;
        gap: 20px;
        border: 3px solid #FFFFFF;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.9), 0 0 40px rgba(255, 230, 0, 0.6);
      }}

      .cta-arrow {{
        font-size: 46px;
        animation: bounce 1s infinite alternate;
      }}

      .cta-text {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 56px;
        letter-spacing: 0.05em;
        line-height: 1;
      }}

      .logo-popup-content {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 28px;
        color: #FFFFFF;
      }}

      .badge-icon {{
        font-size: 38px;
      }}

      .badge-label {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 44px;
        letter-spacing: 0.03em;
        line-height: 1;
      }}

      .emoji-big {{
        font-size: 110px;
        filter: drop-shadow(0 12px 24px rgba(0, 0, 0, 0.7));
      }}

      @keyframes bounce {{
        0% {{ transform: translateY(0); }}
        100% {{ transform: translateY(8px); }}
      }}
    </style>
  </head>
  <body>
    <div id="root">
{all_elements}
    </div>

{all_audio}

    <script>
      // GSAP In/Out animations for overlays
      document.querySelectorAll('.overlay-element').forEach((el) => {{
        const start = parseFloat(el.getAttribute('data-start') || '0');
        const dur = parseFloat(el.getAttribute('data-duration') || '1');
        
        // Elastic spring-in
        gsap.timeline()
          .fromTo(el,
            {{ opacity: 0, scale: 0.4, y: 30 }},
            {{ opacity: 1, scale: 1, y: 0, duration: 0.35, ease: "back.out(1.8)", delay: start }}
          )
          .to(el,
            {{ opacity: 0, scale: 0.8, y: -20, duration: 0.2, ease: "power2.in", delay: Math.max(0, dur - 0.55) }}
          );
      }});
    </script>
  </body>
</html>'''
    return html
