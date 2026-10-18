# ChatGPT Starter Kit 真人使用測試

**目前狀態：待真人參與。** 尚無真實非工程參與者紀錄；成功率與耗時應為空值，不得用 AI 模擬、單元測試或工具連線成功替代。

## 參與者看到的任務（不需要寫程式）

使用既有 ChatGPT 帳號與 ATLAS Starter Kit，完成一次虛構品牌的內容任務。只使用套件中的虛構資料，不上傳客戶機密、個資、帳密或公司內部文件。

1. 下載並開啟 `starter/chatgpt/`，讀取 `README.md`。
2. 在自己的 ChatGPT 帳號建立一個新的 Project。若找不到此功能或權限不足，直接告訴觀察者；不必購買或更改訂閱。
3. 將 `PROJECT_INSTRUCTIONS.md` 的內容加入該 Project 的指示。
4. 將 `SAMPLE_BRIEF.md` 的虛構品牌簡報加入同一 Project。
5. 依套件 README 的第一個任務提示，取得第一份回覆；確認沒有把未提供的數字或產品能力寫成事實。
6. 將回覆複製成文字檔，依 `OUTCOME_REVIEW_LOG.md` 留下審查紀錄。分享前移除帳號資訊及個資。

目標是觀察能否在十分鐘內完成，**不是保證十分鐘成功**。卡住、超時、失敗或中途停止都是有效結果，不需要假裝完成。

## 觀察者的固定流程

- 邀請真實、非工程背景、願意參與的人；使用 `participant-001` 之類的代號。是否為非工程背景為本人聲明，不是系統推斷。
- 先說明資料用途、同意與退出方式；未同意不建立人測紀錄。不使用 AI 代理冒充參與者。
- 確認觀察者實際見到參與過程（例如本人操作或同意的螢幕分享）。不自動錄影或上傳截圖。
- 固定 Starter Kit 版本、任務、平台與裝置條件。準備完成且參與者開始第一步時才開計時；事前說明時間另記，不偷減安裝／登入卡關時間。
- 除非安全問題，不代替參與者操作；需要提示或協助時記在獨立的去識別化觀察筆記，不把受協助成功宣稱成無協助成功。
- 六個步驟完成即記錄；卡住記 `blocked`。同一步多次卡關只算同一名參與者一次，但原事件保留。
- 成功需六步完整且實際輸出存在，觀察者核對其確實來自該次任務，才提供文字證據檔。程式只驗證檔案與敏感資料、計算摘要，不能證明回覆真的來自 ChatGPT。
- 十分鐘時記錄當時狀態；可繼續測，但較晚成功不能算「十分鐘內成功」。中途離開以 `abandoned` 結案；未結案及失敗仍留在分母。
- 每人同一研究只記首次嘗試。重試、不同版本或不同平台使用另一份明確標示的研究，不混算成功率。

## 可實際執行的紀錄器

從完整原始碼 checkout 執行；觀察者需要 Python 3.9+，**參與者不需要終端機**。本工具不會登入、操作或設定 ChatGPT，也不會自行確認真人身分。

先選擇個人可寫且受保護的資料夾；不要把資料放進 Git。下列使用 shell 的 `$HOME` 範例，`--starter-revision` 應填當次實際核對的固定版本。

```sh
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" start participant-001 \
  --kind human --background non_engineer --consent --observer observer-001 --attested \
  --runtime ChatGPT --starter-revision 8cb5eed2
```

`--consent` 與 `--attested` 是觀察者對已發生事實的聲明，不是取得同意的替代品。僅在真人實際同意且觀察者確實見到參與時使用。回傳的 `session` 代碼用於後續指令。

```sh
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" step SESSION download_kit --status completed
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" step SESSION create_project --status completed
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" step SESSION add_instructions --status completed
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" step SESSION attach_brief --status completed
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" step SESSION complete_first_task --status completed
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" step SESSION save_result --status completed
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" finish SESSION --outcome success --evidence /physical/path/to/sanitized-output.txt
python3 -m evaluation.usability --db "$HOME/.atlas-study/private/study.sqlite" report
```

若卡關，以該步驟 `--status blocked` 記錄；無法繼續則 `finish SESSION --outcome blocked`，自行離開則用 `abandoned`。不要為了讓紀錄成功而補填未實際完成的步驟。

## 數據口徑與限制

- 人測分母只包含 `human`、`non_engineer`、已同意且由觀察者聲明的首次嘗試；包含卡關及未完成者。
- 工程背景、未知背景與 `agent_qa` 不納入非工程人測成功率，也不納入其中位耗時。
- 沒有人測資料時，成功率與中位耗時為 `null`，**不是 0% 或 100%**。
- 首次參與者不能重複建立；不同平台或 Starter 版本不能放在同一份研究裡混算。
- 時間來自觀察者機器的 UTC 時鐘；倒退會拒絕記錄，但本工具不是抗竄改計時器。不同程序可重新開啟同一紀錄，不可透過測試用 `clock` 注入來製造真人耗時。
- 本機資料目錄需私有、檔案為 owner-only；SQLite 交易序列化紀錄操作。管理資料夾的可信任觀察者仍能修改資料，因此這不是數位簽章或真人身分認證服務。
- 成功證據只讀取觀察者明確指定的非空 UTF-8 文字檔（上限 1 MiB）；拒絕葉節點 symlink 與敏感內容，僅保存 SHA-256，不保存或上傳原文。所有目錄祖先、裝置與時鐘由觀察者保護。
- 截圖可另由參與者同意後去識別化保存，不由此工具自動收集。原始證據由觀察者保留並控制刪除；分享研究報告時再次檢查權限及去識別化。
- 單元測試中的虛構人測與代理 QA 只能驗證紀錄器，不是產品人測。GitHub/Codex/ChatGPT 的工具通知、模型輸出、同意欄位本身皆不是已招募的真人。

## 待實際填寫的驗收

- 非工程真人數：待招募。
- 十分鐘內成功人數／首次參與者：尚未測得。
- 成功率、中位耗時：尚未測得。
- 主要卡關步驟、需要協助的內容：待真人觀察。

至少完成一位真實參與者的流程及輸出核對，才可說已完成「真人試用」；代表性成功率與穩定可用性仍需更多樣本，不能從一人推論所有使用者。
