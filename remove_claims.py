"""Removing erroneous claims"""

import os

import pywikibot
from pywikibot import config2
from SPARQLWrapper import SPARQLWrapper, JSON

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

sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
            select ?item where {
                ?item <https://linkedopendata.eu/prop/direct/P35> <https://linkedopendata.eu/entity/Q9934> .
                ?item <https://linkedopendata.eu/prop/direct/P32> <https://linkedopendata.eu/entity/Q12> .
            }
        """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    qid = result['item']['value'].replace("https://linkedopendata.eu/entity/", "")
    item = pywikibot.ItemPage(wikibase_repo, qid)
    item.get() #To access item.claims

    claims = item.claims
    if 'P1368' in claims:
        for claim in claims['P1368']: #Iterate over every summary
            target = claim.getTarget()
            print(f"removing claim for {qid}")
            item.removeClaims(claim, summary=u'Removing claim') #Removing claim
    else:
        print(f"No such claim found for {qid}")
