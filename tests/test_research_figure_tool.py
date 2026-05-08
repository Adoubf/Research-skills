from __future__ import annotations

import contextlib
import io
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

    def test_validate_figure_rejects_core_qa_na(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            manifest = self.write_valid_figure_project(project_dir)
            manifest["qa"]["statistics"] = "n/a"
            self.write_manifest(project_dir, manifest)

            result = self.tool.validate_figure(project_dir)

        self.assertIn("qa check did not pass: statistics (Statistics)", result.errors)

    def test_validate_figure_requires_json_manifest_not_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "data").mkdir()
            (project_dir / "data" / "source.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            (project_dir / "manifest.yaml").write_text("backend: python\n", encoding="utf-8")

            result = self.tool.validate_figure(project_dir)

        self.assertIn("manifest.yaml/yml is not supported; use manifest.json", result.errors)
        self.assertIn("Figure validation requires manifest.json", result.errors)

    def test_validate_figure_rejects_missing_source_data_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            manifest = self.write_valid_figure_project(project_dir)
            manifest["figure_contract"]["source_data_needed"] = "data/missing.csv"
            self.write_manifest(project_dir, manifest)

            result = self.tool.validate_figure(project_dir)

        self.assertIn(
            "figure_contract.source_data_needed does not exist: data/missing.csv",
            result.errors,
        )

    def test_validate_figure_counts_only_existing_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            self.write_valid_figure_project(project_dir)
            (project_dir / "figures" / "figure.svg").unlink()

            result = self.tool.validate_figure(project_dir)

        self.assertIn("listed export does not exist: figures/figure.svg", result.errors)
        self.assertIn("export bundle must include an SVG primary output", result.errors)

    def test_validate_figure_rejects_project_escape_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            manifest = self.write_valid_figure_project(project_dir)
            manifest["figure_contract"]["source_data_needed"] = "../outside.csv"
            manifest["statistics"]["source-data file"] = "/tmp/outside.csv"
            self.write_manifest(project_dir, manifest)

            result = self.tool.validate_figure(project_dir)

        self.assertIn(
            "figure_contract.source_data_needed escapes project directory: ../outside.csv",
            result.errors,
        )
        self.assertIn(
            "statistics.source-data file must be project-relative, not absolute: /tmp/outside.csv",
            result.errors,
        )

    def test_validate_figure_rejects_python_comment_only_fonttype(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            self.write_valid_figure_project(project_dir)
            (project_dir / "scripts" / "plot.py").write_text(
                "import matplotlib.pyplot as plt\n"
                "# plt.rcParams['svg.fonttype'] = 'none'\n"
                "# plt.rcParams['pdf.fonttype'] = 42\n"
                "fig, ax = plt.subplots()\n"
                "fig.savefig('figures/figure.svg')\n",
                encoding="utf-8",
            )

            result = self.tool.validate_figure(project_dir)

        self.assertIn(
            "Python plot script must set svg.fonttype='none' for editable SVG text",
            result.errors,
        )

    def test_validate_figure_rejects_backend_script_extension_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            manifest = self.write_valid_figure_project(project_dir)
            manifest["backend"] = "r"
            manifest["figure_contract"]["backend"] = "R"
            self.write_manifest(project_dir, manifest)

            result = self.tool.validate_figure(project_dir)

        self.assertIn(
            "plot script extension '.py' does not match backend r; expected .r",
            result.errors,
        )

    def test_validate_figure_accepts_complete_r_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            manifest = self.write_valid_figure_project(project_dir)
            r_script = project_dir / "scripts" / "plot.R"
            r_script.write_text(
                "library(ggplot2)\n"
                "plot <- ggplot(data.frame(x = 1, y = 2), aes(x, y)) + geom_point()\n"
                "svglite::svglite('figures/figure.svg', width = 7, height = 4)\n"
                "print(plot)\n"
                "dev.off()\n"
                "grDevices::cairo_pdf('figures/figure.pdf', width = 7, height = 4)\n"
                "print(plot)\n"
                "dev.off()\n"
                "ragg::agg_tiff('figures/figure.tiff', width = 7, height = 4, units = 'in', res = 600)\n"
                "print(plot)\n"
                "dev.off()\n",
                encoding="utf-8",
            )
            manifest["backend"] = "r"
            manifest["script"] = "scripts/plot.R"
            manifest["figure_contract"]["backend"] = "R"
            self.write_manifest(project_dir, manifest)

            result = self.tool.validate_figure(project_dir)

        self.assertFalse(result.errors)

    def test_validate_figure_rejects_r_missing_svglite(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            manifest = self.write_valid_figure_project(project_dir)
            r_script = project_dir / "scripts" / "plot.R"
            r_script.write_text(
                "# svglite::svglite('figures/figure.svg')\n"
                "grDevices::cairo_pdf('figures/figure.pdf')\n"
                "ragg::agg_tiff('figures/figure.tiff')\n",
                encoding="utf-8",
            )
            manifest["backend"] = "r"
            manifest["script"] = "scripts/plot.R"
            manifest["figure_contract"]["backend"] = "R"
            self.write_manifest(project_dir, manifest)

            result = self.tool.validate_figure(project_dir)

        self.assertIn("R plot script must use svglite for editable SVG export", result.errors)

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
            self.assertIn("research-figure/LICENSE", names)
            shutil.rmtree(out_dir / "research-figure")

    def test_pack_skill_no_zip_exports_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "dist"

            output = self.tool.pack_skill(REPO_ROOT / "research-figure", out_dir, zip_output=False)

            self.assertEqual(output, out_dir / "research-figure")
            self.assertTrue((output / "SKILL.md").is_file())
            self.assertTrue((output / "LICENSE").is_file())

    def test_pack_skill_from_skill_root_excludes_nested_dist(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "research-figure"
            shutil.copytree(REPO_ROOT / "research-figure", source)

            output = self.tool.pack_skill(source, source / "dist", zip_output=False)

            self.assertTrue((output / "SKILL.md").is_file())
            self.assertFalse((output / "dist").exists())

    def test_main_cli_commands_return_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "project"
            project_dir.mkdir()
            self.write_valid_figure_project(project_dir)
            out_dir = Path(tmp) / "dist"

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                validate_skill_code = self.tool.main(["validate-skill", str(REPO_ROOT / "research-figure")])
                validate_figure_code = self.tool.main(["validate-figure", str(project_dir)])
                pack_code = self.tool.main(
                    ["pack-skill", str(REPO_ROOT / "research-figure"), "--out", str(out_dir), "--no-zip"]
                )

        self.assertEqual(validate_skill_code, 0)
        self.assertEqual(validate_figure_code, 0)
        self.assertEqual(pack_code, 0)

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
            "statistics": {
                "n definition": "Biological replicates per group",
                "biological replicates": "n = 3 independent cultures",
                "technical replicates": "Two measurements per culture",
                "center statistic": "Mean",
                "spread/interval": "95% CI",
                "test": "Two-sided Welch t-test",
                "multiple-comparison correction": "Benjamini-Hochberg",
                "p-value display": "Exact p values in source data",
                "source-data file": "data/source.csv",
            },
            "image_panels": False,
        }
        self.write_manifest(project_dir, manifest)
        return manifest

    def write_manifest(self, project_dir: Path, manifest: dict[str, object]):
        (project_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
