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
familyfile = os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
    print("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
config2.usernames['my']['my'] = 'DG Regio'

# connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

# map with all NUTS
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P192")
dictionaryNutsIdentifiers = idSparql.load()

# find projects without NUTS
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
select ?s ?coordinates where {
    ?s ?p2 <https://linkedopendata.eu/entity/Q9934> .
    ?s <https://linkedopendata.eu/prop/direct/P127> ?coordinates .
    FILTER NOT EXISTS {?s <https://linkedopendata.eu/prop/direct/P1845> ?o .}
}
        """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

border_points = {'Point(19.5351 54.3894)': '',
                 'Point(4.1374 43.5312)': 'POINT(4.140618650817878 43.53253786995643)',
                 'Point(149.1163 -35.2845)': '',
                 'Point(-61.074 16.3018)': '',
                 'Point(9.2888 41.5948)': 'POINT(9.28159022216795 41.593837154871096)',
                 'Point(45.1431 -12.9284)': 'POINT(45.15327093658449 -12.927730759773462)',
                 'Point(10.6097 55.0528)': 'POINT(10.60950688095093 55.05372184528758)',
                 'Point(-178.1794 -14.2449)': '',
                 'Point(-1.9138 50.1345)': '',
                 'Point(9.8345 44.0507)': 'POINT(9.832273181377262 44.06100741374293)',
                 'Point(13.7534 45.6771)': 'POINT(13.804211767578138 45.65982597118566)',
                 'Point(15.2197 37.2369)': 'POINT(15.221416613769518 37.2442796326066)',
                 }

for result in results['results']['bindings']:
    id = result['s']['value'].replace("https://linkedopendata.eu/entity/", "")
    coo = result['coordinates']['value']

    # check if the point is in the border points

    for key, val in border_points.items():
        if key == coo:
            coo = val

    wikibase_item = pywikibot.ItemPage(wikibase_repo, id)
    wikibase_item.get()
    # take the geo-coordinate and compute the nuts
    sparql = SPARQLWrapper("http://localhost:1234/api/endpoint/sparql")
    query = ''' PREFIX geof: <http://www.opengis.net/def/function/geosparql/> 
            PREFIX geo: <http://www.opengis.net/ont/geosparql#> 
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
            SELECT ?id  WHERE {{ 
                ?s rdf:type <http://nuts.de/NUTS3> . 
                ?s <http://nuts.de/geometry> ?o . 
                FILTER (geof:ehCovers(\"{0}\"^^geo:wktLiteral,?o)) 
                ?s <http://nuts.de/id> ?id .  }} '''.format(coo)
    # print(query)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    nuts = sparql.query().convert()
    for nut in nuts['results']['bindings']:
        nut_id = nut['id']['value']
        if nut_id in dictionaryNutsIdentifiers:
            print("Inserting")
            claim = pywikibot.Claim(wikibase_repo, "P1845", datatype='wikibase-item')
            object = pywikibot.ItemPage(wikibase_repo, dictionaryNutsIdentifiers[nut_id])
            claim.setTarget(object)
            data = {}
            newClaims = []
            newClaims.append(claim.toJSON())
            data['claims'] = newClaims
            wikibase_item.editEntity(data,
                                     summary='Edited by the materialized bot - inferring region from the coordinates')
        else:
            print("NUT NOT FOUND!!!!!!!!!!!!!!")
