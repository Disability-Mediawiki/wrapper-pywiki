# coding=utf-8
import os
import csv
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

dictionaryBeneficiaryNames = {}
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
select ?s ?name where {
    ?s ?p <https://linkedopendata.eu/entity/Q196899> .
    ?s rdfs:label ?name .
}
"""
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
  dictionaryBeneficiaryNames[result['name']['value']] = result['s']['value'].replace("https://linkedopendata.eu/entity/","")



query = """
select ?s ?name ?country where {
 ?s <https://linkedopendata.eu/prop/direct/P841> ?name .
 ?s <https://linkedopendata.eu/prop/direct/P32> ?country .
 FILTER (?country =  <https://linkedopendata.eu/entity/Q13> )
 FILTER NOT EXISTS {?s <https://linkedopendata.eu/prop/direct/P889> ?o2}
}
"""
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
link = {}
for result in results['results']['bindings']:
  if result['name']['value'] not in dictionaryBeneficiaryNames:

    wikibase_item = pywikibot.ItemPage(wikibase_repo)
    data = {}
    newClaims =[]
    print(result['country']['value'])
    if result['country']['value'] == 'https://linkedopendata.eu/entity/Q25':
      data['labels'] = {"cs": result['name']['value']}
    if result['country']['value'] == 'https://linkedopendata.eu/entity/Q20':
      data['labels'] = {"fr": result['name']['value']}
    if result['country']['value'] == 'https://linkedopendata.eu/entity/Q13':
      data['labels'] = {"pl": result['name']['value']}
    if result['country']['value'] == 'https://linkedopendata.eu/entity/Q12':
      data['labels'] = {"da": result['name']['value']}
    if result['country']['value'] == 'https://linkedopendata.eu/entity/Q15':
      data['labels'] = {"it": result['name']['value']}
    if result['country']['value'] == 'https://linkedopendata.eu/entity/Q2':
      data['labels'] = {"en": result['name']['value']}

    # # link to wikidata if possible
    # print(row[6])
    # if row[6] in dictionaryIdentifiersWikidata:
    #   claim = pywikibot.Claim(wikibase_repo, "P1", datatype='external-id')
    #   claim.setTarget(dictionaryIdentifiersWikidata.get(row[6]))
    #   newClaims.append(claim.toJSON())

    # add the country
    claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
    object = pywikibot.ItemPage(wikibase_repo, result['country']['value'].replace("https://linkedopendata.eu/entity/",""))
    claim.setTarget(object)
    newClaims.append(claim.toJSON())

    # instance of beneficiary
    claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
    object = pywikibot.ItemPage(wikibase_repo, "Q196899")
    claim.setTarget(object)
    newClaims.append(claim.toJSON())

    data['claims'] = newClaims

    try:
      wikibase_item.editEntity(data)
      id = wikibase_item.getID()
      print(id)
      dictionaryBeneficiaryNames[result['name']['value']] = id

      data = {}
      newClaims = []
      wikibase_item = pywikibot.ItemPage(wikibase_repo, result['s']['value'].replace("https://linkedopendata.eu/entity/",""))
      wikibase_item.get()
      claim = pywikibot.Claim(wikibase_repo, "P889", datatype='wikibase-item')
      object = pywikibot.ItemPage(wikibase_repo, id)
      claim.setTarget(object)
      newClaims.append(claim.toJSON())
      data['claims'] = newClaims
      wikibase_item.editEntity(data)
    except pywikibot.exceptions.OtherPageSaveError as e:
      fine = False

  else:
    data = {}
    newClaims = []
    wikibase_item = pywikibot.ItemPage(wikibase_repo, result['s']['value'].replace("https://linkedopendata.eu/entity/",""))
    print(result['s']['value'])
    wikibase_item.get()
    claim = pywikibot.Claim(wikibase_repo, "P889", datatype='wikibase-item')
    object = pywikibot.ItemPage(wikibase_repo, dictionaryBeneficiaryNames[result['name']['value']])
    claim.setTarget(object)
    newClaims.append(claim.toJSON())
    data['claims'] = newClaims
    wikibase_item.editEntity(data)






