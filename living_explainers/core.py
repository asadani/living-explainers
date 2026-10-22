"""Validation, freshness, and rendering for authored explanation models."""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

HEX = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
ORIGINS = {"observed", "stated", "proposed"}


class ModelError(ValueError):
    """An actionable model or source reference error."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ModelError(message)


def _object(value: Any, where: str) -> dict:
    _need(isinstance(value, dict), f"{where} must be an object")
    return value


def _text(value: Any, where: str, *, empty: bool = False) -> None:
    _need(isinstance(value, str) and (empty or bool(value.strip())), f"{where} must be a non-empty string")


def validate_model(model: dict) -> None:
    model = _object(model, "model")
    _need(isinstance(model.get("schema_version"), int) and not isinstance(model.get("schema_version"), bool) and model["schema_version"] == 1, "schema_version must be integer 1")
    for key in ("id", "title", "scope"):
        _text(model.get(key), key)
    for collection in ("sources", "nodes", "paths", "questions"):
        _need(isinstance(model.get(collection), list), f"{collection} must be an array")
    _need(bool(model["paths"]), "paths must contain at least one authored path")
    sources: dict[str, dict] = {}
    nodes: dict[str, dict] = {}
    paths: dict[str, dict] = {}
    for name, collection, dest in (("source", model["sources"], sources), ("node", model["nodes"], nodes), ("path", model["paths"], paths)):
        for i, raw in enumerate(collection):
            item = _object(raw, f"{name}[{i}]")
            ident = item.get("id")
            _need(isinstance(ident, str) and ID.fullmatch(ident), f"{name}[{i}].id must be a simple identifier")
            _need(ident not in dest, f"duplicate {name} id: {ident}")
            dest[ident] = item
    for ident, ref in sources.items():
        _text(ref.get("path"), f"source {ident}.path")
        for key in ("line_start", "line_end"):
            val = ref.get(key)
            _need(isinstance(val, int) and not isinstance(val, bool) and val > 0, f"source {ident}.{key} must be a positive integer")
        _need(ref["line_end"] >= ref["line_start"], f"source {ident} line_end must be >= line_start")
        status = ref.get("review_status")
        _need(isinstance(status, str) and status in {"proposed", "confirmed"}, f"source {ident}.review_status must be proposed or confirmed")
        _source_relative(ref["path"], f"source {ident}.path")
        if status == "confirmed":
            _need(isinstance(ref.get("sha256"), str) and HEX.fullmatch(ref["sha256"]), f"source {ident} confirmed source requires a 64-character sha256")
            _text(ref.get("reviewer"), f"source {ident}.reviewer")
            _valid_time(ref.get("reviewed_at"), f"source {ident}.reviewed_at")
        else:
            _need(ref.get("sha256") is None, f"source {ident} proposed source must have sha256 null")
    for ident, node in nodes.items():
        _text(node.get("label"), f"node {ident}.label")
        _text(node.get("summary"), f"node {ident}.summary")
        _need(isinstance(node.get("origin"), str) and node.get("origin") in ORIGINS, f"node {ident}.origin must be observed, stated, or proposed")
        refs = node.get("source_ids")
        _need(isinstance(refs, list) and all(isinstance(x, str) for x in refs), f"node {ident}.source_ids must be an array of source ids")
        _need(len(set(refs)) == len(refs), f"node {ident}.source_ids contains duplicates")
        _need(all(x in sources for x in refs), f"node {ident} refers to an unknown source")
        if node["origin"] in {"observed", "stated"}:
            _need(bool(refs), f"node {ident} with origin {node['origin']} requires a source")
        if "assumptions" in node:
            _need(isinstance(node["assumptions"], list) and all(isinstance(x, str) and x.strip() for x in node["assumptions"]), f"node {ident}.assumptions must contain non-empty strings")
    for ident, path in paths.items():
        for key in ("label", "trigger", "outcome"):
            _text(path.get(key), f"path {ident}.{key}")
        _need(isinstance(path.get("origin"), str) and path.get("origin") in ORIGINS, f"path {ident}.origin must be observed, stated, or proposed")
        steps = path.get("steps")
        _need(isinstance(steps, list) and bool(steps), f"path {ident}.steps must be a non-empty array")
        for i, step in enumerate(steps):
            step = _object(step, f"path {ident}.steps[{i}]")
            _need(isinstance(step.get("node_id"), str) and step.get("node_id") in nodes, f"path {ident} step {i} refers to an unknown node")
            _text(step.get("explanation"), f"path {ident} step {i}.explanation")
    qids: set[str] = set()
    for i, raw in enumerate(model["questions"]):
        q = _object(raw, f"question[{i}]")
        ident = q.get("id")
        _need(isinstance(ident, str) and ID.fullmatch(ident), f"question[{i}].id must be a simple identifier")
        _need(ident not in qids, f"duplicate question id: {ident}")
        qids.add(ident)
        _text(q.get("label"), f"question {ident}.label")
        _need(q.get("path_id") is None or (isinstance(q.get("path_id"), str) and q.get("path_id") in paths), f"question {ident} refers to an unknown path")
        _text(q.get("note"), f"question {ident}.note")


def _valid_time(value: Any, where: str) -> None:
    _need(isinstance(value, str), f"{where} must be an ISO 8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ModelError(f"{where} must be an ISO 8601 timestamp") from exc
    _need(parsed.tzinfo is not None, f"{where} must include a timezone")
    _need(parsed.utcoffset() == timezone.utc.utcoffset(parsed), f"{where} must be expressed in UTC")


def _source_path(root: Path, relative: str) -> Path:
    base = root.resolve()
    target = (base / _source_relative(relative, "source path")).resolve()
    _need(target == base or base in target.parents, f"source path escapes --root: {relative}")
    return target


def _source_relative(value: str, where: str) -> str:
    windows = PureWindowsPath(value)
    portable = value.replace("\\", "/")
    parts = PurePosixPath(portable).parts
    _need(not windows.drive and not windows.is_absolute() and not portable.startswith("/") and ".." not in parts, f"{where} must stay relative to --root")
    return portable


def source_statuses(model: dict, root: Path) -> list[dict]:
    validate_model(model)
    statuses = []
    for ref in model["sources"]:
        result = {"id": ref["id"], "path": ref["path"], "line_start": ref["line_start"], "line_end": ref["line_end"]}
        target = _source_path(root, ref["path"])
        try:
            raw = target.read_bytes()
            text = raw.decode("utf-8")
            valid = ref["line_end"] <= len(text.splitlines())
            if ref["review_status"] != "confirmed":
                status = "unreviewed"
            elif not valid or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
                status = "stale"
            else:
                status = "current"
            result.update(status=status, range_valid=valid)
        except (OSError, UnicodeError):
            result.update(status="missing", range_valid=None)
        statuses.append(result)
    return statuses


def explore_path(model: dict, path_id: str) -> dict:
    validate_model(model)
    for path in model["paths"]:
        if path["id"] == path_id:
            nodes = {x["id"]: x for x in model["nodes"]}
            return {"path": path, "steps": [{**step, "node": nodes[step["node_id"]]} for step in path["steps"]]}
    raise ModelError(f"unknown path id: {path_id}")


def review_source(model: dict, root: Path, ref_id: str, reviewer: str, reviewed_at: str) -> dict:
    validate_model(model)
    _text(reviewer, "reviewer")
    _valid_time(reviewed_at, "reviewed_at")
    revised = json.loads(json.dumps(model))
    ref = next((x for x in revised["sources"] if x["id"] == ref_id), None)
    _need(ref is not None, f"unknown source id: {ref_id}")
    try:
        target = _source_path(root, ref["path"])
        raw = target.read_bytes()
        lines = raw.decode("utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ModelError(f"cannot read source {ref['path']}: {exc}") from exc
    _need(ref["line_end"] <= len(lines), f"source {ref_id} range ends at line {ref['line_end']}, file has {len(lines)} lines")
    ref.update(sha256=hashlib.sha256(raw).hexdigest(), review_status="confirmed", reviewer=reviewer.strip(), reviewed_at=reviewed_at)
    return revised


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_html(model: dict, statuses: list[dict]) -> str:
    validate_model(model)
    problematic = sum(s["status"] != "current" for s in statuses)
    title = html.escape(model["title"])
    css = (Path(__file__).parent / "explorer.css").read_text(encoding="utf-8")
    js = (Path(__file__).parent / "explorer.js").read_text(encoding="utf-8")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Living Explainers</title><style>{css}</style></head>
<body><main class="shell"><header class="masthead"><a class="brand" href="#top" aria-label="Living Explainers home">LE <span>FIELD NOTES</span></a><p>Authored request trace · snapshot at build time</p></header>
<section class="intro" id="top"><div><p class="eyebrow">REQUEST PATH / REVIEWED MODEL</p><h1>{title}</h1><p class="scope">{html.escape(model['scope'])}</p></div><aside class="freshness" aria-live="polite"><span class="freshness-label">SOURCE REVIEW</span><strong id="freshness-count">{problematic} needing review</strong><span>Checked when this page was built</span></aside></section>
<section class="controls" aria-label="Trace controls"><label>Request path<select id="path-select"></select></label><label>Question<select id="question-select"></select></label><label class="check"><input type="checkbox" id="focus-review"><span>Emphasize assumptions and proposed steps</span></label></section>
<section class="workspace"><div><div class="section-head"><p class="eyebrow">AUTHORED SEQUENCE</p><p id="path-meta"></p></div><ol id="steps" class="steps"></ol><div id="not-covered" class="not-covered" hidden></div></div><aside class="detail" aria-labelledby="detail-title"><p class="eyebrow">STEP NOTES</p><h2 id="detail-title">Choose a step</h2><div id="detail-body">Select any point in the path to inspect its explanation and evidence.</div></aside></section>
<footer><p><strong>Scope:</strong> {html.escape(model['scope'])}</p><p>Source paths are references on your machine. This file does not read them. A changed source needs an explicit reviewer update.</p></footer>
<noscript><p class="noscript">Enable JavaScript to select paths and inspect authored steps. The scope and build-time review count remain available above.</p></noscript></main>
<script type="application/json" id="model-data">{_safe_json({"model": model, "freshness": {"sources": statuses}})}</script><script>{js}</script></body></html>'''
