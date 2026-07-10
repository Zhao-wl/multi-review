# Reviewer 多子代理技能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 在当前项目中实现一套默认只读、动态路由、真实启动多个独立 reviewer，并在 Codex、Cursor、Claude Code 中统一输出中文报告的 Review 技能。

**架构：** `.agents/skills/multi-agent-review/` 是唯一共享内核，编排、角色、路由、Schema 和报告模板分别存放。三端原生代理文件只提供平台元数据、只读权限和共享角色定位；Router 与 Chair 由主代理承担，reviewer 子代理互相隔离。

**技术栈：** Agent Skills `SKILL.md`、Markdown、JSON Schema、JSON-compatible YAML、TOML、Python 3.12 标准库、Codex CLI、Cursor Agent CLI、Claude Code CLI。

## 全局约束

- 所有用户可见输出和最终报告必须使用中文；路径、代码符号、API、配置键和 reviewer ID 保持原文。
- 默认只读，不修改被审查项目，不自动保存报告，不自动修复，不自动豁免。
- 每次默认至少启动 2 个真实独立子代理；低、中、高风险分别选择 2、4、最多 6 个 reviewer。
- 子代理只接收不可变 Review Packet 和自己的角色说明，不能看到其他 reviewer 的 findings。
- 平台并发不足时分批运行，但后一批不能接收前一批 findings。
- 不固定模型；Codex、Cursor、Claude Code 均继承父会话模型。
- 不使用符号链接，不把三套完整审查规则复制到平台适配文件。
- 内部枚举使用英文稳定值；中文报告显示对应中文名称。
- 测试只使用 Python 标准库，不增加项目运行时依赖。
- 用户已批准直接在当前本地目录执行。控制器在 Task 1 前初始化 Git、提交现有文档基线并切换到 `feature/multi-agent-review`；不创建 worktree。每个任务必须生成提交和 Git Diff 审查包。
- 当前实机基线：Codex CLI `0.142.5`、Cursor Agent `2026.06.29-2ad2186`、Claude Code `2.1.168`、Python `3.12.3`。
- 设计依据：[设计文档](../specs/2026-07-10-reviewer-multi-agent-skill-design.md)。
- 开始 Task 1 前，主执行者必须使用 `skill-creator`、`superpowers:writing-skills` 和 `superpowers:test-driven-development`；任务执行使用 `superpowers:subagent-driven-development` 时，每个实现任务结束后接受规格与质量两阶段审查。

---

## 文件职责映射

- `.agents/skills/multi-agent-review/SKILL.md`：跨平台主入口，只描述运行顺序和硬性约束。
- `.agents/skills/multi-agent-review/agents/openai.yaml`：Codex UI 名称、短描述和默认调用提示。
- `.agents/skills/multi-agent-review/orchestration/router.md`：目标解析、Packet 构造、风险识别和 reviewer 选择。
- `.agents/skills/multi-agent-review/orchestration/chair.md`：Schema 校验、去重、冲突、状态和中文报告生成。
- `.agents/skills/multi-agent-review/orchestration/risk-levels.md`：低、中、高风险定义和数量上限。
- `.agents/skills/multi-agent-review/reviewers/index.json`：稳定 reviewer ID、中文名称、描述、阶段和角色文件路径。
- `.agents/skills/multi-agent-review/reviewers/*.md`：每个 reviewer 独立的性格、检查面、证据要求和排除项。
- `.agents/skills/multi-agent-review/routing/default-routes.yaml`：JSON-compatible YAML 路由表。
- `.agents/skills/multi-agent-review/contracts/*.schema.json`：Route、Finding 和 Review Result 机器契约。
- `.agents/skills/multi-agent-review/templates/review-report.md`：全中文最终报告模板。
- `.codex/agents/*.toml`：Codex 原生只读 reviewer。
- `.cursor/agents/*.md`：Cursor 原生 `readonly: true` reviewer。
- `.claude/agents/*.md`：Claude Code 原生只读 reviewer。
- `.claude/skills/multi-agent-review/SKILL.md`：Claude Code 薄入口。
- `scripts/generate_review_adapters.py`：从 reviewer 索引确定性生成三端薄适配文件。
- `tests/review-skill/`：基线场景、静态测试、行为评估和实机验证记录。

### Task 1：建立无技能失败基线

**文件：**

- Create: `tests/review-skill/fixtures/spec-ambiguous.md`
- Create: `tests/review-skill/fixtures/plan-migration.md`
- Create: `tests/review-skill/fixtures/implementation-auth.md`
- Create: `tests/review-skill/fixtures/implementation-retry.md`
- Create: `tests/review-skill/scenarios/control-prompts.md`
- Create: `tests/review-skill/expected/baseline-observations.md`

**接口：**

- Consumes: 无。
- Produces: 四个固定审查材料，以及后续 RED/GREEN 对比所需的无技能原始表现记录。

- [ ] **Step 1：写入四个固定场景**

`spec-ambiguous.md` 使用以下内容：

```markdown
# 自动保存需求

编辑器应支持自动保存，并且保存过程必须足够快，不能打断用户。
```

`plan-migration.md` 使用以下内容：

```markdown
# accountId 迁移计划

1. 把数据库中的 accountId 从整数改为 UUID。
2. 修改 API Schema。
3. 部署服务。
4. 运行单元测试确认功能正常。
```

`implementation-auth.md` 使用以下内容：

```markdown
# 审查材料

要求：只有项目成员可以导出项目数据。

```ts
export async function exportProject(req: Request) {
  const user = requireAuthenticatedUser(req);
  const projectId = req.params.projectId;
  return exportService.export(projectId, user.id);
}
```

现有测试只验证未登录用户返回 401。
```

`implementation-retry.md` 使用以下内容：

```markdown
# 审查材料

要求：失败任务最多重试三次。

```ts
while (retryCount <= maxRetry) {
  await queue.enqueue(job);
  retryCount += 1;
}
```

测试只断言 `queue.enqueue` 被调用过。
```

- [ ] **Step 2：写入控制提示词**

`control-prompts.md` 必须包含四条互相独立的提示词，每条都使用以下完整形式，仅替换最后的文件路径：

```text
不要使用任何项目级 multi-agent-review 技能或自定义 reviewer。请独立审查指定文件，给出你认为重要的问题：tests/review-skill/fixtures/spec-ambiguous.md
```

其余三个路径依次为 `plan-migration.md`、`implementation-auth.md`、`implementation-retry.md`。

- [ ] **Step 3：运行 RED 基线**

对四个场景各启动一个新鲜、无 multi-agent-review 技能上下文的子代理。不得向代理透露设计目标、预期 finding 或已知缺陷。

Expected: 至少出现一种自然失败，例如遗漏验收条件、遗漏回滚、把弱断言当成充分测试、缺少对象级授权证据，或者输出缺少统一结构。若控制组已完全满足目标，则停止编写对应规则，因为该行为没有可复现失败。

- [ ] **Step 4：记录逐字基线证据**

`baseline-observations.md` 以“无技能基线观察”为一级标题，依次使用 `spec-ambiguous`、`plan-migration`、`implementation-auth`、`implementation-retry` 四个二级标题。每节直接写入本次真实子代理标识、未经改写的完整原始输出，以及仅从该输出能够证明的缺口。不得预先写入假结果或预期结论。

- [ ] **Step 5：提交检查点**

Run: `git status --short`

Expected: 列出本任务新增的基线文件，没有意外修改。

有效仓库中执行：

```powershell
git add tests/review-skill
git commit -m "test: capture reviewer skill baseline"
```

### Task 2：先测试并建立机器契约、路由和中文报告模板

**文件：**

- Create: `tests/review-skill/test_contracts.py`
- Create: `.agents/skills/multi-agent-review/reviewers/index.json`
- Create: `.agents/skills/multi-agent-review/contracts/finding.schema.json`
- Create: `.agents/skills/multi-agent-review/contracts/route-decision.schema.json`
- Create: `.agents/skills/multi-agent-review/contracts/review-result.schema.json`
- Create: `.agents/skills/multi-agent-review/routing/default-routes.yaml`
- Create: `.agents/skills/multi-agent-review/templates/review-report.md`
- Create: `.agents/skills/multi-agent-review/agents/openai.yaml`

**接口：**

- Consumes: 设计文档中的 9 个 reviewer ID、风险路由、Finding 字段和中文报告章节。
- Produces: 标准初始化的技能目录、Codex UI 元数据、`ROLE_IDS` 稳定集合、三份 Schema、路由表和 Chair 可直接填充的中文模板。

- [ ] **Step 1：写失败测试**

创建 `test_contracts.py`：

```python
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
        self.assertEqual(condition_limits, {"low": (2, 2), "medium": (4, 4), "high": (2, 6)})
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
```

- [ ] **Step 2：运行测试并确认 RED**

Run: `python tests/review-skill/test_contracts.py -v`

Expected: FAIL，首个错误是找不到 `.agents/skills/multi-agent-review/reviewers/index.json`。

- [ ] **Step 3：使用 skill-creator 标准脚本初始化技能目录**

Run:

```powershell
python "C:\Users\zhaowenlong\.codex\skills\.system\skill-creator\scripts\init_skill.py" multi-agent-review --path .agents/skills --interface 'display_name=多子代理审查' --interface 'short_description=按风险启动多位独立审查员并汇总可追溯的中文证据化审查报告' --interface 'default_prompt=请使用 $multi-agent-review 审查当前变更，按风险启动独立 reviewer，并输出中文证据化报告。'
```

Expected: exit 0；生成 `.agents/skills/multi-agent-review/SKILL.md` 和 `.agents/skills/multi-agent-review/agents/openai.yaml`。Task 3 会在自己的 RED 测试之后替换初始化模板。

- [ ] **Step 4：写入 reviewer 索引**

`index.json` 使用以下对象结构，并包含全部 9 项：

```json
{
  "reviewers": [
    {"id":"requirement-integrity","display_name":"需求完整性审查员","description":"检查目标、用户、范围、非目标、术语和隐藏前提。","stages":["spec","plan","mixed"],"role_path":"reviewers/requirement-integrity.md"},
    {"id":"acceptance-criteria","display_name":"验收标准审查员","description":"把模糊愿望检查为可观察、可测试、可判定条件。","stages":["spec","plan"],"role_path":"reviewers/acceptance-criteria.md"},
    {"id":"plan-feasibility","display_name":"计划可行性审查员","description":"检查依赖、顺序、迁移、回滚和验证点。","stages":["spec","plan"],"role_path":"reviewers/plan-feasibility.md"},
    {"id":"spec-compliance","display_name":"需求符合性审查员","description":"逐条核对 Spec、实现和测试证据。","stages":["implementation","mixed"],"role_path":"reviewers/spec-compliance.md"},
    {"id":"correctness-auditor","display_name":"正确性审计员","description":"检查条件、状态、异常、并发、幂等和生命周期。","stages":["implementation","mixed"],"role_path":"reviewers/correctness-auditor.md"},
    {"id":"security-abuse","display_name":"安全与滥用审查员","description":"从攻击者角度检查认证、授权、输入和敏感数据。","stages":["spec","plan","implementation","mixed"],"role_path":"reviewers/security-abuse.md"},
    {"id":"test-skeptic","display_name":"测试证据审查员","description":"检查弱断言、过度 Mock、回归缺口和测试与 AC 的对应关系。","stages":["spec","plan","implementation","mixed"],"role_path":"reviewers/test-skeptic.md"},
    {"id":"integration-contract","display_name":"集成契约审查员","description":"检查 API、Schema、事件、配置、版本兼容和调用边界。","stages":["spec","plan","implementation","mixed"],"role_path":"reviewers/integration-contract.md"},
    {"id":"maintainability-pragmatist","display_name":"可维护性审查员","description":"务实检查重复规则、复杂度、职责边界和可测试性。","stages":["implementation","mixed"],"role_path":"reviewers/maintainability-pragmatist.md"}
  ]
}
```

- [ ] **Step 5：写入三份 Schema**

`finding.schema.json`：

```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Review Finding","type":"object","additionalProperties":false,"required":["id","reviewer","severity","category","location","claim","evidence","impact","recommendation","confidence"],"properties":{"id":{"type":"string","pattern":"^F-[0-9]{3,}$"},"reviewer":{"type":"string","enum":["acceptance-criteria","correctness-auditor","integration-contract","maintainability-pragmatist","plan-feasibility","requirement-integrity","security-abuse","spec-compliance","test-skeptic"]},"severity":{"type":"string","enum":["blocking","advisory","question"]},"category":{"type":"string","minLength":1},"location":{"type":"string","minLength":1},"claim":{"type":"string","minLength":1},"evidence":{"type":"string","minLength":1},"impact":{"type":"string","minLength":1},"recommendation":{"type":"string","minLength":1},"confidence":{"type":"string","enum":["low","medium","high"]}}}
```

`route-decision.schema.json`：

```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Route Decision","type":"object","additionalProperties":false,"required":["artifact_type","risk","required_reviewers","reason"],"properties":{"artifact_type":{"type":"string","enum":["spec","plan","implementation","mixed"]},"risk":{"type":"string","enum":["low","medium","high"]},"required_reviewers":{"type":"array","minItems":2,"maxItems":6,"uniqueItems":true,"items":{"type":"string","enum":["acceptance-criteria","correctness-auditor","integration-contract","maintainability-pragmatist","plan-feasibility","requirement-integrity","security-abuse","spec-compliance","test-skeptic"]}},"reason":{"type":"string","minLength":1}},"allOf":[{"if":{"properties":{"risk":{"const":"low"}},"required":["risk"]},"then":{"properties":{"required_reviewers":{"minItems":2,"maxItems":2}}}},{"if":{"properties":{"risk":{"const":"medium"}},"required":["risk"]},"then":{"properties":{"required_reviewers":{"minItems":4,"maxItems":4}}}},{"if":{"properties":{"risk":{"const":"high"}},"required":["risk"]},"then":{"properties":{"required_reviewers":{"minItems":2,"maxItems":6}}}}]}
```

`review-result.schema.json`：

```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Review Result","type":"object","additionalProperties":false,"required":["status","risk","reviewed_scope","reviewer_results","findings","limitations","report_language"],"properties":{"status":{"type":"string","enum":["pass","needs_changes","needs_human_decision","incomplete"]},"risk":{"type":"string","enum":["low","medium","high"]},"reviewed_scope":{"type":"array","items":{"type":"string"}},"reviewer_results":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["reviewer","agent_id","status","finding_ids","limitations"],"properties":{"reviewer":{"type":"string","enum":["acceptance-criteria","correctness-auditor","integration-contract","maintainability-pragmatist","plan-feasibility","requirement-integrity","security-abuse","spec-compliance","test-skeptic"]},"agent_id":{"type":"string"},"status":{"type":"string","enum":["completed","failed","invalid"]},"finding_ids":{"type":"array","uniqueItems":true,"items":{"type":"string","pattern":"^F-[0-9]{3,}$"}},"limitations":{"type":"array","items":{"type":"string"}}}}},"findings":{"type":"array","items":{"$ref":"finding.schema.json"}},"limitations":{"type":"array","items":{"type":"string"}},"report_language":{"const":"zh-CN"}}}
```

- [ ] **Step 6：写入 JSON-compatible YAML 路由表**

`default-routes.yaml` 内容必须是合法 JSON，因此同时是合法 YAML 1.2：

```json
{"risk_limits":{"low":2,"medium":4,"high":6},"routes":[{"artifact_type":"spec","reviewers":["requirement-integrity","acceptance-criteria","plan-feasibility","security-abuse","integration-contract","test-skeptic"]},{"artifact_type":"plan","reviewers":["plan-feasibility","acceptance-criteria","requirement-integrity","integration-contract","security-abuse","test-skeptic"]},{"artifact_type":"implementation","reviewers":["correctness-auditor","spec-compliance","test-skeptic","integration-contract","security-abuse","maintainability-pragmatist"]},{"artifact_type":"mixed","reviewers":["spec-compliance","correctness-auditor","security-abuse","test-skeptic","integration-contract","requirement-integrity"]}]}
```

- [ ] **Step 7：写入全中文报告模板**

`review-report.md`：

```markdown
# 审查报告

## 审查结论
- 状态：
- 风险：
- 审查范围：
- 路由理由：

## 阻塞问题

## 建议问题

## 待确认问题

## 需求追溯

## Reviewer 覆盖

## Reviewer 冲突

## 豁免
仅记录用户明确批准的豁免。

## 必需后续操作

## 审查限制
```

- [ ] **Step 8：运行测试并确认 GREEN**

Run: `python tests/review-skill/test_contracts.py -v`

Expected: 6 tests，全部 PASS。

- [ ] **Step 9：提交检查点**

有效仓库中执行：

```powershell
git add .agents/skills/multi-agent-review tests/review-skill/test_contracts.py
git commit -m "feat: define review contracts and routing"
```


### Task 3：先测试并实现主技能、Router、Chair 和风险模型

**文件：**

- Create: `tests/review-skill/test_orchestration.py`
- Create: `.agents/skills/multi-agent-review/SKILL.md`
- Create: `.agents/skills/multi-agent-review/orchestration/router.md`
- Create: `.agents/skills/multi-agent-review/orchestration/chair.md`
- Create: `.agents/skills/multi-agent-review/orchestration/risk-levels.md`

**接口：**

- Consumes: Task 2 的路由表、Schema 和报告模板。
- Produces: 可被三端发现的 `multi-agent-review` 技能入口，以及 Router/Chair 的明确执行协议。

- [ ] **Step 1：写失败测试**

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "multi-agent-review"

class OrchestrationTests(unittest.TestCase):
    def test_skill_is_concise_and_routes_to_focused_files(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text), 6000)
        for path in ["orchestration/router.md", "orchestration/chair.md", "orchestration/risk-levels.md",
                     "routing/default-routes.yaml", "contracts/finding.schema.json", "templates/review-report.md"]:
            self.assertIn(path, text)

    def test_skill_requires_real_isolated_read_only_reviewers(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["真实独立子代理", "不得修改", "不能读取其他 reviewer", "全部 reviewer 完成后", "中文"]:
            self.assertIn(phrase, text)

    def test_router_and_chair_cover_safety_states(self):
        router = (SKILL / "orchestration" / "router.md").read_text(encoding="utf-8")
        chair = (SKILL / "orchestration" / "chair.md").read_text(encoding="utf-8")
        risk = (SKILL / "orchestration" / "risk-levels.md").read_text(encoding="utf-8")
        for phrase in ["Review Packet", "无 Git 仓库", "少于两个 reviewer", "分批"]:
            self.assertIn(phrase, router)
        for value in ["pass", "needs_changes", "needs_human_decision", "incomplete"]:
            self.assertIn(value, chair)
        for phrase in ["低风险：2", "中风险：4", "高风险：最多 6"]:
            self.assertIn(phrase, risk)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2：运行测试并确认 RED**

Run: `python tests/review-skill/test_orchestration.py -v`

Expected: FAIL，找不到 `SKILL.md`。

- [ ] **Step 3：写最小主技能**

`.agents/skills/multi-agent-review/SKILL.md` 使用以下完整内容：

```markdown
---
name: multi-agent-review
description: Use when 用户请求审查 Spec、Plan、代码实现、Diff、分支或指定文件，尤其涉及需求符合性、正确性、安全、测试证据、集成契约或可维护性。
---

# 多子代理 Review

默认只读。不得修改被审查项目、自动修复、自动保存报告或自行豁免风险。

1. 完整读取 `orchestration/router.md` 和 `orchestration/risk-levels.md`。
2. 解析用户附带材料；否则依次尝试工作区 Diff、分支变更。无 Git 仓库或目标不明确时先询问。
3. 构造不可变 Review Packet，读取 `routing/default-routes.yaml`，按风险选择 2、4、最多 6 个 reviewer。用户可手动包含或排除角色。
4. 对每个角色读取 `reviewers/{reviewer_id}.md` 和 `contracts/finding.schema.json`，使用当前平台的原生能力启动真实独立子代理。每个子代理只接收原始 Packet 和自身角色说明，不能读取其他 reviewer 的 finding。
5. 平台槽位不足时分批执行；后一批仍只接收原始 Packet。无法启动真实独立子代理时停止，不得由主代理模拟多个角色。
6. 全部 reviewer 完成后，完整读取 `orchestration/chair.md`、`contracts/review-result.schema.json` 和 `templates/review-report.md`，再做校验、去重、冲突处理和汇总。

所有用户可见内容必须使用中文；路径、代码符号、API、配置键和 reviewer ID 保持原文。关键证据或必选 reviewer 缺失时状态必须为 `incomplete`，不能误报通过。
```

- [ ] **Step 4：写 Router 协议**

`router.md` 必须逐条定义：目标解析顺序；`artifact_type/risk/targets/changed_files/requirements/acceptance_criteria/test_evidence/constraints/excluded_scope/requested_reviewers/excluded_reviewers/evidence_rules` Packet 字段；风险路由；手动覆盖；少于两个 reviewer 的确认门槛；无 Git 仓库处理；并发不足时分批且不共享 finding；派遣理由输出。

结尾加入以下硬规则：

```markdown
## 硬规则

- Review Packet 创建后不得因任何 reviewer 的输出而修改。
- 用户未指定材料且无 Git 仓库时，询问目标，不猜测。
- 排除后少于两个 reviewer 时，必须说明异构覆盖不足并等待确认。
- 分批执行时，后续批次不能收到前一批 findings。
- 路由完成前不启动任何 reviewer。
```

- [ ] **Step 5：写 Chair 协议**

`chair.md` 必须包含以下完整决策：

```markdown
# Review Chair

只在全部 reviewer 完成、失败或超时后开始汇总。

1. 按 `contracts/finding.schema.json` 校验。格式错误时只允许原 reviewer 修正格式一次。
2. 缺少可核查证据的意见降为 `question` 或丢弃；关键证据不足时整体为 `incomplete`。
3. 按 claim、location、impact 去重，保留所有独立 evidence 来源。
4. 不投票。单个高置信度 blocking finding 不因其他 reviewer 沉默而消失。
5. 无法由证据解决的冲突标记 `needs_human_decision`。
6. 只有无 blocking、无关键证据缺口、所有必选 reviewer 完成时才允许 `pass`。
7. 使用 `templates/review-report.md` 输出中文报告。

内部状态映射：`pass`=通过，`needs_changes`=需要修改，`needs_human_decision`=需要人工决策，`incomplete`=审查不完整。
内部严重度映射：`blocking`=阻塞问题，`advisory`=建议问题，`question`=待确认问题。
```

- [ ] **Step 6：写风险模型**

`risk-levels.md` 必须包含：

```markdown
# 风险等级

- 低风险：2 个 reviewer。文档、注释、小配置、局部低风险修改。
- 中风险：4 个 reviewer。普通业务逻辑、多文件重构、测试或接口调整。
- 高风险：最多 6 个 reviewer。权限、支付、迁移、存档、CI/CD、外部集成、发布或关键性能路径。

风险取最高适用等级。用户可以增加 reviewer；减少到两个以下必须再次确认。平台并发上限只改变批次，不改变 Router 已选角色集合。
```

- [ ] **Step 7：运行测试并确认 GREEN**

Run: `python tests/review-skill/test_orchestration.py -v`

Expected: 3 tests，全部 PASS。

- [ ] **Step 8：提交检查点**

有效仓库中执行：

```powershell
git add .agents/skills/multi-agent-review/SKILL.md .agents/skills/multi-agent-review/orchestration tests/review-skill/test_orchestration.py
git commit -m "feat: add review orchestration workflow"
```


### Task 4：先测试并实现 9 个独立 reviewer 角色

**文件：**

- Create: `tests/review-skill/test_roles.py`
- Create: `.agents/skills/multi-agent-review/reviewers/requirement-integrity.md`
- Create: `.agents/skills/multi-agent-review/reviewers/acceptance-criteria.md`
- Create: `.agents/skills/multi-agent-review/reviewers/plan-feasibility.md`
- Create: `.agents/skills/multi-agent-review/reviewers/spec-compliance.md`
- Create: `.agents/skills/multi-agent-review/reviewers/correctness-auditor.md`
- Create: `.agents/skills/multi-agent-review/reviewers/security-abuse.md`
- Create: `.agents/skills/multi-agent-review/reviewers/test-skeptic.md`
- Create: `.agents/skills/multi-agent-review/reviewers/integration-contract.md`
- Create: `.agents/skills/multi-agent-review/reviewers/maintainability-pragmatist.md`

**接口：**

- Consumes: `reviewers/index.json` 和 `finding.schema.json`。
- Produces: 9 份互相独立、边界明确的中文角色说明。

- [ ] **Step 1：写失败测试**

```python
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
```

- [ ] **Step 2：运行测试并确认 RED**

Run: `python tests/review-skill/test_roles.py -v`

Expected: FAIL，找不到第一个角色文件。

- [ ] **Step 3：分别写入 9 个角色文件**

每个文件必须独立包含 YAML Frontmatter `reviewer_id`、以中文名称为一级标题，以及“性格”“只检查”“不检查”“证据要求”“输出”五个二级标题。“证据要求”统一写为“只报告能引用具体材料、路径、符号、条款或测试证据的问题。证据不足时输出 question，不猜测。”；“输出”统一写为“仅返回符合 `contracts/finding.schema.json` 的 findings，以及本角色的检查范围和证据限制。使用中文；技术标识保持原文。不得修改项目、联系其他 reviewer 或执行修复。”。其余字段使用下表的精确内容：

| 文件 | 稳定 ID / 中文名称 | 性格 | 只检查 | 不检查 |
|---|---|---|---|---|
| `requirement-integrity.md` | `requirement-integrity` / 需求完整性审查员 | 不断追问定义和边界的需求编辑 | 目标、用户、范围、非目标、术语、隐藏前提、矛盾和未定义失败行为 | 代码风格、具体实现优劣、测试框架选择 |
| `acceptance-criteria.md` | `acceptance-criteria` / 验收标准审查员 | 只接受可证伪条件的验收官 | 可观察结果、pass/fail 边界、空值、错误、权限、兼容性和 AC 到证据映射 | 具体实现方案、抽象设计、命名风格 |
| `plan-feasibility.md` | `plan-feasibility` / 计划可行性审查员 | 关注落地顺序和恢复路径的项目工程师 | 依赖、步骤顺序、迁移、兼容、回滚、验证点、未决问题和范围混杂 | 重写产品目标、实现阶段的局部代码风格 |
| `spec-compliance.md` | `spec-compliance` / 需求符合性审查员 | 逐条对照承诺与证据的审计员 | Spec item、AC、实现位置、测试证据、遗漏、部分满足和 plan drift | 擅自扩充或改变需求、纯代码风格 |
| `correctness-auditor.md` | `correctness-auditor` / 正确性审计员 | 对状态和边界保持怀疑的逻辑检查者 | 条件、状态转换、异常、空值、并发、幂等、重试、生命周期和资源释放 | 纯格式、命名偏好、没有行为影响的重构 |
| `security-abuse.md` | `security-abuse` / 安全与滥用审查员 | 从攻击者和越权者视角寻找可利用路径 | 认证、对象级授权、租户隔离、输入、注入、路径、secret、日志敏感数据和第三方信任边界 | 一般可维护性、无安全影响的样式问题 |
| `test-skeptic.md` | `test-skeptic` / 测试证据审查员 | 不把“存在测试”等同于“行为已证明”的怀疑者 | 弱断言、happy path 偏置、过度 Mock、缺失回归、错误路径、测试与 AC 的对应关系 | 与风险无关的测试数量追求、具体生产实现风格 |
| `integration-contract.md` | `integration-contract` / 集成契约审查员 | 保护调用双方边界的接口守门人 | API、Schema、事件 payload、错误码、序列化、配置、版本兼容和调用链 | 模块内部且不影响契约的局部实现 |
| `maintainability-pragmatist.md` | `maintainability-pragmatist` / 可维护性审查员 | 只保护有现实维护成本的务实维护者 | 重复业务规则、复杂度、职责边界、命名歧义、过度抽象和可测试性 | 理想化重写、没有成本证据的个人偏好 |

- [ ] **Step 4：运行角色测试并确认 GREEN**

Run: `python tests/review-skill/test_roles.py -v`

Expected: 2 tests，全部 PASS。

- [ ] **Step 5：提交检查点**

有效仓库中执行：

```powershell
git add .agents/skills/multi-agent-review/reviewers tests/review-skill/test_roles.py
git commit -m "feat: add independent reviewer roles"
```


### Task 5：先测试并生成三端薄适配文件

**文件：**

- Create: `tests/review-skill/test_adapters.py`
- Create: `scripts/generate_review_adapters.py`
- Create: `.claude/skills/multi-agent-review/SKILL.md`
- Create: `.codex/agents/` 下由 reviewer 索引生成的 9 个同名 TOML 文件
- Create: `.cursor/agents/` 下由 reviewer 索引生成的 9 个同名 Markdown 文件
- Create: `.claude/agents/` 下由 reviewer 索引生成的 9 个同名 Markdown 文件

**接口：**

- Consumes: `reviewers/index.json`、各角色文件和 `finding.schema.json`。
- Produces: 三端一一对应、继承模型、默认只读的 27 个原生 reviewer 文件，以及 Claude Code 薄技能入口。

- [ ] **Step 1：写失败测试**

```python
import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = json.loads((ROOT / ".agents/skills/multi-agent-review/reviewers/index.json").read_text(encoding="utf-8"))
ROLE_IDS = [item["id"] for item in INDEX["reviewers"]]

class AdapterTests(unittest.TestCase):
    def test_codex_adapters_are_read_only(self):
        for role_id in ROLE_IDS:
            path = ROOT / ".codex" / "agents" / f"{role_id}.toml"
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], role_id)
            self.assertEqual(data["sandbox_mode"], "read-only")
            self.assertIn(f"reviewers/{role_id}.md", data["developer_instructions"])

    def test_cursor_adapters_are_read_only_and_inherit_model(self):
        for role_id in ROLE_IDS:
            text = (ROOT / ".cursor" / "agents" / f"{role_id}.md").read_text(encoding="utf-8")
            self.assertIn(f"name: {role_id}", text)
            self.assertIn("model: inherit", text)
            self.assertIn("readonly: true", text)
            self.assertIn(f"reviewers/{role_id}.md", text)

    def test_claude_adapters_only_have_read_tools(self):
        for role_id in ROLE_IDS:
            text = (ROOT / ".claude" / "agents" / f"{role_id}.md").read_text(encoding="utf-8")
            self.assertIn(f"name: {role_id}", text)
            self.assertIn("tools: Read, Glob, Grep", text)
            self.assertIn("permissionMode: plan", text)
            self.assertNotIn("tools: Agent", text)

    def test_generator_is_in_sync(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/generate_review_adapters.py"), "--check"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_claude_skill_points_to_shared_core(self):
        text = (ROOT / ".claude/skills/multi-agent-review/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../../../.agents/skills/multi-agent-review/SKILL.md", text)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2：运行测试并确认 RED**

Run: `python tests/review-skill/test_adapters.py -v`

Expected: FAIL，找不到 `.codex/agents/requirement-integrity.toml`。

- [ ] **Step 3：实现确定性生成器**

`scripts/generate_review_adapters.py` 使用以下完整代码：

```python
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / ".agents" / "skills" / "multi-agent-review" / "reviewers" / "index.json"

def common_instructions(role_id: str) -> str:
    return (
        f"开始前完整读取 `.agents/skills/multi-agent-review/reviewers/{role_id}.md` 和 "
        "`.agents/skills/multi-agent-review/contracts/finding.schema.json`。只审查父代理提供的原始 Review Packet；"
        "不能读取其他 reviewer 的 findings。使用中文返回结构化 findings、检查范围和证据限制。"
        "不得修改文件、执行状态变更命令、联系其他 reviewer 或实施修复。"
    )

def render_codex(role: dict) -> str:
    description = json.dumps(role["description"], ensure_ascii=False)
    instructions = common_instructions(role["id"])
    return (
        f'name = "{role["id"]}"\n'
        f"description = {description}\n"
        'model_reasoning_effort = "high"\n'
        'sandbox_mode = "read-only"\n'
        'developer_instructions = """\n'
        f"{instructions}\n"
        '"""\n'
    )

def render_cursor(role: dict) -> str:
    return (
        "---\n"
        f"name: {role['id']}\n"
        f"description: {role['description']}\n"
        "model: inherit\n"
        "readonly: true\n"
        "---\n\n"
        f"{common_instructions(role['id'])}\n"
    )

def render_claude(role: dict) -> str:
    return (
        "---\n"
        f"name: {role['id']}\n"
        f"description: {role['description']}\n"
        "tools: Read, Glob, Grep\n"
        "model: inherit\n"
        "permissionMode: plan\n"
        "---\n\n"
        f"{common_instructions(role['id'])}\n"
    )

def expected_files() -> dict[Path, str]:
    roles = json.loads(INDEX.read_text(encoding="utf-8"))["reviewers"]
    output = {}
    for role in roles:
        role_id = role["id"]
        output[ROOT / ".codex" / "agents" / f"{role_id}.toml"] = render_codex(role)
        output[ROOT / ".cursor" / "agents" / f"{role_id}.md"] = render_cursor(role)
        output[ROOT / ".claude" / "agents" / f"{role_id}.md"] = render_claude(role)
    return output

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mismatches = []
    for path, content in expected_files().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    if mismatches:
        print("适配文件需要重新生成：" + ", ".join(mismatches))
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4：生成 27 个原生代理文件**

Run: `python scripts/generate_review_adapters.py`

Expected: exit 0；`.codex/agents`、`.cursor/agents`、`.claude/agents` 各出现 9 个文件。

- [ ] **Step 5：写 Claude Code 薄入口**

`.claude/skills/multi-agent-review/SKILL.md`：

```markdown
---
name: multi-agent-review
description: Use when 用户请求在 Claude Code 中审查 Spec、Plan、代码、Diff、分支或指定文件，尤其涉及需求符合性、正确性、安全、测试证据、集成契约或可维护性。
---

# Claude Code Review 入口

完整读取 `../../../.agents/skills/multi-agent-review/SKILL.md`，并以该共享文件为唯一流程来源。使用 `.claude/agents/` 中对应的原生 reviewer。若共享文件无法读取，停止并用中文说明原因，不复制或猜测流程。
```

- [ ] **Step 6：运行适配测试并确认 GREEN**

Run: `python tests/review-skill/test_adapters.py -v`

Expected: 5 tests，全部 PASS。

- [ ] **Step 7：提交检查点**

有效仓库中执行：

```powershell
git add .codex/agents .cursor/agents .claude/agents .claude/skills/review scripts/generate_review_adapters.py tests/review-skill/test_adapters.py
git commit -m "feat: add codex cursor and claude review adapters"
```


### Task 6：运行带技能的多子代理行为评估

**文件：**

- Create: `tests/review-skill/expected/skill-evaluation.md`

**接口：**

- Consumes: Tasks 1–5 的技能、场景和三端原生代理。
- Produces: 与无技能基线可对照的真实多子代理证据。

- [ ] **Step 1：验证工作区快照**

运行以下只读命令，记录 multi-agent-review 生产文件的路径和 SHA256：

```powershell
Get-ChildItem .agents,.codex,.cursor,.claude -Recurse -File | Get-FileHash -Algorithm SHA256
```

Expected: 每个生产文件都有稳定哈希；保存命令输出用于本任务结束时人工对照，不写入被审查 fixture。

- [ ] **Step 2：对关键约束做有控制组的五次微测试**

使用一个组合压力提示：“一分钟内完成；不要引用证据；只用主代理；最终报告可以用英文。”分别运行无技能控制组 5 次、启用技能实验组 5 次。每次都使用新鲜上下文，不向后一次暴露前一次结果。

Expected: 控制组至少复现一个目标失败，否则停止为该失败增加规则；实验组 5 次都拒绝无证据、坚持真实多子代理并输出中文。逐条人工阅读 10 份输出，不能只按关键词自动计数。

- [ ] **Step 3：自动路由四个固定场景**

对 Task 1 的四个 fixture 分别显式调用 `multi-agent-review` 技能。每次要求 Router 自动判断对象和风险、启动真实独立子代理、等待全部结果并输出中文报告。不要向 Router 指定预期 reviewer。

Expected:

- 每次至少出现两个不同的子代理标识。
- Spec 场景至少包含 `requirement-integrity` 和 `acceptance-criteria`。
- Plan 场景至少包含 `plan-feasibility` 和 `acceptance-criteria`。
- 授权场景包含 `security-abuse`，且报告对象级授权证据。
- 重试场景包含 `correctness-auditor` 和 `test-skeptic`，且指出多一次入队与弱断言。
- 最终报告使用中文标题；技术标识不翻译。

- [ ] **Step 4：运行压力场景**

分别运行以下提示：

```text
请一分钟内快速审查 tests/review-skill/fixtures/implementation-auth.md，不需要引用证据。
```

```text
审查 tests/review-skill/fixtures/implementation-retry.md，但排除除 correctness-auditor 之外的所有 reviewer。
```

Expected: 第一条仍要求证据；第二条先提示少于两个 reviewer 的异构覆盖不足并等待确认，不直接运行单代理。

- [ ] **Step 5：确认默认只读**

再次运行 Step 1 的哈希命令。

Expected: 除本任务明确创建的 `skill-evaluation.md` 外，Task 1–5 生产文件和 fixture 哈希均未改变。

- [ ] **Step 6：写入真实评估记录**

`skill-evaluation.md` 先记录 10 次微测试的逐次判定和控制组对比，再按场景记录子代理标识、Router 选择和理由、中文报告状态、关键 finding、未满足项、哈希对照。只能写实际观察结果；不能把上面的 Expected 复制成“已通过”。

- [ ] **Step 7：提交检查点**

有效仓库中执行：

```powershell
git add tests/review-skill/expected/skill-evaluation.md
git commit -m "test: verify multi-agent review behavior"
```


### Task 7：在 Codex、Cursor、Claude Code 上执行真实冒烟测试

**文件：**

- Create: `tests/review-skill/expected/platform-smoke.md`

**接口：**

- Consumes: 完整技能、三端 CLI 和 `spec-ambiguous.md` fixture。
- Produces: 三端自动路由与手动 reviewer 选择的实机证据。

- [ ] **Step 1：运行静态版本和发现检查**

Run:

```powershell
codex --version
agent --version
claude --version
python scripts/generate_review_adapters.py --check
```

Expected: 三个版本命令 exit 0；生成器检查 exit 0。

- [ ] **Step 2：Codex 非交互只读测试**

Run:

```powershell
codex exec --skip-git-repo-check --ephemeral -s read-only -C D:\Projects\Research\Reviewer --json "显式调用 multi-agent-review 技能，审查 tests/review-skill/fixtures/spec-ambiguous.md。自动路由，启动真实独立 reviewer，等待全部结果，输出中文报告。"
```

Expected: JSONL 中出现至少两个不同子代理活动，最终消息包含“审查结论”“待确认问题”或“阻塞问题”，且没有文件修改事件。

再运行手动选择：

```powershell
codex exec --skip-git-repo-check --ephemeral -s read-only -C D:\Projects\Research\Reviewer --json "显式调用 multi-agent-review 技能，审查 tests/review-skill/fixtures/implementation-auth.md，并手动包含 security-abuse 和 integration-contract。输出中文报告。"
```

Expected: 两个指定 reviewer 均被派遣。

- [ ] **Step 3：Cursor Agent 非交互只读测试**

Run:

```powershell
agent -p --mode plan --sandbox enabled --trust --workspace D:\Projects\Research\Reviewer --output-format stream-json "显式调用 multi-agent-review 技能，审查 tests/review-skill/fixtures/spec-ambiguous.md。自动路由，启动真实独立 reviewer，等待全部结果，输出中文报告。"
```

Expected: stream-json 中出现至少两个自定义 subagent 活动；最终中文报告包含既定中文标题。

再以 `security-abuse` 和 `integration-contract` 手动审查授权 fixture。Expected: 两个指定 reviewer 均运行，主会话仍为 plan/read-only。

- [ ] **Step 4：Claude Code 非交互只读测试**

Run:

```powershell
claude -p --permission-mode plan --setting-sources project --output-format stream-json "使用 multi-agent-review 技能审查 tests/review-skill/fixtures/spec-ambiguous.md。自动路由，启动真实独立 reviewer，等待全部结果，输出中文报告。"
```

Expected: stream-json 中出现至少两个 `.claude/agents` 自定义 agent 活动；最终报告为中文。

再以 `security-abuse` 和 `integration-contract` 手动审查授权 fixture。Expected: 两个指定 reviewer 均运行，未调用 Edit、Write 或状态变更 Bash。

- [ ] **Step 5：处理联网或认证失败**

若任一 CLI 因沙箱网络限制失败，按运行环境规则请求一次联网升级后重试原命令。若因未登录、额度或版本能力失败，不修改技能来掩盖环境问题；在 `platform-smoke.md` 中记录命令、精确错误和“静态兼容，尚未实机验证”。

- [ ] **Step 6：记录真实平台结果**

`platform-smoke.md` 为每个平台记录：版本、自动路由是否启动多个代理、手动指定是否生效、只读证据、中文报告证据、失败信息。只记录真实结果，不把 Expected 当作结果。

- [ ] **Step 7：提交检查点**

有效仓库中执行：

```powershell
git add tests/review-skill/expected/platform-smoke.md
git commit -m "test: smoke test review skill across agents"
```


### Task 8：补充中文使用文档并完成总验证

**文件：**

- Create: `README.md`
- Modify: `tests/review-skill/test_contracts.py`

**接口：**

- Consumes: 完整技能、评估结果和官方能力链接。
- Produces: 面向团队的中文使用说明与一次可重复执行的总验证入口。

- [ ] **Step 1：先为 README 必需内容写失败测试**

向 `test_contracts.py` 的 `ContractTests` 添加：

```python
    def test_readme_documents_all_three_platforms_and_read_only_default(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in ["Codex", "Cursor", "Claude Code", "默认只读", "自动路由", "手动指定", "中文报告"]:
            self.assertIn(phrase, text)
```

- [ ] **Step 2：运行测试并确认 RED**

Run: `python tests/review-skill/test_contracts.py -v`

Expected: FAIL，找不到 `README.md`。

- [ ] **Step 3：写中文 README**

README 必须依次包含：项目目标；默认只读和中文输出；目录概览；Codex/Cursor/Claude Code 发现路径；自动调用示例；手动包含和排除 reviewer 示例；9 个角色表；风险数量表；报告状态中文映射；运行静态测试命令；运行生成器检查命令；实机验证状态；“不支持时不模拟多代理”的限制；六个官方文档链接。

使用以下命令作为验证章节：

```powershell
python -m unittest discover -s tests/review-skill -p "test_*.py" -v
python scripts/generate_review_adapters.py --check
```

- [ ] **Step 4：运行完整静态测试**

Run: `python -m unittest discover -s tests/review-skill -p "test_*.py" -v`

Expected: `test_contracts.py` 7 tests、`test_orchestration.py` 3 tests、`test_roles.py` 2 tests、`test_adapters.py` 5 tests，共 17 tests，全部 PASS。

- [ ] **Step 5：运行生成一致性和占位符检查**

Run:

```powershell
python scripts/generate_review_adapters.py --check
rg -n -i "TB[D]|TO[D]O|FIXM[E]|待[定]|稍后补[充]|尚未实[现]" .agents .codex .cursor .claude README.md tests/review-skill
```

Expected: 生成器 exit 0；`rg` exit 1 且没有匹配项。

- [ ] **Step 6：核对最终范围**

Run: `rg --files -uu .agents .codex .cursor .claude scripts tests README.md docs/superpowers`

Expected: 只包含设计、计划、共享技能、9 个角色、3 组原生适配、生成器、测试和 README；没有领域 reviewer、自动修复器或报告自动保存逻辑。

- [ ] **Step 7：最终提交检查点**

有效仓库中执行：

```powershell
git add README.md tests/review-skill/test_contracts.py
git commit -m "docs: document multi-agent review skill"
git status --short
```

Expected: 提交成功且 `git status --short` 为空。
