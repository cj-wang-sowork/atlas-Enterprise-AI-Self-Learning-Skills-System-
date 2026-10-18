# ATLAS for ChatGPT Agency Edition v1.0｜三分鐘起步路徑

「三分鐘」是理想起步路徑，不是實測保證。這是來源工作流程檔案包，未驗證真人在 ChatGPT 的完整操作時間、實際建立 Project 或多人使用成果，不是後端安裝程式。

## 1. 一個客戶、一個 Project
以 `ATLAS | 客戶名` 命名。品牌名還未知可先叫 `ATLAS | 未識別保養客戶`，待確認再綁定 client_id；不要混入另一品牌檔案。Project 組織不是 ATLAS 後端安全邊界；真正分享、帳號、記憶與存取權依平台設定。先確認當前方案可用功能，不保證所有方案相同。

## 2. 貼入指令、上傳五檔
將 PROJECT_INSTRUCTIONS.md 全文**貼入專案指令設定**，不是只上傳此檔。

主要上傳清單（五檔）：
1. CLIENT_BRIEF.md：客戶範圍與來源，未知可留未知；不必填完才工作。
2. AGENCY_PLAYBOOK.md：發布包編譯的角色／流程／技能權威合併檔。
3. TASK_BOARD.md：任務與版本人工索引。
4. CURRENT_RULES.md：當前核准規則索引，初始 EMPTY (0)。
5. REVIEW_LOG.md：回饋、修稿與人工決定證據。

AGENT_ROLES.md、WORKFLOW.md、SKILL_PACK.md 是 ZIP 內的編寫參考，已合併至 AGENCY_PLAYBOOK.md，**不要再與合併檔一起上傳**，以免重複版本衝突。AGENCY_SETUP.md 不必上傳。下載包若缺合併檔，先請維護者提供正式合併版本，不假裝已安裝。實際方案若檔案限制更少，由維護者人工合併、記清單一權威來源與版本，再移除舊版；不要盲目堆疊重複檔，不保證所有方案都容納五檔。

## 3. 只送這一句開始第一週
> 我剛接到一個保養品牌客戶，幫我建立行銷團隊，完成下週的社群企劃。

應收到 ClientBrief → ResearchBrief → StrategyBrief → ContentCalendar → ReviewReport 五份可用 DRAFT；預設七天且七篇完整文案、視覺方向、CTA。非關鍵缺口用假設完成，不先訪談十題。沒有來源的研究稿明示未完成經驗證市場研究；沒有產品資料就不寫產品功效。

完整虛構範例見下載包 [SAMPLE_WORK.md](SAMPLE_WORK.md)，包含示範 brief、五份成果及七篇全文。只放在**獨立 demo Project**；**不要與真實客戶** brief 或規則一起上傳，以免示範資料混入客戶工作。這不是完成真人、平台 UI 或業務學習驗證的證據。

## 4. 邀請同事、分任務對話
在當前方案介面確認能邀請的明確成員及適當最低權限，再邀請；不推薦公開連結存取客戶專案，不捏造按鈕名稱或方案上限。每個任務獨立對話，附 TASK_BOARD 任務卡。分享最終成果及當前品牌規則由指定維護者**人工**更新，先鎖版本，避免過時檔或同時覆蓋。兩人以上協作是操作協定，不是已做真人測試；同 Project 不代表讀到同一聊天或即時同步檔案。

## 核准的唯一流程
真人 owner/reviewer 尚未指定就標 UNASSIGNED。先改本輪稿，後記 Candidate Lesson；指定 reviewer 的精確決定語法：`Accept CL-001 v1` / `Revise CL-001 v1` / `Reject CL-001 v1`。真人維護者核對證據後手動更新 CURRENT_RULES。這是流程約定，不是技術 ACL；自稱姓名不構成身份驗證。初始已核准業務經驗 0，無發布、寄信、CRM、cron、API daemon 或 SSO 變更。
