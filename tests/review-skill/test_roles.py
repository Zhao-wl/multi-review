import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEWERS = ROOT / ".agents" / "skills" / "multi-agent-review" / "reviewers"


class RoleTests(unittest.TestCase):
    def test_every_indexed_role_has_a_focused_file(self):
        index = json.loads((REVIEWERS / "index.json").read_text(encoding="utf-8"))
        for role in index["reviewers"]:
            path = ROOT / ".agents" / "skills" / "multi-agent-review" / role["role_path"]
            text = path.read_text(encoding="utf-8")
            self.assertIn(f"reviewer_id: {role['id']}", text)
            for heading in ["性格", "只检查", "不检查", "证据要求", "输出"]:
                self.assertIn(heading, text)
            self.assertNotIn("修改文件", text.split("## 输出")[-1])

    def test_role_focus_is_not_identical(self):
        texts = [p.read_text(encoding="utf-8") for p in REVIEWERS.glob("*.md")]
        self.assertEqual(len(texts), 9)
        self.assertEqual(len(set(texts)), 9)


if __name__ == "__main__":
    unittest.main()
