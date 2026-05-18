---
name: cut
description: Trim a video by explicit keep ranges using HyperFrames rendering. Trigger when user says $cut or asks to cut video by specific timestamps.
---

# $cut

Use this skill to cut a video by explicit keep ranges.

## Command

```bash
scripts/cut --input <input.mp4> --output <output.mp4> --ranges "0-3.2,5.1-9.0"
```

## Options

- `--fps` default `30`
- `--quality` one of `draft|standard|high` (default `high`)
- `--workers` default `1`
- `--docker/--no-docker` default `--docker`

## Example

```bash
scripts/cut \
  --input ./in.mp4 \
  --output ./out.mp4 \
  --ranges "0-2.8,4.0-7.5" \
  --quality high \
  --docker
```
