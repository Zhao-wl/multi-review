import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "multi-agent-review"


class OrchestrationTests(unittest.TestCase):
    def test_skill_is_concise_and_routes_to_focused_files(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text), 6000)
        for path in [
            "orchestration/router.md",
            "orchestration/chair.md",
            "orchestration/risk-levels.md",
            "routing/default-routes.yaml",
            "contracts/finding.schema.json",
            "templates/review-report.md",
        ]:
            self.assertIn(path, text)

    def test_skill_requires_real_isolated_read_only_reviewers(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in [
            "真实独立子代理",
            "不得修改",
            "不能读取其他 reviewer",
            "全部 reviewer 完成后",
            "中文",
        ]:
            self.assertIn(phrase, text)

    def test_router_and_chair_cover_safety_states(self):
        router = (SKILL / "orchestration" / "router.md").read_text(
            encoding="utf-8"
        )
        chair = (SKILL / "orchestration" / "chair.md").read_text(
            encoding="utf-8"
        )
        risk = (SKILL / "orchestration" / "risk-levels.md").read_text(
            encoding="utf-8"
        )
        for phrase in ["Review Packet", "无 Git 仓库", "少于两个 reviewer", "分批"]:
            self.assertIn(phrase, router)
        for value in ["pass", "needs_changes", "needs_human_decision", "incomplete"]:
            self.assertIn(value, chair)
        for phrase in ["低风险：2", "中风险：4", "高风险：最多 6"]:
            self.assertIn(phrase, risk)


if __name__ == "__main__":
    unittest.main()
