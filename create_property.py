# coding=utf-8
import os
import csv
import pywikibot
from pywikibot import config2
from datetime import datetime
import requests
import json
import csv
from IdSparql import IdSparql
from SPARQLWrapper import SPARQLWrapper, JSON
# application config
import configparser
appConfig = configparser.ConfigParser()
appConfig.read('config/application.config.ini')

family = 'my'
mylang = 'my'
familyfile=os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
  print ("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
# config2.usernames['my']['my'] = 'DG Regio'
# config2.usernames['my']['my'] = 'WikibaseAdmin'
config2.usernames['my']['my'] = appConfig.get('wikibase','user')

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()


sparql = SPARQLWrapper(appConfig.get('wikibase','sparqlEndPoint'))
site = pywikibot.Site()

def capitaliseFirstLetter(word):
    # new = list(word)
    # new[0] = word[0].upper()
    # captWord=''.join(new)
    return word.capitalize().rstrip()

#get items with sparql
def getWikiItemSparql(label):
    # sparql = SPARQLWrapper("http://localhost:8989/bigdata/namespace/wdq/sparql")
    query = """
         select ?label ?s where
                {
                  ?s ?p ?o.
                  ?s rdfs:label ?label .
                  FILTER(lang(?label)='fr' || lang(?label)='en')
                  FILTER(?label = '""" + label + """'@en)

                }
         """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # for result in results['results']['bindings']:
    #     print(result)
    print(results)
    return results

# Searches a concept based on its label with a API call
def searchWikiItem(label):
    if label is None:
        return True
    params = {'action': 'wbsearchentities', 'format': 'json',
              'language': 'en', 'type': 'item', 'limit':1,
              'search': label}
    request = wikibase._simple_request(**params)
    result = request.submit()
    print(result)
    return True if len(result['search'])>0 else False

def createProperty(label, description,datatype, property_map):
    if (capitaliseFirstLetter(label.rstrip()) in property_map):
        return property_map
    property_result = getWikiItemSparql(capitaliseFirstLetter(label.rstrip()))
    if (len(property_result['results']['bindings']) == 0):
        data = {
            'datatype': datatype,  # mandatory
            'descriptions': {
                'en': {
                    'language': 'en',
                    'value': capitaliseFirstLetter(description).rstrip() + " en"
                }
            },
            'labels': {
                'en': {
                    'language': 'en',
                    'value': capitaliseFirstLetter(label).rstrip()
                }
            }
        }
        params = {
            'action': 'wbeditentity',
            'new': 'property',
            'data': json.dumps(data),
            'summary': 'creating properties from scripts',
            'token': wikibase.tokens['edit']
        }
        req = wikibase._simple_request(**params)
        response=req.submit();
        property_map[capitaliseFirstLetter(label).rstrip()]=response['entity']['id']
        print(response)
        return property_map;
        # property_map=
    else:
       property_map[capitaliseFirstLetter(label).rstrip()] = property_result['results']['bindings'][0]['s']['value'].split("/")[-1]
       return property_map;

#Reading CSV
def readFileAndProcess():
    with open('data/Predicates.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        property_map={}
        for row in csv_reader:
            print(f'Processing line number of {line_count} ')
            if line_count ==0:
                print(f'Column Headings are {", ".join(row)}')
                line_count += 1
            else:
                if not row[2] :
                    description = capitaliseFirstLetter(row[0]).rstrip()+" : property"
                    label = capitaliseFirstLetter(row[0]).rstrip()
                    datatype = row[1]
                    property_map= createProperty(label,description,datatype,property_map)

                else :
                    description=capitaliseFirstLetter(row[2]).rstrip()
                    label = capitaliseFirstLetter(row[0]).rstrip()
                    datatype= row[1]
                    property_map = createProperty(label, description, datatype, property_map)


                line_count += 1
        print(f'Completed Creating Properties total of {line_count} ')

readFileAndProcess();

exit()