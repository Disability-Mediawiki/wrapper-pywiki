# coding=utf-8
import os
import csv
import pywikibot
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

#program ID
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1367")
dictionaryIdentifiers = idSparql.load()



#country codes
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P192")
countryIdentifiers = idSparql.load()




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


