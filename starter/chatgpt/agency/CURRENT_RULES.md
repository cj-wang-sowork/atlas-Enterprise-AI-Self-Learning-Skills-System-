# CURRENT_RULES｜當前核准版本人工索引

Approved rules: EMPTY (0)

- index_version: v1
- client_id: UNSET
- scope: UNSET
- designated_reviewer: UNSET
- index_maintainer: UNSET
- last_review_evidence: none
- approved_business_experiences: 0

沒有預設品牌規則，也沒有示範回饋的預先核准。這是手動流程索引，不是後端學習儲存或技術存取控制。真人尚未綁定便不核准。共享 Project 平台編輯者可能修改檔案；本協定不是技術 ACL，聊天自稱 reviewer 不是經驗證身份。審查者資格由 owner 在平台可核對身份與授權紀錄中指定。

## 使用閘門（全部通過才用）
1. 取得維護者提供的最新索引版本與同 client_id/scope 綁定；未知、缺最新索引或出現衝突即排除受影響規則，明說原因，不沿用猜測的舊版。
2. 索引指向精確 CL-ID/vN，REVIEW_LOG 有真實回饋、Task/output evidence、適用範圍、例外、review trigger、指定人工 reviewer 的 exact ID+version 決定及證據。
3. 狀態必須 approved 且未 revoked、rejected、expired、superseded；錯客戶或超範圍一律排除。示範 fictional Candidate 永遠不是已核准證據。
4. 文字變更必須新版本、重新核准；舊批准不自動延續。只有版本未變且索引／條件仍有效才可重用。

## 人工更新協定
先改當前成果，再記 Candidate。指定 reviewer 對精確版本用：
- `Accept CL-001 v1`：人工批准該版本；維護者核對證據後更新索引。
- `Revise CL-001 v1`：要求修改；新版本仍 pending，不能使用。
- `Reject CL-001 v1`：拒絕且排除，不可當 approved。

單一維護者／手動版本鎖避免多人覆寫；衝突時凍結受影響規則與任務，保留雙方版本交真人處理。不因 ChatGPT 自我 QA 或口頭自稱批准而更新。以下只列未來核准記錄欄位，不是已存在規則：

| Exact ID+version | client_id/scope | Approved text | Feedback/task evidence | Designated reviewer + decision evidence | Exceptions / review trigger | Status |
|---|---|---|---|---|---|---|

本輪適用規則初始 none (0)；沒有核准不得說已獲得 C 組學習成效。發布成果批准和業務規則批准分開記錄。
