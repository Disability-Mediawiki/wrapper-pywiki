# coding=utf-8
import os
import csv
import pywikibot
from pywikibot import config2
from pywikibot.data import api
from datetime import datetime
import requests
import json
import csv
from IdSparql import IdSparql
from SPARQLWrapper import SPARQLWrapper, JSON
import time

#application config
import configparser
config = configparser.ConfigParser()
config.read('config/application.config.ini')

family = 'my'
mylang = 'my'
familyfile=os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
  print ("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
# config2.usernames['my']['my'] = 'DG Regio'
# config2.usernames['my']['my'] = 'WikibaseAdmin'
config2.usernames['my']['my'] = config.get('wikibase','user')

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()
sparql = SPARQLWrapper(config.get('wikibase','sparqlEndPoint'))

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

# Searches a concept based on its label on Tripple store
def searchWikiItemSparql(label):
    query = """
         select ?label ?s where
                {
                  ?s ?p ?o.
                  ?s rdfs:label ?label .
                  FILTER(lang(?label)='fr' || lang(?label)='en')
                  FILTER(?label = '"""+label+"""'@en)
                
                }
         """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # for result in results['results']['bindings']:
    #     print(result)
    print(results)
    if(len(results['results']['bindings']) > 0) :
        return True
    else :
        return False


def capitaliseFirstLetter(word):
    new = list(word)
    new[0] = word[0].upper()
    captWord=''.join(new)
    return captWord

#get items with sparql
def getWikiItemSparql(label):
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
    print(results)
    return results

def readFileAndProcess() :
    with open('data/Concepts.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            new_item={}
            print(f'processing line no {line_count}')
            if(line_count==0) :
                line_count+=1
            else:
                isExistSPQL=searchWikiItemSparql(row[1].rstrip())
                isExistAPI=searchWikiItem(row[1].rstrip())
                if(not isExistSPQL and not isExistAPI) :
                    try:
                        print(f"inserting concept {row[1].rstrip()} , count : {line_count}")
                        labels = {"en": row[1].rstrip()}
                        descriptions = {"en": "des :"+ row[1].rstrip()}
                        new_item = pywikibot.ItemPage(wikibase_repo)
                        new_item.editLabels( labels=labels , summary="Creating Concepts")
                        new_item.editDescriptions(descriptions,summary="Setting descripotion")
                        print(new_item)
                        time.sleep(1)
                    except:
                        print(f"ERROR : inserting concept {row[1].rstrip()} , count : {line_count}")
                line_count+=1

def createItem(label, description, key, entity_list) :
    # check whether concept already inserted
    if (capitaliseFirstLetter(key.rstrip()) in entity_list):
        return entity_list
    entity = getWikiItemSparql(capitaliseFirstLetter(key.rstrip()))
    isExistAPI = searchWikiItem(capitaliseFirstLetter(key.rstrip()))
    if (len(entity['results']['bindings']) == 0 and not isExistAPI):
        data = {}
        print(f"inserting concept {key.rstrip()} ")
        data['labels'] = label
        data['descriptions'] = description
        new_item = pywikibot.ItemPage(wikibase_repo)
        new_item.editEntity(data)
        entity_list[capitaliseFirstLetter(key.rstrip())] = new_item.getID()
        return entity_list
    else:
        entity = getWikiItemSparql(capitaliseFirstLetter(key.rstrip()))
        entity_list[capitaliseFirstLetter(key.rstrip())] = entity['results']['bindings'][0]['s']['value'].split("/")[
            -1]
        return entity_list

def readFileAndProcessV2() :
    entity_list={}
    with open('data/Concepts.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            new_item={}
            print(f'processing line no {line_count}')
            if(line_count==0) :
                line_count+=1
            else:
                #check whether concept already inserted
                # insertItem=entity_list[capitaliseFirstLetter(row[1].rstrip())]
                # if not insertItem is None :
                if(capitaliseFirstLetter(row[1].rstrip()) in entity_list) :
                    line_count+=1
                    continue
                entity=getWikiItemSparql(capitaliseFirstLetter(row[1].rstrip()))
                isExistAPI=searchWikiItem(capitaliseFirstLetter(row[1].rstrip()))
                if( len(entity['results']['bindings']) == 0 and not isExistAPI) :
                    try:
                        data = {}
                        print(f"inserting concept {row[1].rstrip()} , count : {line_count}")
                        data['labels'] = {"en": capitaliseFirstLetter(row[1].rstrip())}
                        data['descriptions']  = {"en": capitaliseFirstLetter(row[1].rstrip()) + " entity"}
                        new_item = pywikibot.ItemPage(wikibase_repo)
                        new_item.editEntity(data)
                        entity_list[capitaliseFirstLetter(row[1].rstrip())]=new_item.getID()
                    except:
                        print(f"ERROR : inserting concept {row[1].rstrip()} , count : {line_count}")
                else:
                    entity=getWikiItemSparql(capitaliseFirstLetter(row[1].rstrip()))
                    entity_list[capitaliseFirstLetter(row[1].rstrip())] = entity['results']['bindings'][0]['s']['value'].split("/")[-1]
                line_count+=1

def readFileAndProcessV3() :
    entity_list={}
    with open('data/Triplets-merged.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            new_item={}
            print(f'processing line no {line_count}')
            if(line_count==0) :
                line_count+=1
            else:
                try:
                    data = {}
                    print(f"inserting concept {row[1].rstrip()} , count : {line_count}")
                    label = {"en": capitaliseFirstLetter(row[1].rstrip())}
                    description = {"en": capitaliseFirstLetter(row[1].rstrip()) + " entity"}
                    entity_list = createItem(label, description, row[1].rstrip(), entity_list)
                except:
                    print(f"ERROR : inserting concept {row[1].rstrip()} , count : {line_count}")
                line_count+=1


# this method helps to run the configuration test
def test():
    site = pywikibot.Site()
    page = pywikibot.Page(site, 'Test Item')
    print(page)
    res=getWikiItemSparql("Test Item")
    print(res)
    isExist=searchWikiItemSparql('Human Rights')
    print(isExist)

readFileAndProcessV3()
exit()