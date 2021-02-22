# coding=utf-8
import os
import csv
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
config2.sysopnames['my']['my'] = 'DG Regio'

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

list = []
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = '''
select ?s where { 
?s <https://linkedopendata.eu/prop/direct/P35> <https://linkedopendata.eu/entity/Q196899> . 
FILTER (NOT EXISTS {?s <https://linkedopendata.eu/prop/direct/P528> ?o}) 
}
'''
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    list.append(result['s']['value'].replace("https://linkedopendata.eu/entity/",""))

for l in list:
    print(l)
    wikibase_item = pywikibot.ItemPage(wikibase_repo, l)
    wikibase_item.delete(reason="forgot identifier")