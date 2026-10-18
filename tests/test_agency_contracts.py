"""Agency source/prompt contracts only: not model, UI, or human-test proof."""
from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[1]
KIT = REPO / "starter/chatgpt/agency"
EXAMPLES = REPO / "examples/agency"


def document(path):
    if not path.is_file():
        raise AssertionError("Missing agency deliverable: " + str(path.relative_to(REPO)))
    return path.read_text(encoding="utf-8")


class AgencyContracts(unittest.TestCase):
    def test_first_request_has_self_contained_draft_operating_contract(self):
        instructions = document(KIT / "PROJECT_INSTRUCTIONS.md")
        self.assertLessEqual(len(instructions), 6500)
        for phrase in ("恰好五個功能角色", "同一個 ChatGPT", "ClientBrief", "ResearchBrief", "StrategyBrief", "ContentCalendar", "ReviewReport", "七天", "七篇完整文案", "DRAFT", "一個問題", "client_id", "EMPTY (0)", "不是技術 ACL", "自動跨對話", "已核准業務經驗 0"):
            self.assertIn(phrase, instructions)
        setup = document(KIT / "AGENCY_SETUP.md")
        self.assertIn("三分鐘", setup)
        self.assertIn("不是實測保證", setup)
        self.assertIn("ATLAS | 客戶名", setup)
        self.assertIn("貼入", setup)
        self.assertIn("AGENCY_PLAYBOOK.md", setup)
        brief = document(KIT / "CLIENT_BRIEF.md")
        for phrase in ("client_id: UNSET", "scope:", "未知", "不是獨立驗證"):
            self.assertIn(phrase, brief)


    def test_five_sequential_roles_have_inputs_outputs_qa_handoff(self):
        roles = document(KIT / "AGENT_ROLES.md")
        entries = re.findall(r"^## ([A-Za-z]+) → ([A-Za-z]+)$", roles, re.M)
        self.assertEqual(entries, [("AccountManager", "ClientBrief"), ("MarketResearcher", "ResearchBrief"), ("BrandStrategist", "StrategyBrief"), ("ContentPlanner", "ContentCalendar"), ("QAReviewer", "ReviewReport")])
        for section in re.split(r"^## [A-Za-z]+ → [A-Za-z]+$", roles, flags=re.M)[1:]:
            for field in ("輸入", "輸出", "DoD / QA", "交接", "status", "human_owner", "next_reviewer"):
                self.assertIn(field, section)
        workflow = document(KIT / "WORKFLOW.md")
        for phrase in ("DRAFT", "READY_FOR_REVIEW", "CHANGES_REQUESTED", "HUMAN_APPROVED", "BLOCKED", "策略未核准", "未完成經驗證市場研究", "每個任務", "人工", "Accept CL-001 v1", "Revise CL-001 v1", "Reject CL-001 v1"):
            self.assertIn(phrase, workflow)


    def test_manual_collaboration_and_empty_version_bound_rule_index(self):
        board = document(KIT / "TASK_BOARD.md")
        for field in ("task_id", "client_id", "artifact_id", "artifact_version", "source_versions", "rule_versions", "evidence", "human_owner", "next_reviewer", "status", "單一維護者", "凍結"):
            self.assertIn(field, board)
        rules = document(KIT / "CURRENT_RULES.md")
        for phrase in ("Approved rules: EMPTY (0)", "client_id: UNSET", "designated_reviewer: UNSET", "revoked", "rejected", "expired", "superseded", "重新核准", "不是技術 ACL"):
            self.assertIn(phrase, rules)
        log = document(KIT / "REVIEW_LOG.md")
        for phrase in ("Actual user feedback", "Task/output evidence", "Candidate Lesson", "client_id/scope", "Exceptions", "Review trigger", "decision: pending", "先改當前稿", "不是客戶回饋"):
            self.assertIn(phrase, log)
        for name in ("AGENCY_SETUP", "PROJECT_INSTRUCTIONS", "CLIENT_BRIEF", "AGENT_ROLES", "WORKFLOW", "TASK_BOARD", "CURRENT_RULES", "REVIEW_LOG"):
            text = document(KIT / (name + ".md"))
            for syntax in ("Accept CL-001 v1", "Revise CL-001 v1", "Reject CL-001 v1"):
                self.assertIn(syntax, text, name)


    def test_labelled_example_has_five_filled_outputs_and_seven_actual_drafts(self):
        brief = document(EXAMPLES / "skincare-brief.md")
        for phrase in ("SYNTHETIC", "示範保養品牌", "DEMO-SKIN-001", "2026-10-18", "user-provided", "未知"):
            self.assertIn(phrase, brief)
        sample = document(EXAMPLES / "first-round.md")
        headings = re.findall(r"^## ([A-Za-z]+)｜", sample, re.M)
        self.assertEqual(headings, ["ClientBrief", "ResearchBrief", "StrategyBrief", "ContentCalendar", "ReviewReport"])
        posts = re.findall(r"^### D([1-7])｜(2026-10-\d{2})｜([^\n]+)\n(.*?)(?=^### |^## |\Z)", sample, re.M | re.S)
        self.assertEqual([int(p[0]) for p in posts], list(range(1, 8)))
        from datetime import date, timedelta
        self.assertEqual([p[1] for p in posts], [str(date(2026, 10, 19) + timedelta(days=i)) for i in range(7)])
        for day, _, _, body in posts:
            text = re.search(r"文案：\n(.+?)\n\n視覺方向：", body, re.S)
            if text is None:
                self.fail("Missing complete copy and visual direction for day " + day)
            self.assertGreater(len(text.group(1)), 55, day)
            self.assertNotRegex(text.group(1), r"\{.*?\}|\[待|待填|TODO|TBD")
            self.assertIn("CTA：", body)
        for phrase in ("未完成經驗證市場研究", "來源缺口", "fictional Candidate", "decision: pending", "不是兩位真人", "不是 live ChatGPT", "不是 C 組學習成效", "已發布 0", "已核准業務經驗 0", "none (0)"):
            self.assertIn(phrase, sample)
        self.assertLess(sample.index("修正後"), sample.index("fictional Candidate"))


    def test_download_sample_is_separate_from_five_authoritative_uploads(self):
        setup = document(KIT / "AGENCY_SETUP.md")
        upload_section = setup.split("主要上傳清單（五檔）：", 1)[1].split("AGENT_ROLES.md", 1)[0]
        self.assertEqual(re.findall(r"^\d\. ([A-Z_]+\.md)", upload_section, re.M), ["CLIENT_BRIEF.md", "AGENCY_PLAYBOOK.md", "TASK_BOARD.md", "CURRENT_RULES.md", "REVIEW_LOG.md"])
        for phrase in ("[SAMPLE_WORK.md](SAMPLE_WORK.md)", "獨立 demo Project", "不要與真實客戶", "不要再與合併檔一起上傳", "不是技術 ACL", "公開連結"):
            self.assertIn(phrase, setup)

    def test_all_draft_posts_exclude_unsupported_product_claims(self):
        sample = document(EXAMPLES / "first-round.md")
        posts = re.findall(r"文案：\n(.+?)\n\n視覺方向：", sample, re.S)
        self.assertEqual(len(posts), 7)
        for post in posts:
            self.assertNotRegex(post, r"SPF|臨床|修復|美白|抗皺|逆齡|保濕|醫師推薦|三天見效|元起|%|含.{0,5}成分|見證")
        research = sample.split("## ResearchBrief｜", 1)[1].split("## StrategyBrief｜", 1)[0]
        self.assertIn("不適用（未外部檢索）", research)
        self.assertNotRegex(research, r"https?://")

    def test_instruction_gates_distinguish_draft_qa_approval_and_learning(self):
        instructions = document(KIT / "PROJECT_INSTRUCTIONS.md")
        for phrase in ("source gap", "未完成經驗證市場研究", "user-provided", "不編 SKU", "自我 QA 不等於客戶核准", "不阻止下游 DRAFT", "UNIDENTIFIED", "D1–D7", "時區", "單一維護者", "版本鎖", "revoked", "rejected", "expired", "superseded", "新版本、重新核准", "自稱審查者不是經驗證身份"):
            self.assertIn(phrase, instructions)

    def test_each_example_artifact_retains_manual_provenance_and_handoff(self):
        sample = document(EXAMPLES / "first-round.md")
        for section in re.split(r"^## [A-Za-z]+｜[^\n]+\n", sample, flags=re.M)[1:]:
            for phrase in ("Task ID=DEMO-T-001", "client_id=DEMO-SKIN-001", "source_versions=", "rule_versions=none (0)", "human_owner=UNASSIGNED", "next_reviewer=UNASSIGNED", "evidence="):
                self.assertIn(phrase, section)
        rules = document(KIT / "CURRENT_RULES.md")
        self.assertNotRegex(rules, r"(?m)^\|\s*CL-\d+")


if __name__ == "__main__":
    unittest.main()
