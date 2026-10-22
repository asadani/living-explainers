# Living Explainers UI Contract

## Product context

- Audience: engineers and reviewers maintaining a small authored request trace.
- Primary job: follow one selected path and inspect its sources and review state.
- Market and locale: general technical audience; English copy, system font fallback.
- Runtime: one local HTML file generated from an explicit JSON model.
- Business authority: `docs/PLAN.md` and `PRODUCT.md`; synthetic fixtures are examples, not production authorization policy.
- Visual tokens and rationale: [`DESIGN.md`](DESIGN.md).

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
| --- | --- | --- | --- | --- |
| Select/Listbox | Native labeled select in explorer renderer | PRODUCT.md and DESIGN.md | Path and question selectors; OS-owned popup | Unit/CLI export checks; browser coverage pending |
| Scrollbar | Global explorer.css baseline | DESIGN.md | Document scrolling with forced-colors fallback | Static audit and stylesheet review; browser coverage pending |

## Canonical controls and behavior

| Capability | Canonical owner | Behavior |
|---|---|---|
| Path and question selection | Native labeled `select` in generated HTML | Changing path clears question selection. A linked question selects its authored path. An unlinked question shows its note and no steps. |
| Step selection | Native `button` in ordered list | Keyboard and pointer selection update `aria-current`, then populate the evidence card. |
| Review filter | Native labeled `checkbox` | Keeps the entire path order visible and de-emphasizes steps without assumptions or proposed origin. It never edits model data. |
| Freshness | Build-time source status | Page displays statuses from generation time; it cannot read or refresh local source files. |
| Source evidence | Text-only evidence card | Displays relative path, inclusive line range, origin, assumptions, and current/stale/missing/unreviewed state. |
| Scrollbar | Global generated stylesheet | Visible page scrollbar uses the CSS standard properties plus WebKit styling, with forced-colors reset. |

No dialogs, toasts, network services, or persistent browser edits are used. If JavaScript is disabled, scope, snapshot freshness count, and limitations remain in static HTML.

## Verification

- Unit and CLI coverage: `python -m unittest discover -s tests -v`.
- Generated content is tested for JSON/script escaping and absence of untrusted HTML insertion.
- `node --check living_explainers/explorer.js` checks JavaScript syntax.
- Browser operation is not verified in this environment; README records this limitation.
