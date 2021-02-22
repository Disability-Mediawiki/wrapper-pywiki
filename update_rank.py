import requests

# Program identifiers
from SPARQLWrapper import SPARQLWrapper, JSON
import os

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

sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
select ?s1 where {
 ?s1  <https://linkedopendata.eu/prop/P35>  ?blank .
 ?blank <https://linkedopendata.eu/prop/statement/P35> <https://linkedopendata.eu/entity/Q196899>
}
"""

sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

count = 0
for result in results['results']['bindings']:
    print(result['s1']['value'])
    qid = result['s1']['value'].replace("https://linkedopendata.eu/entity/", "")
    item = pywikibot.ItemPage(wikibase_repo, qid)
    item.get()
    claims = item.claims
    if 'P35' in claims:
        for cl in claims['P35']:
            cl_json = cl.toJSON()
            id = cl_json.get('mainsnak').get('datavalue').get('value').get('numeric-id')
            if str(id) == "196899": # check if beneficiary ...
                if str(cl_json.get('rank')) == 'normal':
                    claim = cl
                    item.removeClaims(claim, summary=u'Removing claim')
                    claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
                    object = pywikibot.ItemPage(wikibase_repo, "Q196899")
                    claim.setTarget(object)
                    claim.setRank("preferred")
                    data = {}
                    newClaims = []
                    newClaims.append(claim.toJSON())
                    data['claims'] = newClaims
                    item.editEntity(data,summary="updated beneficiary")
                    count += 1
                break

print(count)