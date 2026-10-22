---
version: alpha
name: "Living Explainers"
description: "A source-trace explorer shaped like an engineer’s field notebook."
colors:
  ink: "#142826"
  muted: "#58716C"
  paper: "#F2F5EF"
  surface: "#FFFFFF"
  line: "#CFDBD3"
  trace: "#096B62"
  review: "#B68124"
  warning: "#BB4B34"
  focus: "#9E3FCE"
  scroll-track: "#E5ECE5"
  scroll-thumb: "#7C9990"
  scroll-hover: "#506963"
typography:
  display:
    fontFamily: '"Iowan Old Style", Baskerville, Georgia, serif'
  sans:
    fontFamily: 'Inter, "Avenir Next", Avenir, system-ui, sans-serif'
  utility:
    fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace"
rounded:
  DEFAULT: "3px"
  sm: "3px"
spacing:
  page-max: "1220px"
  section-gap: "34px"
components:
  native-select: { }
  trace-step: { }
  evidence-card: { }
---

# Living Explainers Design System

## Overview

### Creative North Star

Treat each generated page as a working field notebook: authored sequence on the left, evidence card beside it, status marks that resemble review annotations. The subject is an engineer tracing a single request, not a general architecture map. Product register: calm, precise, and inspectable. The one expressive move is the large literary title above the ordered trace; source metadata stays compact and monospaced.

The page must never resemble a generic flowchart canvas or a hosted documentation portal. The repository is the source of truth; the exported page is a self-contained snapshot. Locale is English in v0.1, with system fallbacks for other scripts. No Japan-market domain is claimed.

### Token ownership and runtime mapping

`living_explainers/explorer.css` is the canonical runtime token source. Its `:root` variables below style the UI and are embedded verbatim by `core.render_html`; generated HTML adds no second theme layer. Keep these values synchronized in the same change when a visual token changes. There is no independent design-token build or external stylesheet.

## Colors

`--ink #142826`, `--muted #58716c`, `--paper #f2f5ef`, and `--surface #fff` establish a subdued technical page. `--teal #096b62` marks trace structure; `--gold #b68124` marks review; `--coral #bb4b34` marks uncovered behavior; `--focus #9e3fce` is the visible keyboard ring. Color never carries freshness alone: each status is named in text.

## Typography

The display face is `"Iowan Old Style", Baskerville, Georgia, serif`; it gives the system a notebook voice in titles and step names. Body copy uses `Inter, "Avenir Next", Avenir, system-ui, sans-serif`. Paths, identifiers, and review metadata use `ui-monospace, SFMono-Regular, Consolas, monospace`. System fallbacks keep the page usable without network fonts.

## Layout

The page is capped at `1220px`, with the title and build-time freshness summary at the top, labeled native selects next, then a two-column sequence and evidence card. At `760px`, controls wrap and the evidence card returns to normal document flow. Steps remain an ordered list at every width. The card is sticky only on wide screens and does not cover keyboard focus.

## Elevation & Depth

Dividers and one quiet evidence-card shadow carry hierarchy. The freshness panel uses a left status rule. No gradients, decorative graphs, or motion compete with the trace.

## Shapes

The interface uses nearly square 3px edges, hairline dividers, and no pill controls. This keeps the page close to a working record rather than a consumer dashboard.

## Components

Native `select`, `checkbox`, `button`, `ol`, and `li` are the canonical controls. Every select has a visible label; step buttons expose selected state through `aria-current` and retain native keyboard activation. `:focus-visible` uses the purple focus token. The detail panel names source path, inclusive line range, review state, assumptions, and origin. The page has a no-JavaScript message and a static build-time freshness count. The generated page makes no network requests and inserts model text only through `textContent`.

## Do's and Don'ts

- Do keep authored sequence and evidence in view together.
- Do spell out proposed, stale, missing, and current states.
- Don't imply a source path opens on every reader's machine.
- Don't invent steps for an uncovered question or claim source review proves the explanation.
