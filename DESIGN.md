---
name: Channel Analyzer API
description: A local quota-aware API presented as a channel on the video site it analyses.
colors:
  bg: "#0F0F0F"
  bg-raised: "#212121"
  bg-sunken: "#000000"
  chip: "#272727"
  chip-hover: "#3F3F3F"
  chip-active: "#F1F1F1"
  on-chip-active: "#0F0F0F"
  line: "#3F3F3F"
  line-soft: "#272727"
  text: "#F1F1F1"
  text-2: "#AAAAAA"
  text-3: "#717171"
  link: "#3EA6FF"
  red: "#FF0033"
  red-text: "#FF4E45"
  red-soft: "#3A0A0F"
  now-tag: "#CC0029"
  ok: "#2BA640"
  ok-soft: "#0E2A14"
  warn: "#F7B500"
  warn-soft: "#3A2C00"
  error: "#FF4E45"
  m-get: "#3EA6FF"
  m-get-soft: "#0B2741"
  m-post: "#3DD068"
  m-post-soft: "#0E2A14"
  m-patch: "#F7B500"
  m-patch-soft: "#3A2C00"
  m-delete: "#FF4E45"
  m-delete-soft: "#3A0A0F"
  scrim: "#000000CC"
  on-scrim: "#FFFFFF"
  drawer-scrim: "#00000080"
  bg-light: "#FFFFFF"
  bg-raised-light: "#FFFFFF"
  bg-sunken-light: "#F9F9F9"
  chip-light: "#F2F2F2"
  chip-hover-light: "#E5E5E5"
  chip-active-light: "#0F0F0F"
  on-chip-active-light: "#FFFFFF"
  line-light: "#E5E5E5"
  line-soft-light: "#F2F2F2"
  text-light: "#0F0F0F"
  text-2-light: "#606060"
  text-3-light: "#757575"
  link-light: "#065FD4"
  red-text-light: "#CC0000"
  red-soft-light: "#FFE5E9"
  ok-light: "#107516"
  ok-soft-light: "#E3F4E5"
  warn-light: "#8A5A00"
  warn-soft-light: "#FFF3D6"
  error-light: "#CC0000"
  m-get-soft-light: "#DEF1FF"
typography:
  display:
    fontFamily: "Roboto, Arial, sans-serif"
    fontSize: "36px"
    fontWeight: 700
    lineHeight: "44px"
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Roboto, Arial, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: "28px"
  card:
    fontFamily: "Roboto, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 500
    lineHeight: "22px"
  body:
    fontFamily: "Roboto, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "20px"
  label:
    fontFamily: "Roboto, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "36px"
  meta:
    fontFamily: "Roboto, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: "18px"
  code:
    fontFamily: "Roboto Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
  method:
    fontFamily: "Roboto Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "11px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.02em"
rounded:
  tag: "4px"
  chip: "8px"
  guide: "10px"
  card: "12px"
  banner: "16px"
  pill: "999px"
spacing:
  s-1: "4px"
  s-2: "8px"
  s-3: "12px"
  s-4: "16px"
  s-5: "24px"
  s-6: "32px"
  s-7: "48px"
components:
  pill:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.text}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "36px"
  pill-hover:
    backgroundColor: "{colors.chip-hover}"
  pill-primary:
    backgroundColor: "{colors.text}"
    textColor: "{colors.bg}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "36px"
  pill-primary-hover:
    backgroundColor: "{colors.text-2}"
  pill-outline:
    backgroundColor: "transparent"
    textColor: "{colors.link}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "36px"
  pill-outline-hover:
    backgroundColor: "{colors.m-get-soft}"
  chip:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.text}"
    rounded: "{rounded.chip}"
    padding: "0 12px"
    height: "32px"
  chip-selected:
    backgroundColor: "{colors.chip-active}"
    textColor: "{colors.on-chip-active}"
  method-get:
    backgroundColor: "{colors.m-get-soft}"
    textColor: "{colors.m-get}"
    typography: "{typography.method}"
    rounded: "{rounded.tag}"
    padding: "0 6px"
    height: "22px"
  badge-time:
    backgroundColor: "{colors.scrim}"
    textColor: "{colors.on-scrim}"
    rounded: "{rounded.tag}"
    padding: "1px 4px"
  status:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.text}"
    typography: "{typography.meta}"
    rounded: "{rounded.pill}"
    height: "28px"
  avatar:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.text}"
    size: "36px"
  search-input:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.text}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "40px"
  thumb:
    backgroundColor: "{colors.bg-sunken}"
    rounded: "{rounded.card}"
    padding: "16px"
  panel:
    backgroundColor: "{colors.chip}"
    rounded: "{rounded.card}"
    padding: "16px"
---

# Design System: Channel Analyzer API

## Overview

**Creative North Star: "The Channel on the Site It Analyses"**

The API presents itself as a channel page and watch page on youtube.com, the visual reference Yasir Khan pinned for this world. It borrows that site's grammar, not its brand: near-black and white grounds, grey chips, pill buttons filled in the text colour, 12px rounded 16:9 thumbnails, Roboto, a masthead with a central search, and a left guide. Service facts take the place of video content: the live health response plays as the "player", the four fetch steps form the "Up next" queue, the stored record types are "videos" in a card grid, and the endpoint groups are shelves behind a chip bar.

Density is that of a video platform: compact 14px body text, 36px controls, generous 40px row gaps between cards, and quiet grey surfaces that let one red signal carry all urgency. Dark is the default theme; light follows the system preference or `data-theme="light"` on any element. The page refuses the developer-landing default of a hero, stat tiles and icon cards.

The Swagger UI info section at `/api-docs` uses the same world in the light theme only, laid out for reading rather than browsing: a compact channel header with the actions on its right, one chip row of endpoint groups, then three open columns split by hairlines (a numbered fetch stepper, a live quota clock with its price ladder, and authorization with the house rules) and a borderless 4 by 2 grid of what gets stored. No boxed cards. The showcase at `/design-system` renders both themes side by side.

**Key Characteristics:**
- youtube.com grammar with no YouTube logo or brand asset.
- One red, reserved for live state and time progress.
- Pills for actions, 8px chips for filters, 12px cards for content.
- Flat surfaces; only the drawer floats.
- Every thumbnail is drawn in code from real public sample data; no raster imagery.

### Topic coverage

Every topic in the owner's design-system standard has a home in this file: Typography, Internationalisation and RTL (Typography); Colour, Data-visualisation colours, Accessibility contrast (Colors); Spacing, Breakpoints and grid, Layout patterns, Z-index (Layout); Elevation (Elevation & Depth); Radius (Shapes); Component states, Iconography, Forms and validation, Empty, loading and error states, Motion, Accessibility (Components); Logo and brand, Imagery, Voice and tone (this Overview).

### Logo and brand

- **Public name:** "Channel Analyzer API". Names shown to anyone other than the owner must not start with "YouTube"; "YouTube Channel Analyzer" stays an internal project name.
- **Mark:** three rounded bars rising left to right (each 7 units wide on a 30 by 22 viewBox, heights 8, 14 and 20, corner radius 2). The two short bars take the current text colour (in the Swagger header they are fixed at the dark ground hex because that page is light-only); the tallest bar is the red. The mark reads as a quota meter.
- **Wordmark:** "Channel Analyzer" in Roboto 700 at 18px with -0.03em tracking, followed by a superscript "API" in Roboto 400 at 10px in the secondary text colour. Below 760px only the mark shows.
- **Reference, not borrowing:** youtube.com is the visual reference. No YouTube logo, play-button glyph, YouTube Sans or other brand asset is used (PRODUCT.md brand commitment). Roboto stands in for YouTube Sans.

### Imagery

No photography and no raster images ship. "Thumbnails" are HTML drawn in code on the sunken ground: a channel row, video stat lines, comments (one in Urdu, right to left), playlist lines, transcript segments, caption chips, shelf blocks, a search bar. Their sample text is real public data from one public channel, named on the page; no invented users, metrics or testimonials.

### Voice and tone

Plain, factual, owner to owner. Sentences state cost and consequence ("Reading stored data never spends quota"). Headings name the thing ("What it stores", "Calling the API"); no slogans, no exclamation. Numbers are exact and tabular. Heuristics are labelled as such ("Shorts flag (heuristic)"); hidden values are said to stay empty. Errors say what happened and what to try next. No em dashes anywhere; use colons, commas or periods.

## Colors

A near-monochrome video-site palette in grey steps, with one red signal and a muted method-colour set for HTTP verbs. Every value is hex; dark values are the defaults and each has a light counterpart (the `-light` keys).

### Primary
- **Live Red** (`red`): the single signal colour. Live dot, quota-day progress fill and scrub dot, the banner's elapsed edge and "now" line, the error status dot, and the tallest bar of the brand mark.
- **Now Tag Red** (`now-tag`): fill of the "now" label on the quota-day banner. It is darker than Live Red so its white text clears 4.5:1 (5.8:1); Live Red under white text would only reach 4.0:1.
- **Red Text** (`red-text`, light `red-text-light`): red used as text, where Live Red would fail contrast.
- **Elapsed Wash** (`red-soft`, light `red-soft-light`): the gradient end of the elapsed part of the quota-day banner.

### Secondary
- **Link Blue** (`link`, light `link-light`): links, the outline pill's text, focus rings, caret, text selection. Doubles as the GET method colour.

### Neutral
- **Night Ground** (`bg`) / **Paper Ground** (`bg-light`): page and masthead background.
- **Raised Ground** (`bg-raised`): the Up next header and the drawer. In light it equals the page ground.
- **Sunken Ground** (`bg-sunken`, light `bg-sunken-light`): thumbnails and the banner.
- **Chip Grey** (`chip`, light `chip-light`): the default fill for pills, chips, avatars, panels, description boxes, the selected guide row and the active queue row.
- **Chip Hover Grey** (`chip-hover`, light `chip-hover-light`): hover fill for every chip-grey control.
- **Selected Fill** (`chip-active` with `on-chip-active`): the inverted fill of a selected chip; it flips with the theme.
- **Hairline** (`line`, `line-soft` and light counterparts): dividers, tab rail, search border, thumbnail edge, banner hour lines.
- **Primary Text** (`text`), **Secondary Text** (`text-2`), **Tertiary Text** (`text-3`): the three text weights. Secondary carries meta lines, descriptions and counts.

### Status and HTTP methods
- **OK Green** (`ok`, `ok-soft`), **Warn Amber** (`warn`, `warn-soft`), **Error** (`error`): status dots, free and expensive quota costs, rule check marks.
- **Method colours** (`m-get`, `m-post`, `m-patch`, `m-delete` with their `-soft` fills): GET blue, POST green, PATCH and PUT amber, DELETE red-orange. In light the strong colours equal Link Blue, OK Green, Warn Amber and Error; the soft fills follow `m-get-soft-light`, `ok-soft-light`, `warn-soft-light` and `red-soft-light`.

### Overlays
- **Badge Scrim** (`scrim` with `on-scrim`): the duration-style badge on thumbnails. Same in both themes.
- **Drawer Scrim** (`drawer-scrim`): the dimmer behind the open guide drawer.

### Data-visualisation colours
Not applicable as a chart palette: no charts ship. The only data encodings are the quota-day progress (Live Red), cost values in the cost table (OK Green for 0 units, Warn Amber for 50 and 100 units, primary text otherwise), the method colours above, and the status dot. A future chart takes its series colours from the method set and keeps red for "now" only.

### Accessibility contrast
Measured pairs: secondary text on the dark ground 8.3:1, secondary text on Chip Grey 6.4:1, light secondary text on the light chip 5.6:1, Link Blue 7.4:1 (dark) and 5.8:1 (light), Red Text 5.9:1 (dark), white on Now Tag Red 5.8:1. Tertiary text reaches only 3.9:1 on the dark ground and 4.4:1 on the light sunken ground, so it is for placeholders, hour ticks and decorative marks, never for content a reader needs.

**The One Red Rule.** One red (#FF0033) is used only for live state and time progress, with one cited exception: the tallest bar of the brand mark, because the mark reads as a quota meter. Red is never decoration, never a button fill, never a heading.

**The Text-Coloured Button Rule.** The primary action is a pill filled in the text colour with the ground colour as its label. It inverts with the theme; it is never red and never blue.

## Typography

**Display Font:** Roboto (with Arial, sans-serif)
**Body Font:** Roboto (with Arial, sans-serif)
**Label/Mono Font:** Roboto Mono (with ui-monospace, SFMono-Regular, Menlo, monospace)

**Character:** One workhorse sans in three weights (400, 500, 700), as on the reference site, with a mono for routes, headers, JSON and numbers. Both are self-hosted variable WOFF2 files (latin and latin-ext subsets) because the service runs locally and must not depend on a font CDN.

### Hierarchy
- **Display** (700, 36px, 44px, -0.01em): the channel name only. Drops to 24px / 32px below 760px.
- **Title** (700, 20px, 28px): section headings, the watch title, the Up next heading, the banner caption.
- **Card** (500, 16px, 22px): card titles and panel headings; shelf headings use 700 at the same size. Tabs use 500 at 16px.
- **Body** (400, 14px, 20px): running text. Descriptions cap at 72 to 80ch.
- **Label** (500, 14px): pill and chip text, guide labels, queue titles.
- **Meta** (400, 12px, 18px): meta lines, counts, footers, badge text (500).
- **Code** (Roboto Mono 400, 13px, 1.4 to 1.6): inline code, curl snippets, cost numbers (500, tabular). The player JSON scales with `clamp(15px, 1.7vw, 22px)`.
- **Method** (Roboto Mono 700, 11px, 0.02em): HTTP verb badges.

**The Tabular Numbers Rule.** Any figure that changes or is compared (clock, cost column, counts in thumbnails) uses `font-variant-numeric: tabular-nums`.

### Internationalisation and RTL
The interface is English and left to right. Content samples prove mixed scripts: Urdu comment and transcript lines carry `lang="ur"` and `dir="rtl"`, are right-aligned, and embed timestamps as `dir="ltr"` spans. Roboto ships latin and latin-ext only; Urdu text falls back to the system Arabic-script font. A fully RTL interface is not applicable in this phase.

## Layout

A video-site shell: a sticky 56px masthead, a 240px left guide, and a content column capped at 1284px with 32px side padding (24px at 1100px and below, 16px at 760px and below).

### Spacing
A 4px base scale (`s-1` to `s-7`: 4, 8, 12, 16, 24, 32, 48). Gaps between controls are 8px; header blocks 24px; sections open with 48px. Card grid rows are 40px apart with 16px column gaps.

### Breakpoints and grid
- **Above 1312px:** watch layout is the player column plus a 402px Up next column; queue thumbnails 160px.
- **1312px and below:** Up next narrows to 360px; queue thumbnails 128px.
- **1100px and below:** the guide leaves the grid and becomes an off-canvas drawer; the watch layout stacks to one column.
- **760px and below:** masthead compacts (search button 44px, wordmark and pill labels hidden, status becomes a dot), the channel header stacks with a 72px avatar, the player becomes 4:3, the chip bar scrolls sideways with a fade, calling panels stack.
- **Card grid:** `repeat(auto-fill, minmax(280px, 1fr))`.
- **Swagger info section:** its own breakpoints at 1180px (actions move under the header, the third column spans the width, the store grid becomes 2 by 4) and 680px (single column, chip row scrolls with an edge fade).

### Layout patterns
Masthead with central pill search; left guide in sections with a footer; channel header (banner, round avatar, name, meta line, description, pills, tabs); watch layout (player, title, owner row, description box, Up next queue); card grid; chip bar over shelves of endpoint rows; two-panel "calling" row.

### Z-index
Masthead 20; drawer scrim 30; drawer 40; skip link 50. Nothing else stacks.

## Elevation & Depth

Flat by default. Depth comes from tonal steps (sunken thumbnails, chip-grey panels, raised drawer) and hairlines, not shadows.

### Shadow Vocabulary
- **Menu shadow** (`box-shadow: 0 4px 32px 0 #0000001A`): the guide drawer at 1100px and below. The token reserves it for menus and drawers.

**The Only-Drawers-Float Rule.** Only menus and drawers carry a shadow. Panels, cards, pills and thumbnails stay flat.

## Shapes

Soft, graded corners that encode role: 4px for small tags (method badges, time badges, inline code, focus ring), 8px for chips and queue thumbnails, 10px for guide rows and endpoint rows, 12px for cards, thumbnails, the player and panels, 16px for the banner, full pills for actions, search and status, and circles for avatars and status dots. Card thumbnails square their corners on hover, as on the reference site.

## Components

### Buttons (pills)
- **Shape:** full pill (999px), 36px tall, 16px side padding, 20px icons with an 8px gap.
- **Primary:** text-colour fill, ground-colour label; hover moves to secondary text colour.
- **Default:** Chip Grey fill, primary text; hover Chip Hover Grey.
- **Outline:** transparent with a hairline border and Link Blue label; hover fills with the GET soft blue and drops the border. Used for "Docs" in the masthead.
- **Icon button:** 40px circle, transparent, hover Chip Grey.

### Chips
- **Style:** 32px tall, 8px corners, Chip Grey fill, 500 weight label.
- **State:** selected (`aria-pressed` or `aria-current` true) inverts to the Selected Fill. Inside a panel, chips sit on the ground colour instead.

### Cards / Containers
- **Video card:** 16:9 thumbnail (12px corners, sunken ground, soft hairline, badge bottom right) above an avatar row with card title and secondary description.
- **Panel and description box:** Chip Grey, 12px corners, 12 to 16px padding, no border, no shadow.
- **Up next:** hairline-bordered 12px box with a raised header; the active row is Chip Grey with a play triangle in place of its number.

### Signature: the player
The live health response plays in a black 16:8 frame (4:3 on small screens) that stays dark in both themes, like a video player. A 3px quota-day progress bar in Live Red with a 13px scrub dot, a red LIVE dot (grey when the check fails), and a tabular clock sit along the bottom.

### Signature: the quota-day banner
A 24-hour strip, midnight to midnight Pacific, labelled every three hours in PKT. The elapsed part fades to the red wash and ends in a 2px Live Red line with the Now Tag.

### Inputs / Fields
- **Style:** the masthead search: 40px pill-left input on the ground colour with a hairline border, joined to a 64px Chip Grey search button.
- **Focus:** border turns Link Blue with a faint inner shadow; caret is Link Blue.

### Forms and validation
The endpoint search is the only form. It filters as you type and never submits data, so validation is not applicable. Disabled controls are shown only in the showcase (40% opacity, not-allowed cursor) and have no token yet.

### Navigation
- **Guide:** 40px rows, 10px corners, 24px icons, 24px icon-to-label gap; current row Chip Grey and 500 weight; hover Chip Grey. Becomes a drawer at 1100px and below (Escape or scrim closes it).
- **Tabs:** 48px tall, secondary text; hover shows a tertiary underline; current is primary text with a 2px text-colour underline.

### Status, methods and badges
- **Status:** 28px pill with an 8px dot: grey while checking, OK Green online, Live Red on error.
- **Method badge:** 22px tall, at least 52px wide, 4px corners, method colour on its soft fill.
- **Time badge:** Badge Scrim with white 12px text, bottom right of a thumbnail, carrying quota cost.

### Iconography
Inline SVG symbols on a 24px grid, stroked (1.75 width, round caps and joins, no fill, current colour). 24px in the guide and masthead, 20px inside pills and avatars. No icon font, no glyph icons, no emoji.

### Component states
Default, hover (one step lighter grey, or a soft fill for the outline pill), selected or current (inverted fill for chips, Chip Grey plus 500 weight for guide rows, underline for tabs), focus-visible (2px Link Blue outline, 2px offset, 4px corners), and disabled (showcase only, see Forms). Live states use `data-state` with `checking`, `ok` and `error`.

### Empty, loading and error states
- **Loading:** plain text in place, no spinners: "Checking" in the status pill, "Waiting for the first response" dimmed in the player, "Loading endpoints" in the empty box.
- **Empty:** a Chip Grey, 12px, centred box with secondary text that names the miss and the way out ("No route matches ... Try another word or the All chip").
- **Error:** status turns red with "Offline" or "Database error", the LIVE dot turns grey, the player prints the error in Red Text with a dimmed hint, and the endpoint box links to the API docs.

### Motion
- **Easing:** `cubic-bezier(0.16, 1, 0.3, 1)` (ease-out).
- **Durations:** 120ms for hover fills, 200ms for the drawer slide and the thumbnail corner change, 900ms for the progress bar and scrub dot.
- `prefers-reduced-motion: reduce` removes every transition and animation.

### Accessibility
Skip link to the main content; one focus ring everywhere; landmarks and labelled sections; the status and health output are live regions; the progress bar is a real `progressbar` with values; decorative SVG is `aria-hidden`; the theme button names the theme it switches to. Contrast figures are in Colors.

### Swagger UI info section
- The info section is built from `SERVICE_DESCRIPTION` HTML with the `ytca` class prefix and styled by `docs.css`, light theme only (the docs page pins `data-theme="light"`). Swagger's own endpoint list keeps its own look.
- Swagger's normalize CSS sets `a { background-color: transparent }` at higher specificity than the tokens, so `docs.css` re-applies the pill and chip backgrounds under `.swagger-ui .ytca`.
- `useUnsafeMarkdown` is on so the description keeps its classes. The description HTML must stay flush left with no blank lines, or the markdown renderer turns it into code blocks and paragraphs.
- Layout: compact channel header (88px avatar, name at 32/40, meta, description; actions in one row on the right), chip row, three columns divided by 1px hairlines with no outer boxes, then the store grid. The quota clock is live: `public/assets/docs.js` is injected by the docs route and updates the countdown and the red day bar every second.
- Swagger's own `.info p` rules outrank a light reset, so paragraph margins are reset at `.swagger-ui .information-container .ytca p` weight and deliberate paragraph sizes and margins carry `!important`; the list and heading reset uses `:where()` so layout margins win.

## Do's and Don'ts

### Do:
- **Do** keep Live Red (#FF0033) for live state and time progress, plus the tallest bar of the mark; use Red Text for red words and Now Tag Red (#CC0029) under white text.
- **Do** fill the primary action pill with the text colour and the default pill with Chip Grey.
- **Do** use 8px chips for filters and selection, and full pills for actions.
- **Do** draw thumbnails in code from real public sample data, on the sunken ground with a time badge.
- **Do** take every value from `tokens.css`, in hex, and give each new dark value a light counterpart.
- **Do** re-apply pill and chip backgrounds under `.swagger-ui .ytca` for anything placed in the Swagger description.

### Don't:
- **Don't** use any YouTube logo, play-button glyph, YouTube Sans or brand asset, and don't start a public name with "YouTube".
- **Don't** use red for decoration, buttons, headings or emphasis.
- **Don't** put a shadow on cards, panels, pills or thumbnails; only menus and drawers float.
- **Don't** set content text in Tertiary Text; it falls below 4.5:1 on the dark ground.
- **Don't** add blank lines or indentation inside `SERVICE_DESCRIPTION`.
- **Don't** use em dashes in interface copy.
