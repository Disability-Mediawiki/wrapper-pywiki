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

# Program identifiers
dictionaryProgramsIdentifiers = {}
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1367")
dictionaryProgramsIdentifiers = idSparql.load()

data = {}
description = "DG Regio "
with open('./data/program_source.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    line_count = 0
    for row in csv_reader:
        if len(row)==2:
            if row[0] in dictionaryProgramsIdentifiers and row[1].startswith("http"):
                wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryProgramsIdentifiers[row[0]])
                print(row)
                claim = pywikibot.Claim(wikibase_repo, "P1750", datatype='url')
                claim.setTarget(row[1])
                data['claims'] = [claim.toJSON()]
                if data != {}:
                    wikibase_item.editEntity(data)