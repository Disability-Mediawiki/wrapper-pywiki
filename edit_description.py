"""Editing descriptions of programmes"""

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
for qid in qids:
    print(qid)
    wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
    new_desc = {'en': 'Programme in the Kohesio project'}
    try:
        wikibase_item.editDescriptions(new_desc, summary=u'Description changed')
    except pywikibot.exceptions.OtherPageSaveError:
        print("Other page save error")
