from __future__ import annotations

import importlib.util
import json
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

    def test_validate_figure_accepts_complete_python_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            self.write_valid_figure_project(project_dir)

            result = self.tool.validate_figure(project_dir)

        self.assertFalse(result.errors)

    def test_validate_figure_rejects_missing_contract_and_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "data").mkdir()
            (project_dir / "data" / "source.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            (project_dir / "manifest.json").write_text(
                json.dumps({"backend": "python", "data_dir": "data"}),
                encoding="utf-8",
            )

            result = self.tool.validate_figure(project_dir)

        self.assertIn("manifest must include a figure_contract object", result.errors)
        self.assertIn("manifest must include script or plot_script", result.errors)
        self.assertIn("manifest must include exports or output_files", result.errors)

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

    def write_valid_figure_project(self, project_dir: Path):
        (project_dir / "data").mkdir()
        (project_dir / "scripts").mkdir()
        (project_dir / "figures").mkdir()
        (project_dir / "data" / "source.csv").write_text("x,y\n1,2\n", encoding="utf-8")
        (project_dir / "scripts" / "plot.py").write_text(
            "import matplotlib.pyplot as plt\n"
            "plt.rcParams['svg.fonttype'] = 'none'\n"
            "plt.rcParams['pdf.fonttype'] = 42\n"
            "fig, ax = plt.subplots()\n"
            "ax.plot([1], [2])\n"
            "fig.savefig('figures/figure.svg')\n",
            encoding="utf-8",
        )
        (project_dir / "figures" / "figure.svg").write_text(
            "<svg><text>Figure</text></svg>", encoding="utf-8"
        )
        (project_dir / "figures" / "figure.pdf").write_bytes(b"%PDF-1.4\n")
        (project_dir / "figures" / "figure.tiff").write_bytes(b"II*\x00")
        manifest = {
            "backend": "python",
            "data_dir": "data",
            "script": "scripts/plot.py",
            "exports": {
                "svg": "figures/figure.svg",
                "pdf": "figures/figure.pdf",
                "preview": "figures/figure.tiff",
            },
            "figure_contract": {
                "core_conclusion": "Treatment X reduces Y.",
                "figure_archetype": "quantitative grid",
                "target_journal_output": "Nature double-column",
                "backend": "Python",
                "final_size": "183 mm x 120 mm",
                "panel_map": {"a": "Primary comparison"},
                "evidence_hierarchy": {"hero evidence": "Panel a"},
                "statistics_needed": "n, center, spread, test",
                "source_data_needed": "data/source.csv",
                "image_integrity_notes": "No image panels",
                "reviewer_risk": "Sample size visibility",
            },
            "qa": {
                "core_conclusion": "pass",
                "archetype": "pass",
                "backend_exclusivity": "pass",
                "final_size": "pass",
                "text_size": "pass",
                "panel_labels": "pass",
                "editable_text": "pass",
                "font": "pass",
                "color": "pass",
                "legend_strategy": "pass",
                "statistics": "pass",
                "source_data": "pass",
                "raster_resolution": "n/a",
                "microscopy_scale": "n/a",
                "image_integrity": "n/a",
                "export_bundle": "pass",
            },
            "statistical_claims": True,
            "statistics": {"n definition": "Biological replicates"},
            "image_panels": False,
        }
        (project_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
