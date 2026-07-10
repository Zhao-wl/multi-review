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
            "contracts/reviewer-output.schema.json",
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
        for phrase in [
            "当前分支相对默认分支",
            "本地 origin/HEAD",
            "仓库配置",
            "明确存在的 main 或 master",
            "不能用同名 upstream 代替默认分支",
            "review_id",
            "每次审查唯一",
            "重试沿用同一值",
            "requested_reviewers 与 excluded_reviewers 有交集时停止并询问用户",
            "移除 excluded_reviewers，再按自动默认数量选取，后续候选负责补位",
            "按用户给定顺序追加到自动集合，不占自动默认名额",
            "超过 6 时停止并询问用户缩减，不启动 reviewer",
            "材料固有风险",
            "容纳最终数量所需最低风险",
            "较高者",
            "手动扩展",
            "覆盖缩减",
            "两者可以同时记录",
            "low + 1 requested",
            "medium=3",
            "排除项",
        ]:
            self.assertIn(phrase, router)
        for phrase in [
            "contracts/reviewer-output.schema.json",
            "contracts/finding.schema.json",
            "原始 Review Packet",
            "自身角色说明",
            "任何 reviewer 不接收其他 reviewer 的输出",
        ]:
            self.assertIn(phrase, router)
        self.assertNotIn("2–3 个只允许来自用户手动排除", router)
        for value in ["pass", "needs_changes", "needs_human_decision", "incomplete"]:
            self.assertIn(value, chair)
        for phrase in [
            "contracts/reviewer-output.schema.json",
            "先校验 Envelope，再校验每条 Finding",
            "envelope reviewer 必须等于每条 finding.reviewer",
            "同一 envelope 内的 local ID 必须唯一",
            "(reviewer, local_id)",
            "全局 Finding ID",
            "required_reviewers 顺序",
            "原输出顺序",
            "原子更新 reviewer_results.finding_ids",
            "所有来源",
            "Envelope.review_id 必须等于 Review Packet.review_id",
            "Envelope.reviewer 必须等于实际派遣 reviewer ID",
            "实际原 reviewer",
            "两个不同 reviewer 都返回 local F-001",
            "不同去重组",
            "global F-001",
            "global F-002",
            "同一去重组",
            "同一 global ID",
        ]:
            self.assertIn(phrase, chair)
        for phrase in ["低风险：2", "中风险：4", "高风险：最多 6"]:
            self.assertIn(phrase, risk)


if __name__ == "__main__":
    unittest.main()
