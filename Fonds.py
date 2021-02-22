# coding=utf-8
import os
import csv
import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON
from pywikibot import config2

from IdSparql import IdSparql

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

#fund ID
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1583")
dictionaryIdentifiers = idSparql.load()

# data = {}
# description = "DG Regio "
# with open('./data/funds.csv', encoding='utf-8') as csv_file:
#     csv_reader = csv.reader(csv_file, delimiter=';')
#     line_count = 0
#     for row in csv_reader:
#         line_count = line_count+1
#         #print(row[1])
#         #print(row[2])
#         if not row[0] in dictionaryIdentifiers:
#             if line_count > 1:
#                 print(row)
#                 wikibase_item = pywikibot.ItemPage(wikibase_repo)
#                 data['labels'] = {"en": row[1], "fr": row[3]}
#                 data['aliases'] = {"en": [row[0]], "fr": [row[2]]}
#                 data['descriptions'] = {"en": "Fund in the Kohesio project"}
#                 newClaims = []
#
#                 # adding the identifier
#                 claim = pywikibot.Claim(wikibase_repo, "P1583", datatype='external-id')
#                 claim.setTarget(row[0])
#                 newClaims.append(claim.toJSON())
#
#                 claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
#                 claim.setTarget(pywikibot.ItemPage(wikibase_repo, "Q2504365"))
#                 newClaims.append(claim.toJSON())
#
#                 data['claims'] = newClaims
#                 if data != {}:
#                     try:
#                         wikibase_item.editEntity(data)
#                         print("Editing")
#                     except pywikibot.exceptions.OtherPageSaveError as e:
#                         fine = False

map = {}
map['CF']='http://publications.europa.eu/resource/authority/eu-programme/CF'
map['ERDF']='http://publications.europa.eu/resource/authority/eu-programme/ERDF'
map['ESF']='http://publications.europa.eu/resource/authority/eu-programme/ESF'
map['YEI']='http://publications.europa.eu/resource/authority/eu-programme/YEI'
map['IPA II']='http://publications.europa.eu/resource/authority/eu-programme/IPA2'
map['ENI']='http://publications.europa.eu/resource/authority/eu-programme/ENI'
map['EAFRD']='http://publications.europa.eu/resource/authority/eu-programme/EAFRD2020'
map['EMFF']='http://publications.europa.eu/resource/authority/eu-programme/EMFF2020'

languages = ['en', 'fr','cs','pl','it','da']


for m in map:
    if m in dictionaryIdentifiers:
        wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(m))
        wikibase_item.get()
        data = {}

        #                 data['aliases'] = {"en": [row[0]], "fr": [row[2]]}
        data['labels'] = {}
        data['aliases'] = {}
        for lang in languages:
            sparql = SPARQLWrapper("http://publications.europa.eu/webapi/rdf/sparql")
            query = "select ?label where { <"+map[m]+">  <http://www.w3.org/2004/02/skos/core#prefLabel> ?label . FILTER(lang(?label)=\'"+lang+"\')}"
            print(query)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            for result in results['results']['bindings']:
                l = result['label']['value'].split("(")[0].lstrip().rstrip()
                print("l", l)
                data['labels'][lang] = l
                data['aliases'][lang] = []
                if len(result['label']['value'].split("("))>1:
                    acr = result['label']['value'].split("(")[1].replace(")","").lstrip().rstrip()
                    print("acr", acr)
                    data['aliases'][lang].append(acr)
        print(data)
        if data != {}:
            try:
                wikibase_item.editEntity(data)
                print("Editing")
            except pywikibot.exceptions.OtherPageSaveError as e:
                fine = False







data = {}
description = "DG Regio "
with open('./data/CCIPrograms.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if row[0] in countryIdentifiers:
            print(countryIdentifiers[row[0]])
        else:
            print(row[0])
        #print(row[0])
        #print(row[1])
        #print(row[2])
        if not row[1] in dictionaryIdentifiers:
            wikibase_item = pywikibot.ItemPage(wikibase_repo)
            data['labels'] = {"en": row[2]}
            data['descriptions'] = {"en": "Programme in the Kohesio project"}
            newClaims = []
            # adding the identifier
            claim = pywikibot.Claim(wikibase_repo, "P1367", datatype='external-id')
            claim.setTarget(row[1])
            newClaims.append(claim.toJSON())

            claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
            claim.setTarget(pywikibot.ItemPage(wikibase_repo, "Q2463047"))
            newClaims.append(claim.toJSON())

            if row[0] in countryIdentifiers:
                claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
                claim.setTarget(pywikibot.ItemPage(wikibase_repo, countryIdentifiers[row[0]]))
                newClaims.append(claim.toJSON())

            line_count = line_count + 1
            data['claims'] = newClaims
            if data != {}:
                try:
                    wikibase_item.editEntity(data)
                    print("Editing")
                except pywikibot.exceptions.OtherPageSaveError as e:
                    fine = False
                    for i in range(1, 3):
                        if fine == False:
                            try:
                                data['labels'] = {"en": row[2] + "_" + str(i)}
                                wikibase_item.editEntity(data)
                                fine = True
                            except pywikibot.exceptions.OtherPageSaveError as e:
                                fine = False

