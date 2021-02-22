# coding=utf-8
import os
import csv
import urllib

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

idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P842")
dictionaryIdentifiers = idSparql.load()

# Category of intervention Identifier P869
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P869")
dictionaryCategoryIdentifiers = idSparql.load()

# Program identifiers
dictionaryProgramsIdentifiers = {}
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
    select ?label ?s
    where
    {{
    ?s ?p <https://linkedopendata.eu/entity/Q2463047> .
    ?s ?p2 <https://linkedopendata.eu/entity/Q13> .
    ?s rdfs:label ?label .
        FILTER(lang(?label)='pl' || lang(?label)='en')
    }
    UNION {
        ?s ?p <https://linkedopendata.eu/entity/Q2463047> .
        ?s ?p2 <https://linkedopendata.eu/entity/Q13> .
        ?s skos:altLabel ?label .
            FILTER(lang(?label)='pl' || lang(?label)='en')
        }
    
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
        FILTER(lang(?label)='pl')
    }
                """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    dictionaryFondIdentifiers[result['label']['value']] = result['s']['value'].replace(
        "https://linkedopendata.eu/entity/", "")



def import_chunk(chunk):

    with open('./data/PL.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            line_count=line_count+1
            newClaims = []
            if line_count in chunk:
                #print("Identifier",row[2])
                wikibase_item = None
                data = {}
                found = False
                if not row[2] in dictionaryIdentifiers:
                    print("enter here")
                    wikibase_item = pywikibot.ItemPage(wikibase_repo)
                    data['labels'] = {"pl": row[0][0:400].lstrip().rstrip()}
                    data['descriptions'] = {"en": "Project in Poland financed by DG Regio",
                                            "pl": "Projekt w Polsce finansowany przez DG Regio"}
                    # adding the identifier
                    claim = pywikibot.Claim(wikibase_repo, "P842", datatype='external-id')
                    claim.setTarget(row[2])
                    newClaims.append(claim.toJSON())
                else:
                    print("is created")
                    wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(row[2]))
                    wikibase_item.get()
                    new_id = wikibase_item.getID()
                    print(new_id)
                    claimsToRemove = []

                    for wikibase_claims in wikibase_item.claims:
                       for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                           if wikibase_c.toJSON().get('mainsnak').get('property') == "P1584":
                               # found = True
                                claimsToRemove.append(wikibase_c)
                    if len(claimsToRemove)>0:
                       wikibase_item.removeClaims(claimsToRemove)


                # # financed by the EU
                # claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
                # object = pywikibot.ItemPage(wikibase_repo, "Q1")
                # claim.setTarget(object)
                # newClaims.append(claim.toJSON())
                #
                # # generate the categorie of intervention
                # c = row[20].split(" ")[0]
                # print(c)
                # if c != "" and c in dictionaryCategoryIdentifiers:
                #         claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                #         object = pywikibot.ItemPage(wikibase_repo,
                #                                     dictionaryCategoryIdentifiers.get(c))
                #         claim.setTarget(object)
                #         newClaims.append(claim.toJSON())
                # print(newClaims)





                # # project by DG Regio
                # if row[11] != "":
                #     claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
                #     object = pywikibot.ItemPage(wikibase_repo, "Q9934")
                #     claim.setTarget(object)
                #     newClaims.append(claim.toJSON())
                #
                #     # adding the country, i.e. Czech Republic
                #     claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
                #     object = pywikibot.ItemPage(wikibase_repo, "Q13")
                #     claim.setTarget(object)
                #     newClaims.append(claim.toJSON())
                #
                #     #adding the budget by the EU
                #     claim = pywikibot.page.Claim(wikibase_repo, "P835",datatype='quantity')
                #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q218")
                #     # 14,235,902.00
                #     target = pywikibot.WbQuantity(amount=round(float(row[11].replace(",","")), 2), unit=wikibase_unit,site=wikibase_repo)
                #     claim.setTarget(target)
                #     newClaims.append(claim.toJSON())
                #     claim = pywikibot.page.Claim(wikibase_repo, "P835", datatype='quantity')
                #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                #     # 14,235,902.00
                #     target = pywikibot.WbQuantity(amount=round(float(row[11].replace(",", "")) * 0.24, 2), unit=wikibase_unit, site=wikibase_repo)
                #     claim.setTarget(target)
                #     #specify exchange rate
                #     qualifier1 = pywikibot.page.Claim(wikibase_repo, "P834", datatype='quantity')
                #     target = pywikibot.WbQuantity(amount=0.24, unit=wikibase_unit,site=wikibase_repo)
                #     qualifier1.setTarget(target)
                #     claim.addQualifier(qualifier1)
                #     # specify time of the exchange rate
                #     qualifier2 = pywikibot.page.Claim(wikibase_repo, "P10",
                #                                  datatype='time')
                #     date = datetime.strptime("13.01.2020","%d.%m.%Y").isoformat()+"Z"
                #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                #     qualifier2.setTarget(target)
                #     claim.addQualifier(qualifier2)
                #     claim.setRank("preferred")
                #     newClaims.append(claim.toJSON())
                #
                # # adding the total budget
                # if row[10] != "":
                #     claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q218")
                #     # 14,235,902.00
                #     target = pywikibot.WbQuantity(amount=round(float(row[10].replace(",", "")), 2), unit=wikibase_unit,
                #                                   site=wikibase_repo)
                #     claim.setTarget(target)
                #     newClaims.append(claim.toJSON())
                #     claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                #     # 14,235,902.00
                #     target = pywikibot.WbQuantity(amount=round(float(row[10].replace(",", "")) * 0.24, 2), unit=wikibase_unit,
                #                                   site=wikibase_repo)
                #     claim.setTarget(target)
                #     # specify exchange rate
                #     qualifier1 = pywikibot.page.Claim(wikibase_repo, "P834", datatype='quantity')
                #     target = pywikibot.WbQuantity(amount=0.24, unit=wikibase_unit, site=wikibase_repo)
                #     qualifier1.setTarget(target)
                #     claim.addQualifier(qualifier1)
                #     # specify time of the exchange rate
                #     qualifier2 = pywikibot.page.Claim(wikibase_repo, "P10",
                #                                       datatype='time')
                #     date = datetime.strptime("13.01.2020", "%d.%m.%Y").isoformat() + "Z"
                #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                #     qualifier2.setTarget(target)
                #     claim.addQualifier(qualifier2)
                #     claim.setRank("preferred")
                #     newClaims.append(claim.toJSON())
                #     # co-financing rate P671
                #     claim = pywikibot.page.Claim(wikibase_repo, "P837", datatype='quantity')
                #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q660")
                #     target = pywikibot.WbQuantity(amount=float(row[12]), unit=wikibase_unit, site=wikibase_repo)
                #     claim.setTarget(target)
                #     newClaims.append(claim.toJSON())
                #
                #
                # # adding the postal code
                # print(row[14])
                # for l in row[14].split("|"):
                #     if l != "":
                #         # claim = pywikibot.Claim(wikibase_repo, "P460", datatype='string')
                #         # claim.setTarget(row[8])
                #         # newClaims.append(claim.toJSON())
                #
                #         # materialize geo corrdinates
                #         location = urllib.parse.quote_plus(l.replace("WOJ.:","").replace("POW.:","").replace("GM.:",""))
                #         print(location)
                #         print("http://ec2-18-184-14-117.eu-central-1.compute.amazonaws.com:7070/search/search?q="+location+"&format=json&addressdetails=1")
                #         response = requests.get("http://ec2-18-184-14-117.eu-central-1.compute.amazonaws.com:7070/search/search?q="+location+"&format=json&addressdetails=1")
                #         print(response.json())
                #         found = False
                #         for r in response.json():
                #            print(r)
                #            if r["address"]["country"] == "Poland" or r["address"]["country"] == "Polska" and found == False:
                #                found = True
                #                claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
                #                target = pywikibot.Coordinate(site=wikibase_repo, lat=float(r["lat"]), lon=float(r["lon"]),
                #                                              globe_item="http://www.wikidata.org/entity/Q2",
                #                                              precision=0.0001
                #                                              )
                #                claim.setTarget(target)
                #                newClaims.append(claim.toJSON())
                #
                #
                #
                # #start time P20
                # if row[16] != "":
                #     claim = pywikibot.Claim(wikibase_repo, "P20", datatype='time')
                #     claim = pywikibot.page.Claim(wikibase_repo, "P20",
                #                                  datatype='time')
                #     #2018-10-01
                #     print(row[16])
                #     date = datetime.strptime(row[16],"%Y-%m-%d").isoformat()+"Z"
                #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                #     claim.setTarget(target)
                #     newClaims.append(claim.toJSON())
                # #
                # # # expected end time P838
                # # if row[10] != "":
                # #     claim = pywikibot.page.Claim(wikibase_repo, "P838",
                # #                                  datatype='time')
                # #     date = datetime.strptime(row[10], "%d.%m.%Y").isoformat() + "Z"
                # #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                # #     claim.setTarget(target)
                # #     newClaims.append(claim.toJSON())
                # #
                # # end time P33
                # if row[17]!="":
                #     claim = pywikibot.page.Claim(wikibase_repo, "P33",
                #                                  datatype='time')
                #     date = datetime.strptime(row[17], "%Y-%m-%d").isoformat() + "Z"
                #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                #     claim.setTarget(target)
                #     newClaims.append(claim.toJSON())
                #
                #
                # # beneficiary P672
                # # here this is a hack .......
                # claim = pywikibot.Claim(wikibase_repo, "P841", datatype='string')
                # claim.setTarget(row[3].replace("\n","").replace("\t","").lstrip().rstrip())
                # newClaims.append(claim.toJSON())
                #
                # # adding the description
                # if row[2]!="":
                #     claim = pywikibot.Claim(wikibase_repo, "P836", datatype='monolingualtext')
                #     object = pywikibot.WbMonolingualText(text = row[1].replace("\n","").replace("\t","").lstrip().rstrip(), language="pl")
                #     claim.setTarget(object)
                #     newClaims.append(claim.toJSON())

                # if row[5].lstrip().rstrip() in dictionaryProgramsIdentifiers and found == False:
                #     claim = pywikibot.Claim(wikibase_repo, "P1368", datatype='wikibase-item')
                #     object = pywikibot.ItemPage(wikibase_repo, dictionaryProgramsIdentifiers[row[5].lstrip().rstrip()])
                #     claim.setTarget(object)
                #     newClaims.append(claim.toJSON())

                if row[4].lstrip().rstrip() in dictionaryFondIdentifiers and found == False:
                    # print("Not FOUND ",row[4])
                    claim = pywikibot.Claim(wikibase_repo, "P1584", datatype='wikibase-item')
                    object = pywikibot.ItemPage(wikibase_repo, dictionaryFondIdentifiers[row[4].lstrip().rstrip()])
                    claim.setTarget(object)
                    newClaims.append(claim.toJSON())

                data['claims'] = newClaims

                # fails when entity with the same title already exists .....
                #if not row[2] in dictionaryIdentifiers:
                if len(newClaims)>0:
                    try:
                        wikibase_item.editEntity(data)
                    except pywikibot.exceptions.OtherPageSaveError as e:
                        fine = False
                        for i in range(1, 1000):
                            if fine == False:
                                try:
                                    print(row[0] + "_" + str(i))
                                    data['labels'] = {"pl": row[0][0:400].lstrip().rstrip() + "_" + str(i)}
                                    wikibase_item.editEntity(data=data, summary="adding the fund")
                                    fine = True
                                except pywikibot.exceptions.OtherPageSaveError as e:
                                    fine = False
                                if i == 999:
                                    raise Exception('The same file name was used more than 10 times!!!!')

if __name__ == '__main__':

    from multiprocessing import Pool, freeze_support
    line_count = 0
    with open('./data/PL.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            line_count = line_count + 1

    import numpy as np

    processes = 4
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