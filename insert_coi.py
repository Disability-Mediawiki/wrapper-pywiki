"""Adding categories of intervention"""

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

df2 = pd.read_csv("data/coi/coi_mapping.csv")
mapping = {}
for i, cid in enumerate(df2["coi"]):
    mapping[cid] = df2["qid"][i]

df3 = pd.read_csv("data/coi/cups.csv")
cups = {}
for i, qid in enumerate(df3["qid"]):
    cups[qid] = df3["cup"][i]

df4 = pd.read_csv("data/coi/it_coi.csv")
cois = {}
for i, cup in enumerate(df4["CUP"]):
    cois[cup] = df4["CoI"][i]

qids = df["qid"]
try:
    coi = df["CoI"]
except KeyError:
    coi = False
for i, qid in enumerate(qids):
    wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
    if coi:
        coi_ids = [int(coi[i])]
    else:
        cup = cups[qid]
        coi_string = cois[cup]
        coi_ids = [int(c) for c in coi_string.split("|")]
    if len(coi_ids) > 2:
        pass # too many CoIs
    else:
        for coi_id in coi_ids:
            coi_qid = mapping[coi_id]
            try:
                item = pywikibot.ItemPage(wikibase_repo, qid)
                try:
                    existing_coi = item.claims['P888']
                    no_coi = False
                except AttributeError: # no CoI present
                    no_coi = True
                if no_coi:
                    print(f"{i+1} -- {qid}: adding CoI {coi_id} ({coi_qid})")
                    claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                    wiki_object = pywikibot.ItemPage(wikibase_repo, coi_qid)
                    claim.setTarget(wiki_object)
                    item.addClaim(claim, summary=u'Adding CoI')
                else:
                    print(f"CoI already present: {existing_coi}")
                    print(f"{qid}: NOT adding CoI {coi_id} ({coi_qid})")
            except pywikibot.exceptions.OtherPageSaveError:
                print("Other page save error")
