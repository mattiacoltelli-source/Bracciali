---
name: Ristorante Dong
description: Two kitchens, one table. Black lacquer, vermilion and brush gold for a Chinese and Japanese restaurant in San Lazzaro di Savena.
colors:
  lacca: "#130a09"
  lacca-2: "#1e100e"
  lacca-3: "#2b1714"
  lacca-foot: "#0b0605"
  vermiglio: "#b8180f"
  vermiglio-deep: "#7d0f0a"
  vermiglio-hover: "#cf2218"
  oro: "#cfa853"
  oro-hi: "#e3c373"
  carta: "#f3ece2"
  carta-soft: "#cdbfb2"
  carta-on-vermiglio: "#f2d3ca"
  status-open: "#58d68d"
  status-closed: "#e8806f"
typography:
  display:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, Georgia, serif"
    fontSize: "clamp(3rem, 12.5vw, 6rem)"
    fontWeight: 800
    lineHeight: 0.98
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, Georgia, serif"
    fontSize: "clamp(2.2rem, 7vw, 4.4rem)"
    fontWeight: 800
    lineHeight: 1.02
    letterSpacing: "0.005em"
  title:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, Georgia, serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "0.005em"
  body:
    fontFamily: "Zen Kaku Gothic New, Hiragino Kaku Gothic ProN, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Zen Kaku Gothic New, Hiragino Kaku Gothic ProN, system-ui, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 700
    lineHeight: 1.4
rounded:
  sm: "4px"
  md: "6px"
  field: "10px"
  pill: "999px"
spacing:
  gutter: "clamp(20px, 5vw, 56px)"
  section: "clamp(64px, 11vw, 140px)"
  max: "1240px"
  header: "68px"
  gap-sm: "12px"
  gap-md: "28px"
  gap-lg: "40px"
components:
  button-gold:
    backgroundColor: "{colors.oro}"
    textColor: "{colors.lacca}"
    rounded: "{rounded.pill}"
    padding: "0 28px"
    height: "52px"
  button-gold-hover:
    backgroundColor: "{colors.oro-hi}"
  button-red:
    backgroundColor: "{colors.vermiglio}"
    textColor: "{colors.carta}"
    rounded: "{rounded.pill}"
    padding: "0 28px"
    height: "52px"
  button-red-hover:
    backgroundColor: "{colors.vermiglio-hover}"
  button-line:
    backgroundColor: "transparent"
    textColor: "{colors.carta}"
    rounded: "{rounded.pill}"
    padding: "0 28px"
    height: "52px"
  chip:
    textColor: "{colors.carta}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "44px"
  chip-selected:
    backgroundColor: "{colors.oro}"
    textColor: "{colors.lacca}"
  tile:
    backgroundColor: "{colors.lacca-3}"
    rounded: "{rounded.sm}"
  book-card:
    backgroundColor: "{colors.lacca-2}"
    rounded: "{rounded.md}"
    padding: "clamp(24px, 5vw, 44px)"
  field-input:
    textColor: "{colors.carta}"
    rounded: "{rounded.field}"
    height: "54px"
    padding: "0 16px"
---

# Design System: Ristorante Dong

## Overview

**Creative North Star: "Lacquer and Brush"**

The site is the dining room put on a screen: a warm-black lacquer ground, one wall of vermilion, brush-gold for the things you act on, and rice-paper white for reading. Palette and form come from the real interior and the restaurant's own logotype and ideogram, not from a restaurant template. The organising idea is yin and yang: Japanese and Chinese are equal halves, and the menu switch re-grounds the whole page between black lacquer and vermilion.

Density is generous and photographic. Sections are tall, headlines are big heavy Mincho set tight, photographs are full-bleed or cropped to small-radius frames, and every section ends in a one-tap action (call, shop, directions). Surfaces are flat; depth comes from tonal steps of lacquer, photo gradients and hairline rules.

**Key Characteristics:**
- Dark lacquer ground by default; vermilion is a full-bleed surface (a half panel, the actions band, the Chinese menu theme), never a small accent.
- Gold marks what is actionable or selected; it is the only accent on dark ground.
- Heavy serif display (800) against a quiet gothic text face.
- Pill-shaped controls, 4px photo frames, hairline rules instead of boxes.
- Soft expo-out motion on one easing curve, fully disabled under reduced motion.

## Colors

Warm-black lacquer, two reds, two golds, two warm whites. No cool neutrals, no pure black or white.

### Primary
- **Vermilion Lacquer** (`vermiglio`): the Chinese half, the actions band, the Chinese menu ground, the red button. Used as a whole surface.
- **Deep Vermilion** (`vermiglio-deep`): the secondary ground when the Chinese theme is active.
- **Brush Gold** (`oro`): primary buttons, selected chips, text selection, map pill, the focus cue base. `oro-hi` is its lighter form for text on dark, hover, focus rings and highlights.

### Neutral
- **Black Lacquer** (`lacca`): page ground, header gradient, mobile nav. `lacca-2` is the raised panel (Japanese half, atmosphere band, booking card); `lacca-3` is photo placeholder and scrollbar track; `lacca-foot` is the footer floor.
- **Rice Paper** (`carta`): primary text and the selected switch state. `carta-soft` is secondary text on lacquer; `carta-on-vermiglio` is secondary text on the red theme.
- Hairline rule: `carta` at 16% alpha (26% on the red theme); no solid grey borders.
- **Status** (`status-open`, `status-closed`): functional dot colours for the live open/closed indicator only.

### Named Rules
**The Theme Switch Rule.** Page colour is carried by four custom properties (`--ground`, `--ground-2`, `--ink-soft`, `--accent`) plus `--rule`; the Chinese menu theme (`body[data-trad="cinese"]`) swaps them to vermilion. New menu-side components must read these, not raw palette values.
**The Gold Means Act Rule.** Gold fills and gold text signal a call, a selection or a hover. It is not decoration.
**The Two Reds Rule.** Vermilion appears as a ground the size of a panel. A thin vermilion line or tiny vermilion chip is wrong; the one small exception is the Chinese tile dot (`#e8503f`, a lifted red so it reads on photos).

## Typography

**Display Font:** Shippori Mincho (Hiragino Mincho ProN, Yu Mincho, Georgia, serif), weights 500/700/800, self-hosted.
**Body Font:** Zen Kaku Gothic New (Hiragino Kaku Gothic ProN, system-ui, sans-serif), weights 400/500/700, self-hosted.

**Character:** A calligraphic Mincho carries every heading, dish name, address and phone number at weight 700-800; the gothic stays plain for reading, buttons and navigation. Both faces cover the Japanese-adjacent flavour without costume.

### Hierarchy
- **Display** (800, `clamp(3rem, 12.5vw, 6rem)`, 0.98): the home H1 only, max 12ch, two stacked lines, second line in `oro-hi`.
- **Headline** (800, `clamp(2.2rem, 7vw, 4.4rem)`, 1.02): section titles; page heroes run `clamp(3rem, 11vw, 6.6rem)`; category and tradition heads sit in the 2.2-4.2rem range.
- **Title** (700-800, 1.28-3rem): action rows (`clamp(1.7rem, 5vw, 3rem)`), atmosphere points (1.5rem, gold), dish names (1.28rem), tile names (1.35rem).
- **Body** (400, 1.0625rem, 1.65): paragraphs, 32-40em measure; intros 1.1rem in `ink-soft`.
- **Label** (500-700, 0.88-1.02rem): buttons 700/1.02rem, nav 500/0.98rem, field labels 700/0.95rem. Sentence case, no uppercase tracking.

### Named Rules
**The Mincho Speaks Rule.** Anything the restaurant says as a statement (headings, names, address, phone) is Mincho; anything the visitor operates is gothic.
**The Tight Heavy Headline Rule.** Display and headline sizes use line-height at or near 1 with `text-wrap: balance`.

## Layout

Single column on mobile, max container 1240px with a fluid gutter (`clamp(20px, 5vw, 56px)`). Sections breathe with `clamp(64px, 11vw, 140px)` vertical padding. The breakpoint that matters is 900px: below it a fixed bottom dock (Prenota / Ordina / Dove) and a full-screen mobile nav replace the desktop nav and header call button; at 900px and above two-column compositions appear (the two-tradition split 1fr/1fr, atmosphere 0.9fr/1.1fr with a sticky text column and a 6-column photo grid, location 1fr/1.1fr). A secondary 760px break turns dish lists into two columns and the footer into four.

The home page opens on a full-height photograph with text pinned bottom-left, then moves in alternating grounds (split red/black, black, raised black, red, black). Horizontal scroll strips (menu tiles, per-category photos) bleed to the viewport edge and snap. Lists are rules and rows, not boxes. The 68px fixed header gets a lacquer gradient, then solid blurred lacquer after scroll.

## Elevation & Depth

Flat. Depth comes from tonal lacquer steps (`lacca`, `lacca-2`, `lacca-3`), the dark gradient laid over photos for legibility, a 1px hairline under a solid header, and backdrop blur on the sticky header, menu bar and dock. There are no drop shadows; the only glows are a status-dot halo and a 3px gold focus ring on fields.

### Named Rules
**The Flat Lacquer Rule.** Surfaces stay flat at rest. State is shown by colour, a 4px nudge, a 45-degree arrow turn or a 4-5% photo zoom, never by a shadow.

## Shapes

Two silhouettes. Controls (buttons, chips, switch, search, map pill, dock actions, round arrow buttons) are full pills (999px). Content is nearly square: photos and tiles at 4px, booking card at 6px, form fields and verdict at 10px. Photographs keep fixed aspect ratios (4/5 tiles, 4/3 and 16/9 frames). Hairline 1px or 1.5px borders define rows and outline buttons. The yin-yang disc is the recurring geometric mark; it straddles the seam of the two-tradition split and in miniature sits in the menu switch, where it turns 180 degrees on selection. The logo's brush ideogram appears large, at 26% opacity and masked to fade, behind inner-page headers.

## Components

### Buttons
- **Shape:** full pill, 52px minimum height, 28px side padding, weight 700.
- **Gold** (`button-gold`): lacquer text on gold; hover lightens to `oro-hi`. The primary call to act.
- **Red** (`button-red`): carta on vermilion; hover to `vermiglio-hover`.
- **Line** (`button-line`): transparent, 1.5px carta-at-50% border; hover turns border and text `oro-hi`.
- **Press:** 1px downward nudge on active. Optional leading 20px stroke icon.

### Chips and Switch
- Chips: 44px pill, hairline border, carta text; selected fills with `--accent` and lacquer text. The Giapponese / Cinese switch is a dark translucent pill track with two 44px pill segments; selected is carta on lacquer text.

### Cards / Containers
- Tile: 4/5 photo, 4px corners, bottom gradient to lacquer, name in Mincho 1.35rem and a small tradition dot (gold for Japanese, lifted red for Chinese). Booking card: `lacca-2`, 6px, fluid padding. Everything else is rows divided by hairlines.

### Inputs / Fields
- 54px (search 48px), 10px corners (search pill), 1.5px hairline border, faint white wash on lacquer, dark colour-scheme. Focus: border to `oro-hi` with a 3px 28% gold glow. Shift choice is a two-segment toggle where checked fills carta. Result messages tint green or salmon at 13-15% on a 10px panel.

### Navigation
- Desktop: gothic 500, carta at 86% opacity, current page full opacity with `oro-hi` and a 2px underline. Mobile: 48px bars icon, full-screen lacquer sheet with Mincho 700 rows (up to 2.6rem) and arrow glyph rows. Dock: three 48px pills, first gold.

### Action Row (signature)
- Large Mincho title with a line of description and a 56px circular arrow button on the right, separated by hairlines. Hover slides the row 14px, turns text `oro-hi` and fills the circle gold while rotating the arrow -45 degrees. Used on the red actions band.

### Open Status
- Inline text with a 10px dot: green with halo when open, salmon when closed, neutral otherwise.

## Do's and Don'ts

### Do:
- **Do** read grounds and accents from `--ground`, `--ground-2`, `--ink-soft`, `--accent` so the Japanese/Chinese switch recolours new components.
- **Do** keep tap targets at 44px or more and pill-shape every interactive control.
- **Do** use Mincho 800 at near-1 line-height for headings and gothic for everything operable.
- **Do** put a call, shop or map action within one tap of every section that persuades.
- **Do** keep all motion on `cubic-bezier(.16, 1, .3, 1)` and honour `prefers-reduced-motion`.
- **Do** use `carta` and `oro-hi` on lacquer or vermilion for AA text; use lacquer text on gold fills.

### Don't:
- **Don't** add shadows, cool greys, pure black or pure white.
- **Don't** use vermilion as a thin accent; it is a ground.
- **Don't** give the Japanese and Chinese halves unequal weight, size or treatment.
- **Don't** box content in cards when a hairline row will do.
- **Don't** open with a generic hero + three cards + gallery grid.
- **Don't** invent facts, reviews or prices; only restaurant-supplied content appears.
