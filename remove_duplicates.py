"""Removing duplicate claims"""

import os
import sys

import pywikibot
from pywikibot import config2
from SPARQLWrapper import SPARQLWrapper, JSON

country = sys.argv[1]
prop_id = sys.argv[2]

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
                ?item <https://linkedopendata.eu/prop/direct/P32> <https://linkedopendata.eu/entity/Q""" + country + """> .
            }
        """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

for result in results['results']['bindings']:
    qid = result['item']['value'].replace("https://linkedopendata.eu/entity/", "")
    item = pywikibot.ItemPage(wikibase_repo, qid)
    item.get()
    all_claims = []
    try:
        for claim in item.claims[f'P{prop_id}']:
            claim_value = claim.toJSON().get('mainsnak').get('datavalue').get('value')
            #print(claim_value)
            if claim_value in all_claims: # duplicate detected
                item.removeClaims(claim, summary=u'Removing duplicate claim')
                print(f"Removing duplicate claim for {qid}")
            else:
                all_claims.append(claim_value)
    except KeyError: # no claim
        pass
