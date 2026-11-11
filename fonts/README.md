# Fonts

The cards embed subsets of these fonts as base64 WOFF data URIs. Each subset
contains only the characters its card uses (made with fontTools' `pyftsubset`
API in `scripts/render_readme_cards.py`).

| File | Family | Weight / style | Source | Licence |
|---|---|---|---|---|
| `Newsreader-Display-Regular.ttf` | Newsreader (72pt optical size) | 400, roman | static instance of `Newsreader[opsz,wght].ttf`, google/fonts | [OFL-Newsreader.txt](OFL-Newsreader.txt) |
| `Newsreader-Display-Medium.ttf` | Newsreader (72pt optical size) | 500, roman | as above | [OFL-Newsreader.txt](OFL-Newsreader.txt) |
| `SourceSans3-Regular.ttf` | Source Sans 3 | 400, roman | static instance of `SourceSans3[wght].ttf`, google/fonts | [OFL-SourceSans3.txt](OFL-SourceSans3.txt) |
| `SourceSans3-SemiBold.ttf` | Source Sans 3 | 600, roman | as above | [OFL-SourceSans3.txt](OFL-SourceSans3.txt) |
| `IBMPlexMono-Regular.ttf` | IBM Plex Mono | 400, roman | google/fonts | [OFL-IBMPlexMono.txt](OFL-IBMPlexMono.txt) |
| `IBMPlexMono-Medium.ttf` | IBM Plex Mono | 500, roman | google/fonts | [OFL-IBMPlexMono.txt](OFL-IBMPlexMono.txt) |

All three are licensed under the SIL Open Font License 1.1. Weight and style
were read from each file's `OS/2` table (`usWeightClass`, `fsSelection`).
Inside the SVGs the embedded subsets are declared under local aliases
(`BG Newsreader`, `BG Source Sans`, `BG Plex Mono`), not under the Reserved
Font Names "Source" and "Plex".
