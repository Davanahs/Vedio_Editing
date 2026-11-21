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
import logging
import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

import cv2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

from engine.analysis.video_probe import probe_video
from engine.analysis.audio_extractor import extract_audio
from engine.providers.registry import get_transcription_provider, get_director_chain
from engine.director.director import generate_edl
from engine.director.validator import apply_plan_composition
from engine.assets.registry import AssetRegistry
from engine.pipeline import group_words_into_bursts
from engine.render.ffmpeg_reel_builder import render_reel_ffmpeg
from engine.assets.subject_cutout import create_subject_cutout

logger = logging.getLogger(__name__)

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
from engine.analysis.audio_signal import analyze_audio_signal
from engine.analysis.multimodal_synthesizer import synthesize_multimodal_plan
from engine.analysis.resource_analyzer import analyze_attached_resources
from engine.analysis.silence_cutter import (
    detect_gaps_from_words,
    detect_false_starts_and_repeats,
    compute_keep_segments,
    retime_edl,
)
from engine.director.edl_schema import EditDecisionList, ZoomEvent

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
app.mount("/media/elements", StaticFiles(directory=str(_ROOT / "engine" / "assets" / "elements")), name="creative_elements")
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
    remove_silence: bool = False
    silence_threshold_ms: int = 380
    cadence_zoom: bool = True
    remove_repeats: bool = True

class RenderRequest(BaseModel):
    filename: str
    edl: Dict[str, Any]
    aspect_ratio: str = "16:9"
    background_mode: str = "blur"

class SubjectCutoutRequest(BaseModel):
    filename: str
    timestamp: float = Field(ge=0)
    aspect_ratio: str = "9:16"
    outline_color: Optional[str] = None
    outline_width: int = Field(default=0, ge=0, le=64)

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
        "stickers": reg.list_available_stickers(),
        "elements": [
            {**metadata,
             "preview_url": f"/media/elements/{Path(metadata['file']).with_suffix('.png').name}",
             "previewable": True}
            for asset_id in reg.list_available_stickers()
            for metadata in [reg.get_asset_metadata(asset_id)]
            if metadata and metadata.get("file") and (_ROOT / "engine" / "assets" / metadata["file"]).is_file()
        ],
    }

@app.post("/api/subject-cutout")
async def make_subject_cutout(req: SubjectCutoutRequest):
    """Generate a transparent person cutout from the selected source-video frame."""
    filename = Path(req.filename).name
    if filename != req.filename or Path(filename).suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm"}:
        raise HTTPException(status_code=400, detail="Select a supported source video")
    source_path = (RAW_DIR / filename).resolve()
    if not source_path.is_relative_to(RAW_DIR.resolve()) or not source_path.is_file():
        raise HTTPException(status_code=404, detail="Source video not found")
    if req.aspect_ratio not in {"9:16", "16:9", "1:1"}:
        raise HTTPException(status_code=422, detail="Aspect ratio must be 9:16, 16:9, or 1:1")

    probe = await probe_video(str(source_path))
    timestamp = min(req.timestamp, max(0.0, float(probe.get("duration", 0.0)) - 0.04))
    capture = cv2.VideoCapture(str(source_path))
    try:
        capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
        ok, frame = capture.read()
    finally:
        capture.release()
    if not ok or frame is None:
        raise HTTPException(status_code=422, detail="Could not decode the selected video frame")

    cutout_id = uuid.uuid4().hex
    work_dir = _ROOT / "engine" / "temp" / "subject_cutouts"
    work_dir.mkdir(parents=True, exist_ok=True)
    frame_path = work_dir / f"{cutout_id}_source.jpg"
    resource_path = Path("graphics") / "cutouts" / f"subject_{cutout_id}.png"
    output_path = RESOURCES_DIR / resource_path
    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 96])
    try:
        result = await asyncio.to_thread(
            create_subject_cutout,
            frame_path,
            output_path,
            req.outline_color,
            req.outline_width,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        frame_path.unlink(missing_ok=True)

    if req.aspect_ratio == "16:9":
        canvas_w, canvas_h = 1920, 1080
    elif req.aspect_ratio == "1:1":
        canvas_w = canvas_h = 1080
    else:
        canvas_w, canvas_h = 1080, 1920
    graphic_width = int(canvas_w * 0.25)
    graphic_height = max(80, round(graphic_width * result["height"] / max(1, result["width"])))
    start = max(0.0, timestamp - 0.15)
    end = min(float(probe.get("duration", timestamp + 2.4)), timestamp + 2.4)
    graphic = {
        "id": f"subject_cutout_{cutout_id[:8]}",
        "asset_id": "subject_cutout",
        "resource_path": resource_path.as_posix(),
        "resource_url": f"/media/resources/{resource_path.as_posix()}",
        "start": start,
        "end": max(start + 0.1, end),
        "x": int(canvas_w * 0.68),
        "y": int(canvas_h * 0.18),
        "width": graphic_width,
        "height": graphic_height,
        "animation": "pop_fade",
        "title": "",
        "subtitle": "",
    }
    return {"success": True, "graphic": graphic, "cutout": result}

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
    allowed_extensions = {
        "images": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"},
        "audio": {".mp3", ".wav", ".aac", ".ogg", ".m4a", ".flac"},
        "graphics": {".svg", ".png"},
    }
    for cat in ["images", "audio", "graphics"]:
        cat_dir = RESOURCES_DIR / cat
        if cat_dir.exists():
            for f in cat_dir.iterdir():
                if not f.is_file() or f.name.startswith(".") or f.suffix.lower() not in allowed_extensions[cat]:
                    continue
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
    audio_path = None
    transcript_text = ""
    words_list: list[dict[str, Any]] = []
    transcription_status = "no_audio_stream"
    transcription_provider = None
    transcription_language = None
    if probe.get("has_audio", False):
        try:
            audio_path = await extract_audio(str(video_path), str(temp_audio))
            tx_provider = get_transcription_provider()
            tx_result = await tx_provider.transcribe(str(audio_path))
            transcript_text = tx_result.text or ""
            words_list = [
                {"word": w.word, "start": w.start, "end": w.end}
                for w in tx_result.words
            ]
            transcription_status = "complete"
            transcription_provider = tx_provider.name
            transcription_language = getattr(tx_result, "language", None)
        except Exception as exc:
            logger.warning("Audio extraction/transcription failed for %s: %s", video_path.name, type(exc).__name__)
            transcription_status = "failed"
    caption_bursts = group_words_into_bursts(words_list)
    audio_signal = analyze_audio_signal(
        str(audio_path) if audio_path else None,
        words_list,
    )

    # 3. Multimodal Analysis: Scene Detection & Representative Frame Sampling
    try:
        scene_timestamps = await detect_scenes(str(video_path), threshold=0.4)
    except Exception as exc:
        logger.warning("Scene detection failed for %s: %s", video_path.name, type(exc).__name__)
        scene_timestamps = []
    frames_dir = _ROOT / "engine" / "temp" / "frames" / video_path.stem
    try:
        max_frames = max(1, min(60, int(os.getenv("AURA_MAX_ANALYSIS_FRAMES", "24"))))
    except ValueError:
        max_frames = 24
    frame_tuples = extract_representative_frames(
        video_path=str(video_path),
        output_dir=frames_dir,
        scene_timestamps=scene_timestamps,
        interval_s=10.0,
        total_duration=duration,
        max_samples=max_frames,
    )

    # 4. Multimodal Synthesis (audio segments + visual frame inspection)
    audio_segments = segment_audio_narration(words_list, duration)
    audio_context = [segment.to_dict() for segment in audio_segments]
    resource_evidence = await asyncio.to_thread(analyze_attached_resources, req.resources, RESOURCES_DIR)
    visual_analyses = await analyze_frames_multimodal(
        frame_tuples=frame_tuples,
        video_topic_hint=transcript_text[:300],
        audio_segments=audio_context,
        max_samples=max_frames,
    )

    target_template = req.template or req.style_preset or "auto_creative"
    asset_reg = AssetRegistry(str(_ROOT))
    target_w, target_h = {
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
        "9:16": (1080, 1920),
    }[req.aspect_ratio]

    multimodal_plan = synthesize_multimodal_plan(
        audio_segments=audio_segments,
        visual_frames=visual_analyses,
        video_metadata={"duration": duration, "width": target_w, "height": target_h},
        template_id=target_template,
        main_prompt=req.prompt,
        additional_instructions=req.additional_instructions or "",
        asset_registry=asset_reg,
        available_resources=req.resources,
        resource_evidence=resource_evidence,
    )

    # 5. Directing with Context & User Prompts
    user_style_note = ""
    res_info = ""
    if req.resources:
        res_info = f"\nUser Uploaded Additional Resources Available: {', '.join(req.resources)}"
    if req.prompt or res_info:
        user_style_note = f"\n\nUSER PROMPT INSTRUCTIONS:\n'{req.prompt}'{res_info}\nTarget Aspect Ratio: {req.aspect_ratio}"

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
    director_validation: dict[str, Any] = {}
    edl = apply_plan_composition(edl, multimodal_plan, report=director_validation)
    edl = edl.model_copy(update={
        "template_id": multimodal_plan.get("applied_template", {}).get("id", target_template),
    })
    director_validation["template_id"] = edl.template_id
    director_validation["source_audio_preserved"] = bool(probe.get("has_audio")) and edl.music is None

    # 6. Smart Silence & Dead-Air Cutting (Automatic Jump-Cuts)
    should_cut_silence = req.remove_silence or any(
        k in (req.prompt + " " + (req.additional_instructions or "")).lower()
        for k in ["cut silence", "remove gap", "jump cut", "tighten", "dead air", "fast paced", "remove pause"]
    )
    cut_intervals = []
    keep_segments = None
    trimmed_seconds = 0.0

    if should_cut_silence and words_list:
        cut_intervals = detect_gaps_from_words(
            words_list,
            min_gap_s=max(0.25, float(req.silence_threshold_ms) / 1000.0),
            pad_s=0.065,
            total_duration=duration,
        )
        if req.remove_repeats:
            repeat_cuts = detect_false_starts_and_repeats(words_list)
            cut_intervals.extend(repeat_cuts)

        if cut_intervals:
            keep_segments = compute_keep_segments(duration, cut_intervals)
            raw_dict = edl.model_dump()
            retimed_dict = retime_edl(raw_dict, keep_segments)
            retimed_dict["keep_segments"] = keep_segments
            retimed_dict["jump_cuts"] = cut_intervals
            trimmed_seconds = round(duration - sum(e - s for s, e in keep_segments), 2)
            edl = EditDecisionList(**retimed_dict)
            logger.info("Smart Jump-Cuts: %d pauses trimmed (%.2fs dead air removed)", len(cut_intervals), trimmed_seconds)

    # 7. Cadence Face Punch Zoom
    if req.cadence_zoom:
        current_zooms = list(edl.zoom_events)
        edl_dur = float(edl.video_duration or duration)
        if not current_zooms:
            if edl_dur >= 7.0:
                current_zooms.append(ZoomEvent(
                    id="z_hook_punch",
                    start=1.0,
                    end=3.5,
                    scale=1.12,
                    target="face",
                    ease="back.out(1.2)"
                ))
            if edl_dur >= 16.0:
                current_zooms.append(ZoomEvent(
                    id="z_mid_punch",
                    start=min(edl_dur - 4.0, 11.0),
                    end=min(edl_dur - 1.0, 14.5),
                    scale=1.10,
                    target="face",
                    ease="power2.inOut"
                ))
            edl = edl.model_copy(update={"zoom_events": current_zooms})

    edl_dict = edl.model_dump()
    elapsed = round(time.perf_counter() - t0, 2)
    frame_dicts = [frame.to_dict() for frame in visual_analyses]
    segment_context = []
    for segment in audio_segments:
        overlapping = [
            frame for frame in frame_dicts
            if segment.start <= frame["timestamp"] <= segment.end
        ]
        if not overlapping and frame_dicts:
            nearest = min(frame_dicts, key=lambda frame: abs(frame["timestamp"] - segment.start))
            if abs(nearest["timestamp"] - segment.start) <= 5.0:
                overlapping = [nearest]
        segment_context.append({
            **segment.to_dict(),
            "visual_evidence": [
                {
                    "timestamp": frame["timestamp"],
                    "summary": frame.get("visual_summary") or frame.get("subject_activity", ""),
                    "objects": frame.get("objects_detected", []),
                    "setting": frame.get("setting_environment", ""),
                    "spoken_topics": frame.get("spoken_topics", []),
                    "mentioned_entities": frame.get("mentioned_entities", []),
                    "face_positions": frame.get("normalized_faces", []),
                    "provider": frame.get("analysis_provider", "unknown"),
                    "status": frame.get("analysis_status", "unknown"),
                }
                for frame in overlapping
            ],
            "model_topics": sorted({
                topic
                for frame in overlapping
                for topic in frame.get("spoken_topics", [])
            }),
            "mentioned_entities": sorted({
                entity
                for frame in overlapping
                for entity in frame.get("mentioned_entities", [])
            }),
        })
    analysis_report = {
        "schema_version": "1.0",
        "source": {
            "filename": video_path.name,
            "duration": duration,
            "width": probe.get("width"),
            "height": probe.get("height"),
            "fps": probe.get("fps"),
            "rotation": probe.get("rotation", 0),
            "has_audio": bool(probe.get("has_audio")),
        },
        "transcription": {
            "status": transcription_status,
            "provider": transcription_provider,
            "language": transcription_language,
            "text": transcript_text,
            "words": words_list,
        },
        "audio_signal": audio_signal,
        "scene_changes": scene_timestamps,
        "frames": frame_dicts,
        "segments": segment_context,
        "attached_resources": resource_evidence,
        "vision_providers_used": sorted({frame["analysis_provider"] for frame in frame_dicts}),
    }

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
        "visual_frames": frame_dicts,
        "analysis_report": analysis_report,
        "multimodal_plan": multimodal_plan,
        "director_validation": director_validation,
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
        sfx_dir=str(SFX_DIR),
        background_mode=req.background_mode,
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=f"Render failed: {res.get('stderr') or res.get('error')}")

    size_mb = round(out_path.stat().st_size / (1024 * 1024), 2)

    return {
        "success": True,
        "export_filename": out_filename,
        "download_url": f"/api/download/{out_filename}",
        "file_size_mb": size_mb,
        "aspect_ratio": req.aspect_ratio,
        "audio_mode": res.get("audio_mode", "unknown"),
        "audio_effects_mixed": res.get("audio_effects_mixed", 0),
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
