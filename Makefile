#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

PRJNAME = Calc-removeduplicates
VERNUM = `cat VERSION`

FILES = \
    Addons.xcu \
    META-INF/manifest.xml \
    description.xml \
    pkg-desc/ \
    registration/gpl-3.0.txt \
    icons/ \
    RemoveDuplicates/ \
    VERSION

all: $(FILES)
	$(shell ./update_version.sh)
	zip -r $(PRJNAME)-$(VERNUM).oxt $(FILES)
