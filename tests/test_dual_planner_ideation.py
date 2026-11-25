"""Structural and contract checks for the dual-planner-ideation skill."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "dual-planner-ideation"
SKILL_MD = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
TEMPLATE_MD = SKILL_DIR / "references" / "co-planner-prompt-template.md"
RUBRIC_MD = SKILL_DIR / "references" / "anti-defensive-rubric.md"
README_MD = ROOT / "README.md"

REQUIRED_TAGS = ("[HARD-FACT]", "[FIXABLE-SPEC]", "[UNVERIFIED-RISK]")


class DualPlannerIdeationTests(unittest.TestCase):
    def test_frontmatter_and_interface_metadata(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md must start with YAML frontmatter")
        frontmatter = match.group(1)
        self.assertIn("name: dual-planner-ideation", frontmatter)
        self.assertIn("description:", frontmatter)

        yaml_text = OPENAI_YAML.read_text(encoding="utf-8")
        for key in ("interface:", "display_name:", "short_description:", "default_prompt:"):
            self.assertIn(key, yaml_text)
        self.assertIn("$dual-planner-ideation", yaml_text)

    def test_relative_markdown_links_resolve(self):
        for doc in (SKILL_MD, TEMPLATE_MD, RUBRIC_MD):
            text = doc.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#")):
                    continue
                resolved = (doc.parent / target).resolve()
                self.assertTrue(resolved.is_file(), f"Broken link {target} in {doc}")

    def test_three_class_triage_and_anti_defensive_clauses_consistent(self):
        for doc in (SKILL_MD, TEMPLATE_MD, RUBRIC_MD):
            text = doc.read_text(encoding="utf-8")
            for tag in REQUIRED_TAGS:
                self.assertIn(tag, text, f"Missing {tag} in {doc.name}")
            self.assertIn("MVV", text, f"Missing MVV rescue clause in {doc.name}")

        self.assertIn("Self-Audit", TEMPLATE_MD.read_text(encoding="utf-8"))
        self.assertIn("Overrule", RUBRIC_MD.read_text(encoding="utf-8"))

    def test_readme_registers_skill(self):
        readme = README_MD.read_text(encoding="utf-8")
        self.assertIn("(dual-planner-ideation/SKILL.md)", readme)
        self.assertIn("dual-planner-ideation/references/co-planner-prompt-template.md", readme)
        self.assertIn("dual-planner-ideation/references/anti-defensive-rubric.md", readme)


if __name__ == "__main__":
    unittest.main()
