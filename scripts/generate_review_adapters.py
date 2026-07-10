import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (
    ROOT
    / ".agents"
    / "skills"
    / "multi-agent-review"
    / "reviewers"
    / "index.json"
)
TARGETS = (
    (ROOT / ".codex" / "agents", ".toml"),
    (ROOT / ".cursor" / "agents", ".md"),
    (ROOT / ".claude" / "agents", ".md"),
)


def common_instructions(role_id: str) -> str:
    return (
        f"开始前完整读取 `.agents/skills/multi-agent-review/reviewers/{role_id}.md`、"
        "`.agents/skills/multi-agent-review/contracts/reviewer-output.schema.json` 和 "
        "`.agents/skills/multi-agent-review/contracts/finding.schema.json`。只审查父代理提供的原始 Review Packet；"
        "不能读取其他 reviewer 的 findings。使用中文返回符合 reviewer-output Schema 的单个 Envelope，"
        "包含 review_id、reviewer、findings、reviewed_scope、limitations、report_language。"
        "不得修改文件、执行状态变更命令、联系其他 reviewer、不得派生子代理或实施修复。"
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
        output[ROOT / ".codex" / "agents" / f"{role_id}.toml"] = render_codex(
            role
        )
        output[ROOT / ".cursor" / "agents" / f"{role_id}.md"] = render_cursor(
            role
        )
        output[ROOT / ".claude" / "agents" / f"{role_id}.md"] = render_claude(
            role
        )
    return output


def extra_files(expected: set[Path]) -> list[Path]:
    extras = []
    for directory, suffix in TARGETS:
        if directory.exists():
            extras.extend(
                path
                for path in directory.glob(f"*{suffix}")
                if path not in expected
            )
    return sorted(extras)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    files = expected_files()
    mismatches = []
    for path, content in files.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                mismatches.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")

    if args.check:
        mismatches.extend(extra_files(set(files)))
    if mismatches:
        relative_paths = ", ".join(
            str(path.relative_to(ROOT)) for path in sorted(mismatches)
        )
        print("适配文件需要重新生成：" + relative_paths)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
