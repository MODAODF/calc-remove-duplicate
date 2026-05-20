"""Options dialog for Remove Duplicates.

Faithful Python rebuild of the original Basic ``Options.xdl`` /
``RemoveDuplicates.xba`` UI: a multi-select column list, a "selection
includes title" checkbox, Select All / OK / Cancel buttons and an
in-dialog progress bar with a "Progress" label.

The actual row-removal work is injected as ``engine`` by ``rdcore`` to
avoid a circular import. ``engine(controller)`` runs while the dialog is
still open, drives the progress bar through the helpers below and polls
``controller.is_cancelled`` so the Cancel button can interrupt it.
"""

import uno
import unohelper

from com.sun.star.awt import XItemListener

import easymacro as app

from rdi18n import _


class _TitleListener(unohelper.Base, XItemListener):
    """Repopulate the column list whenever the title checkbox toggles."""

    def __init__(self, controller):
        self.controller = controller

    def itemStateChanged(self, event):
        self.controller.refresh_list()

    def disposing(self, event):
        pass


class RemoveDuplicatesDialog:
    def __init__(self, doc, engine):
        self.doc = doc
        self.engine = engine
        self.in_progress = False
        self.result = None
        self._pval = 0

        ctx = uno.getComponentContext()
        self._toolkit = ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.awt.Toolkit", ctx)

        self.d = app.dialog.create({
            "Title": _("Remove Duplicates"),
            "Width": 201, "Height": 168,
        })
        self.d.events = lambda dialog: self
        self._build_controls()
        self._add_progress_bar()

        self.refresh_list()

    # -- construction ------------------------------------------------------

    def _build_controls(self):
        self.d.add_control({
            "Type": "Label", "Name": "OptionHint",
            "Label": _("~Please select the duplicate columns "
                       "(Press Ctrl to multiselect):"),
            "X": 5, "Y": 4, "Width": 190, "Height": 9,
        })
        self.d.add_control({
            "Type": "listbox", "Name": "lbList", "MultiSelection": True,
            "X": 5, "Y": 18, "Width": 190, "Height": 87,
        })
        self.d.add_control({
            "Type": "button", "Name": "btnSelectAll", "Label": _("Select ~All"),
            "X": 8, "Y": 111, "Width": 38, "Height": 14,
        })
        self.d.add_control({
            "Type": "checkbox", "Name": "cbTitle",
            "Label": _("~Selection includes title"),
            "X": 82, "Y": 115, "Width": 110, "Height": 7,
        })
        self.d.cbTitle.obj.addItemListener(_TitleListener(self))
        self.d.add_control({
            "Type": "Label", "Name": "Label1", "Label": _("Progress"),
            "X": 93, "Y": 128, "Width": 28, "Height": 8,
        })
        self.d.add_control({
            "Type": "button", "Name": "btnOK", "Label": _("~OK"),
            "X": 86, "Y": 148, "Width": 65, "Height": 14,
        })
        self.d.add_control({
            "Type": "button", "Name": "btnCancel", "Label": _("~Cancel"),
            "X": 157, "Y": 148, "Width": 38, "Height": 14,
        })

    def _add_progress_bar(self):
        model = self.d.model.createInstance(
            "com.sun.star.awt.UnoControlProgressBarModel")
        model.PositionX = 7
        model.PositionY = 138
        model.Width = 190
        model.Height = 6
        self.d.model.insertByName("ProgressBar1", model)
        self.bar = self.d.obj.getControl("ProgressBar1")

    # -- column list -------------------------------------------------------

    @property
    def has_title(self):
        return self.d.cbTitle.value > 0

    def _column_labels(self):
        sel = self.doc.obj.getCurrentSelection()
        if self.has_title:
            first = sel.getCellRangeByPosition(0, 0, sel.Columns.Count - 1, 0)
            return [str(v) for v in first.getDataArray()[0]]
        prefix = _("Column ")
        return [prefix + name for name in sel.Columns.ElementNames]

    def refresh_list(self):
        labels = self._column_labels()
        lb = self.d.lbList.obj
        lb.setVisible(False)  # speeds up the update manyfold
        lb.removeItems(0, lb.getItemCount())
        lb.addItems(tuple(labels), 0)
        self._select_all()
        lb.setVisible(True)

    def _select_all(self):
        lb = self.d.lbList.obj
        lb.selectItemsPos(tuple(range(lb.getItemCount())), True)

    @property
    def selected_positions(self):
        return self.d.lbList.obj.getSelectedItemsPos()

    # -- progress / cancel helpers used by the engine ----------------------

    @property
    def is_cancelled(self):
        return not self.in_progress

    def pump(self):
        try:
            self._toolkit.processEventsToIdle()
        except AttributeError:
            pass

    def progress_range(self, lo, hi):
        self.bar.setRange(lo, hi)
        self._pval = lo
        self.bar.setValue(lo)

    def progress_set(self, value):
        self._pval = value
        self.bar.setValue(value)

    def progress_step(self, step):
        self._pval += step
        self.bar.setValue(self._pval)

    # -- events ------------------------------------------------------------

    def btnSelectAll_action(self, event):
        self._select_all()

    def btnOK_action(self, event):
        self.in_progress = True
        for name in ("btnSelectAll", "cbTitle", "btnOK", "lbList"):
            getattr(self.d, name).enabled = False
        self.result = self.engine(self)
        self.d.close(self.result)

    def btnCancel_action(self, event):
        if self.in_progress:
            self.d.btnCancel.enabled = False  # prevent a second Cancel
            self.in_progress = False
        else:
            self.d.close(0)

    def execute(self):
        return self.d.execute()
