"""Adding funds"""

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

mapping = {"ERDF": "Q2504369", "R": "Q2504369", "ESF": "Q2504370", "S": "Q2504370", "YEI": "Q2504371"}

try:
    qids = df["qid"]
except KeyError:
    qids = df["QID"]
try:
    fund = df["Fond / Fund"]
except KeyError:
    fund = df["fund"]

for i, qid in enumerate(qids):
    wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
    fund_id = fund[i]
    fund_qid = mapping[fund_id]
    print(f"{qid}: adding fund {fund_id} ({fund_qid})")
    try:
        item = pywikibot.ItemPage(wikibase_repo, qid)
        claim = pywikibot.page.Claim(wikibase_repo, "P1584", datatype='wikibase-item')
        wiki_object = pywikibot.ItemPage(wikibase_repo, fund_qid)
        claim.setTarget(wiki_object)
        item.addClaim(claim, summary=u'Adding fund')
    except pywikibot.exceptions.OtherPageSaveError:
        print("Other page save error")
