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

idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1358")
dictionaryIdentifiers = idSparql.load()

# dictionaryIdentifiersWikidata = {}
# sparql = SPARQLWrapper("https://qanswer-core1.univ-st-etienne.fr/api/endpoint/wikidata/sparql")
# query = """
#             select ?item ?id where {
#                 ?item <http://www.wikidata.org/prop/direct/P4156> ?id
#             }
#         """
# sparql.setQuery(query)
# sparql.setReturnFormat(JSON)
# results = sparql.query().convert()
# for result in results['results']['bindings']:
#     dictionaryIdentifiersWikidata[result['id']['value']] = result['item']['value'].replace("http://www.wikidata.org/entity/","")

with open('./data/IT_correct.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        line_count = line_count +1
        if line_count>1:
            beneficiary = row[156].split(":::")
            identifier = row[155].split(":::")
            for i in range (0,len(beneficiary)):
                print(beneficiary[i]+"----"+identifier[i])
                wikibase_item = None
                data = {}
                newClaims = []
                if not identifier[i] in dictionaryIdentifiers:
                    wikibase_item = pywikibot.ItemPage(wikibase_repo)
                    data['labels'] = {"it": beneficiary[i].lstrip().rstrip()}
                    data['descriptions'] = {"en": "Beneficiary of a project financed by DG Regio"}
                    # adding the identifier
                    claim = pywikibot.Claim(wikibase_repo, "P1358", datatype='external-id')
                    claim.setTarget(identifier[i])
                    newClaims.append(claim.toJSON())

                    # #link to wikidata if possible
                    # print(row[6])
                    # if row[6] in dictionaryIdentifiersWikidata:
                    #     claim = pywikibot.Claim(wikibase_repo, "P1", datatype='external-id')
                    #     claim.setTarget(dictionaryIdentifiersWikidata.get(row[6]))
                    #     newClaims.append(claim.toJSON())

                    #add the country
                    claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
                    object = pywikibot.ItemPage(wikibase_repo, "Q15")
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
                        print(wikibase_item.getID())
                        dictionaryIdentifiers[identifier[i]] = wikibase_item.getID()
                    except pywikibot.exceptions.OtherPageSaveError as e:
                        fine = False
                else:
                    print("Found!")