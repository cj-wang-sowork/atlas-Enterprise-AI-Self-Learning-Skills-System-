# Learning Loop（人工核准的學習迴圈）

Status: v0.1 手動範本。沒有任何自動學習功能。

## 這不是什麼

這不是自動學習、不是模型更新，也不是跨對話記憶。模型本身不會因為這些檔案而改變。
它只是一套讓「真人」把實際成效記下來、審核、核准後，再交給模型重用的流程。

## 迴圈（五步）

1. Record：真人在貼文實際發佈後，把數據填進 LEARNINGS.md。未發佈的稿件不算。
2. Review：每週用 WEEKLY_REVIEW.md 的提示，請模型依 M05 方法整理資料。
3. Propose：模型只能提出 HYPOTHESIS（候選假設），不能自行核准。
4. Approve：真人在 REVIEW_LOG.md 記錄決定，把通過的規則寫入 APPROVED_RULES.md。
5. Reuse：把 APPROVED_RULES.md 與 LEARNINGS.md 連同客戶資料檔上傳到 Project，下次產出時只套用 APPROVED 規則。

## 檔案

| 檔案 | 用途 |
|---|---|
| LEARNINGS.md | 成效紀錄表（原始數據、定義、期間、來源） |
| APPROVED_RULES.md | 已由真人核准的規則（附證據與版本） |
| WEEKLY_REVIEW.md | 每週回顧流程與提示 |
| REVIEW_LOG.md | 核准／退回的決策紀錄 |

## 在 ChatGPT 或 Claude Project 使用

1. 上傳 APPROVED_RULES.md、LEARNINGS.md 與該客戶的 CLIENT_CONTEXT.md。
2. 每週依 WEEKLY_REVIEW.md 回顧一次。
3. 有規則被核准後，重新上傳更新後的檔案（舊版要換掉，避免版本衝突）。

## 規則的最低門檻

- 至少 2 篇可比較的已發佈貼文，才能提出候選假設。
- 相關不等於因果；規則要寫成「下次測試」，不是「已證實」。
- 未知不等於 0；沒有取得的數據標 X。

## 資料與隱私

- 一個客戶一份獨立檔案；不要把客戶資料放進公開 repo。
- 不放密碼、金鑰、顧客個資。
- 手動分檔不是技術上的隔離保證。

## 升級路徑

- Level 1（本資料夾）：手動紀錄與每週回顧。
- Level 2：唯讀匯入平台洞察資料（連接器尚未驗證）。
- Level 3：平台端後台（例如 OnBrand／SoWork），內建核准關卡。

## 限制

- 需要真人持續填寫與核准。
- 樣本很小時，結論只是候選假設。
- 這些範本尚未在真實客戶上驗證成效。
