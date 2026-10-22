import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from living_explainers.core import ModelError, source_statuses, validate_model

ROOT=Path(__file__).resolve().parents[1]
class ReviewEdges(unittest.TestCase):
    def test_empty_path_collection_rejected_before_html_build(self):
        model=json.loads((ROOT/'fixtures/model.json').read_text())
        model['paths']=[]
        model['questions']=[]
        with self.assertRaises(ModelError): validate_model(model)

    def test_symlink_escape_is_invalid_not_a_missing_source(self):
        model=json.loads((ROOT/'fixtures/model.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder); root=base/'root'; root.mkdir()
            outside=base/'outside.txt'; outside.write_text('outside source')
            (root/model['sources'][0]['path']).symlink_to(outside)
            with self.assertRaises(ModelError): source_statuses(model,root)

    def test_proposed_sources_are_checked_for_presence_and_range(self):
        model=json.loads((ROOT/'fixtures/model.json').read_text())
        model['sources'][0].update(review_status='proposed',sha256=None)
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder); root=base/'src'; root.mkdir()
            (root/'handler.py').write_text('one\ntwo\n')
            model['sources'][0].update(path='handler.py',line_start=1,line_end=3)
            statuses=source_statuses(model,root)
            self.assertEqual((statuses[0]['status'],statuses[0]['range_valid']),('unreviewed',False))
            model_file=base/'model.json'; model_file.write_text(json.dumps(model))
            run=subprocess.run([sys.executable,'-m','living_explainers','validate',str(model_file),'--root',str(root)],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,2); self.assertNotIn('Traceback',run.stderr)
            built=base/'trace.html'
            result=subprocess.run([sys.executable,'-m','living_explainers','build',str(model_file),'--root',str(root),'--out',str(built)],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('needing review',built.read_text())
            model['sources'][0]['path']='absent.py'
            model_file.write_text(json.dumps(model))
            statuses=source_statuses(model,root)
            self.assertEqual(statuses[0]['status'],'missing')
            run=subprocess.run([sys.executable,'-m','living_explainers','validate',str(model_file),'--root',str(root)],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,2); self.assertIn('request-handler',run.stderr)
            result=subprocess.run([sys.executable,'-m','living_explainers','build',str(model_file),'--root',str(root),'--out',str(built)],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_cli_output_errors_and_input_overwrite_guards(self):
        model_path=ROOT/'fixtures/model.json'; original=model_path.read_bytes()
        def run(*args):
            return subprocess.run([sys.executable,'-m','living_explainers',*args],cwd=ROOT,text=True,capture_output=True)
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder); directory=out/'already-a-directory'; directory.mkdir()
            failed=run('build',str(model_path),'--root','fixtures/system','--out',str(directory))
            self.assertEqual(failed.returncode,2); self.assertNotIn('Traceback',failed.stderr); self.assertIn('output',failed.stderr)
            alias=out/'model-alias.json'; alias.symlink_to(model_path)
            failed=run('check',str(model_path),'--root','fixtures/system','--out',str(alias))
            self.assertEqual(failed.returncode,2); self.assertIn('overwrite input model',failed.stderr)
            self.assertEqual(model_path.read_bytes(),original)
            source=ROOT/'fixtures/system/authorization.py'; source_bytes=source.read_bytes()
            failed=run('build',str(model_path),'--root','fixtures/system','--out',str(source))
            self.assertEqual(failed.returncode,2); self.assertIn('overwrite referenced source',failed.stderr)
            self.assertEqual(source.read_bytes(),source_bytes)
