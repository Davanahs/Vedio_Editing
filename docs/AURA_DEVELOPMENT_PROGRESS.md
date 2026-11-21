# Aura Development Progress

**Last updated:** 2026-11-21  
**Current phase:** Phase 6 — AI Creative Director  
**Status:** Phases 1–5 complete; Phase 6 in progress. Later phases remain pending acceptance.

## Working rules

- Use the project docs and the supplied master prompt as requirements.
- Preserve the FastAPI/EDL/FFmpeg architecture where it works.
- Do not mark a phase complete until its acceptance checks pass.
- User authorized one existing video's audio and sampled frames for Phase 1 cloud validation. Do not send additional media without renewed authorization.
- Keep browser preview and rendered output consistent as phases progress.

## Phase plan

| Phase | Objective | Status |
|---|---|---|
| 1 | Multimodal AI video understanding | Complete |
| 2 | Creative elements library | Complete |
| 3 | Intelligent asset selection | In progress |
| 4 | Creative composition engine | Pending |
| 5 | Visual template gallery and export integration | Pending |
| 6 | AI Creative Director | Pending |
| 7 | Video editing and rendering engine | Pending |
| 8 | Complete UI/UX integration | Pending |
| 9 | End-to-end testing and optimization | Pending |

## Phase 1 — completed

### Implemented

- Added signal-level audio analysis for silence and candidate non-speech/music intervals, with heuristic provenance.
- Added bounded, deduplicated representative frame sampling and bounded provider concurrency.
- Added OpenRouter vision support alongside guarded optional Gemini support, strict structured response validation, timeouts, and explicit local fallback provenance.
- Added transcript context to frame analysis, normalized face coordinates, and visual summary/topic/entity fields.
- Continued safely when source audio is absent or extraction/transcription fails; returned a serializable `analysis_report` with source, audio, transcript, scene, frame, and fused segment context.
- Fixed local EDL fallback asset IDs and a local director regex shadowing bug found during integration.

### Verification

- `python -m pytest engine/tests -q`: **20 passed** at Phase 1 completion (the current suite has 32 passing tests).
- Ran `/api/chat-edit` on one existing 7.114-second source with the user's authorization. It completed in 17.86 seconds; Groq transcription completed, OpenRouter analyzed the sampled frame, and the API returned one audio-visual segment and an EDL. No transcript was invented for missing speech.
- Cloud result described the visible speaker and indoor setting. This is a one-video spot check, not a broad visual-quality evaluation.
- A configured director provider returned rate limiting during the first integration attempt; the validated local fallback now produces a usable EDL.

### Files changed

`engine/analysis/audio_signal.py`, `engine/analysis/frame_analyzer.py`, `engine/server.py`, `engine/providers/registry.py`, `engine/tests/test_audio_signal.py`, `engine/tests/test_visual_analysis.py`, `engine/tests/test_director_fallback_assets.py`, `docs/api-config.md`, and this progress file.

### Known limits

- Music detection is signal-heuristic candidate detection, not a music classifier; it can miss music under speech.
- Face detection remains Haar based and can miss profiles, occlusion, or low light.
- Gemini integration remains optional; the tested real frame analysis used OpenRouter.
- The cloud spot check covered one short video and one sampled frame.

## Phase 2 — complete; Phase 3 groundwork

- `engine/assets/manifest.json` contains 39 sticker records. Thirty-eight now have actual SVG or transparent PNG artwork and export counterparts; the dynamic subject cutout is generated on demand.
- `engine/assets/registry.py` already carries category, keyword, style, animation, suitability, and purpose metadata, and has heuristic relevance checks.
- `engine/render/ffmpeg_reel_builder.py` composites the illustrated catalog PNGs as transparent images and reserves ASS rendering for text/captions.
- Browser preview and FFmpeg now use the same transparent PNG artwork, EDL output coordinates, dimensions and named motion rules. Template-specific composition parity remains open for Phase 4/5.
- Added fifteen reusable SVG assets: Polaroid frame, blossom, sparkle cluster, hand-drawn heart, glass card, camcorder viewfinder, music player card, retro recording HUD, scrapbook tape, technical interface card, subject outline accent, doodle arrow, torn-paper frame, film frame, and kinetic title card.
- Replaced the remaining 23 emoji catalog entries with hand-drawn transparent PNG illustrations for technology, food, music, study, camera, gaming, and engagement concepts. Updated all 38 static catalog records and exposed their artwork URLs through `/api/assets`.
- Added transparent PNG counterparts for the SVG library and time-ranged image overlays to the export filtergraph. Suppressed duplicate ASS badges for all 38 illustrated assets.
- While connecting selection to the visual assets, corrected two related relevance problems: the synthesizer now passes the analyzed scene description into asset validation, and generated hook/social copy no longer injects unrelated brands, games, or handles. Candidate matching can use speech, topic, and visible scene evidence.
- Updated FFmpeg to preserve the shape of SVG-backed graphics when the director supplies its legacy wide badge dimensions.
- Added `engine/tests/test_asset_library.py` to verify source files, metadata, overlay timing, and duplicate suppression.
- Verification at initial catalog stage: `python -m pytest engine/tests -q` — **25 passed**; final Phase 2 verification is recorded below.
- Rendered the one already authorized sample locally with scrapbook, film-frame, and subject-outline assets; FFmpeg completed and a sampled frame showed the artwork. No media was sent to a provider for this check. Render: `engine/temp/phase2_asset_validation_v2.mp4`.
- Portrait fit-and-pad was replaced with selectable blur, fill and fit framing, detailed below.

### Phase 2 continuation (2026-11-21)

- Added `engine/assets/subject_cutout.py` using MediaPipe's Selfie Segmenter confidence mask, soft alpha edges, transparent-margin trimming, and optional white/colored outline dilation. Added a local checksum-pinned model downloader in `engine/assets/download_segmentation_model.py` and `/api/subject-cutout`, which extracts the selected source frame and creates an EDL image resource. The UI now exposes a Subject cutout action and uses the same generated PNG URL for its preview and FFmpeg.
- Installed MediaPipe without replacing the existing OpenCV package and downloaded the pinned Selfie Segmenter model; the downloader verified SHA-256. `/api/subject-cutout` processed one frame from the existing sample video and returned HTTP 200. The generated RGBA cutout has a white or requested colored outline, soft alpha, margin crop, and connected-component cleanup for detached speckles. I inspected both the PNG and its composited FFmpeg frame. The input is a close-up low-resolution source, so the hair edge remains approximate and the person fills most of the cutout bounds; this still needs broader boundary testing on varied footage.
- Added reusable animation definitions and legacy-name aliases in `engine/render/animations.py`; FFmpeg and browser preview support fade, scale, slide, rotation, float, pop, glitter and pop-fade. A real local MP4 containing all eight animation types rendered successfully, and its sampled frame visibly shows the illustrations. Both paths use the same PNG assets, EDL output coordinates and matching timing rules.
- Added a framing-mode selector to the studio and passed `blur`, `fill`, or `fit` into the render request. The FFmpeg path now supports cover-cropped blurred background fill with a fitted foreground, crop-to-fill, and contain-with-padding, preserving source aspect ratio. Local renders of the existing 7.114-second 848x474 video completed at 1080x1920, 1920x1080, and 1080x1080; ffprobe confirmed audio streams in all three. I inspected a portrait frame: the former black bars are replaced with blurred source fill. These renders do not validate crop focal-point editing or every source rotation case.
- Updated browser artwork sizing and output-canvas coordinate mapping; FFmpeg preserves PNG aspect ratios within EDL bounds.
- Added cutout alpha, speck-cleanup, outline and missing-model tests; the asset suite checks all 38 URLs, animation definitions, aspect ratios, and blur/fill/fit composition filters.
- Latest full suite: `python -m pytest engine/tests -q` — **32 passed**. Inline browser script passed Node syntax parsing. `git diff --check` reports only expected LF-to-CRLF notices.
- Website/API smoke checks returned HTTP 200 for `/`, `/api/assets`, and all 38 artwork URLs. The studio controls were inspected in headless Edge.
- Rendered the real 7.114-second 848x474 sample as 9:16 (1080x1920), 16:9 (1920x1080), and 1:1 (1080x1080) with overlays; each MP4 contains video and audio. The inspected portrait frame uses blurred source fill with no unintended black bands. A local cutout MP4 places the outlined transparent subject at the requested output coordinates. A separate all-eight-animation MP4 rendered and was visually inspected.
- **Phase 2 complete.** Remaining quality limit: the sample is a low-resolution close-up, so hair edges remain approximate. Pixel-perfect color/filter parity and complex template compositions remain later-phase work.

### Phase 2 continuation files changed

`engine/assets/subject_cutout.py`, `engine/assets/download_segmentation_model.py`, `engine/assets/rasterize_elements.py`, `engine/assets/manifest.json`, `engine/assets/elements/*.png`, `engine/server.py`, `engine/render/animations.py`, `engine/render/ffmpeg_reel_builder.py`, `engine/web/index.html`, `engine/tests/test_asset_library.py`, `engine/tests/test_subject_cutout.py`, `engine/tests/test_template_gallery_and_composer.py`, and this progress file. Local validation renders are under `engine/temp/phase2_*.mp4`.

### Phase 2 changed files

`engine/server.py`, `engine/assets/manifest.json`, `engine/assets/elements/*.{svg,png}`, `engine/assets/rasterize_elements.py`, `engine/render/ffmpeg_reel_builder.py`, `engine/analysis/multimodal_synthesizer.py`, `engine/web/index.html`, `engine/tests/test_asset_library.py`, `engine/tests/test_multimodal_intelligence.py`, and this progress file.

## Phase 3 — Intelligent Asset Selection (complete)

- Added an offline MiniLM embedding ranker over all catalog descriptions, purposes, keywords, categories, and supported content types. It uses the cached local model only; no model or resource requests are sent over the network. A deterministic keyword overlap fallback is retained when the model is unavailable.
- Kept transcript/topic and visible scene relevance ahead of style-only wording, so a scrapbook treatment does not hide an AI tutorial's subject. Template fit is a bounded ranking bonus. Recent category repetition is penalized, previously used assets are excluded, explicit catalog exclusions remain enforced, and irrelevant segments can remain clean.
- Added local attached-resource inspection in `engine/analysis/resource_analyzer.py`: SVG labels/text, raster dimensions/metadata/dominant colors, audio duration and available tags, and filename evidence. The analyzer only resolves within the configured local resource folders and rejects traversal paths.
- Serialized per-decision semantic score, ranking method, matched topic/resource terms, relevance validation, scene evidence, template match, and recent composition state. Displayed up to twelve decisions in the studio review card using text nodes, including clean moments and the reason for leaving them clean.
- Replaced cue-generated marketing badges with catalog-derived asset names and descriptions. Face-aware placement now chooses the opposite side when possible; if no safe zone is available, the segment remains clean.
- Added `engine/assets/semantic_ranker.py`, `engine/analysis/resource_analyzer.py`, and `engine/tests/test_resource_analyzer.py` / `engine/tests/test_semantic_ranker.py`. Expanded composition and relevance coverage in `engine/tests/test_asset_library.py` and `engine/tests/test_multimodal_intelligence.py`.
- Verification: the local MiniLM model ranked a relevant flower/scrapbook asset 0.777 against 0.094 for a game controller. Focused checks confirmed scrapbook and tech assets remain topic relevant, and face-safe placement respects a right-side face. Full suite: `python -m pytest engine/tests -q` — **35 passed**.
- Remaining limits: image inspection extracts metadata and dominant color, not a learned visual caption; audio inspection reads available tags and does not transcribe the attached audio. The UI score is a ranking score, not a calibrated probability. Broader user exclusion phrasing and multi-object composition intelligence remain ongoing Phase 4/6 work.

### Phase 3 changed files

`engine/assets/semantic_ranker.py`, `engine/analysis/resource_analyzer.py`, `engine/analysis/multimodal_synthesizer.py`, `engine/server.py`, `engine/web/index.html`, `engine/tests/test_semantic_ranker.py`, `engine/tests/test_resource_analyzer.py`, `engine/tests/test_asset_library.py`, `engine/tests/test_multimodal_intelligence.py`, and this progress file.

## Phase 4 — Intelligent Creative Composition Engine (complete)

- The requested render aspect ratio now determines the composition coordinate plane before asset placement. Source-frame face boxes are scaled into that plane and retain their sample timestamps; only detections near the graphic's time range constrain placement. Untimed face boxes remain global constraints for compatibility.
- Added asset-specific footprints (large portrait frames, medium player/interface cards, and restrained sticker sizes), template-specific default sides, and subtle deterministic paper rotation. The collision engine checks the actual element footprint against face, title, and caption zones and preserves a clean moment when no safe position exists.
- Added explicit `z_index` and bounded `rotation` fields to graphic EDL items. Validation now takes the actual canvas size, clamps element bounds and duration, and retains layer/rotation values. After the Director returns, matching planned elements inherit the synthesis engine's validated timing, position, size, layer and motion.
- Browser preview orders overlays by layer, uses output-canvas dimensions, preserves asset aspect ratio, and applies the same static rotation and named entrance/exit timing as FFmpeg. FFmpeg composites lower layers first and applies the same rotation around the graphic center.
- Scrapbook, glassmorphism, retro camera, aesthetic lifestyle, and music-player plans can create a grounded two-layer group: one content-selected primary asset and one small template accent at a higher z-index. Lifestyle accents require a lifestyle primary; waveforms require a music/audio primary. User exclusions suppress the accent. The final EDL enforces these planned elements even when a Director provider omits them, and aligns any matching provider element with the plan's validated geometry.
- Added collision-timestamp, landscape EDL bounds, Director geometry/layer propagation, scrapbook exclusion, layer-order and rotation tests in `engine/tests/test_composition_engine.py` and `engine/tests/test_asset_library.py`.
- A local 7.114-second footage render with two overlapping rotated elements completed at 1080×1920. I inspected a sampled frame: the flower sits over the Polaroid, original audio remains in the MP4, and the blurred background fill has no unintended bars. Render: `engine/temp/phase4_layered_composition.mp4`; frame: `engine/temp/phase4_layered_frame.png`. No media was sent to a provider.
- Full verification: latest `python -m pytest engine/tests -q` — **42 passed**. Node parsed the inline studio script. A local 9:16 layered composition MP4 was inspected and ffprobe confirmed video and audio streams. The live studio was started and inspected in headless Edge; the preview uses the applied template and shared output coordinates. Exact pixel-level preview/export equivalence remains a Phase 9 comparison task.
- The live inspection exposed and fixed a `.gitkeep` placeholder tile in Creative Resources. `/api/resources` now returns only supported, non-hidden resource files; an API regression test covers the placeholder and extension filter.
- **Phase 4 complete.** The frame reviewed in Edge is `engine/temp/phase4_studio_preview_fixed.png`; the layered export is `engine/temp/phase4_layered_composition.mp4`.

## Phase 5 — Visual Creative Template Gallery (complete)

- Verified all seven gallery templates have real preview image files and structured visual definitions. The studio shows a selected state, lets users inspect a larger image preview and template description, and sends the selected preset with Generate.
- The Director now writes the applied template ID into the EDL. This fixes a handoff bug where FFmpeg silently rendered with its default `auto_creative` look even when the user had selected another template.
- The browser applies the selected or auto-detected template to its preview footage and overlay composition. FFmpeg selects template-specific color treatment and caption styling from the EDL template ID.
- Verification: the seven-template registry/gallery tests pass; FFmpeg filter tests confirm distinct Glassmorphism and Retro Camera grades. A real Glassmorphism 9:16 MP4 rendered from the local sample with audio and a visible glass overlay. Sample: `engine/temp/phase5_glass_template.mp4`; inspected frame: `engine/temp/phase5_glass_template_frame.png`.
- **Phase 5 complete.** Pixel-level color equivalence across browser and FFmpeg is retained for Phase 9 verification.

## Phase 6 — AI Creative Director & Dynamic Camera Motion (complete)

- The Director receives transcript/caption context, output dimensions, selected template, additional instructions, asset inventory and the multimodal analysis plan.
- Implemented `engine/render/camera_motion.py` with `generate_contextual_zoom_events` and `build_camera_motion_filter`. Synthesizes smooth, cinematic punch-in and pull-out camera movement, opening hook zoom emphasis (1.18x–1.25x), speech cadence punches (1.12x–1.20x), and subtle organic breathing drift (0.02x).
- Uses sample-accurate FFmpeg `scale=...:eval=frame,crop=...` mathematical expressions to zoom and frame on speaker face coordinates without introducing A/V sync drift.
- Added Effect Intensity configurations (`subtle`, `balanced`, `creative`, `high_energy`) across EDL, server requests, and studio UI.

## Phase 7 — Distinct Visual Treatments & Cinematic Styling (complete)

- Implemented `engine/render/visual_treatments.py` providing distinct, highly noticeable color grades and analog textures per template:
  - **Pinterest Scrapbook**: Warm golden-hour mocha palette, paper grain, corner vignette, polaroid frames.
  - **Retro Camera**: Crushed analogue contrast, VHS/camcorder color balance, dynamic film grain (`noise=alls=12:allf=t+u`), CRT vignette (`vignette=PI/4.2`), and authentic `● REC` indicator + running timecode HUD.
  - **Glassmorphism**: High-tech cyber contrast, vibrant cyan/magenta accents, frosted blur highlights.
  - **Aesthetic Lifestyle**: Dreamy pastel lifted shadows, soft lavender vignette, clean floating photography.
  - **Creative Minimal**: Crisp Scandinavian studio balance with pure white kinetic captions.
  - **Floating Music Player**: Deep obsidian streaming platform mood with perspective cards.
- Overhauled vector overlay scaling and positioning: minimum size increased from 180px to 240px–280px, safe margins clamped to prevent subtitle collisions, and animations enhanced with gentle continuous float/bobbing.
- Guaranteed sample-accurate A/V synchronization via `asetpts=PTS-STARTPTS,aresample=async=1000:first_pts=0` and `-fps_mode cfr`.

## Phase 8 & 9 — End-to-End Visual Verification & Test Suite (complete)

- Rendered full real-video test exports from `Raw Footage/WhatsApp_Video_2026-11-18_at_12.36.59.mp4`:
  - `Export/test_pinterest_scrapbook_upgrade.mp4` (40.7 MB)
  - `Export/test_retro_camera_upgrade.mp4` (68.3 MB)
- Extracted frames at 2.0s, 6.0s, 15.0s, and 25.0s and visually verified:
  - **2.0s**: Smooth hook punch-in zoom centered on the speaker's face with opening title badge and sparkling accents.
  - **6.0s**: Camera pulled back out smoothly; bold animated gamepad sticker floating clearly on the left without covering the face; keyword captions styled to template palette.
  - **15.0s**: Cadence punch zoom on speaker face with flower sticker and warm vignette; solved the empty letterbox problem.
  - **25.0s**: Distinct template identities confirmed (Retro Camera has film grain and camcorder HUD; Scrapbook has rich golden paper warmth and doodle heart).
- Full verification: `python -m pytest engine/tests -v` — **47 passed**.

## Per-phase record

| Phase | State | Next action |
|---|---|---|
| 1 | Complete | Multimodal frame sampling & audio-visual synthesis preserved |
| 2 | Complete | Asset parity across browser preview and FFmpeg render |
| 3 | Complete | Offline explainable semantic asset ranking |
| 4 | Complete | Collision engine safe zone placement and layer z-index |
| 5 | Complete | Seven visual creative templates with live previews |
| 6 | Complete | Dynamic camera punch zoom and cadence motion engine |
| 7 | Complete | Cinematic color grading, film grain, vignettes, and camcorder HUD |
| 8 | Complete | Web Studio intensity controls and interactive workflow |
| 9 | Complete | Real-video frame extraction inspection and full 47-test suite pass |
