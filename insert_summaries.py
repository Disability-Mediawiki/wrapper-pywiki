"""Adding translated summaries to items"""

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
try:
    skip = sys.argv[2]
    df = pd.read_csv(filename, skiprows=range(1, int(skip)))
except IndexError:
    df = pd.read_csv(filename)
try:
    qids = df["qid"]
except KeyError:
    qids = df["QID"]
summaries = df["summary"]
for i, qid in enumerate(qids):
    new_summary = str(summaries[i])
    if len(new_summary) > 5000:
        print(f"{qid} is longer than 5000 chars")
    elif "linkedopendata" not in new_summary and new_summary != "nan":
        try:
            item = pywikibot.ItemPage(wikibase_repo, qid)
            langofsums = set()
            try:
                for claim in item.claims['P836']:
                    lang = claim.toJSON().get('mainsnak').get('datavalue').get('value').get('language')
                    langofsums.add(lang)
            except AttributeError: # no summary at all
                pass
            if 'en' not in langofsums:
                claim = pywikibot.Claim(wikibase_repo, u'P836', datatype='monolingualtext')
                target = pywikibot.WbMonolingualText(text=new_summary, language='en')
                claim.setTarget(target)
                item.addClaim(claim, summary=u'Adding English summary')
            else:
                print(f"{qid} already has an English summary")
        except pywikibot.exceptions.OtherPageSaveError:
            print("Other page save error")
