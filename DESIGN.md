---
name: Ristorante Dong
description: Due cucine. Un solo tavolo. A mahjong table of ivory tiles on jade felt for a Chinese and Japanese restaurant in San Lazzaro di Savena.
colors:
  felt: "#0c3a2d"
  felt-2: "#08281f"
  felt-hi: "#165243"
  felt-indaco: "#10172a"
  felt-indaco-2: "#0a0f1d"
  felt-indaco-hi: "#1d2a49"
  carta: "#f1ead8"
  carta-soft: "#b9cbbf"
  carta-soft-indaco: "#b8c2d6"
  accento: "#e2bd62"
  accento-indaco: "#f0c36a"
  osso-1: "#f8f3e5"
  osso-2: "#efe7d1"
  osso-3: "#e1d7bb"
  giada: "#1f8a62"
  giada-2: "#135c42"
  inchiostro: "#1a1813"
  drago-rosso: "#b01e14"
  drago-verde: "#14683f"
  punto-blu: "#2455a4"
  oro: "#d9b255"
  status-open: "#6be29a"
  status-closed: "#ff8a76"
typography:
  display:
    fontFamily: "Bricolage Grotesque, Arial Rounded MT Bold, system-ui, sans-serif"
    fontSize: "clamp(2.8rem, 9.4vw, 5.6rem)"
    fontWeight: 800
    lineHeight: 0.98
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Bricolage Grotesque, Arial Rounded MT Bold, system-ui, sans-serif"
    fontSize: "clamp(2.2rem, 7vw, 4.4rem)"
    fontWeight: 800
    lineHeight: 1.04
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Bricolage Grotesque, Arial Rounded MT Bold, system-ui, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Hanken Grotesk, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Hanken Grotesk, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.02rem"
    fontWeight: 700
    lineHeight: 1.4
  tile-glyph:
    fontFamily: "Tessere (Shippori Mincho 800 subset), Hiragino Mincho ProN, Yu Mincho, serif"
    fontSize: "clamp(3.8rem, 14vw, 6rem)"
    fontWeight: 800
    lineHeight: 1
rounded:
  tile-sm: "9px"
  tile: "16px"
  tile-lg: "22px"
  control: "14px"
  chip: "10px"
  field: "12px"
  photo: "8px"
spacing:
  gutter: "clamp(18px, 5vw, 56px)"
  section: "clamp(64px, 11vw, 140px)"
  max: "1200px"
  header: "68px"
  gap-sm: "14px"
  gap-md: "24px"
  gap-lg: "40px"
components:
  button-rosso:
    backgroundColor: "{colors.drago-rosso}"
    textColor: "#fff6ea"
    rounded: "{rounded.control}"
    padding: "0 28px"
    height: "54px"
  button-osso:
    backgroundColor: "{colors.osso-1}"
    textColor: "{colors.inchiostro}"
    rounded: "{rounded.control}"
    padding: "0 28px"
    height: "54px"
  button-linea:
    backgroundColor: "transparent"
    textColor: "{colors.carta}"
    rounded: "{rounded.control}"
    padding: "0 28px"
    height: "54px"
  tile:
    backgroundColor: "{colors.osso-2}"
    textColor: "{colors.inchiostro}"
    rounded: "{rounded.tile}"
  tile-back:
    backgroundColor: "{colors.giada}"
    rounded: "{rounded.tile}"
  chip:
    textColor: "{colors.carta}"
    rounded: "{rounded.chip}"
    padding: "0 16px"
    height: "42px"
  chip-selected:
    backgroundColor: "{colors.osso-1}"
    textColor: "{colors.inchiostro}"
  switch-segment:
    textColor: "{colors.carta}"
    rounded: "11px"
    padding: "0 16px 0 12px"
    height: "44px"
  switch-segment-selected:
    backgroundColor: "{colors.osso-1}"
    textColor: "{colors.inchiostro}"
  field-search:
    textColor: "{colors.carta}"
    rounded: "{rounded.control}"
    height: "52px"
    padding: "0 16px 0 48px"
  field-date:
    backgroundColor: "#fffdf6"
    textColor: "{colors.inchiostro}"
    rounded: "{rounded.field}"
    height: "56px"
    padding: "0 16px"
  dock-action:
    backgroundColor: "{colors.osso-1}"
    textColor: "{colors.inchiostro}"
    rounded: "11px"
    height: "52px"
---

# Design System: Ristorante Dong

## Overview

**Creative North Star: "The Mahjong Table"**

The site is a table where a game is about to start. Green felt is the ground, ivory tiles are the only objects on it, and the restaurant's line "Due cucine. Un solo tavolo." is made literal: four tiles spell D-O-N-G, the menu is a hand of tiles, and the three dragon tiles (red Zhong, green Fa, white blank) are the three actions: book, takeaway, delivery. Dots mark the Japanese kitchen, bamboo marks the Chinese one, as in the real suits.

The felt changes with the tradition. Jade green is the house table; choosing Giapponese in the menu moves the whole page to a night-indigo felt. Everything lit or tappable is a tile: ivory, rounded, with a visible jade edge as its thickness. Everything else is felt, text and hairline rules.

Density is generous. Sections are tall, tiles are large, photographs sit on tiles like photos set into ivory, and every section ends within one tap of a dragon.

**Key Characteristics:**
- Felt ground (jade, or night indigo for the Japanese menu) with a faint paper-noise grain and a soft lighter pool at the top.
- Ivory tile (`osso`) is the single raised object; its jade edge is the only depth cue.
- Tile inks: red, green, blue, plus near-black. Gold is rare.
- Rounded grotesque display (Bricolage Grotesque 800) over a plain humanist text face (Hanken Grotesk), with a Mincho subset used only for tile glyphs.
- Springy tile motion (drop, tilt, lift, flip) on a bounce curve; fully reduced under reduced motion.

## Colors

Deep green-black felt, warm ivory, three tile inks and one rare gold. No pure black or white on ground; text on felt is warm ivory.

### Primary
- **Jade Felt** (`felt`, with `felt-2` for bands, header, footer and mobile nav, and `felt-hi` for the top glow): the table. These three are redefined by `body[data-trad="giapponese"]` as **Night-Indigo Felt** (`felt-indaco`, `felt-indaco-2`, `felt-indaco-hi`).
- **Dragon Red** (`drago-rosso`): the Zhong tile ink, the Prenota button, the floating search button, the map pill, Chinese-tradition accents, tile corner glyphs.

### Secondary
- **Dragon Green** (`drago-verde`): the Fa tile ink, bamboo marks, focus and valid states on ivory.
- **Dot Blue** (`punto-blu`): the white-dragon frame, Japanese-tradition accents, dot marks.
- **Jade Edge** (`giada`, `giada-2`): the visible side of every tile and the back of flipped hero tiles.

### Tertiary
- **Table Gold** (`accento`, indigo variant `accento-indaco`): headline second line, hover and current-page text, atmosphere points on felt. `oro` is the same family used for selection, caret, focus ring and the tile-back ring.

### Neutral
- **Ivory Bone** (`osso-1`, `osso-2`, `osso-3`): tile faces as a 160-degree gradient from light to shaded.
- **Tile Ink** (`inchiostro`): text on ivory.
- **Table Paper** (`carta`): text on felt; `carta-soft` (indaco variant `carta-soft-indaco`) is secondary text on felt. Secondary text on ivory uses the literal warm greys `#5a5445`, `#4a4638`, `#3a362c`.
- Hairline: `carta` at 18% alpha, never a solid grey.
- **Status** (`status-open`, `status-closed`): functional dot colours for the live open/closed indicator only.

### Named Rules
**The Felt Swap Rule.** Page ground is carried by `--felt`, `--felt-2`, `--felt-hi`, `--carta-soft`, `--accento`, which the Japanese menu theme redefines. New components on felt read these variables, not raw hex.
**The Tile Is The Object Rule.** Anything raised, tappable-as-a-token or photo-bearing is an ivory tile with a jade edge. Nothing else on the page casts a shadow.
**The Rare Gold Rule.** Gold marks the current, the hovered and the second line of a headline. It never fills a large surface.
**The Ink Is Meaning Rule.** Red, green and blue appear as tile ink on ivory (glyphs, marks, links), tied to dragons and suits: red Chinese, blue Japanese, green bamboo and "yes".

## Typography

**Display Font:** Bricolage Grotesque (Arial Rounded MT Bold, system-ui, sans-serif), weights 700/800, self-hosted.
**Body Font:** Hanken Grotesk (system-ui, sans-serif), weights 400/500/600, self-hosted.
**Glyph Font:** "Tessere", a Shippori Mincho 800 subset limited to the tile characters (中 發 白 and the wind characters 東南西北); used for glyphs only, never for text.

**Character:** A friendly, slightly quirky heavy grotesque carries all headings, dish names and numbers at tight leading; the text face stays quiet. The Mincho glyphs are the only calligraphic voice and live on tiles.

### Hierarchy
- **Display** (800, `clamp(2.8rem, 9.4vw, 5.6rem)`, 0.98): the home H1, max 14ch, second line in `accento`. Hero D-O-N-G tile letters run up to 9.4rem at -0.04em.
- **Headline** (800, `clamp(2.2rem, 7vw, 4.4rem)`, 1.04): section titles; page heroes `clamp(3rem, 12vw, 6rem)`; category heads up to 3.8rem.
- **Title** (800, 1.25-2.6rem): dish names (1.25rem), tile names (1.35rem), dragon names (up to 2.4rem), address and phone (up to 4rem).
- **Body** (400, 1.0625rem, 1.65): paragraphs on a 34-40em measure; intros 1.1rem in `carta-soft`.
- **Label** (600-700, 0.95-1.02rem): buttons 700/1.02rem, nav 600/0.98rem, field labels 700/0.95rem. Sentence case.

### Named Rules
**The Glyphs Stay On Tiles Rule.** Mincho glyphs appear only as tile faces or tile corner marks, never in running text.
**The Tight Heavy Headline Rule.** Display and headline sizes sit at line-height near 1 with `text-wrap: balance`.

## Layout

Single column on mobile, 1200px container with fluid gutter (`clamp(18px, 5vw, 56px)`), sections padded `clamp(64px, 11vw, 140px)`. The decisive breakpoint is 900px: below it a fixed bottom dock of three dragon tiles (Prenota / Ordina / Dove) and a full-screen felt nav replace the desktop nav and header button; at 900px and above compositions go two-column (two traditions 1fr/1fr with the Japanese tile dropped 56px, atmosphere .85fr/1.15fr with a sticky text column and a 6-column photo wall, dragons 1.35fr/1fr/1fr aligned to the bottom, four winds across). A 760px break sets dishes in two columns and the footer in four.

The home opens on a full-height felt with a faint luminosity-blended room photo, tiles settling bottom-left, headline, lede and buttons below them, then moves through felt, a darker band, and tile-based sections. Horizontal strips (menu tiles, per-category photos) bleed to the viewport edge and snap. Lists are hairline rows. The 68px fixed header starts as a dark gradient and turns into blurred `felt-2` with a hairline once scrolled.

## Elevation & Depth

Depth exists only as tile thickness. A tile is ivory with an inset highlight and a stacked hard edge in jade (6px, 10px, 13px offsets in `giada`, `giada-2`, `#0d4331`) over a long soft floor shadow; small controls use a 3-5px two-step jade or dark-red edge. Felt itself is flat: bands are tonal steps (`felt`, `felt-2`), with backdrop blur and a 1px hairline on the sticky header, menu bar and dock. A selected chip, switch segment or turn is "lifted": it translates up 3px and gains the jade edge.

### Shadow Vocabulary
- **Slab** (`box-shadow: inset 0 3px 0 #fff, ..., 0 6px 0 #1f8a62, 0 10px 0 #135c42, 0 13px 0 #0d4331, 0 28px 32px -8px rgba(0,0,0,.7)`): large tile, hero-scale objects, photo frames.
- **Tile** (`inset 0 2px 0 #fff, inset 0 -3px 8px rgba(120,98,55,.18), 0 18px 26px -12px rgba(0,0,0,.6)`): default `.t3` surface.
- **Key edge** (`inset 0 2px 0 rgba(255,255,255,.28), 0 4px 0 #7f160f, 0 14px 18px -8px rgba(0,0,0,.6)`): red buttons.
- **Small jade edge** (`inset 0 1.5px 0 #fff, 0 3px 0 #1f8a62, 0 5px 0 #135c42`): dock tiles, selected chips, verdict tile.

### Named Rules
**The Visible Edge Rule.** The jade edge is how a tile reads as a physical piece. It is allowed only on tile objects, never on text blocks, cards of copy or felt panels.
**The Press Rule.** Hover lifts a tile 2-8px; pressing sinks it 2-3px; no other state effects.

## Shapes

Tiles are rounded rectangles in a 3 : 4.1 proportion: 16px for hero and ordinary tiles, 22px for the two tradition tiles, 9-14px for small tiles, buttons and dock keys (14px, 11px). Photos sit inside ivory with 7-10px padding and 8px inner corners, like a picture set in a tile. Chips and switch segments are small tiles (10-11px). Fields are 12-14px. Suit marks are drawn shapes: round dots for Japanese, upright rounded bars (6 x 14-16px) for Chinese bamboo. The white dragon is a 5px blue-framed square on a blank tile. The gold brush ideogram from the logo appears on flipped tile backs and as a faint large mark behind the hero.

## Components

### Buttons
- **Shape:** 14px radius, 54px min height, 28px side padding, weight 700.
- **Rosso:** red tile with white-ish text and dark-red edge; primary action (Prenota).
- **Osso:** ivory tile with jade edge and ink text; secondary action (Guarda il menu).
- **Linea:** transparent with 2px inset ivory ring at 50%; hover turns ring and text gold.
- **Hover / Press:** hover lifts 2px (hover-capable devices only); active sinks 3px.

### Tile (Tessera)
- Ivory gradient, 16px, with a red corner glyph mark top-left (.95rem). Variants: slab (full jade thickness) for photo frames and hero tiles; small edge for keys. Content on it is ink, with warm grey secondary.

### Hero Tiles (D O N G)
- Four tiles 3 : 4.1 at `clamp(66px, 20.5vw, 200px)` wide, each tilted by its own `--r`, falling in with a stagger and bounce. Tap flips on the Y axis to a jade back with a gold ring and the brush ideogram.

### Dragons (actions)
- Large tile face (red Zhong, green Fa, white frame) beside name, line of copy and a gold "arrow" link; the red one is largest. Hover lifts and tilts -1.5 degrees.

### Winds (Dove siamo)
- Four tiles with a red wind glyph at the top-left, label, then the value in display type (address, hours, phone, closing day).

### Menu Tile (Foto su tessera)
- Ivory tile with 8px-corner 4 : 5 photo, name in display 1.35rem, tradition mark (blue dot or green bar); rotated by its own angle, straightens and lifts on hover. Strips snap horizontally.

### Chips and Switch
- Chips: 42px, 10px corners, dark translucent with a gold 1.5px inset ring; current becomes an ivory lifted tile with jade edge. Giapponese / Cinese switch: two 44px key segments carrying a dot or bamboo glyph; the selected one lifts as ivory. Selecting recolours the page via the felt swap.

### Inputs / Fields
- Search: 52px, 14px, 2px hairline border, dark wash, gold border and 3px gold glow on focus. On ivory (booking), date field is 56px, 12px, warm white; focus turns border green with a green glow. Shift choice (turni) is two segments; checked becomes an ink tile lifted 3px.

### Verdict
- Booking result panel with a small tile glyph at left (green yes, red no) and tinted wash at 14-16%.

### Navigation
- Desktop: text links 600, ivory at 85%, current page gold underlined 2px. Mobile: 48px bars icon, full-screen `felt-2` sheet with large rows each led by a tile glyph. Dock: three 52px tile keys, first red; glyph colours red, green, blue.

### Open Status
- Inline text with 11px dot: green with halo when open, salmon when closed, neutral otherwise.

## Do's and Don'ts

### Do:
- **Do** build every raised or tappable object as an ivory tile with the jade edge; leave felt flat.
- **Do** read grounds from `--felt`, `--felt-2`, `--felt-hi`, `--accento` so the tradition switch recolours new components.
- **Do** keep tap targets at 44px or more, with 14px or smaller tile corners for controls.
- **Do** use Bricolage Grotesque 800 at near-1 leading for headings and Hanken Grotesk for reading and operating.
- **Do** keep red for Chinese and the primary action, blue for Japanese, green for bamboo and confirmation.
- **Do** put a dragon (book, order, directions) within one tap of every persuading section.
- **Do** use ink on ivory, ivory on felt, and honour `prefers-reduced-motion`.

### Don't:
- **Don't** return to the previous dark-lacquer, vermilion and gold look.
- **Don't** put the jade edge or any cast shadow on copy blocks, felt panels or text.
- **Don't** use gold as a surface fill or on more than a line or hover state per view.
- **Don't** set Mincho glyphs in running text.
- **Don't** give the Japanese and Chinese traditions unequal size or treatment.
- **Don't** open with a generic hero + three cards + gallery grid.
- **Don't** invent facts, reviews or prices; only restaurant-supplied content appears.

### Not canonized
- Category tile caption (`.cat-n small`, 0.72rem uppercase tracked) is a small uppercase tracked label; treat as a build defect, do not reuse.
