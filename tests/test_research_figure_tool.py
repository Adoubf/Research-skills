from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "research-figure" / "scripts" / "research_figure_tool.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("research_figure_tool_under_test", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ResearchFigureToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_validate_skill_accepts_bundled_skill(self):
        result = self.tool.validate_skill(REPO_ROOT / "research-figure")
        self.assertFalse(result.errors)

    def test_validate_project_requires_data_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.tool.validate_project(Path(tmp))
        self.assertIn("Missing required data directory: data/", result.errors)

    def test_validate_project_accepts_supported_data_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            data_dir = project_dir / "data"
            data_dir.mkdir()
            (data_dir / "source.csv").write_text("x,y\n1,2\n", encoding="utf-8")

            result = self.tool.validate_project(project_dir)

        self.assertFalse(result.errors)

    def test_pack_skill_exports_directory_and_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "dist"

            output = self.tool.pack_skill(REPO_ROOT / "research-figure", out_dir)

            self.assertEqual(output, out_dir / "research-figure.zip")
            self.assertTrue((out_dir / "research-figure" / "SKILL.md").is_file())
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as zf:
                names = zf.namelist()
            self.assertIn("research-figure/SKILL.md", names)
            self.assertFalse(any("__pycache__" in name for name in names))
            shutil.rmtree(out_dir / "research-figure")


if __name__ == "__main__":
    unittest.main()
