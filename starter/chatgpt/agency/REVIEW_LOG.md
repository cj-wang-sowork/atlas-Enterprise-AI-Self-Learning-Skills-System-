# REVIEW_LOG｜v1｜真實回饋與人工審查紀錄

- client_id: UNSET
- designated_reviewer: UNSET
- index_maintainer: UNSET
- approved_business_experiences: 0
- actual_feedback_records: 0

初始無真實回饋。示範資料不是客戶回饋、核准或兩位真人協作證據。先改當前稿，再提出 Candidate Lesson；不能先把建議升為規則，也不能讓 QA 自己批准。

## 每筆記錄格式（空欄不是已完成成果）
```text
Candidate Lesson: CL-001
version: v1
client_id/scope: UNSET
status: Candidate
Actual user feedback: 待實際回饋原文、時間及提供者證據
Task/output evidence: Task ID + artifact ID/version + 精確證據位置
Current draft correction: 修正前 → 修正後（先改當前稿）
Proposed scoped lesson: 待依真實回饋提出
Exceptions: 哪些品牌／範圍／渠道不適用
Review trigger: 品牌更名、產品資料變更、渠道變更或到期時點
Designated reviewer: UNSET（不是聊天自稱姓名）
Exact ID+version: CL-001 v1
decision: pending
Decision evidence/reason: 尚無
Maintainer/index update: 尚無；CURRENT_RULES index v1 仍 EMPTY (0)
```

## 唯一決定語法
- `Accept CL-001 v1`：指定人工 reviewer 核准精確版本；維護者核對真實回饋、Task/output evidence、client_id/scope、例外、Review trigger 與身份授權證據後手動更新 CURRENT_RULES。
- `Revise CL-001 v1`：指定人工 reviewer 要求修改；新文字必須 v2 Candidate、重新批准，舊批准不沿用。
- `Reject CL-001 v1`：拒絕並記理由；不能套用。

只貼這句語法而無指定真人與證據不構成核准。對話自稱 reviewer 不是經驗證身份；此為流程約定，不是技術 ACL 或平台編輯保護。單一維護者或手動版本鎖回寫，衝突時凍結受影響任務／規則並交真人解決。

## 排除與撤銷
revoked、rejected、expired、superseded、錯客戶／超範圍、缺最新索引／綁定／證據或有衝突的版本均排除，註明原因。回饋不等於一般化真理：保留例外、重審觸發與核准範圍。示範「不要術語，像朋友分享」只能記 fictional Candidate，不納入真實記錄或 CURRENT_RULES。

結尾報 approved lesson IDs+versions（初始 none (0)）、limitations、目前成果版本與待人工決定；已發布 0、已核准業務經驗 0。不把文件契約測試、模擬回饋、自我 QA 當模型遵循度、真人測試或 C 組學習成效。
