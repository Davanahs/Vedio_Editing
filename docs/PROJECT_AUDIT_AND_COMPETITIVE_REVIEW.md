# Project Audit and Competitive Review

**Reviewed:** 21 November 2026  
**Scope:** repository structure, FastAPI studio, editing pipeline, EDL, renderer, UI, included HyperFrames project and MP4 render, project documentation, and current public product documentation for ChatCut, Descript, CapCut, and OpusClip.

## Executive summary

Aura/Reel Editor has a useful foundation for an AI-assisted short-form editor: a self-hostable Python/FastAPI app, prompt-to-EDL generation, transcription and frame analysis, template definitions, an FFmpeg export path, and a separate HyperFrames composition sample. Today it is closer to an AI edit generator/demo than a dependable nonlinear editor.

The main gap is the handoff from AI plan to reviewable, editable, trustworthy output. The UI presents a multitrack timeline and claims mastered music and sidechain ducking, but timeline clips only seek the preview, and the FFmpeg renderer ignores EDL music and zoom events. The included rendered sample also has a major framing issue: the vertical export uses a short, wide video band centered in a large empty canvas. These gaps make the output hard to refine and the app’s preview/status labels unreliable.

**Recommendation:** first make framing, preview/export parity, and audio truthful and predictable. Next add safe editing controls and resilient job handling. Then invest in broader AI features and marketing claims.

## What is in the repository

| Area | Main files | Role |
|---|---|---|
| Web app | engine/server.py, engine/web/index.html | FastAPI API and a single-file HTML/CSS/JS studio UI |
| Analysis | engine/analysis/ | Video probing, audio extraction, scene detection, frame sampling, face detection, audio segmentation, multimodal planning |
| AI providers | engine/providers/ | Groq transcription, local Whisper fallback, Gemini/OpenRouter director providers, local heuristic director |
| Edit plan | engine/director/ | Pydantic EDL schema, prompt construction, validation, provider orchestration |
| Templates/assets | engine/templates/, engine/assets/, assets/ | Template specifications, sound effects, logo and asset registry |
| Export | engine/render/ffmpeg_reel_builder.py | FFmpeg crop/pad, ASS captions/graphics, audio processing and MP4 export |
| Persistence/queue scaffolding | engine/db/, engine/task_queue/, docker-compose.yml | SQL migration/models and optional PostgreSQL/Redis/Celery scaffolding |
| Separate composition sample | my-video/ | HyperFrames HTML/GSAP project and assets |
| Documentation | README.md, PROJECT_DETAILS.md, docs/, style-sheet.md | Product claims, setup, architecture notes, style rules, and performance claims |

The Python studio and my-video are separate editing paths. The web server serves engine/web/index.html; the included MP4 is rendered from the HyperFrames project. The sample MP4 should not be treated as proof that the FastAPI editor exports the same composition.

## Runtime and render review

The local site was already listening on port 5050. The root page returned HTTP 200 and /api/status returned ready, with four source videos listed. A second server launch failed because that port was already occupied, so I used the running app and did not start a duplicate. I reviewed the served HTML and sampled the included my-video/renders/my-video_2026-11-18_11-21-30.mp4.

### Included render facts

- 46.6 seconds, 1080×1920, 30 fps, H.264 video and stereo AAC audio.
- A sampled frame at 12 seconds shows the speaker footage in a wide horizontal band across the middle of the portrait canvas. Large areas above and below are unused patterned background.
- The speaker and caption remain legible in the sampled frame, but the subject uses a small share of the vertical canvas. The treatment reads like a landscape clip placed inside a portrait card, rather than a portrait-first reframe.
- The HTML composition declares a 50.85-second duration and places the CTA at 47.85 seconds, later than the MP4’s 46.6-second duration. That CTA cannot appear in this render.
- This is one sampled frame and one included render, not a quality assessment of every source, template, or FastAPI export.

### Website observations

The studio has resource upload, template cards, prompt entry, original/edited view modes, a preview, a timeline display, and export controls. Several controls overstate the editing model:

- Timeline rows are populated from the EDL and clicking a clip seeks to its start. I found no clip drag, trim, split, delete, or edit operation on the timeline.
- The edited preview draws browser-side overlays; export reconstructs graphics and captions through a separate FFmpeg/ASS path. Those are separate implementations with no evident shared renderer or parity check.
- The original/edited toggle changes overlay visibility. It does not switch to a separately rendered output.
- The UI claims “-14 LUFS Mastered Audio Track” and “Sidechain Ducking Active”; the export path has no background music input or sidechain filter.
- Template descriptions promise distinct scrapbook, floating player, glass, and retro treatments. The FFmpeg path applies a small set of color filters and renders graphics as ASS text/emoji; it does not render the template compositions or their described animations.

## How an edit currently flows

1. Upload or select a source in Raw Footage/.
2. POST /api/chat-edit probes it, extracts audio, transcribes it, groups words into caption bursts, detects scenes, extracts representative frames, analyzes frames, synthesizes a multimodal plan, and asks a director provider to create an EDL.
3. The browser receives the EDL and paints a preview and timeline representation.
4. POST /api/render passes the source and EDL to render_reel_ffmpeg, which creates an ASS subtitle/graphics file, builds an FFmpeg filter graph, and writes an MP4 in Export/.

The EDL is a promising boundary for future editing, but the renderer only consumes part of it. It currently renders captions, graphics, sound effects, hook/social text, aspect ratio, and a template color filter. It does not apply zoom_events, the music object, or color_grade. The timeline is not yet an editor for this plan.

## Prioritized findings

### P0 — fix before claiming dependable exports

1. **Portrait framing wastes the canvas.**  
   my-video/index.html positions the footage at 960×544 inside a 1080×1920 canvas, which explains the wide-band composition in the sampled render. The web renderer also uses force_original_aspect_ratio=decrease followed by black padding, so landscape footage will remain letterboxed for 9:16 exports unless users can choose and adjust a crop or subject-aware reframe. Add explicit fill, fit, and blurred-background modes, a crop/focal point, and a preview that matches export.

2. **Preview and exported video are different products.**  
   Browser overlay code and FFmpeg subtitle/graphic generation are separate renderers. A user can approve one composition and receive another. Share a normalized composition model and renderer rules; at minimum, create a parity checklist with representative preview/render screenshots for every supported aspect ratio and template.

3. **Audio labels do not match the render.**  
   The FFmpeg builder normalizes source audio and mixes SFX. It has no BGM input, no ducking, and no limiter after the subsequent volume=1.4 gain. The UI advertises mastering and sidechain ducking anyway. Implement music selection, speech-aware ducking, and final loudness/true-peak measurement. Otherwise remove the claims and controls until implemented.

4. **The included composition’s duration and CTA disagree.**  
   my-video/index.html declares 50.85 seconds and the CTA begins at 47.85 seconds; the shipped render lasts 46.6 seconds. Drive composition duration from source/render metadata and validate every timed element against it before rendering.

5. **Uploads and file APIs need path and size controls before network exposure.**  
   Upload endpoints derive file paths from client-supplied filenames with only spaces replaced. Resource category and filename are also used in filesystem paths; resource deletion and downloads are unauthenticated. This is unsafe if the service is reachable by another user or exposed outside localhost. Generate server-side IDs, validate file types and sizes, constrain resolved paths to intended directories, validate categories, and add authentication/authorization before deploying beyond a trusted local machine. The Dockerfile binds to 0.0.0.0; do not treat the development server as a production boundary.

### P1 — make edits controllable and jobs reliable

6. **The timeline is display-and-seek only.**  
   The interface resembles a multitrack editor, but has no edit operations or undo. Add direct caption timing/text edits, graphic timing/placement edits, SFX changes, trim/split/delete, undo/redo, and a clear regenerate-plan action. Keep generated changes reversible.

7. **Long operations have no durable job model or progress.**  
   /api/chat-edit and /api/render are single HTTP requests. Rendering calls synchronous subprocess.run inside an async route, blocking the event loop. There is no persisted per-job status, cancellation, resumability, or progress stream. PostgreSQL/Redis/Celery exist as scaffolding, not as an integrated job lifecycle. Use a background queue, expose stage/progress/error details, allow cancellation, and clean temporary artifacts.

8. **No project identity, version history, or safe concurrent edits.**  
   Projects are represented by shared filenames. Uploading a same-named file overwrites the previous one; extraction temp audio is named from the stem; broad wildcard matching can select the wrong file. Concurrent requests can collide. Introduce project/media IDs, isolated directories, immutable sources, edit versions, and per-project locks or concurrency-safe workers.

9. **The requested aspect ratio is not consistently represented.**  
   The render builder maps unknown ratios to portrait, but the API does not reject unsupported values. In /api/chat-edit, every ratio other than 16:9 is passed to the director as 1080×1920; square should be 1080×1080. Validate allowed ratios centrally and pass consistent dimensions and safe-area coordinates through analysis, preview, EDL, and render.

10. **AI fallback order and docs disagree.**  
    get_director_chain() constructs Gemini, local heuristic, then OpenRouter. Since the local heuristic typically returns an EDL, OpenRouter is not reached when both are configured. docs/api-config.md describes Gemini → OpenRouter → error, and other documentation describes a different chain. Set the intended order explicitly, report which provider generated the plan, and keep setup docs aligned with actual behavior.

11. **Render-time analysis is repeated and may leak disk space.**  
    Each edit re-extracts audio and representative frames into engine/temp/ without an evident cleanup or cache invalidation policy. Cache analysis by content hash and model/version, add retention limits, and show cache hits in job diagnostics.

12. **The editor has no clear failure recovery or validation feedback.**  
    The EDL validator filters some bad timestamps but only raises for unknown assets/SFX; it does not validate all end times, ordering/overlap, geometry dimensions, safe zones, or consistency with source duration. Add a complete validation report with warnings and auto-fixes, and make invalid plans recoverable instead of silently dropping elements.

### P2 — improve product fit and output quality

13. **No content-finding workflow for long recordings.**  
    The current pipeline edits a selected source over its duration; it does not surface candidate moments or a set of alternate short clips. Add highlight detection with rationale and let users approve candidate ranges before styling.

14. **Limited transcript-level editing.**  
    Word timestamps are generated, but there is no transcript editor to remove filler, silence, false starts, or rearrange spoken sections. A transcript-first editing surface would make corrections faster and more transparent.

15. **Multimodal understanding needs confidence and evidence.**  
    Vision inspection uses sampled frames and has a local heuristic fallback. The UI should show which frames and transcript spans led to each graphic or cut, give confidence, and let users correct it. Avoid presenting local heuristics as equivalent to a vision-language model.

16. **Accessibility, localization, and platform-safe areas are underspecified.**  
    Add caption size/contrast controls, subtitle export, language selection, and safe zones for platform UI overlays. Test portrait, landscape, and square outputs at actual phone preview sizes.

17. **Performance and cost claims are not reproducible.**  
    README/docs assert sub-30-second or sub-60-second workflows, but no machine profile, input benchmark set, cold/warm distinction, or stage-level current results accompany the claims. Publish a repeatable benchmark with source duration/resolution, CPU/GPU, provider, render settings, median and p95 stage time, and failure rate. Do not promise time until measured.

18. **Build a consistent visual system instead of piling on decorative templates.**  
    Current template cards describe complex animated experiences that export does not reproduce. Prioritize typography, pacing, caption placement, subject scale, contrast, and safe-zone controls. Keep scrapbook/music/glass treatments as modular styles supported identically in preview and export.

## Comparison with current products

This compares publicly documented capabilities, not hands-on competitor builds. Vendor feature pages describe their products and may not represent every plan or limit.

| Capability | Aura/Reel Editor in this repository | ChatCut | Descript | CapCut | OpusClip |
|---|---|---|---|---|---|
| Main workflow | Prompt creates an EDL, then a separate FFmpeg export | Natural-language agent edits a real multi-track timeline | Edit media by editing a transcript; AI co-editor | Full editor with AI tools, captions and reframing | Find highlights in long videos and turn them into social clips |
| Manual refinement | Preview + seek-only timeline; EDL is not directly editable in UI | Documented multi-track timeline plus prompt edits | Transcript editing plus timeline controls | Timeline and manual controls | In-app editor for polishing clips |
| Transcript editing | Transcription generates caption bursts; no transcript editor | Word-level transcript editing | Core text-based editing, filler removal and retake cleanup | Auto captions and text tools | Captions and clip editing |
| Clip discovery | No candidate clips/highlight picker | Can create short versions/alternate timelines | AI can create short clips from compositions | AI clip/highlight tools documented | Core product focus: highlight selection and repurposing |
| Reframing | Aspect ratio choice; renderer fits and pads, no subject-aware crop UI | Aspect ratios and editable timeline | Portrait/square layouts and reframing workflows | Auto Reframe | AI reframe for social aspect ratios |
| Audio | Source normalization and SFX; BGM/ducking claims not implemented | Music, voice, sound and noise tools documented | Studio Sound and audio editing documented | Broad AI audio/video feature set | AI audio enhancement and voice-over documented |
| Delivery | Local MP4 export; server writes into Export/ | Video and other media/project exports documented | Export and platform workflows | Platform-focused export | Publish/share workflows documented |
| Differentiator to pursue | Self-hostable, inspectable EDL and local FFmpeg pipeline | Agent + editable timeline | Transcript-first workflow | Broad creator toolkit and polish | Fast, multi-clip repurposing |

Sources:

- [ChatCut: What is ChatCut?](https://chatcut.io/docs/what-is-chatcut) and [ChatCut feature list](https://chatcut.io/features)
- [Descript feature overview](https://www.descript.com/features) and [text-based video editing](https://www.descript.com/video-editing)
- [CapCut Desktop AI editor](https://www.capcut.com/tools/desktop-ai-power)
- [OpusClip overview](https://www.opus.pro/) and [ClipAnything](https://www.opus.pro/clipanything)

### Product position

Do not compete on “AI makes a reel in seconds” alone. Several products already combine prompting with an editable timeline, and OpusClip focuses on finding many publishable segments from long recordings. A stronger position for this project is:

- **Self-hostable and inspectable:** show the EDL, model/provider, source spans, and asset decisions.
- **High-control short-form finishing:** make aspect ratios, captions, crop, pacing, and audio easy to adjust.
- **Fast local rendering:** only advertise measured performance on a named setup.
- **A few reliably implemented styles:** fewer templates with predictable preview/export parity.

## Recommended sequence

### Phase 1 — trust the output

- Make portrait exports fill the frame with selectable fit/fill/blur modes and a crop/focal point.
- Fix duration handling and enforce timed-element bounds.
- Make UI audio claims truthful; implement BGM/ducking or remove those labels.
- Align browser preview and FFmpeg output for framing, captions, graphics, and color treatment.
- Add export validation for dimensions, duration, audio presence/levels, caption bounds, and sample frames.

### Phase 2 — make it an editor

- Add transcript editing and timeline operations for caption/graphic/SFX clips.
- Add undo/redo and edit versions.
- Show AI reasoning as evidence-linked decisions users can accept, reject, or tweak.
- Add candidate clip selection for long recordings and alternative edits.

### Phase 3 — make it dependable

- Move edit/render into durable background jobs with progress, cancellation, retries, and cleanup.
- Use project/media IDs and isolate all files and temporary outputs.
- Add upload/path validation, authentication for non-local use, and clear provider/privacy controls.
- Add repeatable quality/performance benchmarks and end-to-end coverage across ratios/templates.

## Review limits

I inspected repository source and documentation, called the already-running local website’s root and health endpoint, and sampled one frame from the included HyperFrames MP4. I did not run an export, submit an upload/edit request, inspect every frame, or run the test suite. Competitor comparison is based on linked official product pages rather than hands-on product testing.

## Follow-up implementation check (2026-11-21)

After the audit, Phase 1 multimodal analysis changes passed 20 project tests and one authorized 7.114-second `/api/chat-edit` cloud validation. Phase 2 then added fifteen metadata-backed SVG assets and transparent PNG export counterparts. The local FFmpeg render completed and showed overlays in the output. Asset selection now uses transcript/topic, visible scene, template, attached resource names, and user instructions, with keyword scoring, evidence, and explicit exclusion checks. Generated hooks/social copy no longer injects unrelated brands or handles. The full suite now reports 25 passing tests. The portrait render still uses fit-and-pad framing, leaving large black bands; that remains an open export-quality issue. This follow-up does not change the competitor comparison above, which remains a source-based feature comparison rather than hands-on product testing.

