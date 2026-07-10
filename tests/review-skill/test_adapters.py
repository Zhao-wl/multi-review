import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = json.loads(
    (
        ROOT
        / ".agents"
        / "skills"
        / "multi-agent-review"
        / "reviewers"
        / "index.json"
    ).read_text(encoding="utf-8")
)
ROLE_IDS = [item["id"] for item in INDEX["reviewers"]]
ROLE_ID_SET = set(ROLE_IDS)
GENERATOR = ROOT / "scripts" / "generate_review_adapters.py"
ROLE_ROOT = ".agents/skills/multi-agent-review"


def adapter_names(directory: Path, suffix: str) -> set[str]:
    return {path.stem for path in directory.glob(f"*{suffix}")}


def run_generator_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


class AdapterTests(unittest.TestCase):
    def test_1_codex_adapters_are_exactly_indexed_and_read_only(self):
        directory = ROOT / ".codex" / "agents"
        for role_id in ROLE_IDS:
            path = directory / f"{role_id}.toml"
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], role_id)
            self.assertEqual(data["sandbox_mode"], "read-only")
            self.assertNotIn("model", data)
            instructions = data["developer_instructions"]
            self.assertIn(f"{ROLE_ROOT}/reviewers/{role_id}.md", instructions)
            self.assertIn(
                f"{ROLE_ROOT}/contracts/reviewer-output.schema.json", instructions
            )
            self.assertIn(f"{ROLE_ROOT}/contracts/finding.schema.json", instructions)
            self.assertIn("不得派生子代理", instructions)
        self.assertEqual(adapter_names(directory, ".toml"), ROLE_ID_SET)

    def test_2_cursor_adapters_are_exactly_indexed_read_only_and_inherit_model(self):
        directory = ROOT / ".cursor" / "agents"
        self.assertEqual(adapter_names(directory, ".md"), ROLE_ID_SET)
        for role_id in ROLE_IDS:
            text = (directory / f"{role_id}.md").read_text(encoding="utf-8")
            self.assertIn(f"name: {role_id}", text)
            self.assertIn("model: inherit", text)
            self.assertIn("readonly: true", text)
            self.assertIn(f"{ROLE_ROOT}/reviewers/{role_id}.md", text)
            self.assertIn(f"{ROLE_ROOT}/contracts/reviewer-output.schema.json", text)
            self.assertIn(f"{ROLE_ROOT}/contracts/finding.schema.json", text)
            self.assertIn("不得派生子代理", text)
            self.assertNotIn("tools: Agent", text)

    def test_3_claude_adapters_are_exactly_indexed_and_only_have_read_tools(self):
        directory = ROOT / ".claude" / "agents"
        self.assertEqual(adapter_names(directory, ".md"), ROLE_ID_SET)
        for role_id in ROLE_IDS:
            text = (directory / f"{role_id}.md").read_text(encoding="utf-8")
            self.assertIn(f"name: {role_id}", text)
            self.assertIn("tools: Read, Glob, Grep", text)
            self.assertIn("model: inherit", text)
            self.assertIn("permissionMode: plan", text)
            self.assertIn(f"{ROLE_ROOT}/reviewers/{role_id}.md", text)
            self.assertIn(f"{ROLE_ROOT}/contracts/reviewer-output.schema.json", text)
            self.assertIn(f"{ROLE_ROOT}/contracts/finding.schema.json", text)
            self.assertIn("不得派生子代理", text)
            self.assertNotIn("tools: Agent", text)

    def test_4_generator_check_detects_content_drift_and_extra_adapter(self):
        result = run_generator_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        drift_path = ROOT / ".codex" / "agents" / f"{ROLE_IDS[0]}.toml"
        original = drift_path.read_text(encoding="utf-8")
        try:
            drift_path.write_text(original + "\n", encoding="utf-8", newline="\n")
            result = run_generator_check()
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(str(drift_path.relative_to(ROOT)), result.stdout)
        finally:
            drift_path.write_text(original, encoding="utf-8", newline="\n")

        extra_path = ROOT / ".claude" / "agents" / "stale-reviewer.md"
        try:
            extra_path.write_text("stale\n", encoding="utf-8", newline="\n")
            result = run_generator_check()
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(str(extra_path.relative_to(ROOT)), result.stdout)
        finally:
            extra_path.unlink(missing_ok=True)

    def test_5_claude_skill_is_a_thin_shared_core_entry(self):
        path = ROOT / ".claude" / "skills" / "multi-agent-review" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("../../../.agents/skills/multi-agent-review/SKILL.md", text)
        self.assertIn(
            "description: Use when 用户请求在 Claude Code 中审查 Spec、Plan、代码、Diff、分支或指定文件，"
            "尤其涉及需求符合性、正确性、安全、测试证据、集成契约或可维护性。",
            text,
        )
        self.assertNotIn("## 工作流", text)
        self.assertNotIn("## 路由", text)


if __name__ == "__main__":
    unittest.main()
