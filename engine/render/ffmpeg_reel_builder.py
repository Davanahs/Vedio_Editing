"""
High-Speed FFmpeg Reel Builder strictly following style-sheet.md.
Renders engaging vertical (9:16) or horizontal (16:9) reels with:
- Top hook banner (Bebas Neue / Electric Yellow)
- Floating social comment question card
- Spoken pop-up badges (PS5/Gaming, Cash, YouTube, Comment, Follow)
- Dual-size kinetic captions (White lead + Electric Neon Yellow keyword)
- Mastered voiceover audio with loudness normalization (-14 LUFS) and mixed SFX transients.
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"

def generate_ass_subtitles(
    captions: List[Dict[str, Any]], 
    graphics: List[Dict[str, Any]], 
    output_path: str, 
    width: int = 1920, 
    height: int = 1080,
    hook_title: Optional[str] = None,
    social_question: Optional[str] = None,
    template_id: str = "auto_creative",
    source_width: Optional[int] = None,
    source_height: Optional[int] = None
):
    """
    Generates an ASS subtitle file styled for the target resolution and creative template,
    implementing context-aware non-colliding layout and design specifications.
    """
    is_vertical = height > width
    src_w = source_width or width
    src_h = source_height or height
    scale_x = width / src_w if src_w > 0 else 1.0
    scale_y = height / src_h if src_h > 0 else 1.0
    
    # Fonts and sizing based on style-sheet & creative template
    font_hook = 44 if is_vertical else 34
    font_lead = 34 if is_vertical else 26
    font_kw = 72 if is_vertical else 50
    font_badge = 38 if is_vertical else 28
    font_card = 28 if is_vertical else 22

    margin_top_hook = 110 if is_vertical else 45
    margin_v_lead = 460 if is_vertical else 130
    margin_v_kw = 360 if is_vertical else 60

    # Template-specific color and font palette
    # Colors in ASS are &HAABBGGRR (hex with Alpha, Blue, Green, Red)
    if template_id == "pinterest_scrapbook":
        hook_font = "Georgia"
        hook_primary = "&H00182436"  # warm mocha
        hook_outline = "&H00DDEEFF"  # warm cream
        hook_back = "&H00DDEEFF"
        badge_font = "Georgia"
        badge_primary = "&H00182436"
        badge_outline = "&H00FFFFFF" # polaroid white frame
        badge_back = "&H80FFFFFF"
        kw_font = "Georgia"
        kw_color = "&H003DB5FF"      # warm amber-gold
    elif template_id == "glassmorphism":
        hook_font = "Inter"
        hook_primary = "&H00FFFFFF"
        hook_outline = "&H00D4B606"  # electric cyan
        hook_back = "&H801A1210"     # translucent dark glass
        badge_font = "Inter"
        badge_primary = "&H00FFFFFF"
        badge_outline = "&H00D4B606" # cyan rim
        badge_back = "&H80221812"    # frosted glass pill
        kw_font = "Arial Black"
        kw_color = "&H00D4B606"      # neon cyan
    elif template_id == "retro_camera":
        hook_font = "Consolas"
        hook_primary = "&H000000FF"  # rec red dot / white text
        hook_outline = "&H00FFFFFF"
        hook_back = "&HB0000000"
        badge_font = "Consolas"
        badge_primary = "&H0000FF00" # viewfinder green
        badge_outline = "&H00000000"
        badge_back = "&HB0000000"
        kw_font = "Consolas"
        kw_color = "&H0000FF00"      # HUD neon green
    elif template_id == "creative_minimal":
        hook_font = "Inter"
        hook_primary = "&H00FFFFFF"
        hook_outline = "&H80000000"  # discreet subtle border
        hook_back = "&H00000000"
        badge_font = "Inter"
        badge_primary = "&H00F5F5F5"
        badge_outline = "&H80000000"
        badge_back = "&H00000000"
        kw_font = "Inter"
        kw_color = "&H00FFFFFF"      # crisp pure white
    elif template_id == "aesthetic_lifestyle":
        hook_font = "Georgia"
        hook_primary = "&H00332233"
        hook_outline = "&H00F2E4EE"  # soft pastel lavender
        hook_back = "&H00F2E4EE"
        badge_font = "Georgia"
        badge_primary = "&H002A1E2A"
        badge_outline = "&H00FFFFFF"
        badge_back = "&H80F8EFF5"
        kw_font = "Georgia"
        kw_color = "&H009966B3"      # soft lilac
    elif template_id == "floating_music_player":
        hook_font = "Inter"
        hook_primary = "&H00FFFFFF"
        hook_outline = "&H00333333"
        hook_back = "&H80181818"
        badge_font = "Inter"
        badge_primary = "&H00FFFFFF"
        badge_outline = "&H001DB954"  # subtle accent
        badge_back = "&H80202020"
        kw_font = "Inter"
        kw_color = "&H00FFFFFF"
    else:  # auto_creative default
        hook_font = "Bebas Neue"
        hook_primary = "&H000D0E13"
        hook_outline = "&H0000E6FF"
        hook_back = "&H0000E6FF"
        badge_font = "Arial Black"
        badge_primary = "&H0000E6FF"
        badge_outline = "&H00000000"
        badge_back = "&H80000000"
        kw_font = "Arial Black"
        kw_color = "&H0000E6FF"

    ass_content = f"""[Script Info]
Title: Style-Sheet Master Reel
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopHook,{hook_font},{font_hook},{hook_primary},&H000000FF,{hook_outline},{hook_back},1,0,0,0,100,100,2,0,1,8,2,8,40,40,{margin_top_hook},1
Style: CommentCard,Inter,{font_card},&H00111111,&H000000FF,&H00FFFFFF,&H00FFFFFF,1,0,0,0,100,100,0,0,1,8,2,5,60,60,0,1
Style: PopUpBadge,{badge_font},{font_badge},{badge_primary},&H000000FF,{badge_outline},{badge_back},1,0,0,0,100,100,1,0,1,6,3,5,40,40,0,1
Style: Lead,Inter,{font_lead},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,60,60,{margin_v_lead},1
Style: Keyword,{kw_font},{font_kw},{kw_color},&H000000FF,&H00000000,&HB0000000,1,0,0,0,100,100,2,0,1,6,3,2,50,50,{margin_v_kw},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    # 1. Top Hook Banner (dynamically inferred from EDL or graphics)
    if not hook_title:
        for g in graphics:
            if g.get("type") == "kinetic_title" or g.get("asset_id") == "kinetic_title":
                t = g.get("title") or g.get("trigger_word", "").replace("Title: ", "")
                if t:
                    hook_title = t.upper()
                break
    
    if hook_title:
        clean_title = hook_title.strip()
        if template_id == "retro_camera":
            formatted_hook = f"● REC  |  {clean_title}"
        elif template_id == "pinterest_scrapbook":
            formatted_hook = f"✂  {clean_title}  ✿"
        elif template_id == "creative_minimal":
            formatted_hook = f"{clean_title}"
        elif template_id == "glassmorphism":
            formatted_hook = f"◈ {clean_title} ◈"
        else:
            formatted_hook = f"⚡ {clean_title} ✦"

        events.append(
            f"Dialogue: 0,0:00:00.20,0:00:05.50,TopHook,,0,0,{margin_top_hook},,  {formatted_hook}  "
        )

    # 2. Contextual Social Question Card (Only if genuinely provided and safe)
    if social_question and "@alex_clips" not in social_question:
        safe_y = int(height * 0.18)
        center_x_card = int(width * 0.5)
        events.append(
            f"Dialogue: 1,0:00:03.80,0:00:08.50,CommentCard,,0,0,0,,{{\\pos({center_x_card},{safe_y})}}  {social_question}  "
        )

    # 3. Dynamic Pop-Up Badges from Graphics list using Collision Engine Placements
    for g in graphics:
        if g.get("type") == "kinetic_title":
            continue
        start_t = format_ass_time(float(g.get("start", 0.0)))
        end_t = format_ass_time(float(g.get("end", 0.0)))
        word = (g.get("title") or g.get("trigger_word", "")).upper()
        asset = g.get("asset_id", "")

        prefix = "✨ "
        if asset == "gamepad": prefix = "🎮 "
        elif asset in ["money", "cash"]: prefix = "💰 "
        elif asset == "youtube": prefix = "🔴 "
        elif asset in ["chatgpt", "robot"]: prefix = "🤖 "
        elif asset == "comment": prefix = "💬 "
        elif asset in ["bell", "ding"]: prefix = "🔔 "
        elif asset == "gemini": prefix = "✨ "
        elif asset == "book": prefix = "📚 "
        elif asset == "presentation": prefix = "📊 "
        elif asset == "quiz": prefix = "📝 "
        elif asset == "audio_mic": prefix = "🎙️ "
        elif asset == "heart": prefix = "❤️ "
        elif asset == "star": prefix = "⭐ "
        elif asset == "polaroid_frame": prefix = "📷 "
        elif asset == "flower_blossom": prefix = "🌸 "
        elif asset == "sparkle_stars": prefix = "⭐ "
        elif asset == "doodle_heart": prefix = "💖 "
        elif asset == "sun_warmth": prefix = "☀️ "
        elif asset == "recipe_dish": prefix = "🍲 "
        elif asset == "chef_hat": prefix = "👨‍🍳 "
        elif asset == "fresh_leaf": prefix = "🌿 "
        elif asset == "music_card": prefix = "🎵 "
        elif asset == "headphones": prefix = "🎧 "
        elif asset == "sound_wave": prefix = "〰️ "
        elif asset == "laptop": prefix = "💻 "
        elif asset == "glass_pill": prefix = "🔲 "
        elif asset == "viewfinder": prefix = "🎯 "
        elif asset == "rec_dot": prefix = "🔴 "
        elif asset == "brain_ai": prefix = "🧠 "
        elif asset == "chip": prefix = "⚡ "

        # Respect SafeZone collision engine coordinates
        raw_x = g.get("x")
        raw_y = g.get("y")
        if raw_x is not None and raw_y is not None:
            pos_x = int(float(raw_x) * scale_x)
            pos_y = int(float(raw_y) * scale_y)
        else:
            # Safe side placement outside center face box
            pos_x = int(width * 0.78) if ("YOUTUBE" in word or "GAME" in word or "STUDY" in word or "PPT" in word) else int(width * 0.22)
            pos_y = int(height * 0.28)

        # Style-specific badge format
        if template_id == "retro_camera":
            badge_text = f"[{word}]"
        elif template_id == "creative_minimal":
            badge_text = f"{word}"
        elif template_id == "pinterest_scrapbook":
            badge_text = f"{prefix}{word} ✿"
        else:
            badge_text = f"{prefix}{word}"

        events.append(
            f"Dialogue: 2,{start_t},{end_t},PopUpBadge,,0,0,0,,{{\\pos({pos_x},{pos_y})}}  {badge_text}  "
        )

    # 4. Spoken Dynamic Captions (Two-tone White + Electric Yellow)
    for c in captions:
        start_t = format_ass_time(float(c.get("start", 0.0)))
        end_t = format_ass_time(float(c.get("end", 0.0)))
        lead = c.get("lead", "").strip()
        keyword = c.get("keyword", "").strip()

        if lead:
            events.append(f"Dialogue: 3,{start_t},{end_t},Lead,,0,0,{margin_v_lead},,{lead}")
        if keyword:
            events.append(f"Dialogue: 4,{start_t},{end_t},Keyword,,0,0,{margin_v_kw},,{keyword}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content + "\n".join(events))


def render_reel_ffmpeg(
    input_video: str,
    output_video: str,
    edl: Dict[str, Any],
    aspect_ratio: str = "16:9",
    sfx_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Renders the complete video into the target aspect ratio (16:9, 9:16, 1:1)
    with pop-up cards, subtitles, speech loudness normalization (-14 LUFS), and mixed SFX.
    """
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    inp = Path(input_video).resolve()
    out = Path(output_video).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # Resolution mapping
    if aspect_ratio == "16:9":
        target_w, target_h = 1920, 1080
    elif aspect_ratio == "1:1":
        target_w, target_h = 1080, 1080
    else:  # default 9:16
        target_w, target_h = 1080, 1920

    # 1. Generate ASS Subtitle & Graphic Overlays File
    temp_dir = out.parent / ".temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    ass_path = temp_dir / f"{out.stem}_master.ass"
    
    template_id = edl.get("template_id") or edl.get("metadata", {}).get("template_id") or "auto_creative"
    vm = edl.get("video_metadata") or {}
    src_w = vm.get("width")
    src_h = vm.get("height")

    generate_ass_subtitles(
        captions=edl.get("captions", []),
        graphics=edl.get("graphics", []),
        output_path=str(ass_path),
        width=target_w,
        height=target_h,
        hook_title=edl.get("hook_title"),
        social_question=edl.get("social_question"),
        template_id=template_id,
        source_width=src_w,
        source_height=src_h
    )

    ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")

    # 2. Build Unified Filtergraph (Video + Audio)
    sound_effects = edl.get("sound_effects", [])
    sfx_base = Path(sfx_dir) if sfx_dir else inp.parent.parent / "assets" / "sfx"
    
    cmd_inputs = ["-i", str(inp)]
    
    # Video Filter: Scale, Pad, and Burn Stylized Visual Layer
    v_filters = [
        f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,subtitles='{ass_escaped}'[vout]"
    ]
    
    # Audio Filters: Master dialogue with loudness normalization to -14 LUFS (Style Sheet Section 7)
    a_filters = ["[0:a]loudnorm=I=-14:TP=-1.0:LRA=7,volume=1.4[main_a]"]
    mix_sources = ["[main_a]"]

    sfx_index = 1
    for s in sound_effects:
        s_id = s.get("asset_id", "")
        start_ms = int(float(s.get("start", 0.0)) * 1000)
        sfx_file = sfx_base / f"{s_id}.wav"
        if sfx_file.exists():
            cmd_inputs.extend(["-i", str(sfx_file)])
            a_filters.append(
                f"[{sfx_index}:a]adelay={start_ms}|{start_ms},volume=0.9[sfx_{sfx_index}]"
            )
            mix_sources.append(f"[sfx_{sfx_index}]")
            sfx_index += 1

    if len(mix_sources) > 1:
        mix_expr = "".join(mix_sources) + f"amix=inputs={len(mix_sources)}:dropout_transition=2:normalize=0[aout]"
        a_filters.append(mix_expr)
    else:
        a_filters.append("[main_a]acopy[aout]")

    full_filtergraph = ";".join(v_filters + a_filters)

    cmd = [
        ffmpeg_bin,
        "-y",
        *cmd_inputs,
        "-filter_complex", full_filtergraph,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-shortest",
        str(out)
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        success = (proc.returncode == 0) and out.exists() and out.stat().st_size > 0
        return {
            "success": success,
            "output_path": str(out),
            "file_size": out.stat().st_size if out.exists() else 0,
            "stderr": proc.stderr if not success else ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
