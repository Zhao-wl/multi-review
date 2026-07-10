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
        stages = {item["id"]: set(item["stages"]) for item in data["reviewers"]}
        self.assertEqual(stages["plan-feasibility"], {"spec", "plan"})
        self.assertEqual(stages["test-skeptic"], {"spec", "plan", "implementation", "mixed"})
        self.assertEqual(stages["requirement-integrity"], {"spec", "plan", "mixed"})

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
        condition_limits = {}
        for condition in schema.get("allOf", []):
            predicate = condition["if"]
            self.assertEqual(predicate.get("required"), ["risk"])
            risk = predicate["properties"]["risk"]["const"]
            limits = condition["then"]["properties"]["required_reviewers"]
            condition_limits[risk] = (limits["minItems"], limits["maxItems"])
        self.assertEqual(condition_limits, {"low": (2, 2), "medium": (2, 4), "high": (2, 6)})
        routes = load_json(SKILL / "routing" / "default-routes.yaml")
        referenced = {role for route in routes["routes"] for role in route["reviewers"]}
        self.assertTrue(referenced <= ROLE_IDS)
        self.assertEqual(routes["risk_limits"], {"low": 2, "medium": 4, "high": 6})
        index = load_json(SKILL / "reviewers" / "index.json")
        stages = {item["id"]: set(item["stages"]) for item in index["reviewers"]}
        for route in routes["routes"]:
            for reviewer in route["reviewers"]:
                self.assertIn(route["artifact_type"], stages[reviewer])

    def test_review_result_is_chinese_and_has_safe_statuses(self):
        schema = load_json(SKILL / "contracts" / "review-result.schema.json")
        self.assertEqual(schema["properties"]["report_language"]["const"], "zh-CN")
        self.assertEqual(
            schema["properties"]["status"]["enum"],
            ["pass", "needs_changes", "needs_human_decision", "incomplete"],
        )
        item = schema["properties"]["reviewer_results"]["items"]
        properties = item.get("properties", {})
        actual_contract = {
            "additionalProperties": item.get("additionalProperties"),
            "required": set(item.get("required", [])),
            "reviewer": properties.get("reviewer"),
            "agent_id": properties.get("agent_id"),
            "status": properties.get("status"),
            "finding_ids": properties.get("finding_ids"),
            "limitations": properties.get("limitations"),
        }
        expected_contract = {
            "additionalProperties": False,
            "required": {"reviewer", "agent_id", "status", "finding_ids", "limitations"},
            "reviewer": {"type": "string", "enum": sorted(ROLE_IDS)},
            "agent_id": {"type": "string"},
            "status": {"type": "string", "enum": ["completed", "failed", "invalid"]},
            "finding_ids": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "pattern": "^F-[0-9]{3,}$"},
            },
            "limitations": {"type": "array", "items": {"type": "string"}},
        }
        self.assertEqual(actual_contract, expected_contract)

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
