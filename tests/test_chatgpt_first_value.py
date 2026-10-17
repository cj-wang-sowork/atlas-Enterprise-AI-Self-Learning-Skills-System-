"""Static prompt contracts, not a claim of live model/UI adherence."""
from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[1]
KIT = REPO / "starter/chatgpt"


def card(text):
    match = re.search(r"```text\n(.*?)\n```", text, re.S)
    if not match:
        raise AssertionError("Missing self-contained copy/paste task card")
    return match.group(1)


class FirstValueTests(unittest.TestCase):
    def test_single_paste_card_starts_work_before_setup(self):
        path = KIT / "FIRST_WIN.md"
        self.assertTrue(path.exists(), "First-win single-chat card is missing")
        prompt = card(path.read_text())
        self.assertIn("我要幫 SoWork 建立一支專門獲取 B2B 新客戶的 AI 行銷團隊。", prompt)
        for required in ("先交付第一份可用成果", "不要先訪談", "最多 3 個功能角色", "1–2 行", "ICP", "不要先做 KPI", "台灣 B2B", "20 家就做 20 家", "3 家"):
            self.assertIn(required, prompt)
        for required in ("即時瀏覽", "已核對的來源包", "不可編造", "來源 URL", "查閱日期", "QA", "先交付", "一個問題", "不得寄送"):
            self.assertIn(required, prompt)
        self.assertIn("不是已完成研究", path.read_text())

    def test_exported_readme_bundles_complete_card_before_optional_setup(self):
        readme = (KIT / "README.md").read_text()
        self.assertEqual(card(readme), card((KIT / "FIRST_WIN.md").read_text()))
        self.assertLess(readme.index("```text"), readme.index("## Optional Project setup"))
        self.assertIn("four-file export", readme)
        self.assertIn("not fetched automatically", readme)

    def test_project_instructions_use_first_output_and_evidence_gate(self):
        instructions = (KIT / "PROJECT_INSTRUCTIONS.md").read_text()
        for text in ("先交付", "最多 3 個功能角色", "20 家就做 20 家", "即時瀏覽", "已核對的來源包", "受阻", "Work standard v1", "approved lesson IDs+versions used", "none (0)", "limitations", "真實使用者回饋", "CandidateLesson", "精確 ID+版本", "拒絕或過時版本不得使用", "不是授權", "跨對話"):
            self.assertIn(text, instructions)

    def test_manual_lesson_record_and_empty_current_index_are_version_bound(self):
        index_path = KIT / "CURRENT_RULES.md"
        self.assertTrue(index_path.exists(), "No human-maintained current rule index")
        index = index_path.read_text()
        for text in ("Approved rules: EMPTY (0)", "operator", "Accept CL-001 v1", "Revise CL-001 v1", "Reject CL-001 v1", "superseded", "not an approved lesson", "exact ID+version"):
            self.assertIn(text, index)
        log = (KIT / "OUTCOME_REVIEW_LOG.md").read_text()
        for text in ("CandidateLesson ID / revision", "Actual user feedback", "Task/output evidence", "Exact ID+version", "Review or expiry trigger", "current-version index", "not approval"):
            self.assertIn(text, log)

    def test_guide_prioritizes_value_and_preserves_manual_security_limits(self):
        guide = (REPO / "docs/CHATGPT_STARTER.md").read_text()
        self.assertIn("FIRST_WIN.md", guide)
        self.assertIn("## Optional Project setup", guide)
        self.assertLess(guide.index("FIRST_WIN.md"), guide.index("## Optional Project setup"))
        for text in ("four-file export", "not the same as setting project instructions", "not fetched automatically", "not been verified", "MEMORY.md", "CURRENT_RULES.md", "no automatic", "one real feedback"):
            self.assertIn(text, guide)


if __name__ == "__main__":
    unittest.main()
