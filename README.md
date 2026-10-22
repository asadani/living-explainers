![Living Explainers](assets/logo.svg)

Living Explainers turns an explicitly authored JSON request trace into a self-contained offline explorer. It keeps the selected path, source line references, assumptions, and build-time freshness status together. The example follows a document preview through request validation, access review, and rendering.

## Requirements

Python 3.11 or newer runs the CLI without third-party Python dependencies. JavaScript checks in the development test suite also require Node.js; local verification used Node.js 26.12.0. Opening the generated HTML needs a JavaScript-capable browser.

## Quickstart

Run these commands from this repository directory with Python 3.11 or newer:

```sh
python -m living_explainers --help
python -m living_explainers validate fixtures/model.json --root fixtures/system
```

Expected result: help exits `0`; validation prints `Valid model: document-preview (5 nodes, 3 paths)` and exits `0`.

Check source baselines and build the page:

```sh
python -m living_explainers check fixtures/model.json --root fixtures/system --out /tmp/living-freshness.json
python -m living_explainers build fixtures/model.json --root fixtures/system --out /tmp/living-explorer.html
```

Expected result: the fixture is current, so `check` exits `0`; `build` exits `0` and writes a single HTML file. Open that file locally to select the three authored paths, inspect evidence, filter assumptions/proposed steps, or choose the uncovered caller-retry question. No source file is fetched by the page.

To record a source review after checking the referenced lines:

```sh
python -m living_explainers review-source fixtures/model.json --root fixtures/system --ref access-check --reviewer "Demo reviewer" --reviewed-at 2026-10-22T09:00:00Z --out /tmp/living-reviewed.json
```

Expected result: the new file contains an updated hash and reviewer only for `access-check`; exit `0`. The original model is unchanged. An invalid model, missing source during `validate`, invalid range, or root escape exits `2` with an error on stderr. `check` exits `1` when a source is stale, missing, or unreviewed. `build` still succeeds for structurally valid models with missing or stale sources and shows those states in the page.

Run the tests:

```sh
python -m unittest discover -s tests -v
```

Expected result: all tests pass with exit `0`. The tests cover path order, current/stale/missing/unreviewed references, source review, invalid references, CLI statuses, HTML escaping, and JavaScript syntax.

## Reading freshness

The check report records each source as `current`, `stale`, `missing`, or `unreviewed`, plus steps affected by those references. Hashes cover the entire source file, so even an unrelated edit can require review. A changed line range is marked stale; a missing/unreadable source is marked missing. Running `build` alone never updates a stored baseline.

## Limits

This tool validates and renders authored claims; it does not infer architecture, execute the described system, establish runtime behavior, or decide production authorization. The bundled sharing and preview examples are synthetic. A source hash only signals that a reviewer should look again; it does not prove that an explanation is accurate. HTML freshness is a build-time snapshot. Browser interaction was not verified in this environment.

## Data integrity

Validation checks source existence and cited ranges even for proposed references. Exported pages can still show missing or unreviewed sources. Report/build output paths cannot replace the model or referenced sources; `review-source` is the explicit operation that can atomically update a model.

See [verification coverage](docs/VERIFICATION.md) and [the design plan](docs/PLAN.md) for tested behavior and remaining limits.
