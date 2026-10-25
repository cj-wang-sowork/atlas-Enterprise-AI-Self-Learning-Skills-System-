"""Public-entrypoint contracts; not a native ChatGPT or Claude UI trial."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MarketingTeamEntrypointTests(unittest.TestCase):
    def test_readme_exposes_one_adaptive_core_and_all_platform_exports(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Adaptive Marketing Team", text)
        self.assertIn("docs/MARKETING_TEAM.md", text)
        for target in ("claude", "chatgpt-plugin", "chatgpt-project"):
            self.assertIn("scripts/build-marketing-team.py --target " + target, text)

    def test_public_entrypoint_separates_discovery_from_execution(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("python3 -m marketing_team discover --task", text)
        self.assertIn("read-only", text)
        self.assertIn("not a permanent installation", text)
        self.assertIn("not independently deployed agents", text)
        self.assertIn("LIVE_SEARCH_UNAVAILABLE", text)

    def test_ci_publishes_all_platform_archive_artifacts(self):
        text = (ROOT / ".github/workflows/regression.yml").read_text(encoding="utf-8")
        for target in ("claude", "chatgpt-plugin", "chatgpt-project"):
            self.assertIn("build-marketing-team.py --target " + target, text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("if-no-files-found: error", text)

    def test_discovery_instructions_require_host_review_not_metadata_approval(self):
        text = (ROOT / "team_core/resources/discovery.md").read_text(encoding="utf-8")
        self.assertIn("REVIEW_REQUIRED", text)
        self.assertIn("host assistant", text)
        self.assertIn("not human approval", text)
        self.assertIn("not a license check", text)
        self.assertIn("LIVE_SEARCH_COMPLETED", text)

    def test_ci_checks_canonical_core_before_packaging(self):
        text = (ROOT / ".github/workflows/regression.yml").read_text(encoding="utf-8")
        self.assertIn("python scripts/build-marketing-team.py --check", text)


if __name__ == "__main__":
    unittest.main()
