"""Core logic for Calc Remove Duplicates.

Python port of the original ``RemoveDuplicates.xba``: resolve the cell
selection, show the options dialog and compact the selected range by
removing rows that are duplicates over the chosen columns.
"""

import time
import traceback

import uno

import easymacro as app

from rdi18n import _

import rddialog

_CELL_DELETE_UP = uno.Enum("com.sun.star.sheet.CellDeleteMode", "UP")


def run():
    try:
        _run()
    except Exception:
        app.msgbox(_("An error occurred! ") + "\n\n" + traceback.format_exc())


def _run():
    doc = app.active
    if doc is None or doc.type != "calc":
        return

    controller = doc.obj.getCurrentController()
    sel = doc.obj.getCurrentSelection()

    if not sel.supportsService("com.sun.star.sheet.SheetCellRange"):
        app.msgbox(_("Do not support multiselection"))
        return

    source = sel.getRangeAddress()

    if sel.supportsService("com.sun.star.sheet.SheetCell"):
        if not _extend_single_selection(sel, controller):
            return
    elif not _clip_selection_to_used_area(sel, controller):
        return

    dlg = rddialog.RemoveDuplicatesDialog(doc, do_remove)
    if dlg.execute() == 0:  # Cancel/error -> restore original selection
        sheet = doc.obj.getCurrentSelection().Spreadsheet
        controller.select(sheet.getCellRangeByPosition(
            source.StartColumn, source.StartRow,
            source.EndColumn, source.EndRow))


def _extend_single_selection(sel, controller):
    cursor = sel.Spreadsheet.createCursorByRange(sel)
    cursor.collapseToCurrentRegion()
    if cursor.Columns.Count == 1 and cursor.Rows.Count == 1:
        app.msgbox(_("Please select a range"))
        return False
    controller.select(cursor)
    return True


def _clip_selection_to_used_area(sel, controller):
    addr = sel.getRangeAddress()
    modified = False
    cursor = sel.Spreadsheet.createCursor()
    cursor.gotoStartOfUsedArea(False)
    used = cursor.getRangeAddress()
    if addr.StartColumn < used.StartColumn:
        addr.StartColumn, modified = used.StartColumn, True
    if addr.StartRow < used.StartRow:
        addr.StartRow, modified = used.StartRow, True
    cursor.gotoEndOfUsedArea(False)
    used = cursor.getRangeAddress()
    if addr.EndColumn > used.EndColumn:
        addr.EndColumn, modified = used.EndColumn, True
    if addr.EndRow > used.EndRow:
        addr.EndRow, modified = used.EndRow, True
    if (addr.StartColumn > addr.EndColumn or addr.StartRow > addr.EndRow or
            (addr.StartColumn == addr.EndColumn and addr.StartRow == addr.EndRow)):
        app.msgbox(_("Please select a range"))
        return False
    if modified:
        controller.select(sel.Spreadsheet.getCellRangeByPosition(
            addr.StartColumn, addr.StartRow, addr.EndColumn, addr.EndRow))
    return True


def _row_key(row, cols):
    return "\x01".join(str(row[i]) for i in cols)


def _cell_address(sheet, col, row):
    a = uno.createUnoStruct("com.sun.star.table.CellAddress")
    a.Sheet = sheet.RangeAddress.Sheet
    a.Column, a.Row = col, row
    return a


def _cell_range_address(sheet, sc, sr, ec, er):
    a = uno.createUnoStruct("com.sun.star.table.CellRangeAddress")
    a.Sheet = sheet.RangeAddress.Sheet
    a.StartColumn, a.EndColumn = sc, ec
    a.StartRow, a.EndRow = sr, er
    return a


def _move_cells(sheet, sc, sr, ec, er, new_row):
    sheet.copyRange(_cell_address(sheet, sc, new_row),
                    _cell_range_address(sheet, sc, sr, ec, er))


def _remove_cells(sheet, sc, sr, ec, er):
    sheet.removeRange(_cell_range_address(sheet, sc, sr, ec, er), _CELL_DELETE_UP)


def do_remove(c):
    """Run the dedup. Returns 1 on success, 0 on cancel/error."""
    start = time.time()
    result = cancelled = modified = False
    doc = c.doc.obj
    sel = doc.getCurrentSelection()
    addr = sel.getRangeAddress()
    data = sel.getDataArray()
    cols = c.selected_positions

    first_row = 1 if c.has_title else 0
    last_row = len(data) - 1

    doc.lockControllers()
    doc.addActionLock()
    undo = doc.getUndoManager()
    undo.enterUndoContext("Remove Duplicates")
    try:
        c.progress_range(first_row, last_row)
        sheet = sel.Spreadsheet
        seen = set()
        last_done = first_row - 1
        n_unique = 0
        for pos in range(first_row, last_row + 1):
            key = _row_key(data[pos], cols)
            if key in seen:  # duplicate
                if n_unique > 0:
                    if n_unique < (pos - first_row):
                        _move_cells(sheet, addr.StartColumn,
                                    addr.StartRow + pos - n_unique,
                                    addr.EndColumn, addr.StartRow + pos - 1,
                                    addr.StartRow + last_done + 1)
                        modified = True
                    last_done += n_unique
                    n_unique = 0
            else:  # unique
                seen.add(key)
                n_unique += 1
            if pos > first_row and pos % 100 == 0:
                if c.is_cancelled:
                    cancelled = True
                    break
                c.progress_step(100)
                c.pump()

        if not cancelled:
            end = last_row + 1
            if n_unique > 0:
                if n_unique < (end - first_row):
                    _move_cells(sheet, addr.StartColumn,
                                addr.StartRow + end - n_unique,
                                addr.EndColumn, addr.StartRow + end - 1,
                                addr.StartRow + last_done + 1)
                    modified = True
                last_done += n_unique
            if last_done < last_row:
                _remove_cells(sheet, addr.StartColumn,
                              addr.StartRow + last_done + 1,
                              addr.EndColumn, addr.StartRow + last_row)
                modified = True
            c.progress_set(last_row)
            doc.getCurrentController().select(sheet.getCellRangeByPosition(
                addr.StartColumn, addr.StartRow,
                addr.EndColumn, addr.StartRow + last_done))
            result = True
    except Exception:
        result = False
    finally:
        undo.leaveUndoContext()
        doc.unlockControllers()
        doc.removeActionLock()

    message = _build_message(result, cancelled, modified, start,
                             first_row, last_row, last_done)
    app.msgbox(message)
    if (not result) and modified:
        undo.Undo()
    return 1 if result else 0


def _build_message(result, cancelled, modified, start,
                   first_row, last_row, last_done):
    secs = int(round(time.time() - start))
    message = _("Finished in ") + str(secs) + _(" seconds.") + "\n"
    if result:
        total = last_row - first_row + 1
        dup = last_row - last_done
        if dup > 0:
            message += (_("We found and deleted ") + str(dup) +
                        _(" duplicated values.") + "\n" +
                        _("Now we have only ") + str(total - dup) +
                        _(" unique values."))
        else:
            message += _("No duplicates found.")
    else:
        message += _("Cancelled. ") if cancelled else _("An error occurred! ")
        message += (_("The changes will now be undone.") if modified
                    else _("No changes have been made."))
    return message
