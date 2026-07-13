import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "plugins" / "multi-review"
BUILD = ROOT / "scripts" / "build_marketplace_plugin.py"


class MarketplaceTests(unittest.TestCase):
    def test_1_generated_plugin_is_in_sync_with_shared_core(self):
        result = subprocess.run(
            [sys.executable, str(BUILD), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_2_every_marketplace_points_to_the_same_plugin(self):
        claude = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        codex = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(claude["plugins"][0]["name"], "multi-review")
        self.assertEqual(codex["plugins"][0]["name"], "multi-review")
        self.assertEqual(codex["plugins"][0]["source"]["path"], "./plugins/multi-review")

    def test_3_platform_manifests_are_version_aligned(self):
        manifests = [
            PACKAGE / ".claude-plugin" / "plugin.json",
            PACKAGE / ".codex-plugin" / "plugin.json",
        ]
        values = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
        self.assertEqual({value["name"] for value in values}, {"multi-review"})
        self.assertEqual({value["version"] for value in values}, {"0.1.2"})
        self.assertNotIn("agents", values[0])
        self.assertEqual(values[1]["skills"], "./skills/")


if __name__ == "__main__":
    unittest.main()
