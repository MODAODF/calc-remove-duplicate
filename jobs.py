#!/usr/bin/env python
"""Context-menu integration.

A document Job (bound to OnLoad / OnNew in Jobs.xcu) registers an
XContextMenuInterceptor on every Calc view. The interceptor appends a
"Remove Duplicates..." entry to the cell context menu, but only when the
right-click happens on a cell-range selection -- so it shows up exactly
where the user expects to act on a selected range.
"""

import uno
import unohelper
from com.sun.star.task import XJob
from com.sun.star.ui import XContextMenuInterceptor

ID = "org.ossii.CalcRemoveDuplicates.ContextMenuJob"
SERVICES = ("com.sun.star.task.Job",)
SERVICE_URL = "service:org.ossii.CalcRemoveDuplicates.do"

_CALC = "com.sun.star.sheet.SpreadsheetDocument"
_RANGE_SERVICES = (
    "com.sun.star.sheet.SheetCellRange",
    "com.sun.star.sheet.SheetCellRanges",
)
_IGNORED = uno.Enum("com.sun.star.ui.ContextMenuInterceptorAction", "IGNORED")
_CONTINUE = uno.Enum(
    "com.sun.star.ui.ContextMenuInterceptorAction", "CONTINUE_MODIFIED")

# Registered interceptors are kept alive here (PyUNO would otherwise GC them).
_INTERCEPTORS = []


class _Interceptor(unohelper.Base, XContextMenuInterceptor):
    def notifyContextMenuExecute(self, event):
        try:
            sel = event.Selection.getSelection()
            if sel is None or not any(
                    sel.supportsService(s) for s in _RANGE_SERVICES):
                return _IGNORED

            from rdi18n import _  # lazy: avoid importing easymacro at register

            container = event.ActionTriggerContainer
            sep = container.createInstance(
                "com.sun.star.ui.ActionTriggerSeparator")
            sep.SeparatorType = 0  # LINE
            entry = container.createInstance("com.sun.star.ui.ActionTrigger")
            # Use setPropertyValue: on some builds `entry.Text = ...` raises
            # CannotConvertException ("value is not interface") via PyUNO.
            entry.setPropertyValue("Text", _("Remove Duplicates..."))
            entry.setPropertyValue("CommandURL", SERVICE_URL)

            pos = container.Count
            container.insertByIndex(pos, sep)
            container.insertByIndex(pos + 1, entry)
            return _CONTINUE
        except Exception:
            return _IGNORED


class ContextMenuJob(unohelper.Base, XJob):
    def __init__(self, ctx):
        self.ctx = ctx

    def execute(self, args):
        try:
            self._register(args)
        except Exception:
            pass
        return ()

    def _register(self, args):
        # XJob.execute receives the sequence<NamedValue> directly as `args`.
        env = {}
        for arg in args:
            if arg.Name == "Environment":
                env = {nv.Name: nv.Value for nv in arg.Value}
                break
        model = env.get("Model")
        if model is None or not model.supportsService(_CALC):
            return
        controller = model.getCurrentController()
        if controller is not None:
            interceptor = _Interceptor()
            # Keep a reference: UNO would otherwise let PyUNO GC it.
            _INTERCEPTORS.append(interceptor)
            controller.registerContextMenuInterceptor(interceptor)


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(ContextMenuJob, ID, SERVICES)
