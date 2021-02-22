"""Correcting total budget for Polish projects"""

import os
import sys

from datetime import datetime
import pandas as pd
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

df = pd.read_csv("data/PL.csv", header=3)
#print(list(df.columns.values))
refcol = "Numer umowy/decyzji/ Contract number"
badcol = "Wartość projektu (w\xa0zł, dla projektów EWT w euro)/ Total\xa0project value (PLN, for ETC projects EUR)"
budgcol = "Wydatki kwalifikowalne (w\xa0zł, dla projektów EWT w euro)/ Total eligible expenditure (PLN, for ETC projects EUR)"

for index, pid in enumerate(df[refcol]):
    oldzlo = float(df[badcol][index])
    newzlo = float(df[budgcol][index])
    if newzlo != oldzlo:
        neweur = newzlo * 0.24

        sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
        query = """
        select ?s  where {
            ?s <https://linkedopendata.eu/prop/direct/P35> <https://linkedopendata.eu/entity/Q9934> .
            ?s <https://linkedopendata.eu/prop/direct/P842> \"""" + pid + """\"
        }
                """
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        response = sparql.query().convert()
        results = response['results']['bindings']
        if len(results) == 0:
            print(f"Missing reference: {pid}")
        elif len(results) > 1:
            print(f"Duplicate reference: {pid}")
            print(results)
        else:
            result = results[0]
            qid = result['s']['value'].replace("https://linkedopendata.eu/entity/", "")
            #print(qid)
            wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
            wikibase_item.get()
            new_id = wikibase_item.getID()
            claimsToRemove = []
            for wikibase_claims in wikibase_item.claims:
                for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                    if wikibase_c.toJSON().get('mainsnak').get('property') == "P474":
                        claimsToRemove.append(wikibase_c)
            if len(claimsToRemove) > 0:
                wikibase_item.removeClaims(claimsToRemove)

                newClaims = []
                claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q218")
                target = pywikibot.WbQuantity(amount=float(newzlo), unit=wikibase_unit, site=wikibase_repo)
                claim.setTarget(target)
                newClaims.append(claim.toJSON())

                claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                target = pywikibot.WbQuantity(amount=round(float(neweur), 2), unit=wikibase_unit, site=wikibase_repo)
                claim.setTarget(target)
                # specify exchange rate
                qualifier1 = pywikibot.page.Claim(wikibase_repo, "P834", datatype='quantity')
                target = pywikibot.WbQuantity(amount=0.24, unit=wikibase_unit, site=wikibase_repo)
                qualifier1.setTarget(target)
                claim.addQualifier(qualifier1)
                # specify time of the exchange rate
                qualifier2 = pywikibot.page.Claim(wikibase_repo, "P10", datatype='time')
                date = datetime.strptime("13.01.2020", "%d.%m.%Y").isoformat() + "Z"
                target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                qualifier2.setTarget(target)
                claim.addQualifier(qualifier2)
                claim.setRank("preferred")
                newClaims.append(claim.toJSON())

                data = {}
                data['claims'] = newClaims

                # fails when entity with the same title already exists .....
                #if not row[2] in dictionaryIdentifiers:
                try:
                    wikibase_item.editEntity(data)
                except pywikibot.exceptions.OtherPageSaveError as e:
                    fine = False
