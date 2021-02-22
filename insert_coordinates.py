"""Adding missing coordinates to items"""

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
qids = df["qid"]
latitude = df["latitude"]
longitude = df["longitude"]
for i, qid in enumerate(qids):
    try:
        item = pywikibot.ItemPage(wikibase_repo, qid)
        claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
        lat = latitude[i]
        lon = longitude[i]
        target = pywikibot.Coordinate(site=wikibase_repo, lat=float(lat), lon=float(lon),
                                      globe_item="http://www.wikidata.org/entity/Q2", precision=0.00001
                                     )
        claim.setTarget(target)
        item.addClaim(claim, summary=u'Adding coordinate location')
    except pywikibot.exceptions.OtherPageSaveError:
        print("Other page save error")
