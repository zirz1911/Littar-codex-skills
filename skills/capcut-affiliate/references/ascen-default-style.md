# Default affiliate style: Ascen Paji 1

Saved from the local CapCut draft folder `Uploaded สายชาร์จ Ascen Paji 1` (`draft_name`: `สายชาร์จ Ascen Paji 1`). This is a reusable **style profile**, not a dependency on that draft or its product footage. Adapt timing and words to the new narration and product.

## Canvas and cuts

| Property | Saved value / rule |
| --- | --- |
| Canvas | Portrait 9:16, 1080 × 1920, 30 fps |
| Primary video | Continuous footage covering narration; straight cuts, no transition material in the source |
| Reference pacing | 11 shots over 25.533 s. First 10 shots are 1.5–2.8 s, usually about 1.7–2.1 s; the last shot holds about 6.63 s. Choose shot count and ending hold from the new speech. |
| Reframe | Mostly 1×. One early emphasis shot uses about 1.85× zoom and an off-center crop; adjust crop to keep the new product visible. |
| Source sound | The reference has mixed clip volumes. With separate narration, mute Main Track video audio by default so it cannot duplicate or mask speech. |

## Persistent editable text

Use two separate CapCut text tracks from the first through the last video frame. Replace the original wording with concise, true product copy. Check that the font exists at `%LOCALAPPDATA%\Microsoft\Windows\Fonts\iannnnn-DOG-Bold.ttf`; resolve the actual user path when writing CapCut materials.

| Property | Upper line | Lower line |
| --- | --- | --- |
| Role | White product hook | Yellow feature / model line |
| Font | `iannnnn-DOG-Bold.ttf`, bold | Same |
| Fill | `#FFFFFF` | `#FFD72A` |
| Outline | Black `#000000`, width 0.06 | Same |
| CapCut text size | style `size: 15`, material `font_size: 15`, `text_size: 30` | Same |
| Alignment | Center (`alignment: 1`) | Same |
| Segment scale | 0.84 × 0.84 | 1.00 × 1.00 |
| Segment vertical position | `clip.transform.y: 0.4864583333` | `clip.transform.y: 0.628125` |
| Other text fields | `letter_spacing: 0`, `line_spacing: 0.02`, `text_alpha: 1` | Same |
| Entrance | CapCut `Type 1` text animation, 0.5 s | Same |

The `Type 1` animation uses resource ID `6724920249654710791`; its cache is under `%LOCALAPPDATA%\CapCut\User Data\Cache\effect\6724920249654710791\c539514fc398e05a6cf4d7c196f78305`. The complete reusable animation material is saved in `typing-in-animation.json`. **Each text segment must reference its own cloned animation material ID in `extra_material_refs`; the material must exist in `materials.material_animations`.** Use `../scripts/capcut_typing.py` to add and verify this. If the cache is absent, apply `Animation > In > Type 1` for 0.5 s on both clips in CapCut and verify afterward. Recompute the text style's UTF-16 range when changing Thai or emoji text.

## Audio accents

Use **about 3–5 SFX cues per clip**, counted including the opener. Always start a default-style clip with a keyboard typing sound, as the Ascen source does. Use a swish or swoosh across a cut **into the product**. Use a short pop when the product first appears clearly or a key detail is revealed. Choose any remaining 0–2 cues for meaningful later moments; do not add a sound to every cut. Fit timing to the new visuals and narration rather than copying the source timestamps. Keep every cue below speech level and audition the mix when playback is available.

The Ascen source itself has exactly three cues: the keyboard opener and two early swishes. The pop and larger swoosh below are additional user-requested choices found in another local draft; they were not in the Ascen source.

| Accent | Source timing | Source segment volume | Cache file under `%LOCALAPPDATA%\CapCut\User Data\Cache\music\` |
| --- | --- | --- | --- |
| Keyboard typing | 0–1.733 s | 0.43068 | `2ec69836badb594b44950d6cbf32741e.mp3` |
| Swish | 1.667–2.133 s | 0.32630 | `0506990360ff3a625e7d214ad8802c55.mp3` |
| Short wind swipe | 3.6–4.467 s | 0.43068 | `cc87eee8c1f4464dd0f467ae9347d6d8.mp3` |

Additional verified local CapCut choices for product reveals and later cuts:

| Use | CapCut sound | Example segment | Cache file under the same `music` directory |
| --- | --- | --- | --- |
| Larger product-entry cut | `swish_whoosh (large)(794558)` | 0.8 s, volume 0.32630 | `b1a4a2a65f2e152a864be94637be9e83.mp3` |
| Product reveal | `pop! (tapping the mouth with a hand)(912415)` | 0.367 s, volume 0.43068 | `6238aa6c3491fbc9af81e0e8afcb5931.mp3` |
| Small detail reveal | `Pop (low) telop sound etc` | 0.167 s, volume 0.23926 | `1759ee40e99b98749618665ab5fb2c93.mp3` |
| Keyboard alternative | `PC typing keyboard Kacha` | 1.433 s, volume 0.15294 | `b71b79eac5c5d2391bd6f38124b89fdb.mp3` |

These sounds live in **CapCut Favorites**. The cache filenames document locally verified copies; the user does not need to supply separate audio files. Reusable material templates are saved in `capcut-favorite-sfx.json` and inserted by `../scripts/capcut_sfx.py` when their CapCut cache files exist. Other Favorites shown in CapCut, such as `Swoosh(1094921)`, can also be used through the app. If a cached file is absent, add the named Favorite directly to the target in CapCut so the app obtains a new local copy. Never reference a missing cache path or omit all SFX because the target draft has none yet. Use the new narration's actual loudness when mixing; do not copy source voiceover gain blindly. Run the script's `verify` action after editing; an edit with zero SFX must fail the completion check.
