"""Adapting amounts and units in all projects"""

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

# connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
select ?s  where {
    ?s <https://linkedopendata.eu/prop/direct/P35> <https://linkedopendata.eu/entity/Q9934> .
}
        """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    qid = result['s']['value'].replace("https://linkedopendata.eu/entity/", "")
    wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
    wikibase_item.get()
    new_id = wikibase_item.getID()
    claimsToRemove = []
    amount = 0
    for wikibase_claims in wikibase_item.claims:
        for wikibase_c in wikibase_item.claims.get(wikibase_claims):
            if wikibase_c.toJSON().get('mainsnak').get('property') == "P837":
                amount = wikibase_c.toJSON().get('mainsnak').get('datavalue').get('value').get('amount')
                if float(amount) != float(str(round(float(amount), 2))):
                    print('different')
                    amount = str(round(float(amount), 2))
                    claimsToRemove.append(wikibase_c)
                print(amount)

    if len(claimsToRemove) > 0:
        wikibase_item.removeClaims(claimsToRemove)

        newClaims = []
        claim = pywikibot.page.Claim(wikibase_repo, "P837", datatype='quantity')
        wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q660")
        target = pywikibot.WbQuantity(amount=float(amount), unit=wikibase_unit, site=wikibase_repo)
        claim.setTarget(target)
        newClaims.append(claim.toJSON())

        data = {}
        data['claims'] = newClaims

        # fails when entity with the same title already exists .....
        #if not row[2] in dictionaryIdentifiers:
        try:
            wikibase_item.editEntity(data)
        except pywikibot.exceptions.OtherPageSaveError as e:
            fine = False
