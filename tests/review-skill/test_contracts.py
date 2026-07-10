import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "multi-agent-review"
ROLE_IDS = {
    "requirement-integrity", "acceptance-criteria", "plan-feasibility",
    "spec-compliance", "correctness-auditor", "security-abuse",
    "test-skeptic", "integration-contract", "maintainability-pragmatist",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ContractTests(unittest.TestCase):
    def test_reviewer_index_is_complete_and_unique(self):
        data = load_json(SKILL / "reviewers" / "index.json")
        ids = [item["id"] for item in data["reviewers"]]
        self.assertEqual(set(ids), ROLE_IDS)
        self.assertEqual(len(ids), len(set(ids)))

    def test_finding_schema_requires_evidence_contract(self):
        schema = load_json(SKILL / "contracts" / "finding.schema.json")
        self.assertEqual(
            set(schema["required"]),
            {"id", "reviewer", "severity", "category", "location", "claim",
             "evidence", "impact", "recommendation", "confidence"},
        )
        self.assertEqual(schema["properties"]["reviewer"]["enum"], sorted(ROLE_IDS))
        self.assertEqual(schema["properties"]["severity"]["enum"], ["blocking", "advisory", "question"])

    def test_route_schema_and_routes_reference_known_roles(self):
        schema = load_json(SKILL / "contracts" / "route-decision.schema.json")
        self.assertEqual(schema["properties"]["risk"]["enum"], ["low", "medium", "high"])
        routes = load_json(SKILL / "routing" / "default-routes.yaml")
        referenced = {role for route in routes["routes"] for role in route["reviewers"]}
        self.assertTrue(referenced <= ROLE_IDS)
        self.assertEqual(routes["risk_limits"], {"low": 2, "medium": 4, "high": 6})

    def test_review_result_is_chinese_and_has_safe_statuses(self):
        schema = load_json(SKILL / "contracts" / "review-result.schema.json")
        self.assertEqual(schema["properties"]["report_language"]["const"], "zh-CN")
        self.assertEqual(
            schema["properties"]["status"]["enum"],
            ["pass", "needs_changes", "needs_human_decision", "incomplete"],
        )

    def test_report_template_uses_required_chinese_headings(self):
        text = (SKILL / "templates" / "review-report.md").read_text(encoding="utf-8")
        for heading in ["审查结论", "阻塞问题", "建议问题", "待确认问题", "需求追溯",
                        "Reviewer 覆盖", "Reviewer 冲突", "豁免", "必需后续操作", "审查限制"]:
            self.assertIn(heading, text)

    def test_openai_metadata_has_ui_copy_and_default_prompt(self):
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "多子代理审查"', text)
        self.assertIn('short_description: "按风险启动多位独立审查员并汇总可追溯的中文证据化审查报告"', text)
        self.assertIn('$multi-agent-review', text)


if __name__ == "__main__":
    unittest.main()
