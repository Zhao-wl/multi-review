"""Build the installable multi-review plugin from the shared review core.

The source of truth remains .agents/skills/multi-agent-review.  This script
creates the committed marketplace artifact under plugins/multi-review so the
three hosts always receive identical review contracts and orchestration rules.
"""

import argparse
import filecmp
import json
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILL = ROOT / ".agents" / "skills" / "multi-agent-review"
PACKAGE_NAME = "multi-review"
PACKAGE_VERSION = "0.1.2"
PACKAGE_ROOT = ROOT / "plugins" / PACKAGE_NAME
REPOSITORY = "https://github.com/Zhao-wl/multi-review"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def manifest_base() -> dict:
    return {
        "name": PACKAGE_NAME,
        "version": PACKAGE_VERSION,
        "description": "由独立子代理执行的结构化多角色审查工作流。",
        "author": {"name": "Zhao-wl", "url": "https://github.com/Zhao-wl"},
        "homepage": f"{REPOSITORY}#readme",
        "repository": REPOSITORY,
        "keywords": ["code-review", "spec-review", "multi-agent", "quality"],
    }


def role_agent(role: dict) -> str:
    return f"""---
name: {role['id']}
description: {role['description']}
model: inherit
readonly: true
tools: Read, Glob, Grep
permissionMode: plan
---

这是 `multi-review` 插件的只读 reviewer。开始前在已安装插件的
`skills/multi-agent-review/` 下完整读取 `reviewers/{role['id']}.md`、
`contracts/reviewer-output.schema.json` 和 `contracts/finding.schema.json`。
只审查父代理提供的原始 Review Packet；不能读取其他 reviewer 的 findings。
使用中文返回符合 reviewer-output Schema 的单个 Envelope，包含 review_id、
reviewer、findings、reviewed_scope、limitations、report_language。不得修改文件、
执行状态变更命令、联系其他 reviewer、派生子代理或实施修复。
"""


def plugin_readme() -> str:
    return """# Multi Review

`multi-review` 是一个结构化多角色审查插件。它针对 Spec、Plan、代码实现、Diff 与分支变更，按风险选择相互隔离的只读 reviewer，并以统一的 Review Packet、Schema 与汇总规则生成中文审查结论。

插件包含需求、验收、可行性、符合性、正确性、安全、测试、集成和可维护性等审查角色。审查流程只输出证据化结果，不自动修改被审查项目。

## 安装

```text
claude plugin marketplace add Zhao-wl/multi-review
claude plugin install multi-review@multi-review

codex plugin marketplace add Zhao-wl/multi-review
codex plugin add multi-review@multi-review
```
"""


def build(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    shutil.copytree(
        SOURCE_SKILL,
        destination / "skills" / "multi-agent-review",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    roles = json.loads(
        (SOURCE_SKILL / "reviewers" / "index.json").read_text(encoding="utf-8")
    )["reviewers"]
    for role in roles:
        path = destination / "agents" / f"{role['id']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(role_agent(role), encoding="utf-8", newline="\n")

    claude = manifest_base()
    # Claude Code discovers plugin component directories automatically. Its
    # manifest validator rejects an explicit `agents` field.
    claude.update({"skills": "./skills/"})
    write_json(destination / ".claude-plugin" / "plugin.json", claude)

    codex = manifest_base()
    codex.update(
        {
            "skills": "./skills/",
            "interface": {
                "displayName": "Multi Review",
                "shortDescription": "结构化多角色只读审查",
                "longDescription": "使用隔离 reviewer 审查 Spec、Plan、实现和 Diff。",
                "developerName": "Zhao-wl",
                "category": "Productivity",
                "capabilities": ["Interactive"],
                "websiteURL": f"{REPOSITORY}#readme",
                "defaultPrompt": [
                    "使用 multi-agent-review 审查当前分支的改动。",
                    "使用 multi-agent-review 审查这个实现是否符合 Spec。",
                ],
                "brandColor": "#2563EB",
            },
        }
    )
    write_json(destination / ".codex-plugin" / "plugin.json", codex)

    (destination / "README.md").write_text(plugin_readme(), encoding="utf-8", newline="\n")


def same_tree(expected: Path, actual: Path) -> bool:
    comparison = filecmp.dircmp(expected, actual)
    if comparison.left_only or comparison.right_only or comparison.diff_files:
        return False
    return all(same_tree(expected / name, actual / name) for name in comparison.common_dirs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not SOURCE_SKILL.is_dir():
        raise SystemExit(f"共享技能不存在：{SOURCE_SKILL}")
    if not args.check:
        build(PACKAGE_ROOT)
        return 0

    if not PACKAGE_ROOT.is_dir():
        print("市场插件尚未构建：plugins/multi-review")
        return 1
    with tempfile.TemporaryDirectory() as temporary:
        expected = Path(temporary) / PACKAGE_NAME
        build(expected)
        if not same_tree(expected, PACKAGE_ROOT):
            print("市场插件已漂移，请运行：python scripts/build_marketplace_plugin.py")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
