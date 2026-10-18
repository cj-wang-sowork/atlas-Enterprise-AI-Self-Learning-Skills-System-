# TASK_BOARD｜人工共享索引｜v1

- client_id: UNSET
- scope: 此客戶社群企劃
- index_maintainer: UNASSIGNED（須指定單一維護者）
- base_version: v1
- manual_lock: none（編輯前填持有人／基準版本／解鎖條件）
- approved rules: none (0)
- published outcomes: 0

本表初始沒有已完成任務；以下是待填任務卡格式，不是實際成果。不必先填滿才做首輪草稿。每個任務一個對話，首輪可用一張父任務卡涵蓋五稿，分工作業再建子 Task ID。

```text
task_id: 待建立穩定 ID，例如 T-001（建立後不可重用）
client_id: UNSET（未識別稿填 UNIDENTIFIED）
scope: 一週社群企劃
conversation_ref: 待貼當前任務對話證據位置
artifact_id: 待建立（五稿逐一登記）
artifact_version: v1
source_versions: CLIENT_BRIEF v1 + 實際取得來源版本
rule_versions: none (0)；CURRENT_RULES index v1
human_owner: UNASSIGNED
next_reviewer: UNASSIGNED
status: DRAFT
evidence: 待貼精確稿件／段落／受控檔案連結及版本
handoff: 下一位真人、所需判斷與時點待指定
base_index_version: v1
manual_lock: 持有人／基準版本／解鎖條件待維護者確認
```

## 兩人以上的交接協定
- owner 貼卡另開任務對話；開始前讀最新 CLIENT_BRIEF、TASK_BOARD、CURRENT_RULES 及必要成果。共享 Project 不保證同一聊天或檔案即時同步；不自動跨對話記憶、抓 GitHub 或寫本機檔。
- AI 回覆中提出任務卡更新內容，不宣稱已寫回共享檔。單一維護者人工檢查並更新已審查版本；別人先取得手動版本鎖再改，避免過時／同時覆蓋。
- artifact 修正升版本；來源／規則精確版本與證據隨卡保留。發現不一致時凍結受影響任務／規則，保留兩版，交真人解決。不可默默採用最後一版。
- human_owner 與 next_reviewer 需填真人，不以五個模擬角色代替。指定 reviewer 對精確成果版本與證據批准才可記 HUMAN_APPROVED，發布還需渠道、法遵與素材權利審查。
- 狀態：DRAFT → READY_FOR_REVIEW → CHANGES_REQUESTED / HUMAN_APPROVED；局部衝突用 BLOCKED，不擋其餘合理草稿。

CURRENT_RULES 的核准另走規則流程：真實回饋先改稿，記 Candidate Lesson，再由指定人工 reviewer 對精確版本作 `Accept CL-001 v1` / `Revise CL-001 v1` / `Reject CL-001 v1`。維護者人工回寫；不是技術 ACL，聊天自稱身份不能代替平台身份與審查證據。初始已核准業務經驗 0。
