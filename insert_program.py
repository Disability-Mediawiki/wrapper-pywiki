"""Adding programmes"""

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

mapping = {"R": "Q2463135", "S": "Q2463132"}

try:
    qids = df["qid"]
except KeyError:
    qids = df["QID"]
fund = df["Fond / Fund"]
for i, qid in enumerate(qids):
    wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
    fund_id = fund[i]
    prog_qid = mapping[fund_id]
    print(f"{qid}: adding program for {fund_id} ({prog_qid})")
    try:
        item = pywikibot.ItemPage(wikibase_repo, qid)
        claim = pywikibot.page.Claim(wikibase_repo, "P1368", datatype='wikibase-item')
        wiki_object = pywikibot.ItemPage(wikibase_repo, prog_qid)
        claim.setTarget(wiki_object)
        item.addClaim(claim, summary=u'Adding program')
    except pywikibot.exceptions.OtherPageSaveError:
        print("Other page save error")
