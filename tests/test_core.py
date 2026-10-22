import copy
import json
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from living_explainers.core import ModelError, explore_path, render_html, review_source, source_statuses, validate_model


class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.ids.update(value for name, value in attrs if name == "id")


class LivingCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads((ROOT / "fixtures/model.json").read_text())
        cls.sources = ROOT / "fixtures/system"

    def test_authored_paths_keep_exact_step_order(self):
        self.assertEqual([x["node_id"] for x in explore_path(self.model, "allowed")["steps"]], ["request", "authorize", "render"])
        self.assertEqual([x["node_id"] for x in explore_path(self.model, "renderer-timeout")["steps"]], ["request", "authorize", "render", "timeout"])

    def test_current_stale_missing_and_unreviewed_are_distinct(self):
        self.assertEqual({x["status"] for x in source_statuses(self.model, self.sources)}, {"current"})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "handler.py").write_text("changed source\n")
            (root / "authorization.py").write_text((self.sources / "authorization.py").read_text())
            (root / "renderer.py").write_text((self.sources / "renderer.py").read_text())
            stale = source_statuses(self.model, root)
            self.assertEqual({x["id"]: x["status"] for x in stale}["request-handler"], "stale")
            missing_model = copy.deepcopy(self.model)
            missing_model["sources"][0]["path"] = "missing.py"
            self.assertEqual(source_statuses(missing_model, root)[0]["status"], "missing")
            proposed = copy.deepcopy(self.model)
            proposed["sources"][0].update(review_status="proposed", sha256=None)
            self.assertEqual(source_statuses(proposed, root)[0]["status"], "unreviewed")

    def test_review_updates_one_reference_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "handler.py").write_text("def changed():\n    first = True\n    second = True\n    third = True\n    return first\n")
            reviewed = review_source(self.model, root, "request-handler", "Reviewer", "2026-10-22T09:00:00Z")
            self.assertEqual(reviewed["sources"][0]["reviewer"], "Reviewer")
            self.assertEqual(self.model["sources"][0]["reviewer"], "Example maintainer")
            self.assertEqual(reviewed["sources"][1], self.model["sources"][1])
            with self.assertRaisesRegex(ModelError, "range ends"):
                bad = copy.deepcopy(self.model)
                bad["sources"][0]["line_end"] = 90
                review_source(bad, self.sources, "request-handler", "Reviewer", "2026-10-22T09:00:00Z")

    def test_validation_rejects_duplicate_broken_and_escaping_refs(self):
        for mutate, message in (
            (lambda m: m["nodes"].append(copy.deepcopy(m["nodes"][0])), "duplicate node id"),
            (lambda m: m["paths"][0]["steps"][0].update(node_id="absent"), "unknown node"),
            (lambda m: m["paths"][0].update(steps=[]), "non-empty array"),
            (lambda m: m["sources"][0].update(line_start=True), "positive integer"),
            (lambda m: m["sources"][0].update(path="../outside.py"), "stay relative"),
            (lambda m: m.update(schema_version=1.0), "integer 1"),
        ):
            model = copy.deepcopy(self.model)
            mutate(model)
            with self.subTest(message=message), self.assertRaisesRegex(ModelError, message):
                validate_model(model)

    def test_html_escapes_script_termination_and_uses_text_only_rendering(self):
        model = copy.deepcopy(self.model)
        model["title"] = "Trace </script><script>bad()</script>"
        model["nodes"][0]["summary"] = "Read </script><img src=x onerror=bad()>"
        output = render_html(model, source_statuses(model, self.sources))
        structure = Structure()
        structure.feed(output)
        self.assertTrue({"main", "select", "ol", "noscript"}.issubset(structure.tags))
        self.assertTrue({"path-select", "question-select", "steps", "detail-body"}.issubset(structure.ids))
        self.assertNotIn("</script><script>bad()", output)
        self.assertIn("\\u003c/script\\u003e", output)
        self.assertIn("textContent", output)
        self.assertIn("createElement('button')", output)
        self.assertNotIn("innerHTML", output)
        self.assertNotIn("fetch(", output)
        self.assertIn('id="path-select"', output)
        self.assertIn("not-covered", output)

    def test_cli_validate_check_build_and_review(self):
        def run(*args):
            return subprocess.run([sys.executable, "-m", "living_explainers", *args], cwd=ROOT, text=True, capture_output=True)
        model = "fixtures/model.json"
        self.assertEqual(run("validate", model, "--root", "fixtures/system").returncode, 0)
        with tempfile.TemporaryDirectory() as temp:
            check = run("check", model, "--root", "fixtures/system", "--out", f"{temp}/freshness.json")
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertEqual(run("build", model, "--root", "fixtures/system", "--out", f"{temp}/explorer.html").returncode, 0)
            reviewed = run("review-source", model, "--root", "fixtures/system", "--ref", "access-check", "--reviewer", "Demo", "--reviewed-at", "2026-10-22T09:00:00Z", "--out", f"{temp}/reviewed.json")
            self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
            self.assertTrue((Path(temp) / "explorer.html").is_file())
        invalid = run("validate", model, "--root", "does-not-exist")
        self.assertEqual(invalid.returncode, 2)
        self.assertNotIn("Traceback", invalid.stderr)
        subprocess.run(["node", "--check", str(ROOT / "living_explainers/explorer.js")], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
