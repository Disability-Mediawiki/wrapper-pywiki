import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON

from pywikibot import config2
import os

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


def dict_replace_value(d, old, new):
    x = {}
    for k, v in d.items():

        if isinstance(v, dict):
            v = dict_replace_value(v, old, new)
        elif isinstance(v, list):
            v = list_replace_value(v, old, new)
        elif isinstance(v, int):
            if v==old:
                v = new
        x[k] = v
    return x


def list_replace_value(l, old, new):
    x = []
    for e in l:
        if isinstance(e, list):
            e = list_replace_value(e, old, new)
        elif isinstance(e, dict):
            e = dict_replace_value(e, old, new)
        x.append(e)
    return x

def substitute(id,to_merge):
    # search all items using the merge entity
    sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
    query = """
                 select distinct ?s ?p_in where {{
                   ?blank ?p_out <https://linkedopendata.eu/entity/{0}> .
                   ?s ?p_in ?blank .
                   FILTER (STRSTARTS(str(?blank),"https://linkedopendata.eu/entity/statement/"))
                 }} """.format(id)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results['results']['bindings']:
        print("---------------")
        print(result['s']['value'].replace("https://linkedopendata.eu/entity/", ""))
        if result['s']['value'].replace("https://linkedopendata.eu/entity/", "").startswith("Q"):
            wikibase_item = pywikibot.ItemPage(wikibase_repo,
                                               result['s']['value'].replace("https://linkedopendata.eu/entity/",
                                                                            ""))
            wikibase_item.get()
            for wikibase_claims in wikibase_item.claims:
                for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                    if wikibase_c.toJSON().get('mainsnak').get('property') == result['p_in']['value'].replace(
                            "https://linkedopendata.eu/prop/", ""):
                        data = {}
                        newClaims = []
                        newClaims.append(
                            dict_replace_value(wikibase_c.toJSON(), int(id.replace('Q', '')), int(to_merge.replace('Q', ''))))
                        data['claims'] = newClaims
                        wikibase_item.editEntity(data,
                                                 summary="Change because item " +
                                                     id + " was merged with " + to_merge)

sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
select distinct ?wikidata_qid where {
  ?s1 <https://linkedopendata.eu/prop/direct/P1> ?wikidata_qid .
  ?s2 <https://linkedopendata.eu/prop/direct/P1> ?wikidata_qid .
  FILTER (?s1 != ?s2)
}
        """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

for result in results['results']['bindings']:
    print("---------------")
    id = result['wikidata_qid']['value']
    # search all entities having the same id
    # the query orders the items in a way that we merge the item with the most incoming links first, so that fewer modifications need to be done
    query = '''
        SELECT (count(?s) as ?c) ?duplicate  WHERE {{ ?duplicate <https://linkedopendata.eu/prop/direct/P1> \'{0}\' . OPTIONAL {{ ?s ?p   ?duplicate }}. }} group by ?duplicate order by desc(?c) 
            '''.format(id)
    # print(query)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    entities = sparql.query().convert()
    first = True
    to_merge = None
    to_merge_id = None
    for entity in entities['results']['bindings']:
        print(entity['duplicate']['value'])
        if first:
            to_merge_id = entity['duplicate']['value'].replace("https://linkedopendata.eu/entity/", "")
            to_merge = pywikibot.ItemPage(wikibase_repo, to_merge_id)
            first = False
        else:
            id = entity['duplicate']['value'].replace("https://linkedopendata.eu/entity/","")
            wikibase_item = pywikibot.ItemPage(wikibase_repo, id)
            # generally merging fails because items have different descriptions
            data = {}
            descriptions = {'da': '', 'en': ''}
            data['descriptions'] = descriptions
            wikibase_item.editEntity(data)
            # merging the item
            wikibase_item.mergeInto(to_merge)
            substitute(id,to_merge_id)

#substitute("Q2501115","Q296513")





