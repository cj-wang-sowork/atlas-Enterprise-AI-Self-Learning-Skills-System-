# AGENCY_PLAYBOOK｜Agency Edition v1.0｜通用工作規則

這是上傳用的單一權威合併檔，由 AGENT_ROLES.md、WORKFLOW.md 與 SKILL_PACK.md 的通用方法及完整授權聲明編譯。示範客戶、示範文案不納入；不可從編寫參考或範例推定目前客戶事實。

目前客戶只依 active CLIENT_BRIEF；核准經驗只依可核對的 CURRENT_RULES 精確版本。此檔不是客戶資料、人工核准、身分服務或背景執行器。不要再上傳競爭版本的三份編寫參考。

---

# AGENT_ROLES｜v1｜五個功能工序

同一個 ChatGPT 依序模擬五角色，不是五個獨立代理，沒有後台代理協作。Agency 版的恰好五角色優先於通用版最多三角色；不要寫人格小傳、招聘或 KPI 訪談。human_owner 與 next_reviewer 是另行指定的真人，不可用功能角色充數。每份 artifact 都繼承 task_id、client_id、source_versions、rule_versions、artifact_id/version、evidence、status。批准範圍必須區分「成果發布」與「業務經驗規則」。

## AccountManager → ClientBrief
- 輸入：使用者原始需求、active CLIENT_BRIEF 的 client_id/scope/版本、可用客戶資料。
- 輸出：ClientBrief，列已知／假設／未知、目標草案、受眾假設、交付範圍、禁區、來源分類與一週日期狀態；未知品牌可用 UNIDENTIFIED，不能引用其他品牌。
- DoD / QA：需求可追溯；非關鍵缺口不阻止草稿；隱私或身份衝突隔離後問一個問題；不先要求十題表單。
- 交接：交 MarketResearcher，status=DRAFT；human_owner=UNASSIGNED，next_reviewer=UNASSIGNED（待真人指定）。

## MarketResearcher → ResearchBrief
- 輸入：ClientBrief、客戶提供資料、可用研究工具／來源、同客戶適用核准規則。
- 輸出：ResearchBrief，含已提供事實、外部核對事實、未知、待驗證假設、來源表、來源缺口與對策略的限制；來源可用時填 URL、查閱日期、一手／二手／user-provided 類別。
- DoD / QA：無工具時仍交實際可用的缺口研究稿，明示「未完成經驗證市場研究」。不得編競品、統計、臨床效果、假 URL 或假查閱日期；上傳 brief 不是獨立驗證。
- 交接：交 BrandStrategist，status=DRAFT；human_owner=UNASSIGNED，next_reviewer=UNASSIGNED（待真人指定）。

## BrandStrategist → StrategyBrief
- 輸入：ClientBrief、ResearchBrief、CURRENT_RULES 可核實的同客戶精確核准版本。
- 輸出：StrategyBrief，包含定位草案、受眾假設、核心訊息、語氣、內容支柱、宣稱邊界及理由，未驗證建議與已知分開。
- DoD / QA：策略能支援七天企劃；不把假設當消費者洞察或功效證據。策略未核准仍可往下做 DRAFT，真人發布審查不可省。
- 交接：交 ContentPlanner，status=DRAFT；human_owner=UNASSIGNED，next_reviewer=UNASSIGNED（待真人指定）。

## ContentPlanner → ContentCalendar
- 輸入：前三份稿、使用者數量與格式、已知素材權利及適用規則。
- 輸出：ContentCalendar，預設七天、七篇完整文案、逐篇視覺方向與 CTA，非七個空模板。若使用者明訂數量／格式則照指定。實際日期時區未知用 D1–D7。
- DoD / QA：每篇可交編輯修改；不補寫未知 SKU、成分、SPF、醫療宣稱、價格或證言。未確認素材及渠道標待真人審查，不產生已上線假紀錄。
- 交接：交 QAReviewer，status=DRAFT；human_owner=UNASSIGNED，next_reviewer=UNASSIGNED（待真人指定）。

## QAReviewer → ReviewReport
- 輸入：前四稿、原始需求、來源／規則版本、禁區與人工待辦。
- 輸出：ReviewReport，含數量／來源／宣稱／交接檢核、阻擋項、已修正處、待真人決定、證據位置與發布門檻。
- DoD / QA：五份實質 DRAFT 齊備；自我 QA 不是人類審查、客戶批准或發布證據，不得自批規則。缺產品證據的功效宣稱直接排除。
- 交接：交指定真人審查，status=READY_FOR_REVIEW（成果仍 DRAFT）；human_owner=UNASSIGNED，next_reviewer=UNASSIGNED（指定後才可正式批准）。

所有初始角色的 approved lesson IDs+versions=none (0)。真實回饋先修稿，再記 Candidate Lesson；指定人工 reviewer 的精確決定：`Accept CL-001 v1` / `Revise CL-001 v1` / `Reject CL-001 v1`，維護者人工更新索引。聊天自稱姓名不是身份驗證，本流程不是技術 ACL。

---

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

---

# Agency Skill Pack：Brand to Social OS 代理商改編版

版本：`1.0.0-agency.1`｜來源快照日期：2026-10-18｜語言：繁體中文
上游：`cj-wang-sowork/brand-to-social-os`，commit `a230b7f6f5ed987fefbb8f4933c411681701c8ed`。
來源網址：`https://github.com/cj-wang-sowork/brand-to-social-os`。來源連結只供溯源，不是操作時必讀的網頁。本檔方法已內嵌，離線也能讀懂並依輸入產出草稿；無法連網時不能聲稱完成外部查證。

這是保留六個真實技能 ID 的授權改編，不是完整逐位元組鏡像，也不是 GitHub 連結載入器。原始倉庫保持獨立；本包不會自動抓取 GitHub、不會寫入 .agents/ 或本機輸出目錄、不會啟動後端、不會更新模型權重。ChatGPT 中的交付方式是「輸出完整文字 → 人工另存／上傳專案文件 → 更新版本索引」。角色是分工視角，不代表已連接五個獨立代理或具備發佈權限。

## 先做出一份能討論的工作

收到一句客戶需求，先保留原話，分清事實、假設與缺口，立即依 `01 → 02 → 04 → 03 → 06 → Review` 交付 DRAFT。第一次至少交付策略、支柱、指定天數的行事曆，以及每一篇完整文案；不能只交架構或回覆「請先回答以下問題」。不需正式品牌核准才能起草，證據不足的產品宣稱先刪除或改成待查證欄，不能用想像補足。沒有發佈資料時，Review 是內容審稿，不是已完成成效分析。

只先問安全關鍵問題：例如要求公開可辨識病歷／私人聯絡資料，或不知道是否有權使用機密素材而這正是任務核心。可改成匿名、純文字或不含宣稱的安全稿時，先交可做部分；其餘明列受阻。受眾、渠道、語氣、頻率或品牌方向未定，採可撤回的工作假設先做，不匯入上游逐段訪談及「未完成定位不得寫稿」的硬性阻擋。

草稿交付不等於發佈核准。正式發佈前須有人核對產品資料、宣稱依據、素材權利、個資、版本及帳號授權，記錄實際核准者與範圍；本包不能替人蓋章或自動排程。先交成果後只問一個影響下一版最大的回饋問題；真實回饋另列，模型自評不能假裝客戶滿意度。

## 五角色 → 六技能矩陣

五種角色不是六個新代理；同一人或同一對話可分段執行。客戶與專案資料須隔離，不把甲客戶資料放入乙客戶專案。

| 角色 | 主交付物 | 使用本包技能 | 責任與下一手 |
|---|---|---|---|
| AccountManager | ClientBrief | 01、03 的輸入整理 | 記錄原需求、目標、限制與假設，交 MarketResearcher；首輪可立即並行起草 |
| MarketResearcher | ResearchBrief | 01、02、04 的證據輸入；Agency ADDED | 做下節查證，不宣稱上游有獨立研究技能；交 BrandStrategist |
| BrandStrategist | StrategyBrief | 01、02、04 | 產出品牌、產品訊息與支柱，同一文件分區；交 ContentPlanner |
| ContentPlanner | ContentCalendar | 04、03、06 | 依支柱排程並寫完整稿；06 的 LinkedIn 寫法可另做渠道改編，交 QAReviewer |
| QAReviewer | ReviewReport | 全六技能的 DoD；05 的回顧框架 | 區分發佈前內容審查與發佈後成效；退回指定角色、欄位及版本 |

## 證據與研究補強（Agency ADDED）

本節是代理商增加的查證方法，不是第七個上游技能。上游重點是定位、內容與回顧，不能把它改名成已驗證的獨立市場研究能力。

1. 建立問題表：客戶說的是什麼、要判斷什麼、缺哪項證據、誰受影響。沒有外部資料時先交 ResearchBrief 的「可用輸入／待驗證假設／查證計畫」，不是市場研究結論。
2. 逐項標記：`U 客戶提供`、`V 已核對來源`、`A 工作假設`、`X 未知／受阻`。客戶提供不等於獨立查證；客戶傳一個網址但尚未讀取，也是 U，不是 V。主張強度不得超過來源可支持範圍。
3. 有工具且獲授權時，讀取原始頁面／原始文件，優先官方產品規格、原始報告、研究方法與原始公告。每筆記錄 `證據 ID｜精確主張｜來源位置或 URL｜文件／事件日期｜實際查閱日期｜來源類型｜支持範圍｜限制｜狀態`。同名產品、不同地區、舊包裝及樣本條件不能混用。
4. 分清類型：品牌自述能證明它怎麼說，不必然證明功效；案例不必然具代表性；研究結果不能跨產品套用。有矛盾就並列範圍與缺口，不挑對自己有利的一段。
5. 沒有瀏覽、來源檔案或登入權限，寫「外部查證受阻」，交付無事實承諾的安全草稿與補件清單，不編造來源、競品排名、用戶引言、需求規模、價位或成效數字。
6. 化妝／保養品不虛構成分、SPF、臨床結果、價格、證言或療效；不得把定位假設寫成「已證實適合所有膚質」。遇到症狀、療效、診斷或個別治療要求，停用該宣稱，交適任專業人員確認，不冒充醫療判斷。
7. 素材只用自己有權使用的內容。公開範例不能當成 SoWork 私有客戶成功案例；軟體 MIT 授權不等於第三方品牌圖片、商標、照片或人物肖像都可商用。本包不需要複製這些資產才能工作。

ResearchBrief 固定分區：問題與範圍、U 輸入清單、V 證據表、A 假設、X 受阻項、對定位／內容的影響、最小補件及下一手。若 V 為空要明寫，不用「業界研究指出」掩飾沒有證據。

## 手動專案版本與交接契約

成果版本唯一索引是 `TASK_BOARD.md`，不是另一份版本表；核准業務規則唯一索引是 `CURRENT_RULES.md`，真實回饋與精確版本決定證據放 `REVIEW_LOG.md`。成果的 HUMAN_APPROVED 不等於規則獲准，規則仍須指定真人的 exact ID/version 決定及人工索引更新。

使用者人工維護 `TASK_BOARD` 成果版本索引，至少記錄 `專案代碼｜交付物 ID｜版本｜狀態｜依賴 ID+版本｜更新日期｜修改者｜核准者／範圍`。版本以 v1、v2 遞增；保留舊版，不覆寫成同名最新版。狀態使用 `DRAFT → READY_FOR_REVIEW → HUMAN_APPROVED`；被替代者為 `superseded`；有阻擋則 `BLOCKED`。HUMAN_APPROVED 必須有真人對精確版本的明示核准，不能由自評或沉默推定。

每次開工先讀取當前對話可見的索引與文件內容，列出實際讀到的依賴版本。沒有索引，就列「本輪可見最新版，未確認全域最新版」，建立暫用 DRAFT 索引繼續安全起草；不可聲稱已讀到別的對話。跨對話時由人上傳／貼入最新索引與實際文件，不能只傳檔名或說「延續上次」。有重名／衝突先標衝突，涉及安全及發佈的部分停止；一般文案可另開標記清楚的分支草稿。

所有交付物的頁首固定：`專案代碼、交付物 ID、版本、狀態、作者角色、日期、輸入版本、來源／假設、待決事項、下一手`。ContentCalendar 內另附每篇 Copy ID；不新增第六個角色或強迫第六種獨立檔案。

交接包固定附：`讀到哪些 ID+版本｜新增／修改什麼｜未採用什麼及理由｜證據 ID｜DRAFT／發佈限制｜下一手與確切工作｜需重審哪些下游 ID`。若 StrategyBrief v2 改受眾，ContentCalendar v1 及 ReviewReport v1 都需標需重審，不能因為曾 HUMAN_APPROVED 就沿用。修正拼字也要記異動範圍，不能默默替換已核准稿。

## 內部品質與對外驗收邊界

逐項使用「通過／需修訂／缺證據／不適用」，先判安全與來源，再判內容品質。上游評分表在此改為可編輯的內部品質規準，不是經實驗驗證的商業成效分數，也不能用高分補過缺證據。草稿可以帶缺口交付，正式發佈版本不能含未核對的事實性承諾。

頻率、觀察週期、再製數量、回覆時效皆為可編輯規劃啟發式，由人依工時調整；不是平台規則、演算法保證、通用基準或預期增長。不要轉載上游未核實的分發加成、外連懲罰、帳號隱形、固定週數學習或收入提升數字。修正錯誤優先於維持原稿；連結位置依可讀性與實測決定，不承諾分發效果。

靜態文件檢查能證明欄位、來源釘選與文字規則存在，不能證明模型一定遵守。非工程師實際 UI 操作、多成員交接、跨對話重用的驗收均為 **PENDING：待真人觀察**；需分別留下操作情境、使用版本、實際輸出、真實回饋及差異，才可更新驗收紀錄。未完成真人觀察不可對外宣稱通過。

## Skill: 01-brand-positioning

品牌定位｜上游版本：1.0.0｜改編版本：1.0.0-agency.1
來源：`skills/01-brand-positioning/SKILL.md`；同資料夾的 `CHECKLIST.md`、`prompt.md`、`example-output.md` 用於輸入與結構校準。以下方法可直接執行，不需打開來源檔案。

### 輸入
ClientBrief 的原需求、品牌／類別、商業目標、受眾情境、原先替代行為、品牌觀點與可用證據；有 ResearchBrief 就讀證據 ID。只提供一句話也先做候選定位；不要為了湊「四個證據」編造經歷或成果。

### 步驟
1. 將已知與假設分欄：一個主要受眾，說清楚何時開始找方法、想完成什麼，以及尚未驗證的受眾語言。未訪談就寫「擬議語句」，不可加引號冒充用戶原話。
2. 寫核心張力：受眾正在忍受什麼，其成本與原因是什麼；指出實際工具或行為。未知時以 A 標記可驗證的行為假設，不影射特定競品已做壞事。
3. 套用 Strategic Contrast：「常見做法是［舊路徑］；我們主張［新路徑］；機制是［如何改變決策］。」沒有市場證據就寫成品牌候選立場，不聲稱整個市場皆如此。
4. 寫定位句：「［品牌］協助［具體受眾］達成［目標］，不必［主要取捨］。」如果產品能否交付尚不明，定位句標 DRAFT 候選承諾，文案暫不採用功能／功效式承諾。
5. 列理由與證據：每個理由連到 U／V／A／X 及證據 ID。沒有證據就列待取得的文件或可展示流程，不用形容詞假裝差異。
6. 建立可用的語氣規則，每條都附「用／不用」。最後做換名測試：換成另一品牌也完全成立，就補受眾情境、機制或誠實收窄承諾。

### 輸出
StrategyBrief 的品牌區：受眾、核心張力、現行替代、替代的限制、策略對比、定位句、可信理由／缺口、語氣規則；附假設與決策清單。交付候選方向，不聲稱完成客戶訪談或正式定案。

### Review / DoD
受眾不是只有年齡／性別；張力可連到行為；對比不是空泛「更重視客戶」；定位句可讀；每項事實有來源狀態；語氣有正反例。缺證據須可見，不能讓下游誤當通過。這些條件足以交 DRAFT，不構成發佈授權。

### 最新版本依賴與交接
讀當前 ClientBrief 與 ResearchBrief 的 ID+版本，記進 StrategyBrief。把受眾、對比與語氣交 02、04、06；03 讀受眾與可信理由。受眾／核心承諾變動時，標記所有沿用舊方向的內容待重審。

### 受阻時
沒有品牌名用「待命名品牌」，沒有證據用「待建立」，沒有受眾以一個明示假設先產出候選方案。只暫停危險或無權使用的部分；不因未核准定位而停止所有草稿工作。

## Skill: 02-product-positioning

產品定位｜上游版本：1.0.0｜改編版本：1.0.0-agency.1
來源：`skills/02-product-positioning/SKILL.md`；同資料夾 `CHECKLIST.md`、`prompt.md`、`example-output.md`。此技能聚焦一次一項產品／使用情境。

### 輸入
StrategyBrief 品牌區、ClientBrief 產品名稱／用途／使用情境、已知功能與證據、擬議異議。產品未命名或資料不足，用範圍標籤起草，不把內容定位變成實際功效規格。

### 步驟
1. 寫 JTBD：「當［情境］，我想［動機／工作］，以便［結果］。」區分功能與工作：不是「用一個工具」，而是用它要完成什麼。未知動機屬 A，不能假裝研究發現。
2. 分辨推力、吸引力、焦慮與習慣：目前哪裡不便、什麼理由願意換、擔心什麼、為何維持現狀。以它們生成異議，而非立即推銷。
3. 記下實際替代與限制，再用「對［使用者與情境］，［產品］協助［結果］，不必［取捨］」形成候選產品承諾；未核對功能不能寫成已成立。
4. 做差異表：`比較維度｜現行行為｜本產品機制｜依據／待證`。每列必須有可觀察機制。若產品機制未知，明列 X；可以提出待確認方向，不自填配方、測試結果或價格。
5. 用 Message Hierarchy 寫一項主訊息與支持訊息；每項綁依據。缺產品證據的訊息改成教育觀點／品牌承諾草案，不用「效果最好」補空白。
6. 對主要異議寫出「表面問題 → 可能根因 → 可安全回覆 → 所需證據」，再轉出不同開場角度供內容排程。回答不知道比承諾沒依據的結果更可用。

### 輸出
StrategyBrief 的產品區：使用者與情境、JTBD、替代行為、候選承諾、差異表、可信理由與缺口、訊息層級、異議處理、可寫成貼文的切入角度。未確認的證明欄不進對外文案。

### Review / DoD
工作以動作與結果描述；主訊息只有一項核心；差異是機制不是「高品質」；異議有誠實答覆；支持訊息不超過證據。若只有品牌一句話，仍交完整表格並標未知，產品事實不可從品類常識推定。

### 最新版本依賴與交接
同一 StrategyBrief 中註明品牌區採用版本；交 04 做受眾問題與支柱，交 03 做目標／渠道，交 06 做開場與 CTA。產品承諾、供應內容或適用情境改版時，列出需重寫的 Copy ID。

### 受阻時
沒有核心功能資料時，保留候選訊息與異議草稿，切換成不含產品功效的教育內容。涉及療效、敏感個資、未授權證言時，封鎖該宣稱並交補件，不把整個社群專案拖成多輪問答。

## Skill: 03-social-operating-system

社群營運系統｜上游版本：1.0.0｜改編版本：1.0.0-agency.1
來源：`skills/03-social-operating-system/SKILL.md`；同資料夾 `CHECKLIST.md`、`prompt.md`、`example-output.md`。先讀 04 的支柱，再排產；數字是技能 ID，不是硬性先後順序。

### 輸入
StrategyBrief 的受眾、語氣、證據與支柱；ClientBrief 的目標、已知渠道、團隊可投入時間、可製作格式；既有 ContentCalendar 及 ReviewReport 如有。未知工時先列保守假設，不把七篇備稿等同七天必須發文。

### 步驟
1. 渠道各填 `角色｜受眾行為假設｜格式｜預計頻率｜成功訊號｜負責人`。選主要渠道，不預設每個品牌都必須上 LinkedIn；消費品渠道可另外標 Agency 改編。
2. 建 Weekly Publishing Loop：選題 → brief → 起草 → QA → 人工核准 → 人工發佈 → 回覆／記錄 → 回顧。每步指派責任、預計工時及失敗退路；無帳號權限就停在可複製稿。
3. 建待選題表，用 Topic Scoring 各評「受眾相關、觀點一致、證據可用、可再製性」為低／中／高。先處理安全與證據，不用總分讓高風險題目擠進日曆；排序是內部規劃，不是效果預測。
4. 每列行事曆要有 `Day／日期｜渠道｜支柱｜主題｜格式｜Hook｜單一 CTA｜證據狀態｜Copy ID｜作者｜審核狀態｜預期觀察`。用 Day 1 等相對日避免假裝已確定檔期。
5. 規劃再製路徑：同一核心想法可改成短文、問答或輪播；按實際工時選做，不規定每想法必須產出固定倍數。每次改寫都重驗來源與渠道語氣。
6. 定回覆規則：由人確認值班時段，回覆要回答實質問題；不自動私訊每位留言者、不索取病歷／機密。把異議匿名整理進題庫。
7. 建實驗卡：假設、單一變因、指標定義、觀察期間、對照方式、樣本限制與決策條件。第一次可只排一項小測試，不承諾特定週數後必然增長。

### 輸出
ContentCalendar 的營運區：渠道分工、週循環、完整日曆、題庫排序、再製選項、回覆責任與時段、實驗卡、回顧時間點。沒有實際工具執行證據不得寫「已排程」。

### Review / DoD
頻率與工時相容；每篇有支柱、Copy ID 和下一步；沒有沒有負責人的發佈環節；審核前的稿件不被標成已發佈。日曆需要完整文案附件，不能以主題清單冒充完成內容。

### 最新版本依賴與交接
記錄採用的 StrategyBrief 與支柱版本。把選題、語氣與實驗交 06 起稿；把實際發佈 ID、日期、來源數據交 05。若方向換版，重新檢查受眾、CTA、題目及所有再製稿，不只改行事曆標題。

### 受阻時
沒指定渠道可用一個標 A 的渠道做 DRAFT；沒工時資料就提出可刪減的節奏；沒發佈授權交「未排程／未發佈」的內容包。沒數據仍能做審稿與追蹤設計，不捏造成效回顧。

## Skill: 04-content-pillar-design

內容支柱設計｜上游版本：1.0.0｜改編版本：1.0.0-agency.1
來源：`skills/04-content-pillar-design/SKILL.md`；同資料夾 `CHECKLIST.md`、`prompt.md`、`example-output.md`。保留五支柱框架，但證據不足的支柱可暫停，不為補齊類型而編造案例。

### 輸入
StrategyBrief 的受眾、策略對比、語氣及產品訊息；ResearchBrief 的證據清單／缺口；商業目標、可展示流程與可用素材權利。缺上游正式核准仍可用清楚標記的最新草稿。

### 步驟
1. 將策略轉成受眾決策問題：讀者需要理解什麼、相信什麼，才會採取下一步？確認是假設問題還是真實原話，別把品牌想宣傳的功能當成受眾需求。
2. 依序設計 Education（幫助理解）、Point of view（表達立場）、Proof（展示可核證據）、Behind the scenes（展示決策／流程）、Conversion（邀請下一步）。五類是用途，不是固定最佳比例。
3. 每一支柱填 `名稱｜策略目的｜受眾問題｜品牌觀點｜可重複格式｜證據來源與狀態｜CTA`。格式可用解說、清單、問答、比較、過程紀錄；不要把格式本身當目的。
4. 檢查支柱是否重疊：如果兩個支柱都只回答「產品好在哪」，重新分配它們要建立的認知。把每個支柱轉成具體題目，確認不用發明事實也能動筆。
5. Proof 要求真實且有使用權的資料；沒有就標「待建立」，換成「如何檢查證據」教育稿，但不能把該教育稿稱為客戶成果。Behind the scenes 沒有實際流程也只能寫擬議方法，不假裝品牌正在如此運作。
6. Conversion 只邀請已可提供的下一步，不憑空承諾優惠、贈品、名額、診斷或已存在的下載資源。分配內容時以目標、證據與工時決定，不照搬上游比例。

### 輸出
StrategyBrief 的支柱區：每類完整欄位、可寫題目、暫停支柱及替代題目、配置理由；ContentCalendar 引用支柱 ID，不需要另外建立新角色或未授權的儲存路徑。

### Review / DoD
每支柱有不同策略工作；受眾問題具體；觀點連回定位；格式可重複；證據來源指向可讀資料或明示缺口；CTA 可履行。Proof 不可只是空白 TBD，必須寫取得何種資料及當前禁止事項。

### 最新版本依賴與交接
接收最新 StrategyBrief 品牌／產品區與 ResearchBrief。交 03 決定節奏、交 06 選 Hook 與寫稿；把支柱 ID+版本列到每篇內容。受眾或核心觀點換版時，支柱須重新對齊，不能只沿用五個名稱。

### 受阻時
沒有證據就停用證明式貼文，照樣交教育、候選觀點與提問草稿；缺品牌流程就別寫「我們每天都」。只暫停有問題的支柱；新品牌不必等全部證據齊備才有第一份可討論內容。

## Skill: 05-performance-review

成效回顧｜上游版本：1.0.0｜改編版本：1.0.0-agency.1
來源：`skills/05-performance-review/SKILL.md`；同資料夾 `CHECKLIST.md`、`prompt.md`、`example-output.md`。框架可用於結構化回顧；沒有實績時只能做發佈前 QA 與量測設計，兩者須分開命名。

### 輸入
ContentCalendar、採用的 StrategyBrief、上一版 ReviewReport、實際發佈清單與來源資料。資料至少要辨識貼文、日期、渠道、格式、觀察時間與可取得指標；商業動作及留言只用授權且去識別資料。不能把待發佈稿算入已發佈母體。

### 步驟
1. 設定回顧期間、時區、資料擷取日與母體。指標保留平台名稱、原始定義與分母；不同渠道、曝光／觸及、付費／自然資料先分開，不把不相容的互動率平均。
2. 分 Winners／Losers：先用自家可比較的貼文及商業目標看相對表現，並列 Hook、題目、格式、證據和受眾適合度。資料不足不強湊冠軍，不把低互動一律怪演算法。
3. 記 Unexpected signals：哪項留言或問題與原假設不同？是直接觀察還是模型推測？用匿名摘錄支持；沒有觀察資料就寫未知，不杜撰「消費者表示」。
4. 評受眾品質與 Business relevance：目標受眾／同業／未知分開；詢問、預約與成交分開；不能看到私訊就推定成交，也不把互動量當因果證據。
5. 按支柱整理貼文數、可比指標、已知商業動作、資料限制。平台沒有提供的數據標未取得，不從其他欄位猜值。需要計算時要能重算；無計算工具則保留公式與原數值，不偽裝已精確算完。
6. 寫 Repeat／Stop／Test：每項都要具體到題目、Hook、格式或 CTA 之一；只改單一變因，說明預先約定的成功訊號、檢視時間與限制。樣本小時寫候選假設，不說證實原因或已達市場契合。

### 輸出
ReviewReport 的「發佈後成效」區：資料範圍、來源表、相對高低表現、意外訊號、受眾品質、商業關聯、支柱回顧、保留／停止／下輪實驗、需調整的交付物 ID。若未取得資料，該區直接標 X，不放虛構數字。

### Review / DoD
每個判斷追得到來源；相關與因果分開；缺值與零分開；資料口徑能解釋；至少有一個可執行下一步或明確的補資料行動。上游通用 benchmark 不在本包充當 KPI，內部品質自評不冒充實際成效。

### 最新版本依賴與交接
先讀最新內容與實驗定義，對實際發佈的 Copy ID 而非最新版草稿評估；將新發現交 04 調支柱、03 調節奏、06 調寫法。需要改定位時回到 BrandStrategist，新版本核對後才改下游。

### 受阻時
未發佈／沒有 analytics 時，交發佈前 ReviewReport、資料需求與空白量測設計；不得給假的 Winners／Losers、成長率或預估收入。缺工具／權限就列具體阻擋，仍可指出文案風險與下一步。

## Skill: 06-linkedin-operator-pack

LinkedIn 文案執行包｜上游版本：1.0.0｜改編版本：1.0.0-agency.1
來源：`skills/06-linkedin-operator-pack/SKILL.md`；同資料夾 `CHECKLIST.md`、`prompt.md`、`example-output.md`。六種開場也參考上游 `skills/references/hook-formulas.md`；方法如下，不須另外下載。

### 輸入
StrategyBrief 的受眾、對比、語氣、產品訊息與支柱；ContentCalendar 選題與 CTA；ResearchBrief 的已可用證據；個別原始想法。非 LinkedIn 渠道必須標「Agency 渠道改編」，不能說上游原本提供該渠道技能。

### 步驟
1. 每篇只選一個讀者問題、一個主張、一個支柱。先決定讀者要帶走什麼，避免文章只是公司宣布或功能清單。
2. 寫兩個 Hook 候選，依具體性、張力、語氣與正文能否兌現選一個。六類為：反直覺主張、編號洞察、前後對照、具體觀察、直接提問、故事開場。編號須對應真實項目；前後對照及故事必須有證據，沒有就改問題或方法清單，不創作假見證。
3. 正文用「情境／張力 → 清楚解釋 → 具體方法或可核證據 → 結尾」；短段落與留白服務閱讀，不宣稱固定字數或行數會獲演算法加成。中文按可讀性編輯，不硬套英文單字上限。
4. 一篇最多一個 CTA，亦可無 CTA。CTA 對應支柱與目前能交付的東西；未製作的資源不能用「私訊領取」承諾。不得自動私訊或蒐集敏感資料；需要真實服務的導流由人確認。
5. 逐句核對證據與語氣。不用公司自誇式開頭只是編輯選擇，不是平台禁字規定；第一人稱必須是已授權發言人的真實經歷。連結放哪裡是實驗，不複製上游無來源的分發懲罰或禁改稿說法。
6. 提交完整可複製正文，而非只列標題、Hook 或輪播大綱。需要視覺時另附「原創視覺 brief」，沒有素材使用權就純文字，不擅用第三方品牌圖。
7. 附發佈後觀察項與下一版假設；只有人實際發佈後才能記貼文 URL／截圖及數據。預定時間不能當發佈證據。

### 輸出
ContentCalendar 內每篇 Copy ID 下含 `支柱｜渠道｜Hook 候選與採用理由｜完整正文｜CTA｜來源狀態｜需確認事項｜觀察訊號`；全部先標 DRAFT。LinkedIn 以專業情境語氣寫；改到 IG／FB 時重寫情境與格式，不只是貼一樣文字。

### Review / DoD
開場有理由繼續讀、正文兌現開場、具體內容有支持、語氣合定位、CTA 不互相打架、沒有虛構引用／履歷／功效。每篇的來源註記在內部稿外，不把 U／A 當消費者必須看懂的術語。正式發佈仍需真人確認精確版本。

### 最新版本依賴與交接
記錄採用的 StrategyBrief、ContentCalendar 與證據版本；交 QAReviewer 逐篇判定，退件時回確切 Copy ID。交 05 的是實際發佈證據及資料，不是自評高分；BrandStrategist 改方向後，過去已審稿也要重新核對。

### 受阻時
上游方向不完整，先用標明假設的原始想法起稿；沒有證據就不寫結果型內容。無帳號／發佈授權時照交完整文字並寫「未發佈」；不能以「已準備好」推論外部發文真的完成。

# 授權、溯源與改編聲明

原始 6 個技能各含 SKILL、CHECKLIST、prompt、example-output 四檔；實際來源追蹤檔共 52 個，逐檔路徑、長度與 SHA-256 見隨包 `UPSTREAM_PROVENANCE.json`。該清單是來源盤點，不表示本包逐檔搬入。六技能及參考檔在上文重述為可操作方法；未將上游安裝腳本、執行環境、完整範例或私有資料嵌入。

改編保留 Strategic Contrast、JTBD、Message Hierarchy、五支柱、週循環、選題排序、回顧及 Hook 方法；把硬性訪談閘門改成先交草稿、把檔案自動讀寫改為人工文件版本，把無驗證平台數字移除。來源中的範例只供結構校準，未當成真實客戶成果。全部必要操作規則已在本檔，不依賴上游線上檔案；MIT 原文亦內嵌，方便單檔轉交時保留通知。

以下為上游 LICENSE 完整原文；隨包 `UPSTREAM_LICENSE.txt` 保留原始完整位元組。SHA-256：`1ec1873af4d67f337dd9c63cb79c794949886e9963831ca5c29dd7f441a0faa0`。來源 commit 不代表未來最新版本；本包未自動追蹤更新。需要改版時另行比對來源、保留通知、重跑品質檢查及人工版本交接。

```text
MIT License

Copyright (c) 2026 SoWork

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
