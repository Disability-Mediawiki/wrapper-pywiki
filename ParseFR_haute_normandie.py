# coding=utf-8
import os
import csv
import urllib

import nltk
import pywikibot
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from pywikibot import config2
from datetime import datetime
import html2text

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
# Category of intervention
dictionaryCategoryIdentifiers = {}
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P869")
dictionaryCategoryIdentifiers = idSparql.load()


# Program identifiers
dictionaryProgramsIdentifiers = {}
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1367")
dictionaryProgramsIdentifiers = idSparql.load()


def import_chunk(chunk):

    with open('./data/FR/FR_bretagne.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        line_count = 0
        print("here")
        for row in csv_reader:
            line_count=line_count+1
            if line_count in chunk:

                    id = 'FR-BR-'+str(line_count)
                    print(row)
                    newClaims = []

                    print("Identifier ",id)
                    wikibase_item = None
                    data = {}
                    if not id in dictionaryIdentifiers:
                        print("enter here", id)
                        wikibase_item = pywikibot.ItemPage(wikibase_repo)
                        data['labels'] = {"fr": row[2][0:400].lstrip().rstrip()}
                        data['descriptions'] = {"en": "Project in France financed by DG Regio",
                                                "fr": "Projet en France financé par DG Regio"}
                        # adding the identifier
                        claim = pywikibot.Claim(wikibase_repo, "P843", datatype='external-id')
                        claim.setTarget(id)
                        newClaims.append(claim.toJSON())
                    # else:
                    #     print("is created")
                    #     wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(id))
                    #     wikibase_item.get()
                    #     claimsToRemove = []
                    #     for wikibase_claims in wikibase_item.claims:
                    #         for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                    #             if not wikibase_c.toJSON().get('mainsnak').get('property') == "P843":
                    #                 claimsToRemove.append(wikibase_c)
                    #     if len(claimsToRemove) > 0:
                    #         wikibase_item.removeClaims(claimsToRemove)


                        print('Done')

                        # project by DG Regio
                        claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
                        object = pywikibot.ItemPage(wikibase_repo, "Q9934")
                        claim.setTarget(object)
                        newClaims.append(claim.toJSON())

                        # financed by the EU
                        claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
                        object = pywikibot.ItemPage(wikibase_repo, "Q1")
                        claim.setTarget(object)
                        newClaims.append(claim.toJSON())
                        claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
                        object = pywikibot.ItemPage(wikibase_repo, "Q8361")
                        claim.setTarget(object)
                        newClaims.append(claim.toJSON())

                        # generate the categorie of intervention
                        if row[11] != '':


                            cat = row[11]
                            if len(cat)==1:
                                cat = '00'+cat
                            if len(cat) == 2:
                                cat = '0' + cat

                            print(cat)

                            claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                            object = pywikibot.ItemPage(wikibase_repo, dictionaryCategoryIdentifiers[cat])
                            claim.setTarget(object)
                            newClaims.append(claim.toJSON())

                        # adding the country, i.e. France
                        claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
                        object = pywikibot.ItemPage(wikibase_repo, "Q20")
                        claim.setTarget(object)
                        newClaims.append(claim.toJSON())

                        # adding the total budget
                        if row[7] != "":
                            claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                            wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                            # 14.235.902
                            print(row[7].replace(".", ""))
                            target = pywikibot.WbQuantity(amount=float(row[7].replace(".", "")), unit=wikibase_unit,
                                                          site=wikibase_repo)
                            claim.setTarget(target)
                            newClaims.append(claim.toJSON())


                        # co-financing rate P671
                        if row[8] != "":
                            print(row[8])
                            claim = pywikibot.page.Claim(wikibase_repo, "P837", datatype='quantity')
                            wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q660")
                            target = pywikibot.WbQuantity(amount=row[8].replace("%", "").replace(",","."), unit=wikibase_unit, site=wikibase_repo)
                            claim.setTarget(target)
                            newClaims.append(claim.toJSON())

                        if row[7] != "" and row[8] != "":
                            #adding the budget by the EU
                            claim = pywikibot.page.Claim(wikibase_repo, "P835",datatype='quantity')
                            wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                            target = pywikibot.WbQuantity(amount=round(float(row[7].replace(".", ""))/100*float(row[8].replace("%", "").replace(",",".")),2), unit=wikibase_unit,site=wikibase_repo)
                            claim.setTarget(target)
                            newClaims.append(claim.toJSON())

                        # adding geo
                        print(row[9])
                        loc = row[9].splitlines()
                        for l in loc:
                            # claim = pywikibot.Claim(wikibase_repo, "P460", datatype='string')
                            # claim.setTarget(row[4])
                            # newClaims.append(claim.toJSON())

                            #materialize geo corrdinates
                            #print("http://ec2-18-184-14-117.eu-central-1.compute.amazonaws.com:7070/search/search?postalcode="+row[4].replace(" ","")+"&format=json&addressdetails=1")
                            print(row[9])
                            response = requests.get("https://nominatim.openstreetmap.org/search/search?q="+urllib.parse.quote_plus(l)+"&format=json&addressdetails=1")
                            print(response.json())
                            found = False
                            for r in response.json():
                               if 'country' in r["address"]  and r["address"]["country"] == "France" and not found:
                                   found = True
                                   claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
                                   target = pywikibot.Coordinate(site=wikibase_repo, lat=float(r["lat"]), lon=float(r["lon"]),
                                                                 globe_item="http://www.wikidata.org/entity/Q2",
                                                                 precision=0.00001
                                                                 )
                                   claim.setTarget(target)
                                   newClaims.append(claim.toJSON())


                        #start time P20
                        if row[4] != "":
                            claim = pywikibot.Claim(wikibase_repo, "P20", datatype='time')
                            claim = pywikibot.page.Claim(wikibase_repo, "P20",
                                                         datatype='time')
                            #2018-10-01
                            print(row[4])
                            date = datetime.strptime(row[4],"%d.%m.%y").isoformat()+"Z"
                            target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                            claim.setTarget(target)
                            newClaims.append(claim.toJSON())

                        # end time P33
                        if row[5]!="":
                            claim = pywikibot.page.Claim(wikibase_repo, "P33",
                                                         datatype='time')
                            date = datetime.strptime(row[5], "%d.%m.%y").isoformat() + "Z"
                            target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                            claim.setTarget(target)
                            newClaims.append(claim.toJSON())


                        # beneficiary P672
                        # here this is a hack .......
                        claim = pywikibot.Claim(wikibase_repo, "P841", datatype='string')
                        claim.setTarget(row[2].replace("\n","").replace("\t","").lstrip().rstrip())
                        newClaims.append(claim.toJSON())
                        #
                        # print(html2text.html2text(row[6]))
                        # adding the description
                        if row[3]!="":
                            if row[3].replace("\n","").replace("\t","").lstrip().rstrip()!="":
                                claim = pywikibot.Claim(wikibase_repo, "P836", datatype='monolingualtext')
                                object = pywikibot.WbMonolingualText(text = row[3][0:1000].replace("\n"," ").replace("\t"," ").lstrip().rstrip(), language="fr")
                                claim.setTarget(object)
                                newClaims.append(claim.toJSON())

                        #adding the program
                        claim = pywikibot.Claim(wikibase_repo, "P1368", datatype='wikibase-item')
                        object = pywikibot.ItemPage(wikibase_repo,
                        dictionaryProgramsIdentifiers['2014FR16M2OP003'])
                        claim.setTarget(object)
                        newClaims.append(claim.toJSON())
                        data['claims'] = newClaims

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
                                            print(row[5] + "_" + str(i))
                                            data['labels'] = {"fr": row[5][0:400].lstrip().rstrip() + "_" + str(i)}
                                            wikibase_item.editEntity(data)
                                            fine = True
                                        except pywikibot.exceptions.OtherPageSaveError as e:
                                            fine = False
                                        if i == 999:
                                            raise Exception('The same file name was used more than 10 times!!!!')



line_count = 0
with open('./data/FR/FR_bretagne.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        line_count = line_count + 1
import numpy as np


lst = range(line_count)
print(lst)
chunks = np.array_split(lst, 1)
print(chunks)

import_chunk(lst)

print("starting")
# while not results.ready():
#     print("Waiting")
#     sys.stdout.flush()
#     results.wait(0.1)