---
name: genz-cut
description: Create Gen Z/TikTok/Reels-style edits with HyperFrames, including voice-driven duration, cut-silence cleanup, fast 9:16 pacing, full-screen meme inserts, separated SFX timing, kinetic captions, proxy re-encoding, validation, and final render handoff. Use when the user asks to cut or edit a video in the same style as the previous Bobo/Minsdetect examples, says "genz-cut", or wants a funny/high-retention vertical edit using HyperFrames plus meme and sound-effect folders.
---

# Gen Z Cut

Use this skill for fast vertical edits that feel like TikTok/Reels ads or meme-heavy explainers. Pair it with `$hyperframes`, `$hyperframes-cli`, and `$cut-silence` when silence trimming is needed.

## Defaults

- Format: `1080x1920`, 9:16.
- FPS: `60` for final unless speed matters; `30` is fine for drafts.
- Pace: cut every `1.5-3s`; meme hits last `1-2s`.
- Meme style: full-screen, not picture-in-picture, unless the user asks otherwise.
- Dynamic framing: never blindly center-crop horizontal assets. Every meme, stock clip, or screen recording should pass through a subject-centric framing setting.
- Captions: lower-third kinetic karaoke style; keep text short and readable.
- Color coding: negative/risk words red; positive/feature words green; technical/product words blue.
- Audio authority: if `Voice 1`, `Voice 2`, etc. exist, concatenate in numeric order and make that the total duration.
- Safety: preserve originals. Create a new HyperFrames project and symlink or proxy assets.

## Workflow

1. Read project instructions such as `CLAUDE.md` if working inside a repo.
2. Locate the requested folder and inspect all media with `rg --files`, `find`, and `ffprobe`.
3. Determine duration:
   - Prefer `Voice 1 + Voice 2 + ...` concatenated in order.
   - Else use the main audio file.
   - Else use the main video duration.
4. If the source has dead air or the user asks to remove silence, use `$cut-silence` before building the HyperFrames composition. Keep the untrimmed source intact.
5. Scaffold a new project near the source folder:
   - `npx hyperframes init <name> --example blank --non-interactive`
6. Create `assets/audio`, `assets/stock`, `assets/memes`, `assets/sfx`, and `assets/proxy` as needed.
7. Symlink source files into the project first. Do not copy large originals unless required.
8. Create a central media configuration before writing the timeline. Every visual asset should have optional framing settings:

```js
const MEDIA_SEQUENCE = [
  { id: "m-rollsafe", file: "assets/proxy/rollsafe.mp4", start: 12.4, duration: 1.6, type: "meme", framing: "left" },
  { id: "m-jim", file: "assets/proxy/jim-carrey.mp4", start: 43.8, duration: 2.1, type: "meme", framing: "right" },
  { id: "ui-dashboard", file: "assets/proxy/ui-gemlogin.mp4", start: 18, duration: 8, type: "ui", region: "top-right", zoom: 1.18 },
  { id: "stock-pan", file: "assets/proxy/shopping.mp4", start: 34, duration: 2.4, type: "stock", framing: "pan_left_to_right" },
];

const MEME_POSITION_SETTINGS = {
  "rollsafe.mp4": { framing: "left", x: 0, y: 0, scale: 1 },
  "jim-carrey.mp4": { framing: "right", x: 0, y: 0, scale: 1 },
  "confused.mp4": { framing: "center", x: 0, y: 0, scale: 1 },
};
```

9. For every video clip that will be seeked or trimmed, create short proxy clips before final render. Do not use a fixed center crop for all assets. Pick the crop expression from the asset's `framing`:

```bash
case "$framing" in
  left) crop_x="0" ;;
  right) crop_x="iw-1080" ;;
  center|"") crop_x="(iw-1080)/2" ;;
esac

ffmpeg -nostdin -y -ss "$start" -i "$src" -t "$dur" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:${crop_x}:0,fps=60" \
  -c:v libx264 -preset veryfast -crf 20 -g 30 -keyint_min 30 \
  -pix_fmt yuv420p -movflags +faststart \
  -map 0:v:0 -map 0:a? -c:a aac -b:a 128k "$out"
```

This avoids sparse-keyframe freezes in HyperFrames renders and makes final renders faster.

For `pan_left_to_right` or `pan_right_to_left`, either:
- keep the source wider than the canvas and animate `x` in HyperFrames, or
- render a proxy with an FFmpeg animated crop expression. Prefer HyperFrames animation when you need easier visual tuning.

## Dynamic 9:16 Framing System

Generic center-cropping horizontal media often cuts off faces. Use subject-centric framing for all horizontal memes, stock footage, and UI/screen recordings.

### Valid Framing Values

- `center`: default. Use only when the subject/action is actually centered.
- `left`: align the left edge of the 16:9 source to the left edge of the 9:16 frame. Use when the subject is on the left, such as Roll Safe tapping head or Patrick/Spongebob left-side reactions.
- `right`: align the right edge of the source to the right edge of the frame. Use when the subject is on the right, such as Jim Carrey typing or right-weighted reaction memes.
- `pan_left_to_right`: animate horizontally across the source during the clip.
- `pan_right_to_left`: same in reverse.
- custom settings: `x`, `y`, `scale`, `focus_x`, `focus_y`, or `region` when the default anchors are not enough.

### Required Helper Pattern

Generated HyperFrames code should separate framing logic from timeline assembly. Use a helper like this:

```js
const CANVAS = { w: 1080, h: 1920 };

function applyVerticalFraming(el, config, tl) {
  const framing = config.framing || config.focus_anchor || "center";
  const scale = config.scale ?? 1;
  const x = config.x ?? 0;
  const y = config.y ?? 0;

  el.style.objectFit = "cover";
  el.style.width = "100%";
  el.style.height = "100%";
  el.style.objectPosition =
    framing === "left" ? "left center" :
    framing === "right" ? "right center" :
    "center center";
  el.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;

  if (framing === "pan_left_to_right") {
    el.style.objectPosition = "left center";
    tl.to(el, { objectPosition: "right center", duration: config.duration, ease: "power1.inOut" }, config.start);
  }

  if (framing === "pan_right_to_left") {
    el.style.objectPosition = "right center";
    tl.to(el, { objectPosition: "left center", duration: config.duration, ease: "power1.inOut" }, config.start);
  }
}
```

If using proxy generation instead of runtime object positioning, apply the same `framing` map to calculate `crop_x`. Do not hardcode center crop as the only path.

### Known Meme Framing Defaults

- Confused guy: `center`
- Shrek staring/smiling: `center`
- Spongebob/Pattrick tracking reactions: `left`
- Roll Safe / smart guy: `left`, or `pan_center_to_left` if face starts off-center
- Jim Carrey typing: `right`
- Michael Jordan laughing/crying: `right`
- Spiderman pointing: `center` unless the chosen clip is asymmetrical

When unsure, make a thumbnail/contact sheet and choose the anchor from the visible face/action position.

### Meme X/Y Settings

Plan for a user-editable settings layer. Store per-meme overrides in a central object and apply it programmatically:

```js
const MEME_POSITION_SETTINGS = {
  "meme-rollsafe.mp4": { framing: "left", x: 0, y: 0, scale: 1.05 },
  "meme-jim-carrey.mp4": { framing: "right", x: -20, y: 0, scale: 1.08 },
  "meme-confused.mp4": { framing: "center", x: 0, y: 0, scale: 1 },
};

function resolveFraming(file, config = {}) {
  const basename = file.split("/").pop();
  return { framing: "center", x: 0, y: 0, scale: 1, ...(MEME_POSITION_SETTINGS[basename] || {}), ...config };
}
```

This makes it easy to expose future UI controls for meme `x`, `y`, `scale`, and `framing` without rewriting timeline code.

### UI And Screen Recording Region Targeting

Software showcases need region targeting, not just crop anchors. In the central config, allow:

- `region`: `top-left`, `top-right`, `bottom-left`, `bottom-right`, `center`
- `target`: custom `{ x, y }` pixel or percent coordinates
- `zoom`: camera scale
- `pan`: optional start/end target

Pattern:

```js
const UI_TARGETS = {
  "new-profile": { region: "top-right", zoom: 1.45 },
  "advanced-settings": { target: { x: 680, y: 760 }, zoom: 1.8 },
  "automation-node-graph": { region: "bottom-right", zoom: 1.9 },
};

function applyUiCamera(tl, selector, start, duration, target) {
  const ease = "power1.inOut"; // or CustomEase cubic-bezier when loaded
  const coords = target.target || regionToOffset(target.region || "center");
  tl.to(selector, { scale: target.zoom || 1.2, x: coords.x, y: coords.y, duration, ease }, start);
}
```

Use smooth easing for every automated camera move.

## Timeline Rules

- Build the edit around the voice/audio timeline first.
- Alternate attention beats:
  - stock/main visual
  - meme reaction
  - UI/product zoom
  - caption punch
  - SFX-only hit
- Do not stack meme insert and standalone SFX at the same time unless the user explicitly asks. If a meme clip has embedded audio, use it lightly and avoid an additional SFX on that same beat.
- Keep full-screen meme clips short. Use the strongest visual moment via `data-media-start` or proxy trimming.
- Every full-screen meme must declare `framing`/`focus_anchor`, or fall back to `center` through `resolveFraming()`. Never assume all 16:9 meme clips are safe with center crop.
- Use `data-track-index` to prevent timeline conflicts; use CSS `z-index` for visual layering.
- Main narration should remain clear. Keep meme/SFX volume around `0.25-0.65` unless the narration is absent.

## HyperFrames Composition Pattern

- Root composition:
  - `data-composition-id="main"`
  - `data-duration="<audio duration>"`
  - `data-width="1080"`
  - `data-height="1920"`
- Use `.clip` on all timed visible elements.
- Use standalone `<audio>` for narration and SFX.
- Use `<video data-has-audio="true">` only when that clip should contribute audio.
- For UI/product shots, build procedural HTML UI when no screen recording exists. Add smooth camera motion with GSAP and cubic-bezier/CustomEase:

```js
gsap.registerPlugin(CustomEase);
const smoothBezier = CustomEase.create("smoothBezier", "M0,0 C0.22,1 0.36,1 1,1");
tl.to("#ui-canvas", { scale: 1.8, x: -280, y: -620, duration: 4, ease: smoothBezier }, 20);
```

Mark intentionally zoomed UI containers with `data-layout-ignore` or `data-layout-allow-overflow` so `inspect` does not block expected camera movement.

## Captions

- Prefer transcript timestamps if good.
- For Thai or noisy audio, Whisper may produce large inaccurate segments. If so, use the user-provided script or scene breakdown and manually time caption segments.
- Render 1 short phrase at a time in the lower third.
- Use HTML spans:
  - `<span class="neg">ตามรอย</span>`
  - `<span class="pos">ปลอดภัย</span>`
  - `<span class="tech">Automation</span>`
- Animate captions in/out quickly with `gsap.fromTo` and `overwrite: "auto"`.

## Validation And Delivery

Run checks before rendering:

```bash
npm run check
```

Acceptable residual warnings:
- `timeline_track_too_dense` for short single-file edits.
- contrast warnings inside intentionally ignored procedural UI, if captions remain readable.

Fix before render:
- overlapping clips on the same track
- missing `id` on media
- missing `.clip`
- media without `data-start`
- layout issues affecting captions or visible text

Render:

```bash
npm run render -- --output renders/<name>.mp4 --fps 60 --quality high
```

Verify:

```bash
ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=codec_type,width,height,avg_frame_rate,duration \
  -of default=noprint_wrappers=1:nokey=0 renders/<name>.mp4
```

Copy the final MP4 back into the source folder with a clear name, and report:
- final file path
- project `index.html`
- duration, resolution, fps
- checks run and any remaining non-blocking warnings
