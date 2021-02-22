"""Adding translated labels to items"""

import os
import sys

import pandas as pd
import pywikibot
from pywikibot import config2

family = 'my'
mylang = 'my'
familyfile = os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
    print("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
config2.usernames['my']['my'] = 'DG Regio'

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

filename = sys.argv[1]
df = pd.read_csv(filename)
try:
    qids = df["qid"]
except KeyError:
    qids = df["QID"]
labels = df["sLabel"]
for i, qid in enumerate(qids):
    wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
    new_label = str(labels[i])
    if len(new_label) > 400:
        new_label = new_label[:397] + "..."
    if "linkedopendata" not in new_label and new_label != "nan":
        new_label_data = {'en': new_label}
        try:
            wikibase_item.editLabels(new_label_data, summary=u'Label in wikibase changed')
        except pywikibot.exceptions.OtherPageSaveError:
            if len(new_label) > 390:
                new_label = new_label[:387] + "..."
            new_label = f"{new_label} - {qid}"
            new_label_data = {'en': new_label}
            try:
                wikibase_item.editLabels(new_label_data, summary=u'Label in wikibase changed')
            except pywikibot.exceptions.OtherPageSaveError:
                print("Other page save error")
