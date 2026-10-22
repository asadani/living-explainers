from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .core import ModelError, explore_path, render_html, review_source, source_statuses, validate_model


def _read(path: str) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ModelError(f"cannot read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ModelError(f"{path} must contain a JSON object")
    return value


def _write(path: str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _guard_output(path: str, model_path: str, model: dict, root: Path, *, allow_model: bool = False) -> None:
    output = Path(path).resolve()
    model_input = Path(model_path).resolve()
    if output == model_input and not allow_model:
        raise ModelError(f"refusing to overwrite input model {model_path}; choose a different --out path")
    for ref in model["sources"]:
        source = (root / ref["path"]).resolve()
        if output == source:
            raise ModelError(f"refusing to overwrite referenced source {ref['path']}; choose a different --out path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m living_explainers", description="Validate and explore authored request explanations.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "check", "build", "review-source"):
        sub = commands.add_parser(name)
        sub.add_argument("model")
        sub.add_argument("--root", default=".", help="source root (default: current directory)")
        if name == "check":
            sub.add_argument("--out", required=True)
        elif name == "build":
            sub.add_argument("--out", required=True)
        elif name == "review-source":
            sub.add_argument("--ref", required=True)
            sub.add_argument("--reviewer", required=True)
            sub.add_argument("--reviewed-at", help="timezone-aware ISO timestamp (default: current UTC time)")
            sub.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        model = _read(args.model)
        validate_model(model)
        root = Path(args.root)
        if args.command == "validate":
            statuses = source_statuses(model, root)
            bad = [x for x in statuses if x["status"] == "missing" or x.get("range_valid") is False]
            if bad:
                raise ModelError("source files or ranges are invalid: " + ", ".join(x["id"] for x in bad))
            print(f"Valid model: {model['id']} ({len(model['nodes'])} nodes, {len(model['paths'])} paths)")
            return 0
        if args.command == "check":
            _guard_output(args.out, args.model, model, root)
            statuses = source_statuses(model, root)
            _write(args.out, _json({"schema_version": 1, "model_id": model["id"], "sources": statuses, "steps": _step_statuses(model, statuses)}))
            return 1 if any(x["status"] != "current" for x in statuses) else 0
        if args.command == "build":
            _guard_output(args.out, args.model, model, root)
            statuses = source_statuses(model, root)
            _write(args.out, render_html(model, statuses))
            print(f"Built offline explorer: {args.out}")
            return 0
        if args.command == "review-source":
            _guard_output(args.out, args.model, model, root, allow_model=True)
            timestamp = args.reviewed_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            revised = review_source(model, root, args.ref, args.reviewer, timestamp)
            _write(args.out, _json(revised))
            print(f"Reviewed source {args.ref}: {args.out}")
            return 0
    except ModelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError) as exc:
        print(f"error: cannot write requested output: {exc}", file=sys.stderr)
        return 2
    return 2


def _step_statuses(model: dict, sources: list[dict]) -> list[dict]:
    by_id = {x["id"]: x for x in sources}
    node_by_id = {x["id"]: x for x in model["nodes"]}
    rows = []
    for path in model["paths"]:
        for step in path["steps"]:
            node = node_by_id[step["node_id"]]
            problematic = [sid for sid in node["source_ids"] if by_id[sid]["status"] != "current"]
            rows.append({"path_id": path["id"], "node_id": node["id"], "origin": node["origin"], "status": "review" if problematic or node["origin"] == "proposed" else "current", "source_ids": problematic})
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
