# coding=utf-8
import os
import csv
import pywikibot
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
# config2.usernames['my']['my'] = 'DG Regio'
config2.usernames['my']['my'] = 'WikibaseAdmin'

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

identifier = "P844"
# idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P844")
spEndpoint = "http://localhost:8989/bigdata/namespace/wdq/sparql"
idSparql = IdSparql(spEndpoint, "P844")
dictionaryIdentifiers = idSparql.load()
print(dictionaryIdentifiers)

# Category of intervention Identifier P869
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P869")
dictionaryCategoryIdentifiers = idSparql.load()

with open('./data/DK.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        line_count=line_count+1
        newClaims = []
        if line_count>2:
            print("Identifier",line_count)
            print(row)
            wikibase_item = None
            data = {}
            if not str(line_count) in dictionaryIdentifiers:
                print("enter here")
                wikibase_item = pywikibot.ItemPage(wikibase_repo)
                data['labels'] = {"da": row[0][0:400].lstrip().rstrip()}
                data['descriptions'] = {"en": "Project in Denmark financed by DG Regio",
                                        "da": "Projekt i Danmark finansieret af DG Regio"}
                # adding the identifier
                claim = pywikibot.Claim(wikibase_repo, identifier, datatype='external-id')
                claim.setTarget(str(line_count))
                newClaims.append(claim.toJSON())
            else:
                print("is created")
                wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(str(line_count)))
                wikibase_item.get()
                new_id = wikibase_item.getID()
                # claimsToRemove = []
                # for wikibase_claims in wikibase_item.claims:
                #    for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                #        if wikibase_c.toJSON().get('mainsnak').get('property') != identifier:
                #         claimsToRemove.append(wikibase_c)
                # if len(claimsToRemove)>0:
                #    wikibase_item.removeClaims(claimsToRemove)

            # financed by the EU
            claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
            object = pywikibot.ItemPage(wikibase_repo, "Q1")
            claim.setTarget(object)
            newClaims.append(claim.toJSON())

            #generate the categorie of intervention
            c = row[19]
            if c!="":
                print(c)

                #062 Samarbejde mellem videninst. og virksomheder
                import re
                pattern_number = re.compile('^\d\d\d')
                match = re.search(pattern_number, c)
                if match != None:
                    if match.group() in dictionaryCategoryIdentifiers:
                        claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                        object = pywikibot.ItemPage(wikibase_repo, dictionaryCategoryIdentifiers.get(match.group()))
                        claim.setTarget(object)
                        newClaims.append(claim.toJSON())
                print(newClaims)

            # # project by DG Regio
            # claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
            # object = pywikibot.ItemPage(wikibase_repo, "Q9934")
            # claim.setTarget(object)
            # newClaims.append(claim.toJSON())
            #
            # #financed by the EU
            # claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
            # object = pywikibot.ItemPage(wikibase_repo, "Q1")
            # claim.setTarget(object)
            # newClaims.append(claim.toJSON())
            #
            # # adding the country
            # claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
            # object = pywikibot.ItemPage(wikibase_repo, "Q12")
            # claim.setTarget(object)
            # newClaims.append(claim.toJSON())
            #
            # #adding the budget by the EU
            # if row[5] != "":
            #     claim = pywikibot.page.Claim(wikibase_repo, "P835",datatype='quantity')
            #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q217")
            #     # 14,235,902.00
            #     target = pywikibot.WbQuantity(amount=float(row[5].replace(".","")), unit=wikibase_unit,site=wikibase_repo)
            #     claim.setTarget(target)
            #     newClaims.append(claim.toJSON())
            #     claim = pywikibot.page.Claim(wikibase_repo, "P835", datatype='quantity')
            #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
            #     # 14,235,902.00
            #     target = pywikibot.WbQuantity(amount=float(row[5].replace(".", ""))*0.13, unit=wikibase_unit, site=wikibase_repo)
            #     claim.setTarget(target)
            #     #specify exchange rate
            #     qualifier1 = pywikibot.page.Claim(wikibase_repo, "P834", datatype='quantity')
            #     target = pywikibot.WbQuantity(amount=0.13, unit=wikibase_unit,site=wikibase_repo)
            #     qualifier1.setTarget(target)
            #     claim.addQualifier(qualifier1)
            #     # specify time of the exchange rate
            #     qualifier2 = pywikibot.page.Claim(wikibase_repo, "P10",
            #                                  datatype='time')
            #     date = datetime.strptime("16.01.2020","%d.%m.%Y").isoformat()+"Z"
            #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
            #     qualifier2.setTarget(target)
            #     claim.addQualifier(qualifier2)
            #     claim.setRank("preferred")
            #     newClaims.append(claim.toJSON())
            #
            # # adding the total budget
            # if row[4] != "":
            #     claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
            #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q217")
            #     # 14,235,902.00
            #     target = pywikibot.WbQuantity(amount=float(row[4].replace(".", "")), unit=wikibase_unit,
            #                                   site=wikibase_repo)
            #     claim.setTarget(target)
            #     newClaims.append(claim.toJSON())
            #     claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
            #     wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
            #     # 14,235,902.00
            #     target = pywikibot.WbQuantity(amount=float(row[4].replace(".", "")) * 0.13, unit=wikibase_unit,
            #                                   site=wikibase_repo)
            #     claim.setTarget(target)
            #     # specify exchange rate
            #     qualifier1 = pywikibot.page.Claim(wikibase_repo, "P834", datatype='quantity')
            #     target = pywikibot.WbQuantity(amount=0.13, unit=wikibase_unit, site=wikibase_repo)
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
            #     target = pywikibot.WbQuantity(amount=float(row[6].replace("%","")), unit=wikibase_unit, site=wikibase_repo)
            #     claim.setTarget(target)
            #     newClaims.append(claim.toJSON())
            #
            #
            # # adding the postal code
            # if row[13] != "":
            #     claim = pywikibot.Claim(wikibase_repo, "P460", datatype='string')
            #     claim.setTarget(row[13])
            #     newClaims.append(claim.toJSON())
            #
            #     #materialize geo corrdinates
            #     print("https://nominatim.openstreetmap.org/search/search?postalcode="+row[13].replace(" ","")+"&country=denmark&format=json&addressdetails=1")
            #     response = requests.get("https://nominatim.openstreetmap.org/search/search?postalcode="+row[13].replace(" ","")+"&country=denmark&format=json&addressdetails=1")
            #     print(response.json())
            #     for r in response.json():
            #        print(r)
            #        if r["address"]["country"] == "Danmark":
            #            claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
            #            target = pywikibot.Coordinate(site=wikibase_repo, lat=float(r["lat"]), lon=float(r["lon"]),
            #                                          globe_item="http://www.wikidata.org/entity/Q2",
            #                                          precision=0.0001
            #                                          )
            #            claim.setTarget(target)
            #            newClaims.append(claim.toJSON())
            #
            # #start time P20
            # if row[1] != "":
            #     claim = pywikibot.Claim(wikibase_repo, "P20", datatype='time')
            #     claim = pywikibot.page.Claim(wikibase_repo, "P20",
            #                                  datatype='time')
            #     #2018-10-01
            #     print(row[1])
            #     date = datetime.strptime(row[1],"%d.%m.%Y").isoformat()+"Z"
            #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
            #     claim.setTarget(target)
            #     newClaims.append(claim.toJSON())
            # # #
            # # # # expected end time P838
            # # # if row[10] != "":
            # # #     claim = pywikibot.page.Claim(wikibase_repo, "P838",
            # # #                                  datatype='time')
            # # #     date = datetime.strptime(row[10], "%d.%m.%Y").isoformat() + "Z"
            # # #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
            # # #     claim.setTarget(target)
            # # #     newClaims.append(claim.toJSON())
            # # #
            # # end time P33
            # if row[2]!="":
            #     claim = pywikibot.page.Claim(wikibase_repo, "P33",
            #                                  datatype='time')
            #     date = datetime.strptime(row[2], "%d.%m.%Y").isoformat() + "Z"
            #     target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
            #     claim.setTarget(target)
            #     newClaims.append(claim.toJSON())
            #
            #
            # # beneficiary P672
            # # here this is a hack .......
            # claim = pywikibot.Claim(wikibase_repo, "P841", datatype='string')
            # claim.setTarget(row[11].replace("\n","").replace("\t","").lstrip().rstrip())
            # newClaims.append(claim.toJSON())
            #
            # # adding the description
            # if row[7]!="":
            #     claim = pywikibot.Claim(wikibase_repo, "P836", datatype='monolingualtext')
            #     object = pywikibot.WbMonolingualText(text = row[7].replace("\n","").replace("\t","").lstrip().rstrip(), language="da")
            #     claim.setTarget(object)
            #     newClaims.append(claim.toJSON())

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
                            print(row[0] + "_" + str(i))
                            data['labels'] = {"da": row[0][0:400].lstrip().rstrip() + " (" + str(i)+")"}
                            wikibase_item.editEntity(data)
                            fine = True
                        except pywikibot.exceptions.OtherPageSaveError as e:
                            fine = False
                        if i == 999:
                            raise Exception('The same file name was used more than 10 times!!!!')
