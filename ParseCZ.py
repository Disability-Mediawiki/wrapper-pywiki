# coding=utf-8
import os
import csv
import sys

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

print("START")

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

# Czech Koesio Identifier P833
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P833")
dictionaryIdentifiers = idSparql.load()

# Category of intervention Identifier P869
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P869")
dictionaryCategoryIdentifiers = idSparql.load()

# Czech beneficiaries P869
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P528")
dictionaryBeneficiariesIdentifiers = idSparql.load()

# Program identifiers
dictionaryProgramsIdentifiers = {}
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
    select ?label ?s
    where
    {
    ?s ?p <https://linkedopendata.eu/entity/Q2463047> .
    ?s ?p2 <https://linkedopendata.eu/entity/Q25> .
    ?s <https://linkedopendata.eu/prop/direct/P1367> ?id.
    ?s <http://www.w3.org/2004/02/skos/core#altLabel> ?label .
        FILTER(lang(?label)='cs')
    }
                """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    dictionaryProgramsIdentifiers[result['label']['value']] = result['s']['value'].replace("https://linkedopendata.eu/entity/", "")

# fund identifiers
dictionaryFondIdentifiers = {}
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
    select ?label ?s
    where
    {
        ?s ?p <https://linkedopendata.eu/entity/Q2504365> .
        ?s skos:altLabel ?label .
        FILTER(lang(?label)='cs')
    }
                """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    dictionaryFondIdentifiers[result['label']['value']] = result['s']['value'].replace(
        "https://linkedopendata.eu/entity/", "")


def import_chunk(chunk):

    print("enter")
    print(chunk)
    with open('./data/CZ.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = -1
        for row in csv_reader:
            line_count = line_count + 1

            if line_count in chunk:

                wikibase_item = None
                data = {}
                if not row[2] in dictionaryIdentifiers:
                    print("Identifier", row[2])
                    print("enter here")
                    wikibase_item = pywikibot.ItemPage(wikibase_repo)
                    data['labels'] = {"cs": row[3].lstrip().rstrip()}
                    data['descriptions'] = {"en": "Project in Czech Republic financed by DG Regio",
                                            "cs": "Projekt v České republice financovaný DG Regio"}
                else:
                    # print("is created")
                    wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(row[2]))
                    wikibase_item.get()
                    new_id = wikibase_item.getID()
                    print(new_id)
                    claimsToRemove = []
                    found = False
                    for wikibase_claims in wikibase_item.claims:
                        for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                            if wikibase_c.toJSON().get('mainsnak').get('property') == "P1584" :
                                found = True
                                # claimsToRemove.append(wikibase_c)
                    if len(claimsToRemove) > 0:
                        wikibase_item.removeClaims(claimsToRemove)

                    newClaims = []

                    # #generate the categorie of intervention
                    # categories = list(set(row[16].split(";")))
                    # for c in categories:
                    #     #IV.1.057
                    #     import re
                    #     pattern_number = re.compile('\d\d\d')
                    #     match = re.search(pattern_number, c)
                    #     print(match.group())
                    #     if match.group() in dictionaryCategoryIdentifiers:
                    #         claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                    #         object = pywikibot.ItemPage(wikibase_repo, dictionaryCategoryIdentifiers.get(match.group()))
                    #         claim.setTarget(object)
                    #         newClaims.append(claim.toJSON())
                    # print(newClaims)
                    #
                    # # attach the beneficiary
                    # if row[6] in dictionaryBeneficiariesIdentifiers:
                    #     claim = pywikibot.page.Claim(wikibase_repo, "P889", datatype='wikibase-item')
                    #     object = pywikibot.ItemPage(wikibase_repo, dictionaryBeneficiariesIdentifiers[row[6]])
                    #     claim.setTarget(object)
                    #     newClaims.append(claim.toJSON())
                    #     print(newClaims)
                    #
                    #
                    # # adding the identifier
                    # claim = pywikibot.Claim(wikibase_repo, "P833", datatype='external-id')
                    # claim.setTarget(row[2])
                    # newClaims.append(claim.toJSON())
                    #
                    #
                    # # project by DG Regio
                    # claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
                    # object = pywikibot.ItemPage(wikibase_repo, "Q9934")
                    # claim.setTarget(object)
                    # newClaims.append(claim.toJSON())
                    #
                    # # project by DG Regio
                    # claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
                    # object = pywikibot.ItemPage(wikibase_repo, "Q196788")
                    # claim.setTarget(object)
                    # newClaims.append(claim.toJSON())
                    #
                    #
                    #
                    # # adding the country, i.e. Czech Republic
                    # claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
                    # object = pywikibot.ItemPage(wikibase_repo, "Q25")
                    # claim.setTarget(object)
                    # newClaims.append(claim.toJSON())
                    #
                    #
                    #
                    # #adding the budget by the EU
                    # claim = pywikibot.page.Claim(wikibase_repo, "P835",datatype='quantity')
                    # wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q220")
                    # # 14,235,902.00
                    # target = pywikibot.WbQuantity(amount=float(row[21].replace(",","")), unit=wikibase_unit,site=wikibase_repo)
                    # claim.setTarget(target)
                    # newClaims.append(claim.toJSON())
                    # claim = pywikibot.page.Claim(wikibase_repo, "P835", datatype='quantity')
                    # wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                    # # 14,235,902.00
                    # target = pywikibot.WbQuantity(amount=float(row[21].replace(",", ""))*0.040, unit=wikibase_unit, site=wikibase_repo)
                    # claim.setTarget(target)
                    # #specify exchange rate
                    # qualifier1 = pywikibot.page.Claim(wikibase_repo, "P834", datatype='quantity')
                    # target = pywikibot.WbQuantity(amount=0.040, unit=wikibase_unit,site=wikibase_repo)
                    # qualifier1.setTarget(target)
                    # claim.addQualifier(qualifier1)
                    # # specify time of the exchange rate
                    # qualifier2 = pywikibot.page.Claim(wikibase_repo, "P10",
                    #                              datatype='time')
                    # date = datetime.strptime("10.01.2020","%d.%m.%Y").isoformat()+"Z"
                    # target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                    # qualifier2.setTarget(target)
                    # claim.addQualifier(qualifier2)
                    # claim.setRank("preferred")
                    # newClaims.append(claim.toJSON())
                    #
                    # # adding the total budget
                    # claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                    # wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q220")
                    # # 14,235,902.00
                    # target = pywikibot.WbQuantity(amount=float(row[20].replace(",", "")), unit=wikibase_unit,
                    #                               site=wikibase_repo)
                    # claim.setTarget(target)
                    # newClaims.append(claim.toJSON())
                    # claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                    # wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                    # # 14,235,902.00
                    # target = pywikibot.WbQuantity(amount=float(row[20].replace(",", "")) * 0.040, unit=wikibase_unit,
                    #                               site=wikibase_repo)
                    # claim.setTarget(target)
                    # # specify exchange rate
                    # qualifier1 = pywikibot.page.Claim(wikibase_repo, "P834", datatype='quantity')
                    # target = pywikibot.WbQuantity(amount=0.040, unit=wikibase_unit, site=wikibase_repo)
                    # qualifier1.setTarget(target)
                    # claim.addQualifier(qualifier1)
                    # # specify time of the exchange rate
                    # qualifier2 = pywikibot.page.Claim(wikibase_repo, "P10",
                    #                                   datatype='time')
                    # date = datetime.strptime("10.01.2020", "%d.%m.%Y").isoformat() + "Z"
                    # target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                    # qualifier2.setTarget(target)
                    # claim.addQualifier(qualifier2)
                    # claim.setRank("preferred")
                    # newClaims.append(claim.toJSON())
                    #
                    #
                    #
                    #
                    # # adding the postal code
                    # if row[8] != "":
                    #     claim = pywikibot.Claim(wikibase_repo, "P460", datatype='string')
                    #     claim.setTarget(row[8])
                    #     newClaims.append(claim.toJSON())
                    #
                    #     #materialize geo corrdinates
                    #     #print("http://localhost:7070/search/search?postalcode="+row[8].replace(" ","")+"&format=json&addressdetails=1")
                    #     response = requests.get("http://18.196.139.9/search/search?postalcode="+row[8].replace(" ","")+"&format=json&addressdetails=1")
                    #     print(response.json())
                    #     for r in response.json():
                    #         if r["address"]["country"] == "Česko" or r["address"]["country"] == "Česká republika":
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
                    # if row[9] != "":
                    #     claim = pywikibot.Claim(wikibase_repo, "P20", datatype='time')
                    #     claim = pywikibot.page.Claim(wikibase_repo, "P20",
                    #                                  datatype='time')
                    #     date = datetime.strptime(row[9],"%d.%m.%Y").isoformat()+"Z"
                    #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                    #     claim.setTarget(target)
                    #     newClaims.append(claim.toJSON())
                    #
                    # # expected end time P838
                    # if row[10] != "":
                    #     claim = pywikibot.page.Claim(wikibase_repo, "P838",
                    #                                  datatype='time')
                    #     date = datetime.strptime(row[10], "%d.%m.%Y").isoformat() + "Z"
                    #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                    #     claim.setTarget(target)
                    #     newClaims.append(claim.toJSON())
                    #
                    # # end time P33
                    # if row[11]!="":
                    #     claim = pywikibot.page.Claim(wikibase_repo, "P33",
                    #                                  datatype='time')
                    #     date = datetime.strptime(row[11], "%d.%m.%Y").isoformat() + "Z"
                    #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                    #     claim.setTarget(target)
                    #     newClaims.append(claim.toJSON())
                    #
                    # # co-financing rate P671
                    # claim = pywikibot.page.Claim(wikibase_repo, "P837", datatype='quantity')
                    # wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q660")
                    # target = pywikibot.WbQuantity(amount=row[19].replace("%", ""), unit=wikibase_unit, site=wikibase_repo)
                    # claim.setTarget(target)
                    # newClaims.append(claim.toJSON())
                    #
                    # # beneficiary P672
                    # # here this is a hack .......
                    # # print(row[5])
                    # claim = pywikibot.Claim(wikibase_repo, "P841", datatype='string')
                    # claim.setTarget(row[5].replace("\n","").replace("\t","").lstrip().rstrip())
                    # newClaims.append(claim.toJSON())
                    #
                    # # adding the description
                    # if row[4]!="":
                    #     claim = pywikibot.Claim(wikibase_repo, "P836", datatype='monolingualtext')
                    #     object = pywikibot.WbMonolingualText(text = row[4].replace("\n","").replace("\t","").lstrip().rstrip(), language="cs")
                    #     claim.setTarget(object)
                    #     newClaims.append(claim.toJSON())

                    # if row[0] in dictionaryProgramsIdentifiers and found == False:
                    #     claim = pywikibot.Claim(wikibase_repo, "P1368", datatype='wikibase-item')
                    #     object = pywikibot.ItemPage(wikibase_repo, dictionaryProgramsIdentifiers[row[0]])
                    #     claim.setTarget(object)
                    #     newClaims.append(claim.toJSON())

                    for f in row[18].split("; "):
                        if f in dictionaryFondIdentifiers and found == False:
                            claim = pywikibot.Claim(wikibase_repo, "P1584", datatype='wikibase-item')
                            object = pywikibot.ItemPage(wikibase_repo, dictionaryFondIdentifiers[f])
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
                                        data['labels'] = {"cs": row[3].lstrip().rstrip() + "_" + str(i)}
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
    with open('./data/CZ.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            line_count = line_count + 1

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