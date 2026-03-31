import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "doc-sync" / "doc_sync.py"


def load_doc_sync_module():
    spec = importlib.util.spec_from_file_location("doc_sync", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DocSyncTests(unittest.TestCase):
    def test_parse_sdk_version_from_html_title(self):
        module = load_doc_sync_module()
        html = """
        <html>
          <head><title>Rhino SDK 2.1.22 documentation</title></head>
          <body></body>
        </html>
        """

        self.assertEqual(module.parse_sdk_version(html), "2.1.22")

    def test_extract_modules_from_python_module_index(self):
        module = load_doc_sync_module()
        html = """
        <html>
          <body>
            <table>
              <tr><td><a href="autoapi/rhino_health/index.html#module-rhino_health">rhino_health</a></td></tr>
              <tr><td><a href="autoapi/rhino_health/lib/endpoints/project/index.html#module-rhino_health.lib.endpoints.project">rhino_health.lib.endpoints.project</a></td></tr>
              <tr><td><a href="autoapi/rhino_health/lib/metrics/basic/index.html#module-rhino_health.lib.metrics.basic">rhino_health.lib.metrics.basic</a></td></tr>
            </table>
          </body>
        </html>
        """

        self.assertEqual(
            module.extract_modules_from_py_modindex(html),
            [
                "rhino_health",
                "rhino_health.lib.endpoints.project",
                "rhino_health.lib.metrics.basic",
            ],
        )

    def test_extract_signatures_from_autoapi_page(self):
        module = load_doc_sync_module()
        html = """
        <html>
          <body>
            <dl>
              <dt class="sig sig-object py" id="rhino_health.lib.endpoints.project.ProjectEndpoints.create_project">
                <span class="sig-name descname"><span class="pre">create_project</span></span>
                <span class="sig-paren">(</span>
                <em class="sig-param"><span class="n"><span class="pre">name</span></span></em>
                <span class="sig-paren">)</span>
              </dt>
              <dt class="sig sig-object py" id="rhino_health.lib.endpoints.project.ProjectEndpoints.get_project">
                <span class="sig-name descname"><span class="pre">get_project</span></span>
                <span class="sig-paren">(</span>
                <em class="sig-param"><span class="n"><span class="pre">project_uid</span></span></em>
                <span class="sig-paren">)</span>
              </dt>
            </dl>
          </body>
        </html>
        """

        self.assertEqual(
            module.extract_signatures_from_autoapi(html),
            ["create_project(name)", "get_project(project_uid)"],
        )

    def test_build_diff_report_detects_changes(self):
        module = load_doc_sync_module()
        scraped = module.ScrapeSnapshot(
            sdk_version="2.1.22",
            modules=["rhino_health.lib.endpoints.project", "rhino_health.lib.endpoints.user"],
            endpoint_signatures={
                "project": ["create_project(name, enable_audit=False)", "get_project(project_uid)"]
            },
            metric_signatures={"basic": ["Count(column_name)", "Mean(column_name)"]},
            enum_members={"CodeRunStatus": ["PENDING", "RUNNING", "COMPLETED", "FAILED"]},
            example_files=["cox.ipynb", "new_example.ipynb"],
        )
        current = module.ContextSnapshot(
            sdk_version="2.1.20",
            sdk_reference_text="## ProjectEndpoints\ncreate_project(name)\n",
            metrics_reference_text="Count(column_name)\n",
            examples_index_text="| cox.py | Example |\n",
        )

        report = module.build_diff_report(scraped, current)

        self.assertEqual(report.current_version, "2.1.20")
        self.assertEqual(report.scraped_version, "2.1.22")
        self.assertIn("rhino_health.lib.endpoints.user", report.new_modules)
        self.assertIn(
            "create_project(name, enable_audit=False)",
            report.changed_signatures["project"],
        )
        self.assertIn("Mean(column_name)", report.new_metrics["basic"])
        self.assertIn("FAILED", report.enum_changes["CodeRunStatus"])
        self.assertIn("new_example.ipynb", report.new_examples)

    def test_apply_safe_updates_bumps_sdk_reference_version(self):
        module = load_doc_sync_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            context_dir = repo_root / "context"
            context_dir.mkdir(parents=True)
            sdk_reference = context_dir / "sdk_reference.md"
            sdk_reference.write_text(
                "# Rhino Health SDK — API Reference\n\n> SDK Version: 2.1.20\n",
                encoding="utf-8",
            )

            report = module.DiffReport(
                current_version="2.1.20",
                scraped_version="2.1.22",
                new_modules=[],
                changed_signatures={},
                new_metrics={},
                enum_changes={},
                new_examples=[],
                removed_examples=[],
                staleness="medium",
            )

            applied = module.apply_safe_updates(repo_root, report)

            self.assertEqual(applied, [str(sdk_reference)])
            self.assertIn("2.1.22", sdk_reference.read_text(encoding="utf-8"))

    def test_build_diff_report_normalizes_examples_and_ignores_nested_endpoint_modules(self):
        module = load_doc_sync_module()
        scraped = module.ScrapeSnapshot(
            sdk_version="2.1.20",
            modules=[
                "rhino_health.lib.endpoints.project",
                "rhino_health.lib.endpoints.project.project_baseclass",
                "rhino_health.lib.endpoints.dicomweb_query",
            ],
            endpoint_signatures={},
            metric_signatures={},
            enum_members={},
            example_files=[
                "README.md",
                "aggregate_quantile_example.ipynb",
                "federated_join",
            ],
        )
        current = module.ContextSnapshot(
            sdk_version="2.1.20",
            sdk_reference_text="## ProjectEndpoints\n",
            metrics_reference_text="",
            examples_index_text=(
                "| aggregate_quantile.py | Example |\n"
                "| federated_join.py | Example |\n"
            ),
        )

        report = module.build_diff_report(scraped, current)

        self.assertEqual(report.new_modules, ["rhino_health.lib.endpoints.dicomweb_query"])
        self.assertEqual(report.new_examples, [])
        self.assertEqual(report.removed_examples, [])


if __name__ == "__main__":
    unittest.main()
