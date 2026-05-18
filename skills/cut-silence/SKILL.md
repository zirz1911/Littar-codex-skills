---
name: cut-silence
description: Detect silence and auto-trim video using HyperFrames rendering. Trigger when user says $cut-silence or asks to remove silent sections.
---

# $cut-silence

Use this skill to remove silent portions automatically.

## Command

```bash
scripts/cut-silence --input <input.mp4> --output <output.mp4>
```

## Options

- `--silence-threshold` default `-30` dB
- `--min-silence-duration` default `0.5` seconds
- `--fps` default `30`
- `--quality` one of `draft|standard|high` (default `high`)
- `--workers` default `1`
- `--docker/--no-docker` default `--docker`

## Example

```bash
scripts/cut-silence \
  --input ./raw.mp4 \
  --output ./raw.trimmed.mp4 \
  --silence-threshold -32 \
  --min-silence-duration 0.45 \
  --quality high \
  --docker
```
