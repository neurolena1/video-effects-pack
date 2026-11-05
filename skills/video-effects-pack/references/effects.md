# Effect reference

Generated from `scripts/fx.py --list`. Use the number or the id with `-e`. The Russian names are accepted too.

**Kind**: *intro* = a fixed-length animation that plays once at `--start` (length adjustable with `--duration` within the range shown); *continuous* = runs from `--start` to `--end`.

| # | id | Russian name | Kind | Default length | `--duration` range | What it does |
|---|---|---|---|---|---|---|
| 1 | `sparkle` | блеск | continuous | - | - | white 4-point sparkles twinkle across the frame |
| 2 | `vglitch` | вертикальный сбой | continuous | - | - | RGB split, vertical bars and film grain for the whole clip |
| 3 | `dropin` | выпадение | intro | 0.80 s | 0.64-1.60 s | the clip zooms in from 80% to 100% on a black background (first 0.8 s) |
| 4 | `details` | детали | intro | 3.00 s | 2.10-6.00 s | blurred background, 5 photo cards with flashes, then a flash and return (3 s) |
| 5 | `clasp` | застежка | intro | 2.50 s | 1.75-5.00 s | black start, black-and-white opens in strips, a diagonal wipe to colour and a flash (2.5 s) |
| 6 | `pulse` | импульсная тряска | continuous | - | - | 4% push-in with frequent vertical jolts |
| 7 | `mosaic` | мозаика | continuous | - | - | pixelates the face (finds it automatically) |
| 8 | `soft` | мягкий | continuous | - | - | smooth sway with up to 3.5 degrees of tilt and a soft focus |
| 9 | `slicemerge` | нарезка и слияние | continuous | - | - | the frame is cut into 4 strips with 1.4x zoom and different offsets; repeats every 3 s |
| 10 | `strip` | полоса | intro | 3.70 s | 2.59-7.40 s | the clip shrinks into a strip of reflected cards and returns (3.7 s) |
| 11 | `cursed` | проклятое видение | continuous | - | - | green tint, ghost reflection, horizontal tears, grain |
| 12 | `split` | разделение на несколько кадров | intro | 3.10 s | 2.17-6.20 s | black start, zoom-in, the frame multiplies into 2 and 3 copies, white bars, return (3 s) |
| 13 | `heartbeat` | сердцебиение встряска | continuous | - | - | 1.14x zoom pulse with a brightness flash twice a second |
| 14 | `mix` | смесь | intro | 4.20 s | 2.94-8.40 s | black-and-white with diagonal strips of a colour copy, a white silhouette and a flash (4.2 s) |
| 15 | `sliceup` | срез вверх фликер | intro | 3.10 s | 2.17-6.20 s | 2x zoom on the face, the cut edge creeps upward with flickering blocks (3 s) |
| 16 | `colorswing` | цвето качели | continuous | - | - | colour sways between violet and turquoise once a second |
| 17 | `formulas` | формулы | continuous | - | - | chalk formulas and triangles drift on the background behind the person (drawn procedurally, loops) |
| 18 | `rainbow` | радужное свечение | continuous | - | - | a diagonal rainbow glows along the frame edges and rotates 288 degrees/s (screen blend) |
| 19 | `griddive` | стена из кадров | intro | 0.85 s | 0.68-1.70 s | the frame pulls back into a tilted wall of tiles (each a different moment of the clip) and dives back (0.85 s) |
| 20 | `screeninscreen` | экран в экране | intro | 1.50 s | 1.05-3.00 s | the vertical video shrinks into a wide monitor frame on white and returns (1.5 s) |
| 21 | `orbit` | орбита | intro | 1.55 s | 1.08-3.10 s | 7 minimal icons (spark, wave, play, burst, CC, Aa, scissors: white tiles, thin dark glyphs) circle on a dotted ellipse around the person, the back half passes behind them |
| 22 | `chat` | чат-захват | intro | 2.03 s | 1.42-4.06 s | the video shrinks into a card and lands in an AI chat under the request message (light minimal chat: grey bubble, 'On it.', a list with black ticks, a reply field), then expands back; request via --text, items via --items |
| 23 | `snapzoom` | щелчок-зум | intro | 2.45 s | 1.72-4.90 s | three sharp push-ins on the face (1.45x, 1.95x, back) with blur and a slow settle |
| 24 | `checklistpop` | всплывающий чек-лист | intro | 1.84 s | 1.29-3.68 s | white pill cards with a thin outline and a black tick pop in from the right one after another (Edit, Captions, Effects); items via --items |
| 25 | `headlinestorm` | шторм заголовков | intro | 2.05 s | 1.43-4.10 s | black-and-white news ribbons tagged BREAKING / JUST IN fly in from both sides: some go behind the person, three pass in front of them (under the chin); texts via --items |
| 26 | `papercutout` | бумажная вырезка | intro | 1.87 s | 1.31-3.74 s | sticker-style person with a white outline on light paper: black disc, star, dots, white stripe, light frame-by-frame jitter |
| 27 | `liquidglass` | жидкое стекло | intro | 1.55 s | 1.08-3.10 s | a big glass lens glides over the face, magnifying and refracting the picture |
| 28 | `greenscreen` | хромакей | intro | 2.05 s | 1.43-4.10 s | a green curtain behind the person, then a sunset sky with a city skyline opens from the bottom in an arc |
| 29 | `digitalzoom` | цифровой зум | intro | 2.05 s | 1.43-4.10 s | a viewfinder with REC, a zoom counter and a focus frame: 1.6x, 2.6x, then a sharp return |
| 30 | `phonemock` | телефон | intro | 1.16 s | 0.81-2.32 s | the video shrinks into a smartphone screen with a short-video app interface (heart, comments, caption) on a light background |
| 31 | `quickzoom` | резкое приближение | intro | 1.90 s | 1.61-3.80 s | fast push-in 100% to 120% in 0.2 s, colour channels split apart (up to 18 px, 0.5 s), radial speed lines (0.35 s), then a smooth return |
| 32 | `smoothzoomout` | плавное отдаление | intro | 1.45 s | 1.16-2.90 s | the camera pulls back from 120% to 100% in 1 s with a smooth ease-in and ease-out |
| 33 | `colorframe` | цветная рамка | intro | 1.90 s | 1.52-3.80 s | a thin glowing frame pops up over the video: the colour flows through three accents, a bright comet runs along the frame, soft glow outside and inside (colours come from the style) |
| 34 | `framebreak` | разбить рамку | intro | 1.75 s | 1.40-3.50 s | the same glowing frame as in 'colorframe' (33) holds for 0.42 s, cracks and shatters into ~48 glowing shards of the same colour (spin, flip, fall), followed by confetti and a circular wave |
| 35 | `growthchart` | рисуем график | intro | 2.30 s | 1.61-4.60 s | a card with axes and grid, the growth line is drawn left to right with a fill, value labels, a +N% counter up to 120, a pulsing dot; title via --text |
| 36 | `pipdelay` | видео поверх видео | intro | 2.10 s | 1.47-4.20 s | a window with a REC mark in the bottom-right corner shows the same video delayed by 0.5 s (head and chin fully visible), slightly tilted and floating |
| 37 | `splitscreen` | сплит-экран | intro | 1.90 s | 1.33-3.80 s | the screen splits horizontally: the normal frame on top, the same frame at 135% below; the halves slide in from the top and bottom in 0.3 s with a line between them; caption on the line via --text |
| 38 | `magazine` | я на обложке | intro | 2.15 s | 1.50-4.30 s | the video turns into a magazine cover: issue and date on top, masthead above the hair, a big number with a label and a cover line on a colour plate below the chin, two small lines and a barcode at the bottom; nothing overlaps the face; every text is editable: --text (masthead), --items (in order: line1\|line2\|number\|label\|bottom1\|bottom2\|issue\|date), --opt key=value, '-' hides an element |
| 39 | `bwframe` | чёрно-белый кадр | intro | 1.90 s | 1.52-3.80 s | colour fades out in 0.35 s (slightly more contrast), holds, returns in 0.45 s |
| 40 | `pixelate` | пикселизация | intro | 1.80 s | 1.44-3.60 s | the whole frame turns into a mosaic: block size grows 1 to 48 px in 0.25 s, holds, returns in 0.55 s |
| 41 | `vignette` | виньетка | intro | 1.55 s | 1.24-3.10 s | the frame edges darken with a radial gradient: appears in 0.35 s, holds ~0.75 s, leaves in 0.45 s |
| 42 | `fadeblack` | плавное затемнение | intro | 1.75 s | 1.40-3.50 s | the screen fades to black in 0.8 s, a short pause, a quick return in 0.4 s |
| 43 | `iconsaround` | иконки вокруг меня | intro | 2.00 s | 1.40-4.00 s | 8 glossy colour icons (music, picture, chat, play, chart, document, spark, bolt) with white glyphs circle on a flat tilted ellipse around the head, some behind the person, some in front; no dotted ring; a variety of 'orbit' |
| 44 | `greenbg` | зелёный фон | intro | 2.10 s | 1.47-4.20 s | a bright green background with soft highlights, dots and growing frames, tracking markers with X/Y labels, the person with a white wavy sticker outline; a variety of 'greenscreen' |
| 45 | `checklist2` | список с галочками | intro | 2.00 s | 1.40-4.00 s | a card with a title and a 3-item list at the bottom of the frame: circles turn into colour ticks one after another, sparks, a progress bar; title via --text, items via --items; a variety of 'checklistpop' |
| 46 | `headlinestorm2` | шторм из заголовков | intro | 2.10 s | 1.47-4.20 s | the screen darkens, three lightning strikes with a flash, coloured headline plates fly in from the sides (some behind the person, some in front), the frame shakes for 1.5 s; texts via --items; a variety of 'headlinestorm' |
| 47 | `phonemock2` | макет телефона | intro | 2.00 s | 1.40-4.00 s | the video shrinks in 0.4 s into a smartphone screen on a uniform neutral background, holds and expands back in 0.45 s; the caption above the phone appears only with --text; a variety of 'phonemock' |
