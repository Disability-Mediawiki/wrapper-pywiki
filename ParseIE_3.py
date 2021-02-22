# coding=utf-8
import os
import csv
import sys
import urllib

import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON
from pywikibot import config2
from datetime import datetime
import requests

from IdSparql import IdSparql
import nltk

family = 'my'
mylang = 'my'
familyfile=os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
  print ("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
config2.usernames['my']['my'] = 'DG Regio'

print("START")

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P891")
dictionaryIdentifiers = idSparql.load()

# Category of intervention Identifier P869
dictionaryInterventionIdentifiers = {}
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
                    select ?label ?item where {
                        ?item <https://linkedopendata.eu/prop/direct/P869> ?id .
                        ?item <http://www.w3.org/2000/01/rdf-schema#label> ?label .
                        FILTER (lang(?label)="en")
                    }
                """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    dictionaryInterventionIdentifiers[result['label']['value']] = result['item']['value'].replace("https://linkedopendata.eu/entity/", "")

# Program id P869
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1367")
dictionaryProgramsIdentifiers = idSparql.load()

def import_chunk(chunk):
    with open('./data/IE_2.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = -1
        for row in csv_reader:
            line_count = line_count + 1

            if line_count>0 and line_count in chunk:
                wikibase_item = None
                data = {}
                newClaims = []
                if not str(line_count) in dictionaryIdentifiers:
                    print("enter here")
                    wikibase_item = pywikibot.ItemPage(wikibase_repo)
                    data['labels'] = {"en": row[3][0:400].lstrip().rstrip()}
                    data['descriptions'] = {"en": "Project in Ireland financed by DG Regio"}
                    # adding the identifier
                    claim = pywikibot.Claim(wikibase_repo, "P891", datatype='external-id')
                    claim.setTarget(str(line_count))
                    newClaims.append(claim.toJSON())
                else:
                    print("is created")
                    wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(str(line_count)))
                    wikibase_item.get()
                    new_id = wikibase_item.getID()
                #     claimsToRemove = []
                #     for wikibase_claims in wikibase_item.claims:
                #         for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                #             if not wikibase_c.toJSON().get('mainsnak').get('property') == "P891":
                #                 claimsToRemove.append(wikibase_c)
                #     if len(claimsToRemove) > 0:
                #         wikibase_item.removeClaims(claimsToRemove)
                #
                #
                #
                # # #generate the categorie of intervention
                # # categories = list(set(row[16].split(";")))
                # # for c in categories:
                # #     #IV.1.057
                # #     import re
                # #     pattern_number = re.compile('\d\d\d')
                # #     match = re.search(pattern_number, c)
                # #     print(match.group())
                # #     if match.group() in dictionaryCategoryIdentifiers:
                # #         claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                # #         object = pywikibot.ItemPage(wikibase_repo, dictionaryCategoryIdentifiers.get(match.group()))
                # #         claim.setTarget(object)
                # #         newClaims.append(claim.toJSON())
                # # print(newClaims)
                #
                # # # attach the beneficiary
                # # if row[6] in dictionaryBeneficiariesIdentifiers:
                # #     claim = pywikibot.page.Claim(wikibase_repo, "P889", datatype='wikibase-item')
                # #     object = pywikibot.ItemPage(wikibase_repo, dictionaryBeneficiariesIdentifiers[row[6]])
                # #     claim.setTarget(object)
                # #     newClaims.append(claim.toJSON())
                # #     print(newClaims)
                #
                #
                # # project by DG Regio
                # claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
                # object = pywikibot.ItemPage(wikibase_repo, "Q9934")
                # claim.setTarget(object)
                # newClaims.append(claim.toJSON())
                #
                # # financed by the EU
                # claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
                # object = pywikibot.ItemPage(wikibase_repo, "Q1")
                # claim.setTarget(object)
                # newClaims.append(claim.toJSON())
                #
                # # financed by DG Regio
                # claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
                # object = pywikibot.ItemPage(wikibase_repo, "Q8361")
                # claim.setTarget(object)
                # newClaims.append(claim.toJSON())
                #
                # # adding the country
                # claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
                # object = pywikibot.ItemPage(wikibase_repo, "Q2")
                # claim.setTarget(object)
                # newClaims.append(claim.toJSON())
                #
                # #adding the budget by the EU
                # claim = pywikibot.page.Claim(wikibase_repo, "P835",datatype='quantity')
                # wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                # # 14,235,902.00
                # target = pywikibot.WbQuantity(amount=float(float(row[6])*float(row[7])), unit=wikibase_unit,site=wikibase_repo)
                # claim.setTarget(target)
                # newClaims.append(claim.toJSON())
                #
                # # adding the total budget
                # claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                # wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                # # 14,235,902.00
                # target = pywikibot.WbQuantity(amount=float(row[6]), unit=wikibase_unit,
                #                               site=wikibase_repo)
                # claim.setTarget(target)
                # newClaims.append(claim.toJSON())
                #
                #
                # # adding the postal code
                # if row[8] != "":
                #     # claim = pywikibot.Claim(wikibase_repo, "P460", datatype='string')
                #     # claim.setTarget(row[8])
                #     # newClaims.append(claim.toJSON())
                #
                #     #materialize geo corrdinates
                #     #print("http://localhost:7070/search/search?postalcode="+row[8].replace(" ","")+"&format=json&addressdetails=1")
                #     #response = requests.get("http://ec2-18-184-14-117.eu-central-1.compute.amazonaws.com:7070/search/search?q="+urllib.parse.quote_plus(row[8])+"&format=json&addressdetails=1")
                #     response = requests.get(
                #         "https://nominatim.openstreetmap.org/search/search?q=" + urllib.parse.quote_plus(
                #             row[8]) + "&format=json&addressdetails=1")
                #
                #     print(response.json())
                #     found = False
                #     for r in response.json():
                #         if r["address"]["country"] == "Ireland" and found == False:
                #             found = True
                #             claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
                #             target = pywikibot.Coordinate(site=wikibase_repo, lat=float(r["lat"]), lon=float(r["lon"]),
                #                                           globe_item="http://www.wikidata.org/entity/Q2",
                #                                           precision=0.00001
                #                                           )
                #             claim.setTarget(target)
                #             newClaims.append(claim.toJSON())
                #
                #
                # #start time P20
                # if row[4] != "":
                #     claim = pywikibot.Claim(wikibase_repo, "P20", datatype='time')
                #     claim = pywikibot.page.Claim(wikibase_repo, "P20",
                #                                  datatype='time')
                #     date = datetime.strptime(row[4],"%Y-%m-%d").isoformat()+"Z"
                #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                #     claim.setTarget(target)
                #     newClaims.append(claim.toJSON())
                #
                # # end time P33
                # if row[5]!="":
                #     claim = pywikibot.page.Claim(wikibase_repo, "P33",
                #                                  datatype='time')
                #     date = datetime.strptime(row[5], "%Y-%m-%d").isoformat() + "Z"
                #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                #     claim.setTarget(target)
                #     newClaims.append(claim.toJSON())
                #
                # # co-financing rate P671
                # claim = pywikibot.page.Claim(wikibase_repo, "P837", datatype='quantity')
                # wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q660")
                # target = pywikibot.WbQuantity(amount=str(round(float(float(row[7])*100), 2)), unit=wikibase_unit, site=wikibase_repo)
                # claim.setTarget(target)
                # newClaims.append(claim.toJSON())
                #
                # # beneficiary P672
                # # print(row[5])
                # claim = pywikibot.Claim(wikibase_repo, "P841", datatype='string')
                # claim.setTarget(row[1].replace("\n","").replace("\t","").lstrip().rstrip())
                # newClaims.append(claim.toJSON())
                #
                # # adding the description
                # if row[3]!="":
                #     claim = pywikibot.Claim(wikibase_repo, "P836", datatype='monolingualtext')
                #     object = pywikibot.WbMonolingualText(text = row[3].replace("\n","").replace("\t","").lstrip().rstrip(), language="en")
                #     claim.setTarget(object)
                #     newClaims.append(claim.toJSON())
                #
                # # adding cetegory of intervention
                # min = 300
                # id = -1
                # for cat in dictionaryInterventionIdentifiers:
                #     if min > nltk.edit_distance(cat, row[10]):
                #         min = nltk.edit_distance(cat, row[10])
                #         id = dictionaryInterventionIdentifiers[cat]
                # if id != -1:
                #     claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                #     object = pywikibot.ItemPage(wikibase_repo, id)
                #     claim.setTarget(object)
                #     newClaims.append(claim.toJSON())




                if '2014IE16RFOP002' in dictionaryProgramsIdentifiers:
                    claim = pywikibot.Claim(wikibase_repo, "P1368", datatype='wikibase-item')
                    object = pywikibot.ItemPage(wikibase_repo, dictionaryProgramsIdentifiers['2014IE16RFOP002'])
                    claim.setTarget(object)
                    newClaims.append(claim.toJSON())

                if len(newClaims)>0:
                    data['claims'] = newClaims
                    # fails when entity with the same title already exists .....
                    # if not row[2] in dictionaryIdentifiers:
                    try:
                        wikibase_item.editEntity(data)
                    except pywikibot.exceptions.OtherPageSaveError as e:
                        fine = False
                        for i in range(1, 1000):
                            if fine == False:
                                try:
                                    print(row[3] + "_" + str(i))
                                    data['labels'] = {"en": row[3].lstrip().rstrip() + "_" + str(i)}
                                    wikibase_item.editEntity(data)
                                    fine = True
                                except pywikibot.exceptions.OtherPageSaveError as e:
                                    fine = False
                                if i == 999:
                                    raise Exception('The same file name was used more than 10 times!!!!')
                    sys.stdout.flush()

if __name__ == '__main__':

    from multiprocessing import Pool, freeze_support
    line_count = 0
    with open('./data/IE_2.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            line_count = line_count + 1

    # line_count = 2

    import numpy as np

    processes = 1
    lst = range(line_count)
    print(lst)
    chunks = np.array_split(lst, processes)
    print(chunks)




    pool = Pool(processes=processes)
    print("starting")
    results = pool.map(import_chunk, chunks)
    print(results)
    # while not results.ready():
    #     print("Waiting")
    #     sys.stdout.flush()
    #     results.wait(0.1)