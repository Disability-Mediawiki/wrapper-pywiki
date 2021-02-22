# coding=utf-8
import os
import csv
import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON
from pywikibot import config2

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

print('doing')
# French Koesio Identifier P843
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P843")
dictionaryIdentifiers = idSparql.load()
print(dictionaryIdentifiers)

print('doing')
# Category of intervention Identifier P869
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P869")
dictionaryCategoryIdentifiers = idSparql.load()
print('doing')

# Program identifiers
dictionaryProgramsIdentifiers = {}
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
    select ?label ?s
    where
    {{
    ?s ?p <https://linkedopendata.eu/entity/Q2463047> .
    ?s ?p2 <https://linkedopendata.eu/entity/Q20> .
    ?s rdfs:label ?label .
        FILTER(lang(?label)='fr' || lang(?label)='en')
    }
    UNION {
        ?s ?p <https://linkedopendata.eu/entity/Q2463047> .
        ?s ?p2 <https://linkedopendata.eu/entity/Q20> .
        ?s skos:altLabel ?label .
            FILTER(lang(?label)='fr' || lang(?label)='en')
        }
    
    }
                """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    dictionaryProgramsIdentifiers[result['label']['value']] = result['s']['value'].replace("https://linkedopendata.eu/entity/", "")
print('doing')
mapping = {}
def import_chunk(chunk):

    with open('./data/FR.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            line_count=line_count+1
            if line_count in chunk:
                newClaims = []

                # print("Identifier",line_count)
                wikibase_item = None
                data = {}
                if not str(line_count) in dictionaryIdentifiers:
                    print("enter here", line_count)
                    wikibase_item = pywikibot.ItemPage(wikibase_repo)
                    data['labels'] = {"fr": row[1][0:400].lstrip().rstrip()}
                    data['descriptions'] = {"en": "Project in France financed by DG Regio",
                                            "fr": "Projet en France financé par DG Regio"}
                    # adding the identifier
                    claim = pywikibot.Claim(wikibase_repo, "P843", datatype='external-id')
                    claim.setTarget(str(line_count))
                    newClaims.append(claim.toJSON())
                else:
                    print("is created")
                    wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(str(line_count)))
                    wikibase_item.get()
                    new_id = wikibase_item.getID()
                    geo = False
                    found = False
                    for wikibase_claims in wikibase_item.claims:
                       for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                           if wikibase_c.toJSON().get('mainsnak').get('property') == "P1368":
                               found = True


                    # claimsToRemove = []
                    # for wikibase_claims in wikibase_item.claims:
                    #    for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                    #        if wikibase_c.toJSON().get('mainsnak').get('property') == "P127":
                    #         claimsToRemove.append(wikibase_c)
                    # if len(claimsToRemove)>0:
                    #    wikibase_item.removeClaims(claimsToRemove)

                    if row[0].lstrip().rstrip() in dictionaryProgramsIdentifiers and found==False:
                        claim = pywikibot.Claim(wikibase_repo, "P1368", datatype='wikibase-item')
                        object = pywikibot.ItemPage(wikibase_repo,
                        dictionaryProgramsIdentifiers[row[0].lstrip().rstrip()])
                        claim.setTarget(object)
                        newClaims.append(claim.toJSON())

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
                    # claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
                    # object = pywikibot.ItemPage(wikibase_repo, "Q8361")
                    # claim.setTarget(object)
                    # newClaims.append(claim.toJSON())
                    #
                    # # generate the categorie of intervention
                    # c = row[12]
                    # print(c)
                    # if c != "":
                    #     print(c)
                    #
                    # # CI01_117 - Amélioration de l'égalité d'accès à l'apprentissage tout au long de la vie pour toutes les catégories d'âges dans un cadre formel,...
                    # import re
                    #
                    # pattern_number = re.compile('_\d\d\d')
                    # match = re.search(pattern_number, c)
                    # if match != None:
                    #     if match.group().replace("_","") in dictionaryCategoryIdentifiers:
                    #         claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                    #         object = pywikibot.ItemPage(wikibase_repo, dictionaryCategoryIdentifiers.get(match.group().replace("_","")))
                    #         claim.setTarget(object)
                    #         newClaims.append(claim.toJSON())
                    # print(newClaims)
                    #
                    # # adding the country, i.e. France
                    # claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
                    # object = pywikibot.ItemPage(wikibase_repo, "Q20")
                    # claim.setTarget(object)
                    # newClaims.append(claim.toJSON())
                    #
                    # if row[15] != "":
                    #     #adding the budget by the EU
                    #     claim = pywikibot.page.Claim(wikibase_repo, "P835",datatype='quantity')
                    #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                    #     # 24892,21
                    #     target = pywikibot.WbQuantity(amount=float(row[15].replace(",", "")), unit=wikibase_unit,site=wikibase_repo)
                    #     claim.setTarget(target)
                    #     newClaims.append(claim.toJSON())
                    #
                    #
                    # # adding the total budget
                    # if row[16] != "":
                    #     claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                    #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                    #     # 14,235,902.00
                    #     target = pywikibot.WbQuantity(amount=float(row[16].replace(",", "")), unit=wikibase_unit,
                    #                                   site=wikibase_repo)
                    #     claim.setTarget(target)
                    #     newClaims.append(claim.toJSON())
                    #
                    #
                    #
                    # # adding the postal code
                    # print(row[4])
                    # if row[4] != "":
                    #     # claim = pywikibot.Claim(wikibase_repo, "P460", datatype='string')
                    #     # claim.setTarget(row[4])
                    #     # newClaims.append(claim.toJSON())
                    #
                    #     #materialize geo corrdinates
                    #     #print("http://ec2-18-184-14-117.eu-central-1.compute.amazonaws.com:7070/search/search?postalcode="+row[4].replace(" ","")+"&format=json&addressdetails=1")
                    #     response = requests.get("https://nominatim.openstreetmap.org/search/search?postalcode="+row[4].replace(" ","")+"&format=json&addressdetails=1")
                    #     print(response.json())
                    #     found = False
                    #     for r in response.json():
                    #        if 'country' in r["address"]  and r["address"]["country"] == "France" and not found:
                    #            found = True
                    #            claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
                    #            target = pywikibot.Coordinate(site=wikibase_repo, lat=float(r["lat"]), lon=float(r["lon"]),
                    #                                          globe_item="http://www.wikidata.org/entity/Q2",
                    #                                          precision=0.00001
                    #                                          )
                    #            claim.setTarget(target)
                    #            newClaims.append(claim.toJSON())
                    #     # if found == False: #this is for cedex addresses
                    #     #     response = requests.get(
                    #     #         "https://nominatim.openstreetmap.org/search/search?postalcode=" + row[4].replace(" ",
                    #     #                                                                                          "")[:-3]+'00' + "&format=json&addressdetails=1")
                    #     #     print(response.json())
                    #     #     found = False
                    #     #     for r in response.json():
                    #     #         if r["address"]["country"] == "France" and not found:
                    #     #             found = True
                    #     #             claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
                    #     #             target = pywikibot.Coordinate(site=wikibase_repo, lat=float(r["lat"]),
                    #     #                                           lon=float(r["lon"]),
                    #     #                                           globe_item="http://www.wikidata.org/entity/Q2",
                    #     #                                           precision=0.00001
                    #     #                                           )
                    #     #             claim.setTarget(target)
                    #     #             newClaims.append(claim.toJSON())
                    #
                    #
                    # #start time P20
                    # if row[5] != "":
                    #     claim = pywikibot.Claim(wikibase_repo, "P20", datatype='time')
                    #     claim = pywikibot.page.Claim(wikibase_repo, "P20",
                    #                                  datatype='time')
                    #     #2018-10-01
                    #     print(row[5])
                    #     date = datetime.strptime(row[5],"%d/%m/%Y").isoformat()+"Z"
                    #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                    #     claim.setTarget(target)
                    #     newClaims.append(claim.toJSON())
                    #
                    # # end time P33
                    # if row[6]!="":
                    #     claim = pywikibot.page.Claim(wikibase_repo, "P33",
                    #                                  datatype='time')
                    #     date = datetime.strptime(row[6], "%d/%m/%Y").isoformat() + "Z"
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
                    # if row[2].replace("\n","").replace("\t","").lstrip().rstrip()!="":
                    #     claim = pywikibot.Claim(wikibase_repo, "P836", datatype='monolingualtext')
                    #     print(row[2])
                    #     print(len(row[2]))
                    #     object = pywikibot.WbMonolingualText(text = row[2][0:500].replace("\n","").replace("\t","").lstrip().rstrip(), language="fr")
                    #     claim.setTarget(object)
                    #     newClaims.append(claim.toJSON())
                    #
                    if len(newClaims)>0:
                        data['claims'] = newClaims
                    #
                    #     # fails when entity with the same title already exists .....
                    #     if not line_count in dictionaryIdentifiers:
                        try:

                            wikibase_item.editEntity(data)
                            print("Editing")
                        except pywikibot.exceptions.OtherPageSaveError as e:
                            fine = False
                            #index = find("*individuo*", "it", 1, 10000)
                            for i in range(1, 1000):
                                if fine == False:
                                    try:
                                        print(data)
                                        print(row[0] + "_" + str(i))
                                        data['labels'] = {"fr": row[0][0:400].lstrip().rstrip() + "_" + str(i)}
                                        wikibase_item.editEntity(data)
                                        fine = True
                                    except pywikibot.exceptions.OtherPageSaveError as e:
                                        fine = False
                                    if i == 999:
                                        raise Exception('The same file name was used more than 10 times!!!!')



line_count = 0
with open('./data/FR.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        line_count = line_count + 1
import numpy as np


lst = range(line_count)
print(lst)
chunks = np.array_split(lst, 4)
print(chunks)

import_chunk(lst)

print("starting")
# while not results.ready():
#     print("Waiting")
#     sys.stdout.flush()
#     results.wait(0.1)