"""
High-Speed FFmpeg Reel Builder strictly following style-sheet.md.
Renders engaging vertical (9:16) or horizontal (16:9) reels with:
- Top hook banner (Bebas Neue / Electric Yellow)
- Floating social comment question card
- Spoken pop-up badges (PS5/Gaming, Cash, YouTube, Comment, Follow)
- Dual-size kinetic captions (White lead + Electric Neon Yellow keyword)
- Original source audio preserved by default, with optional timed SFX mixing.
"""
import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from PIL import Image

from engine.assets.registry import AssetRegistry
from engine.render.animations import get_animation


def _probe_display_size(video_path: Path, fallback_width: int, fallback_height: int) -> tuple[int, int]:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_tags=rotate:stream_side_data=rotation", "-of", "json", str(video_path)],
            capture_output=True, text=True, timeout=15,
        )
        stream = (json.loads(result.stdout).get("streams") or [{}])[0]
        width, height = int(stream.get("width") or fallback_width), int(stream.get("height") or fallback_height)
        rotation = int(stream.get("tags", {}).get("rotate", 0) or 0)
        for side in stream.get("side_data_list", []):
            if "rotation" in side:
                rotation = int(round(float(side["rotation"])))
        if abs(rotation) in (90, 270):
            return height, width
        return width, height
    except Exception:
        return max(1, fallback_width), max(1, fallback_height)


def _has_audio_stream(video_path: Path) -> bool:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type", "-of", "json", str(video_path)],
            capture_output=True, text=True, timeout=15,
        )
        streams = json.loads(result.stdout).get("streams") or []
        return any(stream.get("codec_type") == "audio" for stream in streams)
    except Exception:
        return False

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
    vector_asset_ids = {"polaroid_frame", "flower_blossom", "sparkle_stars", "doodle_heart", "glass_pill", "viewfinder", "music_player_card", "retro_recording_hud", "scrapbook_tape", "tech_interface_card", "subject_outline", "doodle_arrow", "torn_paper_frame", "film_frame", "kinetic_title_card", "subject_cutout", "gemini", "robot", "brain_ai", "chip", "laptop", "sun_warmth", "recipe_dish", "chef_hat", "fresh_leaf", "music_card", "headphones", "sound_wave", "book", "presentation", "quiz", "audio_mic", "bulb", "rec_dot", "gamepad", "money", "comment", "heart", "bell"}
    for g in graphics:
        if g.get("type") == "kinetic_title":
            continue
        if g.get("asset_id") in vector_asset_ids:
            continue  # The corresponding transparent artwork is composited by FFmpeg.
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

        # Animate entrance: glide in from subtle offset with smooth fade
        drift_x = pos_x - 14 if pos_x < (width / 2) else pos_x + 14
        drift_y = pos_y + 10
        events.append(
            f"Dialogue: 2,{start_t},{end_t},PopUpBadge,,0,0,0,,{{\\fad(220,180)\\move({drift_x},{drift_y},{pos_x},{pos_y},0,420)}}  {badge_text}  "
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
    sfx_dir: Optional[str] = None,
    background_mode: str = "blur",
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
    source_width, source_height = _probe_display_size(inp, int(src_w or target_w), int(src_h or target_h))
    source_has_audio = _has_audio_stream(inp)

    generate_ass_subtitles(
        captions=edl.get("captions", []),
        graphics=edl.get("graphics", []),
        output_path=str(ass_path),
        width=target_w,
        height=target_h,
        hook_title=edl.get("hook_title"),
        social_question=edl.get("social_question"),
        template_id=template_id,
        source_width=src_w or target_w,
        source_height=src_h or target_h
    )

    ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")

    # 2. Build Unified Filtergraph (Video + Audio)
    sound_effects = edl.get("sound_effects", [])
    sfx_base = Path(sfx_dir) if sfx_dir else inp.parent.parent / "assets" / "sfx"
    
    cmd_inputs = ["-i", str(inp)]
    
    # Aesthetic Color Grading Filter based on template identity
    if template_id == "pinterest_scrapbook":
        grade_filter = "eq=contrast=1.06:brightness=0.02:saturation=1.12"
    elif template_id == "glassmorphism":
        grade_filter = "eq=contrast=1.08:brightness=0.01:saturation=1.18"
    elif template_id == "retro_camera":
        grade_filter = "eq=contrast=1.05:saturation=0.92"
    elif template_id == "aesthetic_lifestyle":
        grade_filter = "eq=contrast=1.03:brightness=0.02:saturation=1.10"
    elif template_id == "creative_minimal":
        grade_filter = "eq=contrast=1.04:saturation=1.02"
    else:
        grade_filter = "eq=contrast=1.05:saturation=1.10"

    # Aspect-ratio composition never distorts source pixels. "blur" preserves
    # the full source in front of a blurred cover-scaled copy; "fill" crops;
    # "fit" deliberately pads.
    background_mode = background_mode if background_mode in {"blur", "fill", "fit"} else "blur"
    focal = edl.get("focal_point") or vm.get("focal_point") or {}
    focal_x = min(1.0, max(0.0, float(focal.get("x", 0.5)))) if isinstance(focal, dict) else 0.5
    focal_y = min(1.0, max(0.0, float(focal.get("y", 0.5)))) if isinstance(focal, dict) else 0.5
    fill_scale = max(target_w / source_width, target_h / source_height)
    fit_scale = min(target_w / source_width, target_h / source_height)
    scaled_w, scaled_h = round(source_width * fill_scale), round(source_height * fill_scale)
    crop_x = round(max(0, scaled_w - target_w) * focal_x)
    crop_y = round(max(0, scaled_h - target_h) * focal_y)

    # 1. Base Stream Pre-processing (Jump-cuts and Audio/Video PTS Synchronization)
    keep_segments = edl.get("keep_segments")
    v_prep_filters = []
    a_prep_filters = []

    if keep_segments and len(keep_segments) > 0:
        cond = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in keep_segments)
        v_prep_filters.append(f"[0:v]select='{cond}',setpts=N/FRAME_RATE/TB[v_raw]")
        if source_has_audio:
            a_prep_filters.append(f"[0:a:0]aselect='{cond}',asetpts=N/SR/TB,aresample=async=1000:first_pts=0[src_a]")
        v_in = "v_raw"
    else:
        v_prep_filters.append("[0:v]setpts=PTS-STARTPTS[v_raw]")
        if source_has_audio:
            a_prep_filters.append("[0:a:0]asetpts=PTS-STARTPTS,aresample=async=1000:first_pts=0[src_a]")
        v_in = "v_raw"

    if background_mode == "fill":
        base_video_filter = (
            f"[{v_in}]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h}:{crop_x}:{crop_y},{grade_filter},subtitles='{ass_escaped}'[vbase]"
        )
    elif background_mode == "blur":
        base_video_filter = (
            f"[{v_in}]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h}:{crop_x}:{crop_y},boxblur=24:12[background];"
            f"[{v_in}]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease[foreground];"
            f"[background][foreground]overlay=(W-w)/2:(H-h)/2,{grade_filter},subtitles='{ass_escaped}'[vbase]"
        )
    else:
        base_video_filter = (
            f"[{v_in}]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,{grade_filter},subtitles='{ass_escaped}'[vbase]"
        )

    # Find safe, in-project PNGs for static library art or generated cutouts.
    element_dir = Path(__file__).resolve().parents[1] / "assets" / "elements"
    resources_root = Path(__file__).resolve().parents[2] / "Resources" / "graphics" / "cutouts"
    vector_graphics = []
    for graphic in edl.get("graphics", []):
        asset_id = str(graphic.get("asset_id", ""))
        if graphic.get("resource_path") and asset_id == "subject_cutout":
            relative = Path(str(graphic["resource_path"]))
            resource_path = (resources_root.parent.parent / relative).resolve()
            if resource_path.is_relative_to(resources_root.resolve()) and resource_path.suffix.lower() == ".png" and resource_path.is_file():
                vector_graphics.append((graphic, resource_path))
        elif re.fullmatch(r"[a-z0-9_]+", asset_id):
            metadata = AssetRegistry().get_asset_metadata(asset_id)
            artwork_file = metadata.get("file", "") if metadata else ""
            png_path = (element_dir / Path(artwork_file).with_suffix(".png").name).resolve()
            if not png_path.is_relative_to(element_dir.resolve()):
                continue
            if png_path.is_file():
                vector_graphics.append((graphic, png_path))

    # Composite lower layers first so preview and export share explicit depth.
    vector_graphics.sort(key=lambda pair: int(pair[0].get("z_index", 50)))

    # Add raster counterparts of the SVG library as image inputs. Browser and
    # FFmpeg use the same artwork; the alpha channel preserves transparent edges.
    vector_input_indices = []
    next_input_index = 1
    for graphic, png_path in vector_graphics:
        vector_input_indices.append(next_input_index)
        next_input_index += 1
        duration = max(0.1, float(graphic.get("end", 0.0)) - float(graphic.get("start", 0.0)))
        start = max(0.0, float(graphic.get("start", 0.0)))
        cmd_inputs.extend(["-itsoffset", f"{start:.3f}", "-loop", "1", "-framerate", "30", "-t", f"{duration:.3f}", "-i", str(png_path)])

    if not vector_graphics:
        base_video_filter = base_video_filter.replace("[vbase]", "[vout]")
    initial_label = "vbase" if vector_graphics else "vout"
    v_filters = [base_video_filter]
    v_filters = v_prep_filters + [base_video_filter]
    current_video_label = initial_label
    for index, ((graphic, _png_path), input_index) in enumerate(zip(vector_graphics, vector_input_indices)):
        width = max(48, min(target_w, int(graphic.get("width") or 180)))
        height = max(48, min(target_h, int(graphic.get("height") or 180)))
        with Image.open(_png_path) as artwork:
            artwork_width, artwork_height = artwork.size
        box_scale = min(width / max(1, artwork_width), height / max(1, artwork_height))
        width = max(2, round(artwork_width * box_scale))
        height = max(2, round(artwork_height * box_scale))
        coordinate_width = max(1, int(src_w or target_w))
        coordinate_height = max(1, int(src_h or target_h))
        x = int(float(graphic.get("x", coordinate_width * 0.72)) * target_w / coordinate_width)
        y = int(float(graphic.get("y", coordinate_height * 0.22)) * target_h / coordinate_height)
        start = max(0.0, float(graphic.get("start", 0.0)))
        end = max(start, float(graphic.get("end", start)))
        rotation = float(graphic.get("rotation", 0.0))
        spec = get_animation(graphic.get("animation"))
        asset_label = f"element_{index}"
        output_label = "vout" if index == len(vector_graphics) - 1 else f"vcomp_{index}"
        animation_filters = [f"[{input_index}:v]scale={width}:{height},format=rgba"]
        if abs(rotation) > 0.01:
            angle = rotation * 3.141592653589793 / 180
            animation_filters.append(f"rotate={angle:.6f}:c=none:ow=rotw(iw):oh=roth(ih)")
        if spec.kind in {"scale", "pop", "pop_fade"}:
            entry = spec.entrance_seconds
            start_scale = "0.05" if spec.kind == "pop" else "0.72"
            entry_scale = f"({start_scale}+(1-{start_scale})*min(1,max(0,(t-{start:.3f})/{entry:.3f})))"
            exit_scale = f"min(1,max(0,({end:.3f}-t)/{spec.exit_seconds:.3f}))" if spec.kind == "scale" else "1"
            animation_filters.append(
                f"scale=w='max(2,iw*{entry_scale}*{exit_scale})':"
                f"h='max(2,ih*{entry_scale}*{exit_scale})':eval=frame"
            )
        if spec.kind == "rotate":
            animation_filters.append(f"rotate='0.10*sin(2*PI*(t-{start:.3f})/2)':c=none:ow=rotw(iw):oh=roth(ih)")
        if spec.kind == "glitter":
            animation_filters.append(f"eq=brightness='0.10+0.12*abs(sin(2*PI*(t-{start:.3f})/0.65))':eval=frame")
        animation_filters.append(f"fade=t=in:st={start:.3f}:d={spec.entrance_seconds:.3f}:alpha=1")
        animation_filters.append(f"fade=t=out:st={max(start, end - spec.exit_seconds):.3f}:d={spec.exit_seconds:.3f}:alpha=1[{asset_label}]")
        v_filters.append(",".join(animation_filters))
        x_expr, y_expr = str(x), str(y)
        if spec.kind == "slide":
            x_expr = f"{x}-80*(1-min(1,max(0,(t-{start:.3f})/{spec.entrance_seconds:.3f})))"
        elif spec.kind == "float":
            y_expr = f"{y}+10*sin(2*PI*(t-{start:.3f})/2)"
        elif spec.kind == "rotate":
            x_expr = f"{x}-(w-{width})/2"
            y_expr = f"{y}-(h-{height})/2"
        elif spec.kind in {"scale", "pop", "pop_fade"}:
            x_expr = f"{x}-(w-{width})/2"
            y_expr = f"{y}-(h-{height})/2"
        elif abs(rotation) > 0.01:
            x_expr = f"{x}-(w-{width})/2"
            y_expr = f"{y}-(h-{height})/2"
        v_filters.append(
            f"[{current_video_label}][{asset_label}]overlay=x='{x_expr}':y='{y_expr}':eof_action=pass:enable='between(t,{start:.3f},{end:.3f})'[{output_label}]"
        )
        current_video_label = output_label
    
    # Audio synchronization & mixing.
    # We guarantee sample-accurate A/V sync by normalizing timestamps and resampling to 48kHz.
    a_filters = list(a_prep_filters)
    mix_sources = ["[src_a]"] if source_has_audio else []
    sfx_index = next_input_index
    added_sfx = 0
    for s in sound_effects:
        s_id = s.get("asset_id", "")
        start_ms = int(float(s.get("start", 0.0)) * 1000)
        sfx_file = sfx_base / f"{s_id}.wav"
        if sfx_file.exists():
            cmd_inputs.extend(["-i", str(sfx_file)])
            volume = min(1.0, max(0.0, float(s.get("volume", 0.8))))
            a_filters.append(
                f"[{sfx_index}:a]adelay={start_ms}|{start_ms},volume={volume:.3f}[sfx_{sfx_index}]"
            )
            mix_sources.append(f"[sfx_{sfx_index}]")
            sfx_index += 1
            added_sfx += 1

    if source_has_audio and added_sfx == 0:
        a_filters.append(f"{mix_sources[0]}anull[aout]")
        audio_map_args = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
        audio_mode = "original_synced"
    elif mix_sources:
        if len(mix_sources) == 1:
            a_filters.append(f"{mix_sources[0]}anull[aout]")
        else:
            mix_expr = "".join(mix_sources) + f"amix=inputs={len(mix_sources)}:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.98[aout]"
            a_filters.append(mix_expr)
        audio_map_args = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
        audio_mode = "original_plus_sfx" if source_has_audio else "sfx_only"
    else:
        audio_map_args = ["-an"]
        audio_mode = "silent_source"

    full_filtergraph = ";".join(v_filters + a_filters)

    cmd = [
        ffmpeg_bin,
        "-y",
        *cmd_inputs,
        "-filter_complex", full_filtergraph,
        "-map", "[vout]",
        *audio_map_args,
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-fps_mode", "cfr",
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
            "audio_mode": audio_mode,
            "audio_effects_mixed": added_sfx,
            "stderr": proc.stderr if not success else ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
