# Skill: 47doors Deck Design (for Manus)

**Confidence:** medium
**Use when:** Building a slide deck that should feel visually continuous with the 47doors web app — specifically for Sean Gayle's NYU ITP/IMA talk where the projector alternates between slides and the live Oracle demo.

**Outcome:** A deck whose typography, color, spacing, and motion language are indistinguishable from the product the audience is about to see on screen. When Sean cuts from slide to demo, the audience should feel zero visual whiplash.

---

## 1. The Two Registers

The 47doors app has **two distinct visual registers**. Your deck must master both and know when to use each.

### Register A — "Product UI" (calm, trustworthy, institutional)
Used on: chat, tickets, admin, runbook pages.
Use in slides for: agenda, architecture diagrams, code, tool screenshots, takeaways, Q&A.

### Register B — "Oracle Stage" (cinematic, mythic, charged)
Used on: `/oracle` projector page.
Use in slides for: section openers, provocations, ethics moments, the attack-rehearsal reveal, closing.

**Rule:** Never mix registers within a single slide. Transition between them at section boundaries only.

---

## 2. Design Tokens (copy these exactly)

### Typography
- **Sans:** `Inter`, fallback `system-ui, sans-serif`. Use for 100% of UI-register slides and 100% of body copy.
- **Mono:** `JetBrains Mono`, fallback `Menlo, monospace`. Use for code, file paths, terminal output, CLI commands.
- **Weights:** 400 body, 500 nav/labels, 600 headings, 700 emphasis, **900 (black)** for Oracle-register hero type only.
- **Tracking:**
  - Default: normal.
  - Micro-labels (uppercase eyebrows above Oracle hero text): `letter-spacing: 0.4em–0.6em`. ALL CAPS. Tiny (11–13px). Low opacity (60–70%).
- **Oracle hero type:** 14vw or larger, `font-weight: 900`, `line-height: 0.95–1.0`, `letter-spacing: -0.02em` (tight).

### Color palette

**UI register (light):**
| Token | Hex | Use |
|---|---|---|
| Primary 600 | `#2563eb` | Buttons, links, active nav, accent fills |
| Primary 500 | `#3b82f6` | Focus rings, hover states |
| Primary 50 | `#eff6ff` | Button hover backgrounds |
| Gray 900 | `#111827` | Headings, primary text |
| Gray 600 | `#4b5563` | Secondary text |
| Gray 500 | `#6b7280` | Tertiary text, taglines |
| Gray 200 | `#e5e7eb` | Borders, dividers |
| Gray 100 | `#f3f4f6` | Card backgrounds, muted fills |
| Gray 50 | `#f9fafb` | Page background |
| White | `#ffffff` | Card surfaces, header background |
| Success 500 | `#10b981` | Status OK, "ticket created", safe guardrail pass |
| Warning 500 | `#f59e0b` | Escalation, caution, "Oracle senses" eyebrow |
| Error 500 | `#ef4444` | Blocked, violations, red-team attack slides |

**Oracle register (dark):**
| Token | Hex | Use |
|---|---|---|
| Stage black | `#000000` | Base background for Oracle-register slides |
| Deep ink | rgba(0,0,0,0.85) | Vignette bottom |
| Soft ink | rgba(0,0,0,0.30) | Vignette mid |
| Amber 200 | `#fde68a` (at 60% opacity) | Eyebrows, "ORACLE LISTENS" labels |
| Amber 100 italic | `#fef3c7` (at 90%) | Italic emphasis inside Oracle hero text |
| Red 300 | `#fca5a5` (at 70%) | BLOCKED state eyebrow only |
| White 95 | rgba(255,255,255,0.95) | Oracle hero type |
| White 85 | rgba(255,255,255,0.85) | Whispered sub-text |
| Emerald 400 | `#34d399` | Live-listening status dot (pulsing) |

### Spacing & rhythm
- Base unit: 4px. All spacing is a multiple (4, 8, 12, 16, 24, 32, 48, 64, 96).
- Slide margin: 64–96px from edge on UI slides. Oracle slides can bleed to edge.
- Card radius: `rounded-lg` = 8px. Buttons `rounded-full` or `rounded-lg`.
- Dividers: 1px solid `#e5e7eb`, never heavier.

### Iconography
- Use **Heroicons outline style** exclusively for UI-register icons (24px, 1.5px stroke).
- Common ones in this product: chat bubble, ticket, cog, clipboard-document-list, tv, sun/moon, trash.
- Never mix icon libraries. Never use emoji as icons on UI-register slides.
- Oracle register: NO icons. Typography and image do all the work.

### Motion
- UI-register transitions: **150–300ms, ease-in-out**. Subtle. Opacity + 10px Y offset only.
- Oracle-register transitions: **1400–1800ms, ease-out**. Long cross-fades between images. No slide-ins, no bounces, no spins — the Oracle is not a Keynote template.
- Pulsing live-indicator: `animate-ping` style — 2s cycle, ease-out, opacity 0.5 → 0.
- NEVER: page curls, 3D flips, confetti, sparkles, laser wipes. Any of these will undo the trust the talk is trying to build.

---

## 3. Slide Layouts

### UI-register layouts

**Title slide (section opener, UI mode):**
- White background, top 1/3 empty.
- H1: 56–72px, gray-900, semibold (600), max 2 lines.
- Eyebrow above: 12px uppercase, tracking 0.3em, gray-500 (e.g. "PART 1 · TOOLS").
- Thin 1px divider below title in primary-600, 64px wide.
- Sub: 20px gray-600 below divider.

**Content slide:**
- Max-width 1024px column, left-aligned.
- H2: 36–44px gray-900, semibold.
- Body: 20–22px gray-700, line-height 1.5, max 65 characters per line.
- Bullets: square 4×4px in primary-600, 16px gap, NEVER round dots.
- Never more than 5 bullets per slide. If more needed, split.

**Code slide:**
- Full-bleed gray-900 (#111827) panel with 48px padding.
- JetBrains Mono 18–22px, white-95 text.
- Language tag top-right: uppercase, 11px, tracking 0.3em, primary-400.
- Line numbers gray-500 if shown.
- Highlight the one line that matters with a primary-600 left border (3px) and subtle primary-600 at 8% background on that line.

**Architecture / flow diagram:**
- White background, gray-900 strokes at 1.5px.
- Nodes: rounded-lg cards with 1px gray-200 border, white fill, 16–20px padding.
- Active path: primary-600 stroke 2px. Inactive: gray-300 at 1px.
- Labels in gray-600, 14px.
- Status badges: success-500 bg + white text for OK, error-500 for BLOCKED, warning-500 for escalation. `rounded-full px-3 py-1 text-xs font-medium uppercase tracking-wider`.

### Oracle-register layouts

**Full-bleed mythic:**
- Pure black background with optional image at 40–60% opacity + `mix-blend-overlay` noise texture.
- Bottom vignette: linear-gradient from rgba(0,0,0,0.85) at bottom to rgba(0,0,0,0.3) at 50%.
- Center-bottom content block, max-width 78vw.
- Eyebrow: 11–13px uppercase, tracking 0.5em, amber-200 at 60%, pulsing slowly.
- Hero line: 36–48px, white-95, italic for emphasis portions only, line-height 1.2.
- One thought per slide. If you have two, make it two slides.

**BLOCKED slide (red-team attack reveal):**
- Black background, NO image.
- Huge word "BLOCKED" in font-black, 14vw, white-95, centered.
- Eyebrow above: "ORACLE REFUSES", red-300 at 70%, tracking 0.4em.
- Sub below: 24px white-90, italic, the distilled reason (e.g. "The vision will not be drawn from that question").

**Pulse/listening state (demo transition slide):**
- Black background.
- Centered: "ASK, AND THE" in 9vw font-black white-95, then line break, then italic amber-100 "vision answers."
- Below, floating pill: black/30 bg with backdrop-blur, 1px amber-200/20 border, rounded-full, 24px horizontal padding.
- Inside pill: green pulsing dot (emerald-400 + animate-ping) + label "LIVE · ORACLE LISTENING".

---

## 4. Composition Rules

1. **One idea per slide.** If a slide needs two beats, make it two slides.
2. **No gradients on text ever.** Color comes from opacity layers over solid backgrounds.
3. **No drop shadows on UI-register cards** beyond `shadow-sm`. No shadows at all on Oracle-register.
4. **Keep alignment baselines strict.** All text on a slide shares at least one vertical edge. Grid of 12 columns, 64px gutters.
5. **Whitespace is content.** Oracle-register slides must have at least 60% negative space. UI-register at least 40%.
6. **Never stretch images.** Crop with `object-cover`, 16:9 or full-bleed.
7. **Brand the deck like the product brands itself** — understated. The institution name sits in 14px gray-500 at bottom-left of every UI slide. No logo lockups in corners. No page numbers over 11px.

---

## 5. Section Register Mapping (for this specific talk)

| Section | Register | Why |
|---|---|---|
| Cold open / hook | Oracle | Pattern break — audience thinks it's art, not a talk |
| Agenda / who I am | UI | Trust, credibility, institutional tone |
| Tool demos (Copilot, Spec Kit, Azure) | UI | These are real products — show them clean |
| Live Oracle demo cutover | Oracle | Projector takes over, slide gets out of the way |
| Guardrails / evals / red team | UI until the reveal slide, then one Oracle BLOCKED slide | Technical explainer, then gut punch |
| Ethics prompt / provocation | Oracle | Should feel like the Oracle speaking, not the speaker |
| Takeaways | UI | Legible, shareable, screenshotable |
| Q&A | UI | Conversational tone |
| Closing | Oracle | Land the emotion |

---

## 6. Copy Voice

- **UI-register copy:** clear, second person, short sentences. No exclamation points. Examples: *"Try it yourself.", "This is the pipeline.", "Here's where it fails."*
- **Oracle-register copy:** second person, poetic, present tense, incomplete sentences allowed. Examples: *"The vision will not be drawn.", "Ask, and the Oracle chooses.", "From a vocabulary of dreams."*
- Never let Oracle voice bleed into UI slides or vice versa. If you find yourself writing *"✨ Let's explore ethics! ✨"* you've lost both registers.

---

## 7. Anti-patterns (do NOT do any of these)

- ❌ Stock photos of handshakes, brains, or circuit boards
- ❌ Clip art, emoji-as-icon, "AI glow" stylings
- ❌ Rainbow or neon gradient backgrounds
- ❌ Serif fonts (this product has none)
- ❌ Centered body paragraphs on UI slides (left-align only)
- ❌ Animations that draw attention to themselves
- ❌ More than three colors on a single slide (neutral + primary + one accent max)
- ❌ Oracle-register slides without adequate contrast (WCAG AA minimum even on stage)

---

## 8. Deliverable checklist for Manus

When producing the deck, confirm each slide passes:

- [ ] Register declared (UI or Oracle) — no mixing within a slide
- [ ] Typography scale matches tokens in §2
- [ ] Colors drawn only from §2 palette
- [ ] One idea per slide
- [ ] At least 40% (UI) or 60% (Oracle) negative space
- [ ] No anti-patterns from §7
- [ ] Transition matches register (150–300ms UI, 1400–1800ms Oracle)
- [ ] Reads in 6 seconds if it's UI, 3 seconds if it's Oracle

---

## 9. Reference files in this repo (authoritative sources)

- `frontend/tailwind.config.js` — canonical color tokens
- `frontend/src/index.css` — CSS variables, focus styles, scrollbar
- `frontend/src/components/Header.tsx` — UI-register header pattern
- `frontend/src/components/OraclePage.tsx` — Oracle-register stage composition
- `frontend/src/components/MessageBubble.tsx` — card + bubble rhythm
- `frontend/src/components/TicketCard.tsx` — status badge pattern

If in doubt, screenshot the live app and match it.

---

**Confidence history:**
- low → medium: Captured from live product source; not yet validated against a final deck build.
- Bump to high after Manus produces a deck and the NYU talk is delivered without visual-whiplash notes.
