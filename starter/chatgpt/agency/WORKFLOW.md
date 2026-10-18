# WORKFLOW｜v1｜從一句需求到可審查的一週

## 開工
讀 active CLIENT_BRIEF 的 client_id/scope/version 與 CURRENT_RULES 的客戶綁定、reviewer、維護者及 index_version。未知客戶用 UNIDENTIFIED DRAFT；不能混用已知其他品牌資料。非關鍵未知用假設完成；涉及客戶衝突、隱私／安全先隔離再只問一個問題。使用者指定數量／格式優先，預設七天七篇全文。不先訪談 KPI、不建立人格小傳。

## 一輪順序與狀態
AccountManager → ClientBrief → MarketResearcher → ResearchBrief → BrandStrategist → StrategyBrief → ContentPlanner → ContentCalendar → QAReviewer → ReviewReport。

五個工序由同一個 ChatGPT 依序模擬，不是獨立 agents。每份成果標 DRAFT；策略未核准仍允許下游 DRAFT。無來源／研究工具時 ResearchBrief 仍須寫明已知、未知、假設與來源缺口，標「未完成經驗證市場研究」，不可用虛構競品／統計裝滿頁面。上傳 brief 是 user-provided，不是獨立驗證。可用來源須記 URL、查閱日期、來源分類。

| 狀態 | 條件 | 下一步／人工責任 |
|---|---|---|
| DRAFT | 已產出可修改內容；假設已標 | 按序交下角色，真人 owner 待指派 |
| READY_FOR_REVIEW | 五稿自我 QA 通過、尚未批准 | 交指定真人 reviewer，不等於已發布 |
| CHANGES_REQUESTED | 真人提出具體修正 | 先修當前稿、升 artifact version、再送審 |
| HUMAN_APPROVED | 真實指定 reviewer 對精確成果版本批准，有證據 | 維護者記錄批准範圍，發布仍需必要渠道／法遵／素材審查 |
| BLOCKED | 身份、來源、資料或版本衝突影響某部分 | 凍結受影響部分，問真人解決；其餘可做 DRAFT |

不編產品／成分／SPF／價格／證言／醫療或臨床利益；素材權利與發布審查待真人。沒有外部操作能力的來源包不自動寄信、排程、發文、CRM、cron、API daemon 或後端 SSO 改動。沒有成果證據不能把企劃說成已執行或取得成效。

## 每個任務一個對話：2+ 人操作協定
1. 指定真實 owner、next reviewer 與單一 index_maintainer（不能只填 AI 角色）。邀請明確成員、依平台現有功能設適當最低權限，勿開公開連結。
2. 維護者用 TASK_BOARD 建穩定 Task ID，貼 client_id、artifact ID/version、來源／規則版本、證據連結、owner、next reviewer、status。每個任務另開對話並貼完整任務卡及目前來源。
3. 開始前核對最新共享索引；同 Project 不代表知道其他對話或即時同步檔案。缺最新索引、客戶綁定或規則決定時，排除該規則並解釋，請維護者補件。
4. 每次交付貼回精確版本與證據。單一維護者人工回寫已審查成果及 TASK_BOARD；需要多人寫時先取得記有持有人與基準版本的手動版本鎖。
5. 發現並行覆蓋或互相衝突，凍結受影響任務／規則，保留兩版證據，由真人解衝突後才產新版本。不可「最後寫入自動勝出」。

這是多人協作規程，不是已測試兩位真人。不承諾自動跨對話記憶、自動 GitHub 取檔、本機寫檔或自動學習。組織方式不是後端安全邊界；實際平台編輯權者可能改指令／檔案，流程不是技術 ACL，聊天自稱 reviewer 不算身份驗證。

## 真實回饋 → 修稿 → Candidate → 人工決定
先修當前稿並記修正前後、Task ID、artifact/version 與證據，再提有 client_id/scope、例外、重審觸發的 Candidate Lesson。缺真實回饋不建立真實學習成效；示範只算 fictional Candidate。

指定人工 reviewer 必須對精確 ID/version 留下其中一項與理由／證據：
- `Accept CL-001 v1`：核准此版本，人工維護者核對後寫入 CURRENT_RULES。
- `Revise CL-001 v1`：要求修改，產 v2 Candidate，舊批准不延續。
- `Reject CL-001 v1`：拒絕並排除；不得當作核准使用。

CURRENT_RULES 初始 Approved rules: EMPTY (0)。只使用索引中同客戶／範圍、確有回饋與任務證據及指定人工批准的精確版本。缺最新索引／綁定／衝突便排除並說明；revoked、rejected、expired、superseded 與錯客戶均排除。規則文字變更產新版本，必須重新審批。最後報五稿狀態、approved lesson IDs+versions=none (0)（初始）、limitations、已發布 0、已核准業務經驗 0，成果後問一個回饋問題。
