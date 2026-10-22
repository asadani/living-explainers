# Living Explainers v0.1 implementation plan

## User job and bounded scope

Maintain a reviewed explanation of one request flow and export a working offline explorer. The model is explicitly authored JSON. The tool validates and renders it; no source-code inference or generated prose is required.

## CLI

```sh
python -m living_explainers validate fixtures/model.json --root fixtures/system
python -m living_explainers check fixtures/model.json --root fixtures/system --out freshness.json
python -m living_explainers build fixtures/model.json --root fixtures/system --out explorer.html
python -m living_explainers review-source fixtures/model.json --root fixtures/system --ref auth-source --reviewer "Demo reviewer" --out reviewed.json
```

`validate` checks structural integrity and source ranges; missing/unreadable source is an error (2). `check` writes all reference and affected-step statuses, returning 1 for stale, missing, or unreviewed references. `build` must still succeed with stale/missing sources and mark them in the page; structurally invalid models fail (2). `review-source` explicitly snapshots one readable source, checks its line range, records reviewer/time, sets the ref confirmed, and writes the requested output (atomic when overwriting). It does not confirm unrelated refs or rewrite explanations.

## JSON model

```json
{
  "schema_version": 1,
  "id": "document-preview",
  "title": "Document preview request",
  "scope": "A single preview request; background jobs are excluded.",
  "sources": [{"id":"auth-source","path":"authorization.py","line_start":1,"line_end":12,"sha256":"<64 hex characters>","review_status":"confirmed","reviewer":"Example maintainer","reviewed_at":"2026-10-22T00:00:00Z"}],
  "nodes": [{"id":"authorize","label":"Authorize access","summary":"Check whether this user can view the document.","origin":"observed","source_ids":["auth-source"]}],
  "paths": [{"id":"success","label":"Access allowed","trigger":"A member opens a document.","steps":[{"node_id":"authorize","explanation":"The membership check allows the request."}],"outcome":"Preview returned","origin":"stated"}],
  "questions": [{"id":"renderer-offline","label":"What if the renderer is offline?","path_id":null,"note":"Not covered. Confirm retry behavior with the renderer owner."}]
}
```

The real fixture includes at least three nodes and three paths (success, denied access, renderer timeout), and questions linking to those paths plus one unsupported question. A node may add `rationale` and `assumptions:[string]`. Source refs use `review_status: proposed|confirmed`; proposed refs can have `sha256:null`, reviewer/time null. Confirmed refs require a 64-hex baseline, nonempty reviewer, and valid timestamp. Nodes have `origin: observed|stated|proposed`; observed/stated nodes require at least one source ID. Proposed nodes may lack sources and must display “proposed.” No empty paths or broken node/source/path references; unique IDs within each collection. Repeated nodes in a path are allowed, representing explicitly authored repeated steps rather than graph traversal.

## Core API and freshness

- `validate_model(model: dict) -> None`
- `source_statuses(model: dict, root: Path) -> list[dict]`
- `explore_path(model: dict, path_id: str) -> dict`
- `review_source(model: dict, root: Path, ref_id: str, reviewer: str, reviewed_at: str) -> dict`
- `render_html(model: dict, statuses: list[dict]) -> str`

Source status is `current`, `stale`, `missing`, or `unreviewed`; confirmed hash equality is current, mismatch stale, unreadable or absent files missing, proposed/no baseline unreviewed. Report invalid ranges separately where current files no longer contain the cited lines. Derived step status lists all problematic source IDs and never hides a proposed origin. Sources are hashed as whole files; a line-number shift or unrelated change can therefore require review. `review_source` returns a new model and does not mutate its input.

## Required HTML behavior

A single output file embeds all CSS, model JSON, freshness data, and JavaScript. Show title, scope, prominent freshness summary, path selector, ordered sequence, selected step details with source path/range/baseline/current status, origin labels, and assumptions. Provide a question selector: a linked question selects its path; null path displays the supplied not-covered note and must not invent a trace. Provide a filter to highlight steps with assumptions or proposed origin without destroying path order. A beginner can read the ordered explanation; an experienced user can jump to any step's evidence.

Use real buttons/selects with associated labels, visible keyboard focus, readable contrast, and a useful narrow layout. Source paths are text references, not localhost file links assumed to work on every machine. Never fetch sources or external assets from the generated page. Embed JSON safely (`<` escaped), and use `textContent` for user text in JS. Render no untrusted HTML. Include a no-JavaScript message and a static scope/freshness summary. Generated HTML is a snapshot: it only reflects freshness at build time and says so.

## Acceptance tests and fixtures

1. Fixture source files plus model yield current refs; `explore_path` returns exact authored step order and outcome for each of three paths.
2. Source modification yields stale status on the right reference and affected step; build still works and includes the warning. A fresh build alone does not update the baseline.
3. Explicit review updates only one ref's hash/reviewer/time; check becomes current for that ref. Missing source or invalid range refuses review.
4. Unknown question coverage displays the authored not-covered note, with no fabricated steps. Proposed nodes and assumptions stay visible.
5. Duplicate node IDs, broken paths, empty steps, invalid source ranges, and path escapes fail clearly. Missing files in check/build are visible rather than crashes.
6. A title or explanation containing `</script><script>…` cannot break embedded JSON or inject HTML. Test the escaping helper and confirm no raw terminator from model content appears.
7. CLI smoke tests cover validate/check/build/review. Inspect the generated HTML in a browser when available: change path, select a step, choose unsupported question, filter assumptions, and use the controls with a keyboard. If unavailable, disclose that UI verification limit and verify exported structure/embedded data in tests.

## Non-goals and milestone

No graph inference, runtime simulation, LLM, automatic corrections, persistent in-browser annotations, hosted website, diagram library, or complete architecture documentation. The v0.1 sequence is the interaction, so a complex graph layout adds no necessary value.

Implement model validation/freshness, then pure path selection/review, then the offline explorer and fixtures. Done means readers can explore three real authored paths, inspect cited evidence, and see a source edit produce a visible review requirement.
