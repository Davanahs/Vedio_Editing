"""
FastAPI Web Studio Server for Reel Editor.
Provides drag-and-drop video upload, interactive AI chat editor,
multi-aspect-ratio rendering (16:9 Horizontal, 9:16 Vertical, 1:1 Square),
and real-time playback.
"""
import os
import sys
import time
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

from engine.analysis.video_probe import probe_video
from engine.analysis.audio_extractor import extract_audio
from engine.providers.registry import get_transcription_provider, get_director_chain
from engine.director.director import generate_edl
from engine.assets.registry import AssetRegistry
from engine.pipeline import group_words_into_bursts
from engine.render.ffmpeg_reel_builder import render_reel_ffmpeg

app = FastAPI(title="Reel Editor AI Web Studio", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAW_DIR = _ROOT / "Raw Footage"
EXPORT_DIR = _ROOT / "Export"
SFX_DIR = _ROOT / "assets" / "sfx"
LOGOS_DIR = _ROOT / "assets" / "cache" / "logos"
from engine.templates.definitions import list_templates, get_template
from engine.analysis.scene_detector import detect_scenes
from engine.analysis.audio_segmenter import segment_audio_narration
from engine.analysis.frame_analyzer import extract_representative_frames, analyze_frames_multimodal
from engine.analysis.multimodal_synthesizer import synthesize_multimodal_plan

WEB_DIR = _ROOT / "engine" / "web"
RESOURCES_DIR = _ROOT / "Resources"

RAW_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
(RESOURCES_DIR / "images").mkdir(parents=True, exist_ok=True)
(RESOURCES_DIR / "audio").mkdir(parents=True, exist_ok=True)
(RESOURCES_DIR / "graphics").mkdir(parents=True, exist_ok=True)

app.mount("/media/raw", StaticFiles(directory=str(RAW_DIR)), name="raw_media")
app.mount("/media/export", StaticFiles(directory=str(EXPORT_DIR)), name="export_media")
app.mount("/media/sfx", StaticFiles(directory=str(SFX_DIR)), name="sfx_media")
app.mount("/media/logos", StaticFiles(directory=str(LOGOS_DIR)), name="logos_media")
app.mount("/media/resources", StaticFiles(directory=str(RESOURCES_DIR)), name="resources_media")
app.mount("/template_previews", StaticFiles(directory=str(WEB_DIR / "template_previews")), name="template_previews")

class ChatEditRequest(BaseModel):
    filename: str
    prompt: str = ""
    template: str = "auto_creative"
    style_preset: Optional[str] = None
    aspect_ratio: str = "16:9"
    additional_instructions: Optional[str] = ""
    resources: List[str] = []

class RenderRequest(BaseModel):
    filename: str
    edl: Dict[str, Any]
    aspect_ratio: str = "16:9"

@app.get("/", response_class=HTMLResponse)
async def serve_studio():
    index_html = WEB_DIR / "index.html"
    if index_html.exists():
        return HTMLResponse(content=index_html.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Reel Editor Studio loading...</h1>")

@app.get("/api/templates")
async def get_templates():
    return {"success": True, "templates": list_templates()}

@app.get("/api/status")
async def get_system_status():
    groq_ok = bool(os.getenv("GROQ_API_KEY", "").startswith("gsk_"))
    openrouter_ok = bool(os.getenv("OPENROUTER_API_KEY", "").startswith("sk-or-"))
    gemini_ok = bool(os.getenv("GEMINI_API_KEY", "").startswith("AIzaSy"))

    videos = []
    for f in RAW_DIR.glob("*.*"):
        if f.suffix.lower() in [".mp4", ".mov", ".webm", ".mkv"]:
            videos.append({
                "name": f.name,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "url": f"/media/raw/{f.name}"
            })

    return {
        "status": "ready",
        "groq_connected": groq_ok,
        "openrouter_connected": openrouter_ok,
        "gemini_connected": gemini_ok,
        "raw_videos": videos
    }

@app.get("/api/assets")
async def get_assets():
    reg = AssetRegistry(str(_ROOT))
    return {
        "success": True,
        "sfx": reg.list_available_sfx(),
        "logos": reg.list_available_logos(),
        "stickers": reg.list_available_stickers()
    }

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    safe_name = file.filename.replace(" ", "_")
    target_path = RAW_DIR / safe_name

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    probe = await probe_video(str(target_path))
    duration = float(probe.get("duration", 0.0))
    width = int(probe.get("width", 1920))
    height = int(probe.get("height", 1080))
    is_landscape = width >= height

    return {
        "success": True,
        "filename": safe_name,
        "url": f"/media/raw/{safe_name}",
        "duration": duration,
        "width": width,
        "height": height,
        "fps": probe.get("fps", 30),
        "recommended_aspect": "16:9" if is_landscape else "9:16"
    }

@app.post("/api/upload-resource")
async def upload_resource(file: UploadFile = File(...), category: Optional[str] = Form(None)):
    safe_name = file.filename.replace(" ", "_")
    ext = Path(safe_name).suffix.lower()

    if not category:
        if ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]:
            category = "images"
        elif ext in [".mp3", ".wav", ".aac", ".ogg", ".m4a"]:
            category = "audio"
        else:
            category = "graphics"

    dest_dir = RESOURCES_DIR / category
    dest_dir.mkdir(parents=True, exist_ok=True)
    target_path = dest_dir / safe_name

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_mb = round(target_path.stat().st_size / (1024 * 1024), 2)
    return {
        "success": True,
        "filename": safe_name,
        "category": category,
        "size_mb": size_mb,
        "url": f"/media/resources/{category}/{safe_name}"
    }

@app.get("/api/resources")
async def get_resources():
    items = []
    for cat in ["images", "audio", "graphics"]:
        cat_dir = RESOURCES_DIR / cat
        if cat_dir.exists():
            for f in cat_dir.glob("*.*"):
                items.append({
                    "filename": f.name,
                    "category": cat,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "url": f"/media/resources/{cat}/{f.name}"
                })
    return {"success": True, "resources": items}

@app.delete("/api/resource/{category}/{filename}")
async def delete_resource(category: str, filename: str):
    target = RESOURCES_DIR / category / filename
    if target.exists():
        target.unlink()
        return {"success": True, "deleted": filename}
    return JSONResponse(status_code=404, content={"success": False, "error": "Not found"})

@app.post("/api/chat-edit")
async def chat_edit(req: ChatEditRequest):
    video_path = RAW_DIR / req.filename
    if not video_path.exists():
        matches = list(RAW_DIR.glob(f"*{req.filename}*"))
        if matches:
            video_path = matches[0]
        else:
            raise HTTPException(status_code=404, detail=f"Video file {req.filename} not found.")

    t0 = time.perf_counter()

    # 1. Probe & Extract Audio
    probe = await probe_video(str(video_path))
    duration = float(probe.get("duration", 46.5))

    temp_audio = _ROOT / "engine" / "temp" / f"{video_path.stem}_audio.wav"
    temp_audio.parent.mkdir(parents=True, exist_ok=True)
    await extract_audio(str(video_path), str(temp_audio))

    # 2. Transcribe via Groq (with exact word timestamps)
    tx_provider = get_transcription_provider()
    tx_result = await tx_provider.transcribe(str(temp_audio))
    transcript_text = tx_result.text
    words_list = [{"word": w.word, "start": w.start, "end": w.end} for w in tx_result.words]
    caption_bursts = group_words_into_bursts(words_list)

    # 3. Multimodal Analysis: Scene Detection & Representative Frame Sampling
    scene_timestamps = await detect_scenes(str(video_path), threshold=0.4)
    frames_dir = _ROOT / "engine" / "temp" / "frames" / video_path.stem
    frame_tuples = extract_representative_frames(
        video_path=str(video_path),
        output_dir=frames_dir,
        scene_timestamps=scene_timestamps,
        interval_s=10.0,
        total_duration=duration
    )

    # 4. Multimodal Synthesis (Audio segments + Visual frame inspection)
    audio_segments = segment_audio_narration(words_list, duration)
    visual_analyses = await analyze_frames_multimodal(
        frame_tuples=frame_tuples,
        video_topic_hint=transcript_text[:150]
    )

    target_template = req.template or req.style_preset or "auto_creative"
    asset_reg = AssetRegistry(str(_ROOT))

    multimodal_plan = synthesize_multimodal_plan(
        audio_segments=audio_segments,
        visual_frames=visual_analyses,
        video_metadata={"duration": duration, "width": probe.get("width", 1920), "height": probe.get("height", 1080)},
        template_id=target_template,
        main_prompt=req.prompt,
        additional_instructions=req.additional_instructions or "",
        asset_registry=asset_reg
    )

    # 5. Directing with Context & User Prompts
    user_style_note = ""
    res_info = ""
    if req.resources:
        res_info = f"\nUser Uploaded Additional Resources Available: {', '.join(req.resources)}"
    if req.prompt or res_info:
        user_style_note = f"\n\nUSER PROMPT INSTRUCTIONS:\n'{req.prompt}'{res_info}\nTarget Aspect Ratio: {req.aspect_ratio}"

    target_w = 1920 if req.aspect_ratio == "16:9" else 1080
    target_h = 1080 if req.aspect_ratio == "16:9" else 1920

    edl = await generate_edl(
        transcript=transcript_text + user_style_note,
        caption_bursts=caption_bursts,
        video_metadata={"duration": duration, "width": target_w, "height": target_h},
        asset_registry=asset_reg,
        sfx_registry=asset_reg.list_available_sfx(),
        multimodal_plan=multimodal_plan,
        template_id=target_template,
        additional_instructions=req.additional_instructions or "",
    )

    edl_dict = edl.model_dump()
    elapsed = round(time.perf_counter() - t0, 2)

    # Generate friendly summary of decisions made
    graphics_list = [g.get("trigger_word", g.get("asset_id")) for g in edl_dict.get("graphics", [])]
    applied_tmpl = multimodal_plan.get("applied_template", {})
    ai_reply = (
        f"Multimodal AI synthesized your edit using **{applied_tmpl.get('name', target_template)}** template in **{req.aspect_ratio}** format! "
        f"Analyzed {len(audio_segments)} narrative audio segments and {len(visual_analyses)} video keyframes. "
        f"Generated {len(edl.captions)} contextual captions, {len(edl.graphics)} strictly relevant visual elements ({', '.join(graphics_list)}), "
        f"preserved {multimodal_plan.get('clean_segments_preserved', 0)} clean moments to prevent clutter, and synchronized {len(edl.sound_effects)} audio SFX."
    )

    return {
        "success": True,
        "edl": edl_dict,
        "transcript": transcript_text,
        "audio_segments": [seg.to_dict() for seg in audio_segments],
        "visual_frames": [vf.to_dict() for vf in visual_analyses],
        "multimodal_plan": multimodal_plan,
        "applied_template": applied_tmpl,
        "applied_instructions": req.additional_instructions or "",
        "caption_count": len(edl.captions),
        "graphics_count": len(edl.graphics),
        "sfx_count": len(edl.sound_effects),
        "ai_response": ai_reply,
        "processing_time_s": elapsed
    }

@app.post("/api/render")
async def render_video(req: RenderRequest):
    video_path = RAW_DIR / req.filename
    if not video_path.exists():
        matches = list(RAW_DIR.glob(f"*{req.filename}*"))
        if matches:
            video_path = matches[0]
        else:
            raise HTTPException(status_code=404, detail="Video file not found")

    timestamp = int(time.time())
    ratio_tag = req.aspect_ratio.replace(":", "x")
    out_filename = f"reel_{video_path.stem}_{ratio_tag}_{timestamp}.mp4"
    out_path = EXPORT_DIR / out_filename

    res = render_reel_ffmpeg(
        input_video=str(video_path),
        output_video=str(out_path),
        edl=req.edl,
        aspect_ratio=req.aspect_ratio,
        sfx_dir=str(SFX_DIR)
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=f"Render failed: {res.get('stderr') or res.get('error')}")

    size_mb = round(out_path.stat().st_size / (1024 * 1024), 2)

    return {
        "success": True,
        "export_filename": out_filename,
        "download_url": f"/api/download/{out_filename}",
        "file_size_mb": size_mb,
        "aspect_ratio": req.aspect_ratio
    }

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Direct forced file download with attachment headers."""
    file_path = EXPORT_DIR / filename
    if not file_path.exists():
        matches = list(EXPORT_DIR.glob(f"*{filename}*"))
        if matches:
            file_path = matches[0]
        else:
            raise HTTPException(status_code=404, detail="Exported video file not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("engine.server:app", host="127.0.0.1", port=5050, reload=False)
