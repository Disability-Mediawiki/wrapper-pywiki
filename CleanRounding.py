# coding=utf-8
import os
import csv
from _decimal import Decimal

import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON
from pywikibot import config2
from datetime import datetime
import requests

from IdSparql import IdSparql

family = 'my'
mylang = 'my'
familyfile=os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
  print ("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
config2.usernames['my']['my'] = 'DG Regio'

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
    select ?s ?budget ?exchange ?time ?round where {
  ?s <https://linkedopendata.eu/prop/P835> ?blank .
  ?blank <https://linkedopendata.eu/prop/statement/P835> ?budget .
  ?blank <https://linkedopendata.eu/prop/qualifier/P834> ?exchange .
  ?blank <https://linkedopendata.eu/prop/qualifier/P10> ?time .
  BIND((ROUND(?budget*100)/100) as ?round)
  FILTER (?budget!=?round )
}
        """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    print(result)
    data = {}
    id = result['s']['value'].replace("https://linkedopendata.eu/entity/","")
    print(id)
    wikibase_item = pywikibot.ItemPage(wikibase_repo, id)
    wikibase_item.get()
    newClaims = []
    data = {}

    claimsToRemove = []
    for wikibase_claims in wikibase_item.claims:
        for wikibase_c in wikibase_item.claims.get(wikibase_claims):
            if wikibase_c.toJSON().get('mainsnak').get('property') == "P835":
                if wikibase_c.toJSON().get('mainsnak').get('datavalue').get('value').get('unit') == 'https://linkedopendata.eu/entity/Q226':
                    print(wikibase_c)
                    claimsToRemove.append(wikibase_c)
    wikibase_item.removeClaims(claimsToRemove)

    #adding the budget by the EU
    claim = pywikibot.page.Claim(wikibase_repo, "P835",datatype='quantity')
    wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
    # 14,235,902.00
    target = pywikibot.WbQuantity(amount=round(Decimal(result['budget']['value']),2), unit=wikibase_unit,site=wikibase_repo)
    claim.setTarget(target)
    # specify exchange rate
    qualifier1 = pywikibot.page.Claim(wikibase_repo, "P834", datatype='quantity')
    target = pywikibot.WbQuantity(amount=result['exchange']['value'], unit=wikibase_unit, site=wikibase_repo)
    qualifier1.setTarget(target)
    claim.addQualifier(qualifier1)
    # specify time of the exchange rate
    qualifier2 = pywikibot.page.Claim(wikibase_repo, "P10",
                                      datatype='time')
    # date = datetime.strptime("10.01.2020", "%d.%m.%Y").isoformat() + "Z"
    target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=result['time']['value'], precision=11)
    qualifier2.setTarget(target)
    claim.addQualifier(qualifier2)
    claim.setRank("preferred")
    newClaims.append(claim.toJSON())
    print(newClaims)


    data['claims'] = newClaims
    wikibase_item.editEntity(data, summary="Fixing rounding issue")

