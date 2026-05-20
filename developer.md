# 開發者文件

本檔說明 Calc Remove Duplicates 的原始碼結構與主要流程。

> 觀念：本 extension 是註冊在 LibreOffice 內的兩個 **UNO 服務**。`Addons.xcu`
> 把工具列按鈕、資料選單項目都指向 service URL
> `service:org.ossii.CalcRemoveDuplicates.do`；LibreOffice 取得該 URL 後建立
> `main.py` 中的 `MainJob` 並呼叫其 `trigger()`，由此進入 Python 邏輯。
> 另一個服務 `ContextMenuJob`（`jobs.py`）由 `Jobs.xcu` 綁在 `OnLoad` / `OnNew`
> 事件，於每份 Calc 文件註冊右鍵選單攔截器。

## 檔案／目錄總覽

```
calc-remove-duplicate/
├── Addons.xcu                  ← UI 註冊：標準工具列(AddLast)、資料選單、Images
├── Jobs.xcu                    ← 把 ContextMenuJob 綁到 OnLoad / OnNew 事件
├── description.xml             ← extension 中介資料（identifier、版本、授權）
├── META-INF/manifest.xml       ← OXT 內檔案的 media-type 註冊
├── Makefile                    ← 打包 .oxt、產生 .pot / 編譯 .mo
├── update_version.sh           ← Makefile 呼叫，把 VERSION 寫進 description.xml
├── VERSION
├── icons/                      ← 工具列圖示（16x16, 26x26 bmp/png）
├── pkg-desc/                   ← 安裝時顯示的多語描述
├── registration/gpl-3.0.txt    ← 授權書（GPLv3）
├── locales/                    ← gettext 多語檔
│   ├── calc-remove-duplicates.pot
│   ├── ru/    calc-remove-duplicates.po + LC_MESSAGES/*.mo
│   ├── zh_CN/ calc-remove-duplicates.po + LC_MESSAGES/*.mo
│   └── zh_TW/ calc-remove-duplicates.po + LC_MESSAGES/*.mo
├── main.py                     ← UNO 進入點：MainJob (XJobExecutor)
├── jobs.py                     ← ContextMenuJob (XJob) + XContextMenuInterceptor
└── pythonpath/                 ← 安裝後自動加入 sys.path
    ├── easymacro/              ← 第三方輔助庫（vendored，GPLv3）
    ├── rdi18n.py               ← gettext bootstrap，提供 _()
    ├── rddialog.py             ← 選項對話框（含對話框內進度條）
    └── rdcore.py               ← 選取範圍解析 + 去重引擎 + run() 協調
```

### 各檔職責

| 檔案 | 職責 |
|---|---|
| `main.py` | `MainJob.trigger()` 動態 import `rdcore.run()`，註冊為 `org.ossii.CalcRemoveDuplicates.do`。 |
| `jobs.py` | `ContextMenuJob` 在 Calc view 建立時註冊 `_Interceptor`；攔截器僅在右鍵點在儲存格範圍選取上時，於選單尾端插入「移除重複項…」。 |
| `pythonpath/rdcore.py` | 對應原 `RemoveDuplicates.xba`：解析選取（單格展開目前區域／多格裁切已用範圍）、`do_remove` 去重引擎（依選取欄判重、上移壓實、移除尾列、UndoContext、可取消）、結果訊息。 |
| `pythonpath/rddialog.py` | 對應原 `Options.xdl`：欄位多選清單、含標題核取方塊、全選、確定/取消、對話框內進度條。去重引擎由 `rdcore` 注入以避免循環匯入。 |
| `pythonpath/rdi18n.py` | `gettext.translation(..., fallback=True)` 載入 locales 下 mo，export `_`。 |
| `locales/*.po` / `*.mo` | gettext 翻譯來源與編譯檔。 |

## 啟動流程

```
工具列按鈕 / 資料選單 / 右鍵選單   （URL = service:org.ossii.CalcRemoveDuplicates.do）
        │
        ▼
MainJob.trigger() → rdcore.run() → rdcore._run()
        │
        ├─ 取得選取；非 SheetCellRange → 「Do not support multiselection」
        ├─ 單格 → _extend_single_selection（仍 1x1 → 「Please select a range」）
        ├─ 多格 → _clip_selection_to_used_area（裁切至已用範圍）
        ├─ 開 RemoveDuplicatesDialog(doc, do_remove) 並 execute()
        │     └─ 按「確定」→ do_remove(controller) 在對話框開啟時執行去重
        └─ execute()==0（取消/錯誤）→ 還原原始選取範圍
```

`do_remove` 每處理 100 列檢查一次 `is_cancelled` 並 `pump()`
（`processEventsToIdle`），讓「取消」按鈕的點擊得以即時分派並中斷迴圈。

## 右鍵選單（Context Menu）的實作

LibreOffice **沒有**任何 `Addons.xcu` 節點可以直接往儲存格右鍵選單加項目，
唯一的官方途徑是 `com.sun.star.ui.XContextMenuInterceptor`。流程如下：

```
Jobs.xcu 把 ContextMenuJob 綁到 OnLoad / OnNew 事件
        │  （每開啟/新建一份文件各觸發一次）
        ▼
ContextMenuJob.execute(args)        ← jobs.py，XJob
        │  從 args 的 "Environment" 取出 Model
        │  只對 Calc 文件處理
        ▼
controller.registerContextMenuInterceptor(_Interceptor())
        │  controller = model.getCurrentController()（ScTabViewObj）
        ▼
（使用者右鍵）_Interceptor.notifyContextMenuExecute(event)
        │  event.Selection.getSelection() 是儲存格範圍才加項目
        │  用 event.ActionTriggerContainer 建 ActionTrigger + 分隔線
        │  CommandURL 指向同一個 service: URL
        └─ return CONTINUE_MODIFIED
```

`_INTERCEPTORS` 這個模組級 list 會保留每個攔截器的參考，否則 PyUNO 會把它
回收，右鍵時就再也不會被呼叫。

### 踩過的雷與避免方式

| 雷 | 症狀 | 原因 | 避免方式 |
|---|---|---|---|
| `jobs.py` 漏進 `Makefile` 的 `FILES` | 安裝成功但 Job 完全沒作用 | manifest 有註冊、檔案卻沒打包進 .oxt | 新增任何 `.py` 元件時，務必同步加到 `Makefile` 的 `FILES`。 |
| `XJob.execute` 參數解析 | 攔截器從未註冊（無錯誤可見） | `execute(self, args)` 收到的 `args` **本身就是** `sequence<NamedValue>`；誤寫 `for x in args[0]` 會迭代到單一 NamedValue 而拋例外，又被 `try/except` 吞掉 | 直接 `for arg in args:`；除錯期間先把例外記到 log，不要默默吞掉。 |
| 模組頂層 `import easymacro` | 安裝時跳 `DisposedException: Binary URP bridge disposed`（soffice 崩潰） | `unopkg` 註冊元件時會 import 該檔；easymacro 在 import 當下就呼叫 configuration provider 等 UNO 服務，在 bootstrap soffice 環境會把橋接打掛 | UNO 元件入口檔（`main.py`/`jobs.py`）頂層只 import `uno`/`unohelper` 與介面，easymacro/`rdi18n` 一律延後到「真正執行時」才 import。 |
| 事件選 `OnViewCreated` | Job 不一定被觸發 | 該事件未必經由 JobExecutor 派送 | 用最可靠的 `OnLoad` + `OnNew`（新建走 OnNew、開檔走 OnLoad，同一份文件只會中一個，不會重複註冊）。 |
| `entry.Text = "..."` | `CannotConvertException: value is not interface` | 部分 LibreOffice 版本中，PyUNO 以屬性指派設定 `ActionTrigger.Text` 會把它誤判為 interface 型別（`CommandURL` 卻正常） | 改用 `entry.setPropertyValue("Text", "...")`。 |

> 另注意：攔截器是在文件事件時註冊，**已開啟的文件需重新開啟**才會掛上；
> 開發時用 `tempfile` 寫一個 log 檔逐步追蹤 execute / notify 兩端，是定位
> 這類「無聲失敗」最快的方法。

## i18n 工作流程

1. 改完 Python 字串後 `make pot` 重新抽出 `locales/calc-remove-duplicates.pot`。
2. 將新 msgid 併入各語系 `.po` 並翻譯。
3. `make mo` 編譯成 `.mo`（執行時由 `rdi18n` 依 LibreOffice 注入的 `LANG`/`LC_*`
   環境變數選用語系；缺翻譯時 fallback 回英文 msgid）。
