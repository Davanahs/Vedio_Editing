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
    height: int = 1080
):
    """
    Generates an ASS subtitle file styled for the target resolution,
    implementing the Master Reel Editor Style Sheet specifications.
    """
    is_vertical = height > width
    
    # Fonts and sizing based on style-sheet.md
    font_hook = 46 if is_vertical else 36
    font_lead = 36 if is_vertical else 28
    font_kw = 78 if is_vertical else 56
    font_badge = 42 if is_vertical else 32
    font_card = 30 if is_vertical else 24

    margin_top_hook = 120 if is_vertical else 50
    margin_v_lead = 480 if is_vertical else 140
    margin_v_kw = 380 if is_vertical else 70

    ass_content = f"""[Script Info]
Title: Style-Sheet Master Reel
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopHook,Bebas Neue,{font_hook},&H000D0E13,&H000000FF,&H0000E6FF,&H0000E6FF,1,0,0,0,100,100,2,0,1,12,3,8,40,40,{margin_top_hook},1
Style: CommentCard,Inter,{font_card},&H00111111,&H000000FF,&H00FFFFFF,&H00FFFFFF,1,0,0,0,100,100,0,0,1,10,3,5,60,60,0,1
Style: PopUpBadge,Arial Black,{font_badge},&H0000E6FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,1,0,1,6,3,5,40,40,0,1
Style: Lead,Inter,{font_lead},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,60,60,{margin_v_lead},1
Style: Keyword,Arial Black,{font_kw},&H0000E6FF,&H000000FF,&H00000000,&HB0000000,1,0,0,0,100,100,2,0,1,6,3,2,50,50,{margin_v_kw},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    # 1. Top Hook Banner (Style Sheet Section 6 & 8)
    hook_title = "⚡ GTA 6 CLIPS • EARN MONEY 💰"
    for g in graphics:
        if g.get("type") == "kinetic_title" or "GTA" in g.get("trigger_word", ""):
            hook_title = f"⚡ {g.get('title', 'GTA 6 GAMING')} • EARN CASH 💰"
            break
    
    events.append(
        f"Dialogue: 0,0:00:00.20,0:00:05.50,TopHook,,0,0,{margin_top_hook},,  {hook_title}  "
    )

    # 2. Floating Social Comment / Question Card (Spring in ~3.8s to 8.5s)
    center_y_card = int(height * 0.38)
    center_x_card = int(width * 0.5)
    events.append(
        f"Dialogue: 1,0:00:03.80,0:00:08.50,CommentCard,,0,0,0,,{{\\pos({center_x_card},{center_y_card})}}  💬 @alex_clips: Can you actually earn from GTA 6 clips?  "
    )

    # 3. Dynamic Pop-Up Badges from Graphics list
    for g in graphics:
        if g.get("type") == "kinetic_title":
            continue
        start_t = format_ass_time(float(g.get("start", 0.0)))
        end_t = format_ass_time(float(g.get("end", 0.0)))
        word = g.get("trigger_word", "").upper()
        asset = g.get("asset_id", "")

        prefix = "✨ "
        if asset == "gamepad": prefix = "🎮 "
        elif asset == "money": prefix = "💰 "
        elif asset == "youtube": prefix = "🔴 "
        elif asset == "chatgpt": prefix = "🤖 "
        elif asset == "comment": prefix = "💬 "
        elif asset == "bell": prefix = "👇 "

        # Alternate positions (left / right) for dynamic visual balance
        pos_x = int(width * 0.72) if "YOUTUBE" in word or "GAME" in word else int(width * 0.28)
        pos_y = int(height * 0.44)

        events.append(
            f"Dialogue: 2,{start_t},{end_t},PopUpBadge,,0,0,0,,{{\\pos({pos_x},{pos_y})}}  {prefix}{word}  "
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
    generate_ass_subtitles(
        captions=edl.get("captions", []),
        graphics=edl.get("graphics", []),
        output_path=str(ass_path),
        width=target_w,
        height=target_h
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
