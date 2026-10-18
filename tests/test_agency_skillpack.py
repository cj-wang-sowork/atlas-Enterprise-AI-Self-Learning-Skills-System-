"""Offline artifact contracts; not evidence of model/UI or business performance.

Pins were measured from the real read-only upstream clone at the stated commit.
CI needs only committed ATLAS artifacts, never that clone, credentials or network.
"""
from pathlib import Path
import hashlib
import json
import re
import unittest

REPO = Path(__file__).resolve().parents[1]
AGENCY = REPO / "starter/chatgpt/agency"
UPSTREAM_COMMIT = "a230b7f6f5ed987fefbb8f4933c411681701c8ed"
LICENSE_SHA256 = "1ec1873af4d67f337dd9c63cb79c794949886e9963831ca5c29dd7f441a0faa0"
SKILL_PINS = {
    "01-brand-positioning": "f02b3fd0cbe98ce4e614bdd40c6077c3ab5a59cc3b5ed5270a889e4de0966daa",
    "02-product-positioning": "a7d54307b79496b016e483c704ece5989f022dd65b669c1d47510334ec5e3677",
    "03-social-operating-system": "20129acb885bfc5ea46137364ea2b192d262730e97b8e92edb63bfe81b1df5c7",
    "04-content-pillar-design": "b830fcf75ad5a01c5caa3d4865455c82e81a44875d2d029004a1961507d03df0",
    "05-performance-review": "3576b9b0a2b559c8c699ca691eda9f591f733921e6a898c960cd8cd1fe193e8d",
    "06-linkedin-operator-pack": "8978fa5394a3a2ad74a86a7ea1f664dec8990171f3da0c803ddd0e6d83785950",
}


class AgencySkillPackTests(unittest.TestCase):
    def manifest(self):
        path = AGENCY / "UPSTREAM_PROVENANCE.json"
        self.assertTrue(path.is_file(), "Missing source-pinned agency provenance")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_upstream_license_bytes_and_source_pins_are_offline_verifiable(self):
        m = self.manifest()
        self.assertEqual(m["repository"], "cj-wang-sowork/brand-to-social-os")
        self.assertEqual(m["commit"], UPSTREAM_COMMIT)
        self.assertEqual(m["as_of"], "2026-10-18")
        self.assertEqual(m["distribution"], "adaptation-not-full-vendor")
        self.assertFalse(m["runtime_upstream_fetch"])
        self.assertEqual(m["license"]["spdx"], "MIT")
        self.assertEqual(m["license"]["sha256"], LICENSE_SHA256)
        license_bytes = (AGENCY / "UPSTREAM_LICENSE.txt").read_bytes()
        self.assertEqual(hashlib.sha256(license_bytes).hexdigest(), LICENSE_SHA256)
        self.assertIn(b"Copyright (c) 2026 SoWork", license_bytes)
        self.assertIn(b"The above copyright notice and this permission notice", license_bytes)
        self.assertIn(b'THE SOFTWARE IS PROVIDED "AS IS"', license_bytes)
        inventory = m["upstream_files"]
        self.assertEqual(m["upstream_tracked_file_count"], 52)
        self.assertEqual(len(inventory), 52)
        by_path = {r["path"]: r for r in inventory}
        self.assertEqual(len(by_path), len(inventory), "Duplicate provenance paths")
        for row in inventory:
            self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(row["bytes"], 0)
            self.assertFalse(Path(row["path"]).is_absolute())
            self.assertNotIn("..", Path(row["path"]).parts)
        self.assertEqual(by_path["LICENSE"]["sha256"], LICENSE_SHA256)
        self.assertEqual(len(m["skills"]), 6)
        self.assertEqual({s["id"] for s in m["skills"]}, set(SKILL_PINS))
        for skill in m["skills"]:
            self.assertEqual(skill["upstream_version"], "1.0.0")
            self.assertEqual(skill["adaptation_version"], "1.0.0-agency.1")
            main = f"skills/{skill['id']}/SKILL.md"
            self.assertEqual(skill["source_path"], main)
            self.assertEqual(by_path[main]["sha256"], SKILL_PINS[skill["id"]])
            self.assertEqual(set(skill["supporting_paths"]), {
                f"skills/{skill['id']}/{name}"
                for name in ("CHECKLIST.md", "prompt.md", "example-output.md")
            })
            for path in skill["supporting_paths"]:
                self.assertIn(path, by_path)

    def pack(self):
        path = AGENCY / "SKILL_PACK.md"
        self.assertTrue(path.is_file(), "Missing self-contained adapted skill methods")
        return path.read_text(encoding="utf-8")

    def test_six_real_skills_have_executable_inline_methods_and_handoffs(self):
        text = self.pack()
        sections = re.split(r"(?m)^## Skill: ", text)[1:]
        self.assertEqual(len(sections), 6)
        actual = {part.splitlines()[0].strip(): part for part in sections}
        self.assertEqual(set(actual), set(SKILL_PINS))
        for sid, section in actual.items():
            for required in (
                f"skills/{sid}/SKILL.md", "上游版本：1.0.0", "改編版本：1.0.0-agency.1",
                "### 輸入", "### 步驟", "### 輸出", "### Review / DoD",
                "### 最新版本依賴與交接", "### 受阻時",
            ):
                self.assertIn(required, section, sid)
            self.assertGreater(len(re.findall(r"[\u4e00-\u9fff]", section)), 350, sid)
        for method in (
            "Strategic Contrast", "JTBD", "Message Hierarchy", "Weekly Publishing Loop",
            "Topic Scoring", "Education", "Point of view", "Proof", "Behind the scenes",
            "Conversion", "Winners", "Losers", "Hook",
        ):
            self.assertIn(method, text)
        for role, artifact in (
            ("AccountManager", "ClientBrief"), ("MarketResearcher", "ResearchBrief"),
            ("BrandStrategist", "StrategyBrief"), ("ContentPlanner", "ContentCalendar"),
            ("QAReviewer", "ReviewReport"),
        ):
            self.assertRegex(text, rf"\| {role} \| {artifact} \|")
        for rule in (
            "Agency ADDED", "不是第七個上游技能", "五種角色不是六個新代理",
            "方法已內嵌", "來源連結只供溯源", "不會自動抓取 GitHub",
            "人工維護", "CurrentVersions", "superseded", "跨對話", "DRAFT",
            "不需正式品牌核准才能起草", "客戶提供不等於獨立查證", "只先問安全關鍵問題",
            "不會寫入 .agents/", "不會啟動後端", "不會更新模型權重",
        ):
            self.assertIn(rule, text)
        notice = (AGENCY / "UPSTREAM_LICENSE.txt").read_text(encoding="utf-8")
        self.assertIn(notice.rstrip(), text, "One-file upload must retain complete MIT notice")

    def test_one_line_skincare_brief_has_strategy_pillars_calendar_and_seven_full_drafts(self):
        text = self.pack()
        self.assertIn("# 一句需求的首輪實作", text)
        example = text.split("# 一句需求的首輪實作", 1)[1].split("# 授權、溯源與改編聲明", 1)[0]
        self.assertIn("幫一個保養品牌規劃七天社群內容。", example)
        for required in ("ClientBrief v1", "ResearchBrief v1", "StrategyBrief v1", "ContentCalendar v1", "ReviewReport v1", "V 為空", "未獨立查證", "未排程／未發佈", "Proof 暫停", "Agency 渠道改編"):
            self.assertIn(required, example)
        rows = re.findall(r"(?m)^\| Day ([1-7]) \|([^\n]+)$", example)
        self.assertEqual([day for day, _ in rows], list("1234567"))
        copies = re.findall(r"(?ms)^### Copy (SK-0[1-7])[^\n]*\n(.*?)(?=^### Copy |^## |\Z)", example)
        self.assertEqual([copy_id for copy_id, _ in copies], [f"SK-{i:02d}" for i in range(1, 8)])
        for copy_id, body in copies:
            self.assertIn("```text\n", body, copy_id)
            caption = body.split("```text\n", 1)[1].split("```", 1)[0]
            self.assertGreaterEqual(len(re.findall(r"[\u4e00-\u9fff]", caption)), 90, copy_id)
            self.assertNotRegex(caption, r"\[(?:待|填|品牌|產品)|TBD|TODO|SPF|臨床|見證|回購率|治療|保證")
            self.assertIn("CTA：", body, copy_id)
            self.assertIn("證據：", body, copy_id)
        for pillar in ("Education", "Point of view", "Proof", "Behind the scenes", "Conversion"):
            self.assertIn(pillar, example)
        self.assertIn("內容審查不是成效分析", example)
        self.assertIn("待真人", example)

        # The new worked output must obey the pack's safety contract as well.
        for forbidden in (
            r"(?:40\s*[-–]\s*60|50\s*[-–]\s*70)\s*%",
            r"Below 1 per week = invisible",
            r"至少\s*3\s*(?:倍|篇).*效率",
            r"已(?:完成|通過)(?:真人|非工程師|多成員|跨對話).*驗證",
            r"Saved output to [`']?\.agents/",
        ):
            self.assertNotRegex(text, forbidden)
        for required in ("可編輯規劃啟發式", "不是平台規則", "PENDING：待真人觀察", "不是經實驗驗證的商業成效分數"):
            self.assertIn(required, text)

    def test_local_pack_digest_and_framework_lineage_match_the_shipped_adaptation(self):
        m = self.manifest()
        self.assertIn("local_artifacts", m, "Adaptation content digest is missing")
        self.assertEqual(set(m["local_artifacts"]), {"SKILL_PACK.md", "UPSTREAM_LICENSE.txt"})
        for name, record in m["local_artifacts"].items():
            data = (AGENCY / name).read_bytes()
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest(), name)
            self.assertEqual(record["bytes"], len(data), name)
        self.assertEqual(m["manifest_hash_policy"], "exclude-self-to-avoid-circular-digest")
        expected = {
            "01-brand-positioning": ["Strategic Contrast"],
            "02-product-positioning": ["JTBD", "Message Hierarchy"],
            "03-social-operating-system": ["Weekly Publishing Loop", "Topic Scoring", "Repurposing Ladder"],
            "04-content-pillar-design": ["Five-pillar Content Model"],
            "05-performance-review": ["Winners / Losers", "Audience Quality", "Business Relevance", "Experiment Review"],
            "06-linkedin-operator-pack": ["Six Hook Formulas", "Hook / Body / CTA"],
        }
        inventory = {row["path"] for row in m["upstream_files"]}
        for skill in m["skills"]:
            self.assertEqual(skill["frameworks"], expected[skill["id"]])
            self.assertTrue(skill["reference_paths"])
            self.assertTrue(set(skill["reference_paths"]).issubset(inventory))
        for key in ("non_engineer_ui", "multi_member_handoff", "cross_conversation_reuse"):
            self.assertEqual(m["acceptance"][key], "PENDING human observation")


if __name__ == "__main__":
    unittest.main()
