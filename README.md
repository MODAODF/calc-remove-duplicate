# Calc Remove Duplicates

A LibreOffice Calc extension that removes duplicate rows within a selected
cell range.

Customized from <https://extensions.libreoffice.org/en/extensions/show/remove-duplicates-fast>.

Originally written in StarBasic, this extension has been rewritten in Python
(via [easymacro](https://easymacro.cuates.net/), developed by Mauricio Baeza) and
localized with gettext (en / ru / zh_CN / zh_TW).

## Usage

1. In Calc, select a cell range (or click a single cell inside a data block).
2. Open the dialog from any of these entry points:
   - The "Remove Duplicates…" button at the end of the **standard toolbar**
   - **Data** menu → "Remove Duplicates…" (after "Filter")
   - **Right-click** on the selection → "Remove Duplicates…"
3. In the dialog, tick the columns used to detect duplicates; if the first
   row of the selection is a header, tick "Selection includes title".
4. Click "OK" to run; you can press "Cancel" mid-progress to interrupt
   (any changes already made are undone automatically).

## Build

```sh
make        # compile the .mo files and package the .oxt
make pot    # re-extract locales/calc-remove-duplicates.pot from the sources
make mo     # recompile the .mo files for the three locales
```

See [developer.md](developer.md) for the source layout and program flow.

---

# Calc Remove Duplicates

LibreOffice Calc 延伸套件：移除選取儲存格範圍中重複的列。

Customized from <https://extensions.libreoffice.org/en/extensions/show/remove-duplicates-fast>。

本套件原以 StarBasic 撰寫，現已改寫為 Python（透過 Mauricia Baeza 所開發之 [easymacro](https://easymacro.cuates.net/)），
並以 gettext 進行多語化（en / ru / zh_CN / zh_TW）。

## 使用方式

1. 在 Calc 中選取一個儲存格範圍（或在資料區內點一個儲存格）。
2. 以下任一入口皆可開啟對話框：
   - **標準工具列**最後面的「移除重複項…」按鈕
   - **資料**選單 →「篩選」之後的「移除重複項…」
   - 在選取範圍上**按右鍵** →「移除重複項…」
3. 在對話框中勾選要做為判重依據的欄；若選取範圍第一列是標題，勾選「選取區域包含了題名」。
4. 按「確定」執行；可在進度進行中按「取消」中斷（已變更會自動還原）。

## 建置

```sh
make        # 編譯 .mo 並打包成 .oxt
make pot    # 從原始碼重新抽出 locales/calc-remove-duplicates.pot
make mo     # 重新編譯三個語系的 .mo
```

詳細的程式結構與流程見 [developer.md](developer.md)。
