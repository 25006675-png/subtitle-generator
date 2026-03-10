# SubVela Website Handoff

> Comprehensive reference for rebuilding the SubVela landing page in a new repository.
> Tech stack: **Plain HTML + Tailwind CSS (CDN)** deployed on **Vercel**.

---

## Table of Contents

1. [Brand Guidelines](#1-brand-guidelines)
2. [Site Structure & Layout](#2-site-structure--layout)
3. [SEO & Meta Tags](#3-seo--meta-tags)
4. [Marketing Copy](#4-marketing-copy)
5. [Animated Hero Section — Complete Code](#5-animated-hero-section--complete-code)
6. [Brand Assets — File Reference](#6-brand-assets--file-reference)
7. [CJK Font-Mapping Feature (Marketing Context)](#7-cjk-font-mapping-feature)
8. [Feature Highlights for Landing Page](#8-feature-highlights-for-landing-page)

---

## 1. Brand Guidelines

### Core Palette

| Token | Hex | Usage |
|---|---|---|
| Navy Deep | `#060A14` | Page background, dark sections |
| Blue | `#3B82F6` | Primary brand blue, buttons, links, hull accent |
| Blue Light | `#60A5FA` | Logo sail, "Vela" text, highlights, hover states |
| Blue Pale | `#93C5FD` | Secondary text on dark, subtle accents |
| White | `#F1F5F9` | Primary text on dark backgrounds (slate-100) |

### Suggested Extended Palette (for UI elements)

| Token | Hex | Usage |
|---|---|---|
| Surface | `#0B1120` | Card backgrounds, elevated surfaces on navy |
| Surface Hover | `#111827` | Hover states for cards/buttons |
| Border | `#1E293B` | Subtle borders, dividers (slate-800) |
| Text Muted | `#94A3B8` | Secondary body text, captions (slate-400) |
| Success | `#22C55E` | Status indicators, "free" badge |
| CTA Gradient Start | `#3B82F6` | Button gradient left |
| CTA Gradient End | `#60A5FA` | Button gradient right |

### Typography

| Role | Font | Weight | Fallbacks |
|---|---|---|---|
| Brand name "Sub" | Geist | 200 (ExtraLight) | SF Pro Display, Segoe UI, sans-serif |
| Brand name "Vela" | Geist | 600 (SemiBold) | SF Pro Display, Segoe UI, sans-serif |
| Headings | Geist | 600 | SF Pro Display, Segoe UI, sans-serif |
| Body text | Geist | 400 | SF Pro Display, Segoe UI, sans-serif |
| Code / technical | JetBrains Mono | 300–400 | monospace |

**Google Fonts import:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@200;400;600&family=JetBrains+Mono:wght@300;400&display=swap" rel="stylesheet">
```

### Logo Construction

The SubVela logo is composed of three geometric elements:

1. **Sail** — a triangle (`#60A5FA`, 40% opacity), pointing right
2. **Hull 1** — a rounded rectangle (`#60A5FA`, 80% opacity), wider bar
3. **Hull 2** — a smaller rounded rectangle (`#3B82F6`, 40% opacity), below hull 1

The wordmark reads **Sub** (white, weight 200) + **Vela** (blue-light `#60A5FA`, weight 600) in Geist at 58px, letter-spacing -1px.

A subtle wake line (`#60A5FA`, 20% opacity) extends horizontally from the hull.

### Design Principles

- **Dark-first**: Navy deep background is the default. All content is designed for dark mode.
- **Blue monochrome**: The entire palette is built on blue. No competing hue families.
- **Minimal motion**: Animations are subtle — bobs, shimmers, gentle fades. Nothing flashy.
- **Generous whitespace**: Sections breathe. No visual clutter.

---

## 2. Site Structure & Layout

### Page Sections (top to bottom)

```
┌─────────────────────────────────────────────┐
│  NAV BAR                                    │
│  Logo (left) | GitHub  Download (right)     │
├─────────────────────────────────────────────┤
│                                             │
│  HERO SECTION                               │
│  Animated logo assembly (cursor → audio     │
│  wave → subtitles → logo settles)           │
│  Tagline + Sub-tagline                      │
│  Two CTA buttons: GitHub | Download         │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  FEATURES GRID (3 columns on desktop)       │
│  Card 1: AI Transcription                   │
│  Card 2: CJK Font Engine                   │
│  Card 3: Bilingual Subtitles               │
│  Card 4: Style Presets                      │
│  Card 5: Karaoke Modes                      │
│  Card 6: 100% Free & Open Source            │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  CTA SECTION                                │
│  "Ready to set sail?" + buttons             │
│  GitHub link + Download installer link      │
│                                             │
├─────────────────────────────────────────────┤
│  FOOTER                                     │
│  "Built with care" | GitHub | License       │
└─────────────────────────────────────────────┘
```

### Responsive Breakpoints

| Breakpoint | Behavior |
|---|---|
| `<640px` (mobile) | Single column, hero scales down, nav collapses |
| `640–1024px` (tablet) | 2-column feature grid |
| `>1024px` (desktop) | 3-column feature grid, full hero animation |

### Tailwind Config Hints

```html
<!-- CDN approach — add to <head> -->
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          navy: { deep: '#060A14' },
          brand: {
            blue: '#3B82F6',
            light: '#60A5FA',
            pale: '#93C5FD',
          },
          surface: '#0B1120',
        },
        fontFamily: {
          geist: ['Geist', 'SF Pro Display', 'Segoe UI', 'sans-serif'],
          mono: ['JetBrains Mono', 'monospace'],
        },
      },
    },
  }
</script>
```

---

## 3. SEO & Meta Tags

```html
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>SubVela — AI-Powered Subtitle Generator</title>
  <meta name="description" content="Generate, translate, and style subtitles with AI. Automatic CJK font mapping, bilingual support, karaoke modes, and beautiful presets. 100% free and open source.">
  <meta name="keywords" content="subtitle generator, AI subtitles, CJK font mapping, bilingual subtitles, karaoke subtitles, Whisper transcription, open source, free subtitle tool">
  <meta name="author" content="SubVela">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="SubVela — AI-Powered Subtitle Generator">
  <meta property="og:description" content="Generate, translate, and style subtitles with AI. Automatic CJK font mapping, bilingual support, and karaoke modes. Free and open source.">
  <meta property="og:image" content="/og-image.png"> <!-- 1200x630 recommended -->
  <meta property="og:url" content="https://subvela.app"> <!-- update when domain is set -->

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="SubVela — AI-Powered Subtitle Generator">
  <meta name="twitter:description" content="AI transcription, CJK font mapping, bilingual subtitles, and karaoke modes. 100% free.">
  <meta name="twitter:image" content="/og-image.png">

  <!-- Favicon strategy -->
  <!-- Generate from the logo-transparent.svg: -->
  <!-- 1. favicon.ico (32x32) -->
  <!-- 2. apple-touch-icon.png (180x180) -->
  <!-- 3. favicon-32x32.png, favicon-16x16.png -->
  <!-- 4. site.webmanifest with name "SubVela" and theme_color "#060A14" -->
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <meta name="theme-color" content="#060A14">
</head>
```

---

## 4. Marketing Copy

### Tagline (Hero)

**Primary:** "Subtitles, powered by AI."

**Sub-tagline:** "Generate, translate, and style — in any language. Free forever."

### Feature Cards Copy

**Card 1 — AI Transcription**
- Headline: "One-Click AI Transcription"
- Body: "Drop a video, get subtitles. Powered by OpenAI Whisper with word-level timestamps — no API keys, no cloud, no cost."

**Card 2 — CJK Font Engine**
- Headline: "Smart CJK Font Mapping"
- Body: "Chinese, Japanese, and Korean text automatically gets the right font. No more missing glyphs or boxes — SubVela handles it."

**Card 3 — Bilingual Subtitles**
- Headline: "Bilingual, Built In"
- Body: "Show original and translated text together. Position, style, and animate each line independently."

**Card 4 — Style Presets**
- Headline: "8 Pro Style Presets"
- Body: "YouTube CC, Netflix, TikTok Viral, Cinematic Gold, Neon Glow, K-Drama Soft, Gaming HUD, and Minimalist — one click to look professional."

**Card 5 — Karaoke Modes**
- Headline: "Karaoke & Animation"
- Body: "Classic highlight, word-by-word reveal, and popup modes. Add fade, slide, or pop transitions to any subtitle."

**Card 6 — Free & Open Source**
- Headline: "100% Free. Forever."
- Body: "No subscriptions, no watermarks, no limits. Open source under MIT. Your subtitles, your data, your machine."

### CTA Section Copy

- Headline: "Ready to set sail?"
- Sub-text: "Download SubVela and start generating subtitles in minutes."
- Button 1: "View on GitHub" (outline style, links to GitHub repo)
- Button 2: "Download for Windows" (filled gradient style, links to releases)

### Footer Copy

"Built with care by the SubVela team. Free and open source."

---

## 5. Animated Hero Section — Complete Code

This is the final animated logo assembly. It runs once on page load: cursor clicks play button, audio waveform pulses, subtitle text appears, then all elements morph into the SubVela logo which settles with a gentle bob.

Total animation duration: ~8 seconds to settle, then infinite idle loop.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SubVela — Play to Sail v5</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@200;400;600&family=JetBrains+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --navy-deep: #060A14;
    --blue: #3B82F6;
    --blue-light: #60A5FA;
    --blue-pale: #93C5FD;
    --white: #F1F5F9;
  }

  body {
    background: var(--navy-deep);
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh; overflow: hidden;
  }

  .stage { position: relative; width: 900px; height: 500px; }

  /* FINAL CONTAINER — 720x280, centered on stage */
  .final-container {
    position: absolute;
    left: 50%; top: 50%;
    transform: translate(-50%, -50%);
    width: 720px; height: 280px;
    pointer-events: none;
    animation: vesselBob 5s ease-in-out 7.5s infinite;
  }
  @keyframes vesselBob {
    0%, 100% { transform: translate(-50%, -50%) translateY(0); }
    30% { transform: translate(-50%, -50%) translateY(-3px); }
    70% { transform: translate(-50%, -50%) translateY(2px); }
  }

  /* SAIL — 88x104 SVG */
  .sail-svg {
    position: absolute;
    left: 110px; top: 28px;
    width: 88px; height: 104px;
    transform-origin: center;
    will-change: transform, opacity;
    animation: sailJourney 8s forwards,
               sailFlutter 4s ease-in-out 7.5s infinite;
  }
  @keyframes sailJourney {
    0%      { opacity: 0;    transform: translate(206px, 60px) scale(2.5); }
    5%      { opacity: 0.7;  transform: translate(206px, 60px) scale(2.5); }
    15%     { opacity: 0.7;  transform: translate(206px, 60px) scale(2.5); }
    17%     { opacity: 0.8;  transform: translate(206px, 60px) scale(2.2); }
    18%     { opacity: 0.8;  transform: translate(206px, 60px) scale(2.7); }
    20%     { opacity: 0;    transform: translate(206px, 60px) scale(3);
              animation-timing-function: linear; }
    48%     { opacity: 0;    transform: translate(206px, 60px) scale(1.5);
              animation-timing-function: cubic-bezier(0.4, 0, 1, 1); }
    64%     { opacity: 0.25; transform: translate(80px, 24px) scale(1.18);
              animation-timing-function: cubic-bezier(0, 0, 0.2, 1); }
    82%     { opacity: 0.4;  transform: translate(0px, 0px) scale(1); }
    100%    { opacity: 0.4;  transform: translate(0px, 0px) scale(1); }
  }
  @keyframes sailFlutter {
    0%, 100% { transform: scaleX(1) skewY(0deg); }
    30% { transform: scaleX(1.03) skewY(-0.8deg); }
    70% { transform: scaleX(0.98) skewY(0.4deg); }
  }

  /* HULL 1 — morphs from subtitle bar to boat hull */
  .hull1 {
    position: absolute;
    background: var(--blue-light);
    opacity: 0;
    will-change: left, top, width, height, opacity;
    animation: hull1Journey 8s forwards,
               hullRip1 3s ease-in-out 7.5s infinite;
  }
  @keyframes hull1Journey {
    0%    { left: 275px; top: 139px; width: 170px; height: 3px; border-radius: 1.5px; opacity: 0; }
    44%   { left: 275px; top: 139px; width: 170px; height: 3px; border-radius: 1.5px; opacity: 0;
            animation-timing-function: ease-out; }
    50%   { left: 275px; top: 139px; width: 170px; height: 3px; border-radius: 1.5px; opacity: 0.65;
            animation-timing-function: cubic-bezier(0, 0, 0.2, 1); }
    82%   { left: 52px;  top: 158px; width: 176px; height: 10px; border-radius: 5px; opacity: 0.8; }
    100%  { left: 52px;  top: 158px; width: 176px; height: 10px; border-radius: 5px; opacity: 0.8; }
  }
  @keyframes hullRip1 {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(3px); }
  }

  /* HULL 2 */
  .hull2 {
    position: absolute;
    background: var(--blue);
    opacity: 0;
    will-change: left, top, width, height, opacity;
    animation: hull2Journey 8s forwards,
               hullRip2 3.5s ease-in-out 7.5s infinite;
  }
  @keyframes hull2Journey {
    0%    { left: 303px; top: 165px; width: 115px; height: 3px; border-radius: 1.5px; opacity: 0; }
    46%   { left: 303px; top: 165px; width: 115px; height: 3px; border-radius: 1.5px; opacity: 0;
            animation-timing-function: ease-out; }
    52%   { left: 303px; top: 165px; width: 115px; height: 3px; border-radius: 1.5px; opacity: 0.5;
            animation-timing-function: cubic-bezier(0, 0, 0.2, 1); }
    84%   { left: 80px;  top: 182px; width: 120px; height: 8px; border-radius: 4px; opacity: 0.4; }
    100%  { left: 80px;  top: 182px; width: 120px; height: 8px; border-radius: 4px; opacity: 0.4; }
  }
  @keyframes hullRip2 {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(5px); }
  }

  /* WAKE — SVG wave path with SMIL curve-to-straight animation */
  .wake-svg {
    position: absolute;
    left: 52px; top: 137px;
    width: 540px; height: 16px;
    opacity: 0;
    transform-origin: left center;
    will-change: transform, opacity;
    animation: wakeReveal 8s forwards,
               wakeShim 4s ease-in-out 7.5s infinite;
  }
  @keyframes wakeReveal {
    0%    { opacity: 0; transform: scaleX(0); }
    56%   { opacity: 0; transform: scaleX(0);
            animation-timing-function: ease-out; }
    66%   { opacity: 0.35; transform: scaleX(1);
            animation-timing-function: linear; }
    82%   { opacity: 0.2; transform: scaleX(1); }
    100%  { opacity: 0.2; transform: scaleX(1); }
  }
  @keyframes wakeShim {
    0%, 100% { opacity: 0.2; }
    50% { opacity: 0.3; }
  }

  /* TEXT — SubVela wordmark */
  .final-text {
    position: absolute;
    left: 245px; top: 66px;
    font-family: 'Geist', 'SF Pro Display', 'Segoe UI', sans-serif;
    font-size: 58px;
    letter-spacing: -1px;
    line-height: 1;
    opacity: 0;
    overflow: hidden;
    animation: textUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) 5.8s forwards;
  }
  .final-text .sub { font-weight: 200; color: var(--white); }
  .final-text .vela { font-weight: 600; color: var(--blue-light); }

  @keyframes textUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .final-text::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(96,165,250,0.25), transparent);
    animation: sweepShim 0.8s ease-in-out 6.5s forwards;
    left: -100%; width: 50%;
  }
  @keyframes sweepShim { from { left: -50%; } to { left: 150%; } }

  /* WATER PARTICLES — idle */
  .wp { position: absolute; border-radius: 50%; background: var(--blue); }
  .wp1 { width: 3px; height: 3px; left: 180px; top: 162px; animation: wdrift 3s ease-in-out 7.5s infinite; }
  .wp2 { width: 2px; height: 2px; left: 150px; top: 175px; animation: wdrift 3.5s ease-in-out 7.9s infinite; }
  .wp3 { width: 2.5px; height: 2.5px; left: 200px; top: 168px; animation: wdrift 4s ease-in-out 8.3s infinite; }
  @keyframes wdrift {
    0% { transform: translateX(0); opacity: 0; }
    15% { opacity: 0.3; }
    85% { opacity: 0.3; }
    100% { transform: translateX(-80px); opacity: 0; }
  }

  /* STAGE-LEVEL ELEMENTS */

  .play-glow {
    position: absolute;
    left: 50%; top: 50%;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(96,165,250,0.06) 0%, transparent 70%);
    transform: translate(-50%, -50%);
    opacity: 0;
    animation: glowFadeIn 0.6s ease-out 0.3s forwards,
               glowFadeOut 0.4s ease-in 1.4s forwards;
  }
  @keyframes glowFadeIn { to { opacity: 1; } }
  @keyframes glowFadeOut { to { opacity: 0; transform: translate(-50%, -50%) scale(1.5); } }

  .cursor-wrap {
    position: absolute;
    left: 640px; top: 390px;
    width: 24px; height: 24px;
    opacity: 0;
    z-index: 10;
    will-change: transform, opacity;
    animation: cursorSlide 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.8s forwards,
               cursorClick 0.15s ease-in-out 1.35s forwards,
               cursorOut 0.4s ease-in 1.55s forwards;
  }
  @keyframes cursorSlide {
    from { opacity: 0; left: 640px; top: 390px; }
    to   { opacity: 0.9; left: 455px; top: 255px; }
  }
  @keyframes cursorClick {
    0%   { transform: scale(1); }
    50%  { transform: scale(0.82); }
    100% { transform: scale(1); }
  }
  @keyframes cursorOut { to { opacity: 0; } }

  .click-ring {
    position: absolute;
    left: 50%; top: 50%;
    width: 30px; height: 30px;
    border-radius: 50%;
    border: 2px solid var(--blue-light);
    transform: translate(-50%, -50%) scale(0);
    opacity: 0;
    animation: ringPop 0.6s ease-out 1.35s forwards;
  }
  .click-ring-2 {
    animation-delay: 1.42s;
    border-color: var(--blue);
  }
  @keyframes ringPop {
    0%   { transform: translate(-50%, -50%) scale(0); opacity: 0.6; }
    100% { transform: translate(-50%, -50%) scale(5); opacity: 0; }
  }

  .wave-container {
    position: absolute;
    left: 50%; top: 50%;
    transform: translate(-50%, -50%);
    display: flex; align-items: center; gap: 5px;
    height: 100px;
    opacity: 0;
    animation: waveIn 0.25s ease-out 1.55s forwards,
               wavePulse 0.4s ease-in-out 1.8s 2,
               waveOut 0.4s ease-in 2.5s forwards;
  }
  @keyframes waveIn { to { opacity: 1; } }
  @keyframes wavePulse {
    0%, 100% { transform: translate(-50%, -50%) scaleY(1); }
    50% { transform: translate(-50%, -50%) scaleY(1.15); }
  }
  @keyframes waveOut {
    to { opacity: 0; transform: translate(-50%, -50%) scaleY(0.5); }
  }

  .bar {
    width: 3.5px; border-radius: 2px;
    background: var(--blue-light);
    height: var(--h);
    opacity: var(--op);
    animation: barPulse var(--dur) ease-in-out infinite;
  }
  @keyframes barPulse {
    0%, 100% { height: var(--h); }
    50% { height: var(--h2); }
  }

  /* Subtitle text (centered on stage) */
  .sub-text {
    position: absolute;
    left: 50%; transform: translateX(-50%);
    white-space: nowrap;
    opacity: 0;
  }
  .sub-text-1 {
    top: 242px;
    font-family: 'Geist', sans-serif;
    font-size: 17px;
    font-weight: 400;
    color: var(--white);
    animation: subClipIn 0.6s ease-out 2.7s forwards,
               subOut 0.4s ease-in 3.5s forwards;
  }
  .sub-text-2 {
    top: 268px;
    font-family: 'Geist', sans-serif;
    font-size: 16px;
    font-weight: 400;
    color: var(--blue-pale);
    animation: subClipIn 0.6s ease-out 3s forwards,
               subOut 0.4s ease-in 3.6s forwards;
  }
  @keyframes subClipIn {
    from { opacity: 0; clip-path: inset(0 100% 0 0); }
    to   { opacity: 0.85; clip-path: inset(0 0 0 0); }
  }
  @keyframes subOut { to { opacity: 0; transform: translateX(-50%) scaleY(0.2) scaleX(0.6); } }

  .glow {
    position: absolute; left: 50%; top: 50%;
    width: 350px; height: 350px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%);
    transform: translate(-50%, -50%);
    opacity: 0;
    animation: glowIn 0.8s ease-out 4.5s forwards,
               glowBreathe 5s ease-in-out 7.5s infinite;
    pointer-events: none;
  }
  @keyframes glowIn { to { opacity: 1; } }
  @keyframes glowBreathe {
    0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
    50% { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
  }
</style>
</head>
<body>

<div class="stage">
  <div class="play-glow"></div>
  <div class="click-ring"></div>
  <div class="click-ring click-ring-2"></div>

  <svg class="cursor-wrap" viewBox="0 0 24 30" fill="none">
    <path d="M5 2l0 20 5.5-5.5L16 26h3l-6-10 7-2z" fill="var(--white)" stroke="rgba(0,0,0,0.25)" stroke-width="0.8" stroke-linejoin="round"/>
  </svg>

  <div class="wave-container">
    <div class="bar" style="--h:22px;--h2:12px;--dur:0.5s;--op:0.35"></div>
    <div class="bar" style="--h:40px;--h2:20px;--dur:0.45s;--op:0.5"></div>
    <div class="bar" style="--h:60px;--h2:28px;--dur:0.4s;--op:0.65"></div>
    <div class="bar" style="--h:45px;--h2:22px;--dur:0.5s;--op:0.55"></div>
    <div class="bar" style="--h:80px;--h2:35px;--dur:0.35s;--op:0.8"></div>
    <div class="bar" style="--h:95px;--h2:42px;--dur:0.3s;--op:0.9"></div>
    <div class="bar" style="--h:70px;--h2:32px;--dur:0.4s;--op:0.7"></div>
    <div class="bar" style="--h:88px;--h2:40px;--dur:0.35s;--op:0.85"></div>
    <div class="bar" style="--h:55px;--h2:25px;--dur:0.45s;--op:0.6"></div>
    <div class="bar" style="--h:75px;--h2:34px;--dur:0.38s;--op:0.75"></div>
    <div class="bar" style="--h:50px;--h2:24px;--dur:0.45s;--op:0.55"></div>
    <div class="bar" style="--h:30px;--h2:15px;--dur:0.5s;--op:0.4"></div>
  </div>

  <!-- Subtitle text: positioned to match hull start positions -->
  <div class="sub-text sub-text-1">Hello, how are you?</div>
  <div class="sub-text sub-text-2">你好，你好吗？</div>

  <div class="glow"></div>

  <div class="final-container">
    <svg class="sail-svg" viewBox="0 0 88 104" fill="none">
      <polygon points="0,0 0,104 88,52" fill="#60A5FA"/>
    </svg>

    <div class="hull1"></div>
    <div class="hull2"></div>

    <svg class="wake-svg" viewBox="0 0 540 16" fill="none">
      <path d="M0 8 C45 0, 90 16, 135 8 C180 0, 225 16, 270 8 C315 0, 360 16, 405 8 C450 0, 495 12, 540 8"
            stroke="#60A5FA" stroke-width="1.5" fill="none" stroke-linecap="round">
        <animate attributeName="d"
                 values="M0 8 C45 0, 90 16, 135 8 C180 0, 225 16, 270 8 C315 0, 360 16, 405 8 C450 0, 495 12, 540 8;
                         M0 8 C45 2, 90 14, 135 8 C180 2, 225 14, 270 8 C315 2, 360 14, 405 8 C450 2, 495 11, 540 8;
                         M0 8 C45 5, 90 11, 135 8 C180 5, 225 11, 270 8 C315 5, 360 11, 405 8 C450 5, 495 9.5, 540 8;
                         M0 8 C45 7, 90 9, 135 8 C180 7, 225 9, 270 8 C315 7, 360 9, 405 8 C450 7, 495 8.5, 540 8;
                         M0 8 C45 8, 90 8, 135 8 C180 8, 225 8, 270 8 C315 8, 360 8, 405 8 C450 8, 495 8, 540 8"
                 keyTimes="0; 0.2; 0.45; 0.75; 1"
                 dur="3.5s" begin="4.6s" fill="freeze"
                 calcMode="spline"
                 keySplines="0.4 0 0.2 1; 0.4 0 0.2 1; 0.4 0 0.2 1; 0.4 0 0.2 1"/>
      </path>
    </svg>

    <span class="final-text">
      <span class="sub">Sub</span><span class="vela">Vela</span>
    </span>

    <div class="wp wp1"></div>
    <div class="wp wp2"></div>
    <div class="wp wp3"></div>
  </div>
</div>

</body>
</html>
```

### Animation Sequence Summary

| Time | Event |
|---|---|
| 0.3s | Play button glow fades in |
| 0.8s | Cursor slides toward center |
| 1.35s | Cursor clicks, ring ripples expand |
| 1.55s | Audio waveform bars appear and pulse |
| 2.5s | Waveform fades out |
| 2.7s | Subtitle line 1 clips in: "Hello, how are you?" |
| 3.0s | Subtitle line 2 clips in: "你好，你好吗？" |
| 3.5s | Subtitle lines compress/morph out |
| 4.5s | Background glow fades in |
| 4.6s | Wake SVG wave begins flattening (SMIL, 3.5s) |
| 5.8s | "SubVela" wordmark slides up |
| 6.5s | Shimmer sweep across wordmark |
| 7.5s | Idle loop begins: vessel bob, sail flutter, hull ripple, wake shimmer, water particles |

---

## 6. Brand Assets — File Reference

Copy these files from the subtitle-generator repo into the new website repo:

| File | Path (in source repo) | Usage |
|---|---|---|
| Logo (transparent) | `assets/logo/brand-kit-final/logo-transparent.svg` | Favicon source, nav logo |
| Logo (with bg) | `assets/logo/brand-kit-final/logo-bg.svg` | OG image background |
| Trademark (dark bg) | `assets/logo/brand-kit-final/trademark-dark.svg` | For light backgrounds (unlikely, but available) |
| Trademark (white) | `assets/logo/brand-kit-final/trademark-white.svg` | Nav bar wordmark, footer logo — 720x280 viewBox |
| Animated hero | `assets/logo/brand-kit-final/animated.html` | Hero section (code included above in Section 5) |

### SVG Quick Reference

**logo-transparent.svg** (400x400 viewBox): Sail + two hulls, no text. Use for favicon/app icon.

**trademark-white.svg** (720x280 viewBox): Full logo with "SubVela" wordmark and wake line. Designed for dark backgrounds. Use in navbar and footer.

---

## 7. CJK Font-Mapping Feature

### Marketing Description (user-facing)

SubVela's CJK font engine automatically detects Chinese, Japanese, and Korean characters in your subtitles and selects the correct font — no configuration needed. When your subtitle contains mixed-language text (e.g., English and Chinese together), SubVela renders each script with its native font while keeping everything visually cohesive.

**What it solves:** Most subtitle tools render CJK text as empty boxes or use the wrong font, producing ugly or unreadable subtitles. SubVela scans your system fonts, builds a smart catalog with alias resolution, and picks the best available CJK font automatically.

**Scripts supported:**
- Chinese Simplified & Traditional (CJK Unified Ideographs)
- Japanese (Hiragana, Katakana, Kanji)
- Korean (Hangul)
- Extended CJK (Rare characters block)

**How users experience it:** They just type or transcribe. SubVela handles the rest. If they want a specific CJK font, they can select it from the font dropdown — the catalog shows localized font names alongside English names (e.g., "微软雅黑 (Microsoft YaHei)").

---

## 8. Feature Highlights for Landing Page

### Marketable Values Summary

| Feature | User Benefit | Differentiator |
|---|---|---|
| AI Transcription (Whisper) | Drop a video, get subtitles with word-level timestamps | Runs 100% locally — no API keys, no uploads, no cost |
| CJK Font Engine | Chinese/Japanese/Korean text always renders correctly | Automatic detection + system font catalog with alias resolution |
| Bilingual Subtitles | Show original + translation on screen simultaneously | Independent styling and positioning per language line |
| Style Presets | One-click professional looks (YouTube, Netflix, TikTok, etc.) | 8 built-in presets + save custom presets |
| Karaoke Modes | Word-by-word highlight synced to audio | Classic, word-by-word, and popup modes with configurable animations |
| Shadow & Glow | Cinematic text effects with real-time preview | Gaussian blur glow, configurable shadow offset/blur |
| Export Formats | SRT, ASS, and burn-in (hardcoded into video) | FFmpeg burn-in with full style preservation |
| 100% Free & Open Source | No subscriptions, watermarks, or limits | MIT license, all processing on user's machine |

### Preset Names (for showcasing)

1. YouTube CC
2. Netflix
3. TikTok Viral
4. Cinematic Gold
5. Neon Glow
6. K-Drama Soft
7. Gaming HUD
8. Minimalist

### Key Technical Specs (for a "specs" section if desired)

- Transcription engine: OpenAI Whisper (faster-whisper, local)
- Video backend: mpv (hardware-accelerated)
- UI framework: CustomTkinter (native-feeling, dark mode)
- Export: SRT, ASS, FFmpeg burn-in
- Platform: Windows (macOS/Linux planned)
- License: MIT

---

## Notes for the New Repo

1. **Vercel deployment**: For plain HTML + Tailwind CDN, just put `index.html` in the repo root. Vercel auto-detects static sites.
2. **OG image**: Create a 1200x630 image using the logo on navy background with the tagline. Use `logo-bg.svg` as the base.
3. **Favicon**: Convert `logo-transparent.svg` to ICO/PNG at 16, 32, 180px sizes. Tools: realfavicongenerator.net or `sharp` CLI.
4. **CTA links**: Use `https://github.com/YOUR_USERNAME/subvela` as placeholder until repo is created. For downloads, link to GitHub Releases page.
5. **Hero responsiveness**: The animated hero is 900x500 fixed. For mobile, consider scaling it down with `transform: scale(0.5)` inside a container, or showing a static logo instead.
6. **Performance**: The hero uses pure CSS animations + one SMIL animate. No JavaScript required. Very lightweight.
