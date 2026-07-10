import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "multi-agent-review"
REVIEWERS = SKILL / "reviewers"
EXPECTED = {
    "requirement-integrity": (
        "需求完整性审查员", "不断追问定义和边界的需求编辑",
        "目标、用户、范围、非目标、术语、隐藏前提、矛盾和未定义失败行为",
        "代码风格、具体实现优劣、测试框架选择",
    ),
    "acceptance-criteria": (
        "验收标准审查员", "只接受可证伪条件的验收官",
        "可观察结果、pass/fail 边界、空值、错误、权限、兼容性和 AC 到证据映射",
        "具体实现方案、抽象设计、命名风格",
    ),
    "plan-feasibility": (
        "计划可行性审查员", "关注落地顺序和恢复路径的项目工程师",
        "依赖、步骤顺序、迁移、兼容、回滚、验证点、未决问题和范围混杂",
        "重写产品目标、实现阶段的局部代码风格",
    ),
    "spec-compliance": (
        "需求符合性审查员", "逐条对照承诺与证据的审计员",
        "Spec item、AC、实现位置、测试证据、遗漏、部分满足和 plan drift",
        "擅自扩充或改变需求、纯代码风格",
    ),
    "correctness-auditor": (
        "正确性审计员", "对状态和边界保持怀疑的逻辑检查者",
        "条件、状态转换、异常、空值、并发、幂等、重试、生命周期和资源释放",
        "纯格式、命名偏好、没有行为影响的重构",
    ),
    "security-abuse": (
        "安全与滥用审查员", "从攻击者和越权者视角寻找可利用路径",
        "认证、对象级授权、租户隔离、输入、注入、路径、secret、日志敏感数据和第三方信任边界",
        "一般可维护性、无安全影响的样式问题",
    ),
    "test-skeptic": (
        "测试证据审查员", "不把“存在测试”等同于“行为已证明”的怀疑者",
        "弱断言、happy path 偏置、过度 Mock、缺失回归、错误路径、测试与 AC 的对应关系",
        "与风险无关的测试数量追求、具体生产实现风格",
    ),
    "integration-contract": (
        "集成契约审查员", "保护调用双方边界的接口守门人",
        "API、Schema、事件 payload、错误码、序列化、配置、版本兼容和调用链",
        "模块内部且不影响契约的局部实现",
    ),
    "maintainability-pragmatist": (
        "可维护性审查员", "只保护有现实维护成本的务实维护者",
        "重复业务规则、复杂度、职责边界、命名歧义、过度抽象和可测试性",
        "理想化重写、没有成本证据的个人偏好",
    ),
}
EVIDENCE = "只报告能引用具体材料、路径、符号、条款或测试证据的问题。证据不足时输出 question，不猜测。"
OUTPUT = (
    "只返回符合 `contracts/reviewer-output.schema.json` 的单个 Envelope，包含 "
    "review_id、reviewer、findings、reviewed_scope、limitations、report_language。"
    "使用中文；技术标识保持原文。不得修改项目、不得联系其他 reviewer、"
    "不得执行修复、不得派生子代理。"
)


def section(text, heading):
    return text.split(f"## {heading}\n\n", 1)[1].split("\n\n## ", 1)[0].strip()


class RoleTests(unittest.TestCase):
    def test_every_indexed_role_has_a_focused_file(self):
        index = json.loads((REVIEWERS / "index.json").read_text(encoding="utf-8"))
        self.assertEqual({role["id"] for role in index["reviewers"]}, set(EXPECTED))
        for role in index["reviewers"]:
            path = ROOT / ".agents" / "skills" / "multi-agent-review" / role["role_path"]
            text = path.read_text(encoding="utf-8")
            name, personality, checks, exclusions = EXPECTED[role["id"]]
            self.assertIn(f"reviewer_id: {role['id']}", text)
            self.assertIn(f"# {name}\n", text)
            self.assertEqual(section(text, "性格"), personality)
            self.assertEqual(section(text, "只检查"), checks)
            self.assertEqual(section(text, "不检查"), exclusions)
            self.assertEqual(section(text, "证据要求"), EVIDENCE)
            self.assertEqual(section(text, "输出"), OUTPUT)
            for phrase in ["不得修改项目", "联系其他 reviewer", "执行修复", "不得派生子代理"]:
                self.assertIn(phrase, section(text, "输出"))

    def test_role_focus_is_not_identical(self):
        texts = [p.read_text(encoding="utf-8") for p in REVIEWERS.glob("*.md")]
        self.assertEqual(len(texts), 9)
        self.assertEqual(len(set(texts)), 9)
        schema_path = SKILL / "contracts" / "reviewer-output.schema.json"
        self.assertTrue(schema_path.exists(), "缺少 reviewer-output.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["required"]),
            {"review_id", "reviewer", "findings", "reviewed_scope", "limitations", "report_language"},
        )
        properties = schema["properties"]
        self.assertEqual(properties["reviewer"]["enum"], sorted(EXPECTED))
        self.assertEqual(properties["findings"]["items"], {"$ref": "finding.schema.json"})
        self.assertEqual(properties["report_language"]["const"], "zh-CN")


if __name__ == "__main__":
    unittest.main()
