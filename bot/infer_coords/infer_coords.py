# coding=utf-8

import urllib
import requests
import os
import csv
import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON
from pywikibot import config2
from datetime import datetime

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


# find projects without NUTS
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
prefix lod: <https://linkedopendata.eu/prop/direct/>
prefix lods: <https://linkedopendata.eu/entity/>
SELECT ?s ?postal ?country_name WHERE {
  ?s lod:P35 lods:Q9934 .
  ?s lod:P460 ?postal .
  ?s lod:P32 ?country .
  ?country rdfs:label ?country_name .
  FILTER NOT EXISTS {?s lod:P127 ?coords} .
  FILTER (lang(?country_name)='en')
} limit 100
 """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

#print(results)
count = 0
country_codes ={
    'France':'fr'
}
for result in results['results']['bindings']:
    id = result['s']['value'].replace("https://linkedopendata.eu/entity/", "")
    postal_code = result['postal']['value']
    response = requests.get("https://nominatim.openstreetmap.org/search/search?q={0}&format=json&addressdetails=1".format(postal_code))
    if len(response.json()) == 0:
        count = count + 1

    wikibase_item = pywikibot.ItemPage(wikibase_repo, id)
    wikibase_item.get()
    for res in response.json():
        if 'country_code' in res['address'] and country_codes[result['country_name']['value']] == res['address']['country_code']:
            print('Found coordinates - inserting ...')
            claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
            target = pywikibot.Coordinate(site=wikibase_repo, lat=float(res["lat"]), lon=float(res["lon"]),
                                          globe_item="http://www.wikidata.org/entity/Q2",
                                          precision=0.00001
                                          )
            claim.setTarget(target)

            newClaims = []
            data = {}
            newClaims.append(claim.toJSON())
            data['claims'] = newClaims
            wikibase_item.editEntity(data,
                                     summary='Edited by the infer coords bot - inferring coordiantes from postal codes')
            break

print("Fail to retrieve {0} postal codes".format(count))
