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

idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1105")
dictionaryIdentifiers = idSparql.load()

data = {}
description = "DG Regio "
with open('./data/thematic_objectives.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        print(row[0])
        print(row[1])
        if not row[0] in dictionaryIdentifiers:
            wikibase_item = pywikibot.ItemPage(wikibase_repo)
            data['labels'] = {"en": row[1]}
            data['descriptions'] = {"en": "Thematic objective used by DG Regio"}
            # adding the identifier
            claim = pywikibot.Claim(wikibase_repo, "P1105", datatype='external-id')
            claim.setTarget(row[0])
            data['claims'] = [claim.toJSON()]
            line_count = line_count + 1
            if data != {}:
                wikibase_item.editEntity(data)
        if row[0] in dictionaryIdentifiers:
            wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers[row[0]])
            wikibase_item.get()
            claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
            claim.setTarget(pywikibot.ItemPage(wikibase_repo, "Q236700"))
            data['claims'] = [claim.toJSON()]
            if data != {}:
                wikibase_item.editEntity(data)

