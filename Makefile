#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

PRJNAME = calc-remove-duplicates
VERNUM = `cat VERSION`

FILES = \
    Addons.xcu \
    Jobs.xcu \
    META-INF/manifest.xml \
    description.xml \
    pkg-desc/ \
    registration/gpl-3.0.txt \
    icons/ \
    pythonpath/ \
    main.py \
    jobs.py \
    README.md \
    VERSION

all: $(FILES) mo
	$(shell ./update_version.sh)
	zip -r $(PRJNAME)-$(VERNUM).oxt $(FILES) locales

pot:
	pygettext3 --output-dir locales -o $(PRJNAME).pot \
	    pythonpath/rdcore.py pythonpath/rddialog.py pythonpath/rdi18n.py

mo:
	msgfmt locales/ru/$(PRJNAME).po -o locales/ru/LC_MESSAGES/$(PRJNAME).mo
	msgfmt locales/zh_CN/$(PRJNAME).po -o locales/zh_CN/LC_MESSAGES/$(PRJNAME).mo
	msgfmt locales/zh_TW/$(PRJNAME).po -o locales/zh_TW/LC_MESSAGES/$(PRJNAME).mo
