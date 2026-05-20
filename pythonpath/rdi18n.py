"""gettext bootstrap. Loads calc-remove-duplicates.mo from the bundled
locales/ directory and exposes `_` for translations.
Pattern adapted from extensions/writer-batch-compress.
"""

import gettext

import easymacro as app

APPNAME = "calc-remove-duplicates"
ID_EXTENSION = "org.ossii.CalcRemoveDuplicates"

PATH_EXT = app.paths.extension(ID_EXTENSION)
PATH_LOCALES = app.paths.join(PATH_EXT, "locales")

t = gettext.translation(APPNAME, PATH_LOCALES, fallback=True)
_ = t.gettext
